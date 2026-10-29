"""List top-layer traces that pass under the body of a part they do not connect to. usage: python under_parts.py board.kicad_pcb"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); T = pcbnew.ToMM
def seg_hits_box(a, c, bx, n=60):
    return any(bx[0] < a[0] + (c[0] - a[0]) * k / n < bx[2] and bx[1] < a[1] + (c[1] - a[1]) * k / n < bx[3] for k in range(n + 1))
segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu]
for fp in b.GetFootprints():
    pts = [g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab and g.GetClass() != "FP_TEXT"]
    if not pts: continue
    x0 = min(T(p.GetLeft()) for p in pts) - 100 + 0.1; y0 = min(T(p.GetTop()) for p in pts) - 100 + 0.1
    x1 = max(T(p.GetRight()) for p in pts) - 100 - 0.1; y1 = max(T(p.GetBottom()) for p in pts) - 100 - 0.1
    own = {p.GetNetname() for p in fp.Pads()}
    hits = sorted({t.GetNetname().lstrip("/") for t in segs if t.GetNetname() not in own and seg_hits_box((T(t.GetStart().x) - 100, T(t.GetStart().y) - 100), (T(t.GetEnd().x) - 100, T(t.GetEnd().y) - 100), (x0, y0, x1, y1))})
    if hits: print(fp.GetReference(), fp.GetValue()[:18], hits)
print("done")
