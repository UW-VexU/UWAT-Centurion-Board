"""Write powerJackal.kicad_sch (KiCad 7 format) from jackal_design.py. Every pin gets a short wire and a net label,
GND pins get a GND symbol, unused pins get a no-connect flag. Parts are packed into titled blocks."""
import re, sys, uuid, json, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from symlib import flat_symbol, pins_of, find_symbol
import jackal_design as D

OUTDIR = sys.argv[1]
PROJ = "powerJackal"
NS = uuid.UUID("6f1d0c3e-6a0b-4c55-9d2e-6a0a3b7c1e01")
U = lambda *k: str(uuid.uuid5(NS, "/".join(map(str, k))))
ROOT = U("root")
_LIBSYM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lib", "UWAT.kicad_sym")
UWAT_LIB = open(_LIBSYM).read() if os.path.exists(_LIBSYM) else None

def lib_text(lib_id):
    lib, name = lib_id.split(":")
    if lib == "UWAT":
        return find_symbol(UWAT_LIB, name).replace('(symbol "%s"' % name, '(symbol "UWAT:%s"' % name, 1)
    return flat_symbol(lib, name)

g = lambda v: round(v / 1.27) * 1.27  # snap to the 50 mil grid
def fmt(v): return f"{v:.4f}".rstrip("0").rstrip(".")

# ---------- collect symbol definitions
used = {p["lib"] for p in D.PARTS} | {"power:GND", "power:PWR_FLAG"}
LIBSYM = {lid: lib_text(lid) for lid in sorted(used)}
PINS = {lid: pins_of(t) for lid, t in LIBSYM.items()}

def body_bbox(lid):
    t = LIBSYM[lid]
    t = re.sub(r'\(pin .*?\(number "[^"]*"[^)]*\)\s*\)\s*\)', '', t, flags=re.S)
    pts = [(float(a), float(b)) for a, b in re.findall(r'\((?:start|end|xy|center|mid) ([-\d.]+) ([-\d.]+)\)', t)]
    rad = [float(r) for r in re.findall(r'\(radius ([\d.]+)\)', t)]
    if not pts: return (-1.27, -1.27, 1.27, 1.27)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; r = max(rad) if rad else 0
    return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)

def xf(rot, px, py):  # library -> screen offset
    return (px, -py) if rot == 0 else (-px, py)

def outward(rot, ang):
    d = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[ang]  # screen, rot 0
    return d if rot == 0 else (-d[0], -d[1])

CW = 1.0  # label character width, mm
def label_len(n): return len(n) * CW + 1.5

