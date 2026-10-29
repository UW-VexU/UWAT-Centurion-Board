"""Hand routing for spots where autorouted copper is untidy. Runs after tidy_tracks.py.
Rules: tracks enter pads straight along a pad axis, branches tap a run with a square T, 45 degree bends only,
one width per run, Kelvin sense lines leave the shunt pads at their inner edges.
Segments are edited as records in the board file (deleting items through pcbnew corrupts the board), then pcbnew refills the pours.
usage: python3 hand_routes.py in.kicad_pcb out.kicad_pcb"""
import sys, re, math, uuid
import pcbnew
from pcb_common import OX, OY
from pcb_place import PLACE, rot_pt

IN, OUT = sys.argv[1], sys.argv[2]
txt = open(IN).read()
def drop_footprint(text, ref):
    """Cut one footprint block out of the board text (pcbnew Remove corrupts the board)."""
    i = text.index(f'(fp_text reference "{ref}"'); s = text.rfind("\n  (footprint ", 0, i) + 1
    d = 0
    for k in range(s + 2, len(text)):      # from the footprint's opening paren
        d += (text[k] == "(") - (text[k] == ")")
        if d == 0: break
    return text[:s] + text[k + 2:]
if '(fp_text reference "JP4"' in txt: txt = drop_footprint(txt, "JP4")      # JP4 replaced by Q1, the USB power switch
NETS = {m[2]: int(m[1]) for m in re.finditer(r'^  \(net (\d+) "([^"]*)"\)', txt, re.M)}
SEG_RE = re.compile(r'^  \(segment( locked)? \(start (\S+) (\S+)\) \(end (\S+) (\S+)\) \(width (\S+)\) \(layer "([^"]+)"\) \(net (\d+)\) \(tstamp [^)]+\)\)\n', re.M)
VIA_RE = re.compile(r'^  \(via( locked)? \(at (\S+) (\S+)\) (.*)\(net (\d+)\) \(tstamp [^)]+\)\)\n', re.M)
segs = [dict(locked=bool(m[1]), a=(float(m[2]) - OX, float(m[3]) - OY), b=(float(m[4]) - OX, float(m[5]) - OY), w=float(m[6]),
             layer=m[7], net=int(m[8])) for m in SEG_RE.finditer(txt)]
vias = [dict(locked=bool(m[1]), at=(float(m[2]) - OX, float(m[3]) - OY), rest=m[4], net=int(m[5])) for m in VIA_RE.finditer(txt)]
NAME = {v: k for k, v in NETS.items()}
log = []

def net(n): return NETS["/" + n] if "/" + n in NETS else NETS[n]
def close(p, q, tol=0.003): return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol
def inbox(p, box): return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
def remove_in_box(nets, box, layer="F.Cu", keep=lambda s: False):
    global segs
    ids = {net(n) for n in nets}; before = len(segs)
    segs = [s for s in segs if not (s["net"] in ids and s["layer"] == layer and inbox(s["a"], box) and inbox(s["b"], box) and not keep(s) and not s.get("new"))]
    log.append(f"removed {before - len(segs)} segments of {', '.join(nets)}")
def remove_seg(n, a, b, layer="F.Cu"):
    global segs
    k = len(segs)
    segs = [s for s in segs if not (s["net"] == net(n) and s["layer"] == layer and
                                    ((close(s["a"], a) and close(s["b"], b)) or (close(s["a"], b) and close(s["b"], a))))]
    assert len(segs) == k - 1, ("segment not found", n, a, b)
def path(n, pts, w, layer="F.Cu"):
    for a, b in zip(pts, pts[1:]):
        segs.append(dict(locked=True, a=a, b=b, w=w, layer=layer, net=net(n), new=True))
MOVES = {}
def move_fp(ref, x, y, rot=None): MOVES[ref] = (x, y, rot)
def move_via(n, old, new):
    for v in vias:
        if v["net"] == net(n) and close(v["at"], old):
            v["at"] = new; return
    raise SystemExit(f"via not found {n} {old}")
def drop_via(n, at):
    global vias
    k = len(vias); vias = [v for v in vias if not (v["net"] == net(n) and close(v["at"], at))]
    assert len(vias) == k - 1, ("via not found", n, at)
def set_end(n, layer, old, new):
    hit = 0
    for s in segs:
        if s["net"] == net(n) and s["layer"] == layer:
            for e in ("a", "b"):
                if close(s[e], old): s[e] = new; hit += 1
    assert hit, ("no segment end at", n, old)
VIA = '(size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") '
def add_via(n, x, y): vias.append(dict(locked=True, at=(x, y), rest=VIA, net=net(n)))
def cell(u):
    ux, uy, ur = PLACE[u]
    return lambda lx, ly: tuple(round(v, 4) for v in (ux + rot_pt(lx, ly, ur)[0], uy + rot_pt(lx, ly, ur)[1]))

