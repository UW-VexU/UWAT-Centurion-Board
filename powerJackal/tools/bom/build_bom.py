"""Smart Port Power test board BOM: xlsx (with formulas) plus a DigiKey BOM Manager CSV."""
import csv, os, sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONT = "Helvetica"
INK, GOLD, LIGHT, LINE, STEEL = "111111", "E0A300", "F4F4F4", "D9D9D9", "5C5C5C"
DK = "https://www.digikey.ca/en/products/detail/"
CHECKED = "October 11, 2026"
FX, FX_DATE = 1.4271, "October 9, 2026"   # Bank of Canada USD to CAD daily rate
BOARDS_DEFAULT = 2

# ref, block, description, manufacturer, MPN, DigiKey PN (cut tape or single unit), qty/board, spares, unit USD, DigiKey stock, link path, notes
# Stock and USD prices: DigiKey listings via the TrustedParts DigiKey feed, checked on CHECKED. DigiKey Canada ships from the same stock.
P = [
    # power input
    ("J1", "Power input", "Smart port jack, 4P4C modular, right angle, through hole", "Molex", "0955012441", "WM5568-ND", 1, 0, 1.03, 4314,
     "molex/0955012441/1835860", "The board footprint is a placeholder until the Molex drawing is checked. Test-fit a real VEX smart cable first."),
    ("J2", "Power input", "Bench supply input, 2-position screw terminal, 5.08 mm", "Phoenix Contact", "1935161", "277-1667-ND", 1, 0, 0.53, 52131,
     "phoenix-contact/1935161/568614", "D3 and D5 OR the two inputs. Either can be plugged in alone or both at once."),
    ("D3, D5", "Power input", "Input OR diodes, Schottky 40 V 3 A, SMA", "Diodes Incorporated", "B340A-13-F", "B340A-FDICT-ND", 2, 1, 0.54, 354008,
     "diodes-incorporated/B340A-13-F/725015", "D5 from the smart port, D3 from the bench input."),
    ("F1", "Protection", "Polyfuse, 1.5 A hold, 3 A trip, 33 V, 2016 SMD", "Littelfuse", "2016L150/33DR", "18-2016L150/33DRCT-ND", 1, 1, 0.89, 825,
     "littelfuse-inc/2016L150-33DR/6347051", "Right after the OR diodes."),
    ("D1", "Protection", "TVS diode, 16 V standoff, about 26 V clamp, unidirectional, SMB", "Littelfuse", "SMBJ16A", "SMBJ16ALFCT-ND", 1, 1, 0.53, 55986,
     "littelfuse-inc/SMBJ16A/762784", "Keeps hot-plug spikes well below the TPSM53602's 38 V absolute maximum."),
    ("C1", "Protection", "Bulk input capacitor, aluminum electrolytic, 47 µF 50 V, radial", "Panasonic", "EEU-FC1H470", "P10321-ND", 1, 0, 0.49, 596,
     "panasonic-industry/EEU-FC1H470/266330", "Damps hot-plug ringing and covers the module's bulk input recommendation."),
    # 5 V regulator
    ("U1", "5 V regulator", "Step-down power module, 3.8 to 36 V in, 2 A, 1.4 MHz, B3QFN-14 5 x 5.5 mm", "Texas Instruments", "TPSM53602RDAR",
     "296-TPSM53602RDARCT-ND", 1, 0, 7.03, 2824, "texas-instruments/TPSM53602RDAR/11502301",
     "Pads under the body: hot plate or hot air with a stencil. 74 on cut tape, more on Digi-Reel."),
    ("C2, C3, C10", "5 V regulator", "Ceramic capacitor, 10 µF 50 V X7R, 1210", "Samsung Electro-Mechanics", "CL32B106KBJNNNE", "1276-3387-1-ND", 3, 2, 0.69, 331,
     "samsung-electro-mechanics/CL32B106KBJNNNE/3888579", "C2, C3 at the TPSM53602 input (datasheet asks for 2 x 10 µF). C10 at the LDO input."),
    ("C4, C5, C11, C12", "5 V regulator", "Ceramic capacitor, 47 µF 10 V X5R, 1206", "Murata", "GRM31CR61A476ME15L", "490-5528-1-ND", 4, 2, 0.41, 14947,
     "murata-electronics/GRM31CR61A476ME15L/2039020", "C4, C5 at the TPSM53602 output (needs 27 µF real at 5 V). C11 at the LDO output, C12 bulk at the ESP32 3V3 pin."),
    ("R4", "5 V regulator", "RFBB, sets 5.0 V out, 2.49 kΩ 1%, 0805", "Yageo", "RC0805FR-072K49L", "311-2.49KCRCT-ND", 1, 2, 0.11, 1194673,
     "yageo/RC0805FR-072K49L/730393", "With R3 (10 kΩ RFBT), from TPSM53602 datasheet Table 7-1."),
    # measurement
    ("U2, U3, U5", "Measurement", "Current and voltage monitor, I2C, 0 to 36 V bus, VSSOP-10", "Texas Instruments", "INA226AIDGSR", "296-29034-1-ND", 3, 0, 3.19, 73740,
     "texas-instruments/INA226AIDGSR/2687236", "U2 input (0x40), U3 5 V rail (0x41), U5 3.3 V rail (0x45)."),
    ("R1, R2", "Measurement", "Current shunt, 20 mΩ 1%, metal strip, 1206", "Vishay Dale", "WSL1206R0200FEA", "WSLC-.02CT-ND", 2, 1, 0.77, 149553,
     "vishay-dale/WSL1206R0200FEA/712488", "About 4 A full scale on the INA226. Sense traces leave from the inner pad edges."),
    ("R12", "Measurement", "Current shunt, 50 mΩ 1%, metal strip, 1206", "Vishay Dale", "WSL1206R0500FEA", "WSLC-.05CT-ND", 1, 1, 0.93, 17384,
     "https://www.digikey.ca/en/products/result?keywords=WSL1206R0500FEA", "3.3 V rail shunt. About 1.6 A full scale."),
    ("C6 to C8, C13 to C15", "Measurement", "Decoupling capacitor, 0.1 µF 50 V X7R, 0805", "Yageo", "CC0805KRX7R9BB104", "311-1140-1-ND", 6, 2, 0.14, 2238739,
     "yageo/CC0805KRX7R9BB104/302874", "C6, C7, C14 at each INA226. C8 at the TPSM53602 input. C13, C15 at the ESP32 3V3 pin."),
    ("C9", "MCU and USB", "Ceramic capacitor, 1 µF 50 V X7R, 0805", "TDK", "C2012X7R1H105K125AB", "445-7547-1-ND", 1, 2, 0.24, 6826,
     "tdk-corporation/C2012X7R1H105K125AB/3754298", "EN delay with R17 (10 kΩ + 1 µF, Espressif's recommended values)."),
    ("R5, R6", "Measurement", "I2C pull-ups, 4.7 kΩ 1%, 0805", "Yageo", "RC0805FR-074K7L", "311-4.70KCRCT-ND", 2, 2, 0.10, 414393,
     "yageo/RC0805FR-074K7L/727929", "To 3.3 V."),
    ("J3", "Measurement", "STEMMA QT / Qwiic connector, JST SH 4-pin, right angle SMD", "JST", "SM04B-SRSS-TB", "455-SM04B-SRSS-TBCT-ND", 1, 0, 0.51, 145702,
     "jst-sales-america-inc/SM04B-SRSS-TB/926710", "I2C out to the OLED."),
    ("DISP1", "Display (optional)", "OLED display, 1.3 in 128x64, I2C, STEMMA QT (off board)", "Adafruit", "938", "1528-1512-ND", 1, 0, 19.95, 2540,
     "adafruit-industries-llc/938/5774238", "Plugs into J3 with the cable below."),
    ("CBL1", "Display (optional)", "STEMMA QT / Qwiic cable, JST SH 4-pin, 100 mm", "Adafruit", "4210", "1528-4210-ND", 1, 0, 0.95, 19336,
     "adafruit-industries-llc/4210/10230021", ""),
    # 3.3 V stage
    ("U6", "3.3 V regulator", "LDO regulator, 3.3 V fixed, 1 A, SOT-223", "Diodes Incorporated", "AP7361C-33E-13", "AP7361C-33E-13DICT-ND", 1, 1, 0.52, 2375,
     "diodes-incorporated/AP7361C-33E-13/5638317", "Pin 1 IN, 2 GND (tab), 3 OUT."),
    ("D2, D4", "3.3 V regulator", "Feed diodes, Schottky 40 V 1 A, SMA", "Vishay", "SS14-E3/61T", "SS14-E3/61TGICT-ND", 2, 1, 0.47, 132279,
     "vishay-general-semiconductor-diodes-division/SS14-E3-61T/1091538", "D2: 5 V rail to the LDO. D4: USB VBUS to the LDO."),
    # MCU and USB
    ("U4", "MCU and USB", "ESP32-C3 module, RISC-V 160 MHz, 4 MB flash, built-in USB serial/JTAG, U.FL antenna connector, 13.2 x 12.5 mm",
     "Espressif Systems", "ESP32-C3-MINI-1U-N4X", "1965-ESP32-C3-MINI-1U-N4XCT-ND", 1, 0, 3.38, 4911,
     "https://www.digikey.ca/en/products/result?keywords=ESP32-C3-MINI-1U-N4X",
     "Recommended chip revision v1.1. Radio not used, so no antenna is fitted. Pads under the module: hot plate or hot air."),
    ("J7", "MCU and USB", "USB-C receptacle, USB 2.0, 16 pin, top mount, horizontal", "GCT", "USB4105-GF-A", "2073-USB4105-GF-ACT-ND", 1, 1, 0.80, 103585,
     "gct/USB4105-GF-A/11198441", "Flashing and serial over the ESP32-C3's built-in USB, plus backup power for the 3.3 V rail."),
    ("Q1", "MCU and USB", "USB power switch, P-channel MOSFET, -30 V -4 A, logic level, SOT-23", "Alpha & Omega Semiconductor", "AO3401A",
     "785-1001-1-ND", 1, 2, 0.52, 369446, "https://www.digikey.ca/en/products/result?keywords=AO3401A",
     "Gate on the 5 V rail: on only while the rail is off, so USB powers the board only with port and bench power off."),
    ("U7", "MCU and USB", "USB ESD protection, 2 lines plus VBUS, SOT-23-6", "STMicroelectronics", "USBLC6-2SC6", "497-5235-1-ND", 1, 1, 0.54, 133662,
     "https://www.digikey.ca/en/products/result?keywords=USBLC6-2SC6", "Right beside J7."),
    ("R14, R15", "MCU and USB", "USB-C CC resistors, 5.1 kΩ 1%, 0805", "Yageo", "RC0805FR-075K1L", "311-5.10KCRCT-ND", 2, 2, 0.10, 2450,
     "https://www.digikey.ca/en/products/result?keywords=RC0805FR-075K1L", "One per CC pin. Required for USB-C to USB-C cables."),
    ("R3, R7, R8, R17, R21, R22, R23", "MCU and USB", "Resistor, 10 kΩ 1%, 0805", "Yageo", "RC0805FR-0710KL", "311-10.0KCRCT-ND", 7, 2, 0.10, 1893501,
     "yageo/RC0805FR-0710KL/727535", "R3 regulator RFBT, R7 PGOOD pull-up, R8 input LED, R17 EN pull-up, R21, R22, R23 hold the GPIO2, GPIO8 and GPIO9 straps high."),
    ("R24, R25", "MCU and USB", "USB D+ and D- series resistors, 22 Ω 1%, 0805", "Yageo", "RC0805FR-0722RL", "311-22.0CRCT-ND", 2, 2, 0.10, 114416,
     "yageo/RC0805FR-0722RL/727658", "Between the USBLC6 and GPIO19/GPIO18, per Espressif's hardware checklist."),
    ("R20", "MCU and USB", "Resistor, 1 kΩ 1%, 0805", "Yageo", "RC0805FR-071KL", "311-1.00KCRCT-ND", 1, 2, 0.10, 884470,
     "yageo/RC0805FR-071KL/730391", "Status LED resistor."),
    ("SW1, SW2", "MCU and USB", "Tactile switch, SMD, low profile", "E-Switch", "TL3342F160QG", "EG2531CT-ND", 2, 1, 0.59, 75505,
     "https://www.digikey.ca/en/products/result?keywords=TL3342F160QG", "SW1 RESET (EN), SW2 BOOT (GPIO9). DigiKey lists the cut-tape part as TL3342F160QG/TR."),
    # indicators
    ("LED1 to LED3", "Indicators", "LED, green, 0805", "Lite-On", "LTST-C171GKT", "160-1423-1-ND", 3, 2, 0.15, 141398,
     "liteon/LTST-C171GKT/386793", "LED1 input power, LED2 5 V rail, LED3 firmware status (GPIO10)."),
    ("R9", "Indicators", "5 V LED resistor, 2.2 kΩ 1%, 0805", "Yageo", "RC0805FR-072K2L", "311-2.20KCRCT-ND", 1, 2, 0.10, 459877,
     "yageo/RC0805FR-072K2L/727676", "About 1.4 mA."),
    # outputs and plug-in loads
    ("J6, J9", "Outputs", "Pluggable output header, 2-position, 3.81 mm, right angle, 8 A", "Phoenix Contact", "1803277", "277-1206-ND", 2, 0, 0.73, 27252,
     "https://www.digikey.ca/en/products/result?keywords=1803277", "J6 is 5 V out, J9 is 3.3 V out. Pin 1 (marked +) is the rail, pin 2 is GND."),
    ("LOAD1 to LOAD4", "Plug-in loads (optional)", "Plug for J6 or J9, 2-position screw, 3.81 mm (off board)", "Phoenix Contact", "1803578", "277-1161-ND", 4, 1, 2.11, 20472,
     "https://www.digikey.ca/en/products/result?keywords=1803578", "One plug per load. LOAD4 stays empty for wires to an electronic load."),
    ("LOAD1, LOAD2", "Plug-in loads (optional)", "Load resistor, 10 Ω 5 W 5%, cement, axial (off board)", "Yageo", "SQP500JB-10R", "10W-5-ND", 3, 0, 0.71, 30811,
     "yageo/SQP500JB-10R/18655", "LOAD1 uses one (0.5 A at 5 V). LOAD2 uses two in parallel (1 A at 5 V). Hot in use."),
    ("LOAD3", "Plug-in loads (optional)", "Load resistor, 22 Ω 5 W 5%, cement, axial (off board)", "Yageo", "SQP500JB-22R", "22W-5-ND", 1, 0, 0.67, 813,
     "yageo/SQP500JB-22R/18663", "150 mA at 3.3 V on J9."),
]

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
    if "optional" in row[1]: continue
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