# ---------- per part geometry (relative to the symbol origin)
def part_geom(p):
    lid, rot = p["lib"], p["rot"]
    pins = PINS[lid]
    items = []  # (sx, sy, dir, net)
    seen = {}
    for num, lst in pins.items():
        for (px, py, ang, name, et) in lst:
            if num not in p["pins"] and lid not in ("Mechanical:MountingHole",):
                raise KeyError(f"{p['ref']} pin {num} ({name}) has no net in the design")
            net = p["pins"].get(num)
            if et == "no_connect":  # module NC or DNC pin: typed no-connect in the symbol, so it needs no flag
                if net is not None: raise ValueError(f"{p['ref']} pin {num} is a no-connect pin but has net {net}")
                continue
            sx, sy = xf(rot, px, py)
            key = (round(sx, 3), round(sy, 3))
            if key in seen:
                if seen[key] != net: raise ValueError(f"{p['ref']} stacked pins at {key} have nets {seen[key]} and {net}")
                continue
            seen[key] = net
            items.append((sx, sy, outward(rot, ang), net))
    bx0, by0, bx1, by1 = body_bbox(lid)
    (ax, ay), (bx, by) = xf(rot, bx0, by0), xf(rot, bx1, by1)
    body = (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))
    # drawing plan: stubs, labels, ground symbols, no-connects (part relative)
    plan = []
    hg = {}  # sideways ground pins grouped by side
    for it in items:
        sx, sy, (dx, dy), net = it
        if net is None: plan.append(("nc", sx, sy)); continue
        ex, ey = sx + dx * 2.54, sy + dy * 2.54
        if net == "GND" and dx:
            hg.setdefault((dx, round(sx, 2)), []).append(it); continue
        plan.append(("wire", sx, sy, ex, ey))
        plan.append(("gnd", ex, ey, (0, dy)) if net == "GND" else ("label", net, ex, ey, (dx, dy)))
    for (dx, sxk), grp in hg.items():  # every ground symbol hangs downward; sideways pins run out past their neighbours' labels
        grp.sort(key=lambda i: i[1])
        chains = [[grp[0]]]
        for it in grp[1:]:
            if it[1] - chains[-1][-1][1] <= 2.55: chains[-1].append(it)
            else: chains.append([it])
        for ch in chains:
            ybot = ch[-1][1]
            near = [i for i in items if i[2][0] == dx and abs(i[0] - sxk) < 0.1 and ybot < i[1] <= ybot + 5.6 and i[3] is not None]
            L = max([0 if i[3] == "GND" else label_len(i[3]) for i in near], default=None)
            ext = 2.54 + (L + 2.54 if L is not None else 0)
            xe = sxk + dx * ext
            for i in ch: plan.append(("wire", i[0], i[1], xe, i[1]))
            for a, b in zip(ch, ch[1:]): plan.append(("wire", xe, a[1], xe, b[1]))
            for i in ch[1:]: plan.append(("junc", xe, i[1]))
            plan.append(("gnd", xe, ybot, (0, 1)))
    # extents
    x0, y0, x1, y1 = body
    def grow(a, b, c, d):
        nonlocal x0, y0, x1, y1
        x0, y0, x1, y1 = min(x0, a), min(y0, b), max(x1, c), max(y1, d)
    for pr in plan:
        if pr[0] == "nc": grow(pr[1] - 1, pr[2] - 1, pr[1] + 1, pr[2] + 1)
        elif pr[0] == "wire": grow(min(pr[1], pr[3]), min(pr[2], pr[4]), max(pr[1], pr[3]), max(pr[2], pr[4]))
        elif pr[0] == "gnd":
            x, y, (_, dy) = pr[1], pr[2], pr[3]
            grow(x - 1.8, min(y, y + dy * 4.7), x + 1.8, max(y, y + dy * 4.7))
        elif pr[0] == "label":
            _, net, x, y, (dx, dy) = pr; L = label_len(net)
            if dx: grow(min(x, x + dx * L), y - 1.6, max(x, x + dx * L), y + 0.6)
            else: grow(x - 1.6, min(y, y + dy * L), x + 0.6, max(y, y + dy * L))
    # fields
    narrow = (body[2] - body[0]) < 6 and any(dy for *_, (dx, dy), _ in [(i[0], i[1], i[2], i[3]) for i in items])
    right_pins = any(dx > 0 for *_, (dx, dy), _ in items)
    if narrow and right_pins:  # fields stacked above the body, right of the top stub
        fld = [(body[2] + 0.6, body[1] - 3.81, "left"), (body[2] + 0.6, body[1] - 1.27, "left")]
        y0 = min(y0, body[1] - 5.2)
        x1 = max(x1, body[2] + 0.6 + max(len(p["ref"]), len(p["value"])) * CW * 1.05)
    elif narrow:
        fld = [(body[2] + 1.27, -1.27, "left"), (body[2] + 1.27, 1.27, "left")]
        x1 = max(x1, body[2] + 1.27 + max(len(p["ref"]), len(p["value"])) * CW * 1.05)
    elif len(items) == 2 and hg:  # two-pin part with a hanging ground: both fields above the body
        fld = [(body[0], body[1] - 3.81, "left"), (body[0], body[1] - 1.27, "left")]
        y0 = min(y0, body[1] - 5.2)
        x1 = max(x1, body[0] + max(len(p["ref"]), len(p["value"])) * CW * 1.05)
    else:
        def clear_x(txt, dy):  # start the field right of any vertical stub it would cross
            xs = body[0]
            for _ in range(4):
                hit = [sx for sx, sy, (dx, ddy), net in items if ddy == dy and net is not None and xs - 1.0 < sx < xs + len(txt) * CW * 1.05 + 1.0]
                if not hit: break
                xs = max(hit) + 2.0
            return xs
        rx_, vx_ = clear_x(p["ref"], -1), clear_x(p["value"], 1)
        fld = [(rx_, body[1] - 1.27, "left"), (vx_, body[3] + 2.54, "left")]
        x1 = max(x1, rx_ + len(p["ref"]) * CW * 1.05, vx_ + len(p["value"]) * CW * 1.05)
        y0 = min(y0, body[1] - 2.8); y1 = max(y1, body[3] + 3.4)
        x1 = max(x1, body[0] + max(len(p["ref"]), len(p["value"])) * CW * 1.05)
    return dict(items=items, plan=plan, bbox=(x0, y0, x1, y1), fields=fld, body=body)