# ======================================================================= R2 / R9 / TP3 / U3 (5 V side)
# 5 V: one straight 0.8 mm bus at the height of the via that takes 5 V down to J6. R2.2, TP3 and R9.1 join it with straight stubs.
VIA5 = (60.784, 8.056); BUS = VIA5[1]
remove_in_box(["5V", "5V_MOD", "3V3"], (48.5, 4.5, 61.0, 13.45))
remove_seg("5V_MOD", (44.009, 10.089), (51.526, 10.089))
path("5V", [(49.188, 5.0), (49.188, BUS - 1.2), (49.188 + 1.2, BUS), (54.963, BUS), (59.1, BUS), VIA5], 0.8)   # R9.1 down, 45, east to the via
path("5V", [(54.963, 10.6), (54.963, BUS)], 0.8)                                                                # R2.2 straight up
path("5V", [(59.1, 5.0), (59.1, BUS)], 0.8)                                                                     # TP3 straight down
path("5V_MOD", [(44.009, 10.089), (52.037, 10.089)], 0.8)                                                        # straight into R2.1 (from the T above C4)
# Kelvin sense, in the sense cell's own frame (rot 0: INA226 at 0,0, shunt pad 1 at (5.0,-3.563), pad 2 at (5.0,-0.637), pins 10/9 at x 2.2)
def kelvin(u, plus, minus):
    G = cell(u)
    path(plus, [G(4.5, -3.15), G(4.0, -3.15), G(3.5, -2.65), G(3.5, -1.5), G(3.0, -1.0), G(2.2, -1.0)], 0.25)    # pad 1 inner edge -> pin 10
    path(minus, [G(4.5, -1.0), G(4.0, -1.0), G(3.5, -0.5), G(2.2, -0.5)], 0.25)                                 # pad 2 inner edge -> pin 9
    path(minus, [G(2.2, -0.5), G(2.2, 0.0)], 0.25)                                                               # pin 9 to pin 8 (VBUS)
kelvin("U3", "5V_MOD", "5V")
# 3V3 to C7 and the via down to the rail: straight out of pin 6, one 45, straight through C7.1 to the via
move_via("3V3", (60.0, 11.51), (60.0, 11.55)); set_end("3V3", "B.Cu", (60.0, 11.51), (60.0, 11.55))
path("3V3", [(56.6, 13.4), (56.6, 12.45), (57.5, 11.55), (58.4, 11.55), (60.0, 11.55)], 0.3)

