"""Smart Port Power test board BOM: xlsx (with formulas) plus a DigiKey BOM Manager CSV."""
import csv, os, sys
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONT = "Helvetica"
INK, GOLD, LIGHT, LINE, STEEL = "111111", "E0A300", "F4F4F4", "D9D9D9", "5C5C5C"
CHECKED = "October 29, 2026"
BOARDS_DEFAULT = 2
OFF = "Off board"   # block name for parts that are bought for the board but not soldered to it

# ref, block, description, manufacturer, MPN, DigiKey PN (cut tape or single unit), qty/board, spares, DigiKey stock, notes
# Stock read from digikey.ca product pages on CHECKED. Prices are in BREAKS below.
P = [
    # power input
    ("J1", "Power input", "Smart port jack, 4P4C modular, right angle, through hole", "Molex", "0955012441", "WM5568-ND", 1, 0, 4151,
     "The board footprint is a placeholder until the Molex drawing is checked. Test-fit a real VEX smart cable first."),
    ("J2", "Power input", "Bench supply input, 2-position screw terminal, 5.08 mm", "Phoenix Contact", "1935161", "277-1667-ND", 1, 0, 44913,
     "D3 and D5 OR the two inputs. Either can be plugged in alone or both at once."),
    ("D3, D5", "Power input", "Input OR diodes, Schottky 40 V 3 A, SMA", "Diodes Incorporated", "B340A-13-F", "B340A-FDICT-ND", 2, 1, 254159,
     "D5 from the smart port, D3 from the bench input."),
    ("F1", "Protection", "Polyfuse, 1.5 A hold, 3 A trip, 33 V, 2016 SMD", "Littelfuse", "2016L150/33DR", "18-2016L150/33DRCT-ND", 1, 1, 29235,
     "Right after the OR diodes."),
    ("D1", "Protection", "TVS diode, 16 V standoff, about 26 V clamp, unidirectional, SMB", "Littelfuse", "SMBJ16A", "SMBJ16ALFCT-ND", 1, 1, 25785,
     "Keeps hot-plug spikes well below the TPSM53602's 38 V absolute maximum."),
    ("C1", "Protection", "Bulk input capacitor, aluminum electrolytic, 47 µF 50 V, 6.3 mm radial, 2.5 mm pitch", "Panasonic", "EEU-FR1H470", "P124235-ND",
     1, 0, 26276,
     "Damps hot-plug ringing and covers the module's bulk input recommendation. Replaces EEU-FC1H470, which is out of stock. "
     "Same 6.3 mm can and 2.5 mm pitch, 12.7 mm tall."),
    # 5 V regulator
    ("U1", "5 V regulator", "Step-down power module, 3.8 to 36 V in, 2 A, 1.4 MHz, B3QFN-14 5 x 5.5 mm", "Texas Instruments", "TPSM53602RDAR",
     "296-TPSM53602RDARCT-ND", 1, 0, 2786, "Pads under the body: hot plate or hot air with a stencil."),
    ("C2, C3, C10", "5 V regulator", "Ceramic capacitor, 10 µF 50 V X7R, 1210", "Samsung Electro-Mechanics", "CL32B106KBJNNNE", "1276-3387-1-ND", 3, 2, 742989,
     "C2, C3 at the TPSM53602 input (datasheet asks for 2 x 10 µF). C10 at the LDO input."),
    ("C4, C5, C11, C12", "5 V regulator", "Ceramic capacitor, 47 µF 10 V X5R, 1206", "Murata", "GRM31CR61A476ME15L", "490-5528-1-ND", 4, 2, 180907,
     "C4, C5 at the TPSM53602 output (needs 27 µF real at 5 V). C11 at the LDO output, C12 bulk at the ESP32 3V3 pin."),
    ("R4", "5 V regulator", "RFBB, sets 5.0 V out, 2.49 kΩ 1%, 0805", "Yageo", "RC0805FR-072K49L", "311-2.49KCRCT-ND", 1, 2, 1178164,
     "With R3 (10 kΩ RFBT), from TPSM53602 datasheet Table 7-1."),
    # measurement
    ("U2, U3, U5", "Measurement", "Current and voltage monitor, I2C, 0 to 36 V bus, VSSOP-10", "Texas Instruments", "INA226AIDGSR", "296-29034-1-ND", 3, 0, 37941,
     "U2 input (0x40), U3 5 V rail (0x41), U5 3.3 V rail (0x45)."),
    ("R1, R2", "Measurement", "Current shunt, 20 mΩ 1%, metal strip, 1206", "Vishay Dale", "WSL1206R0200FEA", "WSLC-.02CT-ND", 2, 1, 147584,
     "About 4 A full scale on the INA226. Sense traces leave from the inner pad edges."),
    ("R12", "Measurement", "Current shunt, 50 mΩ 1%, metal strip, 1206", "Vishay Dale", "WSL1206R0500FEA", "WSLC-.05CT-ND", 1, 1, 17342,
     "3.3 V rail shunt. About 1.6 A full scale."),
    ("C6 to C8, C13 to C15", "Measurement", "Decoupling capacitor, 0.1 µF 50 V X7R, 0805", "Yageo", "CC0805KRX7R9BB104", "311-1140-1-ND", 6, 2, 4955773,
     "C6, C7, C14 at each INA226. C8 at the TPSM53602 input. C13, C15 at the ESP32 3V3 pin."),
    ("C9", "MCU and USB", "Ceramic capacitor, 1 µF 25 V X7R, 0805", "Yageo", "CC0805KKX7R8BB105", "311-1456-1-ND", 1, 2, 327549,
     "EN delay with R17 (10 kΩ + 1 µF, Espressif's recommended values). Replaces TDK C2012X7R1H105K125AB (50 V), which is out of stock. "
     "EN only sees 3.3 V."),
    ("R5, R6", "Measurement", "I2C pull-ups, 4.7 kΩ 1%, 0805", "Yageo", "RC0805FR-074K7L", "311-4.70KCRCT-ND", 2, 2, 601787,
     "To 3.3 V."),
    ("J3", "Measurement", "STEMMA QT / Qwiic connector, JST SH 4-pin, right angle SMD", "JST", "SM04B-SRSS-TB", "455-SM04B-SRSS-TBCT-ND", 1, 0, 111721,
     "Spare I2C port (3.3 V, GND, SDA, SCL) for a STEMMA QT display or sensor later."),
    # 3.3 V stage
    ("U6", "3.3 V regulator", "LDO regulator, 3.3 V fixed, 1 A, 250 mV dropout, SOT-223", "Microchip Technology", "MCP1826ST-3302E/DB",
     "MCP1826ST-3302E/DBCT-ND", 1, 1, 39535,
     "Pin 1 IN, 2 GND (tab), 3 OUT, the same as the AP7361C-33E it replaces. That part is out of stock with a 44 week lead time."),
    ("D2, D4", "3.3 V regulator", "Feed diodes, Schottky 40 V 1 A, SMA", "Vishay", "SS14-E3/61T", "SS14-E3/61TGICT-ND", 2, 1, 178712,
     "D2: 5 V rail to the LDO. D4: USB VBUS to the LDO."),
    # MCU and USB
    ("U4", "MCU and USB", "ESP32-C3 module, RISC-V 160 MHz, 4 MB flash, built-in USB serial/JTAG, U.FL antenna connector, 13.2 x 12.5 mm",
     "Espressif Systems", "ESP32-C3-MINI-1U-N4X", "1965-ESP32-C3-MINI-1U-N4XCT-ND", 1, 0, 4953,
     "Recommended chip revision v1.1. Radio not used, so no antenna is fitted. Pads under the module: hot plate or hot air."),
    ("J7", "MCU and USB", "USB-C receptacle, USB 2.0, 16 pin, top mount, horizontal", "GCT", "USB4105-GF-A", "2073-USB4105-GF-ACT-ND", 1, 1, 85017,
     "Flashing and serial over the ESP32-C3's built-in USB, plus backup power for the 3.3 V rail."),
    ("Q1", "MCU and USB", "USB power switch, P-channel MOSFET, -30 V -4 A, logic level, SOT-23", "Alpha & Omega Semiconductor", "AO3401A",
     "785-1001-1-ND", 1, 2, 319128,
     "Gate on the 5 V rail: on only while the rail is off, so USB powers the board only with port and bench power off."),
    ("U7", "MCU and USB", "USB ESD protection, 2 lines plus VBUS, SOT-23-6", "STMicroelectronics", "USBLC6-2SC6", "497-5235-1-ND", 1, 1, 63346,
     "Right beside J7."),
    ("R14, R15", "MCU and USB", "USB-C CC resistors, 5.1 kΩ 1%, 0805", "Stackpole Electronics", "RMCF0805FT5K10", "RMCF0805FT5K10CT-ND", 2, 2, 98354,
     "One per CC pin. Required for USB-C to USB-C cables. Replaces Yageo RC0805FR-075K1L, which is out of stock."),
    ("R3, R7, R8, R17, R21, R22, R23", "MCU and USB", "Resistor, 10 kΩ 1%, 0805", "Yageo", "RC0805FR-0710KL", "311-10.0KCRCT-ND", 7, 2, 1489428,
     "R3 regulator RFBT, R7 PGOOD pull-up, R8 input LED, R17 EN pull-up, R21, R22, R23 hold the GPIO2, GPIO8 and GPIO9 straps high."),
    ("R24, R25", "MCU and USB", "USB D+ and D- series resistors, 22 Ω 1%, 0805", "Yageo", "RC0805FR-0722RL", "311-22.0CRCT-ND", 2, 2, 70552,
     "Between the USBLC6 and GPIO19/GPIO18, per Espressif's hardware checklist."),
    ("R20", "MCU and USB", "Resistor, 1 kΩ 1%, 0805", "Yageo", "RC0805FR-071KL", "311-1.00KCRCT-ND", 1, 2, 554941,
     "Status LED resistor."),
    ("SW1, SW2", "MCU and USB", "Tactile switch, SMD, low profile", "E-Switch", "TL3342F160QG", "EG2531CT-ND", 2, 1, 72083,
     "SW1 RESET (EN), SW2 BOOT (GPIO9). DigiKey lists the cut-tape part as TL3342F160QG/TR."),
    # indicators
    ("LED1 to LED3", "Indicators", "LED, green, 0805", "Lite-On", "LTST-C171GKT", "160-1423-1-ND", 3, 2, 106301,
     "LED1 input power, LED2 5 V rail, LED3 firmware status (GPIO10)."),
    ("R9", "Indicators", "5 V LED resistor, 2.2 kΩ 1%, 0805", "Yageo", "RC0805FR-072K2L", "311-2.20KCRCT-ND", 1, 2, 374622,
     "About 1.4 mA."),
    # outputs
    ("J6, J9", "Outputs", "Pluggable output header, 2-position, 3.81 mm, right angle, 8 A", "Phoenix Contact", "1803277", "277-1206-ND", 2, 0, 25786,
     "J6 is 5 V out, J9 is 3.3 V out. Pin 1 (marked +) is the rail, pin 2 is GND."),
    ("J6 plug, J9 plug", OFF, "Mating plug for J6 and J9, 2-position screw, 3.81 mm", "Phoenix Contact", "1803578", "277-1161-ND", 2, 0, 26689,
     "Not soldered to the board. Screw the load wires into it."),
]

