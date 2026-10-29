"""Run tidy_tracks.py, then DRC; any new clearance problem near a changed corner halves that corner's chamfer, then drops it.
usage: python3 tidy_loop.py in.kicad_pcb out.kicad_pcb workdir"""
import sys, os, re, json, math, subprocess
IN, OUT, WD = sys.argv[1:4]
HERE = os.path.dirname(os.path.abspath(__file__))
from pcb_common import OX, OY
scale = {}; sf = os.path.join(WD, "scale.json")
BAD = ("clearance", "shorting_items", "tracks_crossing", "hole_clearance", "copper_edge_clearance", "track_dangling", "unconnected_items", "via_dangling")
for it in range(6):
    json.dump(scale, open(sf, "w"))
    r = subprocess.run([sys.executable, os.path.join(HERE, "tidy_tracks.py"), IN, OUT + ".tidy.kicad_pcb", sf], capture_output=True, text=True)
    print("pass", it, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-800:])
    r2 = subprocess.run([sys.executable, os.path.join(HERE, "hand_routes.py"), OUT + ".tidy.kicad_pcb", OUT], capture_output=True, text=True)
    if r2.returncode: print(r2.stderr[-1500:]); raise SystemExit("hand_routes failed")
    import shutil; shutil.copy(OUT + ".tidy.kicad_pcb.mods.json", OUT + ".mods.json")
    rep = os.path.join(WD, "drc_loop.txt")
    subprocess.run([sys.executable, os.path.join(HERE, "check.py"), OUT, rep], capture_output=True, text=True)
    txt = open(rep).read()
    unconn = int(re.search(r"Found (\d+) unconnected", txt).group(1))
    blocks = re.split(r"\n(?=\[)", txt)
    pts = []
    for bl in blocks:
        m = re.match(r"\[(\w+)\]", bl)
        if m and m.group(1) in BAD:
            pts += [(float(x) - OX, float(y) - OY, m.group(1)) for x, y in re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\)", bl)]
    mods = json.load(open(OUT + ".mods.json"))
    print("  problems", len(pts), "unconnected", unconn)
    if not pts and unconn == 0: break
    hit = set()
    def dist(md, x, y):
        ps = md.get("pts") or [[md["x"], md["y"]]]
        best = min(math.hypot(px - x, py - y) for px, py in ps)
        for (ax, ay), (bx, by) in zip(ps, ps[1:]):
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            k = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
            best = min(best, math.hypot(ax + k * dx - x, ay + k * dy - y))
        return best
    for (x, y, kind) in pts:
        near = sorted(mods, key=lambda md: dist(md, x, y))
        if near and dist(near[0], x, y) < 2.5: hit.add(near[0]["key"])
        else: print("  problem not near a change:", kind, round(x, 2), round(y, 2))
    for k in hit:
        scale[k] = 0.5 if scale.get(k, 1) == 1 else 0
        print("  ", k, "->", scale[k])
    if not hit: break
