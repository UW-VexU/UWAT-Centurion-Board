"""Build imuBoard_revA_BOM.xlsx and imuBoard_revA_DigiKey_upload.csv, in the centurion / powerJackal / stellaNova format.

Run with a Python that has openpyxl:  python build_bom.py <outdir>
DigiKey Canada prices and stock were read from digikey.ca on November 4, 2026 (parts shared with centurion: from
centurion's BOM, read the same day). The part list must match the schematic: check.py-style cross-check at the bottom.
"""
import sys, os, csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
BOARDS = 4   # two robots plus two spares
DK = "https://www.digikey.ca/en/products/detail/"
# ref, block, description, manufacturer, mpn, digikey pn, qty per board, spares, your order qty, stock, link, notes
P = [
    ("U1", "IMU", "6-axis IMU (accelerometer and gyroscope), LGA-14 2.5 x 3.0 mm", "Bosch Sensortec", "BMI270", "828-1091-1-ND",
     1, 1, None, 32589, DK + "bosch-sensortec/BMI270/9974486",
     "Reflow or hot air: the pads are under the part. Firmware uploads Bosch's config file at every power-up."),
    ("U2", "Cable jack", "ESD protection, 4 channel, USON-10 (automotive grade)", "Texas Instruments", "TPD4E05U06QDQARQ1",
     "296-40696-1-ND", 1, 1, None, 132598, DK + "texas-instruments/TPD4E05U06QDQARQ1/4972148",
     "Same part as centurion U5, U8 to U12, U17. Flow-through: the traces run over pins 6, 7, 9 and 10."),
    ("J1", "Cable jack", "JST GH 8-pin, vertical (top entry) SMD", "JST", "BM08B-GHS-TBT", "455-BM08B-GHS-TBTCT-ND",
     1, 0, None, 35607, DK + "jst-sales-america-inc/BM08B-GHS-TBT/807806",
     "Same jack as centurion J5; the cable is straight through (pin n to pin n). Cable parts are on centurion's Cables and tools tab."),
    ("R1", "IMU", "Resistor, 100 Ω 1%, 0805", "Yageo", "RC0805FR-07100RL", "311-100CRCT-ND", 1, 2, None, 926187,
     DK + "yageo/RC0805FR-07100RL/727543", "MISO series resistor, same part as centurion R8, R9, R41, R55."),
    ("C1, C2", "IMU", "Ceramic capacitor, 100 nF 50 V X7R, 0805", "Yageo", "CC0805KRX7R9BB104", "311-1140-1-ND", 2, 2, None,
     4955773, DK + "yageo/CC0805KRX7R9BB104/302874", "C1 at VDD (pin 8), C2 at VDDIO (pin 5)."),
    ("C3", "Cable jack", "Ceramic capacitor, 1 µF 25 V X7R, 0805", "Yageo", "CC0805KKX7R8BB105", "311-1456-1-ND", 1, 2, None,
     327549, DK + "yageo/CC0805KKX7R8BB105/2833621", "Bulk at the board input."),
]
BREAKS = {
    "BMI270": [(1, 6.70), (5, 5.996), (10, 5.737), (25, 5.4268)],
    "TPD4E05U06QDQARQ1": [(1, 2.06), (10, 1.301), (50, 0.9676), (100, 0.8594), (500, 0.66956)],
    "BM08B-GHS-TBT": [(1, 0.74), (10, 0.636), (100, 0.5404), (500, 0.48228), (1000, 0.45925)],
    "RC0805FR-07100RL": [(1, 0.16), (10, 0.06), (25, 0.0448), (50, 0.0368), (100, 0.0304), (250, 0.024), (500, 0.0204), (1000, 0.01754)],
    "CC0805KRX7R9BB104": [(1, 0.27), (10, 0.146), (50, 0.1018), (100, 0.0884), (500, 0.06584)],
    "CC0805KKX7R8BB105": [(1, 0.42), (10, 0.239), (50, 0.1704), (100, 0.1495), (500, 0.11464)],
}

def unit_price(mpn, q):
    p = BREAKS[mpn][0][1]
    for b, v in BREAKS[mpn]:
        if q >= b: p = v
    return p