ws["A1"] = "Smart Port Power Test Board (Jackal), Bill of Materials, Rev A draft 6 (TPSM53602 + ESP32-C3, 72.4 x 47.0 mm)"
ws["A1"].font = f(size=16, bold=True, color=INK)
ws["A2"] = (f"UWAT VEXU. DigiKey stock and qty-1 USD prices checked {CHECKED}. DigiKey Canada ships from the same stock. "
            f"CAD = USD x the rate in C4 (Bank of Canada, {FX_DATE}); digikey.ca's own CAD prices can differ by a few cents.")
ws["A2"].font = f(size=10, italic=True, color=STEEL)
for row, label, val, fmt, tip in ((3, "Boards to build", BOARDS_DEFAULT, "0", "Edit the yellow cells. Order qty = qty per board x boards + spares."),
                                  (4, "USD to CAD", FX, "0.0000", f"Bank of Canada daily rate, {FX_DATE}.")):
    ws.cell(row, 1, label).font = f(bold=True)
    c = ws.cell(row, 3, val); c.font = f(bold=True, color="0000FF"); c.fill = PatternFill("solid", fgColor="FFFF00")
    c.alignment = Alignment(horizontal="center"); c.number_format = fmt
    ws.cell(row, 4, tip).font = f(italic=True, color=STEEL)
