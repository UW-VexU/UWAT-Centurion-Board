"""Programmatic KiCad 7 schematic builder (format 20230121)."""
import copy, uuid, os
from sexp import Sym, dump, find, findall
from libs import flatten, pins as lib_pins, body_bbox, xform, outward

NS = uuid.UUID('6f1c2a7e-3d5b-4f0e-9a1c-v5dbg0000000'.replace('v5dbg', 'abcde'))

def uid(*names):
    return str(uuid.uuid5(NS, '/'.join(str(n) for n in names)))

def g(v):
    """Snap to 0.01 mm to kill float noise."""
    return round(v * 100) / 100

S = Sym

def font(size=1.27, bold=False, italic=False):
    f = [S('font'), [S('size'), size, size]]
    if bold: f.append(S('bold'))
    if italic: f.append(S('italic'))
    return f

def effects(size=1.27, justify=None, hide=False, bold=False, italic=False):
    e = [S('effects'), font(size, bold, italic)]
    if justify:
        e.append([S('justify')] + [S(j) for j in justify.split()])
    if hide:
        e.append(S('hide'))
    return e


class SymInst:
    def __init__(self, sch, lib_id, flat, ref, value, at, rot, mirror, props, dnp, unit=1):
        self.sch, self.lib_id, self.flat = sch, lib_id, flat
        self.ref, self.value, self.at, self.rot, self.mirror = ref, value, at, rot, mirror
        self.props, self.dnp, self.unit = props, dnp, unit
        self.uuid = uid('sym', ref)
        self.pins = {}
        for p in lib_pins(flat):
            if p['unit'] not in (0, unit):
                continue
            self.pins.setdefault(p['number'], p)
        self.fields = {}

    def _t(self, x, y):
        if self.mirror == 'y':
            x = -x
        dx, dy = xform(x, y, self.rot)
        return (g(self.at[0] + dx), g(self.at[1] + dy))

    def pin(self, num):
        p = self.pins[str(num)]
        return self._t(p['x'], p['y'])

    def out(self, num):
        p = self.pins[str(num)]
        rot = p['rot']
        if self.mirror == 'y':
            rot = (180 - rot) % 360
        return outward(rot, self.rot)

    def bbox(self):
        x0, y0, x1, y1 = body_bbox(self.flat)
        pts = [self._t(x, y) for x in (x0, x1) for y in (y0, y1)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)