# digikey.ca CAD price breaks for the packaging sold from qty 1, read from each product page on CHECKED:
# MPN -> (packaging, [(min qty, unit price CAD), ...] in increasing qty). Full-reel tape and reel prices are left out.
YAGEO_0805_1PCT = [(1, 0.16), (10, 0.054), (25, 0.0404), (50, 0.033), (100, 0.0271), (250, 0.02128), (500, 0.01798), (1000, 0.0154)]
BREAKS = {
    "0955012441": ("Tray", [(1, 1.53), (10, 1.293), (25, 1.2124), (50, 1.1544), (100, 1.0992), (250, 1.0304), (500, 0.98114), (1000, 0.9343),
                            (2500, 0.87581)]),
    "1935161": ("Bulk", [(1, 0.79), (10, 0.64)]),
    "B340A-13-F": ("Cut Tape", [(1, 0.80), (10, 0.497), (25, 0.4124), (50, 0.359), (100, 0.3141)]),
    "2016L150/33DR": ("Cut Tape", [(1, 1.32), (5, 1.098), (10, 1.013), (50, 0.8406), (100, 0.7755), (250, 0.69716), (500, 0.64294)]),
    "SMBJ16A": ("Cut Tape", [(1, 0.79), (10, 0.487), (50, 0.3522), (100, 0.3084), (500, 0.23086)]),
    "EEU-FR1H470": ("Bulk", [(1, 0.70), (10, 0.432), (50, 0.3178), (200, 0.2515), (600, 0.21365), (1000, 0.19946), (2600, 0.17757), (5000, 0.16549)]),
    "TPSM53602RDAR": ("Cut Tape", [(1, 11.13), (5, 10.72), (10, 10.548), (25, 10.3232), (50, 10.1558), (100, 9.9907), (250, 9.7764), (500, 9.6171)]),
    "CL32B106KBJNNNE": ("Cut Tape", [(1, 1.02), (10, 0.636), (50, 0.483), (100, 0.436), (500, 0.35672)]),
    "GRM31CR61A476ME15L": ("Cut Tape", [(1, 0.61), (10, 0.362), (50, 0.2668), (100, 0.2372), (500, 0.18736)]),
    "RC0805FR-072K49L": ("Cut Tape", [(1, 0.17), (10, 0.057), (25, 0.0432), (50, 0.0348), (100, 0.0287), (250, 0.02256), (500, 0.01906), (1000, 0.01634)]),
    "INA226AIDGSR": ("Cut Tape", [(1, 5.05), (10, 3.777), (25, 3.4596), (100, 3.1086), (250, 2.94152), (500, 2.88846)]),
    "WSL1206R0200FEA": ("Cut Tape", [(1, 1.22), (10, 0.735), (25, 0.6252), (50, 0.5616), (100, 0.5115), (250, 0.46064), (500, 0.43118), (1000, 0.4078)]),
    "WSL1206R0500FEA": ("Cut Tape", [(1, 1.47), (10, 0.912), (25, 0.7852), (50, 0.7128), (100, 0.6549), (250, 0.59648), (500, 0.56262), (1000, 0.53565)]),
    "CC0805KRX7R9BB104": ("Cut Tape", [(1, 0.27), (10, 0.146), (50, 0.1018), (100, 0.0884), (500, 0.06584)]),
    "CC0805KKX7R8BB105": ("Cut Tape", [(1, 0.42), (10, 0.239), (50, 0.1704), (100, 0.1495), (500, 0.11464)]),
    "RC0805FR-074K7L": ("Cut Tape", YAGEO_0805_1PCT),
    "SM04B-SRSS-TB": ("Cut Tape", [(1, 0.76), (10, 0.643), (100, 0.5458), (500, 0.48704), (1000, 0.46377)]),
    "MCP1826ST-3302E/DB": ("Cut Tape", [(1, 1.44), (25, 1.2192), (100, 1.2111)]),
    "SS14-E3/61T": ("Cut Tape", [(1, 0.70), (10, 0.425), (50, 0.3068), (100, 0.2682), (500, 0.20024)]),
    "ESP32-C3-MINI-1U-N4X": ("Cut Tape", [(1, 5.35), (10, 4.624), (25, 4.3696), (100, 4.0197), (250, 3.81004)]),
    "USB4105-GF-A": ("Cut Tape", [(1, 1.19), (10, 1.004), (25, 0.9408), (50, 0.896), (100, 0.8532), (250, 0.79968)]),
    "AO3401A": ("Cut Tape", [(1, 0.82), (10, 0.51), (50, 0.3692), (100, 0.3234), (500, 0.24248)]),
    "USBLC6-2SC6": ("Cut Tape", [(1, 0.80), (10, 0.489), (50, 0.354), (100, 0.3101), (500, 0.2326)]),
    "RMCF0805FT5K10": ("Cut Tape", [(1, 0.16), (10, 0.043), (25, 0.0312), (50, 0.0246), (100, 0.0201), (250, 0.01564), (500, 0.01304), (1000, 0.01103)]),
    "RC0805FR-0710KL": ("Cut Tape", YAGEO_0805_1PCT),   # the 10k, 22R, 1k, 2.2k and 4.7k pages all show this same table
    "RC0805FR-0722RL": ("Cut Tape", YAGEO_0805_1PCT),
    "RC0805FR-071KL": ("Cut Tape", YAGEO_0805_1PCT),
    "RC0805FR-072K2L": ("Cut Tape", YAGEO_0805_1PCT),
    "TL3342F160QG": ("Cut Tape", [(1, 0.93), (10, 0.801), (25, 0.746), (100, 0.6665), (250, 0.61736), (500, 0.58282), (1000, 0.55087)]),
    "LTST-C171GKT": ("Cut Tape", [(1, 0.24), (10, 0.165), (100, 0.1132), (500, 0.0897), (1000, 0.08186)]),
    "1803277": ("Bulk", [(1, 1.08), (10, 0.881)]),
    "1803578": ("Bulk", [(1, 3.13), (10, 2.547)]),
}