# ======================================================================= inputs: J1, D5, TP1, D3, F1, R1 / U2
remove_in_box(["VPORT"], (15.0, 9.0, 24.0, 18.5))
path("VPORT", [(16.54, 17.41), (20.2, 13.75), (21.5, 13.75)], 0.8)                     # off J1's round pin at 45, straight into D5.2
path("VPORT", [(21.5, 13.6), (21.5, 10.4)], 0.8)                                       # D5.2 straight up into TP1
remove_in_box(["VIN_OR"], (14.0, 16.0, 24.0, 27.0))
path("VIN_OR", [(21.5, 17.6), (21.5, 21.05)], 0.8)                                     # D5.1 straight down into F1.1
path("VIN_OR", [(16.0, 26.1), (16.0, 24.65), (19.6, 21.05), (22.0, 21.05)], 0.8)       # D3.1 up, 45, straight into F1.1
remove_in_box(["VFUSE"], (21.5, 21.0, 29.5, 24.7))
path("VFUSE", [(22.0, 24.15), (26.1, 24.15)], 0.8)                                     # F1.2 straight into R1.1
remove_in_box(["VIN_MOD"], (24.5, 19.5, 29.5, 22.5))
remove_in_box(["VIN_MOD"], (23.8, 4.5, 25.5, 20.5), layer="B.Cu")
move_via("VIN_MOD", (24.979, 20.016), (24.6, 21.138))
path("VIN_MOD", [(24.6, 5.0), (24.6, 21.138)], 0.8, layer="B.Cu")                       # C1 to the via beside R1, one straight run
path("VIN_MOD", [(24.6, 21.138), (26.1, 21.138)], 0.8)                                  # straight into R1.2
kelvin("U2", "VFUSE", "VIN_MOD")
# U2 supply and ground
remove_in_box(["3V3"], (26.8, 16.0, 29.0, 19.6))
path("3V3", [(27.05, 16.1), (27.05, 17.7)], 0.3)                                        # via straight down into C6.1
path("3V3", [(27.05, 17.7), (27.05, 18.7), (27.85, 19.5), (28.9, 19.5)], 0.3)           # C6.1 down, 45, straight into pin 6
move_via("3V3", (27.01, 16.1), (27.05, 16.1))
remove_seg("3V3", (27.01, 16.1), (28.3, 17.2), layer="B.Cu"); remove_seg("3V3", (28.3, 17.2), (28.3, 23.7), layer="B.Cu")
path("3V3", [(27.05, 16.1), (28.3, 17.35), (28.3, 23.7)], 0.3, layer="B.Cu")
move_via("GND", (27.5, 20.0), (27.3, 20.0)); set_end("GND", "F.Cu", (27.5, 20.0), (27.3, 20.0))
move_via("GND", (25.19, 16.4), (25.5, 16.4)); set_end("GND", "F.Cu", (25.19, 16.4), (25.5, 16.4)); set_end("GND", "F.Cu", (25.19, 17.7), (25.5, 17.7))   # C6.2 via clear of the VIN_MOD run
remove_seg("GND", (33.3, 21.5), (34.1, 22.5)); drop_via("GND", (34.1, 22.5))
path("GND", [(33.3, 21.0), (34.4, 21.0)], 0.25); vias.append(dict(locked=True, at=(34.4, 21.0), rest='(size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") ', net=net("GND")))
# I2C out of U2: both leave their pins outward, SDA in the inner lane, SCL in the outer lane
remove_in_box(["SDA"], (32.0, 19.8, 34.2, 26.0))
path("SDA", [(33.3, 20.0), (34.55, 20.0), (35.05, 20.5), (35.05, 24.025), (35.05, 25.6), (34.55, 26.1), (32.012, 26.1)], 0.25)
path("SDA", [(35.05, 24.025), (34.128, 24.025)], 0.25)                                 # tap to the via that takes SDA to U3, U5 and the ESP32
remove_in_box(["SCL"], (31.9, 19.0, 49.3, 28.2))
path("SCL", [(33.3, 19.5), (35.05, 19.5), (35.55, 20.0), (35.55, 26.862), (35.55, 27.6), (35.05, 28.1), (33.247, 28.1), (32.012, 28.1)], 0.25)
path("SCL", [(35.55, 26.862), (41.0, 26.862)], 0.25); add_via("SCL", 41.0, 26.862)     # drops to the bottom before D2
# SCL passes D2 and U6 on the bottom layer, so no top copper runs under their bodies or past U6's tab
remove_in_box(["SCL"], (49.0, 24.9, 51.2, 27.0))
path("SCL", [(41.0, 26.862), (49.0, 26.862), (50.85, 25.012), (52.5, 25.012)], 0.25, layer="B.Cu"); add_via("SCL", 52.5, 25.012)
# ======================================================================= regulator: D1, C2, C3, C8, U1, C4, C5, R3, R4
remove_in_box(["VIN_MOD"], (31.5, 1.0, 38.5, 17.0))
path("VIN_MOD", [(31.6, 2.2), (32.6, 2.2), (32.6, 3.5), (33.1, 4.0), (35.95, 4.0)], 0.8)   # TP2 down, 45, straight into D1.1
path("VIN_MOD", [(34.95, 4.0), (34.95, 11.5)], 0.8)                                       # D1.1 straight down into C2.1
path("VIN_MOD", [(34.575, 11.6), (36.955, 11.6)], 0.8)                                    # C2.1 straight into VIN (pin 14)
path("VIN_MOD", [(36.955, 9.65), (36.955, 11.6)], 0.8)                                    # C8.1 straight down into pin 14
path("VIN_MOD", [(34.575, 11.5), (34.575, 15.7)], 0.8)                                    # C2.1 to C3.1
path("VIN_MOD", [(34.575, 15.6), (36.955, 15.6)], 0.8)                                    # C3.1 straight into VIN (pin 1)
path("VIN_MOD", [(37.93, 15.95), (36.955, 15.95)], 0.25)                                  # pin 2 to pin 1
move_fp("R3", 42.7, 8.0); move_fp("R4", 40.5, 8.0)                                        # 0.5 mm up so the 5V_MOD run clears R3.2
remove_in_box(["5V_MOD"], (41.0, 7.0, 44.5, 16.0))
path("5V_MOD", [(41.43, 11.6), (43.425, 11.6)], 0.8)                                     # VOUT pin 8 straight into C4.1
path("5V_MOD", [(41.43, 15.6), (43.425, 15.6)], 0.8)                                     # VOUT pin 7 straight into C5.1
path("5V_MOD", [(43.425, 11.6), (43.425, 15.6)], 0.8)
path("5V_MOD", [(43.425, 11.6), (43.425, 10.36), (43.696, 10.089), (44.009, 10.089)], 0.8)   # C4.1 up onto the run to R2
path("5V_MOD", [(44.009, 10.089), (44.009, 7.388), (43.709, 7.088), (42.7, 7.088)], 0.8)     # T up to R3.1 (RFBT top)
remove_in_box(["FB"], (40.0, 8.5, 43.5, 11.5))
path("FB", [(42.7, 8.912), (40.5, 8.912)], 0.25)                                          # R3.2 to R4.1
path("FB", [(40.53, 8.912), (40.53, 11.25)], 0.25)                                        # R4.1 straight down into FB (pin 9)
# PGOOD: one straight run down from U1.6 with square taps into TP10 and R7.2, then a via beside R7.2
remove_in_box(["PGOOD"], (37.5, 15.5, 45.0, 26.0))
path("PGOOD", [(40.53, 15.95), (40.53, 21.6), (40.53, 23.788), (40.13, 24.188), (39.1, 24.188), (37.8, 24.188)], 0.25)
path("PGOOD", [(40.53, 21.6), (38.5, 21.6)], 0.25)                                           # tap left into TP10 (moved beside the run)
move_via("PGOOD", (38.081, 25.155), (37.8, 24.188))
remove_in_box(["PGOOD"], (35.5, 24.5, 39.0, 39.6), layer="B.Cu")
move_via("PGOOD", (36.086, 39.4), (37.8, 39.4)); remove_seg("PGOOD", (37.0, 39.4), (36.086, 39.4))
path("PGOOD", [(37.8, 24.188), (37.8, 39.4)], 0.25, layer="B.Cu")
path("PGOOD", [(37.0, 39.4), (37.8, 39.4)], 0.25)                                           # pin 6 straight out to its via