class Schematic:
    def __init__(self, project, title, paper='A3'):
        self.project, self.title, self.paper = project, title, paper
        self.root = uid('root', project)
        self.lib = {}
        self.syms = []
        self.items = []        # wires, labels, junctions, nc, text, shapes
        self.pwr_n = 0
        self.wires = []        # (p1, p2)
        self.title_block = {}
        self.nc_pins = []

    # ---------- library ----------
    def use(self, lib_id, flat=None):
        if lib_id not in self.lib:
            if flat is None:
                lib, name = lib_id.split(':')
                flat = flatten(lib, name)
            self.lib[lib_id] = flat
        return self.lib[lib_id]

    # ---------- placement ----------
    def add(self, lib_id, ref, value, at, rot=0, mirror=None, footprint=None, dnp=False,
            fields=None, ref_at=None, val_at=None, ref_just='left', val_just='left', hide_value=False):
        flat = self.use(lib_id)
        props = dict(fields or {})
        s = SymInst(self, lib_id, flat, ref, value, (g(at[0]), g(at[1])), rot, mirror, props, dnp)
        s.footprint = footprint if footprint is not None else self._prop(flat, 'Footprint')
        s.datasheet = props.pop('Datasheet', None) or self._prop(flat, 'Datasheet') or '~'
        x0, y0, x1, y1 = s.bbox()
        if ref_at is None:
            ref_at = (x1 + 1.27, (y0 + y1) / 2 - 1.27) if ref.startswith(('R', 'C', 'L', 'F')) and abs(x1 - x0) < 6 else (x0, y0 - 1.27)
        if val_at is None:
            val_at = (x1 + 1.27, (y0 + y1) / 2 + 1.27) if ref.startswith(('R', 'C', 'L', 'F')) and abs(x1 - x0) < 6 else (x0, y1 + 2.54)
        s.ref_at, s.val_at = (g(ref_at[0]), g(ref_at[1])), (g(val_at[0]), g(val_at[1]))
        s.ref_just, s.val_just, s.hide_value = ref_just, val_just, hide_value
        self.syms.append(s)
        return s

    @staticmethod
    def _prop(flat, name):
        for p in findall(flat, 'property'):
            if p[1] == name:
                return p[2]
        return None

    def power(self, lib_id, at, rot=0):
        self.pwr_n += 1
        flat = self.use(lib_id)
        val = self._prop(flat, 'Value')
        pre = '' if os.environ.get('SHOW_PWR') else '#'
        s = SymInst(self, lib_id, flat, f'{pre}PWR0{self.pwr_n:02d}' if not lib_id.endswith('PWR_FLAG') else f'{pre}FLG0{self.pwr_n:02d}',
                    val, (g(at[0]), g(at[1])), rot, None, {}, False)
        s.footprint, s.datasheet, s.power = '', '', True
        if lib_id.endswith('GND') and rot in (90, 270):
            # sideways ground: text beside the triangle, not under it
            d = -1 if rot == 270 else 1
            s.ref_at, s.val_at = (s.at[0] + d * 7.62, s.at[1] + 2.54), (s.at[0] + d * 5.08, s.at[1])
        elif lib_id.endswith('GND'):
            s.ref_at, s.val_at = (s.at[0], s.at[1] + 6.35), (s.at[0], s.at[1] + 3.81)
        elif rot in (90, 270) and not lib_id.endswith('PWR_FLAG'):
            # sideways supply arrow (points up in the library): text beside it
            d = -1 if rot == 90 else 1
            s.ref_at, s.val_at = (s.at[0] + d * 7.62, s.at[1] + 2.54), (s.at[0] + d * 6.6, s.at[1])
        elif lib_id.endswith('PWR_FLAG'):
            s.ref_at, s.val_at = (s.at[0], s.at[1] - 1.91), (s.at[0], s.at[1] - 3.81)
        elif rot == 180:
            s.ref_at, s.val_at = (s.at[0], s.at[1] + 6.35), (s.at[0], s.at[1] + 3.56)
        else:
            s.ref_at, s.val_at = (s.at[0], s.at[1] - 6.35), (s.at[0], s.at[1] - 3.56)
        s.ref_just = s.val_just = None
        s.hide_value = False
        self.syms.append(s)
        return s

    # ---------- connectivity ----------
    def wire(self, *pts):
        pts = [(g(p[0]), g(p[1])) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                self.wires.append((a, b))

    def label(self, name, at, direction):
        """direction: unit vector the label text should extend toward."""
        dx, dy = direction
        ang, just = {(1, 0): (0, 'left'), (-1, 0): (180, 'right'), (0, -1): (90, 'left'), (0, 1): (270, 'right')}[(dx, dy)]
        self.items.append([S('label'), name, [S('at'), g(at[0]), g(at[1]), ang], [S('fields_autoplaced')],
                           effects(1.27, f'{just} bottom'), [S('uuid'), S(uid('label', name, at))]])

    def nc(self, at):
        self.items.append([S('no_connect'), [S('at'), g(at[0]), g(at[1])], [S('uuid'), S(uid('nc', at))]])

    def junction(self, at):
        self.items.append([S('junction'), [S('at'), g(at[0]), g(at[1])], [S('diameter'), 0],
                           [S('color'), 0, 0, 0, 0], [S('uuid'), S(uid('junc', at))]])

    def stub(self, sym, pin, length=2.54, to=None, rail=None, nc=False):
        """Short wire out of a pin, ending in a label, power symbol or no-connect."""
        p = sym.pin(pin)
        if nc:
            self.nc(p)
            self.nc_pins.append((sym.ref, str(pin)))
            return p
        d = sym.out(pin)
        e = (g(p[0] + d[0] * length), g(p[1] + d[1] * length))
        if length:
            self.wire(p, e)
        if rail:
            self.power(rail, e)
        elif to:
            self.label(to, e, d)
        return e

    # ---------- annotation ----------
    def text(self, s, at, size=1.27, bold=False, italic=False):
        self.items.append([S('text'), s, [S('at'), g(at[0]), g(at[1]), 0],
                           effects(size, 'left top', bold=bold, italic=italic), [S('uuid'), S(uid('text', s[:40], at))]])

    def frame(self, x0, y0, x1, y1, title, note=None):
        self.items.append([S('rectangle'), [S('start'), g(x0), g(y0)], [S('end'), g(x1), g(y1)],
                           [S('stroke'), [S('width'), 0.254], [S('type'), S('dash')], [S('color'), 72, 72, 72, 1]],
                           [S('fill'), [S('type'), S('none')]], [S('uuid'), S(uid('frame', title))]])
        self.text(title, (x0 + 2.54, y0 + 2.54), size=2.0, bold=True)
        if note:
            self.text(note, (x0 + 2.54, y0 + 6.35), size=1.27, italic=True)

    # ---------- output ----------
    def _junctions(self):
        pts = {}
        for a, b in self.wires:
            for p in (a, b):
                pts[p] = pts.get(p, 0) + 1
        pinpts = set()
        for s in self.syms:
            for n in s.pins:
                pinpts.add(s.pin(n))
        # midpoint T-joins: endpoint lying strictly inside another wire
        for a, b in self.wires:
            for p in list(pts):
                if p in (a, b):
                    continue
                if (a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1])) or \
                   (a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0])):
                    raise ValueError(f'T-junction on wire mid-span at {p}; split the wire')
        for p, n in pts.items():
            if n + (1 if p in pinpts else 0) >= 3:
                self.junction(p)

    def _sym_sexpr(self, s):
        e = [S('symbol'), [S('lib_id'), s.lib_id], [S('at'), s.at[0], s.at[1], s.rot]]
        if s.mirror:
            e.append([S('mirror'), S(s.mirror)])
        e += [[S('unit'), s.unit], [S('in_bom'), S('no' if getattr(s, 'power', False) else 'yes')],
              [S('on_board'), S('yes')], [S('dnp'), S('yes' if s.dnp else 'no')]]
        if not getattr(s, 'power', False):
            e.append([S('fields_autoplaced')])
        e.append([S('uuid'), S(s.uuid if not getattr(s, 'power', False) else uid('pwr', s.ref))])
        is_pwr = getattr(s, 'power', False)
        fa = 90 if s.rot in (90, 270) else 0
        e.append([S('property'), 'Reference', s.ref, [S('at'), s.ref_at[0], s.ref_at[1], fa],
                  effects(1.27, s.ref_just and f'{s.ref_just}', hide=is_pwr)])
        e.append([S('property'), 'Value', s.value, [S('at'), s.val_at[0], s.val_at[1], fa],
                  effects(1.27, s.val_just and f'{s.val_just}', hide=s.hide_value or (is_pwr and s.lib_id.endswith('PWR_FLAG') is False and False))])
        e.append([S('property'), 'Footprint', s.footprint or '', [S('at'), s.at[0], s.at[1], 0], effects(1.27, hide=True)])
        e.append([S('property'), 'Datasheet', s.datasheet or '~', [S('at'), s.at[0], s.at[1], 0], effects(1.27, hide=True)])
        for k, v in s.props.items():
            e.append([S('property'), k, v, [S('at'), s.at[0], s.at[1], 0], effects(1.27, hide=True)])
        for n, p in s.pins.items():
            e.append([S('pin'), n, [S('uuid'), S(uid('pin', s.ref, n))]])
        e.append([S('instances'), [S('project'), self.project,
                  [S('path'), '/' + self.root, [S('reference'), s.ref], [S('unit'), s.unit]]]])
        return e

    def write(self, path):
        self._junctions()
        tb = [S('title_block'), [S('title'), self.title]]
        for k in ('date', 'rev', 'company'):
            if k in self.title_block:
                tb.append([S(k), self.title_block[k]])
        for i, c in enumerate(self.title_block.get('comments', []), 1):
            tb.append([S('comment'), i, c])
        root = [S('kicad_sch'), [S('version'), 20230121], [S('generator'), S('eeschema')],
                [S('uuid'), S(self.root)], [S('paper'), self.paper], tb,
                [S('lib_symbols')] + [copy.deepcopy(v) for v in self.lib.values()]]
        for a, b in self.wires:
            root.append([S('wire'), [S('pts'), [S('xy'), a[0], a[1]], [S('xy'), b[0], b[1]]],
                         [S('stroke'), [S('width'), 0], [S('type'), S('default')]], [S('uuid'), S(uid('wire', a, b))]])
        root += self.items
        for s in self.syms:
            root.append(self._sym_sexpr(s))
        root.append([S('sheet_instances'), [S('path'), '/', [S('page'), '1']]])
        open(path, 'w').write(dump(root) + '\n')
