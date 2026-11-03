# Centurion rev A: hand-routing guide

The board in `centurion.kicad_pcb` was placed by script and routed by Freerouting. It passes DRC with schematic parity (0 violations, 0 unconnected), and every connection is made. It is **not order-ready yet**. An autorouter connects pins, but it doesn't know where return current flows, so it ran 2.6 m of signal track on the bottom layer, where the ground plane should be.

This guide is the hand work that's left, in priority order. Each step says what is wrong, why it matters, exactly what to do in KiCad, and how to check it's done.

All coordinates are KiCad's absolute coordinates: what the status bar shows at the bottom of the PCB editor. The board runs from (100.0, 100.0) at the top-left corner to (203.2, 162.6) at the bottom-right. The easiest way to find a part is **Ctrl+F**, then type its reference (for example `U9`).

## Contents

0. [Set up](#0-set-up-once)
1. [ESD clamps in the signal path](#1-esd-clamps-in-the-signal-path-30-min)
2. [USB data pair](#2-usb-data-pair-1-h)
3. [RS-485 pairs to the smart ports](#3-rs-485-pairs-to-the-smart-ports-45-min)
4. [CAN pair to ramBar](#4-can-pair-to-rambar-20-min)
5. [Clear the bottom layer](#5-clear-the-bottom-layer-4-6-h-the-big-one)
6. [GND vias the script couldn't fit](#6-gnd-vias-the-script-couldnt-fit-30-min)
7. [Crystal neighbourhood](#7-crystal-neighbourhood-20-min)
8. [Silkscreen leftovers](#8-silkscreen-leftovers-15-min)
9. [Final checks](#9-final-checks)

Where we are now and the targets for "done":

| Measure | Now | Done when |
|---|---|---|
| Signal and power copper on B.Cu (not GND) | 2577 mm | under 600 mm, and no B.Cu run longer than 15 mm except along the board edge |
| Separate pieces of bottom GND pour | 11 (largest 2265 mm²) | 1 to 3, with the largest holding nearly all of it |
| USB pair spacing | mean 2.1 mm, worst 10.5 mm, 141 mm on B.Cu | the two traces side by side the whole way (gap ≤ 0.3 mm), top layer only |
| RS-485 and CAN pairs | 10 to 18 mm of one wire on B.Cu, gaps up to 4.4 mm | both wires of each pair on the same layer, side by side |
| Sensor-jack ESD | 13 to 30 mm from jack to clamp; TOF1_SDA reaches the mux before the clamp | every line goes jack, then clamp, then mux; under 15 mm to the clamp |
| DRC with schematic parity | 0 / 0 / 0 | still 0 / 0 / 0 |

Already fixed by the script (don't undo these):
- **Buck stage (U1).** Input caps C2, C32 and C3 sit in a row right above the VIN pins. Output caps C4 and C5 sit under the VOUT pins, and the feedback divider R29/R30 sits at the FB pin; the FB node is now 3.9 mm. A keep-out stops any bottom-layer track under the whole buck area, so the bottom plane there is solid.
- **Crystal.** Y1 and its load caps C22 and C23 are tight against the MCU, and the OSC traces are now 7.6 and 5.7 mm. A keep-out stops bottom tracks under them.
- **Screw heads.** Tracks and vias are kept 4.5 mm from each mounting-hole centre, so the #8 screw heads can't short anything.
- **Vias.** Every power-net layer change has 3 vias. There are 46 GND vias at ground pads, plus a GND via fence along the board edge.

## 0. Set up (once)

1. **Make a restore point.** Commit the current board, or copy `centurion.kicad_pcb` somewhere safe. Hand routing can't be undone past KiCad's undo history.
2. **Edit this board file from now on.** The layout script that generated it lives outside the repo; regenerating would throw your hand work away.
3. Open `centurion.kicad_pro` in KiCad 10 and open the PCB editor.
4. **Router mode.** Route → Interactive Router Settings:
   - Mode: **Shove**.
   - Tick **Remove redundant tracks**.
   - Tick **Optimize pad connections**.
   - Shove pushes neighbouring tracks out of the way instead of refusing.
5. **Differential pair classes for the USB pair.** Board Setup → Design Rules → Net Classes:
   - Add a class `USB` with Track width 0.25, DP width 0.25, DP gap 0.2.
   - Under Netclass assignments, assign the patterns `USB_D+`, `USB_D-`, `/Power/USB_DP` and `/Power/USB_DN` to `USB`.
   - KiCad's differential pair router recognises these names as pairs because they end in `+`/`-` or `P`/`N`.
6. **Hotkeys you'll use** (all of these are also in the menus):

   | Key | Does |
   |---|---|
   | `X` | Route a single track (click a pad, click to bend, double-click to finish) |
   | `6` | Route a differential pair |
   | `V` | While routing: drop a via and switch layer |
   | `/` | While routing: flip the corner direction |
   | `U` | With a track selected: expand the selection to the whole connection (press again to grow it) |
   | `` ` `` (backtick) | Highlight the net under the cursor (press again to clear) |
   | `Delete` | Delete the selection |
   | `B` | Refill all zones (do this after every step) |
   | `Ctrl+Shift+M` | Measure |

7. **Seeing one layer.** In the Appearance panel (right side), Layers tab, click the eye next to F.Cu or B.Cu to hide it. Hide F.Cu to see exactly what is cutting the bottom ground plane.
8. **Track lengths per layer.** Inspect → Net Inspector lists every net's track length on each layer. Use it to check the numbers in the targets table.

General rules for everything below:
- **Signals belong on top (F.Cu). The bottom (B.Cu) is the ground plane.** Use the bottom only for short hops (a few mm) to cross another top trace, at right angles to it, and climb back up.
- **A bottom trace along the board edge does little harm.** A bottom trace across the middle of the board cuts every return path that crosses it.
- **Keep GND vias next to every layer change of a signal**, so its return current can change layers too. Where you move a signal from one layer to the other, put a GND via within about 2 mm of the signal via.
- **Press B and check the bottom pour after each change.** The goal is one solid sheet.

## 1. ESD clamps in the signal path (30 min)

**Why.** An ESD clamp only protects what's behind it. A zap enters at the connector and takes the first path it finds. If the trace reaches the mux or MCU before the clamp, the chip takes the hit.

**The one real defect: TOF1_SDA (jack J9).** Its trace runs J9 pin 3, then U6 pin 10 (the mux), then the clamp U9 pin 5, 30 mm in all.
1. Ctrl+F → `J9` (the TOF1 jack at (146.3, 103.2)). Click the trace leaving its pin 3 (hover a pad to see its number and net). Press `U` until the whole TOF1_SDA trace is selected, then press `Delete`. The ratsnest (thin lines) now shows what's unconnected.
2. Press `X`, start on J9 pin 3, and route to **U9 pin 5** at about (141.0, 115.3). Keep to F.Cu.
3. From U9 pin 5, continue to **U6 pin 10** (U6 is the mux at (142.0, 122.0)).
4. Reconnect the pullup R20 to the trace anywhere between J9 and U9.
5. **Check.** Highlight the net with the backtick key. Following the copper from J9, you must reach U9 before U6.

**The other 15 jack lines (J6–J13, pins 2 and 3).** They already reach their clamp before the mux, but by detours of 15–24 mm where 11–12 mm is possible. For each one longer than about 15 mm (listed below), delete it and reroute it jack, then clamp, then mux, on top. The clamps for each pair of jacks are:
- U8 at (119.8, 115.3) for J6/J7
- U9 at (141.0, 115.3) for J8/J9
- U10 at (162.2, 115.3) for J10/J11
- U11 at (183.4, 115.3) for J12/J13

Longest first:

| Line | Now (mm) | Clamp pin |
|---|---|---|
| J10.3 TOF2_SDA | 24.7 | U10.4 |
| J12.3 TOF4_SDA | 23.6 | U11.4 |
| J7.2 ENC2_SCL | 22.5 | U8.2 |
| J8.3 LASER_SDA | 22.3 | U9.4 |
| J6.3 ENC1_SDA | 21.2 | U8.4 |
| J12.2 TOF4_SCL | 20.4 | U11.1 |
| J11.3 TOF3_SDA | 20.0 | U10.5 |
| J13.2 MUX7_SCL | 20.0 | U11.2 |
| J9.2 TOF1_SCL | 19.2 | U9.2 |
| J7.3 ENC2_SDA | 19.0 | U8.5 |
| J6.2 ENC1_SCL | 18.5 | U8.1 |
| J10.2 TOF2_SCL | 17.4 | U10.1 |
| J8.2 LASER_SCL | 16.5 | U9.1 |

The pullups (R13–R28, R42, R43) can branch off anywhere between the jack and the clamp; that's fine.

**IMU connector J5.** IMU_MOSI_H runs J5 pin 4, then R9, then the clamp U5 pin 2. Reroute it as J5.4, then U5.2 (at (184.2, 136.5)), then R9. Do the same for IMU_CS_H: J5.6, then U5.5, then R58 and R41.

## 2. USB data pair (1 h)

**Why.** USB is a differential signal: the two wires carry equal and opposite currents, and the receiver only looks at the difference. That only works if the wires stay together. Today D+ and D- take different routes, up to 10.5 mm apart, mostly on the bottom layer, and the loop between them picks up noise and radiates it. At full speed (12 Mbit/s) we don't need exact 90 Ω impedance, which a 2-layer, 1.6 mm board can't reach anyway. We do need the two traces side by side over unbroken ground.

The pair runs from the USB-C connector J16 (103.1, 116.5), through the ESD part U13 (112.0, 117.0) and the 22 Ω series resistors R38 and R39, to MCU pins **U3.46 (D+)** and **U3.45 (D-)**. Those pins are on the **right** side of U3, at (164.7, 134.2) and (164.7, 134.8). The connector-side half (J16 → U13 → R38/R39) is already short and tight (0.74 mm mean spacing), so leave it.

1. **Line up the resistors.** R38 sits at (110.3, 120.5) and R39 at (114.1, 120.4), so the pair starts 5.6 mm apart.
   - Select R39 and press `M` to move it. Put it right beside R38 at about (112.0, 120.5), pads parallel to R38's.
   - Rotate (`R`) if that lines up the pads better.
   - Reconnect the two short traces from U13.
2. **Delete the long half.**
   - Click a USB_D+ track and press `U` until it's all selected, then `Delete`.
   - Do the same for USB_D-.
   - Only the R38/R39 → U3 half should go.
3. **Pick the corridor.** Hide B.Cu and look for a top-layer path from R38/R39 to the right side of U3. U3's pins 45/46 face right, so the pair has to come around U3 into the gap between U3 and the LEDs D6–D8.
   - Suggested path: east along y ≈ 119–120 (under the sensor jack ESD row), between U6's top edge and the clamps, until about x 167, then south to y ≈ 134 and in to the pins from the right.
   - Shove mode will move other traces out of the way. Accept that, but read step 5 first: those traces belong on top too.
4. **Route it.**
   - Press `6`, click R38's MCU-side pad, and route to U3.46/45.
   - Keep corners at 45°.
   - If the pair has to change layer, do it once, with both vias side by side and a GND via right beside them.
5. **Check.**
   - USB_D+ and USB_D- are on F.Cu end to end, side by side, with lengths within about 2 mm of each other.
   - Hide F.Cu: no slot in the bottom GND crosses under the pair.

## 3. RS-485 pairs to the smart ports (45 min)

**Why.** RS-485 is differential like USB, and the cable to the V5 brain is long and noisy. The pairs are short, so this is about keeping each pair together on one layer, not impedance.

| Port | Connector pins (A, B) | Transceiver pins (A, B) | Termination | Test pads |
|---|---|---|---|---|
| A | J1.1 (114.3, 127.0), J1.2 (116.8, 128.3) | U14.6 (130.0, 128.1), U14.7 (130.0, 126.9) | R51 (131.5, 132.4) | TP8 (A), TP9 (B) |
| B | J2.1 (114.3, 139.8), J2.2 (116.8, 141.1) | U15.6 (130.0, 139.4), U15.7 (130.0, 138.2) | R52 (131.1, 134.7) | TP11 (A), TP12 (B) |

Today port A's B wire has 17.8 mm on the bottom; on port B both wires use the bottom (10.6 and 13.3 mm).

For each port:
1. Delete both A and B tracks (select a segment, `U`, `Delete`).
2. Route A and B together on F.Cu with `X`, one right beside the other (0.25 mm track, 0.2–0.3 mm gap). They aren't recognised as a KiCad pair, so route A first, then B hugging it.
3. **Order along the pair:** connector, then transceiver pins, then the termination resistor and test pads as short branches at the end.
4. The A and B pads on the jack are 1.3 mm apart vertically, so the pair will fan in. Keep that fan-in short.

**Check.** Net Inspector shows 0 mm on B.Cu for all four RS485_A/RS485_B nets.

## 4. CAN pair to ramBar (20 min)

**Why.** Same reason as RS-485: CAN is differential and goes off-board.

The pair runs from J19 pins 5 (CAN_H, (184.6, 152.1)) and 6 (CAN_L, (183.4, 152.1)), through the TVS D12 (178.4, 152.7), to the transceiver U16 pins 7 (CANH) and 6 (CANL) around (183.9, 147.5), and on to the termination R53 (187.3, 144.4). Today CAN_L has 9.9 mm on the bottom and three vias, and the pair separates by up to 4.4 mm.

1. Delete both nets' tracks.
2. Route J19, then D12 (the clamp first), then U16, then R53, side by side on F.Cu. D12 is just west of J19; going there first is the right order for ESD anyway.
3. **Check.** Both nets on F.Cu only, side by side.

## 5. Clear the bottom layer (4–6 h, the big one)

**Why.** Every signal's current returns through ground, and at anything above audio frequency it returns directly underneath the trace. A bottom-layer trace slices the plane. Any top-layer signal that crosses the slot has to send its return current the long way around it. That makes a loop antenna (EMI) and lets signals couple into each other (crosstalk). This is the single biggest improvement left on the board.

**How to work.**
1. Hide F.Cu and fill zones (`B`). You'll see the bottom GND as a sheet with cuts in it. Each cut is a B.Cu track.
2. Take the nets below in order. For each one:
   - Highlight it (backtick) to see where it goes.
   - Select its B.Cu segments (click, then `U`) and delete them.
   - Reroute the gap on F.Cu. If you must cross a top trace, drop to B.Cu for the shortest possible straight hop at right angles, then come straight back up.
3. After each net, press `B` and look at the bottom again: the sheet should have fewer cuts.
4. Re-run DRC every few nets (step 9) so mistakes don't pile up.

**First, the supply rails.** These are the longest bottom runs, and they're wide (0.3–0.5 mm), so they make the widest cuts. Rails are allowed to stay on the bottom only where they run **along the board edge**.

| Net | B.Cu now (mm) | What it feeds | Suggested route |
|---|---|---|---|
| SENS_3V3 | 131 | pin 1 of every supply shunt (JP1–JP10), the IMU and the SPI jack | With SENS_5V: two straight rails running the length of the jack row, with short taps to each header (pin 1 = 3V3, pin 3 = 5V). Put one rail on F.Cu. If the other has to be on B.Cu, run it hard against the top edge, under the jacks, so it's an edge rail. Either way, nothing should zig-zag through the middle of the board |
| +3.3V | 121 | the MCU, mux, transceivers, LEDs | Mostly on F.Cu around U3. The LDO U7 output (163.0, 157.0) can come up the gap between U3 and U16 |
| SENS_5V | 114 | pin 3 of every supply shunt | See SENS_3V3 |
| /Power/5V_LDO | 67 | D9 to the LDO | F.Cu, D9 (155.0, 158.5) straight to U7 |
| /Power/VBUS_USB | 60 | USB-C VBUS to Q1/D10 | Along the left edge on B.Cu is acceptable; take it off the middle |
| +5V | 48 | from the buck to F3, D9, ramBar | F.Cu, wide (0.8 mm) |

**Then the signals, longest first.** Move each to F.Cu, using a short B.Cu hop only where it must cross something.

| Net | B.Cu now (mm) | Runs between (approx. box) |
|---|---|---|
| I2C_AUX_SDA | 90 | J18 → U12 → MCU: (163, 115)–(199, 136) |
| USB_D+ / USB_D- | 83 / 59 | (done in step 2) |
| RS485B_RX | 79 | U15 → MCU: (126, 136)–(175, 162) |
| TOF3_SCL | 66 | U10 → mux: (136, 103)–(166, 125) |
| VBUS_SENSE | 62 | (119, 123)–(160, 142) |
| TOF4_SDA | 59 | U11 → mux: (144, 104)–(185, 123) |
| MUX7_SDA | 58 | U11 → mux: (146, 107)–(187, 122) |
| IMU_MOSI | 56 | MCU → U5/R9: (141, 124)–(185, 144) |
| RS485A_RX, RS485B_DE | 50 each | U14/U15 → MCU |
| RAMBAR_RX, RAMBAR_TX | 49 / 47 | MCU → U17/J19 |
| IMU_MISO, MUX_RST, RS485A_TX | 42–43 | |
| SPARE_CS, JETSON_TX, TOF3_SDA, TOF4_SCL, JETSON_RX, IMU_INT2, RS485A_DE, SPARE_INT, PGOOD, MUX7_SCL, POT_SIG, TOF2_SCL, I2C_AUX_SCL, ENC1_SCL, VIN_MOD, TOF1_SDA | 30–40 | |
| everything else on the list | 8–30 | |

For the full list with lengths, use Inspect → Net Inspector and sort by B.Cu length.

**Tips for the crowded middle.**
- Signals from the mux (U6) and transceivers go to MCU pins on the **left** and **top** sides of U3; signals for the right-hand connectors go to the **right** and **bottom** sides. Most crossings come from a net leaving the MCU on the wrong side. If a net looks impossible, check the pin map in [README.md](README.md#mcu-pin-map). Swapping which free pin a function uses is a schematic change, so ask before doing that.
- Route buses (I2C, SPI) as neat parallel groups, not one wire at a time.
- When two top traces must cross, make the bottom hop short (≤ 5 mm), straight, at 90° to the trace above, and put a GND via next to each end of the hop.

**Check.**
- Net Inspector: total B.Cu length for all non-GND nets is under 600 mm.
- With F.Cu hidden, the bottom pour is one sheet with only short cuts.

## 6. GND vias the script couldn't fit (30 min)

After step 5 there will be room for these. Each pad below has no GND via within 1.5 mm, so its ground current has to travel through the top pour first. For each pad, start a track from the pad with `X`, go about 1 mm, press `V` to drop a via, and finish. The via takes the pad's net (GND).

- **Decoupling caps:** C9, C12, C14, C15, C17, C18, C19, C20, C21, C25, C27, C28, C29, C30, C8, C6 (pad 2 = GND on each)
- **ESD clamp GND pins:**
  - U5 pins 3 and 8
  - U8, U10, U11 pins 3 and 8
  - U9 pin 3
  - U13 pin 2
  - U17 pins 3 and 8
  - D4 pin 2
- **Chips:**
  - U3 pins 27 and 63 (MCU VSS)
  - U6 pins 12 and 21
  - U14 and U15 pins 2 and 5
  - U16 pins 2, 5 and 8
- **Smaller:** J5.2, J15.2 and their MP pads, J10.4, R35, R40, R47, R48, R31, R37 (pad 2), D6–D8 pin 1, SW1 pin 2

**Check.** DRC still clean after `B`.

## 7. Crystal neighbourhood (20 min)

Y1 (149.4, 136.0), with C22 above it and C23 below. The OSC traces are short and on top; good. Three MCU escape traces run on B.Cu just right of the crystal keep-out, around x 151.8–153.6: **VBAT_SENSE, POT_SIG and PGOOD** (U3 pins 8, 9 and 11, right below the OSC pins 5 and 6).
- Re-route these escapes so they leave the pins on F.Cu, heading down and left away from Y1, and change layer (if at all) below y ≈ 140.
- **Why:** ST's crystal guide (AN2867) asks for nothing but ground near the crystal and its caps, so digital edges don't couple into the oscillator.

**Check.** With F.Cu hidden, nothing but GND between x 146 and 154, y 131 and 141.

## 8. Silkscreen leftovers (15 min)

The script printed connector names beside nearly every connector. Two had no room:
- **J14 (AUX1)** at (200.0, 116.7)
- **J18 (I2C bus 2)** at (200.0, 127.5)

Their pads face the shunt headers, and the screw-head keep-out is above them. After step 5, look for a 1.5 mm gap nearby and add text (Place → Text, layer F.Silkscreen, height 0.8 mm, thickness 0.15 mm):
- `J14 AUX1` and `J18 I2C`;
- or, if nothing fits, put `J14 AUX1  J18 I2C  J17 POT` on **B.Silkscreen** behind the connectors.

Check while you're there:
- "J2 PORT B" sits just between the two smart ports, so confirm it reads as J2's.
- Silkscreen text must be at least 0.8 mm tall and 0.15 mm thick (PCBWay).

## 9. Final checks

1. Press `B` (refill all zones).
2. Inspect → Design Rules Checker: tick **Test for parity between PCB and schematic**, and run. Required: **0 violations, 0 unconnected items, 0 footprint errors**. Don't ignore an "unconnected" result: after hand edits it usually means a stub you deleted wasn't re-routed.
3. Check the targets table at the top with Net Inspector.
4. Ask Claude Code to "run pcb-layout-auditor on centurion". The audit agent in `../.claude/agents/` re-measures everything in this guide (and more) against [PCB_DESIGN_GUIDELINES.md](../PCB_DESIGN_GUIDELINES.md).
5. View → 3D Viewer: check every label is readable and nothing prints under a part.
6. Then follow "Before ordering" in [README.md](README.md).
