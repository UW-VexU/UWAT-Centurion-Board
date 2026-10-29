"""Build the shared UWAT library: UWAT.kicad_sym (TPSM53602, ESP32-C3-MINI-1U) and UWAT.pretty (ESP32-C3-MINI-1U, 2016L fuse, Molex 4P4C, #8-32 hole)."""
import os, sys, uuid
OUT = sys.argv[1]
os.makedirs(os.path.join(OUT, "UWAT.pretty"), exist_ok=True)
F = '(effects (font (size 1.27 1.27)))'
FH = '(effects (font (size 1.27 1.27)) hide)'

def pin(etype, x, y, ang, name, num, hide=False, length=2.54):
    if hide and etype != "no_connect": etype = "passive"  # stacked duplicate: passive and hidden, so KiCad makes no implicit global net
    return (f'      (pin {etype} line (at {x:g} {y:g} {ang}) (length {length:g}){" hide" if hide else ""}\n'
            f'        (name "{name}" {F})\n        (number "{num}" {F})\n      )\n')

def symbol(name, ref, value, fp, ds, desc, kw, body, pins, ref_at, val_at):
    s = f'  (symbol "{name}" (in_bom yes) (on_board yes)\n'
    s += f'    (property "Reference" "{ref}" (at {ref_at[0]:g} {ref_at[1]:g} 0) {F})\n'
    s += f'    (property "Value" "{value}" (at {val_at[0]:g} {val_at[1]:g} 0) {F})\n'
    s += f'    (property "Footprint" "{fp}" (at 0 0 0) {FH})\n'
    s += f'    (property "Datasheet" "{ds}" (at 0 0 0) {FH})\n'
    s += f'    (property "ki_keywords" "{kw}" (at 0 0 0) {FH})\n'
    s += f'    (property "ki_description" "{desc}" (at 0 0 0) {FH})\n'
    s += f'    (symbol "{name}_0_1"\n      (rectangle (start {body[0]:g} {body[1]:g}) (end {body[2]:g} {body[3]:g}) (stroke (width 0.254) (type default)) (fill (type background)))\n    )\n'
    s += f'    (symbol "{name}_1_1"\n' + "".join(pins) + '    )\n  )\n'
    return s

# ---------- TPSM53602 (TI 36 V, 2 A buck module, B3QFN-14 RDA)
tp = [pin("power_in", -12.7, 5.08, 0, "VIN", "1"), pin("power_in", -12.7, 5.08, 0, "VIN", "14", hide=True),
      pin("input", -12.7, 0, 0, "EN", "2"),
      pin("power_out", 12.7, 5.08, 180, "VOUT", "7"), pin("power_out", 12.7, 5.08, 180, "VOUT", "8", hide=True),
      pin("input", 12.7, 0, 180, "FB", "9"), pin("open_collector", 12.7, -2.54, 180, "PGOOD", "6"),
      pin("power_out", 12.7, -5.08, 180, "V5V", "13"),
      pin("power_in", 5.08, -15.24, 90, "PGND", "15")] + \
     [pin("power_in", 5.08, -15.24, 90, "NC", n, hide=True) for n in ("3", "10", "11")] + \
     [pin("power_in", -5.08, -15.24, 90, "AGND", "12"),
      pin("no_connect", -5.08, 2.54, 0, "DNC", "4", hide=True), pin("no_connect", -5.08, -2.54, 0, "DNC", "5", hide=True)]
tpsm = symbol("TPSM53602", "U", "TPSM53602", "UWAT:Texas_B3QFN-14-1EP_5x5.5mm_P0.65mm_ThermalVia",
              "https://www.ti.com/lit/ds/symlink/tpsm53602.pdf",
              "36 V, 2 A step-down power module, 1 V to 7 V out, B3QFN-14 5 x 5.5 mm. NC pins 3, 10, 11 tie to PGND. DNC pins 4, 5 stay open.",
              "buck power module TPSM53602", (-10.16, 7.62, 10.16, -12.7), tp, (-10.16, 8.89), (-10.16, -17.78))

# ---------- ESP32-C3-MINI-1U (Espressif module, external antenna connector)
ep = [pin("power_in", -19.05, 20.32, 0, "3V3", "3"), pin("input", -19.05, 15.24, 0, "EN", "8"),
      pin("bidirectional", -19.05, 10.16, 0, "GPIO9/BOOT", "23"), pin("bidirectional", -19.05, 7.62, 0, "GPIO8", "22"),
      pin("bidirectional", -19.05, 5.08, 0, "GPIO2", "5"), pin("bidirectional", -19.05, 0, 0, "GPIO0", "12"),
      pin("bidirectional", -19.05, -2.54, 0, "GPIO1", "13")]
for name, num, y in (("GPIO18/USB_D-", "26", 20.32), ("GPIO19/USB_D+", "27", 17.78), ("GPIO20/U0RXD", "30", 12.7),
                     ("GPIO21/U0TXD", "31", 10.16), ("GPIO4", "18", 5.08), ("GPIO5", "19", 2.54), ("GPIO6", "20", 0),
                     ("GPIO7", "21", -2.54), ("GPIO10", "16", -7.62), ("GPIO3", "6", -10.16)):
    ep.append(pin("bidirectional", 19.05, y, 180, name, num))
