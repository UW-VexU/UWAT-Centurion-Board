"""Build uwat-stellaNova_revA_BOM.xlsx and the DigiKey upload CSV.

Same layout, formulas and styling as powerJackal_revA_BOM.xlsx (UWAT VEXU).
Prices and stock: digikey.ca, read 2026-10-30 (dk_prices_2026-10-30.json).
"""
import json, csv, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_XLSX = os.path.join(HERE, 'uwat-stellaNova_revA_BOM.xlsx')
OUT_CSV = os.path.join(HERE, 'uwat-stellaNova_revA_DigiKey_upload.csv')
P = json.load(open(os.path.join(HERE, 'dk_prices_2026-10-30.json')))
BOARDS = 5

# key, refs, block, description, manufacturer, mpn, dk pn, qty/board, spares, notes
ROWS = [
    ('PORT', 'J1', 'Smart port', 'Smart port jack, 4P4C modular, right angle, tab down, through hole',
     'Molex', '0432024101', 'WM5439-ND', 1, 0,
     'Pin 1 = RS-485 A, 2 = B, 3 = GND, 4 = battery. Beep a smart cable through it on the first board (README step 2).'),
    ('RS485', 'U3', 'Smart port', 'RS-485 transceiver, half duplex, 3.3 V, ±65 V fault protected, true fail-safe, 2 Mbps, SOIC-8',
     'Analog Devices', 'MAX33071EASA+', '505-MAX33071EASA+-ND', 1, 0,
     'Survives a miswired or damaged smart cable. Cheaper drop-in with the same pinout: ST3485EBDR (497-2080-1-ND, about $2.49), but its bus pins are only rated 14 V.'),
    ('R120', 'R4', 'Smart port', 'Bus termination, 120 Ω 1%, 0603 (not fitted)',
     'Yageo', 'RC0603FR-07120RL', '311-120HRCT-ND', 0, 0,
     'Not fitted. Only needed for smart cables longer than about 750 mm. Type a quantity in the yellow cell to buy some.'),
    ('PTC', 'F1', 'Power input', 'Polyfuse, 0.5 A hold, 30 V, 1812',
     'Bel Fuse', '0ZCG0050AF2C', '5923-0ZCG0050AF2CCT-ND', 1, 1,
     'First part after J1 pin 4. The board draws about 50 mA average, 220 mA peak, from the port.'),
    ('SCHOTTKY', 'D2, D3', 'Power input', 'Schottky diode, 60 V 2 A, SOD-123W',
     'Nexperia', 'PMEG6020ER,115', '1727-5217-1-ND', 2, 1,
     'D2 blocks reverse polarity from the port. D3 lets USB run the board, and D2 stops USB back-feeding the brain.'),
    ('TVS', 'D1', 'Power input', 'TVS diode, 18 V standoff, 29.2 V clamp, unidirectional, SMA',
     'Bourns', 'SMAJ18A', 'SMAJ18ABCT-ND', 1, 1,
     'Clears a full 14.6 V battery and clamps under the buck\'s 35 V limit.'),
    ('C10U50', 'C1', 'Power input', 'Ceramic capacitor, 10 µF 50 V X7R, 1210',
     'Samsung Electro-Mechanics', 'CL32B106KBJNNNE', '1276-3387-1-ND', 1, 1,
     'VIN bulk at the buck input.'),
    ('BUCK', 'U2', '3.3 V buck', 'Buck converter, 3.8 to 32 V in, 3 A, 500 kHz, adjustable, TSOT-26',
     'Diodes Incorporated', 'AP63301WU-7', '31-AP63301WU-7CT-ND', 1, 1,
     'Replaces the fixed AP63203, which is out of stock until mid 2027. Output set by R20 and R21.'),
    ('IND', 'L1', '3.3 V buck', 'Power inductor, 10 µH, 4.6 A saturation, 110 mΩ max, WE-MAPI 4030',
     'Würth Elektronik', '74438357100', '732-11206-1-ND', 1, 0,
     'Datasheet range is 2.2 to 10 µH. About 0.5 A ripple at 14.6 V in.'),
    ('C22U', 'C4, C5', '3.3 V buck', 'Ceramic capacitor, 22 µF 10 V X5R, 0805',
     'Murata', 'GRM21BR61A226ME51L', '490-10511-1-ND', 2, 2,
     'Buck output, per the AP63301 datasheet.'),
    ('R_FBT', 'R20', '3.3 V buck', 'Feedback divider top, 93.1 kΩ 1%, 0603',
     'Stackpole Electronics', 'RMCF0603FT93K1', 'RMCF0603FT93K1CT-ND', 1, 2,
     'With R21: 0.8 V x (1 + 93.1 / 30.1) = 3.27 V.'),
    ('R_FBB', 'R21', '3.3 V buck', 'Feedback divider bottom, 30.1 kΩ 1%, 0603',
     'Yageo', 'RC0603FR-0730K1L', '311-30.1KHRCT-ND', 1, 2,
     'With R20, sets 3.27 V out.'),
    ('C_FF', 'C13', '3.3 V buck', 'Feed-forward capacitor, 56 pF 50 V C0G, 0603',
     'KEMET', 'C0603C560J5GACTU', '399-C0603C560J5GACTUCT-ND', 1, 2,
     'Across R20, value from the AP63301 datasheet table.'),
    ('R100K', 'R1', '3.3 V buck', 'Buck enable resistor, 100 kΩ 1%, 0603',
     'Stackpole Electronics', 'RMCF0603FT100K', 'RMCF0603FT100KCT-ND', 1, 2,
     'EN to VIN. EN is rated to 35 V.'),
    ('R_UVLO', 'R2', '3.3 V buck', 'UVLO divider resistor, 37.4 kΩ 1%, 0603 (not fitted)',
     'Yageo', 'RC0603FR-0737K4L', '311-37.4KHRCT-ND', 0, 0,
     'Not fitted. If fitted, the buck may not start on USB power alone.'),
    ('C220U', 'C6', '3.3 V buck', 'Polymer tantalum capacitor, 220 µF 6.3 V, 45 mΩ, 3528 (not fitted)',
     'KEMET', 'T520B227M006ATE045', '399-5755-1-ND', 0, 0,
     'Not fitted. The buck datasheet covers 22 to 68 µF out. Fit only if a load-step test shows 3.3 V dips.'),
    ('ESP32', 'U1', 'MCU and USB', 'ESP32-S3 module, dual core 240 MHz, 16 MB flash, 2 MB quad PSRAM, WiFi and Bluetooth LE, PCB antenna',
     'Espressif Systems', 'ESP32-S3-WROOM-1-N16R2', '5407-ESP32-S3-WROOM-1-N16R2CT-ND', 1, 0,
     'Replaces N16R8, which is out of stock. Set PSRAM to Quad mode in firmware. Pads under the module: hot plate or hot air.'),
    ('C10U', 'C8, C11', 'MCU and USB', 'Ceramic capacitor, 10 µF 25 V X5R, 0805',
     'Murata', 'GRM21BR61E106KA73K', '490-16824-1-ND', 2, 2,
     'C8 at the ESP32 3V3 pin. C11 at the microSD socket.'),
    ('C1U', 'C10', 'MCU and USB', 'Ceramic capacitor, 1 µF 50 V X5R, 0603',
     'TDK', 'C1608X5R1H105K080AB', '445-7468-1-ND', 1, 2,
     'EN delay with R5 (10 kΩ + 1 µF, Espressif\'s recommended values).'),
    ('C100N', 'C2, C3, C7, C9, C12', 'Several blocks', 'Decoupling capacitor, 0.1 µF 50 V X7R, 0603',
     'Yageo', 'CC0603KRX7R9BB104', '311-1344-1-ND', 5, 2,
     'C2 buck input, C3 buck bootstrap, C7 at U3, C9 at the ESP32 3V3 pin, C12 at the microSD socket.'),
    ('R10K', 'R3, R5, R6, R9 to R14', 'Several blocks', 'Resistor, 10 kΩ 1%, 0603',
     'Yageo', 'RC0603FR-1310KL', '13-RC0603FR-1310KLCT-ND', 9, 2,
     'R3 holds RS-485 DE low (listen only at boot). R5 EN pull-up, R6 BOOT pull-up. R9 to R14 microSD pull-ups and card detect.'),
    ('USBC', 'J2', 'MCU and USB', 'USB-C receptacle, USB 2.0, 16 pin, top mount, horizontal',
     'GCT', 'USB4105-GF-A', '2073-USB4105-GF-ACT-ND', 1, 1,
     'Flashing, JTAG and serial over the ESP32-S3\'s built-in USB, plus bench power.'),
    ('ESD_USB', 'D5', 'MCU and USB', 'USB ESD protection, 2 lines plus VBUS, SOT-23-6',
     'STMicroelectronics', 'USBLC6-2SC6', '497-5235-1-ND', 1, 1,
     'Right beside J2.'),
    ('R5K1', 'R7, R8, R22', 'MCU and USB', 'USB-C CC pull-downs and VBUS bleed, 5.1 kΩ 1%, 0603',
     'Yageo', 'RC0603FR-075K1L', '311-5.10KHRCT-ND', 3, 2,
     'R7, R8 one per CC pin. R22 drains D3 leakage so VBUS reads 0 V on port power and a laptop will attach.'),
    ('R22', 'R18, R19', 'MCU and USB', 'USB D+ and D- series resistors, 22 Ω 1%, 0603',
     'Stackpole Electronics', 'RMCF0603FT22R0', 'RMCF0603FT22R0CT-ND', 2, 2,
     'Close to U1, per Espressif\'s hardware checklist.'),
    ('SW', 'SW1, SW2', 'MCU and USB', 'Tactile switch, SMD, 4.2 x 3.2 mm, low profile',
     'C&K', 'PTS810 SJM 250 SMTR LFS', 'CKN10502CT-ND', 2, 1,
     'SW1 RESET (EN), SW2 BOOT (IO0). Beep one on the first board: it should short only while pressed.'),
    ('SD', 'J3', 'microSD', 'microSD socket, push-push, top mount, card detect switch',
     'Hirose Electric', 'DM3AT-SF-PEJM5', 'HR1964CT-ND', 1, 0,
     'Card inserts from the right board edge. Card detect on IO1, low = card in.'),
    ('LED_G', 'D6', 'Indicators', 'LED, green, 0603',
     'Lite-On', 'LTST-C191KGKT', '160-1446-1-ND', 1, 2,
     'PWR, on whenever 3.3 V is up.'),
    ('LED_O', 'D7', 'Indicators', 'LED, orange, 0603',
     'Lite-On', 'LTST-C191KFKT', '160-1445-1-ND', 1, 2,
     'LINK, IO13, high = on.'),
    ('LED_R', 'D8', 'Indicators', 'LED, red, 0603',
     'Lite-On', 'LTST-C191KRKT', '160-1447-1-ND', 1, 2,
     'ACT, IO14, high = on.'),
    ('R1K', 'R15, R16, R17', 'Indicators', 'LED resistors, 1 kΩ 1%, 0603',
     'Yageo', 'RC0603FR-071KL', '311-1.00KHRCT-ND', 3, 2,
     'About 1 to 1.3 mA per LED.'),
]

