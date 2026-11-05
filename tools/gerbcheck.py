"""Independent check of exported Gerbers + Excellon drill files against the KiCad board they came from.

The Gerber and drill readers here are written from scratch, not KiCad's plotter, so a bug in KiCad's
export can't hide itself. Each file is rasterised at 25 px/mm, then:
  1. Drills: hole and slot counts per diameter vs the board's vias and through-hole pads.
  2. Layers: copper, mask and paste vs the board's own polygons from pcbnew (0.08 mm tolerance).
  3. Netlist: connectivity rebuilt from the Gerber copper + plated drills only, checked against every
     pad's net. Reports shorts (one copper piece holding two nets) and opens (one net in several pieces).
It also writes preview PNGs drawn from the Gerbers alone.

Expects the files from the main README's "Making Gerber files" steps (Protel extensions, Excellon with
separate PTH/NPTH files, absolute origin). Works for 2- and 4-layer boards.

Usage, with KiCad's Python (it has pcbnew, numpy and Pillow):
  "C:\Program Files\KiCad.0in\python.exe" tools/gerbcheck.py centurion/centurion.kicad_pcb centurion/fab/gerbers [out_dir]
out_dir defaults to <gerber_dir>/../gerbcheck. Exit code 0 = everything matched, 1 = something didn't."""
import sys, os, re, math, glob, collections
import numpy as np
from PIL import Image, ImageDraw
import pcbnew

if len(sys.argv) < 3: sys.exit(__doc__)
BRD, GDIR = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(GDIR)), "gerbcheck")
FAIL = []
S = 25.0                      # px per mm
B = pcbnew.LoadBoard(BRD); mm = pcbnew.ToMM
bb = B.GetBoardEdgesBoundingBox()
X0, Y0 = mm(bb.GetX()) - 1.0, mm(bb.GetY()) - 1.0          # board coords of pixel (0,0)
W, H = int((mm(bb.GetWidth()) + 2) * S), int((mm(bb.GetHeight()) + 2) * S)
def px(bx, by): return ((bx - X0) * S, (by - Y0) * S)        # board coords -> pixel
YSIGN = -1                                                   # gerber y = -board y (checked below)
def gpx(gx, gy): return px(gx, YSIGN * gy)

# ---------------- Gerber reader ----------------
def tokens(txt):
    i, n = 0, len(txt)
    while i < n:
        c = txt[i]
        if c in " \r\n\t": i += 1; continue
        if c == "%":
            j = txt.index("%", i + 1); yield ("ext", txt[i + 1:j]); i = j + 1
        else:
            j = txt.index("*", i); yield ("cmd", txt[i:j].strip()); i = j + 1

def mexpr(e, var):
    e = e.strip()
    for k in sorted(var, key=lambda k: -k):
        e = e.replace("$%d" % k, "(%r)" % var[k])
    e = e.replace("x", "*").replace("X", "*")
    if not re.fullmatch(r"[0-9eE.+\-*/() ]*", e): raise ValueError(e)
    return float(eval(e)) if e else 0.0

def rot(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)