# digikey.ca product page for every MPN, each opened and checked on CHECKED. The number at the end picks the page,
# so open a new link once to be sure it shows the right part.
DKCA = "https://www.digikey.ca/en/products/detail/"
LINK = {
    "0955012441": "molex/0955012441/1835860",
    "1935161": "phoenix-contact/1935161/568614",
    "B340A-13-F": "diodes-incorporated/B340A-13-F/725015",
    "2016L150/33DR": "littelfuse-inc/2016L150-33DR/6347051",
    "SMBJ16A": "littelfuse-inc/SMBJ16A/762784",
    "EEU-FR1H470": "panasonic-industry/EEU-FR1H470/9921029",
    "TPSM53602RDAR": "texas-instruments/TPSM53602RDAR/11502301",
    "CL32B106KBJNNNE": "samsung-electro-mechanics/CL32B106KBJNNNE/3889045",
    "GRM31CR61A476ME15L": "murata-electronics/GRM31CR61A476ME15L/2334879",
    "RC0805FR-072K49L": "yageo/RC0805FR-072K49L/727695",
    "INA226AIDGSR": "texas-instruments/INA226AIDGSR/2687236",
    "WSL1206R0200FEA": "vishay-dale/WSL1206R0200FEA/712488",
    "WSL1206R0500FEA": "vishay-dale/WSL1206R0500FEA/712495",
    "CC0805KRX7R9BB104": "yageo/CC0805KRX7R9BB104/302874",
    "CC0805KKX7R8BB105": "yageo/CC0805KKX7R8BB105/2833621",
    "RC0805FR-074K7L": "yageo/RC0805FR-074K7L/727929",
    "SM04B-SRSS-TB": "jst-sales-america-inc/SM04B-SRSS-TB/926710",
    "MCP1826ST-3302E/DB": "microchip-technology/MCP1826ST-3302E-DB/1635505",
    "SS14-E3/61T": "vishay-general-semiconductor-diodes-division/SS14-E3-61T/1091538",
    "ESP32-C3-MINI-1U-N4X": "espressif-systems/ESP32-C3-MINI-1U-N4X/27525543",
    "USB4105-GF-A": "gct/USB4105-GF-A/11198441",
    "AO3401A": "alpha-omega-semiconductor-inc/AO3401A/1855773",
    "USBLC6-2SC6": "stmicroelectronics/USBLC6-2SC6/1040559",
    "RMCF0805FT5K10": "stackpole-electronics-inc/RMCF0805FT5K10/1760394",
    "RC0805FR-0710KL": "yageo/RC0805FR-0710KL/727535",
    "RC0805FR-0722RL": "yageo/RC0805FR-0722RL/727735",
    "RC0805FR-071KL": "yageo/RC0805FR-071KL/730391",
    "TL3342F160QG": "e-switch/TL3342F160QG-TR/379004",
    "LTST-C171GKT": "liteon/LTST-C171GKT/386793",
    "RC0805FR-072K2L": "yageo/RC0805FR-072K2L/727676",
    "1803277": "phoenix-contact/1803277/260574",
    "1803578": "phoenix-contact/1803578/260529",
}
assert {row[4] for row in P} == set(LINK) == set(BREAKS), "every BOM line needs one digikey.ca link and one price table"
for mpn, (_, br) in BREAKS.items():
    assert br[0][0] == 1 and all(a[0] < b[0] and a[1] >= b[1] for a, b in zip(br, br[1:])), ("price breaks out of order", mpn)