# Suggested order quantity: among the needed quantity and every price break above it, the largest one whose
# total is within ROUND_UP dollars of the cheapest total. Cheap parts round up to a break for free spares.
ROUND_UP = 0.50

def unit_at(tiers, q):
    u = tiers[0][1]
    for b, p in tiers:
        if b <= q:
            u = p
    return u

def suggested(tiers, need):
    if need <= 0:
        return 0
    cands = [need] + [b for b, p in tiers if b > need]
    cost = {q: q * unit_at(tiers, q) for q in cands}
    best = min(cost.values())
    return max(q for q in cands if cost[q] <= best + ROUND_UP + 1e-9)

# ---------------------------------------------------------------- styles
H = 'Helvetica'
F = lambda **k: Font(name=H, size=k.pop('size', 10), **k)
DARK, GREY = 'FF111111', 'FF5C5C5C'
BLUE, GREEN, LINK = 'FF0000FF', 'FF008000', 'FF8F6A00'
HDR_FILL = PatternFill('solid', fgColor=DARK)
YELLOW = PatternFill('solid', fgColor='FFFFFF00')
TOTAL_FILL = PatternFill('solid', fgColor='FFFFF3CC')
THIN = Border(bottom=Side(style='thin', color='FFD0D0D0'))
HDR_BORDER = Border(bottom=Side(style='medium', color=DARK))
TOP = Border(top=Side(style='thin', color=DARK))
MONEY4, MONEY2, MONEY5 = '\\$#,##0.0000', '\\$#,##0.00', '\\$#,##0.00000'