class Gerber:
    def __init__(self, path):
        self.img = Image.new("L", (W, H), 0); self.d = ImageDraw.Draw(self.img)
        self.ap, self.am = {}, {}; self.warn = collections.Counter()
        self.parse(open(path).read())
    def poly(self, pts, on):
        if len(pts) >= 3: self.d.polygon([gpx(*p) for p in pts], fill=255 if on else 0)
    def circle(self, cx, cy, dia, on):
        x, y = gpx(cx, cy); r = dia / 2 * S
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=255 if on else 0)
    def flash(self, a, x, y, on):
        kind, p = self.ap[a]
        if kind == "C": self.circle(x, y, p[0], on)
        elif kind == "R":
            w, h = p[0] / 2, p[1] / 2; self.poly([(x - w, y - h), (x + w, y - h), (x + w, y + h), (x - w, y + h)], on)
        elif kind == "O":
            w, h = p[0], p[1]
            if w > h:
                r = h / 2; self.poly([(x - w / 2 + r, y - r), (x + w / 2 - r, y - r), (x + w / 2 - r, y + r), (x - w / 2 + r, y + r)], on)
                self.circle(x - w / 2 + r, y, h, on); self.circle(x + w / 2 - r, y, h, on)
            else:
                r = w / 2; self.poly([(x - r, y - h / 2 + r), (x + r, y - h / 2 + r), (x + r, y + h / 2 - r), (x - r, y + h / 2 - r)], on)
                self.circle(x, y - h / 2 + r, w, on); self.circle(x, y + h / 2 - r, w, on)
        elif kind == "P":
            dia, nv = p[0], int(p[1]); r0 = p[2] if len(p) > 2 else 0
            self.poly([(x + dia / 2 * math.cos(math.radians(r0 + 360 * k / nv)), y + dia / 2 * math.sin(math.radians(r0 + 360 * k / nv))) for k in range(nv)], on)
        elif kind == "M":
            name, args = p
            var = {i + 1: v for i, v in enumerate(args)}
            for prim in self.am[name]:
                f = prim.split(",")
                if f[0].strip().startswith("$"):          # variable definition
                    k, e = f[0].split("="); var[int(k.strip()[1:])] = mexpr(e, var); continue
                v = [mexpr(t, var) for t in f]
                code = int(v[0])
                if code == 0: continue
                exp = v[1] > 0.5
                if not exp: self.warn["macro exposure off"] += 1
                if code == 1:
                    c = rot((v[3], v[4]), v[5] if len(v) > 5 else 0); self.circle(x + c[0], y + c[1], v[2], on and exp)
                elif code == 20:
                    w, (x1, y1, x2, y2), a = v[2], v[3:7], v[7]
                    L = math.hypot(x2 - x1, y2 - y1) or 1e-9; nx, ny = -(y2 - y1) / L * w / 2, (x2 - x1) / L * w / 2
                    pts = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
                    self.poly([(x + q[0], y + q[1]) for q in (rot(p_, a) for p_ in pts)], on and exp)
                elif code == 21:
                    w, h, cx, cy, a = v[2:7]
                    pts = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
                    self.poly([(x + q[0], y + q[1]) for q in (rot(p_, a) for p_ in pts)], on and exp)
                elif code == 4:
                    nv = int(v[2]); pts = [(v[3 + 2 * k], v[4 + 2 * k]) for k in range(nv + 1)]; a = v[3 + 2 * (nv + 1)]
                    self.poly([(x + q[0], y + q[1]) for q in (rot(p_, a) for p_ in pts)], on and exp)
                elif code == 5:
                    nv, cx, cy, dia, a = int(v[2]), v[3], v[4], v[5], v[6]
                    pts = [(cx + dia / 2 * math.cos(2 * math.pi * k / nv), cy + dia / 2 * math.sin(2 * math.pi * k / nv)) for k in range(nv)]
                    self.poly([(x + q[0], y + q[1]) for q in (rot(p_, a) for p_ in pts)], on and exp)
                else: self.warn["macro primitive %d" % code] += 1
    def arcpts(self, x1, y1, x2, y2, i, j, cw):
        cx, cy = x1 + i, y1 + j; r = math.hypot(i, j)
        a1, a2 = math.atan2(y1 - cy, x1 - cx), math.atan2(y2 - cy, x2 - cx)
        if cw:
            if a2 >= a1 - 1e-9: a2 -= 2 * math.pi
        else:
            if a2 <= a1 + 1e-9: a2 += 2 * math.pi
        n = max(4, int(abs(a2 - a1) * r * S / 2) + 1)
        return [(cx + r * math.cos(a1 + (a2 - a1) * k / n), cy + r * math.sin(a1 + (a2 - a1) * k / n)) for k in range(1, n + 1)]
    def stroke(self, pts, on):
        kind, p = self.ap[self.cur]
        if kind != "C": self.warn["draw with non-circular aperture %s" % kind] += 1
        w = p[0] if kind == "C" else min(p[0], p[1])
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            L = math.hypot(xb - xa, yb - ya)
            if L > 0:
                nx, ny = -(yb - ya) / L * w / 2, (xb - xa) / L * w / 2
                self.poly([(xa + nx, ya + ny), (xb + nx, yb + ny), (xb - nx, yb - ny), (xa - nx, ya - ny)], on)
            self.circle(xb, yb, w, on)
        self.circle(pts[0][0], pts[0][1], w, on)
    def parse(self, txt):
        x = y = 0.0; interp = 1; region = False; contour = []; on = True; self.cur = None; dec = 6
        for kind, t in tokens(txt):
            if kind == "ext":
                for st in [s for s in t.split("*") if s.strip()]:
                    if st.startswith("FS"):
                        m = re.match(r"FSLAX(\d)(\d)Y(\d)(\d)", st); dec = int(m.group(2))
                    elif st.startswith("MO") and st != "MOMM": raise ValueError("units " + st)
                    elif st.startswith("LP"): on = st == "LPD"
                    elif st.startswith("SR") and st not in ("SR", "SRX1Y1I0J0"): self.warn["step-repeat"] += 1
                if t.startswith("AD"):
                    m = re.match(r"ADD(\d+)([A-Za-z_][A-Za-z0-9_.]*),?(.*)", t.rstrip("*"))
                    n, nm, prm = int(m.group(1)), m.group(2), [float(q) for q in m.group(3).split("X") if q.strip()]
                    self.ap[n] = (nm, prm) if nm in ("C", "R", "O", "P") else ("M", (nm, prm))
                elif t.startswith("AM"):
                    parts = [s.strip() for s in t.split("*")]
                    name = parts[0][2:]; self.am[name] = [s for s in parts[1:] if s and not s.startswith("0 ")]
                continue
            if not t or t.startswith("G04"): continue
            if t in ("M02", "M00"): break
            m = re.match(r"^(?:G(\d+))?(.*)$", t); g, rest = m.group(1), m.group(2)
            if g:
                gi = int(g)
                if gi in (1, 2, 3): interp = gi
                elif gi == 36: region, contour = True, []
                elif gi == 37:
                    if len(contour) > 2: self.poly(contour, on)
                    region, contour = False, []
                elif gi == 74: self.warn["single-quadrant arcs"] += 1
            if not rest: continue
            dm = re.match(r"^D(\d+)$", rest)
            if dm and int(dm.group(1)) >= 10: self.cur = int(dm.group(1)); continue
            co = dict((k, int(v) / 10 ** dec) for k, v in re.findall(r"([XYIJ])([+-]?\d+)", rest))
            dd = re.search(r"D0?([123])$", rest); op = int(dd.group(1)) if dd else 1
            nx, ny = co.get("X", x), co.get("Y", y)
            if op == 2:
                if region and len(contour) > 2: self.poly(contour, on)
                if region: contour = [(nx, ny)]
            elif op == 3: self.flash(self.cur, nx, ny, on)
            else:
                seg = [(nx, ny)] if interp == 1 else self.arcpts(x, y, nx, ny, co.get("I", 0), co.get("J", 0), interp == 2)
                if region:
                    if not contour: contour = [(x, y)]
                    contour += seg
                else: self.stroke([(x, y)] + seg, on)
            x, y = nx, ny
    def arr(self): return np.array(self.img) > 127

