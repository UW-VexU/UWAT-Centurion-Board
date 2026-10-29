"""Build the Jackal 3D render from the real KiCad board: layer textures from kicad-cli, part placement from the .kicad_pcb.
usage: python3 build_v3.py <board.kicad_pcb> <workdir>"""
import sys, os, json, re, subprocess, base64, io, math
import numpy as np
from PIL import Image
import pcbnew

PCB, WORK = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kicad"))
import jackal_design as D
OX = OY = 100.0
from pcb_common import W, H   # board size follows the KiCad scripts
S = 20  # px per mm
os.makedirs(WORK, exist_ok=True)

# ---------------- layer images
def layer_png(layers, name, scale=None, pcb=None):
    scale = scale or S
    svg = os.path.join(WORK, name + ".svg"); png = os.path.join(WORK, name + ".png")
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "-l", layers, "--black-and-white", "--page-size-mode", "2",
                    "--exclude-drawing-sheet", "--drill-shape-opt", "0", "-o", svg, pcb or PCB], check=True, capture_output=True)
    subprocess.run(["node", os.path.join(HERE, "svg2png.mjs"), svg, png, str(scale)], check=True, capture_output=True, cwd=HERE)
    a = np.asarray(Image.open(png).convert("L")).astype(np.float32) / 255.0
    return 1.0 - a  # 1 where something is drawn