dv = DataValidation(type="whole", operator="between", formula1="1", formula2="50", showErrorMessage=True,
                    errorTitle="Boards", error="Enter a whole number from 1 to 50.")
ws.add_data_validation(dv); dv.add("C3")

HEAD = ["Ref", "Block", "Description", "Manufacturer", "Mfr part number", "DigiKey part number", "Qty per board", "Unit price (USD)",
        "Unit price (CAD)", "Cost for 1 board (CAD)", "Spares", "Order qty", "Order cost (CAD)", "DigiKey stock", "DigiKey Canada link", "Notes"]
HR = 6
CENTER = (7, 8, 9, 10, 11, 12, 13, 14)
for c, h in enumerate(HEAD, 1):
    cell = ws.cell(HR, c, h)
    cell.font = f(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=INK)
    cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="center" if c in CENTER else "left")
    cell.border = Border(bottom=Side(style="medium", color=GOLD))
ws.row_dimensions[HR].height = 30

r0 = HR + 1
for i, (ref, block, desc, mfr, mpn, dkpn, q, sp, price, stock, path, note) in enumerate(P):
    r = r0 + i
    vals = [ref, block, desc, mfr, mpn, dkpn or None, q, price, f"=H{r}*$C$4", f"=G{r}*I{r}", sp, f"=G{r}*$C$3+K{r}", f"=L{r}*I{r}",
            stock, "Open" if not path.startswith("http") else "Search", note or None]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v)
        cell.font = f(color="0000FF") if c in (7, 8, 11, 14) else f()
        cell.alignment = Alignment(vertical="center", wrap_text=c in (3, 16), horizontal="center" if c in (7, 11, 12, 14) else None)
        cell.border = Border(bottom=thin)
        if i % 2:
            cell.fill = PatternFill("solid", fgColor=LIGHT)
    ws.cell(r, 5).font = f(bold=True)
    for c in (8, 9, 10, 13): ws.cell(r, c).number_format = '$#,##0.00;($#,##0.00);"-"'
    ws.cell(r, 14).number_format = '#,##0'
    link = ws.cell(r, 15)
    link.hyperlink = path if path.startswith("http") else DK + path
    link.font = f(color="8F6A00", underline="single")
