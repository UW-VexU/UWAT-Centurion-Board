# uwat-stellaNova rev A: design audit

## Converted to 2 layers, 2026-10-30

The board below was first audited as a 4-layer design. It is now 2 layers. The original 4-layer board is in `archive/uwat-stellaNova-4layer.kicad_pcb`.

- **What changed.** The In1 GND plane and the In2 3.3 V plane were removed. All 482 existing tracks and vias were locked and kept exactly as they were. Freerouting 2.5.0 routed only the 20 3.3 V connections that used to drop into In2. Its other output was discarded.
- **3.3 V route.** 55 new segments, 132 mm, 0.3 mm wide (four short necks at 0.225 mm), mostly on the back. It reuses the existing 3.3 V vias. At a 500 mA WiFi peak the trace drops about 50 mV, so the ESP32 still sees about 3.2 V. C8 and C9 (10 µF and 100 nF) sit at its 3V3 pin.
- **Ground.** GND is carried by the top and bottom pours, tied by 50 stitching vias. One via was added at C12, whose GND pad was boxed in by the new 3.3 V route. Four 3.3 V vias that no longer joined two layers were removed, three of them with their pad stubs. TP2, a pad on the back, now joins the 3.3 V route with a short trace on the back.
- **Checks on the result.** ERC 0 errors. DRC 0 violations and 0 unconnected, including the J1 pin-field rule and the 0.5 mm battery rule. Schematic to PCB parity 0 issues. All 57 footprints and their 3D models load.
- **Datasheet check of the circuit.** U2 (AP63301): pins FB 1, EN 2, VIN 3, GND 4, SW 5, BST 6. R20 93.1k, R21 30.1k, C1 10 µF, 2 x 22 µF out, C3 100 nF and C13 56 pF all match Table 1 for 3.3 V. Output is 3.27 V. L1 is 10 µH against 4.7 µH in Table 1, inside the 2.2 to 10 µH the datasheet allows. EN and VIN are rated to 35 V, above D1's clamp. U3 (MAX33071E): SO-8, half duplex, 3 to 5.5 V supply, 2 Mbps, ±65 V on A and B.
- **Open from the review.** On port power with USB unplugged, D5's VBUS pin lets the ESP32's D+ pull-up lift VBUS to about 2 V (see the README). Tying D5 pin 5 to 3.3 V instead of VBUS would remove this. Not changed yet.

The rest of this file is the 4-layer audit.

stellaNova is the VEX V5 wireless debugger. Checked 2026-10-30 in two rounds. In the first round an independent reviewer checked every connection, and every symbol pin against its footprint and datasheet. Stock, trace widths and layout rules were measured on the board. A second, fresh reviewer then went over the schematic and layout again. Everything it raised is fixed or noted below, and all checks were run again on the final files.

## Result

| Check | Result |
|---|---|
| Schematic connectivity (ERC rules on the netlist) | 0 errors |
| PCB DRC, KiCad 7, with the J1 pin-field rule and the 0.5 mm battery rule | 0 violations, 0 unconnected |
| Strict DRC (all ignored checks turned back on) | only 3 expected items, listed below |
| Schematic to PCB parity | 57 of 57 footprints, 0 pad net mismatches |
| Symbol pin to footprint pad to datasheet | all 57 parts match |
| DigiKey Canada stock | all 31 lines Active and in stock |
| Parts cost per board | CAD 48.46 at qty 1, 36.70 at qty-10 pricing |

## Fixed in the first round

