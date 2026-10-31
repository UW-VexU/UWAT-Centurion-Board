"""uwat-stellaNova: schematic definition.

Run with /usr/bin/python3 design.py <outdir>
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sch import Schematic
from parts import PART, fields_for
import custom

PROJECT = 'uwat-stellaNova'
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'

s = Schematic(PROJECT, 'uwat-stellaNova')
s.title_block = {'date': '2026-10-29', 'rev': 'A',
                 'comments': ['stellaNova: ESP32-S3 WiFi/BLE debugger for the VEX V5 smart port',
                              'Single smart port, RS-485 half duplex, powered from the V5 battery',
                              'Generated design. Verify the smart port pinout with a meter before first plug-in.']}
custom.register(s)

GND, P3V3, VBUS, VIN, FLAG = 'power:GND', 'power:+3V3', 'power:VBUS', 'stellaNova:VIN', 'power:PWR_FLAG'


def part(lib_id, ref, at, rot=0, mirror=None, **kw):
    p = PART[ref]
    return s.add(lib_id, ref, p['value'], at, rot=rot, mirror=mirror, footprint=p['footprint'],
                 dnp=p.get('dnp', False), fields=fields_for(ref), **kw)


def vpass(lib_id, ref, x, ytop, top=None, bot=None, toplen=0, botlen=0):
    """Vertical two-pin part with pin 1 at (x, ytop). top/bot: rail lib_id or label name."""
    sym = part(lib_id, ref, (x, ytop + 3.81), rot=0)
    for pin, what, ln in (('1', top, toplen), ('2', bot, botlen)):
        if what is None:
            continue
        if ':' in what:
            s.stub(sym, pin, length=ln, rail=what)
        else:
            s.stub(sym, pin, length=ln or 2.54, to=what)
    return sym


# =====================================================================
# Block A: V5 smart port and RS-485
# =====================================================================
s.frame(12.7, 12.7, 200.66, 106.68, 'V5 smart port and RS-485',
        'Brain to board over one smart port. Half duplex, so the board can also send back.')

u3 = part('stellaNova:MAX33071E', 'U3', (63.5, 55.88), ref_at=(68.58, 38.1), val_at=(68.58, 40.64))
s.stub(u3, '1', 10.16, to='RS485_RX')
s.wire(u3.pin('2'), (48.26, 55.88)); s.power(GND, (48.26, 55.88), rot=270)
s.stub(u3, '3', 10.16, to='RS485_DE')
s.stub(u3, '4', 10.16, to='RS485_TX')
s.stub(u3, '8', 2.54, rail=P3V3)
s.stub(u3, '5', 0, rail=GND)

j1 = part('stellaNova:V5_SmartPort', 'J1', (124.46, 53.34))
# B line: straight across to J1.2, label part way
s.wire(u3.pin('7'), (93.98, 53.34), j1.pin('2'))
s.label('RS485_B', (93.98, 53.34), (1, 0))
# A line: dog-leg up to J1.1
s.wire(u3.pin('6'), (83.82, 60.96), (83.82, 55.88), (93.98, 55.88), j1.pin('1'))
s.label('RS485_A', (93.98, 55.88), (1, 0))
s.wire(j1.pin('3'), (111.76, 50.8)); s.power(GND, (111.76, 50.8), rot=270)
s.stub(j1, '4', 10.16, to='VBAT_PORT')

# support parts
r3 = vpass('Device:R', 'R3', 27.94, 77.47, top='RS485_DE', bot=GND)
c7 = vpass('Device:C', 'C7', 43.18, 77.47, top=P3V3, bot=GND)
r4 = part('Device:R', 'R4', (165.1, 80.01), rot=90, ref_at=(165.1, 76.2), val_at=(165.1, 83.82),
          ref_just=None, val_just=None)
s.stub(r4, '1', 2.54, to='RS485_A'); s.stub(r4, '2', 2.54, to='RS485_B')

s.text('Smart port pins (VEX cables are straight-through)\n'
       '1 = RS-485 A (non-inverting)    2 = RS-485 B (inverting)\n'
       '3 = GND                         4 = raw battery, 10 to 14.6 V\n'
       'Contact order A, B, GND, + as in the labelled VEX Forum cable photo\n'
       '(black A, red B, green GND, yellow +).\n\n'
       'U3 ~{RE} tied low, so the receiver is always on.\n'
       'R3 holds DE low: the board boots listen-only.\n'
       'R4 is DNP. Fit it only for cables over 750 mm.\n'
       'U3 MAX33071E: A/B survive +/-65 V even unpowered, so a miswired\n'
       'cable cannot kill it. Cheaper drop-in: ST3485EBDR (14 V max).', (55.88, 78.74))

# =====================================================================
# Block B: power input and 3.3 V buck
# =====================================================================
s.frame(12.7, 111.76, 200.66, 200.66, 'Power input and 3.3 V buck',
        'Raw battery in, reverse and surge protected, USB fallback for bench work.')
RAIL = 132.08
f1 = part('Device:Polyfuse', 'F1', (31.75, RAIL), rot=90, ref_at=(31.75, RAIL - 3.81), val_at=(31.75, RAIL + 3.81),
          ref_just=None, val_just=None)
s.wire((20.32, RAIL), f1.pin('1')); s.label('VBAT_PORT', (20.32, RAIL), (-1, 0))
d2 = part('Device:D_Schottky', 'D2', (48.26, RAIL), rot=180, ref_at=(48.26, RAIL - 3.81), val_at=(48.26, RAIL + 3.81),
          ref_just=None, val_just=None)
s.wire(f1.pin('2'), d2.pin('2'))
# VIN rail: D2 cathode -> taps -> U2 IN
taps = [52.07, 57.15, 69.85, 83.82, 99.06, 109.22, 119.38]
s.wire(*[(x, RAIL) for x in taps])
d3 = part('Device:D_Schottky', 'D3', (57.15, RAIL - 3.81), rot=90, ref_at=(64.77, RAIL - 5.08),
          val_at=(66.04, RAIL - 2.54), ref_just=None, val_just=None)
s.power(VBUS, d3.pin('2'))
s.wire((57.15, RAIL), (57.15, RAIL + 2.54)); s.power(VIN, (57.15, RAIL + 2.54), rot=180)
d1 = part('Diode:SMAJ18A', 'D1', (69.85, RAIL + 3.81), rot=270, ref_at=(72.39, RAIL + 2.54), val_at=(72.39, RAIL + 5.08))
s.power(GND, d1.pin('2'))
c1 = vpass('Device:C', 'C1', 83.82, RAIL, bot=GND)
c2 = vpass('Device:C', 'C2', 99.06, RAIL, bot=GND)
r1 = vpass('Device:R', 'R1', 109.22, RAIL)
r2 = vpass('Device:R', 'R2', 109.22, RAIL + 7.62, bot=GND)
u2 = part('stellaNova:AP63301WU', 'U2', (129.54, 134.62), ref_at=(119.38, 123.19), val_at=(119.38, 125.73))
s.wire(r1.pin('2'), (115.57, RAIL + 7.62), (115.57, 137.16), u2.pin('2'))
s.stub(u2, '4', 0, rail=GND)
# SW node, BST, L1, FB
s.wire(u2.pin('5'), (143.51, RAIL), (147.32, RAIL))
s.label('SW', (143.51, RAIL), (0, -1))
s.stub(u2, '6', 2.54, to='BST')
l1 = part('Device:L', 'L1', (151.13, RAIL), rot=90, ref_at=(151.13, RAIL - 3.81), val_at=(151.13, RAIL + 3.81),
          ref_just=None, val_just=None)
out_taps = [154.94, 160.02, 170.18, 180.34, 190.5]
s.wire(*[(x, RAIL) for x in out_taps])
s.power(P3V3, (160.02, RAIL))
r20 = vpass('Device:R', 'R20', 160.02, RAIL)                 # FB divider top
r21 = vpass('Device:R', 'R21', 160.02, RAIL + 7.62, bot=GND)  # FB divider bottom
s.wire(u2.pin('1'), (146.05, 137.16), (146.05, RAIL + 7.62), (152.4, RAIL + 7.62), r20.pin('2'))
c13 = vpass('Device:C', 'C13', 153.67, 149.86, top=P3V3, bot='FB')
s.label('FB', (152.4, RAIL + 7.62), (0, 1))
c4 = vpass('Device:C', 'C4', 170.18, RAIL, bot=GND)
c5 = vpass('Device:C', 'C5', 180.34, RAIL, bot=GND)
c6 = vpass('Device:C_Polarized', 'C6', 190.5, RAIL, bot=GND)
c3 = part('Device:C', 'C3', (143.51, 149.86 + 3.81))
s.stub(c3, '1', 2.54, to='BST'); s.stub(c3, '2', 2.54, to='SW')
# ERC power flags: rail symbol, short wire, flag
for i, rail in enumerate([VIN, P3V3, VBUS]):
    x = 127.0 + i * 17.78
    s.power(rail, (x, 180.34)); s.wire((x, 180.34), (x + 7.62, 180.34)); s.power(FLAG, (x + 7.62, 180.34))
s.power(GND, (187.96, 177.8)); s.power(FLAG, (187.96, 177.8))
s.text('ERC power flags (no parts)', (127.0, 186.69))

s.text('U2 AP63301: adjustable buck, 0.8 V FB, 500 kHz forced PWM, 3 A rated, 0.57 A worst case here.\n'
       'Vout = 0.8 V x (1 + 93.1k / 30.1k) = 3.27 V. C13 56 pF feed-forward and C4, C5 2 x 22 uF per datasheet.\n'
       'L1 10 uH (datasheet range 2.2 to 10 uH): ripple 0.51 A at 14.6 V in. Isat 4.6 A at 20% drop.\n'
       'C6 220 uF is DNP: the datasheet characterises 22 to 68 uF out. Fit only if a load-step test shows a need.\n'
       'Port current worst case: about 220 mA peak, 50 mA average at 10 V battery.\n'
       'D2 blocks reverse polarity. D3 lets USB run the board on the bench, and D2 stops it back-feeding the brain.\n'
       'D1 18 V standoff clears a 14.6 V battery and clamps under the 35 V buck limit.\n'
       'R1 enables the buck from VIN. R2 (DNP) adds a UVLO divider, but fitted it stops USB start-up.', (15.24, 176.53))

# =====================================================================
# Block C: ESP32-S3 module
# =====================================================================
s.frame(205.74, 12.7, 322.58, 160.02, 'ESP32-S3 module',
        'WiFi 2.4 GHz and Bluetooth LE 5. Native USB, no bridge chip.')
u1 = part('RF_Module:ESP32-S3-WROOM-1', 'U1', (264.16, 83.82), ref_at=(269.24, 53.34), val_at=(269.24, 55.88))
left = {'3': 'ESP_EN', '27': 'BOOT', '39': 'SD_DET', '38': 'SD_D2', '17': 'RS485_RX', '18': 'RS485_DE',
        '19': 'RS485_TX', '21': 'LED_LINK', '22': 'LED_ACT'}
right = {'37': 'U0TXD', '36': 'U0RXD', '13': 'ESP_USB_DN', '14': 'ESP_USB_DP', '31': 'SD_D1', '32': 'SD_D0',
         '33': 'SD_CLK', '34': 'SD_CMD', '35': 'SD_D3'}
for pin in u1.pins:
    if pin in ('1', '40', '41'):
        continue
    if pin == '2':
        s.stub(u1, pin, 2.54, rail=P3V3)
    elif pin in left:
        s.stub(u1, pin, 7.62, to=left[pin])
    elif pin in right:
        s.stub(u1, pin, 7.62, to=right[pin])
    else:
        s.stub(u1, pin, nc=True)
s.stub(u1, '1', 0, rail=GND)

c8 = vpass('Device:C', 'C8', 215.9, 124.46, top=P3V3, bot=GND)
c9 = vpass('Device:C', 'C9', 226.06, 124.46, top=P3V3, bot=GND)
r5 = vpass('Device:R', 'R5', 238.76, 124.46, top=P3V3, bot='ESP_EN')
c10 = vpass('Device:C', 'C10', 251.46, 124.46, top='ESP_EN', bot=GND)
sw1 = part('Switch:SW_Push', 'SW1', (271.78, 132.08), ref_at=(271.78, 127.0), val_at=(271.78, 135.89),
           ref_just=None, val_just=None)
s.stub(sw1, '1', 2.54, to='ESP_EN'); s.stub(sw1, '2', 2.54, rail=GND)
r6 = vpass('Device:R', 'R6', 289.56, 124.46, top=P3V3, bot='BOOT')
sw2 = part('Switch:SW_Push', 'SW2', (304.8, 147.32), ref_at=(304.8, 142.24), val_at=(304.8, 151.13),
           ref_just=None, val_just=None)
s.stub(sw2, '1', 2.54, to='BOOT'); s.stub(sw2, '2', 2.54, rail=GND)
s.text('SW1 RESET, SW2 BOOT. Hold BOOT, tap RESET for the ROM bootloader.', (208.28, 152.4))

# =====================================================================
# Block D: USB-C
# =====================================================================
s.frame(327.66, 12.7, 406.4, 106.68, 'USB-C',
        'Flashing, JTAG, wired console and bench power.')
j2 = part('Connector:USB_C_Receptacle_USB2.0_16P', 'J2', (345.44, 55.88), ref_at=(335.28, 33.02), val_at=(335.28, 35.56))
s.wire(j2.pin('A4'), (365.76, 40.64)); s.power(VBUS, (365.76, 40.64))
s.stub(j2, 'A5', 5.08, to='CC1'); s.stub(j2, 'B5', 2.54, to='CC2')
s.wire(j2.pin('A7'), (363.22, 53.34), (368.3, 53.34)); s.wire(j2.pin('B7'), (363.22, 55.88), (363.22, 53.34))
s.label('USB_DN', (368.3, 53.34), (1, 0))
s.wire(j2.pin('A6'), (363.22, 58.42), (363.22, 60.96), (368.3, 60.96)); s.wire(j2.pin('B6'), (363.22, 60.96))
s.label('USB_DP', (368.3, 60.96), (1, 0))
s.stub(j2, 'A8', nc=True); s.stub(j2, 'B8', nc=True)
s.stub(j2, 'A1', 0, rail=GND); s.stub(j2, 'S1', 0, rail=GND)
r7 = vpass('Device:R', 'R7', 378.46, 66.04, top='CC1', bot=GND)
r8 = vpass('Device:R', 'R8', 388.62, 66.04, top='CC2', bot=GND)
r22 = vpass('Device:R', 'R22', 398.78, 66.04, top=VBUS, bot=GND)   # holds VBUS at 0 V when port powered
d5 = part('Power_Protection:USBLC6-2SC6', 'D5', (391.16, 45.72), ref_at=(377.19, 53.34), val_at=(377.19, 55.88))
s.stub(d5, '1', 2.54, to='USB_DN'); s.stub(d5, '6', 2.54, to='USB_DN')
s.stub(d5, '3', 2.54, to='USB_DP'); s.stub(d5, '4', 2.54, to='USB_DP')
s.stub(d5, '5', 0, rail=VBUS); s.stub(d5, '2', 0, rail=GND)
r18 = part('Device:R', 'R18', (355.6, 85.09), rot=90, ref_at=(355.6, 81.28), val_at=(355.6, 88.9), ref_just=None, val_just=None)
s.stub(r18, '1', 2.54, to='USB_DN'); s.stub(r18, '2', 2.54, to='ESP_USB_DN')
r19 = part('Device:R', 'R19', (355.6, 95.25), rot=90, ref_at=(355.6, 91.44), val_at=(355.6, 99.06), ref_just=None, val_just=None)
s.stub(r19, '1', 2.54, to='USB_DP'); s.stub(r19, '2', 2.54, to='ESP_USB_DP')
s.text('5.1 k CC pulldowns: USB sink, 5 V only.\nR18/R19 22 ohm series close to U1. D+/D- as a 90 ohm pair.\n'
       'R22 drains D3 leakage so VBUS reads 0 V on port power and a host will attach.', (330.2, 100.33))

# =====================================================================
# Block E: microSD
# =====================================================================
s.frame(327.66, 111.76, 406.4, 200.66, 'microSD logging',
        'Keeps logging when the wireless link drops.')
j3 = part('Connector:Micro_SD_Card_Det_Hirose_DM3AT', 'J3', (378.46, 147.32), ref_at=(355.6, 128.27), val_at=(355.6, 130.81))
sdmap = {'1': 'SD_D2', '2': 'SD_D3', '3': 'SD_CMD', '5': 'SD_CLK', '7': 'SD_D0', '8': 'SD_D1', '10': 'SD_DET'}
for pin, net in sdmap.items():
    s.stub(j3, pin, 10.16, to=net)
s.wire(j3.pin('4'), (353.06, 144.78)); s.power(P3V3, (353.06, 144.78), rot=90)
s.wire(j3.pin('6'), (353.06, 149.86)); s.power(GND, (353.06, 149.86), rot=270)
s.wire(j3.pin('9'), (353.06, 160.02)); s.power(GND, (353.06, 160.02), rot=270)
s.wire(j3.pin('11'), (401.32, 160.02)); s.power(GND, (401.32, 160.02))
for i, (ref, net) in enumerate([('R9', 'SD_CMD'), ('R10', 'SD_D0'), ('R11', 'SD_D1'), ('R12', 'SD_D2'),
                                ('R13', 'SD_D3'), ('R14', 'SD_DET')]):
    vpass('Device:R', ref, 335.28 + i * 8.89, 172.72, top=P3V3, bot=net)
c11 = vpass('Device:C', 'C11', 389.89, 172.72, top=P3V3, bot=GND)
c12 = vpass('Device:C', 'C12', 398.78, 172.72, top=P3V3, bot=GND)

# =====================================================================
# Block F: status, test points, mounting
# =====================================================================
s.frame(12.7, 205.74, 200.66, 251.46, 'Status LEDs and test points',
        'About 1.3 mA per LED through 1 k. Blue and InGaN green need too much voltage for 3.3 V.')
for i, (rref, dref, top) in enumerate([('R15', 'D6', P3V3), ('R16', 'D7', 'LED_LINK'), ('R17', 'D8', 'LED_ACT')]):
    x = 27.94 + i * 22.86
    rr = vpass('Device:R', rref, x, 226.06, top=top)
    led = part('Device:LED', dref, (x, 226.06 + 7.62 + 3.81), rot=90, ref_at=(x + 6.35, 236.22), val_at=(x + 6.35, 238.76),
               ref_just=None, val_just=None)
    s.power(GND, led.pin('1'))
for i, (ref, net) in enumerate([('TP1', VIN), ('TP2', P3V3), ('TP3', GND), ('TP4', 'U0TXD'), ('TP5', 'U0RXD')]):
    x = 106.68 + i * 17.78
    tp = part('Connector:TestPoint', ref, (x, 231.14), ref_at=(x + 1.27, 224.79), val_at=(x + 1.27, 227.33))
    if net == GND:
        s.power(GND, tp.pin('1'))
    elif ':' in net:
        s.wire(tp.pin('1'), (x, 233.68)); s.power(net, (x, 233.68), rot=180)
    else:
        s.stub(tp, '1', 2.54, to=net)
s.text('No mounting holes: the board hangs from its smart cable.\n'
       'Keep metal at least 15 mm from the antenna end for good range.', (106.68, 243.84))

# =====================================================================
# Firmware notes
# =====================================================================
s.frame(205.74, 165.1, 322.58, 246.38, 'Firmware pin map', 'All signals 3.3 V. GPIO numbers are ESP32-S3 IO numbers.')
s.text('RS-485  RX IO9   DE IO10   TX IO11   (UART_MODE_RS485_HALF_DUPLEX, RTS = IO10)\n'
       'USB     D- IO19  D+ IO20   (USB Serial/JTAG, auto-reset into bootloader)\n'
       'microSD CLK IO40  CMD IO41  D0 IO39  D1 IO38  D2 IO2  D3 IO42  DET IO1 (low = card in)\n'
       'LEDs    LINK IO13  ACT IO14  (high = on)\n'
       'Buttons RESET = EN,  BOOT = IO0\n'
       'UART0   TX IO43 (TP4), RX IO44 (TP5): ROM boot log\n\n'
       'Brain side: vexGenericSerialEnable(port, 0) then\n'
       'vexGenericSerialBaudrate(port, 230400). PROS: pros::Serial.\n\n'
       'Module N16R2 has quad PSRAM: set PSRAM mode to Quad, not Octal.\n'
       'Strapping pins IO3, IO45, IO46 are left floating on purpose\n'
       '(internal defaults give SPI boot and 3.3 V flash).',
       (208.28, 177.8), size=1.4)

os.makedirs(OUT, exist_ok=True)
custom.write_lib(os.path.join(OUT, 'stellaNova.kicad_sym'))
s.write(os.path.join(OUT, PROJECT + '.kicad_sch'))
import json
json.dump(s.nc_pins, open(os.path.join(os.path.dirname(__file__), 'nc_pins.json'), 'w'))
print('ok', len(s.syms), 'symbols')
