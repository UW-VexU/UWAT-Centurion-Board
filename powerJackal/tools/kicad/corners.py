"""Audit trace corners: every point where track segments meet, with the angle between them, and every track that
enters a pad off the pad's axis. usage: python3 corners.py board.kicad_pcb [report.json]"""
import sys, math, json, collections
import pcbnew
from pcb_common import OX, OY

b = pcbnew.LoadBoard(sys.argv[1])
T = pcbnew.ToMM
segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = list(b.GetPads())

node = collections.defaultdict(list)          # (layer, x, y) -> [(track, direction away from the node)]
for t in segs:
    s, e = t.GetStart(), t.GetEnd()
    if s == e: continue
    for p, q in ((s, e), (e, s)):
        d = (q.x - p.x, q.y - p.y); L = math.hypot(*d)
        node[(t.GetLayer(), p.x, p.y)].append((t, (d[0] / L, d[1] / L)))

def pad_at(layer, x, y, net):
    for p in pads:
        if p.GetNetCode() == net and p.IsOnLayer(layer) and p.HitTest(pcbnew.VECTOR2I(x, y)): return p
    return None
def via_at(x, y):
    for v in vias:
        if v.GetPosition().x == x and v.GetPosition().y == y: return v
    return None
ZONES = list(b.Zones())
def in_pour(layer, x, y, net):
    v = pcbnew.VECTOR2I(x, y)
    return any(z.GetNetCode() == net and z.IsOnLayer(layer) and z.HitTestFilledArea(layer, v) for z in ZONES)
def ang(u, v): return math.degrees(math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))))

corners = []
for (layer, x, y), lst in node.items():
    if len(lst) < 2: continue
    net = lst[0][0].GetNetname(); p = pad_at(layer, x, y, lst[0][0].GetNetCode())
    worst = min(ang(a[1], c[1]) for i, a in enumerate(lst) for c in lst[i + 1:])
    tee = len(lst) == 3 and any(abs(ang(a[1], c[1]) - 180) < 0.5 for i, a in enumerate(lst) for c in lst[i + 1:]) and worst > 89.5
    kind = "acute" if worst < 89.5 else "right" if worst < 90.5 else "obtuse" if worst < 179.5 else "straight"
    corners.append(dict(x=round(T(x) - OX, 3), y=round(T(y) - OY, 3), layer=b.GetLayerName(layer), net=net, n=len(lst),
                        angle=round(worst, 1), kind=kind, pad=(p.GetParent().Cast().GetReference() + "." + p.GetNumber()) if p else None,
                        via=bool(via_at(x, y)), tee=tee, pour=bool(in_pour(layer, x, y, lst[0][0].GetNetCode())), width=round(T(lst[0][0].GetWidth()), 2)))

entries = []   # a track that ends inside a non-round pad and is not lined up with one of the pad's axes
for t in segs:
    for p_end, q_end in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
        p = pad_at(t.GetLayer(), p_end.x, p_end.y, t.GetNetCode())
        if not p or p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE: continue
        d = math.degrees(math.atan2(-(q_end.y - p_end.y), q_end.x - p_end.x))
        rel = (d - p.GetOrientationDegrees()) % 90
        off = min(rel, 90 - rel)
        if off > 1.0:
            entries.append(dict(pad=p.GetParent().Cast().GetReference() + "." + p.GetNumber(), net=t.GetNetname(), off=round(off, 1),
                                x=round(T(p_end.x) - OX, 3), y=round(T(p_end.y) - OY, 3), layer=b.GetLayerName(t.GetLayer())))

cnt = collections.Counter(c["kind"] for c in corners)
print("track nodes:", len(corners), dict(cnt))
for k in ("acute", "right"):
    sel = [c for c in corners if c["kind"] == k]
    print(f"\n{k} corners: {len(sel)}  (at a pad: {sum(1 for c in sel if c['pad'])}, at a via: {sum(1 for c in sel if c['via'])}, "
          f"in a pour: {sum(1 for c in sel if c['pour'] and not c['pad'])}, T joints: {sum(1 for c in sel if c['tee'] and not c['pad'])}, "
          f"open bends: {sum(1 for c in sel if not (c['pad'] or c['via'] or c['pour'] or c['tee']))})")
    for c in sorted(sel, key=lambda c: (c["net"], c["x"])):
        print(f"  {c['net']:12s} {c['layer']:5s} ({c['x']:6.2f}, {c['y']:6.2f}) {c['angle']:5.1f} deg  w {c['width']}  segs {c['n']}"
              + (f"  pad {c['pad']}" if c['pad'] else "") + ("  via" if c['via'] else "") + ("  in pour" if c['pour'] else "") + ("  T joint" if c['n'] == 3 and c['tee'] else ""))
print(f"\nangled pad entries: {len(entries)}")
for e in sorted(entries, key=lambda e: e["pad"]): print(f"  {e['pad']:8s} {e['net']:12s} {e['off']:5.1f} deg off axis at ({e['x']}, {e['y']})")
if len(sys.argv) > 2: json.dump(dict(corners=corners, entries=entries), open(sys.argv[2], "w"), indent=1)
