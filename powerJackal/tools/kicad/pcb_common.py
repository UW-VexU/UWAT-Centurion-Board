"""Shared PCB helpers: footprint loading, board geometry, net classes."""
import os, json
import pcbnew
import jackal_design as D

HERE = os.path.dirname(os.path.abspath(__file__))
FPLIB = os.environ.get("KICAD_FOOTPRINT_DIR", "/usr/share/kicad/footprints")   # KiCad standard footprints
UWAT_PRETTY = os.path.join(HERE, "..", "..", "lib", "UWAT.pretty")   # powerJackal/lib
OX, OY = 100.0, 100.0           # board origin in KiCad coordinates
W, H = 72.4, 47.0               # board size, mm: the 63.5 x 38.1 VEX hole pattern with 4.45 mm margins
HOLES = [(4.45, 4.45), (67.95, 4.45), (4.45, 42.55), (67.95, 42.55)]  # on the 0.5 in VEX grid: 63.5 x 38.1 spacing

mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
def toloc(v): return (pcbnew.ToMM(v.x) - OX, pcbnew.ToMM(v.y) - OY)

def lib_path(lib):
    return UWAT_PRETTY if lib == "UWAT" else os.path.join(FPLIB, lib + ".pretty")

def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(lib_path(lib), name)
    if fp is None: raise RuntimeError("footprint not found " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def net_name(n):
    return "GND" if n == "GND" else "/" + n

# net classes: name -> (track, clearance, via dia, via drill, nets)
POWER = ["VPORT", "BENCH_IN", "VIN_OR", "VFUSE", "VIN_MOD", "5V_MOD", "5V", "5V_LDO", "3V3_LDO"]
CLASSES = {
    "Default": (0.25, 0.2, 0.6, 0.3, []),
    "Power":   (0.8, 0.2, 0.8, 0.4, POWER),
    "Supply3V3": (0.3, 0.2, 0.6, 0.3, ["3V3"]),
    "USBPower": (0.4, 0.2, 0.6, 0.3, ["VBUS_USB", "USB_PWR"]),
    "Ground": (0.4, 0.2, 0.6, 0.3, ["GND"]),     # poured, not autorouted
}