gnds = ["1", "2", "11", "14"] + [str(n) for n in range(36, 54)]
ep += [pin("power_in", 0, -25.4, 90, "GND", n, hide=i > 0) for i, n in enumerate(gnds)]
ncs = ["4", "7", "9", "10", "15", "17", "24", "25", "28", "29", "32", "33", "34", "35"]
ep += [pin("no_connect", -8.89 + i * 1.27, -17.78, 0, "NC", n, hide=True) for i, n in enumerate(ncs)]
esp = symbol("ESP32-C3-MINI-1U", "U", "ESP32-C3-MINI-1U-N4X", "UWAT:ESP32-C3-MINI-1U",
             "https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf",
             "ESP32-C3 RISC-V module, 4 MB flash, built-in USB serial/JTAG on GPIO18/19, external antenna connector, 13.2 x 12.5 mm",
             "ESP32-C3 module USB", (-16.51, 22.86, 16.51, -22.86), ep, (-16.51, 24.13), (-16.51, -27.94))

open(os.path.join(OUT, "UWAT.kicad_sym"), "w").write("(kicad_symbol_lib (version 20220914) (generator uwat_gen)\n" + tpsm + esp + ")\n")

# ---------- footprints
def fp_header(name, descr, tags, smd=True):
    return (f'(footprint "{name}" (version 20221018) (generator uwat_gen)\n  (layer "F.Cu")\n  (descr "{descr}")\n  (tags "{tags}")\n'
            f'  (attr {"smd" if smd else "through_hole"})\n')
def text(kind, val, x, y, layer, hide=False, size=1.0):
    return f'  (fp_text {kind} "{val}" (at {x:g} {y:g}) (layer "{layer}"){" hide" if hide else ""}\n    (effects (font (size {size:g} {size:g}) (thickness {size*0.15:g})))\n  )\n'
def rect(x0, y0, x1, y1, layer, w):
    return f'  (fp_rect (start {x0:g} {y0:g}) (end {x1:g} {y1:g}) (stroke (width {w:g}) (type solid)) (fill none) (layer "{layer}"))\n'
def line(x0, y0, x1, y1, layer, w):
    return f'  (fp_line (start {x0:g} {y0:g}) (end {x1:g} {y1:g}) (stroke (width {w:g}) (type solid)) (layer "{layer}"))\n'

# ESP32-C3-MINI-1U: Espressif's own footprint (github.com/espressif/kicad-libraries), 3D model kept with the project
import shutil, glob
ESPLIB = os.environ["ESPLIB"]   # a clone of github.com/espressif/kicad-libraries
src = open(os.path.join(ESPLIB, "footprints", "Espressif.pretty", "ESP32-C3-MINI-1U.kicad_mod")).read()
src = src.replace("${KICAD8_3RD_PARTY}/3dmodels/com_github_espressif_kicad-libraries/espressif.3dshapes/ESP32-C3-MINI-1U.STEP",
                  "${KIPRJMOD}/../lib/3d/ESP32-C3-MINI-1U.STEP")
assert "${KIPRJMOD}/../lib/3d/ESP32-C3-MINI-1U.STEP" in src
open(os.path.join(OUT, "UWAT.pretty", "ESP32-C3-MINI-1U.kicad_mod"), "w").write(src)
os.makedirs(os.path.join(OUT, "3d"), exist_ok=True)
shutil.copy(os.path.join(ESPLIB, "3dmodels", "espressif.3dshapes", "ESP32-C3-MINI-1U.STEP"), os.path.join(OUT, "3d", "ESP32-C3-MINI-1U.STEP"))
for old in glob.glob(os.path.join(OUT, "UWAT.pretty", "LTM8023*")): os.remove(old)