wb = Workbook()
ws = wb.active
ws.title = 'BOM'
ws.sheet_view.showGridLines = False

ws['A1'] = 'uwat-stellaNova, Bill of Materials, Rev A (ESP32-S3 + MAX33071E, 48 x 40 mm, 4 layers)'
ws['A1'].font = F(size=16, bold=True, color=DARK)
ws.row_dimensions[1].height = 20.25
ws['A2'] = ('UWAT VEXU. DigiKey Canada stock and CAD price breaks, read from digikey.ca on October 30, 2026. '
            'The unit price follows the order quantity, using the breaks on the Price breaks tab.')
ws['A2'].font = F(italic=True, color=GREY)
ws['A3'] = 'Boards to build'; ws['A3'].font = F(bold=True)
ws['C3'] = BOARDS
ws['C3'].font = F(bold=True, color=BLUE); ws['C3'].fill = YELLOW
ws['C3'].alignment = Alignment(horizontal='center'); ws['C3'].number_format = '0'
ws['D3'] = 'Edit the yellow cells. Type your own quantity in the yellow Your order qty column to override the suggested one.'
ws['D3'].font = F(italic=True, color=GREY)

HEAD = ['Ref', 'Block', 'Description', 'Manufacturer', 'Mfr part number', 'DigiKey part number', 'Qty per board', 'Spares',
        'Needed (boards x qty + spares)', 'Your order qty (optional)', 'Order qty', 'Unit price at order qty (CAD)',
        'Order cost (CAD)', 'Next price break (qty)', 'Unit price at next break (CAD)', 'Tip', 'DigiKey stock',
        'DigiKey Canada link', 'Notes']