def unit_at(mpn, qty):
    """digikey.ca unit price at an order quantity: the largest break at or below qty."""
    return [p for q, p in BREAKS[mpn][1] if q <= qty][-1]

# every on-board BOM line must match the KiCad design exactly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad"))
import re as _re
import jackal_design as _D
def _refs(s):
    out = []
    for part in [x.strip() for x in s.split(",")]:
        m = _re.match(r"([A-Z]+)(\d+) to [A-Z]+(\d+)$", part)
        if m: out += [f"{m.group(1)}{n}" for n in range(int(m.group(2)), int(m.group(3)) + 1)]
        else: out.append(part)
    return out
_design = {}
for p in _D.PARTS:
    if p["in_bom"]: _design.setdefault(p["mpn"], set()).add(p["ref"])
_bom = {}
for row in P:
    if row[1] == OFF: continue
    _bom.setdefault(row[4], set()).update(_refs(row[0]))
    assert len(_refs(row[0])) == row[6], ("qty mismatch", row[0])
if _bom != _design:
    for k in sorted(set(_bom) | set(_design)):
        if _bom.get(k) != _design.get(k): print("BOM/design mismatch", k, _bom.get(k), _design.get(k))
    raise SystemExit("BOM does not match jackal_design.py")
print("BOM matches the KiCad design:", sum(len(v) for v in _design.values()), "placed parts")