# ======================================================================= ESP32-C3: support parts lined up with the pins they serve
move_fp("R22", 26.988, 31.9); move_fp("R20", 33.612, 32.4); move_fp("LED3", 37.0, 32.4)
move_fp("C9", 39.0, 36.85); move_fp("R21", 39.0, 41.112); move_fp("C13", 39.0, 44.5)
move_fp("R17", 41.8, 33.2); move_fp("C15", 41.8, 36.6, 270); move_fp("C12", 41.8, 40.65); move_fp("SW2", 46.0, 39.4)
# 3V3 to the IO8 pull-up: the old route ran under D4; now a short hop on the bottom layer past JP4 and the 5V_LDO line
remove_in_box(["3V3"], (21.0, 27.9, 26.7, 32.5)); remove_seg("3V3", (22.167, 28.1), (30.188, 28.1))
path("3V3", [(25.0, 28.1), (30.188, 28.1)], 0.3); add_via("3V3", 25.0, 28.1)
path("3V3", [(25.0, 28.1), (25.0, 31.9)], 0.3, layer="B.Cu"); add_via("3V3", 25.0, 31.9)
path("3V3", [(25.0, 31.9), (26.076, 31.9)], 0.3)                                            # straight into R22.1
remove_in_box(["IO8"], (27.5, 32.0, 28.6, 34.6)); path("IO8", [(27.9, 31.9), (27.9, 34.5)], 0.25)   # R22.2 straight down into pin 22
# BOOT, SDA, SCL leave their top-row pins outward to vias just outside the module, nothing runs under it
remove_in_box(["BOOT"], (26.9, 34.4, 29.5, 35.6)); drop_via("BOOT", (29.274, 35.419))
remove_seg("BOOT", (35.229, 41.373), (29.274, 35.419), layer="B.Cu"); remove_seg("BOOT", (40.55, 41.373), (35.229, 41.373), layer="B.Cu")
remove_in_box(["BOOT"], (40.4, 35.5, 50.0, 46.0)); drop_via("BOOT", (40.55, 41.373))
path("BOOT", [(27.1, 34.5), (27.1, 33.35)], 0.25); add_via("BOOT", 27.1, 33.35)
path("BOOT", [(27.1, 33.35), (34.75, 41.0), (44.1, 41.0)], 0.25, layer="B.Cu"); add_via("BOOT", 44.1, 41.0)
path("BOOT", [(44.1, 36.25), (44.1, 41.0), (44.1, 42.55)], 0.25)                          # SW2.1 pads: joined inside the switch, KiCad 7 still wants copper
path("BOOT", [(44.1, 42.55), (44.1, 43.5), (44.6, 44.0), (49.213, 44.0), (49.713, 44.5), (49.713, 45.4)], 0.25)   # on to R23.2
for a, b_ in (((31.1, 34.5), (31.1, 33.751)), ((31.1, 33.751), (30.929, 33.58))): remove_seg("SDA", a, b_)
for a, b_ in (((30.929, 33.58), (30.929, 27.224)), ((30.929, 27.224), (34.128, 24.025))): remove_seg("SDA", a, b_, layer="B.Cu")
move_via("SDA", (30.929, 33.58), (31.1, 33.65))
path("SDA", [(31.1, 34.5), (31.1, 33.65)], 0.25); path("SDA", [(31.1, 33.65), (34.128, 30.622), (34.128, 24.025)], 0.25, layer="B.Cu")
for a, b_ in (((30.3, 34.5), (30.3, 35.227)), ((30.3, 35.227), (31.073, 36.0)), ((31.073, 36.0), (33.296, 36.0))): remove_seg("SCL", a, b_)
for a, b_ in (((33.296, 28.149), (33.247, 28.1)), ((33.296, 36.0), (33.296, 28.149))): remove_seg("SCL", a, b_, layer="B.Cu")
drop_via("SCL", (33.296, 36.0)); add_via("SCL", 30.3, 33.3)
path("SCL", [(30.3, 34.5), (30.3, 33.3)], 0.25); path("SCL", [(30.3, 33.3), (33.247, 30.353), (33.247, 28.1)], 0.25, layer="B.Cu")
# status LED: R20 sits over pin 16 now
remove_seg("LED_STAT", (32.7, 33.512), (31.588, 32.4)); remove_seg("LED_STAT", (32.7, 34.5), (32.7, 33.512))
path("LED_STAT", [(32.7, 32.4), (32.7, 34.5)], 0.25)
remove_seg("LED3_A", (35.362, 32.4), (33.412, 32.4)); path("LED3_A", [(34.524, 32.4), (36.063, 32.4)], 0.25)
# EN: pin 8 straight into C9.1, up between the part columns into R17.2, then over SW2 to SW1.1
remove_in_box(["EN"], (36.5, 31.5, 50.6, 43.0))
path("EN", [(37.0, 37.8), (39.0, 37.8), (40.05, 37.8), (40.4, 37.45), (40.4, 32.488), (40.6, 32.288), (41.8, 32.288)], 0.25)
path("EN", [(41.8, 32.288), (43.8, 32.288), (44.3, 32.788), (44.3, 34.573), (44.8, 35.073), (49.7, 35.073), (50.2, 35.573), (50.2, 36.75)], 0.25)
move_fp("SW1", 52.1, 39.9)                                                                     # 0.5 mm down: room to enter SW1.1 straight from above
path("EN", [(50.2, 36.75), (50.2, 43.05)], 0.25)                                             # SW1.1 pad pair
# IO2: pin 5 straight into R21.2
remove_seg("IO2", (37.0, 40.2), (37.738, 40.2)); remove_seg("IO2", (37.738, 40.2), (39.0, 38.938))
path("IO2", [(37.0, 40.2), (39.0, 40.2)], 0.25)
# 3V3: pin 3 straight through R21.1 and C12.1 onto a spine that also takes R17.1 and C15.1, down to one line through C13.1, the feed via and R23.1
remove_in_box(["3V3"], (36.9, 33.5, 48.5, 46.0))
for a, b_ in (((55.8, 35.7), (46.869, 44.631)), ((46.869, 44.631), (46.869, 45.052))): remove_seg("3V3", a, b_, layer="B.Cu")
drop_via("3V3", (46.869, 45.052)); add_via("3V3", 46.1, 45.4)
path("3V3", [(58.8, 38.6), (52.0, 45.4), (46.1, 45.4)], 0.3, layer="B.Cu")
path("3V3", [(37.0, 41.8), (43.1, 41.8)], 0.3)
path("3V3", [(41.8, 34.112), (42.8, 34.112), (43.1, 34.412), (43.1, 35.65), (43.1, 41.8), (43.1, 45.4)], 0.3)
path("3V3", [(41.8, 35.65), (43.1, 35.65)], 0.3)
path("3V3", [(39.0, 45.4), (43.1, 45.4), (46.1, 45.4), (47.887, 45.4)], 0.3)
add_via("GND", 40.35, 39.19); path("GND", [(41.8, 39.19), (40.35, 39.19)], 0.4)             # ground between the part columns: C12.2 straight to a via