HR = 5
for c, h in enumerate(HEAD, 1):
    cell = ws.cell(HR, c, h)
    cell.font = F(bold=True, color='FFFFFFFF'); cell.fill = HDR_FILL; cell.border = HDR_BORDER
    cell.alignment = Alignment(horizontal='left' if c in (1, 2, 3, 4, 5, 6, 16, 18, 19) else 'center', vertical='center', wrap_text=True)
ws.row_dimensions[HR].height = 44.1

PB = "'Price breaks'"
r0 = HR + 1
PB_LAST = 2 + sum(len(P[k]['tiers']) for k, *_ in ROWS) + 20      # breaks plus room for more
A, Bq, C = f"{PB}!$A$2:$A${PB_LAST}", f"{PB}!$B$2:$B${PB_LAST}", f"{PB}!$C$2:$C${PB_LAST}"
fitted_rows = []
for i, (key, refs, block, desc, mfr, mpn, dk, qty, spares, notes) in enumerate(ROWS):
    r = r0 + i
    d = P[key]
    need = qty * BOARDS + spares
    sugg = suggested(d['tiers'], need)
    vals = {
        1: refs, 2: block, 3: desc, 4: mfr, 5: mpn, 6: dk, 7: qty, 8: spares,
        9: f'=G{r}*$C$3+H{r}',
        10: sugg if sugg else None,
        11: f'=IF(N(J{r})>0,J{r},I{r})',
        12: f'=IF(K{r}<=0,0,LOOKUP(2,1/(({A}=$E{r})*({Bq}<=K{r})),{C}))',
        13: f'=K{r}*L{r}',
        14: f'=IFERROR(INDEX({Bq},MATCH(1,INDEX(({A}=$E{r})*({Bq}>$K{r}),0),0)),"")',
        15: f'=IFERROR(INDEX({C},MATCH(1,INDEX(({A}=$E{r})*({Bq}>$K{r}),0),0)),"")',
        16: f'=IF(N{r}="","",IF(N{r}*O{r}<=M{r},"Buy "&N{r}&", saves $"&TEXT(M{r}-N{r}*O{r},"0.00"),""))',
        17: d['stock'], 18: d['url'], 19: notes,
    }
    for c, v in vals.items():
        cell = ws.cell(r, c, v)
        cell.font = F(); cell.border = THIN
        cell.alignment = Alignment(vertical='center', horizontal='center' if 7 <= c <= 15 or c == 17 else None,
                                   wrap_text=True if c in (3, 19) else None)
    for c in (7, 8, 17):
        ws.cell(r, c).font = F(color=BLUE)
    ws.cell(r, 5).font = F(bold=True)
    ws.cell(r, 10).font = F(color=BLUE); ws.cell(r, 10).fill = YELLOW
    ws.cell(r, 11).font = F(bold=True)
    for c in (12, 15):
        ws.cell(r, c).number_format = MONEY4
    ws.cell(r, 13).number_format = MONEY2
    ws.cell(r, 17).number_format = '#,##0'
    ws.cell(r, 18).font = F(color=LINK)
    ws.cell(r, 18).hyperlink = d['url']
    long_text = max(len(desc) / 44, len(notes) / 52)
    ws.row_dimensions[r].height = 25.5 if long_text <= 2 else (38.25 if long_text <= 3 else 51.0)
    if qty > 0:
        fitted_rows.append(r)
