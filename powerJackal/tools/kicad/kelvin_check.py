"""Check that no routed (unlocked) copper touches the INA226 Kelvin sense lines, and report USB pair lengths."""
import sys, math
import pcbnew
from pcb_common import *
from pcb_place import PLACE, rot_pt
from gen_pcb import SENSE

b = pcbnew.LoadBoard(sys.argv[1])
T = pcbnew.ToMM
def seg_pt_dist(a, c, p):
    ax, ay = a; bx, by = c; px, py = p
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
bad = 0
for u, r, c in SENSE:
    ux, uy, ur = PLACE[u]
    G = lambda lx, ly: (ux + rot_pt(lx, ly, ur)[0], uy + rot_pt(lx, ly, ur)[1])
    sense = [[G(2.2, -1.0), G(3.25, -1.0), G(3.25, -2.55), G(4.9, -2.55), G(4.9, -3.15)],
             [G(2.2, -0.5), G(3.75, -0.5), G(3.75, -1.65), G(4.9, -1.65), G(4.9, -1.05)]]
    for path in sense:
        for t in tracks:
            if t.IsLocked(): continue
            for end in (toloc(t.GetStart()), toloc(t.GetEnd())):
                for a, c2 in zip(path, path[1:]):
                    if seg_pt_dist(a, c2, end) < 0.15:
                        bad += 1; print(f"{u}: routed {t.GetNetname()} track ends on a sense line at {end[0]:.2f},{end[1]:.2f}")
print("Kelvin lines clean" if bad == 0 else f"{bad} problems")
for n in ("/USB_DP", "/USB_DN"):
    L = sum(T(t.GetLength()) for t in tracks if t.GetNetname() == n)
    vias = sum(1 for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == n)
    print(f"{n}: {L:.1f} mm of track, {vias} vias")