last = r0 + len(P) - 1

t = last + 2
rows = [("Parts cost for 1 board, everything soldered on the board (CAD)", f'=SUMIFS(J{r0}:J{last},B{r0}:B{last},"<>*optional*")', True),
        ("Optional extras for 1 board: OLED, cable, plug-in load kit (CAD)", f'=SUMIFS(J{r0}:J{last},B{r0}:B{last},"*optional*")', False),
        ("Total for 1 board with the extras (CAD)", f"=L{t}+L{t + 1}", True),
        ("Order cost at the board count in C3, with spares (CAD)", f"=SUM(M{r0}:M{last})", False),
        ("Parts cost for 1 board in USD, for reference", f'=SUMPRODUCT((ISERROR(SEARCH("optional",B{r0}:B{last})))*G{r0}:G{last}*H{r0}:H{last})', False),
        ("Lowest DigiKey stock on any line", f"=MIN(N{r0}:N{last})", False)]
for k, (label, formula, bold) in enumerate(rows):
    ws.cell(t + k, 3, label).font = f(bold=True)
    c = ws.cell(t + k, 12, formula); c.font = f(bold=bold, size=11 if bold else 10)
    c.number_format = '$#,##0.00' if ("CAD" in label or "USD" in label) else '#,##0'
    c.alignment = Alignment(horizontal="right"); c.border = Border(top=thin)
    if bold: c.fill = PatternFill("solid", fgColor="FFF3CC")
