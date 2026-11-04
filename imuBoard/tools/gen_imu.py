"""Generate the centurion IMU board (imuBoard): project library, schematic and PCB, for KiCad 10.

Run with KiCad's own Python from anywhere:
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" imuBoard/tools/gen_imu.py

It writes, in imuBoard/:
    imuBoard.kicad_pro, imuBoard.kicad_sch, imuBoard.kicad_pcb, sym-lib-table, fp-lib-table,
    lib/imuBoard.kicad_sym (BMI270), lib/imuBoard.pretty/ (the TPD4E05U06 DQA footprint from centurion).
UUIDs are derived from names, so reruns give the same UUIDs. Rerunning OVERWRITES the schematic and the board:
once the board is edited by hand in KiCad, stop using this script for it.
"""
import os, re, sys, json, uuid, math, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PD = os.path.dirname(HERE)                      # imuBoard/
REPO = os.path.dirname(PD)
PROJ = "imuBoard"
KS = "C:/Program Files/KiCad/10.0/share/kicad"
SYMDIR, FPDIR = KS + "/symbols", KS + "/footprints"
NS = uuid.UUID("2b7d4f0e-5d1a-4c3e-9f7a-1e6b3c9d0a42")
U = lambda *k: str(uuid.uuid5(NS, "/".join(map(str, k))))
ROOT = U("root")
REV = "1.0"

# =====================================================================================================
# Design: parts, values, footprints, part numbers and the pin-to-net map
# Net names: power nets as power symbols (GND, +3V3); signals as local labels on the root sheet (/SCK...).
# J1 pinout matches centurion J5 exactly, so the cable is straight through (pin n to pin n).
# =====================================================================================================
PARTS = [
    dict(ref="J1", lib="Connector_Generic_MountingPin:Conn_01x08_MountingPin", value="BM08B-GHS-TBT",
         fp="Connector_JST:JST_GH_BM08B-GHS-TBT_1x08-1MP_P1.25mm_Vertical", mpn="BM08B-GHS-TBT", mfr="JST",
         desc="To centurion J5: JST GH 8-pin, vertical, straight-through cable",
         pins={"1": "+3V3", "2": "GND", "3": "SCK", "4": "MOSI", "5": "MISO_C", "6": "CS", "7": "INT1", "8": "INT2", "MP": "GND"},
         at=(53.34, 99.06), rot=0, stub={"1": (7.62, (0, -1))}),
    dict(ref="U2", lib="Power_Protection:TPD4E05U06DQA", value="TPD4E05U06DQA",
         fp="imuBoard:TI_DQA_USON-10_2.5x1.0mm_P0.5mm", mpn="TPD4E05U06QDQARQ1", mfr="Texas Instruments",
         desc="4-channel ESD clamp at the cable jack; pins 6, 7, 9 and 10 are not connected inside, the traces run over them (flow-through)",
         pins={"1": "CS", "10": "CS", "2": "SCK", "9": "SCK", "4": "MOSI", "7": "MOSI", "5": "MISO_C", "6": "MISO_C", "3": "GND", "8": "GND"},
         at=(111.76, 99.06), rot=0, fields="below_right"),
    dict(ref="R1", lib="Device:R", value="100", fp="Resistor_SMD:R_0805_2012Metric", mpn="RC0805FR-07100RL", mfr="Yageo",
         desc="MISO series resistor at the IMU: damps the cable (centurion/sim, spi_imu.cir with ROIMU = 140)",
         pins={"1": "MISO_C", "2": "MISO"}, at=(152.4, 78.74), rot=90),
    dict(ref="U1", lib="imuBoard:BMI270", value="BMI270", fp="Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm", mpn="BMI270",
         mfr="Bosch Sensortec", desc="6-axis IMU, 4-wire SPI. ASDx, ASCx, OCSB and OSDO are left unconnected (BMI270 datasheet table 25)",
         pins={"1": "MISO", "2": None, "3": None, "4": "INT1", "5": "+3V3", "6": "GND", "7": "GND", "8": "+3V3",
               "9": "INT2", "10": None, "11": None, "12": "CS", "13": "SCK", "14": "MOSI"},
         at=(205.74, 99.06), rot=0),
    dict(ref="C1", lib="Device:C", value="100nF", fp="Capacitor_SMD:C_0805_2012Metric", mpn="CC0805KRX7R9BB104", mfr="Yageo",
         desc="U1 VDD decoupling", pins={"1": "+3V3", "2": "GND"}, at=(218.44, 58.42), rot=0),
    dict(ref="C2", lib="Device:C", value="100nF", fp="Capacitor_SMD:C_0805_2012Metric", mpn="CC0805KRX7R9BB104", mfr="Yageo",
         desc="U1 VDDIO decoupling", pins={"1": "+3V3", "2": "GND"}, at=(231.14, 58.42), rot=0),
    dict(ref="C3", lib="Device:C", value="1uF", fp="Capacitor_SMD:C_0805_2012Metric", mpn="CC0805KKX7R8BB105", mfr="Yageo",
         desc="Bulk at the board input", pins={"1": "+3V3", "2": "GND"}, at=(243.84, 58.42), rot=0),
    dict(ref="H1", lib="Mechanical:MountingHole", value="#8-32", fp="UWAT:MountingHole_4.5mm_8-32", mpn="", mfr="",
         desc="", pins={}, at=(132.08, 165.1), rot=0, in_bom=False),
    dict(ref="H2", lib="Mechanical:MountingHole", value="#8-32", fp="UWAT:MountingHole_4.5mm_8-32", mpn="", mfr="",
         desc="", pins={}, at=(144.78, 165.1), rot=0, in_bom=False),
]
POWER = {"GND": "power:GND", "+3V3": "power:+3V3"}
NOTES = [
    "Centurion IMU board, rev %s. Plugs into centurion J5 with a straight JST GH 8-pin cable (pin n to pin n), 30 cm or less." % REV,
    "SPI mode 0 or 3, 10 MHz max. Centurion has 100 ohm series resistors on SCK, MOSI and CS (R8, R9, R41); R1 here is the matching one on MISO.",
    "BMI270: firmware must upload Bosch's 8 kB config file after every power-up (INIT_CTRL / INIT_DATA), and do one dummy read to select SPI.",
    "Axes as printed on the top silkscreen: +X toward J1, +Y toward H2, +Z up out of the board.",
    "J5 pin 7 (IMU_INT1) is BMI270 INT1 (pin 4); J5 pin 8 (IMU_INT2) is BMI270 INT2 (pin 9).",
]