1. **Smart port A/B were swapped.** J1 now reads 1 = A, 2 = B, 3 = GND, 4 = battery. That gives the contact order A, B, GND, + from the labelled smart cable photo on the VEX Forum.
2. **U3 could die from a bad cable.** The ST3485EBDR bus pins are rated 14 V, but a full battery is 14.6 V. U3 is now the MAX33071EASA+: same pinout, ±65 V fault protected even unpowered, true fail-safe, 2 Mbps. The ST3485EBDR remains a cheaper drop-in.
3. **Traces ran between J1's pins.** VBUS and LED_ACT passed 0.19 mm from the jack's solder pins. A bridge there could put battery voltage on a laptop's USB port. Both were re-routed. A permanent rule in `uwat-stellaNova.kicad_dru` now keeps other nets 0.5 mm from J1's pins, and DRC enforces it.
4. **VBUS could float on port power.** Leakage through D3 could hold VBUS up, and a laptop would then refuse to attach. R22 (5.1 k to GND) fixes this.
5. **Output capacitance.** C6 (220 µF) is now DNP. That keeps the 3.3 V output inside the 22 to 68 µF range the buck datasheet characterises.
6. **Silkscreen.** All labels are now at least 0.8 mm tall with 0.15 mm strokes, and none overlap. BOOT moved beside SW2.
7. **Housekeeping.** Fixed the L1 value text and the J1 library model path, removed the unused SM712 line, and added a note on R2 and USB start-up.

## Fixed in the second round

1. **3.3 V buck layout.** The 10 µF input cap was 5.3 mm from U2's VIN pin. U2 and its parts were re-placed and the power copper hand routed:
   - C1 now sits right across the U2 VIN and GND pins (2.5 mm centre to centre, 0.6 mm traces), with C2 beside it.
   - The switch node runs 2 mm straight out to L1.
   - C4 and C5 sit next to L1 on top copper, with their grounds tied together and stitched to the GND plane.
   - The feedback divider sits on the far side of U2, away from the switch node.
2. **Battery copper too close to ESP32 pins.** BOOT and LED_LINK came within 0.20 to 0.37 mm of the battery trace and fuse. A new "Battery" net class keeps VBAT_PORT and the fuse to diode link 0.5 mm from every other net. BOOT now drops to the back layer beside J1, and the LED_LINK via moved up. DRC enforces this.
3. **Button pin pairing.** The reviewer could not confirm which PTS810 pins are tied inside. The C&K datasheet shows pins 1 and 2 tied, pins 3 and 4 tied, and the button joining the two pairs. The footprint and wiring match that, so no change was needed.
4. **Not-fitted parts.** C6, R2 and R4 now have no paste openings and are left out of the pick-and-place file.
5. **J1 test fit.** The J1 footprint text no longer says "ultra low profile". A 1:1 print PDF is now in `docs/` so a real jack can be checked against it before ordering.
6. **README notes added.** RS-485 echo (the receiver is always on), no pin JTAG (IO39 to IO42 go to the microSD), USB VBUS sitting near 2 V on port power, and JLCPCB assembly tips.
7. **Name.** The board is now uwat-stellaNova everywhere: KiCad files, library, title block, silkscreen, BOM and zip.
8. **Part number.** The PTS810 part number now reads the same in every file.

## Stock, DigiKey Canada, 2026-10-30

| Part | DigiKey CA | Stock | CAD qty 1 |
|---|---|---|---|
| ESP32-S3-WROOM-1-N16R2 | 5407-ESP32-S3-WROOM-1-N16R2CT-ND | 4,702 | 10.61 |
| MAX33071EASA+ | 505-MAX33071EASA+-ND | 2,956 | 12.30 |
| AP63301WU-7 | 31-AP63301WU-7CT-ND | 13,846 | 1.52 |
| Molex 0432024101 (J1) | WM5439-ND | 2,540 | 2.18 |
| GCT USB4105-GF-A | 2073-USB4105-GF-ACT-ND | 85,103 | 1.19 |
| Hirose DM3AT-SF-PEJM5 | HR1964CT-ND | 76,375 | 5.27 |
| Würth 74438357100 (10 µH, Isat 4.6 A, 110 mΩ max) | 732-11206-1-ND | 15,980 | 2.68 |
| All passives, diodes, LEDs, buttons | see the BOM | 29,489 to 4,044,224 | 0.15 to 2.12 |