edge = layer_png("Edge.Cuts", "L_edge")
ys, xs = np.nonzero(edge > 0.5)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
sx, sy = (x1 - x0) / (W + 0.1), (y1 - y0) / (H + 0.1)        # edge line is 0.1 mm wide, centred on the outline
ox, oy = x0 + 0.05 * sx, y0 + 0.05 * sy
TW, TH = int(round(W * S)), int(round(H * S))
def crop(a, k=1.0):
    """a was rendered at S*k px/mm; return the board area at S*k px/mm."""
    tw, th = int(round(W * S * k)), int(round(H * S * k))
    im = Image.fromarray((a * 255).astype(np.uint8))
    im = im.transform((tw, th), Image.AFFINE, (W / tw * sx * k, 0, ox * k, 0, H / th * sy * k, oy * k), resample=Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255.0

L = {k: crop(layer_png(v, "L_" + k)) for k, v in
     {"fcu": "F.Cu", "fmask": "F.Mask", "fsilk": "F.SilkS", "bcu": "B.Cu", "bmask": "B.Mask", "bsilk": "B.SilkS"}.items()}

board = pcbnew.LoadBoard(PCB)
holes = []
for p in board.GetPads():
    d = p.GetDrillSize()
    if d.x > 0:
        x, y = pcbnew.ToMM(p.GetPosition().x) - OX, pcbnew.ToMM(p.GetPosition().y) - OY
        holes.append((x, y, pcbnew.ToMM(d.x) / 2, pcbnew.ToMM(d.y) / 2, p.GetOrientationDegrees()))
for v in board.GetTracks():
    if v.GetClass() == "PCB_VIA":
        x, y = pcbnew.ToMM(v.GetPosition().x) - OX, pcbnew.ToMM(v.GetPosition().y) - OY
        r = pcbnew.ToMM(v.GetDrillValue()) / 2; holes.append((x, y, r, r, 0))
def hole_mask(k=1.0, big=False):
  s = S * k; th, tw = int(round(H * s)), int(round(W * s))
  yy, xx = np.mgrid[0:th, 0:tw]
  hole = np.zeros((th, tw), np.float32)
  for (hx, hy, rx, ry, rot) in holes:
    if rx > 2.0 and not big: continue  # mounting holes are cut in the mesh
    cx, cy = hx * s, hy * s
    a = math.radians(-rot); dx, dy = xx - cx, yy - cy
    u, v = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
    if abs(rx - ry) < 1e-3: m = u * u + v * v <= (rx * s) ** 2
    else:  # oval slot
        r = min(rx, ry) * s; half = (max(rx, ry) - min(rx, ry)) * s
        if rx > ry: m = (np.clip(np.abs(u) - half, 0, None) ** 2 + v * v) <= r * r
        else: m = (u * u + np.clip(np.abs(v) - half, 0, None) ** 2) <= r * r
    hole = np.maximum(hole, m.astype(np.float32))
  return hole
hole = hole_mask()

def composite(cu, mask, silk, name, mirror=False):
    rng = np.random.default_rng(3)
    open_ = mask > 0.5
    col = np.zeros((TH, TW, 3), np.float32)
    base = np.array([11, 12, 13], np.float32); trace = np.array([26, 30, 33], np.float32)
    gold = np.array([216, 174, 88], np.float32); silkc = np.array([240, 240, 235], np.float32); fr4 = np.array([96, 82, 46], np.float32)
    col[:] = base
    col += (rng.random((TH, TW, 1)) * 4.0).astype(np.float32)
    c = cu[..., None]
    col = col * (1 - c) + trace * c                                   # copper under the black mask shows faintly
    pad = (open_ & (cu > 0.5))[..., None]
    col = np.where(pad, gold, col)
    bare = (open_ & (cu <= 0.5))[..., None]
    col = np.where(bare, fr4, col)
    s = (silk * (1 - (mask > 0.5)))[..., None]
    col = col * (1 - s) + silkc * s
    h = hole[..., None]
    col = col * (1 - h) + np.array([5, 5, 5], np.float32) * h
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    # roughness (green) and metalness (blue)
    rm = np.zeros((TH, TW, 3), np.float32); rm[..., 1] = 150
    rm[..., 1] = np.where(pad[..., 0], 70, rm[..., 1]); rm[..., 2] = np.where(pad[..., 0], 255, 0)
    rm[..., 1] = np.where(s[..., 0] > 0.5, 215, rm[..., 1])
    rimg = Image.fromarray(rm.astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=90); a = base64.b64encode(buf.getvalue()).decode()
    buf = io.BytesIO(); rimg.save(buf, "PNG", optimize=True); r = base64.b64encode(buf.getvalue()).decode()
    img.save(os.path.join(WORK, name + "_color.png"))
    return a, r

TOP = composite(L["fcu"], L["fmask"], L["fsilk"], "top")
BOT = composite(L["bcu"], L["bmask"], L["bsilk"], "bot")

# ---------------- flat design views for the page (schematic, assembly, layers)
DOCS = os.path.join(HERE, "..", "..", "docs", "board_viewer")
VIEWS = os.path.join(DOCS, "views"); os.makedirs(VIEWS, exist_ok=True)
K = 1.5  # 30 px/mm
V = {k: crop(layer_png(v, "V_" + k, S * K), K) for k, v in
     {"fcu": "F.Cu", "bcu": "B.Cu", "fsilk": "F.SilkS", "bsilk": "B.SilkS", "fmask": "F.Mask", "edge": "Edge.Cuts"}.items()}
ASM = os.path.join(WORK, "asm.kicad_pcb")   # board copy with values hidden and one centred reference per part
subprocess.run([sys.executable, os.path.join(HERE, "asm_board.py"), PCB, ASM], check=True, capture_output=True)
V["ffab"] = crop(layer_png("F.Fab", "V_ffab", S * K, pcb=ASM), K)
HB = hole_mask(K, big=True)
def mix(base, layers):
    col = np.zeros(V["fcu"].shape + (3,), np.float32); col[:] = base
    for a, c, alpha in layers:
        m = (a * alpha)[..., None]; col = col * (1 - m) + np.array(c, np.float32) * m
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
sub = (24, 30, 26)
mix(sub, [(V["fcu"], (214, 72, 58), 1.0), (V["fsilk"], (236, 226, 160), 1.0), (V["edge"], (225, 225, 220), 1.0), (HB, (8, 8, 8), 1.0)]).save(os.path.join(VIEWS, "top_layer.png"), optimize=True)
mix(sub, [(V["bcu"], (70, 128, 222), 1.0), (V["bsilk"], (236, 226, 160), 1.0), (V["edge"], (225, 225, 220), 1.0), (HB, (8, 8, 8), 1.0)]).transpose(Image.FLIP_LEFT_RIGHT).save(os.path.join(VIEWS, "bottom_layer.png"), optimize=True)
mix(sub, [(V["bcu"], (70, 128, 222), 0.75), (V["fcu"], (214, 72, 58), 0.8), (V["edge"], (225, 225, 220), 1.0), (HB, (8, 8, 8), 1.0)]).save(os.path.join(VIEWS, "both_layers.png"), optimize=True)
# assembly: black board on white. Inside of the outline from the Edge.Cuts line, through holes (not tented vias) show white.
def board_inside(k):
    """Anti-aliased mask of the board outline (rounded rectangle, radius read from the Edge.Cuts arcs) at S*k px/mm."""
    rr = max([pcbnew.ToMM(d.GetRadius()) for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_ARC] or [0.0])
    s = S * k; th, tw = int(round(H * s)), int(round(W * s))
    yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32); px, py = (xx + 0.5) / s, (yy + 0.5) / s
    qx, qy = np.abs(px - W / 2) - (W / 2 - rr), np.abs(py - H / 2) - (H / 2 - rr)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rr   # signed distance, mm
    return np.clip(0.5 - d * s, 0, 1).astype(np.float32)