ws.cell(t + 7, 1, "Prices are DigiKey qty-1 on cut tape (or single unit). Upload the DigiKey sheet or CSV to BOM Manager on digikey.ca for an exact "
        "CAD cart. The PCB itself, the VEX smart cable, screws and shipping are not included. Blue cells are inputs, black cells are formulas.").font = f(italic=True, color=STEEL, size=9)

for col, w in zip("ABCDEFGHIJKLMNOP", [14, 14, 44, 17, 21, 24, 9, 10, 10, 11, 8, 8, 11, 11, 13, 52]):
    ws.column_dimensions[col].width = w
ws.freeze_panes = ws.cell(r0, 4)
ws.auto_filter.ref = f"A{HR}:P{last}"
ws.page_setup.orientation = "landscape"; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_title_rows = f"{HR}:{HR}"

# ---------------- DigiKey upload sheet (BOM Manager: Quantity, Manufacturer Part Number, Manufacturer, Customer Reference)
up = wb.create_sheet("DigiKey upload")
up.sheet_view.showGridLines = False
uh = ["Quantity", "Manufacturer Part Number", "Manufacturer", "Customer Reference"]
for c, h in enumerate(uh, 1):
    cell = up.cell(1, c, h); cell.font = f(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=INK)
for i in range(len(P)):
    r, s = i + 2, r0 + i
    for c, v in enumerate([f"=BOM!L{s}", f"=BOM!E{s}", f"=BOM!D{s}", f"=BOM!A{s}"], 1):
        up.cell(r, c, v).font = f(color="008000")
