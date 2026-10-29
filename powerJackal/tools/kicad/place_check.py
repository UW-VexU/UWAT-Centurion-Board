"""Placement check before routing: courtyard overlaps (rectangle courtyards, hole courtyards as circles) and parts
sticking out of the board. usage: python3 place_check.py board.kicad_pcb"""
import sys, math
import pcbnew
from pcb_common import *

OVERHANG_OK = {"J1", "J2", "J6", "J9", "J7"}   # edge connectors whose mouths sit at or past the board edge
b = pcbnew.LoadBoard(sys.argv[1])
T = pcbnew.ToMM
rects, circles = {}, {}
for fp in b.GetFootprints():
    ref = fp.GetReference()
    xs, ys = [], []
    for it in fp.GraphicalItems():
        if it.GetLayer() != pcbnew.F_CrtYd: continue
        if it.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c = toloc(it.GetCenter()); circles[ref] = (c[0], c[1], T(it.GetRadius())); break
        bb = it.GetBoundingBox(); xs += [T(bb.GetLeft()) - OX, T(bb.GetRight()) - OX]; ys += [T(bb.GetTop()) - OY, T(bb.GetBottom()) - OY]
    if xs and ref not in circles: rects[ref] = (min(xs), min(ys), max(xs), max(ys))
bad = 0
refs = sorted(rects)
for i, a in enumerate(refs):
    for c in refs[i + 1:]:
        A, B = rects[a], rects[c]
        ox, oy = min(A[2], B[2]) - max(A[0], B[0]), min(A[3], B[3]) - max(A[1], B[1])
        if ox > 0.02 and oy > 0.02: bad += 1; print(f"overlap {a} {c}: {ox:.2f} x {oy:.2f} mm")
for h, (cx, cy, r) in circles.items():
    for a, R in rects.items():
        nx, ny = min(max(cx, R[0]), R[2]), min(max(cy, R[1]), R[3])
        d = math.hypot(cx - nx, cy - ny)
        if d < r - 0.02: bad += 1; print(f"overlap {h} {a}: {r - d:.2f} mm into the hole courtyard")
for a, R in rects.items():
    if a in OVERHANG_OK: continue
    out = max(-R[0], -R[1], R[2] - W, R[3] - H)
    if out > 0.02: bad += 1; print(f"{a} sticks out of the board by {out:.2f} mm")
print("placement problems:", bad)