INSIDE = board_inside(K)
VIA_AT = {(round(pcbnew.ToMM(t.GetPosition().x) - OX, 4), round(pcbnew.ToMM(t.GetPosition().y) - OY, 4)) for t in board.GetTracks() if t.GetClass() == "PCB_VIA"}
_all = holes; holes = [h for h in _all if (round(h[0], 4), round(h[1], 4)) not in VIA_AT]
HP = hole_mask(K, big=True); holes = _all
BLACK = (20, 21, 23)
mix((255, 255, 255), [(INSIDE, BLACK, 1.0), (V["fmask"], (212, 172, 90), 1.0), (V["ffab"], (238, 238, 234), 1.0),
                      (HP, (255, 255, 255), 1.0)]).save(os.path.join(VIEWS, "assembly.png"), optimize=True)
# assembly + copper: the same board with the routed tracks (pours hidden), bottom in blue under top in red
V["fcu_t"] = crop(layer_png("F.Cu", "V_fcu_t", S * K, pcb=ASM), K)
V["bcu_t"] = crop(layer_png("B.Cu", "V_bcu_t", S * K, pcb=ASM), K)
mix((255, 255, 255), [(INSIDE, BLACK, 1.0), (V["bcu_t"] * INSIDE, (78, 138, 232), 0.85), (V["fcu_t"] * INSIDE, (232, 88, 62), 1.0),
                      (V["fmask"], (212, 172, 90), 1.0), (V["ffab"], (238, 238, 234), 1.0),
                      (HP, (255, 255, 255), 1.0)]).save(os.path.join(VIEWS, "assembly_copper.png"), optimize=True)
subprocess.run(["kicad-cli", "sch", "export", "svg", "-o", WORK, os.path.join(os.path.dirname(PCB), "powerJackal.kicad_sch")], check=True, capture_output=True)
_svg = open(os.path.join(WORK, "powerJackal.svg")).read()
_svg = re.sub(r"<!DOCTYPE[^>]*>", "", _svg, count=1, flags=re.S)   # the host refuses DTDs in supporting files
open(os.path.join(VIEWS, "schematic.svg"), "w").write(_svg)
print("views written", sorted(os.listdir(VIEWS)))