last = r0 + len(ROWS) - 1

# totals
t = last + 2
labels = [
    ('Order total at the quantities above (CAD)', f'=SUM(M{r0}:M{last})', MONEY2, True),
    ('Parts cost for 1 board at the order unit prices, all fitted parts (CAD)', f'=SUMPRODUCT(G{r0}:G{last}*L{r0}:L{last})', MONEY2, True),
    ('Adding the not-fitted options C6, R2 and R4 to 1 board, at 1-piece prices (CAD)', None, MONEY2, True),
    ('Lowest DigiKey stock on any line', f'=MIN(Q{r0}:Q{last})', '#,##0', False),
]
dnp_rows = [r0 + i for i, row in enumerate(ROWS) if row[7] == 0]
labels[2] = (labels[2][0], '=' + '+'.join(f'INDEX({C},MATCH($E{r},{A},0))' for r in dnp_rows), MONEY2, True)
for j, (lab, f, nf, big) in enumerate(labels):
    rr = t + j
    ws.cell(rr, 3, lab).font = F(bold=True)
    c = ws.cell(rr, 13, f)
    c.number_format = nf; c.alignment = Alignment(horizontal='right'); c.border = TOP
    c.font = F(size=11 if big else 10, bold=big)
    if big:
        c.fill = TOTAL_FILL
foot = t + len(labels) + 1
ws.cell(foot, 1, 'Unit prices are digikey.ca CAD on cut tape (or the packaging sold from qty 1: tray for J1, tube for U3), '
                 'at the price break for the order qty. The yellow order quantities are suggestions: the needed qty, rounded up '
                 'to a price break when that costs at most $0.50 more in total (free spares on cheap parts). Tip: a green cell means buying up to the next break costs less '
                 'in total. Stock turns red if it is below the order qty. Not-fitted parts (C6, R2, R4) have 0 per board. '
                 'The PCB, the VEX smart cable, a microSD card and shipping are not included. Blue cells are inputs, black '
                 'cells are formulas.').font = F(size=9, italic=True, color=GREY)

widths = {'A': 16, 'B': 15, 'C': 44, 'D': 19, 'E': 23, 'F': 30, 'G': 8, 'H': 8, 'I': 11, 'J': 10, 'K': 9, 'L': 12,
          'M': 11, 'N': 10, 'O': 12, 'P': 20, 'Q': 11, 'R': 60, 'S': 56}
for k, v in widths.items():
    ws.column_dimensions[k].width = v
ws.freeze_panes = f'F{r0}'
ws.auto_filter.ref = f'A{HR}:S{last}'
ws.conditional_formatting.add(f'P{r0}:P{last}', FormulaRule(formula=[f'LEN(P{r0})>0'],
    fill=PatternFill('solid', fgColor='FFD9F2D9', bgColor='FFD9F2D9'), font=Font(name=H, color='FF1E6B1E')))
ws.conditional_formatting.add(f'Q{r0}:Q{last}', FormulaRule(formula=[f'Q{r0}<K{r0}'],
    fill=PatternFill('solid', fgColor='FFF8D7D7', bgColor='FFF8D7D7'), font=Font(name=H, color='FF9B1C1C')))
dv1 = DataValidation(type='whole', operator='greaterThanOrEqual', formula1='1', allow_blank=False,
                     error='Boards to build must be a whole number of 1 or more.')
dv2 = DataValidation(type='whole', operator='greaterThanOrEqual', formula1='0', allow_blank=True,
                     error='Order quantity must be a whole number of 0 or more. Leave it blank to use the needed quantity.')