# ---------------- Excellon reader ----------------
def drills(path):
    tools, hits, slots, cur, metric = {}, [], [], None, True
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith(";"): continue
        m = re.match(r"^T(\d+)C([\d.]+)", ln)
        if m: tools[int(m.group(1))] = float(m.group(2)); continue
        if ln == "INCH": metric = False
        m = re.match(r"^T(\d+)$", ln)
        if m: cur = int(m.group(1)); continue
        m = re.match(r"^X([-\d.]+)Y([-\d.]+)G85X([-\d.]+)Y([-\d.]+)$", ln)
        if m: slots.append((tools[cur],) + tuple(map(float, m.groups()))); continue
        m = re.match(r"^X([-\d.]+)Y([-\d.]+)$", ln)
        if m: hits.append((tools[cur], float(m.group(1)), float(m.group(2))))
    assert metric
    return hits, slots

def poly_raster(ps):
    img = Image.new("L", (W, H), 0); d = ImageDraw.Draw(img)
    ps.Fracture()
    for i in range(ps.OutlineCount()):
        ch = ps.COutline(i); pts = [px(mm(ch.CPoint(k).x), mm(ch.CPoint(k).y)) for k in range(ch.PointCount())]
        if len(pts) > 2: d.polygon(pts, fill=255)
    return np.array(img) > 127

def dilate(a, r):
    o = a.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r: o |= np.roll(np.roll(a, dy, 0), dx, 1)
    return o