# ---------------- footprints and parts
ALIAS = {"R_0805_2012Metric": "R0805", "R_1206_3216Metric": "R1206", "C_0805_2012Metric": "C0805", "C_1206_3216Metric": "C1206",
         "LED_0805_2012Metric": "LED0805", "D_SMA": "SMA", "D_SMB": "SMB", "Fuse_Littelfuse_2016L": "FUSE", "SOT-223-3_TabPin2": "SOT223",
         "SOT-23-6": "SOT236", "SOT-23": "SOT23", "VSSOP-10_3x3mm_P0.5mm": "VSSOP10", "LQFP-32_7x7mm_P0.8mm": "LQFP32",
         "LTM8023_LGA-50_11.25x9mm_P1.27mm": "LTM", "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal": "USBC",
         "Molex_95501-2441_4P4C_Horizontal": "RJ", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal": "MKDS",
         "PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal": "MC2", "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal": "JSTSH4",
         "SW_SPST_TL3342": "TL3342", "PinHeader_1x05_P2.54mm_Vertical": "HDR5", "TestPoint_Keystone_5015_Micro-Minature": "TP5015", "TestPad_3.4x1.8mm": "TPPAD",
         "CP_Radial_D6.3mm_P2.50mm": "CP63", "SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm": "SJ", "MountingHole_4.3mm_M4": "MH", "MountingHole_4.5mm_8-32": "MH",
         "C_1210_3225Metric": "C1210", "Texas_B3QFN-14-1EP_5x5.5mm_P0.65mm_ThermalVia": "QFNMOD", "ESP32-C3-MINI-1U": "MINI1U"}
BODY = {"R0805": "res", "C0805": "cap", "C1206": "cap", "LED0805": "led", "SMA": "diode", "SMB": "diode", "FUSE": "fuse", "SOT223": "ic",
        "SOT236": "ic", "SOT23": "ic", "VSSOP10": "ic", "LQFP32": "ic", "LTM": "ltm", "USBC": "usbc", "RJ": "rj", "MKDS": "mkds", "MC2": "mc2",
        "JSTSH4": "jst", "TL3342": "tact", "HDR5": "hdr5", "TP5015": "tp", "TPPAD": "none", "CP63": "ecap", "SJ": "none", "MH": "none", "R1206": "res",
        "C1210": "cap", "QFNMOD": "qfnmod", "MINI1U": "mini1u"}
SHUNTS = {"R1", "R2", "R12"}
HEIGHT = {"SMA": 2.2, "SMB": 2.3, "C1206": 1.6, "C1210": 2.5, "SOT223": 1.6, "SOT236": 1.1, "SOT23": 1.1, "VSSOP10": 1.0, "LQFP32": 1.4, "QFNMOD": 4.0}
FP = {}
def fp_geom(fp):
    T = pcbnew.ToMM
    o = fp.GetPosition(); rot = fp.GetOrientationDegrees()
    def loc(v):  # world -> footprint local (undo rotation)
        dx, dy = T(v.x - o.x), T(v.y - o.y); a = math.radians(rot)
        return (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))
    def bbox(layer):
        pts = []
        for g in fp.GraphicalItems():
            if g.GetLayer() == layer and g.GetClass() != "MTEXT" and "TEXT" not in g.GetClass():
                if g.GetShape() == pcbnew.SHAPE_T_CIRCLE:
                    c = loc(g.GetCenter()); r = T(g.GetRadius()); pts += [(c[0] - r, c[1] - r), (c[0] + r, c[1] + r)]
                elif g.GetShape() in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_RECT):
                    pts += [loc(g.GetStart()), loc(g.GetEnd())]
        if not pts: return None
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]
    pads = []
    for p in fp.Pads():
        x, y = loc(p.GetPosition()); a = p.GetAttribute()
        typ = {pcbnew.PAD_ATTRIB_SMD: "smd", pcbnew.PAD_ATTRIB_PTH: "thru_hole", pcbnew.PAD_ATTRIB_NPTH: "np_thru_hole"}.get(a, "smd")
        shape = {pcbnew.PAD_SHAPE_RECT: "rect", pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_OVAL: "oval"}.get(p.GetShape(), "roundrect")
        sz = p.GetSize()
        pads.append([p.GetNumber(), typ, shape, round(x, 3), round(y, 3), round(p.GetOrientationDegrees() - rot, 1),
                     round(T(sz.x), 3), round(T(sz.y), 3), round(T(p.GetDrillSize().x), 3), p.IsOnLayer(pcbnew.F_Cu)])
    fab = bbox(pcbnew.F_Fab); crt = bbox(pcbnew.F_CrtYd)
    return {"fab": fab or crt, "crt": crt or fab, "pads": pads}

