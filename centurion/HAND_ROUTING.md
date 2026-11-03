# Centurion rev A: hand-routing guide

The board in `centurion.kicad_pcb` was placed by script and routed by Freerouting. The router was set to make bottom-layer (B.Cu) track cost 4–6 times as much as top-layer track, so it keeps the bottom for the ground plane wherever it can. It is **not order-ready yet**:
- It is 2 connections short.
- An autorouter doesn't know which loops matter electrically, so pairs, ESD order and the remaining bottom-layer signals need a person.

This guide is the hand work that's left, in priority order. Each step says what is wrong, why it matters, exactly what to do in KiCad, and how to check it's done. To have Claude Desktop do these steps by driving KiCad, see [CLAUDE_DESKTOP_ROUTING.md](CLAUDE_DESKTOP_ROUTING.md).

All coordinates are KiCad's absolute coordinates: what the status bar shows at the bottom of the PCB editor. The board runs from (100.0, 100.0) at the top-left corner to (203.2, 162.6) at the bottom-right. The easiest way to find a part is **Ctrl+F**, then type its reference (for example `U9`).

## Contents

0. [Set up](#0-set-up-once)
1. [The two open connections](#1-the-two-open-connections-15-min)
2. [ESD clamps in the signal path](#2-esd-clamps-in-the-signal-path-45-min)
3. [USB data pair](#3-usb-data-pair-1-h)
4. [RS-485 pairs to the smart ports](#4-rs-485-pairs-to-the-smart-ports-45-min)
5. [CAN pair to ramBar](#5-can-pair-to-rambar-20-min)
6. [Clear the bottom layer](#6-clear-the-bottom-layer-3-5-h-the-big-one)
7. [GND vias next to ground pads](#7-gnd-vias-next-to-ground-pads-30-min)
8. [Crystal neighbourhood](#8-crystal-neighbourhood-10-min)
9. [Silkscreen leftovers](#9-silkscreen-leftovers-15-min)
10. [Final checks](#10-final-checks)

Where we are now and the targets for "done":

| Measure | Now | Done when |
|---|---|---|
| DRC with schematic parity | 2 unconnected; 2 dangling-via warnings | 0 violations, 0 unconnected, 0 parity |
| Signal and power copper on B.Cu (not GND) | 1583 mm (it was 2577 before the bottom-layer bias) | under 600 mm, and no B.Cu run longer than 15 mm except along the board edge |
| Bottom GND pour | one main sheet of 3616 mm², plus 4 specks under 6 mm² | stays one sheet |
| USB pair | D+ has 49 mm on B.Cu; D- is unrouted | both on F.Cu, side by side the whole way (gap ≤ 0.3 mm) |
| RS-485 and CAN pairs | port A's B wire 6 mm on B.Cu; CAN 3.5 / 9.7 mm on B.Cu; port B pair up to 4.8 mm apart | both wires of each pair on F.Cu, side by side |
| Sensor-jack ESD | 16–45 mm from jack to clamp; **ENC2_SDA reaches the mux before its clamp** | every line goes jack, then clamp, then mux; under 15 mm to the clamp |

Already fixed by the script (don't undo these):
- **Buck stage (U1).** Input caps C2, C32 and C3 sit in a row right above the VIN pins. Output caps C4 and C5 sit under the VOUT pins, and the feedback divider R29/R30 sits at the FB pin; the FB node is 3.9 mm. A keep-out stops any bottom-layer track under the whole buck area.
- **Crystal.** Y1 and its load caps C22 and C23 are tight against the MCU, and the OSC traces are 7.7 and 5.8 mm. A keep-out stops bottom tracks under them.
- **Screw heads.** Tracks and vias are kept 4.5 mm from each mounting-hole centre, so the #8 screw heads can't short anything.
- **Vias.** Every power-net layer change has 3 vias. There are GND vias at 54 ground pads and a GND via fence along the board edge.

## 0. Set up (once)

1. **Make a restore point.** Commit the current board to git before each session, and again after each step that passes its check.
2. **Edit this board file from now on.** The layout script that generated it lives outside the repo; regenerating would throw your hand work away.
3. Open `centurion.kicad_pro` in KiCad 10 and open the PCB editor.
4. **Router mode.** Route → Interactive Router Settings:
   - Mode: **Shove**.
   - Tick **Remove redundant tracks**.
   - Tick **Optimize pad connections**.
   - Shove pushes neighbouring tracks out of the way instead of refusing.
5. **Differential pair class for USB.** Board Setup → Design Rules → Net Classes:
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
- **Keep GND vias next to every layer change of a signal**, so its return current can change layers too. Where a signal changes layer, put a GND via within about 2 mm of the signal via.
- **Press B and check the bottom pour after each change.** It is one sheet now; keep it that way.

## 1. The two open connections (15 min)

Run Inspect → Design Rules Checker (with **Test for parity** ticked). It lists:
- **MUX7_SCL**: U11 pad 2 (182.9, 115.7) to the end of its trace at (187.6, 112.2), near jack J13. Route it on F.Cu with `X`. It's also an ESD line (jack J13 → clamp U11 → mux), so check in step 2 that it goes J13, then U11, then on.
- **USB_D-**: the whole run from R39 to the MCU pin U3.45. Leave this for step 3, which reroutes the whole USB pair.
- **Two dangling vias** (warnings): one on USB_D- at (114.2, 122.3), which step 3 removes, and one on RS485A_TX at (126.5, 129.4). Click each in the DRC list to zoom to it, select it and press Delete, unless it connects a track on both layers.

## 2. ESD clamps in the signal path (45 min)

**Why.** An ESD clamp only protects what's behind it. A zap enters at the connector and takes the first path it finds. If the trace reaches the mux or MCU before the clamp, the chip takes the hit.

**The real defect: ENC2_SDA (jack J7).** Its trace runs J7 pin 3, then U6 pin 6 (the mux), and only then the clamp U8 pin 5, 45 mm in all.
1. Ctrl+F → `J7` (the ENC2 jack at (125.1, 103.2)). Click the trace leaving its pin 3 (hover a pad to see its number and net). Press `U` until the whole /Sensors/ENC2_SDA trace is selected, then press `Delete`. The ratsnest (thin lines) now shows what's unconnected.
2. Press `X`, start on J7 pin 3, and route on F.Cu to **U8 pin 5** at about (119.8, 115.3).
3. From U8 pin 5, continue to **U6 pin 6** (U6 is the mux at (142.0, 122.0)).
4. Reconnect the pullup R16 to the trace anywhere between J7 and U8.
5. **Check.** Highlight the net with the backtick key. Following the copper from J7, you must reach U8 before U6.

**The other jack lines (J6–J13, pins 2 and 3).** They reach their clamp first, but by detours of up to 37 mm where 11–12 mm is possible. For each one over about 15 mm (listed below), delete it and reroute it jack, then clamp, then mux, on top. The clamps for each pair of jacks are:
- U8 at (119.8, 115.3) for J6/J7
- U9 at (141.0, 115.3) for J8/J9
- U10 at (162.2, 115.3) for J10/J11
- U11 at (183.4, 115.3) for J12/J13

Longest first:

| Line | Now (mm) | Clamp pin |
|---|---|---|
| J12.3 TOF4_SDA | 36.7 | U11.4 |
| J10.3 TOF2_SDA | 27.4 | U10.4 |
| J6.3 ENC1_SDA | 26.6 | U8.4 |
| J13.3 MUX7_SDA | 24.6 | U11.5 |
| J8.3 LASER_SDA | 24.0 | U9.4 |
| J9.3 TOF1_SDA | 22.5 | U9.5 |
| J11.3 TOF3_SDA | 22.3 | U10.5 |
| J10.2 TOF2_SCL | 21.3 | U10.1 |
| J9.2 TOF1_SCL | 20.0 | U9.2 |
| J11.2 TOF3_SCL | 18.6 | U10.2 |
| J7.2 ENC2_SCL | 18.2 | U8.2 |
| J6.2 ENC1_SCL | 16.7 | U8.1 |
| J12.2 TOF4_SCL | 16.6 | U11.1 |
| J8.2 LASER_SCL | 16.0 | U9.1 |

The pullups (R13–R28, R42, R43) can branch off anywhere between the jack and the clamp; that's fine.

**IMU connector J5.** IMU_MOSI_H runs J5 pin 4, then R9, then the clamp U5 pin 2. Reroute it as J5.4, then U5.2 (at (184.2, 136.5)), then R9.

## 3. USB data pair (1 h)

**Why.** USB is a differential signal: the two wires carry equal and opposite currents, and the receiver only looks at the difference. That only works if the wires stay together. Today D- isn't routed at all, and D+ has 49 mm on the bottom layer. At full speed (12 Mbit/s) we don't need exact 90 Ω impedance, which a 2-layer, 1.6 mm board can't reach anyway. We do need the two traces side by side over unbroken ground.

The pair runs from the USB-C connector J16 (103.1, 116.5), through the ESD part U13 (112.0, 117.0) and the 22 Ω series resistors R38 and R39, to MCU pins **U3.46 (D+)** and **U3.45 (D-)**. Those pins are on the **right** side of U3, at (164.7, 134.2) and (164.7, 134.8). The connector-side half (J16 → U13 → R38/R39) is already short and tight, so leave it.

1. **Line up the resistors.** R38 sits at (110.3, 120.5) and R39 at (114.1, 120.4), so the pair starts 5.6 mm apart.
   - Select R39 and press `M` to move it. Put it right beside R38 at about (112.0, 120.5), pads parallel to R38's.
   - Reconnect the two short traces from U13.
2. **Delete the long half.**
   - Click a USB_D+ track and press `U` until it's all selected, then `Delete`.
   - Delete the stub and dangling via on USB_D- too.
3. **Pick the corridor.** Hide B.Cu and look for a top-layer path from R38/R39 to the right side of U3. U3's pins 45/46 face right, so the pair has to come around U3 into the gap between U3 and the LEDs D6–D8.
   - Suggested path: east along y ≈ 119–120 (under the sensor jack ESD row), until about x 167, then south to y ≈ 134 and in to the pins from the right.
   - Shove mode will move other traces out of the way.
4. **Route it.**
   - Press `6`, click R38's MCU-side pad, and route to U3.46/45.
   - Keep corners at 45°.
   - If the pair has to change layer, do it once, with both vias side by side and a GND via right beside them.
5. **Check.**
   - USB_D+ and USB_D- are on F.Cu end to end, side by side, with lengths within about 2 mm of each other.
   - DRC: no unconnected items left.

## 4. RS-485 pairs to the smart ports (45 min)

**Why.** RS-485 is differential like USB, and the cable to the V5 brain is long and noisy. The pairs are short, so this is about keeping each pair together on one layer, not impedance.

| Port | Connector pins (A, B) | Transceiver pins (A, B) | Termination | Test pads |
|---|---|---|---|---|
| A | J1.1 (114.3, 127.0), J1.2 (116.8, 128.3) | U14.6 (130.0, 128.1), U14.7 (130.0, 126.9) | R51 (131.5, 132.4) | TP8 (A), TP9 (B) |
| B | J2.1 (114.3, 139.8), J2.2 (116.8, 141.1) | U15.6 (130.0, 139.4), U15.7 (130.0, 138.2) | R52 (131.1, 134.7) | TP11 (A), TP12 (B) |

Today port A's B wire has 6 mm on the bottom and 3 vias. Port B is all on top, but its two wires wander up to 4.8 mm apart.

For each port:
1. Delete both A and B tracks (select a segment, `U`, `Delete`).
2. Route A and B together on F.Cu with `X`, one right beside the other (0.25 mm track, 0.2–0.3 mm gap). They aren't recognised as a KiCad pair, so route A first, then B hugging it.
3. **Order along the pair:** connector, then transceiver pins, then the termination resistor and test pads as short branches at the end.

**Check.** Net Inspector shows 0 mm on B.Cu for all four RS485_A/RS485_B nets.

## 5. CAN pair to ramBar (20 min)

**Why.** Same reason as RS-485: CAN is differential and goes off-board. CAN_L also has an ESD order problem: it reaches the transceiver before its TVS diode.

The pair runs from J19 pins 5 (CAN_H, (184.6, 152.1)) and 6 (CAN_L, (183.4, 152.1)), through the TVS D12 (178.4, 152.7), to the transceiver U16 pins 7 (CANH) and 6 (CANL) around (183.9, 147.5), and on to the termination R53 (187.3, 144.4).

1. Delete both nets' tracks.
2. Route J19, then D12 (the clamp first), then U16, then R53, side by side on F.Cu.
3. **Check.** Both nets on F.Cu only, side by side. From J19, D12 comes before U16 on both.

## 6. Clear the bottom layer (3–5 h, the big one)

**Why.** Every signal's current returns through ground, and at anything above audio frequency it returns directly underneath the trace. A bottom-layer trace slices the plane. Any top-layer signal that crosses the slot has to send its return current the long way around it. That makes a loop antenna (EMI) and lets signals couple into each other (crosstalk). The bias already halved this; the rest needs a person.

**How to work.**
1. Hide F.Cu and fill zones (`B`). You'll see the bottom GND as a sheet with slots in it. Each slot is a B.Cu track.
2. Take the nets below in order. For each one:
   - Highlight it (backtick) to see where it goes.
   - Select its B.Cu segments (click, then `U`) and delete them.
   - Reroute the gap on F.Cu. If you must cross a top trace, drop to B.Cu for the shortest possible straight hop at right angles, then come straight back up.
3. After each net, press `B` and look at the bottom again: the sheet should have fewer slots.
4. Re-run DRC every few nets so mistakes don't pile up.

**First, the supply rails.** These are wide (0.3–0.5 mm), so they make the widest slots. Rails are allowed to stay on the bottom only where they run **along the board edge**.

| Net | B.Cu now (mm) | What it feeds | Suggested route |
|---|---|---|---|
| SENS_3V3 | 102 | pin 1 of every supply shunt (JP1–JP10), the IMU and the SPI jack | With SENS_5V: two straight rails running the length of the jack row, with short taps to each header (pin 1 = 3V3, pin 3 = 5V). Put one rail on F.Cu. If the other has to be on B.Cu, run it hard against the top edge, under the jacks, so it's an edge rail. Nothing should zig-zag through the middle |
| +3.3V | 80 | the MCU, mux, transceivers, LEDs | Mostly on F.Cu around U3. The LDO U7 output (163.0, 157.0) can come up the gap between U3 and U16 |
| +5V | 43 | from the buck to F3, D9, ramBar | F.Cu, wide (0.8 mm) |
| SENS_5V | 33 | pin 3 of every supply shunt | See SENS_3V3 |

**Then the signals, longest first.** Move each to F.Cu, using a short B.Cu hop only where it must cross something.

| Net | B.Cu now (mm) | Runs between (approx. box) |
|---|---|---|
| SPARE_MOSI | 59 | MCU → J15 (spare SPI): (159, 115)–(197, 137) |
| RS485B_RX | 49 | U15 → MCU: (129, 136)–(165, 161) |
| USB_D+ | 49 | (done in step 3) |
| IMU_INT2 | 47 | J5 → MCU: (155, 114)–(187, 139) |
| I2C_AUX_SDA | 46 | J18 / U12 → MCU: (163, 121)–(196, 136) |
| RS485A_DE | 46 | MCU → U14: (127, 124)–(158, 140) |
| SPARE_INT | 45 | J15 → MCU: (158, 115)–(190, 139) |
| MUX7_SDA | 43 | U11 → mux: (143, 113)–(181, 123) |
| SPARE_MISO | 43 | J15 → MCU: (161, 115)–(194, 141) |
| AUX1_SIG | 39 | U12 → MCU: (144, 138)–(176, 156) |
| MUX_RST | 38 | MCU → mux: (137, 118)–(158, 138) |
| RS485B_DE, TOF4_SCL, IMU_MISO, JETSON_TX, PGOOD, VBUS_SENSE, RAMBAR_TX, SPARE_CS, JETSON_RX | 25–32 | |
| everything else on the list | 8–25 | |

For the full, current list, use Inspect → Net Inspector and sort by B.Cu length. Or ask Claude Code to "measure the board".

**Tips for the crowded middle.**
- The spare SPI and IMU nets (SPARE_*, IMU_*) all run between the MCU's right side and J5/J15. Route them as a neat parallel bus on F.Cu instead of one at a time.
- Signals from the mux (U6) and transceivers go to MCU pins on the **left** and **top** sides of U3; signals for the right-hand connectors go to the **right** and **bottom** sides. If a net looks impossible, check the pin map in [README.md](README.md#mcu-pin-map). Changing which pin a function uses is a schematic change, so ask before doing that.
- When two top traces must cross, make the bottom hop short (≤ 5 mm), straight, at 90° to the trace above, and put a GND via next to each end of the hop.

**Check.**
- Net Inspector: total B.Cu length for all non-GND nets is under 600 mm.
- With F.Cu hidden, the bottom pour is one sheet with only short slots.

## 7. GND vias next to ground pads (30 min)

After step 6 there will be room for these. Each pad below is connected to ground by a track, but has no GND via within 1.5 mm, so its return current takes a longer path to the bottom plane. For each pad: start a track from the pad with `X`, go about 1 mm, press `V` to drop a via, and finish. The via takes the pad's net (GND).

- **Decoupling caps (pad 2):** C6, C8, C9, C10, C11, C12, C13, C14, C15, C17, C18, C19, C20, C21, C24, C28, C29, C31
- **Crystal and its caps:** Y1 pins 2 and 4, C22 and C23 pad 2
- **ESD clamp GND pins:**
  - U5 pins 3 and 8
  - U10 pins 3 and 8
  - U12 pin 8
  - U13 pin 2
- **Chips:**
  - U3 pins 15, 27, 31, 47 and 63 (MCU VSS)
  - U6 pins 2, 12 and 21
  - U14 and U15 pin 5
  - U7 pin 2
- **Connectors and others:**
  - J5.2 and J15.2 and their MP pads
  - J19.4
  - SW1 pin 2
  - D6–D8 pin 1
  - R2, R35, R40 (pad 2)
  - TP5

**Check.** DRC still clean after `B`.

## 8. Crystal neighbourhood (10 min)

Y1 (149.4, 136.0), with C22 above it and C23 below. The OSC traces are short and on top, and only one stray track is left nearby: a short B.Cu piece of **VBAT_SENSE** at y 137.0, x 152.0–154.7, just right of the crystal keep-out. Reroute it on F.Cu, leaving U3 pin 8 downwards and away from Y1.
- **Why:** ST's crystal guide (AN2867) asks for nothing but ground near the crystal and its caps, so digital edges don't couple into the oscillator.

**Check.** With F.Cu hidden, nothing but GND between x 146 and 154, y 131 and 141.

## 9. Silkscreen leftovers (15 min)

The script printed connector names beside nearly every connector. Two had no room:
- **J14 (AUX1)** at (200.0, 116.7)
- **J18 (I2C bus 2)** at (200.0, 127.5)

Their pads face the shunt headers, and the screw-head keep-out is above them. Look for a 1.5 mm gap nearby and add text (Place → Add Text, layer F.Silkscreen, height 0.8 mm, thickness 0.15 mm):
- `J14 AUX1` and `J18 I2C`;
- or, if nothing fits, put `J14 AUX1  J18 I2C  J17 POT` on **B.Silkscreen** behind the connectors.

Check while you're there:
- "J2 PORT B" sits between the two smart ports, so confirm it reads as J2's.
- Silkscreen text must be at least 0.8 mm tall and 0.15 mm thick (PCBWay).

## 10. Final checks

1. Press `B` (refill all zones).
2. Inspect → Design Rules Checker: tick **Test for parity between PCB and schematic**, and run. Required: **0 violations, 0 unconnected items, 0 footprint errors**. Don't ignore an "unconnected" result: after hand edits it usually means a stub you deleted wasn't re-routed.
3. Check the targets table at the top with Net Inspector, or ask Claude Code to "measure the board".
4. Ask Claude Code to "run pcb-layout-auditor on centurion". The audit agent in `../.claude/agents/` re-measures everything in this guide (and more) against [PCB_DESIGN_GUIDELINES.md](../PCB_DESIGN_GUIDELINES.md).
5. View → 3D Viewer: check every label is readable and nothing prints under a part.
6. Then follow "Before ordering" in [README.md](README.md).