# TPSM53602 (TI RDA B3QFN-14): KiCad's thermal-via footprint with the 11 exposed-pad vias opened from 0.2 to 0.3 mm drill
src = open(os.path.join(os.environ.get("KICAD_FOOTPRINT_DIR", "/usr/share/kicad/footprints"), "Package_DFN_QFN.pretty", "Texas_B3QFN-14-1EP_5x5.5mm_P0.65mm_ThermalVia.kicad_mod").read()
n = src.count("(size 0.5 0.5) (drill 0.2)")
assert n == 11, n
src = src.replace("(size 0.5 0.5) (drill 0.2)", "(size 0.6 0.6) (drill 0.3)")
n2 = src.count('(size 0.6 0.6) (drill 0.3) (layers "*.Cu" "*.Mask")')
assert n2 == 11, n2
src = src.replace('(size 0.6 0.6) (drill 0.3) (layers "*.Cu" "*.Mask")', '(size 0.6 0.6) (drill 0.3) (layers "*.Cu" "F.Mask")')   # tented on the back
src = src.replace("${KICAD7_3DMODEL_DIR}", "${KICAD10_3DMODEL_DIR}") if False else src
open(os.path.join(OUT, "UWAT.pretty", "Texas_B3QFN-14-1EP_5x5.5mm_P0.65mm_ThermalVia.kicad_mod"), "w").write(src)

# Littelfuse 2016L: recommended land 1.5 x 3.4 mm pads, 4.6 mm overall
s = fp_header("Fuse_Littelfuse_2016L", "Littelfuse 2016L PolySwitch PTC, recommended land pattern 1.5x3.4 mm pads, 4.6 mm overall", "fuse PTC polyswitch 2016")
s += text("reference", "REF**", 0, -2.9, "F.SilkS") + text("value", "2016L", 0, 2.9, "F.Fab") + text("user", "${REFERENCE}", 0, 0, "F.Fab", size=0.8)
s += rect(-2.6, -2.1, 2.6, 2.1, "F.Fab", 0.1) + rect(-3.0, -2.3, 3.0, 2.3, "F.CrtYd", 0.05)
s += line(-0.6, -2.2, 0.6, -2.2, "F.SilkS", 0.12) + line(-0.6, 2.2, 0.6, 2.2, "F.SilkS", 0.12)
s += '  (pad "1" smd roundrect (at -1.55 0) (size 1.5 3.4) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))\n'
s += '  (pad "2" smd roundrect (at 1.55 0) (size 1.5 3.4) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))\n)\n'
open(os.path.join(OUT, "UWAT.pretty", "Fuse_Littelfuse_2016L.kicad_mod"), "w").write(s)

# Molex 95501-2441: placeholder on the common 1.27 mm staggered 4P4C pattern (KiCad RJ9 Evercom geometry). Replace with the Molex drawing.
src = open("/usr/share/kicad/footprints/Connector_RJ.pretty/RJ9_Evercom_5301-440xxx_Horizontal.kicad_mod").read()
src = src.replace('(footprint "RJ9_Evercom_5301-440xxx_Horizontal"', '(footprint "Molex_95501-2441_4P4C_Horizontal"', 1)
src = src.replace('(module RJ9_Evercom_5301-440xxx_Horizontal', '(module Molex_95501-2441_4P4C_Horizontal', 1)
import re
src = re.sub(r'\(descr "[^"]*"\)', '(descr "PLACEHOLDER for Molex 95501-2441 4P4C right angle jack. Uses the 1.27 mm staggered 4P4C pattern. Check holes and pegs against Molex SD-95501 before ordering boards.")', src, count=1)
open(os.path.join(OUT, "UWAT.pretty", "Molex_95501-2441_4P4C_Horizontal.kicad_mod"), "w").write(src)
# #8-32 VEX mounting hole: 4.5 mm close-fit NPTH (the screw is 4.17 mm), courtyard covers a button head
s = fp_header("MountingHole_4.5mm_8-32", "Mounting hole for a #8-32 VEX screw, 4.5 mm close fit, no copper", "mounting hole 8-32 VEX", smd=False)
s += text("reference", "REF**", 0, -5.4, "F.SilkS", hide=True) + text("value", "#8-32", 0, 5.4, "F.Fab")
s += '  (fp_circle (center 0 0) (end 4.0 0) (stroke (width 0.15) (type solid)) (fill none) (layer "Cmts.User"))\n'
s += '  (fp_circle (center 0 0) (end 4.6 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))\n'
s += '  (pad "" np_thru_hole circle (at 0 0) (size 4.5 4.5) (drill 4.5) (layers "*.Cu" "*.Mask"))\n)\n'
open(os.path.join(OUT, "UWAT.pretty", "MountingHole_4.5mm_8-32.kicad_mod"), "w").write(s)

# bare copper test pad: the same 3.4 x 1.8 mm land as a Keystone 5015 loop, so a loop can still be soldered on later.
# No paste (stays bare copper with the board finish), nothing to buy, so it stays out of the BOM and pick-and-place.
s = fp_header("TestPad_3.4x1.8mm", "Bare copper test pad, 3.4 x 1.8 mm, Keystone 5015 land", "test point pad bare")
s = s.replace("(attr smd)", "(attr smd exclude_from_pos_files exclude_from_bom)")
s += text("reference", "REF**", 0, -2.25, "F.SilkS") + text("value", "TestPad", 0, 2.25, "F.Fab")
s += text("user", "${REFERENCE}", 0, 0, "F.Fab", size=0.6)
s += rect(-1.9, -1.1, 1.9, 1.1, "F.SilkS", 0.15) + rect(-2.15, -1.35, 2.15, 1.35, "F.CrtYd", 0.05) + rect(-1.7, -0.9, 1.7, 0.9, "F.Fab", 0.1)
s += '  (pad "1" smd rect (at 0 0) (size 3.4 1.8) (layers "F.Cu" "F.Mask"))\n)\n'
open(os.path.join(OUT, "UWAT.pretty", "TestPad_3.4x1.8mm.kicad_mod"), "w").write(s)
print("library written to", OUT)