ROLE = {
    "J1": ("Smart port jack", "V5 smart cable plugs in here. Footprint is a stand-in until the Molex drawing is checked.", "Smart port"),
    "J2": ("Bench input terminal", "10 to 15 V bench supply. Safe with the smart port connected too, the higher input wins.", "Bench in"),
    "D5": ("Port OR diode", "Smart port into the shared input.", None), "D3": ("Bench OR diode", "Bench input into the shared input.", None),
    "F1": ("Polyfuse", "1.5 A hold, right after the OR diodes.", "Polyfuse"), "D1": ("TVS clamp", "Keeps hot-plug spikes well below the module's 38 V limit.", None),
    "C1": ("Bulk input capacitor", "Damps hot-plug ringing.", "Bulk cap"),
    "U1": ("5 V step-down module", "TI TPSM53602: port voltage to 5 V, up to 2 A, inductor inside. Pads under the body: hot plate or hot air.", "TPSM53602"),
    "U2": ("INA226, input", "Port voltage and current, address 0x40.", None), "U3": ("INA226, 5 V rail", "Address 0x41.", None),
    "U5": ("INA226, 3.3 V rail", "Address 0x45, A1 and A0 both tied to VS.", None), "R1": ("Input shunt", "Kelvin sense traces from the inner pad edges.", None),
    "R2": ("5 V shunt", "Kelvin sense traces from the inner pad edges.", None), "R12": ("3.3 V shunt", "Kelvin sense traces from the inner pad edges.", None),
    "U6": ("3.3 V LDO", "Tab is GND and sits in the ground pour.", "LDO"),
    "U4": ("ESP32-C3 module", "Built-in USB serial and JTAG on the USB-C port: flash and print over one cable. Radio unused, no antenna fitted.", "ESP32-C3"),
    "J7": ("USB-C", "Flashing, serial terminal, and 3.3 V power when the port is off.", "USB-C"), "U7": ("USB ESD protection", "Right beside J7.", None),
    "J6": ("5 V output", "Pin 1 (+) is 5 V. Takes a 1803578 plug.", "5 V out"), "J9": ("3.3 V output", "Pin 1 (+) is 3.3 V.", "3.3 V out"),
    "J3": ("STEMMA QT / I2C", "Cable to the OLED.", "I2C"),
    "SW1": ("RESET button", "Pulls EN low.", None), "SW2": ("BOOT button", "Holds GPIO9 low at reset for download mode.", "BOOT"),
    "Q1": ("USB power switch", "AO3401A P-MOSFET. USB powers the board only while the 5 V rail is off, so port readings never include USB current.", None),
}
P = []
parts = {p["ref"]: p for p in D.PARTS}
for fp in board.GetFootprints():
    ref = fp.GetReference(); name = str(fp.GetFPID().GetLibItemName()); key = ALIAS[name]
    if key not in FP:
        FP[key] = fp_geom(fp)
    x, y = pcbnew.ToMM(fp.GetPosition().x) - OX, pcbnew.ToMM(fp.GetPosition().y) - OY
    m = "shunt" if ref in SHUNTS else BODY[key]
    if m == "none" and key == "MH": continue
    part = parts[ref]
    title, note, tag = ROLE.get(ref, (part["value"], "", None))
    if ref.startswith("TP"): title, note = "Test point " + part["value"], "Bare 3.4 × 1.8 mm copper pad. Same land as a Keystone 5015, so a loop can be added later."
    q = {"ref": ref, "fp": key, "x": round(x, 3), "y": round(y, 3), "rot": round((-fp.GetOrientationDegrees()) % 360, 1), "m": m,
         "i": [title, (part["value"] + " · " if part["value"] not in title and part["value"] != part["mpn"] else "") + (part["mpn"] or "copper"), note]}
    if key in HEIGHT: q["h"] = HEIGHT[key]
    if tag: q["tag"] = tag
    P.append(q)