# suggested order qty: what is needed, rounded up to a price break when that costs at most $0.50 more in total
for i, row in enumerate(P):
    need = row[6] * BOARDS + row[7]
    best = need
    for b, v in BREAKS[row[4]]:
        if b > need and b * v - need * unit_price(row[4], need) <= 0.50:
            best = b; break
    P[i] = row[:8] + (best,) + row[9:]

wb = Workbook()
ws = wb.active; ws.title = "BOM"
HDR = Font(bold=True, color="FFFFFF"); HFILL = PatternFill("solid", fgColor="111111")
YEL = PatternFill("solid", fgColor="FFFF00"); BLUE = Font(color="0000FF")
ws["A1"] = "Centurion IMU board, Bill of Materials, Rev A (BMI270 on SPI, plugs into centurion J5, 38 x 24 mm, 2 layers)"
ws["A1"].font = Font(bold=True, size=16, color="111111")
ws["A2"] = "UWAT VEXU. DigiKey Canada stock and CAD price breaks, read from digikey.ca on November 4, 2026 (parts shared with centurion: from centurion's BOM, read the same day). The unit price follows the order quantity, using the breaks on the Price breaks tab."
ws["A2"].font = Font(size=10, color="5C5C5C")
ws["A3"] = "Boards to build"; ws["A3"].font = Font(bold=True)
ws["C3"] = BOARDS; ws["C3"].fill = YEL; ws["C3"].font = Font(bold=True, color="0000FF")
ws["D3"] = "Edit the yellow cells. Type your own quantity in the yellow Your order qty column to override the suggested one."
cols = ["Ref", "Block", "Description", "Manufacturer", "Mfr part number", "DigiKey part number", "Qty per board", "Spares",
        "Needed (boards x qty + spares)", "Your order qty (optional)", "Order qty", "Unit price at order qty (CAD)", "Order cost (CAD)",
        "Next price break (qty)", "Unit price at next break (CAD)", "Tip", "DigiKey stock", "DigiKey Canada link", "Notes"]
for c, h in enumerate(cols, 1):
    cell = ws.cell(5, c, h); cell.font = HDR; cell.fill = HFILL; cell.alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[5].height = 42
first = 6
last = first + len(P) - 1
NPB = sum(len(v) for v in BREAKS.values()) + 1
for i, (ref, blk, desc, mfr, mpn, dk, qty, spares, order, stock, link, notes) in enumerate(P):
    r = first + i
    vals = [ref, blk, desc, mfr, mpn, dk, qty, spares]
    for c, v in enumerate(vals, 1): ws.cell(r, c, v)
    ws.cell(r, 7).font = BLUE; ws.cell(r, 8).font = BLUE
    ws.cell(r, 9, "=G%d*$C$3+H%d" % (r, r))
    ws.cell(r, 10, order if order != qty * BOARDS + spares else None).fill = YEL
    ws.cell(r, 10).font = BLUE
    ws.cell(r, 11, "=IF(N(J%d)>0,J%d,I%d)" % (r, r, r))
    ws.cell(r, 12, "=IFERROR(IF(MAX(K{r},I{r})<=0,0,LOOKUP(2,1/(('Price breaks'!$A$2:$A${n}=$E{r})*('Price breaks'!$B$2:$B${n}<=MAX(1,IF(K{r}>0,K{r},I{r})))),'Price breaks'!$C$2:$C${n})),0)".format(r=r, n=NPB))
    ws.cell(r, 13, "=K%d*L%d" % (r, r))
    ws.cell(r, 14, "=IF($K{r}<=0,\"\",IFERROR(INDEX('Price breaks'!$B$2:$B${n},MATCH(1,INDEX(('Price breaks'!$A$2:$A${n}=$E{r})*('Price breaks'!$B$2:$B${n}>$K{r}),0),0)),\"\"))".format(r=r, n=NPB))
    ws.cell(r, 15, "=IF($K{r}<=0,\"\",IFERROR(INDEX('Price breaks'!$C$2:$C${n},MATCH(1,INDEX(('Price breaks'!$A$2:$A${n}=$E{r})*('Price breaks'!$B$2:$B${n}>$K{r}),0),0)),\"\"))".format(r=r, n=NPB))
    ws.cell(r, 16, "=IF(OR(N{r}=\"\",K{r}<=0),\"\",IF(N{r}*O{r}<=M{r},\"Buy \"&N{r}&\", saves $\"&TEXT(M{r}-N{r}*O{r},\"0.00\"),\"\"))".format(r=r))
    ws.cell(r, 17, stock); ws.cell(r, 17).number_format = "#,##0"
    ws.cell(r, 18, link); ws.cell(r, 19, notes)
    ws.cell(r, 12).number_format = "$#,##0.0000"; ws.cell(r, 13).number_format = "$#,##0.00"; ws.cell(r, 15).number_format = "$#,##0.0000"
    for c in (1, 2, 3, 19): ws.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")
