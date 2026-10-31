"""Build the V5 wireless debugger board: placement, outline, planes, silkscreen.

Stage 1 (place): writes the unrouted board and a DSN for Freerouting.
Run with /usr/bin/python3 pcb.py place
"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from erc import load
from parts import PART

PRJ = '/home/claude/v5dbg/project'
NAME = 'uwat-stellaNova'
NETLIST = '/tmp/claude-0/-home-claude/0eeef73e-c7fb-5128-b9bd-a2ea2b0cc62d/scratchpad/v5.net'
FPDIR = '/usr/share/kicad/footprints'
OX, OY = 100.0, 100.0
W, H = 48.0, 40.0
R_CORNER = 1.0

mm = pcbnew.FromMM
def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))

# ---------------------------------------------------------------------------
# Placement: ref -> (x, y, rotation_deg, side)   board coords, origin top-left
# ---------------------------------------------------------------------------
PLACE = {
    # top band: support column | module (antenna overhangs top edge) | microSD
    'U1': (15.25, 6.75, 0, 'F'),
    'C8': (3.35, 1.3, 0, 'F'), 'C9': (3.4, 3.1, 0, 'F'), 'R5': (3.4, 4.7, 0, 'F'), 'C10': (3.4, 6.3, 0, 'F'),
    'SW1': (2.6, 10.3, 90, 'F'),                     # RESET, beside the EN pin
    'R6': (3.4, 14.4, 0, 'F'),                       # BOOT pull-up
    'R18': (3.4, 16.4, 0, 'F'), 'R19': (3.4, 18.0, 0, 'F'),   # USB series, next to IO19/IO20
    'J3': (39.1, 11.0, 90, 'F'),                     # card inserts from the right edge
    # microSD pull-ups and decoupling, block under the socket
    'R9': (35.7, 19.9, 0, 'F'), 'R10': (38.8, 19.9, 0, 'F'), 'R11': (41.9, 19.9, 0, 'F'), 'R12': (45.0, 19.9, 0, 'F'),
    'R13': (35.7, 21.7, 0, 'F'), 'R14': (38.8, 21.7, 0, 'F'), 'C12': (41.9, 21.7, 0, 'F'), 'C11': (45.2, 21.7, 0, 'F'),
    # bottom band left: RS-485 above USB-C
    'U3': (5.0, 24.3, 0, 'F'), 'C7': (10.3, 22.3, 90, 'F'), 'R3': (10.3, 25.8, 90, 'F'),
    'D5': (5.5, 29.6, 0, 'F'), 'R7': (1.8, 29.6, 90, 'F'), 'R8': (9.2, 29.6, 90, 'F'), 'R4': (10.8, 29.6, 90, 'F'),
    'J2': (5.5, 36.9, 0, 'F'),                       # USB-C, opening on the bottom edge
    'R22': (32.0, 24.8, 0, 'F'),                    # VBUS discharge, over the VBUS feed to D3
    'J1': (16.0, 25.7, 0, 'F'),                      # smart port, opening on the bottom edge
    # beside the jack: protection, BOOT, LEDs
    'F1': (27.4, 23.6, 0, 'F'), 'D2': (27.4, 27.2, 180, 'F'),
    'SW2': (27.6, 31.0, 0, 'F'),
    'R15': (32.4, 30.3, 0, 'F'), 'R16': (32.4, 31.9, 0, 'F'), 'R17': (32.4, 33.5, 0, 'F'),
    'D6': (25.4, 38.0, 90, 'F'), 'D7': (27.6, 38.0, 90, 'F'), 'D8': (29.8, 38.0, 90, 'F'),
    # buck, lower-right corner
    'D1': (37.7, 24.8, 180, 'F'), 'D3': (35.0, 28.2, 180, 'F'), 'C1': (43.3, 25.0, 90, 'F'),
    'U2': (43.0, 30.6, 0, 'F'), 'R20': (39.6, 29.0, 90, 'F'), 'R21': (38.0, 31.0, 90, 'F'), 'C13': (39.6, 32.6, 90, 'F'),
    'R1': (36.4, 31.0, 90, 'F'), 'R2': (36.4, 34.4, 90, 'F'),
    'C2': (42.0, 33.6, 0, 'F'), 'C3': (46.5, 29.2, 90, 'F'), 'L1': (45.6, 34.8, 0, 'F'),
    'C4': (45.6, 38.8, 0, 'F'), 'C5': (41.9, 38.8, 0, 'F'), 'C6': (37.6, 37.8, 0, 'F'),
    # test pads on the back
    'TP1': (33.5, 30.6, 0, 'B'), 'TP2': (33.5, 34.0, 0, 'B'), 'TP3': (30.2, 30.6, 0, 'B'),
    'TP4': (20.0, 4.8, 0, 'B'), 'TP5': (20.0, 8.2, 0, 'B'),
}
SILK_REF = {'U2', 'U3', 'J1', 'J3', 'L1'}


def fpid(fp_str):
    lib, name = fp_str.split(':')
    return lib, name


def load_fp(fp_str):
    lib, name = fpid(fp_str)
    path = os.path.join(PRJ, 'stellaNova.pretty') if lib == 'stellaNova' else os.path.join(FPDIR, lib + '.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f'footprint not found {fp_str}')
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def outline(board):
    r = R_CORNER
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        board.Add(s)
    def arc(cx, cy, sx, sy, ang):
        a = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        a.SetCenter(P(cx, cy)); a.SetStart(P(sx, sy)); a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1)); board.Add(a)
    seg(r, 0, W - r, 0); seg(W, r, W, H - r); seg(W - r, H, r, H); seg(0, H - r, 0, r)
    arc(W - r, r, W - r, 0, 90); arc(W - r, H - r, W, H - r, 90)
    arc(r, H - r, r, H, 90); arc(r, r, 0, r, 90)


def zone(board, net, layer, pts, priority=0, clearance=0.25, min_w=0.2, name=None):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(OX + x), mm(OY + y))
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_w))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.SetAssignedPriority(priority)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


def silk_text(board, text, x, y, size=0.9, layer=pcbnew.F_SilkS, bold=False, angle=0, just=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(P(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(max(0.15, size * 0.15)))
    t.SetBold(bold)
    if angle:
        t.SetTextAngle(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    if just:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if just < 0 else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    board.Add(t)


def build():
    comps, nets = load(NETLIST)
    path = os.path.join(PRJ, NAME + '.kicad_pcb')
    if os.path.exists(path):
        os.remove(path)
    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(4)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    board.SetLayerName(pcbnew.In1_Cu, 'In1.Cu')
    board.SetLayerName(pcbnew.In2_Cu, 'In2.Cu')
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    tb = board.GetTitleBlock()
    tb.SetTitle('uwat-stellaNova'); tb.SetRevision('A'); tb.SetDate('2026-10-29')
    tb.SetComment(0, 'stellaNova: ESP32-S3 WiFi/BLE debugger for the VEX V5 smart port')
    tb.SetComment(1, '4 layers: F.Cu signal, In1 GND, In2 3V3, B.Cu signal. 1.6 mm FR4')

    netinfo = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pad_net = {}
    for name, nodes in nets.items():
        for n in nodes:
            pad_net[(n['ref'], n['pin'])] = name

    missing = [r for r in comps if r not in PLACE]
    extra = [r for r in PLACE if r not in comps]
    if missing or extra:
        raise RuntimeError(f'placement mismatch missing={missing} extra={extra}')

    for ref, c in comps.items():
        part = PART[ref]
        fp = load_fp(c['fp'] or part['footprint'])
        fp.SetReference(ref)
        fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH('/' + c['tstamp']))
        fp.SetProperty('Sheetfile', NAME + '.kicad_sch')
        fp.SetProperty('Sheetname', '')
        for k in ('mfr', 'mpn', 'dk'):
            if part.get(k):
                fp.SetProperty({'mfr': 'Manufacturer', 'mpn': 'MPN', 'dk': 'DigiKey'}[k], part[k])
        attrs = fp.GetAttributes()
        if part.get('dnp'):
            attrs |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        if ref.startswith('TP'):
            attrs |= pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES
        fp.SetAttributes(attrs)
        model = {'J3': 'Hirose_DM3AT-SF-PEJM5', 'J1': 'Molex_43202-4101', 'SW1': 'CK_PTS810', 'SW2': 'CK_PTS810',
                 'F1': 'BelFuse_0ZCG_1812'}.get(ref)
        if model:
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = '${KIPRJMOD}/3dmodels/' + model + '.step'
            fp.Models().push_back(m)
        x, y, rot, side = PLACE[ref]
        board.Add(fp)
        fp.SetPosition(P(x, y))
        if side == 'B':
            fp.Flip(P(x, y), False)
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            key = (ref, num)
            if key in pad_net:
                pad.SetNet(netinfo[pad_net[key]])
        # silkscreen reference only on the larger parts
        rt = fp.Reference()
        rt.SetVisible(ref in SILK_REF)
        rt.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        rt.SetTextThickness(mm(0.15))
        fp.Value().SetVisible(False)

    outline(board)
    corners = [(0, 0), (W, 0), (W, H), (0, H)]
    gnd, p3 = netinfo['GND'], netinfo['+3V3']
    zone(board, gnd, pcbnew.In1_Cu, corners, name='GND plane')
    zone(board, p3, pcbnew.In2_Cu, corners, name='3V3 plane')

    # 0.45 mm ring along the outline: keeps router tracks and vias off the edge
    ring = pcbnew.ZONE(board)
    ring.SetIsRuleArea(True)
    ring.SetDoNotAllowTracks(True); ring.SetDoNotAllowVias(True)
    ring.SetDoNotAllowPads(False); ring.SetDoNotAllowCopperPour(False); ring.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); [ls.AddLayer(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)]
    ring.SetLayerSet(ls)
    ol = ring.Outline(); ol.NewOutline()
    for x, y in [(0, 0), (W, 0), (W, H), (0, H)]:
        ol.Append(mm(OX + x), mm(OY + y))
    ol.NewHole()
    e = 0.45
    for x, y in [(e, e), (e, H - e), (W - e, H - e), (W - e, e)]:
        ol.Append(mm(OX + x), mm(OY + y), 0, 0)
    ring.SetZoneName('edge keepout')
    board.Add(ring)

    # antenna side: stitching vias tie the top-edge ground together under the module
    for i in range(9):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(7.75 + i * 1.875, 0.85))
        v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
        v.SetLocked(True)
        board.Add(v)

    # functional silkscreen
    silk_text(board, 'PWR', 25.4, 35.2, 0.8, angle=90); silk_text(board, 'LINK', 27.6, 35.2, 0.8, angle=90)
    silk_text(board, 'ACT', 29.8, 35.2, 0.8, angle=90)
    silk_text(board, 'BOOT', 24.25, 31.0, 0.8, angle=90)
    silk_text(board, 'RST', 5.05, 10.3, 0.8, angle=90)
    silk_text(board, 'USB', 5.6, 31.9, 0.8)
    silk_text(board, 'V5 PORT', 17.9, 39.0, 0.8)
    silk_text(board, 'SD', 47.2, 2.0, 0.8, just=1)
    for ref, lab in (('TP1', 'VIN'), ('TP2', '3V3'), ('TP3', 'GND'), ('TP4', 'TX0'), ('TP5', 'RX0')):
        x, y, _, _ = PLACE[ref]
        silk_text(board, lab, x + 0.05, y + 1.65, 0.8, layer=pcbnew.B_SilkS)
    silk_text(board, 'uwat-stellaNova rev A', 22.5, 14.5, 0.9, layer=pcbnew.B_SilkS)
    silk_text(board, 'Smart port 1=A 2=B 3=GND 4=VBAT', 22.5, 16.0, 0.8, layer=pcbnew.B_SilkS)
    silk_text(board, 'ESP32-S3  USB-C  RS-485', 22.5, 17.4, 0.8, layer=pcbnew.B_SilkS)

    pcbnew.SaveBoard(path, board)
    return board, path


def fanout(board, netnames=('GND', '+3V3'), via_d=0.6, via_drill=0.3, clr=0.2):
    """Drop a plane via beside each SMD pad of the given nets, where it fits cleanly."""
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    placed, skipped = [], []
    edge = board.GetBoardEdgesBoundingBox()
    keepouts = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowVias() and z.GetZoneName() != 'edge keepout']
    for fp in board.GetFootprints():
        keepouts += [z for z in fp.Zones() if z.GetIsRuleArea()]
    def ok(pt, net):
        for z in keepouts:
            if z.Outline().Contains(pcbnew.VECTOR2I(pt.x, pt.y), -1, mm(0.35)):
                return False
        r = via_d / 2
        x, y = pcbnew.ToMM(pt.x), pcbnew.ToMM(pt.y)
        if x - r < pcbnew.ToMM(edge.GetLeft()) + 0.5 or x + r > pcbnew.ToMM(edge.GetRight()) - 0.5: return False
        if y - r < pcbnew.ToMM(edge.GetTop()) + 0.5 or y + r > pcbnew.ToMM(edge.GetBottom()) - 0.5: return False
        for p in pads:
            same = p.GetNetname() == net and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
            bb = p.GetBoundingBox()
            gap = 0.05 if same else clr
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_NPTH, pcbnew.PAD_ATTRIB_PTH):
                gap = max(gap, 0.3)
            dx = max(pcbnew.ToMM(bb.GetLeft()) - x, 0, x - pcbnew.ToMM(bb.GetRight()))
            dy = max(pcbnew.ToMM(bb.GetTop()) - y, 0, y - pcbnew.ToMM(bb.GetBottom()))
            if (dx * dx + dy * dy) ** 0.5 < r + gap:
                return False
        for v in vias + placed:
            vx, vy = pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y)
            if ((vx - x) ** 2 + (vy - y) ** 2) ** 0.5 < via_d + 0.25:
                return False
        return True
    for fp in board.GetFootprints():
        inward = fp.GetReference() == 'U1'
        cu = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
        c = fp.GetPosition()
        for p in fp.Pads():
            net = p.GetNetname()
            if net not in netnames or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            pp = p.GetPosition()
            bb = p.GetBoundingBox()
            hw, hh = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
            ox, oy = pcbnew.ToMM(pp.x - c.x), pcbnew.ToMM(pp.y - c.y)
            dirs = []
            if inward:
                if p.GetNumber() == '41':
                    continue
                ox, oy = -ox, -oy
            if abs(ox) >= abs(oy) and ox != 0: dirs.append((1 if ox > 0 else -1, 0))
            if abs(oy) > abs(ox) and oy != 0: dirs.append((0, 1 if oy > 0 else -1))
            dirs += [(0, 1), (0, -1), (1, 0), (-1, 0)]
            done = False
            for dx, dy in dirs:
                for extra in (0.15, 0.4, 0.7, 1.0):
                    d = (hw if dx else hh) + via_d / 2 + extra
                    pt = pcbnew.VECTOR2I(pp.x + mm(dx * d), pp.y + mm(dy * d))
                    if ok(pt, net):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pt); v.SetWidth(mm(via_d)); v.SetDrill(mm(via_drill))
                        v.SetNet(p.GetNet()); v.SetLocked(True); board.Add(v); placed.append(v)
                        t = pcbnew.PCB_TRACK(board)
                        t.SetStart(pp); t.SetEnd(pt); t.SetWidth(mm(0.3)); t.SetLayer(cu)
                        t.SetNet(p.GetNet()); t.SetLocked(True); board.Add(t)
                        done = True
                        break
                if done:
                    break
            if not done:
                skipped.append(f'{fp.GetReference()}.{p.GetNumber()}')
    return placed, skipped


def check_overlaps(board):
    """Courtyard overlaps and out-of-board courtyards (front side parts)."""
    issues = []
    fps = list(board.GetFootprints())
    for side, layer in (('F', pcbnew.F_CrtYd), ('B', pcbnew.B_CrtYd)):
        cy = []
        for fp in fps:
            fp.BuildCourtyardCaches()
            poly = fp.GetCourtyard(layer)
            if poly.OutlineCount():
                cy.append((fp.GetReference(), poly))
        for i in range(len(cy)):
            for j in range(i + 1, len(cy)):
                a, b = cy[i][1], cy[j][1]
                inter = pcbnew.SHAPE_POLY_SET(a)
                inter.BooleanIntersection(b, pcbnew.SHAPE_POLY_SET.PM_FAST)
                if inter.OutlineCount() and inter.Area() > mm(0.01) * mm(0.01) * 4:
                    issues.append(f'courtyard overlap {cy[i][0]} x {cy[j][0]}: {inter.Area() / 1e12:.2f} mm2')
    edge = pcbnew.SHAPE_POLY_SET()
    for fp in fps:
        ref = fp.GetReference()
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            x0, y0 = pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY
            x1, y1 = pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY
            if x0 < 0.3 or y0 < 0.3 or x1 > W - 0.3 or y1 > H - 0.3:
                if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    issues.append(f'pad near/over edge {ref}.{pad.GetNumber()} [{x0:.2f},{y0:.2f}..{x1:.2f},{y1:.2f}]')
    return issues


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else 'place'
    if stage == 'place':
        board, path = build()
        board = pcbnew.LoadBoard(path)
        for i in check_overlaps(board):
            print('ISSUE', i)
        placed, skipped = fanout(board)
        print(f'fanout vias {len(placed)}, left for router: {skipped}')
        pcbnew.SaveBoard(path, board)
        dsn = path.replace('.kicad_pcb', '.dsn')
        ok = pcbnew.ExportSpecctraDSN(board, dsn)
        print('saved', path, 'dsn', ok)