# ======================================================================= right side: LDO, U5 sense cell, U3 bottom pins, J9, J3
# Old copper here is cleared by area (tidy_tracks can shift its corners from run to run), then laid again by hand.
move_fp("TP10", 38.5, 21.6)                       # off the 5 V run, beside PGOOD
# 5 V out to J6: both layers enter J6.1 from the left along its long axis. F.Cu runs on to D2, B.Cu comes down from the 5 V via.
remove_in_box(["5V"], (42.5, 16.0, 65.0, 25.2))
path("5V", [(64.35, 16.6), (62.0, 16.6), (58.224, 20.376), (46.174, 20.376), (43.1, 23.45), (43.1, 25.1)], 0.8)
remove_in_box(["5V"], (60.0, 7.5, 65.0, 17.0), layer="B.Cu")
path("5V", [(60.784, 8.056), (61.4, 8.672), (61.4, 15.6), (62.4, 16.6), (64.35, 16.6)], 0.8, layer="B.Cu")
# USB power switch Q1 (AO3401A, SOT-23, rotated 180): drain on the left takes USB_PWR straight from D4, source (top right)
# feeds 5V_LDO straight into D2.1, gate (bottom right) drops through a via and runs on the bottom up to D2.2 (5 V rail).
# D2.1 -> LDO input: straight 0.8 mm line, C10 tapped straight down.
Q1 = (39.35, 29.65); QD, QS, QG = (Q1[0] - 0.9375, Q1[1]), (Q1[0] + 0.9375, Q1[1] - 0.95), (Q1[0] + 0.9375, Q1[1] + 0.95)
remove_in_box(["5V_LDO"], (27.0, 28.5, 47.0, 33.5))
LDO_Y = 29.65
path("5V_LDO", [QS, (43.1, QS[1])], 0.6)                                                        # source straight into D2.1
path("5V_LDO", [(43.1, LDO_Y), (45.425, LDO_Y), (46.8, LDO_Y)], 0.8)
path("5V_LDO", [(45.425, LDO_Y), (45.425, 33.2)], 0.8)
remove_in_box(["USB_PWR"], (22.0, 28.5, 40.0, 30.5))
path("USB_PWR", [(23.1, LDO_Y), QD], 0.4)                                                       # D4 straight into Q1's drain
GV = (QG[0], 31.6); FV = (41.5, 25.1)
path("5V", [QG, GV], 0.25); add_via("5V", *GV)
path("5V", [GV, (GV[0], FV[1] + (41.0 - GV[0])), (41.0, FV[1]), FV], 0.25, layer="B.Cu"); add_via("5V", *FV)
path("5V", [FV, (43.1, FV[1])], 0.25)                                                           # into D2.2 from the left
# LDO output: right, 45, straight up into R12.1. C11 now sits right under the LDO output pin.
move_fp("C11", 52.875, 33.1)
remove_in_box(["3V3_LDO"], (50.0, 26.5, 57.0, 34.0))
path("3V3_LDO", [(51.4, 30.25), (52.7, 30.25), (53.62, 29.33), (53.62, 27.1)], 0.8)       # outer half of R12.1
path("3V3_LDO", [(51.4, 30.25), (51.4, 33.1)], 0.8)
path("3V3_LDO", [(54.27, 27.6), (54.27, 28.12), (54.75, 28.6), (55.9, 28.6), (56.4, 29.1), (56.4, 29.9)], 0.25)   # U5 IN+ from R12.1's inner edge
# 3V3 at the top of U5: R12.2 out to a via, IN- Kelvin from the inner edge, pin 9 to pin 8, VS through C14.1 to a via, on to J9.1
remove_in_box(["3V3"], (55.5, 26.0, 63.0, 30.5))
remove_in_box(["3V3"], (61.0, 29.5, 65.0, 38.5))                                             # old J9 -> TP4 run
drop_via("3V3", (61.8, 28.01))
path("3V3", [(56.762, 27.1), (57.75, 27.1)], 0.3); add_via("3V3", 57.75, 27.1)
path("3V3", [(56.4, 27.6), (56.4, 28.1), (56.9, 28.6), (56.9, 29.9)], 0.25); path("3V3", [(56.9, 29.9), (57.4, 29.9)], 0.25)
path("3V3", [(58.4, 29.9), (58.4, 28.95), (59.3, 28.05), (60.2, 28.05), (61.8, 28.05)], 0.3); add_via("3V3", 61.8, 28.05)
path("3V3", [(61.8, 28.05), (61.8, 29.65), (62.25, 30.1), (64.35, 30.1)], 0.3)                # straight into J9.1
# 3V3 on the bottom: the rail from the via by C7 straight down, R12.2's via tees in, then down the right side to TP4 and J3
remove_in_box(["3V3"], (55.0, 11.0, 65.0, 37.0), layer="B.Cu")
path("3V3", [(60.0, 11.55), (60.0, 18.65), (60.0, 27.1)], 0.3, layer="B.Cu")
path("3V3", [(57.75, 27.1), (60.0, 27.1), (61.3, 27.1), (61.8, 27.6), (61.8, 28.05), (61.8, 35.6), (58.8, 38.6)], 0.3, layer="B.Cu")
add_via("3V3", 61.8, 35.6); add_via("3V3", 58.8, 38.6)
move_fp("TP4", 62.4, 37.8); path("3V3", [(61.8, 35.6), (61.8, 36.4)], 0.3)                    # TP4 straight down from its via
# U5 bottom: A1 and A0 both to VS (address 0x45). Pins 1 and 2 join, then one run down to J3.2.
remove_in_box(["3V3"], (55.5, 34.0, 59.2, 41.7))
drop_via("3V3", (55.8, 35.7))
remove_in_box(["GND"], (56.6, 34.0, 57.8, 36.0)); drop_via("GND", (57.5, 35.7))
path("3V3", [(56.4, 34.3), (56.9, 34.3)], 0.25)
path("3V3", [(56.9, 34.3), (56.9, 36.1), (58.8, 38.0), (58.8, 38.6), (58.8, 41.65)], 0.3)
# U5 SDA: straight down to a via just outside the chip, fed on the bottom from the SDA bus. F.Cu on to J3.3.
remove_in_box(["SDA"], (55.0, 29.9, 58.2, 33.2), layer="B.Cu"); drop_via("SDA", (58.099, 33.052))
remove_in_box(["SDA"], (57.7, 32.9, 60.0, 41.7))
add_via("SDA", 57.9, 35.75)
path("SDA", [(57.9, 34.3), (57.9, 35.75), (57.9, 35.9), (59.8, 37.8), (59.8, 41.65)], 0.25)
path("SDA", [(55.069, 30.022), (57.9, 32.853), (57.9, 35.75)], 0.25, layer="B.Cu")
# SCL: the old route snaked between J6 and J9 along the edge. Now the main line runs straight to a via past the 3V3 rail,
# U5 and J3 hang off a bottom run down the right side, and U3 drops to the main line on the bottom.
remove_in_box(["SCL"], (51.0, 15.0, 67.0, 41.7))
path("SCL", [(52.5, 25.012), (57.1, 25.012), (61.9, 25.012)], 0.25); add_via("SCL", 57.1, 25.012); add_via("SCL", 61.9, 25.012)
path("SCL", [(61.9, 25.012), (66.0, 25.012), (66.5, 25.512), (66.5, 37.7), (65.6, 38.6), (60.8, 38.6)], 0.25, layer="B.Cu")
add_via("SCL", 60.8, 38.6)
path("SCL", [(58.4, 34.3), (58.4, 35.1), (60.8, 37.5), (60.8, 38.6), (60.8, 41.65)], 0.25)
path("SCL", [(56.6, 17.8), (56.6, 18.9), (57.1, 19.4)], 0.25); add_via("SCL", 57.1, 19.4)
path("SCL", [(57.1, 19.4), (57.1, 25.012)], 0.25, layer="B.Cu")
# U3 bottom pins: SDA (pin 4) straight down to its via, A0 (pin 2, 3V3) straight down to its via, A1 (pin 1, GND) down, 45, to its via
remove_in_box(["SDA"], (55.9, 17.5, 56.7, 19.2))
remove_in_box(["SDA"], (54.9, 18.5, 56.7, 22.6), layer="B.Cu")
move_via("SDA", (56.529, 19.038), (56.1, 19.4))
path("SDA", [(56.1, 17.8), (56.1, 19.4)], 0.25)
path("SDA", [(56.1, 19.4), (56.1, 21.0), (55.069, 22.031), (55.069, 22.546)], 0.25, layer="B.Cu")
remove_in_box(["3V3"], (42.0, 17.5, 56.0, 19.8)); drop_via("3V3", (55.7, 19.4))
path("3V3", [(42.432, 19.31), (52.0, 19.31)], 0.3); add_via("3V3", 52.0, 19.31)
path("3V3", [(52.0, 19.31), (52.66, 18.65), (55.1, 18.65), (60.0, 18.65)], 0.3, layer="B.Cu")      # just below U3's pins, above its vias
path("3V3", [(55.1, 17.8), (55.1, 19.45)], 0.3); add_via("3V3", 55.1, 19.45); path("3V3", [(55.1, 19.45), (55.1, 18.65)], 0.3, layer="B.Cu")
remove_in_box(["GND"], (53.4, 17.5, 54.8, 18.8)); move_via("GND", (53.6, 18.6), (53.8, 19.4))
path("GND", [(54.6, 17.8), (54.6, 18.6), (53.8, 19.4)], 0.25)