# =====================================================================================================
# Symbol library helpers (KiCad 10 text; resolves 'extends')
# =====================================================================================================
def block_at(text, i):
    depth, j, instr = 0, i, False
    while j < len(text):
        c = text[j]
        if instr:
            if c == "\\": j += 2; continue
            if c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0: return text[i:j + 1]
        j += 1
    raise ValueError("unbalanced")

def find_symbol(libtext, name):
    m = re.search(r'\n\s*\(symbol "%s"\s' % re.escape(name), libtext)
    if not m: raise KeyError(name)
    return block_at(libtext, libtext.index("(", m.start()))

def prop(block, key):
    m = re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(key), block)
    return m.group(1) if m else None

def set_prop(block, key, val):
    return re.sub(r'(\(property "%s" ")((?:[^"\\]|\\.)*)(")' % re.escape(key), lambda mm: mm.group(1) + val + mm.group(3), block, count=1)

def flat(lib, name):
    """Symbol text with 'extends' resolved, top level named lib:name, units name_u_s."""
    text = open("%s/%s.kicad_sym" % (SYMDIR, lib), encoding="utf-8").read()
    blk = find_symbol(text, name)
    m = re.search(r'\(extends "([^"]+)"\)', blk)
    if m:
        parent = m.group(1)
        out = find_symbol(text, parent)
        for key in ("Reference", "Value", "Footprint", "Datasheet", "Description", "ki_keywords", "ki_fp_filters"):
            v = prop(blk, key)
            if v is not None: out = set_prop(out, key, v)
        out = out.replace('(symbol "%s"' % parent, '(symbol "%s"' % name, 1)
        out = re.sub(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(parent), lambda mm: '(symbol "%s_%s_%s"' % (name, mm.group(1), mm.group(2)), out)
        blk = out
    return blk.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, name), 1)

def pins_of(sym):
    """pin number -> list of (x, y, angle, name, type), library coordinates (y up). Handles '(hide yes)'."""
    out = {}
    for m in re.finditer(r"\(pin (\w+) (\w+)", sym):
        b = block_at(sym, m.start())
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", b)
        name = re.search(r'\(name "((?:[^"\\]|\\.)*)"', b).group(1)
        num = re.search(r'\(number "((?:[^"\\]|\\.)*)"', b).group(1)
        out.setdefault(num, []).append((float(at.group(1)), float(at.group(2)), int(float(at.group(3) or 0)), name, m.group(1)))
    return out

# BMI270: same package and pinout as the BMI160 (checked against the BMI270 datasheet pin table)
bmi = flat("Sensor_Motion", "BMI160").replace('(symbol "Sensor_Motion:BMI160"', '(symbol "imuBoard:BMI270"', 1)
bmi = re.sub(r'\(symbol "BMI160_(\d+)_(\d+)"', lambda mm: '(symbol "BMI270_%s_%s"' % (mm.group(1), mm.group(2)), bmi)
bmi = set_prop(bmi, "Value", "BMI270")
bmi = set_prop(bmi, "Datasheet", "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf")
bmi = set_prop(bmi, "Description", "6-axis IMU (accelerometer and gyroscope), SPI or I2C, LGA-14 3x2.5 mm. Pinout as BMI160")
bmi = set_prop(bmi, "ki_keywords", "IMU accelerometer gyroscope Bosch BMI270")

