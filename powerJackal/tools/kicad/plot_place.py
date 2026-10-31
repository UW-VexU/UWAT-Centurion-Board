"""Quick placement plot: courtyards, pads coloured by net, ratsnest (MST per net, GND faint), plus overlap and keepout checks."""
import sys, math, colorsys, hashlib
import pcbnew
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from pcb_common import *

brd = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]
show_tracks = len(sys.argv) > 3
zoom = [float(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
T = pcbnew.ToMM
def P(v): return (T(v.x) - OX, T(v.y) - OY)

def court(fp):
    pts = []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            if g.GetShape() == pcbnew.SHAPE_T_SEGMENT: pts += [P(g.GetStart()), P(g.GetEnd())]
            elif g.GetShape() == pcbnew.SHAPE_T_RECT:
                pts += [P(c) for c in g.GetCorners()]
            elif g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                c = P(g.GetCenter()); r = T(g.GetRadius()); pts += [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)]
            else:
                bb = g.GetBoundingBox(); pts += [P(bb.GetOrigin()), P(bb.GetEnd())]
    if not pts:
        for pd in fp.Pads():
            bb = pd.GetBoundingBox(); pts += [P(bb.GetOrigin()), P(bb.GetEnd())]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))

def col(n):
    h = int(hashlib.md5(n.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    return colorsys.hsv_to_rgb(h, 0.75, 0.85)

fig, ax = plt.subplots(figsize=(16, 16 * H / W + 0.6), dpi=110)
ax.add_patch(plt.Rectangle((0, 0), W, H, fill=False, lw=1.5, ec="k"))
for (hx, hy) in HOLES: ax.add_patch(Circle((hx, hy), 4.58, fill=False, ls="--", ec="gray"))
boxes = {}
for fp in brd.GetFootprints():
    ref = fp.GetReference()
    bb = court(fp); boxes[ref] = bb
    ax.add_patch(plt.Rectangle((bb[0], bb[1]), bb[2] - bb[0], bb[3] - bb[1], fill=False, lw=0.6, ec="#888"))
    for pd in fp.Pads():
        n = pd.GetNetname()
        poly = pd.GetEffectivePolygon()
        try:
            o = poly.Outline(0); pts = [P(o.CPoint(i)) for i in range(o.PointCount())]
        except Exception:
            c = P(pd.GetPosition()); s = (T(pd.GetSize().x) / 2, T(pd.GetSize().y) / 2); pts = [(c[0] - s[0], c[1] - s[1]), (c[0] + s[0], c[1] - s[1]), (c[0] + s[0], c[1] + s[1]), (c[0] - s[0], c[1] + s[1])]
        fc = "#bbb" if not n else ("#556" if n == "GND" else col(n))
        ax.add_patch(Polygon(pts, closed=True, fc=fc, ec="none", alpha=0.9))
    c = P(fp.GetPosition())
    ax.text((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, ref, fontsize=(14 if zoom else 7), ha="center", va="center", color="k", weight="bold", alpha=0.75, clip_on=True)

if show_tracks:
    for t in brd.GetTracks():
        a, b2 = P(t.GetStart()), P(t.GetEnd())
        if t.GetClass() == "PCB_VIA":
            ax.add_patch(Circle(a, T(t.GetWidth()) / 2, fc="#c90", ec="k", lw=0.3))
            if zoom: ax.text(a[0], a[1], t.GetNetname().strip("/")[:6], fontsize=6, ha="center", va="center", clip_on=True)
        else:
            ax.plot([a[0], b2[0]], [a[1], b2[1]], color=("#d33" if t.GetLayer() == pcbnew.F_Cu else "#33d"), lw=T(t.GetWidth()) * (3.2 * (4 if zoom else 1)), alpha=0.6, solid_capstyle="round")
else:
    # ratsnest
    nets = {}
    for pd in brd.GetPads():
        n = pd.GetNetname()
        if n: nets.setdefault(n, []).append(P(pd.GetPosition()))
    total = 0
    for n, pts in nets.items():
        if len(pts) < 2: continue
        inT = {0}; d = {i: math.dist(pts[0], pts[i]) for i in range(1, len(pts))}; par = {i: 0 for i in d}
        while d:
            i = min(d, key=d.get); inT.add(i)
            a, b2 = pts[par[i]], pts[i]
            if n == "GND": ax.plot([a[0], b2[0]], [a[1], b2[1]], color="#999", lw=0.3, alpha=0.5)
            else: ax.plot([a[0], b2[0]], [a[1], b2[1]], color=col(n), lw=0.9); total += math.dist(a, b2)
            del d[i]
            for j in d:
                dj = math.dist(pts[i], pts[j])
                if dj < d[j]: d[j] = dj; par[j] = i
    print("ratsnest length (no GND): %.0f mm" % total)

ax.set_xticks(range(0, int(W) + 1, 5)); ax.set_yticks(range(0, int(H) + 1, 5))
ax.set_aspect("equal"); ax.grid(True, lw=0.2)
ax.set_xlim(-2, W + 2); ax.set_ylim(H + 2, -2)
if zoom: ax.set_xlim(zoom[0], zoom[2]); ax.set_ylim(zoom[3], zoom[1])
plt.tight_layout(); plt.savefig(out)

# checks
refs = sorted(boxes)
for i, a in enumerate(refs):
    A = boxes[a]
    for b2 in refs[i + 1:]:
        B = boxes[b2]
        ov = min(A[2], B[2]) - max(A[0], B[0]), min(A[3], B[3]) - max(A[1], B[1])
        if ov[0] > 0.05 and ov[1] > 0.05: print(f"OVERLAP {a} {b2} {ov[0]:.2f} x {ov[1]:.2f}")
    if not a.startswith("H"):
        for (hx, hy) in HOLES:
            dx = max(A[0] - hx, 0, hx - A[2]); dy = max(A[1] - hy, 0, hy - A[3])
            if math.hypot(dx, dy) < 4.6: print(f"HOLE {a} near hole at {hx},{hy}")
        if A[0] < -0.6 or A[1] < -0.6 or A[2] > W + 0.6 or A[3] > H + 0.6: print(f"OUTSIDE {a} {A}")