wb = Workbook()
ws = wb.active
ws.title = "BOM"
ws.sheet_view.showGridLines = False
f = lambda **k: Font(name=FONT, **{"size": 10, **k})
thin = Side(style="thin", color=LINE)
INPUT = PatternFill("solid", fgColor="FFFF00")

ws["A1"] = "Smart Port Power Test Board (Jackal), Bill of Materials, Rev A draft 8 (TPSM53602 + ESP32-C3, 72.4 x 47.0 mm)"
ws["A1"].font = f(size=16, bold=True, color=INK)
ws["A2"] = (f"UWAT VEXU. DigiKey Canada stock and CAD price breaks, read from digikey.ca on {CHECKED}. "
            "The unit price follows the order quantity, using the breaks on the Price breaks tab.")
ws["A2"].font = f(size=10, italic=True, color=STEEL)
ws.cell(3, 1, "Boards to build").font = f(bold=True)
c = ws.cell(3, 3, BOARDS_DEFAULT); c.font = f(bold=True, color="0000FF"); c.fill = INPUT
c.alignment = Alignment(horizontal="center"); c.number_format = "0"
ws.cell(3, 4, "Edit the yellow cells. Type your own quantity in the yellow Your order qty column to override the suggested one.").font = \
    f(italic=True, color=STEEL)
dv = DataValidation(type="whole", operator="between", formula1="1", formula2="50", showErrorMessage=True,
                    errorTitle="Boards", error="Enter a whole number from 1 to 50.")
ws.add_data_validation(dv); dv.add("C3")

# columns: A ref, B block, C description, D mfr, E MPN, F DigiKey PN, G qty/board, H spares, I needed, J your order qty, K order qty,
# L unit price at K, M order cost, N next break qty, O next break unit price, P tip, Q stock, R link, S notes
HEAD = ["Ref", "Block", "Description", "Manufacturer", "Mfr part number", "DigiKey part number", "Qty per board", "Spares",
        "Needed (boards x qty + spares)", "Your order qty (optional)", "Order qty", "Unit price at order qty (CAD)", "Order cost (CAD)",
        "Next price break (qty)", "Unit price at next break (CAD)", "Tip", "DigiKey stock", "DigiKey Canada link", "Notes"]
HR = 5
CENTER = (7, 8, 9, 10, 11, 12, 13, 14, 15, 17)
for col, h in enumerate(HEAD, 1):
    cell = ws.cell(HR, col, h)
    cell.font = f(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=INK)
    cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="center" if col in CENTER else "left")
    cell.border = Border(bottom=Side(style="medium", color=GOLD))