P.sort(key=lambda q: (q["ref"][0], int(re.sub(r"\D", "", q["ref"]) or 0)))
ZDEF = [
    ("in", "Power in", "#E2553C", "J1 and J2, the D5 and D3 OR diodes, F1, LED1 and the RS-485 test points.",
     "J1 J2 D5 D3 F1 R8 LED1 TP1 TP8 TP9 TP5"),
    ("v5", "5 V", "#E0A300", "TVS, bulk and input caps, the TPSM53602 module, the input and 5 V INA226 cells, and J6.",
     "D1 C1 C2 C3 C8 U1 R3 R4 C4 C5 TP2 U2 R1 C6 U3 R2 C7 J6 R9 LED2 TP3 TP10"),
    ("v33", "3.3 V", "#3D8BFD", "D2, the Q1 USB power switch, U6 LDO, the 3.3 V INA226 cell and J9.", "U6 D2 Q1 C10 C11 U5 R12 C14 J9 TP4 TP6"),
    ("usb", "USB-C", "#25AE9F", "J7, CC resistors, U7 ESD and the D4 USB power diode.", "J7 U7 R14 R15 D4"),
    ("mcu", "ESP32-C3", "#9B6BE8", "U4 module, RESET and BOOT, strap and I2C pull-ups, status LED and the STEMMA QT port.",
     "U4 C9 R21 C13 R17 C15 C12 R22 SW1 SW2 R5 R6 R7 J3 R20 LED3"),
]
_zone_of = {r: k for k, (zid, *_rest, refs) in enumerate(ZDEF) for r in refs.split()}
_cbox = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in _zone_of: continue
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox(); xs += [pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetRight()) - OX]; ys += [pcbnew.ToMM(bb.GetTop()) - OY, pcbnew.ToMM(bb.GetBottom()) - OY]
    if xs: _cbox[ref] = (max(min(xs), 0), max(min(ys), 0), min(max(xs), W), min(max(ys), H))
missing = set(_zone_of) - set(_cbox)
assert not missing, missing
STEP = 0.5
nx, ny = int(round(W / STEP)), int(round(H / STEP))
grid = []
for j in range(ny):
    row = []
    for i in range(nx):
        cx, cy = (i + 0.5) * STEP, (j + 0.5) * STEP
        best = min(_cbox, key=lambda r: math.hypot(max(_cbox[r][0] - cx, 0, cx - _cbox[r][2]), max(_cbox[r][1] - cy, 0, cy - _cbox[r][3])))
        row.append(_zone_of[best])
    grid.append(row)
ZRECTS = {k: [] for k in range(len(ZDEF))}
open_runs = {}   # (zone, i0, i1) -> [x0, y0, x1, y1] still growing downward
for j, row in enumerate(grid):
    runs, i = [], 0
    while i < nx:
        k = row[i]; i0 = i
        while i < nx and row[i] == k: i += 1
        runs.append((k, i0, i))
    nxt = {}
    for k, i0, i1 in runs:
        r = open_runs.pop((k, i0, i1), None)
        if r: r[3] = (j + 1) * STEP; nxt[(k, i0, i1)] = r
        else: nxt[(k, i0, i1)] = [i0 * STEP, j * STEP, i1 * STEP, (j + 1) * STEP]
    for (k, *_x), r in open_runs.items(): ZRECTS[k].append(r)
    open_runs = nxt
for (k, *_x), r in open_runs.items(): ZRECTS[k].append(r)
ZONES = [{"id": zid, "name": name, "color": col, "rects": [[round(v, 2) for v in r] for r in ZRECTS[k]], "text": text}
         for k, (zid, name, col, text, refs) in enumerate(ZDEF)]
print("zone rects", sum(len(z["rects"]) for z in ZONES))
print("parts", len(P), "footprints", len(FP))

