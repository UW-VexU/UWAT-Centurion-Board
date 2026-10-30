# uwat-stellaNova, rev A

stellaNova is a VEX V5 wireless debugger. Full name: uwat-stellaNova.

It is an ESP32-S3 board that plugs into one VEX V5 smart port, receives whatever the brain writes to that port
over RS-485, and serves it to a laptop, phone or tablet over WiFi or Bluetooth LE. It can also send
commands back to the brain over the same wire (half duplex). Powered from the V5 battery through the
smart port, or from USB-C on the bench.

## What is in this folder

- The KiCad project is in this folder: open `uwat-stellaNova.kicad_pro` in KiCad 10. The project symbols
  (`stellaNova.kicad_sym`), footprints (`stellaNova.pretty/`) and 3D models (`3dmodels/`) are here too.
- `archive/uwat-stellaNova-4layer.kicad_pcb`: the original 4-layer board, kept for reference.
- `fabrication/`: **still the old 4-layer outputs. Regenerate the gerbers, drill and placement files from the 2-layer
  board before ordering.** `gerbers/` holds the files unzipped, plus the drill map PDFs.
- `bom/`: `uwat-stellaNova_revA_BOM.xlsx` (prices, order quantities, notes), `uwat-stellaNova_revA_DigiKey_upload.csv`
  (upload in DigiKey BOM Manager), plus a plain CSV BOM and a JLCPCB-style BOM.
- `docs/`: schematic PDF and PNG, layout, assembly and 3D renders, and a STEP model of the assembled board.
  The layout and 3D renders still show the 4-layer board.
- `AUDIT.md`: design audit results. `generator-scripts/`: the scripts that built the design, for reference only.

## Ordering the PCB

- Regenerate the gerbers first (see `fabrication/` above). Layers: 2. Thickness: 1.6 mm. Copper: 1 oz.
- No impedance control needed. USB here is full speed.
- Min track/spacing: the board uses 0.15 mm gaps, so pick 5/5 mil (0.127 mm) or finer.
- Min hole: 0.2 mm. The ESP32 module footprint has 0.2 mm thermal vias. Normal vias are 0.3 mm.
- Surface finish: lead-free HASL works. ENIG gives flatter pads for the ESP32 module and USB-C if hand soldering.
- Any solder mask color. Vias are tented in the files.

## Board

- 48 x 40 mm, 2 layers, 1.6 mm FR4. Both layers carry signals and a GND pour. 3.3 V runs as a 0.3 mm trace,
  mostly on the back, from L1 to every 3.3 V pin. Rev A was first laid out on 4 layers with inner GND and 3.3 V
  planes. See AUDIT.md for the conversion.