ws.row_dimensions[HR].height = 44

# price lookups against the Price breaks tab: the largest break at or below the order qty, and the next break above it
PB_ROWS = sum(len(br) for _, br in BREAKS.values()) + 200   # room to add rows on the Price breaks tab
PBA, PBB, PBC = (f"'Price breaks'!${c}$2:${c}${PB_ROWS}" for c in "ABC")
r0 = HR + 1
for i, (ref, block, desc, mfr, mpn, dkpn, q, sp, stock, note) in enumerate(P):
    r = r0 + i
    url = DKCA + LINK[mpn]
    nxt = f"MATCH(1,INDEX(({PBA}=$E{r})*({PBB}>$K{r}),0),0)"
    vals = [ref, block, desc, mfr, mpn, dkpn or None, q, sp,
            f"=G{r}*$C$3+H{r}",
            None,
            f'=IF(N(J{r})>0,J{r},I{r})',
            f"=IF(K{r}<=0,0,LOOKUP(2,1/(({PBA}=$E{r})*({PBB}<=K{r})),{PBC}))",
            f"=K{r}*L{r}",
            f'=IFERROR(INDEX({PBB},{nxt}),"")',
            f'=IFERROR(INDEX({PBC},{nxt}),"")',
            f'=IF(N{r}="","",IF(N{r}*O{r}<=M{r},"Buy "&N{r}&", saves $"&TEXT(M{r}-N{r}*O{r},"0.00"),""))',
            stock, url, note or None]
    for col, v in enumerate(vals, 1):
        cell = ws.cell(r, col, v)
        cell.font = f(color="0000FF") if col in (7, 8, 10, 17) else f()
        cell.alignment = Alignment(vertical="center", wrap_text=col in (3, 19), horizontal="center" if col in CENTER else None)
        cell.border = Border(bottom=thin)
        if i % 2:
            cell.fill = PatternFill("solid", fgColor=LIGHT)
    ws.cell(r, 5).font = f(bold=True)
    ws.cell(r, 10).fill = INPUT
    ws.cell(r, 11).font = f(bold=True)
    for col in (12, 15): ws.cell(r, col).number_format = '$#,##0.0000'
    ws.cell(r, 13).number_format = '$#,##0.00'
    ws.cell(r, 17).number_format = '#,##0'
    link = ws.cell(r, 18)
    link.hyperlink = url
    link.font = f(color="8F6A00", underline="single")
last = r0 + len(P) - 1
qv = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True, showErrorMessage=True,
                    errorTitle="Order qty", error="Enter a whole number, or clear the cell to use the suggested quantity.")
ws.add_data_validation(qv); qv.add(f"J{r0}:J{last}")
ws.conditional_formatting.add(f"P{r0}:P{last}", FormulaRule(formula=[f'LEN(P{r0})>0'], fill=PatternFill("solid", fgColor="D9F2D9"),
                                                            font=Font(name=FONT, bold=True, color="1E6B1E")))
ws.conditional_formatting.add(f"Q{r0}:Q{last}", FormulaRule(formula=[f'Q{r0}<K{r0}'], fill=PatternFill("solid", fgColor="F8D7D7"),
                                                            font=Font(name=FONT, bold=True, color="9B1C1C")))

t = last + 2
on = f'(B{r0}:B{last}<>"{OFF}")'
rows = [("Order total at the quantities above (CAD)", f"=SUM(M{r0}:M{last})", True),
        ("Parts cost for 1 board at the order unit prices, everything soldered on the board (CAD)",
         f"=SUMPRODUCT({on}*G{r0}:G{last}*L{r0}:L{last})", True),
        ("Mating plugs for J6 and J9, 1 board at the order unit prices (CAD)",
         f'=SUMPRODUCT((B{r0}:B{last}="{OFF}")*G{r0}:G{last}*L{r0}:L{last})', False),
        ("Lowest DigiKey stock on any line", f"=MIN(Q{r0}:Q{last})", False)]
for k, (label, formula, bold) in enumerate(rows):
    ws.cell(t + k, 3, label).font = f(bold=True)
    c = ws.cell(t + k, 13, formula); c.font = f(bold=bold, size=11 if bold else 10)
    c.number_format = '$#,##0.00' if "CAD" in label else '#,##0'
    c.alignment = Alignment(horizontal="right"); c.border = Border(top=thin)
    if bold: c.fill = PatternFill("solid", fgColor="FFF3CC")
ws.cell(t + 5, 1, "Unit prices are digikey.ca CAD on cut tape (or the packaging sold from qty 1), at the price break for the order qty. "
        "Tip: a green cell means buying up to the next break costs less in total. Stock turns red if it is below the order qty. "
        "The PCB itself, the VEX smart cable, screws and shipping are not included. Blue cells are inputs, black cells are formulas.").font = \
    f(italic=True, color=STEEL, size=9)