The smallest stocks are J1, U3 and U1, at thousands each. TI's protected transceivers (THVD1450DR, THVD2450DR, SN65HVD75DR, SN65HVD78DR) all showed 0 in stock in Canada, which is why U3 is the Maxim part.

## Layout and traces

- **Widths.** Each width suits the current it carries (IPC-2221, outer layer, 1 oz, 10 °C rise).
  - Power (VIN, port battery, SW node): 0.4 mm, and 0.6 mm in the buck's input and output loops.
  - 3.3 V, VBUS, GND: 0.3 mm, and 0.6 mm at the buck.
  - USB pair: 0.25 mm.
  - Signals: 0.2 mm.
  - Nothing is under 0.2 mm or over 0.6 mm.
- **Spacing.** 0.15 mm general, 0.2 mm for power, 0.5 mm around battery copper and around J1's pins.
- **Vias.** All are 0.6 mm pad with 0.3 mm drill (0.15 mm ring). Every via is tented. The smallest holes are the ESP32 module's own 0.2 mm thermal vias, which are within standard 4-layer capability.
- **Corners.** No acute corners on open copper. The 10 that a raw scan finds all sit inside pads or vias.
- **Planes.** In the 4-layer version, In1 was solid GND and In2 solid 3.3 V. The 2-layer board has GND pours on both sides instead (see the top of this file). The antenna hangs past the board edge with no copper under it.
- **microSD.** Traces under the socket stay out of Hirose's five keepout zones, and the vias there are tented.
- **USB.** D+ and D- differ by 8.8 mm. That doesn't matter at USB full speed (12 Mbps).

**Notes, accepted as is:**
- The microSD 100 nF and 10 µF caps sit 14 to 16 mm from the socket's VDD pin. They connect through the solid 3.3 V and GND planes, which is fine at 25 MHz SD clock. A rev B could move the 100 nF next to the socket.
- F1 uses KiCad's generic 1812 land. It works, but Bel's own pattern would be a closer match.

**Strict DRC items that remain, all expected:**
- The ESP32 module outline runs past the board edge where the antenna overhangs. The fab trims it.
- The USB-C footprint is flagged through-hole while most of its pads are SMD. That comes from KiCad's library and is harmless.
- Library-path warnings appear because this check ran without a KiCad library install.

## Still to confirm

These can't be settled on paper. The README bring-up list covers them.

1. Before ordering, print `docs/uwat-stellaNova-1to1-print.pdf` at 100% and set a real Molex 43202-4101 jack on it.
2. Beep a smart cable through J1: black to J1.1, red to J1.2, green to J1.3, yellow to J1.4. The jack is tab-down, the same as the VEXBridge board's Evercom jack, and the staggered pins only fit one way.
3. Beep SW1 and SW2. Each should short to GND only while pressed.
4. Plug into the brain with USB unplugged. The PWR LED should light. If it doesn't, nothing is damaged.
5. Load-step test the 3.3 V rail.

## Sources

- [VEX Forum smart cable pinout photo (nickmertin)](https://www.vexforum.com/t/smart-ports-power-wire/68061/4)
- [VEX KB, V5 crimping tool (straight-through cables)](https://kb.vex.com/hc/en-us/articles/360036143012-Using-the-V5-Crimping-Tool)
- [MAX33070E/MAX33071E datasheet](https://www.mouser.com/datasheet/2/256/MAX33070E_MAX33071E-2401125.pdf)
- [ST3485EB datasheet](https://www.farnell.com/datasheets/1788494.pdf)
- [ESP32-S3-WROOM-1 datasheet](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- [AP63300/AP63301 datasheet](https://static.chipdip.ru/lib/118/DOC031118364.pdf)
- [Molex SDA-43202 drawing](https://static.chipdip.ru/lib/680/DOC044680973.pdf)
- [C&K PTS810 datasheet](https://www.ckswitches.com/media/1476/pts810.pdf)
- [DigiKey Canada](https://www.digikey.ca)