tr = last + 2
lines = [("Order total (CAD), at the order unit prices", "=SUM(M%d:M%d)" % (first, last), "$#,##0.00"),
         ("Parts cost for 1 board at the order unit prices", "=SUMPRODUCT(G%d:G%d,L%d:L%d)" % (first, last, first, last), "$#,##0.00"),
         ("Lines to order", "=COUNTIF(K%d:K%d,\">0\")" % (first, last), "0"),
         ("Lines where DigiKey stock is below the order qty", "=SUMPRODUCT((Q%d:Q%d<K%d:K%d)*(K%d:K%d>0))" % (first, last, first, last, first, last), "0")]
for i, (t, f, nf) in enumerate(lines):
    ws.cell(tr + i, 3, t).font = Font(bold=True)
    c = ws.cell(tr + i, 13, f); c.font = Font(bold=True); c.number_format = nf
ws.cell(tr + 5, 1, "Unit prices are digikey.ca CAD on cut tape, at the price break for the order qty. The yellow order quantities are suggestions: what is needed, rounded up to a price break when that costs at most $0.50 more in total. Tip: a filled tip means buying up to the next break costs less in total. Stock turns red if it is below the order qty. H1 and H2 are screw holes, not parts. The PCB itself, the cable (centurion's Cables and tools tab), screws and shipping are not included. U2, R1, C1 to C3 and J1 are centurion parts too: when both boards are ordered together, combine those lines. Blue cells are inputs, black cells are formulas.")
ws.cell(tr + 5, 1).alignment = Alignment(wrap_text=True, vertical="top")
ws.merge_cells(start_row=tr + 5, start_column=1, end_row=tr + 5, end_column=13)
ws.row_dimensions[tr + 5].height = 60
ws.conditional_formatting.add("P%d:P%d" % (first, last), FormulaRule(formula=["LEN(P%d)>0" % first], fill=PatternFill("solid", fgColor="C6EFCE")))
ws.conditional_formatting.add("Q%d:Q%d" % (first, last), FormulaRule(formula=["Q%d<K%d" % (first, first)], font=Font(color="C00000", bold=True)))
dv = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="1"); ws.add_data_validation(dv); dv.add("C3")
dv2 = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True); ws.add_data_validation(dv2); dv2.add("J%d:J%d" % (first, last))
for col, w in zip("ABCDEFGHIJKLMNOPQRS", (12, 12, 44, 18, 22, 26, 8, 8, 11, 10, 9, 12, 11, 10, 12, 20, 11, 60, 70)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = "A6"
ws.auto_filter.ref = "A5:S%d" % last

pb = wb.create_sheet("Price breaks")
for c, h in enumerate(("Mfr part number", "Min qty", "Unit price (CAD)", "Packaging"), 1):
    cell = pb.cell(1, c, h); cell.font = HDR; cell.fill = HFILL
r = 2
for mpn, br in BREAKS.items():
    for q, v in br:
        pb.cell(r, 1, mpn); pb.cell(r, 2, q).font = BLUE; pb.cell(r, 3, v).font = BLUE; pb.cell(r, 4, "Cut Tape"); pb.cell(r, 3).number_format = "$#,##0.0000"; r += 1
pb.cell(r + 1, 1, "Source: digikey.ca product pages, CAD, November 4, 2026. One block per part, smallest break first. To update a price, edit the blue cells; add rows for new breaks inside the block of the same part, because the BOM tab takes the last break at or below the order quantity.")
pb.column_dimensions["A"].width = 24; pb.column_dimensions["B"].width = 9; pb.column_dimensions["C"].width = 16; pb.column_dimensions["D"].width = 12
pb.freeze_panes = "A2"

up = wb.create_sheet("DigiKey upload")
for c, h in enumerate(("Quantity", "Manufacturer Part Number", "Manufacturer", "DigiKey Part Number", "Customer Reference"), 1):
    up.cell(1, c, h).font = Font(bold=True)
for i in range(len(P)):
    br = first + i
    for c, col in enumerate(("K", "E", "D", "F", "A"), 1):
        up.cell(2 + i, c, "=BOM!%s%d" % (col, br))
up.cell(len(P) + 3, 1, "This sheet follows the Order qty column on the BOM tab. After changing quantities, save this sheet as CSV and upload it in DigiKey BOM Manager on digikey.ca. The CSV sent with this file uses the suggested quantities.")
for col, w in zip("ABCDE", (10, 26, 18, 26, 16)): up.column_dimensions[col].width = w

dn = wb.create_sheet("Design notes")
for c, h in enumerate(("Topic", "Note"), 1):
    cell = dn.cell(1, c, h); cell.font = HDR; cell.fill = HFILL
notes = [
    ("Board", "38 x 24 mm, 2 layers, 1.6 mm, GND pour on both sides. Two #8-32 holes (4.5 mm), 25.4 mm (1 in) apart on the long axis, not tied to GND, with a 5 mm copper keepout for the screw heads. Order a standard 2-layer board, ENIG or lead-free HASL."),
    ("IMU", "U1 BMI270 on 4-wire SPI, 10 MHz max. ASDx, ASCx, OCSB and OSDO unconnected (BMI270 datasheet pin table). Firmware must do a dummy read to select SPI, then upload Bosch's 8 kB config file at every power-up."),
    ("Axes", "Printed on the top silkscreen: +X toward J1, +Y toward H2, +Z up out of the board (BMI270 datasheet section 8.2, with U1 turned 180 degrees)."),
    ("Cable", "J1 matches centurion J5 pin for pin, so the cable is straight through: 1 3V3, 2 GND, 3 SCK, 4 MOSI, 5 MISO, 6 CS, 7 INT1, 8 INT2. Keep it 30 cm or less (centurion/sim/README.md); the JST pre-crimped 305 mm leads fit exactly."),
    ("Signal integrity", "Centurion has 100 Ω in series with SCK, MOSI and CS (R8, R9, R41). R1 (100 Ω) does the same for MISO at the IMU: in centurion's spi_imu.cir it cuts the MISO overshoot at the MCU from 4.7 V to 3.6 V and lets a 0.5 m cable pass at any GPIO speed."),
    ("ESD", "U2 TPD4E05U06-Q1 clamps SCK, MOSI, MISO and CS at the jack. INT1 and INT2 are outputs of the IMU and are not clamped."),
    ("Not in this list", "PCB, the J5 cable (see centurion's BOM, Cables and tools tab), #8-32 screws and nuts, solder paste and stencil."),
]
for i, (a, b) in enumerate(notes, 2):
    dn.cell(i, 1, a).font = Font(bold=True); dn.cell(i, 2, b).alignment = Alignment(wrap_text=True, vertical="top")
dn.column_dimensions["A"].width = 18; dn.column_dimensions["B"].width = 120

os.makedirs(OUT, exist_ok=True)
wb.save(os.path.join(OUT, "imuBoard_revA_BOM.xlsx"))
with open(os.path.join(OUT, "imuBoard_revA_DigiKey_upload.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["Quantity", "Manufacturer Part Number", "Manufacturer", "DigiKey Part Number", "Customer Reference"])
    for row in P:
        w.writerow([row[8], row[4], row[3], row[5], row[0]])
tot = sum(row[8] * unit_price(row[4], row[8]) for row in P)
print("BOM written; %d lines, order total about $%.2f" % (len(P), tot))
for row in P: print("  %-8s %-20s need %d order %d @ %.4f" % (row[0], row[4], row[6] * BOARDS + row[7], row[8], unit_price(row[4], row[8])))