for col, w in zip("ABCDEFGHIJKLMNOPQRS", [14, 14, 44, 17, 21, 26, 8, 8, 11, 11, 9, 12, 11, 10, 12, 20, 11, 60, 52]):
    ws.column_dimensions[col].width = w
ws.freeze_panes = ws.cell(r0, 6)
ws.auto_filter.ref = f"A{HR}:S{last}"
ws.page_setup.orientation = "landscape"; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_title_rows = f"{HR}:{HR}"

# ---------------- price breaks: one row per break, each part's rows in increasing quantity
pb = wb.create_sheet("Price breaks")
pb.sheet_view.showGridLines = False
for col, h in enumerate(["Mfr part number", "Min qty", "Unit price (CAD)", "Packaging"], 1):
    cell = pb.cell(1, col, h); cell.font = f(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=INK)
r = 2
for row in P:
    pack, br = BREAKS[row[4]]
    for q, p in br:
        pb.cell(r, 1, row[4]).font = f(bold=True); pb.cell(r, 2, q).font = f(color="0000FF")
        c = pb.cell(r, 3, p); c.font = f(color="0000FF"); c.number_format = '$#,##0.00000'
        pb.cell(r, 4, pack).font = f()
        r += 1
pb.cell(r + 1, 1, f"From digikey.ca product pages on {CHECKED}. To update a price, edit the blue cells. Keep each part's rows together "
        "and in increasing quantity, because the BOM tab takes the last break at or below the order quantity.").font = \
    f(italic=True, color=STEEL, size=9)
for col, w in zip("ABCD", [24, 9, 15, 14]):
    pb.column_dimensions[col].width = w
pb.freeze_panes = "A2"

# ---------------- DigiKey upload sheet (BOM Manager matches on the DigiKey part number first, then the MPN)
up = wb.create_sheet("DigiKey upload")
up.sheet_view.showGridLines = False
uh = ["Quantity", "Manufacturer Part Number", "Manufacturer", "DigiKey Part Number", "Customer Reference"]
for col, h in enumerate(uh, 1):
    cell = up.cell(1, col, h); cell.font = f(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=INK)
for i in range(len(P)):
    r, s = i + 2, r0 + i
    for col, v in enumerate([f"=BOM!K{s}", f"=BOM!E{s}", f"=BOM!D{s}", f"=BOM!F{s}", f"=BOM!A{s}"], 1):
        up.cell(r, col, v).font = f(color="008000")
for col, w in zip("ABCDE", [10, 24, 24, 28, 22]):
    up.column_dimensions[col].width = w
note_r = len(P) + 3
up.cell(note_r, 1, "This sheet follows the Order qty column on the BOM tab. After changing quantities, save this sheet as CSV "
        "and upload it in DigiKey BOM Manager on digikey.ca. The CSV sent with this file uses the suggested quantities.").font = \
    f(italic=True, color=STEEL, size=9)

