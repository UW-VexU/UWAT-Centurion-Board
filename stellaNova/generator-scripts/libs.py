"""Load and flatten KiCad library symbols; compute pin geometry."""
import copy, math, os
from sexp import parse, find, findall, Sym

SYMDIR = '/usr/share/kicad/symbols'
_cache = {}

def _lib(name, path=None):
    if name not in _cache:
        p = path or os.path.join(SYMDIR, name + '.kicad_sym')
        _cache[name] = parse(open(p).read())
    return _cache[name]

def _raw(lib, name, path=None):
    L = _lib(lib, path)
    for s in findall(L, 'symbol'):
        if s[1] == name:
            return s
    raise KeyError(f'{lib}:{name}')

def flatten(lib, name, path=None):
    """Return a lib_symbols entry named 'lib:name' with inheritance resolved."""
    s = copy.deepcopy(_raw(lib, name, path))
    ext = find(s, 'extends')
    if ext:
        parent = flatten(lib, ext[1], path)
        pname = ext[1]
        out = [Sym('symbol'), f'{lib}:{name}']
        child_props = {p[1]: p for p in findall(s, 'property')}
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == 'property' and c[1] in child_props:
                out.append(child_props.pop(c[1]))
            elif isinstance(c, list) and c[0] == 'symbol':
                cc = copy.deepcopy(c)
                cc[1] = cc[1].replace(pname.split(':')[-1] + '_', name + '_', 1)
                out.append(cc)
            else:
                out.append(copy.deepcopy(c))
        for p in child_props.values():
            out.append(p)
        return out
    s[1] = f'{lib}:{name}'
    return s

def pins(flat):
    """List of dicts: number, name, type, x, y (lib coords, y up), rot, length, unit, hidden."""
    out = []
    base = flat[1].split(':')[-1]
    for u in findall(flat, 'symbol'):
        parts = u[1][len(base) + 1:].split('_')
        unit = int(parts[0])
        for p in findall(u, 'pin'):
            at = find(p, 'at')
            out.append(dict(
                number=find(p, 'number')[1], name=find(p, 'name')[1], type=str(p[1]),
                x=float(at[1]), y=float(at[2]), rot=float(at[3]) if len(at) > 3 else 0.0,
                length=float(find(p, 'length')[1]), unit=unit,
                hidden=any(isinstance(c, Sym) and c == 'hide' for c in p)))
    return out

def body_bbox(flat):
    xs, ys = [], []
    base = flat[1].split(':')[-1]
    for u in findall(flat, 'symbol'):
        for g in u[2:]:
            if not isinstance(g, list):
                continue
            if g[0] == 'rectangle':
                st, en = find(g, 'start'), find(g, 'end')
                xs += [float(st[1]), float(en[1])]; ys += [float(st[2]), float(en[2])]
            elif g[0] == 'polyline':
                for xy in findall(find(g, 'pts'), 'xy'):
                    xs.append(float(xy[1])); ys.append(float(xy[2]))
            elif g[0] == 'circle':
                c = find(g, 'center'); r = float(find(g, 'radius')[1])
                xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
    for p in pins(flat):
        xs.append(p['x']); ys.append(p['y'])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)

def xform(x, y, rot):
    """Lib (y-up) point -> schematic offset (y-down) for symbol rotation rot (deg, CCW on screen)."""
    u, v = x, -y
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    return (u * c + v * s, -u * s + v * c)

def outward(pin_rot, sym_rot):
    """Unit vector pointing away from the body at a pin, in schematic coords."""
    t = math.radians(pin_rot)
    # pin direction (into body) in lib coords
    dx, dy = round(math.cos(t)), round(math.sin(t))
    ox, oy = xform(-dx, -dy, sym_rot)
    return (ox, oy)