remove_in_box(["SDA"], (31.5, 25.4, 32.53, 26.8))                                            # leftover stub inside R5.2

# ======================================================================= USB-C CC2: out of R15.1 sideways (R14 sits right below it), down the outside
remove_in_box(["CC2"], (10.5, 34.0, 13.4, 42.2))
path("CC2", [(12.3, 34.213), (11.3, 34.213), (10.9, 34.613), (10.9, 40.078), (12.937, 42.115), (13.293, 42.115)], 0.25)
# USB data at J7: the A and B row pins are joined with 45 degree links clear of the next pin, and each line jogs
# once to enter the ESD chip pad on its centre line
remove_in_box(["USB_DP", "USB_DN"], (16.9, 37.2, 19.4, 41.0))
path("USB_DP", [(18.85, 39.65), (18.85, 38.6), (18.85, 38.3), (19.05, 38.1), (19.05, 37.238)], 0.25)
path("USB_DP", [(17.85, 39.65), (17.85, 38.9), (18.15, 38.6), (18.85, 38.6)], 0.25)
path("USB_DN", [(17.35, 39.65), (17.35, 38.3), (17.15, 38.1), (17.15, 37.238)], 0.25)
path("USB_DN", [(18.35, 39.65), (18.35, 40.6), (18.05, 40.9), (17.65, 40.9), (17.35, 40.6), (17.35, 39.65)], 0.25)