LIBSYM = {"imuBoard:BMI270": bmi}
for lid in sorted({p["lib"] for p in PARTS} | set(POWER.values()) | {"power:PWR_FLAG"}):
    if lid not in LIBSYM:
        LIBSYM[lid] = flat(*lid.split(":"))
PINS = {lid: pins_of(t) for lid, t in LIBSYM.items()}

# =====================================================================================================
# Files: libraries, tables, project
# =====================================================================================================
os.makedirs(os.path.join(PD, "lib", "imuBoard.pretty"), exist_ok=True)
libsym_text = bmi.replace('(symbol "imuBoard:BMI270"', '(symbol "BMI270"', 1)
with open(os.path.join(PD, "lib", "imuBoard.kicad_sym"), "w", encoding="utf-8", newline="\n") as f:
    f.write('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n\t(generator_version "10.0")\n\t'
            + libsym_text.replace("\n", "\n\t").rstrip() + "\n)\n")
shutil.copy(os.path.join(REPO, "centurion", "lib", "centurion.pretty", "TI_DQA_USON-10_2.5x1.0mm_P0.5mm.kicad_mod"),
            os.path.join(PD, "lib", "imuBoard.pretty", "TI_DQA_USON-10_2.5x1.0mm_P0.5mm.kicad_mod"))
with open(os.path.join(PD, "sym-lib-table"), "w", newline="\n") as f:
    f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "imuBoard") (type "KiCad") (uri "${KIPRJMOD}/lib/imuBoard.kicad_sym") (options "") (descr "centurion IMU board parts"))\n)\n')
with open(os.path.join(PD, "fp-lib-table"), "w", newline="\n") as f:
    f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "imuBoard") (type "KiCad") (uri "${KIPRJMOD}/lib/imuBoard.pretty") (options "") (descr ""))\n'
            '\t(lib (name "UWAT") (type "KiCad") (uri "${KIPRJMOD}/../powerJackal/lib/UWAT.pretty") (options "") (descr ""))\n)\n')