- ESP32 antenna overhangs the top edge by 6 mm (Espressif's preferred placement). Keep metal 15 mm away.
- No mounting holes. The board hangs from its smart cable.
- All parts on the top side, so single-sided assembly. Test pads are on the back.
- USB-C alone gives the 500 mA USB 2.0 default. Worst case the board draws about 480 mA from it,
  so use a powered hub or the brain for long WiFi sessions. R22 keeps VBUS at 0 V on port power
  so a laptop still attaches when plugged in later.
- D5 (USB ESD protection) has its supply pin, pin 5, on 3.3 V rather than VBUS. So on port power the
  ESP32's D+ pull-up cannot lift VBUS through D5. USB and the smart cable can go in either order.
- C6 (220 uF bulk) is not fitted: the buck datasheet characterises 22 to 68 uF of output
  capacitance. Fit it only if a load-step test shows a dip on 3.3 V.

- U3 is MAX33071EASA+: its A/B pins survive +/-65 V even unpowered, so a miswired or damaged
  smart cable cannot kill it. ST3485EBDR (497-2080-1-ND, about $2.49) is a cheaper drop-in with
  the same pinout, but its bus pins are only rated 14 V.
- J1 pin field: other nets keep 0.5 mm from J1's pins (custom rule in the .kicad_dru), so a solder
  bridge on the hand-soldered jack cannot reach USB or a GPIO.
- Battery copper (VBAT_PORT and the fuse to diode link) keeps 0.5 mm from every other net ("Battery"
  net class), so a bridge or debris cannot put 14 V on an ESP32 pin.
- 3.3 V buck: the 10 uF input cap sits right across the U2 VIN and GND pins, the switch node runs
  straight out to L1, and the output caps sit next to L1. Feedback is on the far side, away from SW.
- SW1 (RESET) and SW2 (BOOT) are C&K PTS810 push buttons. Per the datasheet, pins 1 and 2 are tied
  together, pins 3 and 4 are tied together, and pressing the button joins the two pairs. The
  footprint and wiring match that.
- Do not populate parts (C6, R2, R4) have no paste openings and are left out of the placement file.

## Things to know when writing firmware or using it

- RS-485 echo: the receiver is always on (RE tied low), so the ESP32 hears its own transmissions on
  RX. Throw away the echoed bytes after each send, or use them to check for bus collisions.
- IO39 to IO42 go to the microSD card, so pin JTAG is not available. Use the built in USB JTAG.

## If you use JLCPCB assembly

- The BOM lists DigiKey parts. Match each line to an LCSC part in the JLCPCB tool, or hand solder.
- Check every part rotation in the JLCPCB placement preview. KiCad and JLCPCB do not always agree
  on the zero angle, especially for the ESP32 module, USB-C, the diodes and the LEDs.
- J1 (smart port jack) is through-hole. Hand solder it after assembly.

## Check before first power-up

0. Before ordering, print `docs/uwat-stellaNova-1to1-print.pdf` at 100% scale (not "fit to page")
   and set a real Molex 43202-4101 jack on it. Its pins and the two pegs must line up with the holes.
1. Jack pin map: 1 = RS-485 A, 2 = RS-485 B, 3 = GND, 4 = battery. Contact order is A, B, GND, + as
   on the labelled smart cable photo on the VEX Forum (black A, red B, green GND, yellow +).
   VEX smart cables are straight-through.
2. On the first board, plug a smart cable into J1 and beep each wire through to the pads on the back:
   black to J1.1, red to J1.2, green to J1.3, yellow to J1.4. Also beep each button: SW1 should
   short EN to GND only while pressed, SW2 should short IO0 to GND only while pressed.
3. Power from USB-C first: 3.3 V on TP2. Then plug into the brain with USB unplugged. The PWR LED
   should light. If it does not, unplug: nothing is damaged (D2 blocks reverse, U3 is 65 V rated).
4. Scope A/B during bring-up and confirm the brain releases the bus between transmissions.
5. Load-step 3.3 V (50 to 400 mA) at 10 V and 14.6 V in. Fit C6 only if it dips.

## Firmware pin map

| Function | GPIO |
|---|---|
| RS-485 RX / DE / TX | IO9 / IO10 / IO11 (UART RS485 half-duplex mode, RTS = IO10) |
| USB D- / D+ | IO19 / IO20 (USB Serial/JTAG) |
| microSD CLK / CMD / D0 / D1 / D2 / D3 | IO40 / IO41 / IO39 / IO38 / IO2 / IO42 |
| microSD card detect | IO1 (low = card in) |
| LEDs LINK / ACT | IO13 / IO14 (high = on) |
| BOOT / RESET | IO0 / EN |
| UART0 TX / RX (back pads) | IO43 / IO44 |

Module is ESP32-S3-WROOM-1-N16R2: set PSRAM to Quad (QSPI) mode, not Octal.

Brain side: `vexGenericSerialEnable(port, 0)` then `vexGenericSerialBaudrate(port, 230400)`, or `pros::Serial`.

## Verification

2-layer board, checked with KiCad 10 on 2026-10-30. The report is `uwat-stellaNova-drc.rpt`.

- ERC: 0 errors.
- PCB DRC, with the J1 pin-field rule and the 0.5 mm battery rule: 0 violations, 0 unconnected.
- Schematic to PCB parity: 0 issues. Every pad is on the net the schematic gives it.
- The board file is KiCad 10 format, so KiCad 9 and older cannot open it. The schematic is still KiCad 7 format.

## BOM (DigiKey Canada, checked 2026-10-30)

| Qty | Refs | Value | MPN | DigiKey CA | Stock | CAD qty 1 |
|---|---|---|---|---|---|---|
| 1 | C1 | 10uF 50V | Samsung CL32B106KBJNNNE | 1276-3387-1-ND | 742,985 | $1.02 |
| 5 | C2 C3 C7 C9 C12 | 100nF | Yageo CC0603KRX7R9BB104 | 311-1344-1-ND | 4,044,224 | $0.21 |
| 2 | C4 C5 | 22uF | Murata GRM21BR61A226ME51L | 490-10511-1-ND | 269,759 | $0.30 |
| 2 | C8 C11 | 10uF | Murata GRM21BR61E106KA73K | 490-16824-1-ND | 88,143 | $0.25 |
| 1 | C10 | 1uF | TDK C1608X5R1H105K080AB | 445-7468-1-ND | 105,003 | $0.25 |
| 1 | C13 | 56pF | KEMET C0603C560J5GACTU | 399-C0603C560J5GACTUCT-ND | 153,858 | $0.15 |
| 1 | D1 | SMAJ18A | Bourns SMAJ18A | SMAJ18ABCT-ND | 29,489 | $0.77 |
| 2 | D2 D3 | PMEG6020ER | Nexperia PMEG6020ER,115 | 1727-5217-1-ND | 375,398 | $0.74 |
| 1 | D5 | USBLC6-2SC6 | STMicroelectronics USBLC6-2SC6 | 497-5235-1-ND | 63,343 | $0.80 |
| 1 | D6 | Green | Lite-On LTST-C191KGKT | 160-1446-1-ND | 2,712,898 | $0.24 |
| 1 | D7 | Orange | Lite-On LTST-C191KFKT | 160-1445-1-ND | 195,728 | $0.22 |
| 1 | D8 | Red | Lite-On LTST-C191KRKT | 160-1447-1-ND | 1,354,761 | $0.24 |
| 1 | F1 | PTC 0.5 A 30 V | Bel Fuse 0ZCG0050AF2C | 5923-0ZCG0050AF2CCT-ND | 345,670 | $0.31 |
| 1 | J1 | V5 smart port (4P4C) | Molex 0432024101 | WM5439-ND | 2,540 | $2.18 |
| 1 | J2 | USB-C 2.0 | GCT USB4105-GF-A | 2073-USB4105-GF-ACT-ND | 85,103 | $1.19 |
| 1 | J3 | microSD push-push | Hirose DM3AT-SF-PEJM5 | HR1964CT-ND | 76,375 | $5.27 |
| 1 | L1 | 10uH | Wurth 74438357100 | 732-11206-1-ND | 15,980 | $2.68 |
| 1 | R1 | 100k | Stackpole RMCF0603FT100K | RMCF0603FT100KCT-ND | 970,951 | $0.17 |
| 9 | R3 R5 R6 R9 R10 R11 R12 R13 R14 | 10k | Yageo RC0603FR-1310KL | 13-RC0603FR-1310KLCT-ND | 221,620 | $0.16 |
| 3 | R7 R8 R22 | 5.1k | Yageo RC0603FR-075K1L | 311-5.10KHRCT-ND | 405,843 | $0.16 |
| 3 | R15 R16 R17 | 1k | Yageo RC0603FR-071KL | 311-1.00KHRCT-ND | 1,993,948 | $0.17 |
| 2 | R18 R19 | 22 | Stackpole RMCF0603FT22R0 | RMCF0603FT22R0CT-ND | 2,171,898 | $0.16 |
| 1 | R20 | 93.1k | Stackpole RMCF0603FT93K1 | RMCF0603FT93K1CT-ND | 216,165 | $0.16 |
| 1 | R21 | 30.1k | Yageo RC0603FR-0730K1L | 311-30.1KHRCT-ND | 119,797 | $0.16 |
| 2 | SW1 SW2 | Tactile | C&K PTS810 SJM 250 SMTR LFS | CKN10502CT-ND | 69,851 | $0.92 |
| 1 | U1 | ESP32-S3-WROOM-1-N16R2 | Espressif ESP32-S3-WROOM-1-N16R2 | 5407-ESP32-S3-WROOM-1-N16R2CT-ND | 4,702 | $10.61 |
| 1 | U2 | AP63301WU-7 | Diodes Inc AP63301WU-7 | 31-AP63301WU-7CT-ND | 13,846 | $1.52 |
| 1 | U3 | MAX33071EASA+ | Analog Devices MAX33071EASA+ | 505-MAX33071EASA+-ND | 2,956 | $12.30 |

Do not populate: C6 R2 R4