for col, w in zip("ABCD", [10, 24, 20, 16]):
    up.column_dimensions[col].width = w
note_r = len(P) + 3
up.cell(note_r, 1, "This sheet follows the BOM tab. Upload it in DigiKey BOM Manager on digikey.ca to see live stock for every line, "
        "or use the CSV sent with this file.").font = f(italic=True, color=STEEL, size=9)

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
    ("3.3 V stage", "U6 AP7361C LDO, fed from the 5 V rail through D2, or from USB through D4 and the Q1 switch. Q1 is on only while the 5 V rail is off, so USB never carries part of the load during port measurements. "
     "The ESP32-C3 draws about 20 to 30 mA with the radio off. Test: read U5, plug LOAD3 into J9 for a 150 mA step, check TP4."),
    ("ESP32-C3 module", "ESP32-C3-MINI-1U-N4X: 3V3 has 47 µF + 2 x 100 nF. EN has 10 kΩ to 3V3 and 1 µF to GND (Espressif's values). "
     "I2C on GPIO4 SDA and GPIO5 SCL, PGOOD on GPIO3, status LED on GPIO10. GPIO2 and GPIO8 are held high by R21 and R22, "
     "GPIO9 is the BOOT strap with R23 as its pull-up. GPIO0, 1, 6, 7, 20 and 21 are unused."),
    ("Programming", "USB-C goes to the module's built-in USB serial/JTAG (GPIO18/19). Flash and open a serial terminal over the same cable "
     "with Arduino, PlatformIO or ESP-IDF, no drivers or buttons needed. If the firmware breaks USB, hold BOOT and tap RESET to force the "
     "ROM download mode, which always works over USB."),
    ("USB-C", "USB 2.0 only. D+ and D- go through the USBLC6 ESD chip and 22 Ω series resistors (R24, R25) to the module. 5.1 kΩ on each CC pin. "
     "USB powers the board only when port and bench power are off (Q1)."),
    ("Plug-in loads", "Loads live off the board. Clamp a cement resistor's leads in a 1803578 plug and plug it into J6 (5 V) or J9 (3.3 V). "
     "LOAD1 10 Ω = 0.5 A at 5 V, LOAD2 two 10 Ω in parallel = 1 A at 5 V (J6 only), LOAD3 22 Ω = 150 mA at 3.3 V."),
    ("Bench input", "J2 feeds the shared input through D3. Set the supply between 10 and 15 V with a current limit. "
     "D3 and D5 keep the bench supply and the brain from feeding each other."),
    ("Hot-plug test", "Probe TP2 (VIN_MOD) against TP6 with a short ground spring while plugging into a live port. The spike should stay "
     "well under 36 V. Also check the port does not drop out from the inrush into C1 to C3."),
    ("Test points", "TP1 to TP6 and TP8 to TP10 are bare 3.4 x 1.8 mm copper pads (no paste), so there is nothing to buy. "
     "They use the same land as a Keystone 5015, so a loop can be soldered onto any of them later if a probe hook is needed."),
    ("Board", "72.4 x 47.0 mm, 2 layers, 1.6 mm, 1 oz copper. Four #8-32 holes on the VEX 0.5 in grid (63.5 x 38.1 mm), 4.45 mm from the edges. "
     "All parts on the top side. The KiCad project, Gerbers, drill and placement files are in the powerJackal folder of the UWAT-Centurion-Board repo."),
    ("Not in this list", "PCB, VEX smart cable, USB-C cable, #8-32 screws and standoffs, solder paste and stencil, an optional U.FL antenna. "
     "The test points are bare pads, so they are not parts."),
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

# CSV for DigiKey BOM Manager at the default board count
with open(os.path.join(OUT, "powerJackal_revA_DigiKey_upload.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(uh)
    for ref, block, desc, mfr, mpn, dkpn, q, sp, *_ in P:
        w.writerow([q * BOARDS_DEFAULT + sp, mpn, mfr, ref])
print("lines", len(P), "rows", r0, last)