def blobs(mask, cell=1.0):
    """coarse clusters of differing pixels: 1 mm cells with > 0.01 mm2 of difference"""
    c = int(cell * S); h, w = mask.shape
    g = mask[: h // c * c, : w // c * c].reshape(h // c, c, w // c, c).sum(axis=(1, 3))
    out = [(g[r, q] / S / S, X0 + (q + 0.5) * cell, Y0 + (r + 0.5) * cell) for r, q in zip(*np.nonzero(g > 0.01 * S * S))]
    return sorted(out, reverse=True)

os.makedirs(OUT, exist_ok=True)
files = {os.path.basename(p): p for p in glob.glob(os.path.join(GDIR, "*"))}
def f(sfx): return [p for n, p in files.items() if n.endswith(sfx)][0]
NCU = B.GetCopperLayerCount()
CUL = [("F.Cu", ".gtl", pcbnew.F_Cu)] + [("In%d.Cu" % k, ".g%d" % k, getattr(pcbnew, "In%d_Cu" % k)) for k in range(1, NCU - 1)] + [("B.Cu", ".gbl", pcbnew.B_Cu)]
for _, sfx, _ in CUL:
    if not any(n.endswith(sfx) for n in files): sys.exit("missing copper file *%s in %s" % (sfx, GDIR))
LAYERS = CUL + [("F.Mask", ".gts", pcbnew.F_Mask), ("B.Mask", ".gbs", pcbnew.B_Mask), ("F.Paste", ".gtp", pcbnew.F_Paste), ("B.Paste", ".gbp", pcbnew.B_Paste)]

# ---- 1. drills ----
pth, pslots = drills(f("-PTH.drl")); npth, nslots = drills(f("-NPTH.drl"))
vias = [(round(mm(t.GetDrill()), 3), mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in B.GetTracks() if t.GetClass() == "PCB_VIA"]
want_p, want_n = collections.Counter(), collections.Counter()
for v in vias: want_p[("hole", v[0])] += 1
for fp in B.GetFootprints():
    for p in fp.Pads():
        if p.GetDrillSize().x == 0: continue
        dx, dy = round(mm(p.GetDrillSize().x), 3), round(mm(p.GetDrillSize().y), 3)
        key = ("hole", dx) if dx == dy else ("slot", min(dx, dy))
        (want_p if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else want_n)[key] += 1
got_p = collections.Counter([("hole", round(h[0], 3)) for h in pth] + [("slot", round(s[0], 3)) for s in pslots])
got_n = collections.Counter([("hole", round(h[0], 3)) for h in npth] + [("slot", round(s[0], 3)) for s in nslots])
print("== Drills (board vs Excellon) ==")
for nm, w_, g_ in (("plated", want_p, got_p), ("non-plated", want_n, got_n)):
    for k in sorted(set(w_) | set(g_)):
        print("  %-10s %-5s %.2f mm   board %4d   file %4d  %s" % (nm, k[0], k[1], w_[k], g_[k], "OK" if w_[k] == g_[k] else "MISMATCH"))
        if w_[k] != g_[k]: FAIL.append("drill %s %s %.2f mm" % (nm, k[0], k[1]))
# y sign check: every via has a drill hit at (x, -y)
vset = {(round(x, 2), round(y, 2)) for _, x, y in vias}
hset = {(round(x, 2), round(YSIGN * y, 2)) for _, x, y in pth}
hxy = [(x, YSIGN * y) for _, x, y in pth]
off = max([min(math.hypot(vx - hx, vy - hy) for hx, hy in hxy) for _, vx, vy in vias] or [0])
print("  worst via-to-drill-hit offset: %.4f mm over %d vias" % (off, len(vias)))
if off > 0.01: FAIL.append("via drill offset %.3f mm" % off)

# ---- 2. raster compare ----
print("== Layer raster compare (Gerber read here vs board polygons), tolerance 0.08 mm ==")
R = {}
for name, sfx, lid in LAYERS:
    g = Gerber(f(sfx)); ga = g.arr(); R[name] = ga
    ps = pcbnew.SHAPE_POLY_SET(); B.ConvertBrdLayerToPolygonalContours(lid, ps); ba = poly_raster(ps)
    extra, missing = ga & ~dilate(ba, 2), ba & ~dilate(ga, 2)
    ea, ma = extra.sum() / S / S, missing.sum() / S / S
    print("  %-8s area gerber %8.1f mm2  board %8.1f mm2   extra %.3f mm2  missing %.3f mm2  %s" % (name, ga.sum() / S / S, ba.sum() / S / S, ea, ma, dict(g.warn) or ""))
    if ea > 0.01 or ma > 0.01: FAIL.append("%s differs (extra %.3f, missing %.3f mm2)" % (name, ea, ma))
    if g.warn: FAIL.append("%s reader warnings %s" % (name, dict(g.warn)))
    for lab, msk in (("extra", extra), ("missing", missing)):
        for a, x, y in blobs(msk)[:5]: print("       %s %.3f mm2 near (%.1f, %.1f)" % (lab, a, x, y))
    Image.fromarray(np.dstack([ga * 255, ba * 255, np.zeros_like(ga, np.uint8)]).astype(np.uint8)).save(os.path.join(OUT, "cmp_%s.png" % name.replace(".", "_")))
edge = Gerber(f(".gm1")).arr(); ys, xs = np.nonzero(edge)
print("  Edge.Cuts outline extent: %.2f x %.2f mm (board edges bbox %.2f x %.2f)" % ((xs.max() - xs.min()) / S, (ys.max() - ys.min()) / S, mm(bb.GetWidth()), mm(bb.GetHeight())))

# ---- 3. netlist test from the Gerbers ----
print("== Netlist test (connectivity from Gerber copper + plated drills vs pad nets) ==")
CU = [n for n, _, _ in CUL]; CUID = [lid for _, _, lid in CUL]
runs = {}
parent = []
def find(a):
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    a, b = find(a), find(b)
    if a != b: parent[b] = a
for L in CU:
    a = R[L]; rows = []
    prev = []
    for r in range(a.shape[0]):
        row = a[r]; d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
        cur = []
        k = 0
        for s, e in zip(st, en):
            idx = len(parent); parent.append(idx); cur.append((s, e, idx))
            while k < len(prev) and prev[k][1] <= s: k += 1
            j = k
            while j < len(prev) and prev[j][0] < e: union(prev[j][2], idx); j += 1
        rows.append(cur); prev = cur
    runs[L] = rows
def node(L, bx, by, search=0.3):
    c0, r0 = px(bx, by)
    for rad in np.arange(0, search * S + 1, 1.0):
        for ang in np.linspace(0, 2 * math.pi, max(1, int(rad * 6)), endpoint=False):
            r, c = int(round(r0 + rad * math.sin(ang))), int(round(c0 + rad * math.cos(ang)))
            if 0 <= r < H:
                for s, e, idx in runs[L][r]:
                    if s <= c < e: return idx
    return None
# plated holes tie the layers together where copper exists at the hole
ties = [(x, YSIGN * y) for _, x, y in pth] + [(x1, YSIGN * y1) for _, x1, y1, x2, y2 in pslots]
for bx, by in ties:
    ns = [node(L, bx, by, search=0.0) for L in CU]; ns = [n for n in ns if n is not None]
    for n in ns[1:]: union(ns[0], n)
group_nets = collections.defaultdict(set); net_groups = collections.defaultdict(set); unplaced = []
for fp in B.GetFootprints():
    for p in fp.Pads():
        net = p.GetNetname() or "<no net %s.%s>" % (fp.GetReference(), p.GetNumber())
        pos = p.GetPosition(); hit = False
        for L, lid in zip(CU, CUID):
            if not p.IsOnLayer(lid): continue
            n = node(L, mm(pos.x), mm(pos.y))
            if n is None: continue
            hit = True; g_ = find(n); group_nets[g_].add(net); net_groups[net].add(g_)
        has_cu = any(p.IsOnLayer(l) for l in CUID)
        if not hit and has_cu and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH: unplaced.append("%s.%s" % (fp.GetReference(), p.GetNumber()))
shorts = [sorted(v) for v in group_nets.values() if len(v) > 1]
opens = {n: len(g) for n, g in net_groups.items() if len(g) > 1}
print("  pads checked: %d   nets: %d   copper groups: %d" % (sum(len(fp.Pads()) for fp in B.GetFootprints()), len(net_groups), len(group_nets)))
print("  shorts (one copper group holding two nets): %d" % len(shorts))
for s in shorts[:20]: print("     ", s)
print("  opens (one net split into separate copper groups): %d" % len(opens))
for n, k in sorted(opens.items())[:30]: print("      %s in %d pieces" % (n, k))
print("  copper pads with no copper found in the Gerbers: %d %s" % (len(unplaced), unplaced[:20]))
if shorts: FAIL.append("%d shorts" % len(shorts))
if opens: FAIL.append("%d opens" % len(opens))
if unplaced: FAIL.append("%d pads missing" % len(unplaced))

# ---- preview render (gerbers only) ----
top = np.full((H, W, 3), (20, 70, 40), np.uint8)
top[R["F.Cu"]] = (190, 160, 60)
m = R["F.Mask"]; top[m & R["F.Cu"]] = (230, 200, 120)
silk = Gerber(f(".gto")).arr(); top[silk] = (245, 245, 245)
top[edge] = (255, 80, 80)
im = Image.fromarray(top); dr = ImageDraw.Draw(im)
for d_, x, y in pth + npth:
    c, r = gpx(x, y); rr = d_ / 2 * S; dr.ellipse([c - rr, r - rr, c + rr, r + rr], fill=(10, 10, 10))
im.save(os.path.join(OUT, "preview_top.png"))
for L in CU: Image.fromarray((~R[L] * 200 + 30).astype(np.uint8)).save(os.path.join(OUT, "layer_%s.png" % L.replace(".", "_")))
print("wrote previews to", OUT)
print()
print("RESULT: " + ("PASS - the Gerbers and drills match the board" if not FAIL else "FAIL - " + "; ".join(FAIL)))
sys.exit(1 if FAIL else 0)