# ======================================================================= stitching vias that now crowd a hand route
def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy
    k = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(a[0] + k * dx - p[0], a[1] + k * dy - p[1])
gnd = net("GND"); used = {s["a"] for s in segs if s["net"] == gnd} | {s["b"] for s in segs if s["net"] == gnd}
dropped = 0
for v in list(vias):
    if v["net"] != gnd or v["locked"] or any(close(v["at"], u) for u in used): continue
    r = float(re.search(r"\(size (\S+)\)", v["rest"])[1]) / 2
    if any(s.get("new") and s["net"] != gnd and seg_dist(v["at"], s["a"], s["b"]) < s["w"] / 2 + r + 0.22 for s in segs):
        vias.remove(v); dropped += 1
log.append(f"stitching vias dropped: {dropped}")

# ======================================================================= write back and refill
def fmt(v): return f"{v:.6f}".rstrip("0").rstrip(".")
def srec(s):
    return (f'  (segment{" locked" if s["locked"] else ""} (start {fmt(s["a"][0] + OX)} {fmt(s["a"][1] + OY)}) (end {fmt(s["b"][0] + OX)} {fmt(s["b"][1] + OY)}) '
            f'(width {fmt(s["w"])}) (layer "{s["layer"]}") (net {s["net"]}) (tstamp {uuid.uuid4()}))\n')