# ---------------- design notes
nt = wb.create_sheet("Design notes")
nt.sheet_view.showGridLines = False
nt.column_dimensions["A"].width = 24; nt.column_dimensions["B"].width = 100
notes = [
    ("Topic", "Note"),
    ("Smart port pinout", "Yellow = power (11 to 14.4 V battery), green = GND, red = RS-485 B, black = RS-485 A, per a VEX Forum tutorial. "
     "Confirm with a multimeter on a powered brain before ordering boards."),
    ("Smart port current", "VEX publishes no rating for the port power pin. VEX's James Pearman advises keeping an added load at 20 W or less "
     "(about 1.6 A at 12.8 V). This board pulls about 12 W at the full 2 A on the 5 V rail."),
    ("RS-485 lines", "A and B go to TP8 and TP9 only."),
    ("TPSM53602 settings", "5.0 V out: RFBT (R3) 10 kΩ, RFBB (R4) 2.49 kΩ, from datasheet Table 7-1. EN tied to VIN. 1.4 MHz fixed. "
     "Input 2 x 10 µF 50 V plus C1 bulk, output 2 x 47 µF (27 µF real minimum at 5 V). DNC pins 4 and 5 and V5V (13) stay open. "
     "NC pins 3, 10, 11 and AGND (12) join the exposed pad. VIN absolute maximum is 38 V."),
    ("TPSM53602 soldering", "B3QFN package with pads underneath and 11 vias in the exposed pad. Use a stencil and a hot plate or hot air. "
     "Ask the fab to tent or plug the exposed-pad vias if it offers that."),
    ("PGOOD", "Open drain from the TPSM53602, pulled up to 3.3 V by R7 and read on ESP32 GPIO3. Low means the 5 V output is not in "
     "regulation. TI only specifies PGOOD with VIN at 2 V or more, so on USB power alone it will most likely read high. Check U2 bus voltage first."),
    ("INA226 setup", "U2 after F1 measures port voltage and current (0x40). U3 on the 5 V rail (0x41). U5 on the 3.3 V rail (0x45, A1 and A0 both tied to VS). "
     "VS is 3.3 V. 20 mΩ shunts give about 4 A full scale, the 50 mΩ shunt about 1.6 A. Sense traces leave from the inner edges of each shunt pad."),
    ("3.3 V stage", "U6 MCP1826S LDO, fed from the 5 V rail through D2, or from USB through D4 and the Q1 switch. Q1 is on only while the 5 V rail is off, "
     "so USB never carries part of the load during port measurements. The ESP32-C3 draws about 20 to 30 mA with the radio off."),
    ("ESP32-C3 module", "ESP32-C3-MINI-1U-N4X: 3V3 has 47 µF + 2 x 100 nF. EN has 10 kΩ to 3V3 and 1 µF to GND (Espressif's values). "
     "I2C on GPIO4 SDA and GPIO5 SCL, PGOOD on GPIO3, status LED on GPIO10. GPIO2 and GPIO8 are held high by R21 and R22, "
     "GPIO9 is the BOOT strap with R23 as its pull-up. GPIO0, 1, 6, 7, 20 and 21 are unused."),
    ("Programming", "USB-C goes to the module's built-in USB serial/JTAG (GPIO18/19). Flash and open a serial terminal over the same cable "
     "with Arduino, PlatformIO or ESP-IDF, no drivers or buttons needed. If the firmware breaks USB, hold BOOT and tap RESET to force the "
     "ROM download mode, which always works over USB."),
    ("USB-C", "USB 2.0 only. D+ and D- go through the USBLC6 ESD chip and 22 Ω series resistors (R24, R25) to the module. 5.1 kΩ on each CC pin. "
     "USB powers the board only when port and bench power are off (Q1)."),
    ("Test loads", "Loads live off the board and are not in this list. Clamp a 5 W cement resistor's leads in a 1803578 plug and plug it into "
     "J6 (5 V) or J9 (3.3 V). 10 Ω = 0.5 A at 5 V, two 10 Ω in parallel = 1 A at 5 V (J6 only), 22 Ω = 150 mA at 3.3 V."),
    ("Bench input", "J2 feeds the shared input through D3. Set the supply between 10 and 15 V with a current limit. "
     "D3 and D5 keep the bench supply and the brain from feeding each other."),
    ("Hot-plug test", "Probe TP2 (VIN_MOD) against TP6 with a short ground spring while plugging into a live port. The spike should stay "
     "well under 36 V. Also check the port does not drop out from the inrush into C1 to C3."),
    ("Test points", "TP1 to TP6 and TP8 to TP10 are bare 3.4 x 1.8 mm copper pads (no paste), so there is nothing to buy. "
     "They use the same land as a Keystone 5015, so a loop can be soldered onto any of them later if a probe hook is needed."),
    ("Board", "72.4 x 47.0 mm, 2 layers, 1.6 mm, 1 oz copper. Four #8-32 holes on the VEX 0.5 in grid (63.5 x 38.1 mm), 4.45 mm from the edges. "
     "All parts on the top side. The KiCad project, Gerbers, drill and placement files are in the powerJackal folder of the UWAT-Centurion-Board repo."),
    ("Not in this list", "PCB, VEX smart cable, USB-C cable, #8-32 screws and standoffs, solder paste and stencil, an optional U.FL antenna, "
     "test load resistors, and any display or sensor for J3. The test points are bare pads, so they are not parts."),
]
for i, (a, b) in enumerate(notes, 1):
    ca, cb = nt.cell(i, 1, a), nt.cell(i, 2, b)
    if i == 1:
        for c in (ca, cb):
            c.font = f(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor=INK)
    else:
        ca.font = f(bold=True); cb.font = f()
        cb.alignment = Alignment(wrap_text=True, vertical="top"); ca.alignment = Alignment(vertical="top")
        for c in (ca, cb):
            c.border = Border(bottom=thin)

xlsx = os.path.join(OUT, "powerJackal_revA_BOM.xlsx")
wb.save(xlsx)

# CSV for DigiKey BOM Manager at the default board count and suggested quantities
with open(os.path.join(OUT, "powerJackal_revA_DigiKey_upload.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(uh)
    for ref, block, desc, mfr, mpn, dkpn, q, sp, *_ in P:
        w.writerow([q * BOARDS_DEFAULT + sp, mpn, mfr, dkpn, ref])

# summary, worked out the same way as the spreadsheet formulas
order = sum((q * BOARDS_DEFAULT + sp) * unit_at(mpn, q * BOARDS_DEFAULT + sp) for _, _, _, _, mpn, _, q, sp, *_ in P)
qty1 = sum(q * unit_at(mpn, 1) for _, blk, _, _, mpn, _, q, *_ in P if blk != OFF)
print(f"lines {len(P)}, order for {BOARDS_DEFAULT} boards with spares ${order:.2f} CAD, "
      f"parts for 1 board at qty-1 prices ${qty1:.2f} CAD, lowest stock {min(row[8] for row in P):,}")
