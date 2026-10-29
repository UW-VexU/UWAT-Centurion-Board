"""Junction audit: taps that land mid-segment, same-net overlapping runs, and joints where different widths meet away from a pad.
usage: python3 junctions.py board.kicad_pcb"""
import sys, math, collections
import pcbnew
from pcb_common import OX, OY
b = pcbnew.LoadBoard(sys.argv[1]); T = pcbnew.ToMM
segs = [(T(t.GetStart().x) - OX, T(t.GetStart().y) - OY, T(t.GetEnd().x) - OX, T(t.GetEnd().y) - OY, T(t.GetWidth()), t.GetLayer(), t.GetNetname())
        for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
pads = list(b.GetPads())
def in_pad(x, y, layer, net):
    v = pcbnew.VECTOR2I(pcbnew.FromMM(x + OX), pcbnew.FromMM(y + OY))
    return any(p.GetNetname() == net and p.IsOnLayer(layer) and p.HitTest(v) for p in pads)
vias = {(round(T(t.GetPosition().x) - OX, 3), round(T(t.GetPosition().y) - OY, 3)) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"}
def on_interior(px, py, s, tol=0.01):
    ax, ay, bx, by = s[:4]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
    if L < 1e-6: return False
    k = ((px - ax) * dx + (py - ay) * dy) / (L * L)
    if k <= 0.001 or k >= 0.999: return False
    return abs((px - ax) * dy - (py - ay) * dx) / L < tol
mid, over = [], []
for i, s in enumerate(segs):
    for (px, py) in ((s[0], s[1]), (s[2], s[3])):
        for j, o in enumerate(segs):
            if i != j and o[5] == s[5] and o[6] == s[6] and on_interior(px, py, o) and not in_pad(px, py, s[5], s[6]):
                mid.append((s[6], b.GetLayerName(s[5]), round(px, 3), round(py, 3)))
    for j in range(i + 1, len(segs)):
        o = segs[j]
        if o[5] != s[5] or o[6] != s[6]: continue
        # collinear overlap: both ends of one on the line of the other and the spans intersect
        if (on_interior(o[0], o[1], s) or on_interior(o[2], o[3], s)) and abs((o[2] - o[0]) * (s[3] - s[1]) - (o[3] - o[1]) * (s[2] - s[0])) < 1e-3:
            over.append((s[6], b.GetLayerName(s[5]), [round(v, 3) for v in s[:4]], [round(v, 3) for v in o[:4]]))
node = collections.defaultdict(set)
for s in segs:
    for (px, py) in ((s[0], s[1]), (s[2], s[3])): node[(round(px, 3), round(py, 3), s[5], s[6])].add(s[4])
mixed = [(k[3], b.GetLayerName(k[2]), k[0], k[1], sorted(w)) for k, w in node.items() if len(w) > 1 and not in_pad(k[0], k[1], k[2], k[3]) and (k[0], k[1]) not in vias]
print("mid-segment taps:", len(mid)); [print("  ", m) for m in sorted(set(mid))]
print("overlapping runs:", len(over)); [print("  ", m) for m in over]
print("mixed widths at a joint:", len(mixed)); [print("  ", m) for m in sorted(mixed)]