def vrec(v):
    return f'  (via{" locked" if v["locked"] else ""} (at {fmt(v["at"][0] + OX)} {fmt(v["at"][1] + OY)}) {v["rest"]}(net {v["net"]}) (tstamp {uuid.uuid4()}))\n'
first = min(SEG_RE.search(txt).start(), VIA_RE.search(txt).start())
body = VIA_RE.sub("", SEG_RE.sub("", txt))
out = body[:first] + "".join(srec(s) for s in segs) + "".join(vrec(v) for v in vias) + body[first:]
open(OUT, "w").write(out)
b = pcbnew.LoadBoard(OUT)
if not b.FindFootprintByReference("Q1"):        # add the USB power switch (adding through pcbnew is safe, removing is not)
    import json, os
    from pcb_common import load_fp
    UU = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "uuids.json")))
    q = load_fp("Package_TO_SOT_SMD:SOT-23"); q.SetReference("Q1"); q.SetValue("AO3401A")
    q.SetPath(pcbnew.KIID_PATH("/" + UU["symbols"]["Q1"]))
    q.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(Q1[0] + OX), pcbnew.FromMM(Q1[1] + OY))); q.SetOrientationDegrees(180)
    q.SetProperty("MPN", "AO3401A"); q.SetProperty("Manufacturer", "Alpha & Omega Semiconductor")
    b.Add(q)
    for pd in q.Pads(): pd.SetNet(b.FindNet(NAME[net({"1": "5V", "2": "5V_LDO", "3": "USB_PWR"}[pd.GetNumber()])]))
for fp in b.GetFootprints():
    if fp.GetReference() in MOVES:
        x, y, rot = MOVES[fp.GetReference()]; fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x + OX), pcbnew.FromMM(y + OY)))
        if rot is not None: fp.SetOrientationDegrees(rot)
PAD_NETS = {("U5", "2"): "3V3"}          # U5 A0 to VS: address 0x45 (the design file says the same)
for (ref, num), n in PAD_NETS.items():
    pd = b.FindFootprintByReference(ref).FindPadByNumber(num); pd.SetNet(b.FindNet(NAME[net(n)]))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)
print("\n".join(log)); print("segments", len(segs), "vias", len(vias))