# ---------- layout: pack parts into blocks (bottom-left skyline, keeps design order)
GEOM = {p["ref"]: part_geom(p) for p in D.PARTS}
POS = {}
GAP = 3.81
for bid, title, (bx, by), (bw, bh) in D.BLOCKS:
    parts = [p for p in D.PARTS if p["block"] == bid]
    left, top, right = bx + 3.81, by + 11.43 + (len(D.NOTES.get(bid, [])) * 3.0), bx + bw - 2.54
    placed = []  # (x0, y0, x1, y1) in sheet coordinates
    for p in parts:
        x0, y0, x1, y1 = GEOM[p["ref"]]["bbox"]
        w, h = x1 - x0, y1 - y0
        xs = sorted({left} | {r[2] + GAP for r in placed})
        ys = sorted({top} | {r[3] + GAP for r in placed})
        best = None
        for cy in ys:
            for cx in xs:
                if cx + w > right: continue
                ox, oy = g(cx - x0 + 1.27), g(cy - y0 + 1.27)
                R = (ox + x0, oy + y0, ox + x1, oy + y1)
                if R[0] < left - 0.01: continue
                if any(R[0] < q[2] + 1.27 and q[0] < R[2] + 1.27 and R[1] < q[3] + 1.27 and q[1] < R[3] + 1.27 for q in placed): continue
                best = (ox, oy, R); break
            if best: break
        if not best: raise SystemExit(f"cannot place {p['ref']} in block {bid}")
        POS[p["ref"]] = best[:2]; placed.append(best[2])
    bottom = max(r[3] for r in placed)
    if bottom > by + bh - 1.27: print(f"WARNING block {bid} overflows by {bottom - by - bh + 1.27:.1f} mm")

# ---------- overlap check between placed parts
boxes = []
for p in D.PARTS:
    X, Y = POS[p["ref"]]; x0, y0, x1, y1 = GEOM[p["ref"]]["bbox"]
    boxes.append((p["ref"], X + x0, Y + y0, X + x1, Y + y1))
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        a, b = boxes[i], boxes[j]
        if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
            print("OVERLAP", a[0], b[0])
    if boxes[i][3] > 409 or boxes[i][4] > 286: print("OFF SHEET", boxes[i])
    if boxes[i][3] > 298 and boxes[i][4] > 252: print("ON TITLE BLOCK", boxes[i])

# ---------- emit
out = []
A = out.append
A(f'(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {ROOT})\n\n  (paper "A3")\n\n')
A(f'  (title_block\n    (title "Jackal: smart port power test board")\n    (date "{datetime.date.today().isoformat()}")\n    (rev "A")\n'
  f'    (company "UWAT VEXU, University of Waterloo")\n    (comment 1 "Centurion board family")\n'
  f'    (comment 2 "Generated from jackal_design.py")\n  )\n\n')