ws.add_data_validation(dv1); ws.add_data_validation(dv2)
dv1.add('C3'); dv2.add(f'J{r0}:J{last}')
ws.page_setup.orientation = 'landscape'
ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
ws.print_title_rows = f'{HR}:{HR}'

# ---------------------------------------------------------------- Price breaks
pb = wb.create_sheet('Price breaks')
pb.sheet_view.showGridLines = False
for c, h in enumerate(['Mfr part number', 'Min qty', 'Unit price (CAD)', 'Packaging'], 1):
    cell = pb.cell(1, c, h); cell.font = F(bold=True, color='FFFFFFFF'); cell.fill = HDR_FILL
rr = 2
for key, refs, block, desc, mfr, mpn, *_ in ROWS:
    for b, p in P[key]['tiers']:
        pb.cell(rr, 1, mpn).font = F(bold=True)
        pb.cell(rr, 2, b).font = F(color=BLUE)
        c = pb.cell(rr, 3, p); c.font = F(color=BLUE); c.number_format = MONEY5
        pb.cell(rr, 4, P[key]['pack']).font = F()
        rr += 1
pb.cell(rr + 1, 1, 'Source: digikey.ca product pages, CAD, read October 30, 2026. One block per part, smallest break first. '
                   'Add rows for new breaks inside the block of the same part.').font = F(size=9, italic=True, color=GREY)
assert rr - 1 <= PB_LAST
for k, v in {'A': 26, 'B': 9, 'C': 15, 'D': 16}.items():
    pb.column_dimensions[k].width = v
pb.freeze_panes = 'A2'

# ---------------------------------------------------------------- DigiKey upload
up = wb.create_sheet('DigiKey upload')
up.sheet_view.showGridLines = False
for c, h in enumerate(['Quantity', 'Manufacturer Part Number', 'Manufacturer', 'DigiKey Part Number', 'Customer Reference'], 1):
    cell = up.cell(1, c, h); cell.font = F(bold=True, color='FFFFFFFF'); cell.fill = HDR_FILL
for j, r in enumerate(fitted_rows, 2):
    for c, col in enumerate(['K', 'E', 'D', 'F', 'A'], 1):
        up.cell(j, c, f'=BOM!{col}{r}').font = F(color=GREEN)
note_r = len(fitted_rows) + 3
up.cell(note_r, 1, 'This sheet follows the Order qty column on the BOM tab and lists the fitted parts only (C6, R2 and R4 are '
                   'left out). After changing quantities, save this sheet as CSV and upload it in DigiKey BOM Manager on '
                   'digikey.ca. The CSV sent with this file uses the suggested quantities.').font = F(size=9, italic=True, color=GREY)
for k, v in {'A': 10, 'B': 26, 'C': 26, 'D': 34, 'E': 26}.items():
    up.column_dimensions[k].width = v