def write_project():
    pro = json.load(open(os.path.join(REPO, "centurion", "centurion.kicad_pro"), encoding="utf-8"))
    pro["meta"]["filename"] = PROJ + ".kicad_pro"
    pro["sheets"] = [[ROOT, "Root"]]
    pro["boards"] = []
    pro["text_variables"] = {}
    ns = pro["net_settings"]
    keep = []
    for c in ns["classes"]:
        if c["name"] == "Default":
            c.update(track_width=0.2, clearance=0.2, via_diameter=0.6, via_drill=0.3)
            keep.append(c)
        elif c["name"] == "3V3":
            c.update(track_width=0.3)
            keep.append(c)
    ns["classes"] = keep
    ns["netclass_patterns"] = [{"netclass": "3V3", "pattern": "+3V3"}]
    ns["netclass_assignments"] = None
    pro.pop("pcbnew", None)
    with open(os.path.join(PD, PROJ + ".kicad_pro"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(pro, f, indent=2)

# =====================================================================================================
# Schematic
# =====================================================================================================
def fmt(v): return ("%.4f" % v).rstrip("0").rstrip(".")
G = 2.54

def rot_lib(px, py, rot):
    a = math.radians(rot)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)

def pin_screen(part, num):
    """(sx, sy, outward dx, dy) of each copy of a pin, screen coordinates."""
    res = []
    for px, py, ang, name, et in PINS[part["lib"]][num]:
        rx, ry = rot_lib(px, py, part["rot"])
        X, Y = part["at"]
        a = math.radians(ang + part["rot"])
        res.append((round(X + rx, 4), round(Y - ry, 4), (-round(math.cos(a)), round(math.sin(a))), name))
    return res

S = []
A = S.append
pwr_n = [0]

def wire(x0, y0, x1, y1):
    A('\t(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))\n' % (fmt(x0), fmt(y0), fmt(x1), fmt(y1), U("w", x0, y0, x1, y1)))

def label(net, x, y, d):
    ang, just = {(-1, 0): (180, "right"), (1, 0): (0, "left"), (0, -1): (90, "left"), (0, 1): (270, "right")}[d]
    A('\t(label "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))\n' % (net, fmt(x), fmt(y), ang, just, U("l", net, x, y)))

def no_connect(x, y):
    A('\t(no_connect (at %s %s) (uuid "%s"))\n' % (fmt(x), fmt(y), U("nc", x, y)))

def text(s, x, y, size=1.27, bold=False):
    s = s.replace('"', "'")
    A('\t(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) (justify left bottom)) (uuid "%s"))\n'
      % (s, fmt(x), fmt(y), size, size, " (bold yes)" if bold else "", U("t", s, x, y)))

def sym_instance(lib_id, ref, value, x, y, rot, props, pins, in_bom=True, on_board=True, uid=None, ref_hidden=False, ref_at=None, val_at=None, field_angle=0):
    uid = uid or U("sym", ref)
    rx, ry = ref_at or (x, y - 2.54)
    vx, vy = val_at or (x, y + 2.54)
    flags = "(in_bom %s) (on_board %s) (in_pos_files %s)" % ("yes" if in_bom else "no", "yes" if on_board else "no", "yes" if on_board else "no")
    out = '\t(symbol (lib_id "%s") (at %s %s %d) (unit 1) (body_style 1) (exclude_from_sim no) %s (dnp no) (uuid "%s")' % (lib_id, fmt(x), fmt(y), rot, flags, uid)
    out += ' (property "Reference" "%s" (at %s %s %d) (effects (font (size 1.27 1.27))%s%s))' % (ref, fmt(rx), fmt(ry), field_angle, "" if ref_hidden else " (justify left)", " (hide yes)" if ref_hidden else "")
    out += ' (property "Value" "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify left)))' % (value, fmt(vx), fmt(vy), field_angle)
    for k, v in props:
        out += ' (property "%s" "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))' % (k, v.replace('"', "'"), fmt(x), fmt(y))
    for num in pins:
        out += ' (pin "%s" (uuid "%s"))' % (num, U("pin", ref, num))
    out += ' (instances (project "%s" (path "/%s" (reference "%s") (unit 1)))))\n' % (PROJ, ROOT, ref)
    A(out)

PWR_ROT = {"power:GND": {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270},
           "power:+3V3": {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}}

def power_symbol(net, x, y, d):
    lid = POWER[net]
    pwr_n[0] += 1
    ref = "#PWR%02d" % pwr_n[0]
    vx, vy = x + d[0] * 4.3, y + d[1] * 4.3 + (0.6 if d[0] else 0)
    if d[0] < 0: vx -= len(net) * 1.1
    sym_instance(lid, ref, net, x, y, PWR_ROT[lid][d], [("Footprint", ""), ("Datasheet", ""), ("Description", "")], ["1"],
                 in_bom=False, on_board=False, uid=U("pwr", ref), ref_hidden=True, ref_at=(x, y), val_at=(vx - (len(net) * 0.5 if d[0] == 0 else 0), vy))

def part_body_bbox(part):
    t = LIBSYM[part["lib"]]
    t = re.sub(r"\(pin \w+ \w+.*?\(number \"[^\"]*\"", "", t, flags=re.S)
    pts = [(float(a), float(b)) for a, b in re.findall(r"\((?:start|end|xy|center|mid) ([-\d.]+) ([-\d.]+)\)", t)]
    if not pts: return (-1.27, -1.27, 1.27, 1.27)
    xs = [rot_lib(a, b, part["rot"])[0] for a, b in pts]; ys = [-rot_lib(a, b, part["rot"])[1] for a, b in pts]
    X, Y = part["at"]
    return X + min(xs), Y + min(ys), X + max(xs), Y + max(ys)

def write_schematic():
    S.clear()
    A('(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "%s")\n\t(paper "A4")\n' % ROOT)
    A('\t(title_block\n\t\t(title "Centurion IMU board")\n\t\t(date "%s")\n\t\t(rev "%s")\n\t\t(company "UWAT VEXU")\n'
      '\t\t(comment 1 "Generated by imuBoard/tools/gen_imu.py")\n\t)\n' % (datetime.date.today().isoformat(), REV))
    A("\t(lib_symbols\n")
    for lid, t in LIBSYM.items():
        A("\t\t" + t.replace("\n", "\n\t\t").rstrip() + "\n")
    A("\t)\n")
    for p in PARTS:
        X, Y = p["at"]
        bx0, by0, bx1, by1 = part_body_bbox(p)
        stubs = {}   # stub end -> net, so adjacent power pins on one side can share one symbol
        seen = {}    # pin position -> net (stacked pins, such as U2's hidden second GND pin, share one stub)
        for num in PINS[p["lib"]]:
            net = p["pins"].get(num, "<missing>")
            if net == "<missing>": raise KeyError("%s pin %s has no entry" % (p["ref"], num))
            for sx, sy, d, name in pin_screen(p, num):
                if (sx, sy) in seen:
                    if seen[(sx, sy)] != net: raise ValueError("%s stacked pins at %s have nets %s and %s" % (p["ref"], (sx, sy), seen[(sx, sy)], net))
                    continue
                seen[(sx, sy)] = net
                if net is None:
                    no_connect(sx, sy); continue
                L, sd = p.get("stub", {}).get(num, (G, d))
                ex, ey = sx + d[0] * L, sy + d[1] * L
                wire(sx, sy, ex, ey)
                stubs[(ex, ey, sd)] = net
        done = set()
        for (ex, ey, d), net in sorted(stubs.items()):
            if (ex, ey) in done: continue
            if net in POWER:
                # join neighbours on the same side that carry the same power net
                grp = [(ex, ey)]
                for (fx, fy, fd), fnet in stubs.items():
                    if fnet == net and fd == d and (fx, fy) != (ex, ey) and abs(fx - ex) + abs(fy - ey) <= G + 0.01:
                        grp.append((fx, fy))
                for gx, gy in grp[1:]:
                    wire(ex, ey, gx, gy); done.add((gx, gy))
                power_symbol(net, ex, ey, d)
            else:
                label(net, ex, ey, d)
            done.add((ex, ey))
        props = [("Footprint", p["fp"]), ("Datasheet", ""), ("Description", p["desc"]), ("MPN", p["mpn"]), ("Manufacturer", p["mfr"])]
        ref_at = (bx1 + 1.27, by0 - 1.27) if p["lib"] not in ("Device:R", "Device:C") else (X + 2.54, Y - 1.27)
        val_at = (bx1 + 1.27, by0 + 1.27) if p["lib"] not in ("Device:R", "Device:C") else (X + 2.54, Y + 1.27)
        fang = 0
        if p["lib"] == "Device:R" and p["rot"] == 90:
            ref_at, val_at, fang = (X - 2.54, Y - 2.54), (X + 3.81, Y - 2.54), 90
        if p.get("fields") == "below_right":
            ref_at, val_at = (bx1 + 1.27, by1 + 2.54), (bx1 + 1.27, by1 + 5.08)
        sym_instance(p["lib"], p["ref"], p["value"], X, Y, p["rot"], props, list(PINS[p["lib"]].keys()),
                     in_bom=p.get("in_bom", True), ref_at=ref_at, val_at=val_at, field_angle=fang)
    # power flags: tell ERC the cable feeds these nets
    for i, net in enumerate(("+3V3", "GND")):
        x, y = 60.96 + i * 15.24, 154.94
        ref = "#FLG%02d" % (i + 1)
        sym_instance("power:PWR_FLAG", ref, "PWR_FLAG", x, y, 0, [("Footprint", ""), ("Datasheet", "~"), ("Description", "")], ["1"],
                     in_bom=False, on_board=False, uid=U("flg", net), ref_hidden=True, ref_at=(x, y - 1.9), val_at=(x - 3.8, y - 3.81))
        wire(x, y, x, y + G)
        power_symbol(net, x, y + G, (0, 1) if net == "GND" else (0, 1))
    text("Power flags: the cable from centurion J5 supplies +3V3 and GND", 45.72, 146.05)
    text("Mounting: two #8-32 holes, 25.4 mm (1 in) apart, not tied to GND", 124.46, 157.48)
    text("Centurion IMU board (rev %s)" % REV, 25.4, 25.4, 2.0, True)
    for i, line in enumerate(NOTES):
        text(line, 25.4, 31.75 + i * 3.81)
    text("J1: to centurion J5", 40.64, 76.2, 1.5, True)
    text("U2: ESD at the jack", 99.06, 76.2, 1.5, True)
    text("R1: MISO series resistor", 139.7, 66.04, 1.5, True)
    text("U1: BMI270 IMU", 194.31, 76.2, 1.5, True)
    text("Decoupling: 100 nF at VDD and VDDIO, 1 uF bulk", 205.74, 45.72, 1.5, True)
    A('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n')
    with open(os.path.join(PD, PROJ + ".kicad_sch"), "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(S))

# =====================================================================================================
# PCB
# =====================================================================================================
BOARD = (100.0, 100.0, 138.0, 124.0)       # x0, y0, x1, y1 (mm)
CORNER = 1.5
PLACE = {   # ref: (x, y, rotation in degrees, CCW as KiCad shows it)
    "H1": (106.3, 112.0, 0), "H2": (131.7, 112.0, 0),
    "J1": (119.0, 119.6, 180), "U2": (119.0, 113.3, 90), "U1": (119.0, 106.0, 180), "R1": (121.6, 109.6, 90),
    "C1": (115.9, 103.1, 270), "C2": (122.0, 102.6, 0), "C3": (113.7, 103.2, 270),
}
HOLE_KEEPOUT_R = 5.0     # #8-32 button head is about 7.9 mm across; keep copper 1 mm outside it

def P(ref, num): return ("P", ref, num)
def V(x, y): return ("V", x, y)
ROUTES = [  # net, width (mm), points; a V() point is a via and switches layer (start on F.Cu)
    ("CS", 0.2, [P("J1", "6"), (117.125, 115.4), (118.0, 114.525), P("U2", "1"), P("U2", "10"), (118.0, 108.9), (118.5, 108.4), P("U1", "12")]),
    ("SCK", 0.2, [P("J1", "3"), V(120.875, 116.15), (120.875, 116.6), (118.6, 116.6), V(118.2, 115.6), (118.5, 114.9), P("U2", "2"), P("U2", "9"), (118.5, 109.6), (119.0, 109.1), P("U1", "13")]),
    ("MOSI", 0.2, [P("J1", "4"), (119.625, 114.6), (119.5, 114.475), P("U2", "4"), P("U2", "7"), P("U1", "14")]),
    ("MISO_C", 0.2, [P("J1", "5"), V(118.375, 119.1), (121.5, 119.1), V(121.5, 115.3), (120.0, 114.4), P("U2", "5"), P("U2", "6"), (120.0, 111.6), P("R1", "1")]),
    ("MISO", 0.2, [P("R1", "2"), (121.6, 107.6), (120.75, 106.75), P("U1", "1")]),
    ("INT1", 0.2, [P("J1", "7"), V(115.875, 116.1), (115.875, 108.0), (122.6, 108.0), V(122.6, 105.25), P("U1", "4")]),
    ("INT2", 0.2, [P("J1", "8"), (114.625, 105.75), P("U1", "9")]),
    ("+3V3", 0.3, [P("J1", "1"), (123.375, 116.4), (124.4, 115.4), (124.4, 101.3), (113.7, 101.3)]),
    ("+3V3", 0.3, [P("U1", "8"), (117.2, 105.25), (117.2, 101.3)]),
    ("+3V3", 0.3, [P("U1", "5"), (119.5, 101.3)]),
    ("+3V3", 0.3, [P("C1", "1"), (115.9, 101.3)]),
    ("+3V3", 0.3, [P("C2", "1"), (121.05, 101.3)]),
    ("+3V3", 0.3, [P("C3", "1"), (113.7, 101.3)]),
    ("GND", 0.25, [P("U1", "6"), (118.75, 103.6)]),
    ("GND", 0.25, [P("U1", "7"), (118.75, 103.6)]),
    ("GND", 0.25, [P("C1", "2"), (115.4, 104.85)]),
    ("GND", 0.25, [P("C3", "2"), (115.4, 104.85)]),
    ("GND", 0.25, [P("C2", "2"), (123.0, 104.0)]),
    ("GND", 0.25, [P("U2", "3"), P("U2", "8")]),
    ("GND", 0.25, [P("U2", "3"), (119.01, 115.75)]),
    ("GND", 0.25, [P("J1", "2"), (122.125, 115.9)]),
]
GND_VIAS = [(118.75, 103.6), (115.4, 104.85), (123.0, 104.0), (119.01, 115.75), (122.125, 115.9), (112.775, 119.0), (125.225, 119.0),
            (103.2, 103.0), (134.8, 103.0), (103.2, 121.0), (134.8, 121.0), (112.0, 101.6), (126.0, 101.6), (126.0, 122.6), (112.0, 122.6)]

def build_pcb():
    import pcbnew
    MM = pcbnew.FromMM
    VEC = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
    path = os.path.join(PD, PROJ + ".kicad_pcb")
    b = pcbnew.NewBoard(path)
    b.SetCopperLayerCount(2)
    pcbnew.SaveBoard(path, b)
    write_project()                       # the copied centurion rules, written after NewBoard made its own
    b = pcbnew.LoadBoard(path)
    ds = b.GetDesignSettings()
    tb = b.GetTitleBlock(); tb.SetTitle("Centurion IMU board"); tb.SetRevision(REV); tb.SetCompany("UWAT VEXU"); tb.SetDate(datetime.date.today().isoformat())

    nets = {}
    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
        return nets[name]
    def netname(p, num):
        n = p["pins"].get(num)
        if n is None:
            pin = PINS[p["lib"]][num][0][3]
            return "unconnected-(%s-%s-Pad%s)" % (p["ref"], pin, num)
        return n if n in POWER else "/" + n

    fps = {}
    for p in PARTS:
        lib, name = p["fp"].split(":")
        libdir = {"imuBoard": os.path.join(PD, "lib", "imuBoard.pretty"), "UWAT": os.path.join(REPO, "powerJackal", "lib", "UWAT.pretty")}.get(lib, "%s/%s.pretty" % (FPDIR, lib))
        f = pcbnew.FootprintLoad(libdir, name)
        f.SetFPID(pcbnew.LIB_ID(lib, name))
        f.SetReference(p["ref"]); f.SetValue(p["value"])
        x, y, r = PLACE[p["ref"]]
        f.SetPosition(VEC(x, y)); f.SetOrientationDegrees(r)
        f.SetPath(pcbnew.KIID_PATH("/" + U("sym", p["ref"])))
        f.SetSheetname("/"); f.SetSheetfile(PROJ + ".kicad_sch")
        for k, v in (("MPN", p["mpn"]), ("Manufacturer", p["mfr"]), ("Description", p["desc"])):
            f.SetField(k, v)
            fld = f.GetField(k)
            fld.SetLayer(pcbnew.F_Fab); fld.SetVisible(False)
        f.Reference().SetLayer(pcbnew.F_Fab)
        if not p.get("in_bom", True): f.SetExcludedFromBOM(True)
        for pad in f.Pads():
            num = pad.GetNumber()
            if num and p["pins"]:
                pad.SetNet(net(netname(p, num)))
        b.Add(f); fps[p["ref"]] = f

    def padpos(ref, num):
        for pad in fps[ref].Pads():
            if pad.GetNumber() == num:
                q = pad.GetPosition(); return pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)
        raise KeyError((ref, num))

    report = {ref: {pad.GetNumber(): tuple(round(v, 3) for v in padpos(ref, pad.GetNumber())) for pad in f.Pads() if pad.GetNumber()} for ref, f in fps.items()}

    def add_via(x, y, n):
        v = pcbnew.PCB_VIA(b); v.SetPosition(VEC(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetDrill(MM(0.3)); v.SetWidth(MM(0.6)); v.SetNet(n); b.Add(v)

    for netn, w, pts in ROUTES:
        n = net(netn if netn in POWER else "/" + netn)
        layer = pcbnew.F_Cu
        prev = None
        for pt in pts:
            if pt[0] == "P": xy = padpos(pt[1], pt[2])
            elif pt[0] == "V": xy = (pt[1], pt[2])
            else: xy = pt
            if prev is not None and (abs(prev[0] - xy[0]) > 1e-6 or abs(prev[1] - xy[1]) > 1e-6):
                t = pcbnew.PCB_TRACK(b); t.SetStart(VEC(*prev)); t.SetEnd(VEC(*xy)); t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(n); b.Add(t)
            if pt[0] == "V":
                add_via(xy[0], xy[1], n)
                layer = pcbnew.B_Cu if layer == pcbnew.F_Cu else pcbnew.F_Cu
            prev = xy
    for x, y in GND_VIAS:
        add_via(x, y, net("GND"))

    # board outline with rounded corners
    x0, y0, x1, y1 = BOARD
    r = CORNER
    def seg(a, c):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(VEC(*a)); s.SetEnd(VEC(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)
    def arc(cx, cy, sx, sy, ex, ey):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        a1 =math.atan2(sy - cy, sx - cx); a2 = math.atan2(ey - cy, ex - cx)
        am = (a1 + a2) / 2 if abs(a2 - a1) < math.pi else (a1 + a2) / 2 + math.pi
        s.SetArcGeometry(VEC(sx, sy), VEC(cx + r * math.cos(am), cy + r * math.sin(am)), VEC(ex, ey)); b.Add(s)
    seg((x0 + r, y0), (x1 - r, y0)); seg((x1, y0 + r), (x1, y1 - r)); seg((x1 - r, y1), (x0 + r, y1)); seg((x0, y1 - r), (x0, y0 + r))
    arc(x1 - r, y0 + r, x1 - r, y0, x1, y0 + r); arc(x1 - r, y1 - r, x1, y1 - r, x1 - r, y1)
    arc(x0 + r, y1 - r, x0 + r, y1, x0, y1 - r); arc(x0 + r, y0 + r, x0, y0 + r, x0 + r, y0)

    # copper keepouts under the screw heads
    for ref in ("H1", "H2"):
        hx, hy, _ = PLACE[ref]
        z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline(); o.NewOutline()
        for i in range(48):
            a = 2 * math.pi * i / 48
            o.Append(MM(hx + HOLE_KEEPOUT_R * math.cos(a)), MM(hy + HOLE_KEEPOUT_R * math.sin(a)))
        z.SetZoneName("%s screw head keepout" % ref)
        b.Add(z)
    # ground pours, both layers
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net("GND"))
        z.SetLocalClearance(MM(0.2)); z.SetMinThickness(MM(0.2))
        z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        o = z.Outline(); o.NewOutline()
        for xx, yy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(MM(xx), MM(yy))
        z.SetZoneName("GND " + ("top" if layer == pcbnew.F_Cu else "bottom"))
        b.Add(z)

    # silkscreen: axes (BMI270 datasheet section 8.2, with U1 rotated 180 degrees), labels, board name on the back
    def sline(a, c, layer=pcbnew.F_SilkS, w=0.15):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(VEC(*a)); s.SetEnd(VEC(*c)); s.SetLayer(layer); s.SetWidth(MM(w)); b.Add(s)
    def stext(txt, x, y, size, layer=pcbnew.F_SilkS, thick=0.15, mirror=False, bold=False, just=0):
        t = pcbnew.PCB_TEXT(b); t.SetText(txt); t.SetPosition(VEC(x, y)); t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(thick)); t.SetBold(bold)
        if mirror: t.SetMirrored(True)
        if just: t.SetHorizJustify(just)
        b.Add(t); return t
    # axis glyph as one board-only footprint from the project library, so its own lines don't count as overlapping silk
    ox, oy = 110.6, 106.6
    lib_dir = os.path.join(PD, "lib", "imuBoard.pretty")
    ax = pcbnew.FOOTPRINT(b); ax.SetFPID(pcbnew.LIB_ID("", "AXES")); ax.SetReference("AX1"); ax.SetValue("AXES")
    ax.Reference().SetVisible(False); ax.Value().SetVisible(False); ax.Reference().SetLayer(pcbnew.F_Fab); ax.Value().SetLayer(pcbnew.F_Fab)
    ax.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    ax.SetLibDescription("BMI270 axes on centurion's IMU board (U1 rotated 180 degrees): +X toward J1, +Y toward H2, +Z up")
    def axline(a_, c_):
        s_ = pcbnew.PCB_SHAPE(ax); s_.SetShape(pcbnew.SHAPE_T_SEGMENT); s_.SetStart(VEC(*a_)); s_.SetEnd(VEC(*c_)); s_.SetLayer(pcbnew.F_SilkS); s_.SetWidth(MM(0.15)); ax.Add(s_)
    axline((0, 0.45), (0, 3.0)); axline((0, 3.0), (-0.5, 2.3)); axline((0, 3.0), (0.5, 2.3))     # +X down (toward J1)
    axline((0.45, 0), (3.0, 0)); axline((3.0, 0), (2.3, -0.5)); axline((3.0, 0), (2.3, 0.5))     # +Y right (toward H2)
    for rr in (0.45, 0.08):
        c2 = pcbnew.PCB_SHAPE(ax); c2.SetShape(pcbnew.SHAPE_T_CIRCLE); c2.SetCenter(VEC(0, 0)); c2.SetEnd(VEC(rr, 0)); c2.SetLayer(pcbnew.F_SilkS); c2.SetWidth(MM(0.15)); ax.Add(c2)
    for txt, tx, ty in (("X", 1.0, 2.6), ("Y", 2.6, -1.0), ("Z", -1.1, -0.9)):
        t_ = pcbnew.PCB_TEXT(ax); t_.SetText(txt); t_.SetPosition(VEC(tx, ty)); t_.SetLayer(pcbnew.F_SilkS)
        t_.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); t_.SetTextThickness(MM(0.15)); ax.Add(t_)
    pcbnew.FootprintSave(lib_dir, ax)
    ax = pcbnew.FootprintLoad(lib_dir, "AXES"); ax.SetFPID(pcbnew.LIB_ID("imuBoard", "AXES")); ax.SetReference("AX1")
    ax.SetPosition(VEC(ox, oy))
    b.Add(ax)
    stext("J5 CABLE", 108.6, 118.4, 0.8)
    bt = stext("CENTURION IMU", 119.0, 104.0, 2.4, pcbnew.B_SilkS, 0.48, True, True)
    bt2 = stext("UWAT VEXU - F26 - REV %s" % REV, 119.0, 107.2, 1.2, pcbnew.B_SilkS, 0.24, True, True)

    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    pcbnew.SaveBoard(path, b)

    # Chakra Petch for the board name, like centurion, powerJackal and stellaNova (pcbnew's Python can't set a font face)
    s = open(path, encoding="utf-8").read()
    for t in ("CENTURION IMU", "UWAT VEXU - F26 - REV %s" % REV):
        i = s.index('(gr_text "%s"' % t)
        j = s.index("(font", i)
        s = s[:j] + '(font\n\t\t\t\t(face "Chakra Petch")' + s[j + len("(font"):]
    open(path, "w", encoding="utf-8", newline="\n").write(s)
    return report

if __name__ == "__main__":
    write_schematic()
    rep = build_pcb()
    json.dump(rep, open(os.path.join(HERE, "pad_positions.json"), "w"), indent=1)
    print("schematic and board written to", PD)
    for ref in ("J1", "U2", "U1", "R1", "C1", "C2", "C3"):
        print(ref, rep[ref])
