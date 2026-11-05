"""Coupling involving In2.Cu traces: side by side on In2, and stacked In2 <-> B.Cu (0.1 mm apart). Read-only."""
import pcbnew, math, collections, sys, json, os
B = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.ToMM
segs = []
for t in B.GetTracks():
    if t.GetClass() != "PCB_TRACK": continue
    a, b = t.GetStart(), t.GetEnd()
    segs.append(dict(net=t.GetNetname(), layer=t.GetLayerName(), w=mm(t.GetWidth()), a=(mm(a.x), mm(a.y)), b=(mm(b.x), mm(b.y))))
skip = lambda n: n in ("GND", "+3.3V", "+5V", "SENS_3V3", "SENS_5V")

def par(s1, s2, maxgap):
    ax, ay = s1["a"]; bx, by = s1["b"]; dx, dy = bx - ax, by - ay; L1 = math.hypot(dx, dy)
    cx, cy = s2["a"]; ex, ey = s2["b"]; fx, fy = ex - cx, ey - cy; L2 = math.hypot(fx, fy)
    if L1 < 0.05 or L2 < 0.05: return None
    ux, uy = dx / L1, dy / L1
    if abs(ux * fy / L2 - uy * fx / L2) > math.sin(math.radians(12)): return None
    t1 = (cx - ax) * ux + (cy - ay) * uy; t2 = (ex - ax) * ux + (ey - ay) * uy
    lo, hi = max(0, min(t1, t2)), min(L1, max(t1, t2))
    if hi - lo < 0.2: return None
    d = (abs((cx - ax) * uy - (cy - ay) * ux) + abs((ex - ax) * uy - (ey - ay) * ux)) / 2
    if d - (s1["w"] + s2["w"]) / 2 > maxgap: return None
    return hi - lo, d

res = collections.defaultdict(lambda: [0.0, 9.0, None])
in2 = [s for s in segs if s["layer"] == "In2.Cu"]
bcu = [s for s in segs if s["layer"] == "B.Cu"]
for i, s1 in enumerate(in2):                      # side by side on In2
    for s2 in in2[i + 1:]:
        if s1["net"] == s2["net"] or skip(s1["net"]) or skip(s2["net"]): continue
        c = par(s1, s2, 0.75)
        if c:
            k = ("In2|In2",) + tuple(sorted((s1["net"], s2["net"])))
            res[k][0] += c[0]; res[k][1] = min(res[k][1], c[1]); res[k][2] = res[k][2] or s1["a"]
for s1 in in2:                                     # stacked In2 / B.Cu, lateral offset up to 1 mm
    for s2 in bcu:
        if s1["net"] == s2["net"] or skip(s1["net"]) or skip(s2["net"]): continue
        c = par(s1, s2, 1.0)
        if c:
            k = ("In2|B.Cu",) + tuple(sorted((s1["net"], s2["net"])))
            res[k][0] += c[0]; res[k][1] = min(res[k][1], c[1]); res[k][2] = res[k][2] or s1["a"]
rows = []
for (kind, a, b), (ln, d, at) in res.items():
    vert = 0.1 if kind == "In2|B.Cu" else 0.0
    D = math.hypot(d, vert)
    h = 0.135                                       # to the nearest plane-like copper; rough
    K = 1 / (1 + (D / h) ** 2)
    rows.append(dict(kind=kind, a=a, b=b, len=round(ln, 2), lateral=round(d, 3), K=round(K, 3), at=[round(v, 1) for v in at]))
rows.sort(key=lambda r: -(r["K"] * min(r["len"], 30)))
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "xtalk_inner.json"), "w"), indent=1)
for r in rows[:30]:
    print("%-9s %-24s %-24s len %6.2f lateral %.3f K %.3f at %s" % (r["kind"], r["a"][:24], r["b"][:24], r["len"], r["lateral"], r["K"], r["at"]))
# B.Cu pour coverage over In2 traces (what the In2 traces see on their near side)
bf = [z.GetFilledPolysList(B.GetLayerID("B.Cu")) for z in B.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(B.GetLayerID("B.Cu")) and z.IsFilled() and z.GetNetname() == "GND"]
tot = cov = 0.0
for s in in2:
    L = math.dist(s["a"], s["b"]); n = max(1, int(L / 0.25))
    for i in range(n):
        x = s["a"][0] + (s["b"][0] - s["a"][0]) * (i + .5) / n; y = s["a"][1] + (s["b"][1] - s["a"][1]) * (i + .5) / n
        tot += L / n
        if any(p.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))) for p in bf): cov += L / n
print("In2 trace length %.0f mm, with B.Cu GND pour directly under it for %.0f mm (%.0f%%)" % (tot, cov, 100 * cov / max(tot, 1)))