# ---------------------------------------------------------------- Design notes
dn = wb.create_sheet('Design notes')
dn.sheet_view.showGridLines = False
NOTES = [
    ('Smart port pinout', 'Contact order A, B, GND, + (J1 pin 1 = RS-485 A, 2 = B, 3 = GND, 4 = battery), from the labelled smart cable '
     'photo on the VEX Forum (black A, red B, green GND, yellow +). VEX smart cables are straight-through. J1 is tab down, '
     'like the Evercom jack on the DevilBots VEXBridge board. Beep a cable through J1 on the first board before plugging into a brain.'),
    ('Smart port current', 'The board draws about 50 mA average and 220 mA peak from the port at 10 V (WiFi bursts). F1 holds 0.5 A.'),
    ('RS-485', 'U3 MAX33071E, half duplex. RE tied low, so the receiver is always on. DE on IO10 with R3 pulling it low, so the board '
     'boots listen-only. RX IO9, TX IO11, use the ESP32 UART in RS485 half-duplex mode with RTS = IO10. Brain side: '
     'vexGenericSerialEnable(port, 0) then vexGenericSerialBaudrate(port, 230400), or pros::Serial. R4 termination is not fitted.'),
    ('Power path', 'Port battery through F1, then D2 (reverse block) to VIN. D1 clamps spikes. USB VBUS joins VIN through D3. '
     'R22 keeps VBUS at 0 V on port power so a laptop still attaches over USB.'),
    ('3.3 V buck', 'AP63301WU-7, 500 kHz forced PWM. Vout = 0.8 V x (1 + 93.1k / 30.1k) = 3.27 V. 56 pF feed-forward (C13), '
     '10 µH (L1), 2 x 22 µF out (C4, C5). C6 220 µF and the R2 UVLO resistor are not fitted. Worst-case 3.3 V load about 0.57 A.'),
    ('ESP32-S3 module', 'ESP32-S3-WROOM-1-N16R2: set PSRAM to Quad (QSPI) mode, not Octal. EN has 10 kΩ (R5) and 1 µF (C10). '
     'BOOT (IO0) has 10 kΩ (R6). Strapping pins IO3, IO45, IO46 are left floating on purpose. The antenna overhangs the top '
     'edge by 6 mm: keep metal 15 mm away from it.'),
    ('Programming', 'USB-C goes to the module\'s built-in USB serial/JTAG (IO19 D-, IO20 D+). Flash and open a serial terminal over '
     'the same cable with Arduino, PlatformIO or ESP-IDF. If firmware breaks USB, hold BOOT (SW2) and tap RESET (SW1) to force '
     'the ROM download mode.'),
    ('USB-C', 'USB 2.0 only. 5.1 kΩ on each CC pin (R7, R8). D+ and D- go through the USBLC6 (D5) and 22 Ω series resistors '
     '(R18, R19). USB alone gives the 500 mA default, enough for the board.'),
    ('microSD', '4-bit SD bus: CLK IO40, CMD IO41, D0 IO39, D1 IO38, D2 IO2, D3 IO42. 10 kΩ pull-ups on CMD and D0 to D3, card '
     'detect on IO1 (low = card in). C11 and C12 decouple the socket.'),
    ('Indicators', 'D6 PWR (green) is on whenever 3.3 V is up. D7 LINK (orange) on IO13, D8 ACT (red) on IO14, high = on. '
     '1 kΩ resistors give about 1 mA.'),
    ('Test points', 'TP1 VIN, TP2 3.3 V, TP3 GND, TP4 TX0, TP5 RX0 are bare pads on the back, so there is nothing to buy.'),
    ('Soldering', 'The ESP32 module has castellated edge pads plus a ground pad underneath. The USB-C jack has 0.5 mm pins. Use a '
     'stencil with a hot plate or hot air, or order assembly. J1 is through hole, soldered on the back. Other nets stay 0.5 mm '
     'from its pins so a solder bridge cannot reach USB or a GPIO.'),
    ('Board', '48 x 40 mm, 4 layers (signal, GND, 3.3 V, signal), 1.6 mm. No mounting holes, it hangs from its smart cable. '
     'All parts on the top side. KiCad project, Gerbers, drill and placement files are in uwat-stellaNova-revA.zip.'),
    ('Not in this list', 'PCB, VEX smart cable, USB-C cable, microSD card, solder paste and stencil. The test points are bare pads, '
     'so they are not parts.'),
]
for c, h in enumerate(['Topic', 'Note'], 1):
    cell = dn.cell(1, c, h); cell.font = F(bold=True, color='FFFFFFFF'); cell.fill = HDR_FILL
for j, (topic, note) in enumerate(NOTES, 2):
    a = dn.cell(j, 1, topic); a.font = F(bold=True); a.alignment = Alignment(vertical='top')
    b = dn.cell(j, 2, note); b.font = F(); b.alignment = Alignment(vertical='top', wrap_text=True)
    dn.row_dimensions[j].height = 12.75 * max(2, -(-len(note) // 110))
dn.column_dimensions['A'].width = 24; dn.column_dimensions['B'].width = 100

wb.save(OUT_XLSX)

# ---------------------------------------------------------------- CSV (suggested quantities)
with open(OUT_CSV, 'w', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['Quantity', 'Manufacturer Part Number', 'Manufacturer', 'DigiKey Part Number', 'Customer Reference'])
    for key, refs, block, desc, mfr, mpn, dk, qty, spares, notes in ROWS:
        if qty == 0:
            continue
        need = qty * BOARDS + spares
        w.writerow([suggested(P[key]['tiers'], need), mpn, mfr.replace('ü', 'u'), dk, refs])
print('wrote', OUT_XLSX, OUT_CSV, 'rows', len(ROWS), 'fitted', len(fitted_rows), 'price rows', rr - 2)