# ---------------- parts and cost table, from the same data as the BOM spreadsheet
import html as _html
_bsrc = open(os.path.join(HERE, "..", "bom", "build_bom.py")).read()
_s = _bsrc.index("P = ["); _e = _bsrc.index("\n]\n", _s) + 3
_ns = {}; exec(_bsrc[_s:_e], _ns); BOMP = _ns["P"]
BOMDATE = re.search(r'CHECKED = "([^"]+)"', _bsrc).group(1)
DKURL = "https://www.digikey.ca/en/products/detail/"
def money(v): return f"${v:,.2f}"
FX = float(re.search(r'FX, FX_DATE = ([\d.]+), "([^"]+)"', _bsrc).group(1)); FXDATE = re.search(r'FX, FX_DATE = ([\d.]+), "([^"]+)"', _bsrc).group(2)
rows, tot_on, tot_opt, min_stock = [], 0.0, 0.0, None
groups = [("On the board", lambda blk: "optional" not in blk), ("Optional, off the board (OLED and plug-in load kit)", lambda blk: "optional" in blk)]
for gname, keep in groups:
    rows.append(f'<tr class="grp"><td colspan="7">{_html.escape(gname)}</td></tr>')
    sub = 0.0
    for (ref, block, desc, mfr, mpn, dkpn, q, sp, price, stock, path, note) in BOMP:
        if not keep(block): continue
        unit = price * FX; cost = q * unit; sub += cost
        min_stock = stock if min_stock is None else min(min_stock, stock)
        url = path if path.startswith("http") else DKURL + path
        rows.append(f'<tr><td class="ref">{_html.escape(ref)}</td><td>{_html.escape(desc)}<br><span class="muted">{_html.escape(mfr)}</span></td>'
                    f'<td class="mpn"><a href="{_html.escape(url)}" target="_blank" rel="noopener">{_html.escape(mpn)}</a></td>'
                    f'<td class="n">{q}</td><td class="n">{stock:,}</td><td class="n">{money(unit)}</td><td class="n">{money(cost)}</td></tr>')
    rows.append(f'<tr class="tot"><td colspan="6">Subtotal</td><td class="n">{money(sub)}</td></tr>')
    if "optional" in gname.lower(): tot_opt = sub
    else: tot_on = sub
BOMSUM = (f'<div><b>{money(tot_on)}</b><span>Parts for 1 board, CAD</span></div>'
          f'<div><b>{money(tot_opt)}</b><span>OLED and load kit, CAD</span></div>'
          f'<div><b>{money(tot_on + tot_opt)}</b><span>Everything, 1 board</span></div>'
          f'<div><b>{len(BOMP)} / {len(BOMP)}</b><span>Lines in stock at DigiKey</span></div>')
print("bom CAD", money(tot_on), money(tot_opt), money(tot_on + tot_opt), "lowest stock", min_stock)

src = open(os.path.join(HERE, "render_src_v5.html")).read()
src = src.replace("__BOMROWS__", "\n".join(rows)).replace("__BOMSUM__", BOMSUM).replace("__BOMDATE__", BOMDATE)
src = src.replace("__FX__", f"{FX:.4f}").replace("__FXDATE__", FXDATE).replace("__ZONES__", json.dumps(ZONES, separators=(",", ":")))
_vw = Image.open(os.path.join(VIEWS, "top_layer.png")).size
src = src.replace("__VW__", str(_vw[0])).replace("__VH__", str(_vw[1]))
_nets = sorted({n for p in D.PARTS for n in p["pins"].values() if n})
src = src.replace("__NSYM__", str(len(D.PARTS))).replace("__NNET__", str(len(_nets)))
out = (src.replace("__FP__", json.dumps(FP, separators=(",", ":"))).replace("__P__", json.dumps(P, separators=(",", ":"), ensure_ascii=False))
          .replace("__TOP__", TOP[0]).replace("__TOPRM__", TOP[1]).replace("__BOT__", BOT[0]).replace("__BOTRM__", BOT[1]))
open(os.path.join(DOCS, "powerJackal_board_viewer.html"), "w").write(out)
print("html bytes", len(out))