A('  (lib_symbols\n')
for lid, t in LIBSYM.items():
    A("    " + t.replace("\n", "\n    ").rstrip() + "\n")
A('  )\n\n')

pwr_n = [0]
GND_ROT = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}
def gnd_symbol(x, y, d=(0, 1)):
    pwr_n[0] += 1; ref = f"#PWR{pwr_n[0]:03d}"; uid = U("pwr", ref)
    rot = GND_ROT[d]
    vx, vy = x + d[0] * 3.3, y + d[1] * 3.81 + (0.5 if d[0] else 0)
    vj = "" if d[0] == 0 else (" (justify left)" if d[0] > 0 else " (justify right)")
    fa = 90 if d[0] else 0
    A(f'  (symbol (lib_id "power:GND") (at {fmt(x)} {fmt(y)} {rot}) (unit 1)\n    (in_bom yes) (on_board yes) (dnp no)\n    (uuid {uid})\n'
      f'    (property "Reference" "{ref}" (at {fmt(x)} {fmt(y + 6.35)} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )\n'
      f'    (property "Value" "GND" (at {fmt(vx)} {fmt(vy)} {fa})\n      (effects (font (size 1.27 1.27)){vj})\n    )\n'
      f'    (property "Footprint" "" (at {fmt(x)} {fmt(y)} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )\n'
      f'    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )\n'
      f'    (pin "1" (uuid {U("pwrpin", ref)}))\n    (instances\n      (project "{PROJ}"\n        (path "/{ROOT}" (reference "{ref}") (unit 1))\n      )\n    )\n  )\n')

def wire(x0, y0, x1, y1):
    A(f'  (wire (pts (xy {fmt(x0)} {fmt(y0)}) (xy {fmt(x1)} {fmt(y1)}))\n    (stroke (width 0) (type default))\n    (uuid {U("w", x0, y0, x1, y1)})\n  )\n')

def label(net, x, y, d):
    ang, just = {(-1, 0): (180, "right"), (1, 0): (0, "left"), (0, -1): (90, "left"), (0, 1): (270, "right")}[d]
    A(f'  (label "{net}" (at {fmt(x)} {fmt(y)} {ang}) (fields_autoplaced)\n    (effects (font (size 1.27 1.27)) (justify {just} bottom))\n    (uuid {U("l", net, x, y)})\n  )\n')

def text(s, x, y, size=1.27, bold=False):
    s = s.replace('"', "'")
    A(f'  (text "{s}" (at {fmt(x)} {fmt(y)} 0)\n    (effects (font (size {size} {size}){" bold" if bold else ""}) (justify left bottom))\n    (uuid {U("t", s, x, y)})\n  )\n')

def box(x0, y0, x1, y1):
    A(f'  (polyline (pts (xy {fmt(x0)} {fmt(y0)}) (xy {fmt(x1)} {fmt(y0)}) (xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x0)} {fmt(y1)}) (xy {fmt(x0)} {fmt(y0)}))\n'
      f'    (stroke (width 0) (type dash))\n    (uuid {U("box", x0, y0)})\n  )\n')

# blocks: frame, title, notes
for bid, title, (bx, by), (bw, bh) in D.BLOCKS:
    box(bx, by, bx + bw, by + bh)
    text(title, bx + 2.54, by + 5.08, 2.0, True)
    for i, line in enumerate(D.NOTES.get(bid, [])):
        text(line, bx + 2.54, by + 9.4 + i * 3.0, 1.27)

# parts
for p in D.PARTS:
    ref = p["ref"]; X, Y = POS[ref]; G = GEOM[ref]; uid = U("sym", ref)
    for pr in G["plan"]:
        if pr[0] == "nc": A(f'  (no_connect (at {fmt(X + pr[1])} {fmt(Y + pr[2])}) (uuid {U("nc", ref, pr[1], pr[2])}))\n')
        elif pr[0] == "wire": wire(X + pr[1], Y + pr[2], X + pr[3], Y + pr[4])
        elif pr[0] == "junc": A(f'  (junction (at {fmt(X + pr[1])} {fmt(Y + pr[2])}) (diameter 0) (color 0 0 0 0)\n    (uuid {U("j", ref, pr[1], pr[2])})\n  )\n')
        elif pr[0] == "gnd": gnd_symbol(X + pr[1], Y + pr[2], pr[3])
        elif pr[0] == "label": label(pr[1], X + pr[2], Y + pr[3], pr[4])
    (rx, ry, rj), (vx, vy, vj) = G["fields"]
    props = [("Reference", ref, X + rx, Y + ry, False), ("Value", p["value"], X + vx, Y + vy, False),
             ("Footprint", p["fp"], X, Y, True), ("Datasheet", "", X, Y, True),
             ("MPN", p["mpn"], X, Y, True), ("Manufacturer", p["mfr"], X, Y, True)]
    if p["note"]: props.append(("Note", p["note"], X, Y, True))
    A(f'  (symbol (lib_id "{p["lib"]}") (at {fmt(X)} {fmt(Y)} {p["rot"]}) (unit 1)\n'
      f'    (in_bom {"yes" if p["in_bom"] else "no"}) (on_board yes) (dnp {"yes" if p["dnp"] else "no"})\n    (uuid {uid})\n')
    for k, v, x, y, hide in props:
        v = v.replace('"', "'")
        just = "" if hide else " (justify left)"
        A(f'    (property "{k}" "{v}" (at {fmt(x)} {fmt(y)} 0)\n      (effects (font (size 1.27 1.27)){just}{" hide" if hide else ""})\n    )\n')
    for num in PINS[p["lib"]]:
        A(f'    (pin "{num}" (uuid {U("pin", ref, num)}))\n')
    A(f'    (instances\n      (project "{PROJ}"\n        (path "/{ROOT}" (reference "{ref}") (unit 1))\n      )\n    )\n  )\n')

# PWR_FLAGs along the bottom of the test point block
bid, title, (bx, by), (bw, bh) = [b for b in D.BLOCKS if b[0] == "tp"][0]
fx, fy = g(bx + 7.62), g(by + bh - 16.51)
FLAG_DX = 10.16
text("Power flags (tell ERC these nets are driven)", bx + 2.54, fy - 8.5, 1.27)
for i, net in enumerate(D.PWR_FLAGS):
    x = g(fx + i * FLAG_DX); ref = f"#FLG{i + 1:02d}"
    A(f'  (symbol (lib_id "power:PWR_FLAG") (at {fmt(x)} {fmt(fy)} 0) (unit 1)\n    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)\n    (uuid {U("flg", net)})\n'
      f'    (property "Reference" "{ref}" (at {fmt(x)} {fmt(fy - 1.905)} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )\n'
      f'    (property "Value" "PWR_FLAG" (at {fmt(x)} {fmt(fy - 3.81)} 0)\n      (effects (font (size 1.27 1.27)))\n    )\n'
      f'    (property "Footprint" "" (at {fmt(x)} {fmt(fy)} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )\n'
      f'    (property "Datasheet" "~" (at {fmt(x)} {fmt(fy)} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )\n'
      f'    (pin "1" (uuid {U("flgpin", net)}))\n    (instances\n      (project "{PROJ}"\n        (path "/{ROOT}" (reference "{ref}") (unit 1))\n      )\n    )\n  )\n')
    wire(x, fy, x, fy + 2.54)
    if net == "GND": gnd_symbol(x, fy + 2.54)
    else: label(net, x, fy + 2.54, (0, 1))

A(f'\n  (sheet_instances\n    (path "/" (page "1"))\n  )\n)\n')
os.makedirs(OUTDIR, exist_ok=True)
open(os.path.join(OUTDIR, f"{PROJ}.kicad_sch"), "w").write("".join(out))
json.dump({"root": ROOT, "symbols": {p["ref"]: U("sym", p["ref"]) for p in D.PARTS}}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "uuids.json"), "w"), indent=1)
print("schematic written,", len(D.PARTS), "parts")
