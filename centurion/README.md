# centurion: sensor board, rev A

The main custom board for the UWAT VEXU robots. It sits between the V5 brain and the Jetson. It takes power and RS-485 from two V5 smart ports, reads I2C sensors (encoders, ToF distance sensors, the lift laser) through a mux, reads a turret potentiometer on an ADC pin, and talks to an off-board IMU over SPI. It talks to the Jetson over USB-C, with a UART connector as a backup, and to the ramBar board on the arm over a UART and CAN FD cable.

## Status

The schematic was updated on 2026-11-02 to the decisions below, plus the review fixes of 2026-11-03. The PCB is a fully routed **4-layer** board, 103.2 x 62.6 mm: signals on top and bottom, a solid GND plane on In1 and a +3.3V plane on In2. On 2026-11-04 KiCad 10 shows 0 DRC violations, 0 unconnected items and 0 schematic parity issues, and ERC is clean. The signal, connector, USB hot-plug and crosstalk simulations are in [sim/](sim/README.md). The board still has to go through the [Before ordering](#before-ordering) list (fab DFM check, a 1:1 test-fit, and two part checks with a meter). The old hand-routing guides, [HAND_ROUTING.md](HAND_ROUTING.md) and [CLAUDE_DESKTOP_ROUTING.md](CLAUDE_DESKTOP_ROUTING.md), describe the earlier 2-layer board and are kept only as a record. Non-urgent layout and circuit improvements are deferred to rev B in [REV_B_IMPROVEMENTS.md](REV_B_IMPROVEMENTS.md).

- MCU is now the STM32G491RET6. The ESP32-S3 is gone.
- Each smart port has its own MAX33071E RS-485 transceiver, on its own USART with hardware DE.
- The IMU moved off the board. The ICM-42688-P and the ADXRS453 header are gone, replaced by an SPI header for an IMU breakout.
- Four #8-32 mounting holes (H1 to H4) are in, on the bracket pattern measured from the robot CAD.
- KiCad 10 ERC: 0 errors, 0 warnings (see [How this was checked](#how-this-was-checked)).
- J16's USB-C shield pin is renamed `S1` to `SH` to match KiCad 10's USB4105 footprint. Before this the shield pads had no net, so the USB shell would have floated instead of going to GND.
- The BOM is in [bom/](bom/). On 2026-11-02 four values were changed to parts already on centurion, powerJackal or stellaNova, which removed 4 unique part numbers: R8, R9 and R41 33 Ω to 22 Ω; R40 27k to 22k; R46/R47 22k/33k to 10k/15k (same ratio); LED1/LED2 0805 to the 0603 green LED used for D6. On 2026-11-04, after the design review: R38/R39 (USB D+/D-) 22 Ω to 0 Ω, because the STM32G4's USB pins need no external series resistor; F2 0.35 A to 0.5 A hold, the same part as F3, because 8 or more jacks on 3.3 V would trip 0.35 A. C33 added: a 47 uF 10 V polymer tantalum (KEMET T520B476M010ATE070) on 5V_LDO next to Q1, so plugging in USB can't ring U7's input past its 6.5 V rating (see [sim/](sim/README.md)). Also on 2026-11-04: the ESD clamps U5, U8 to U12 and U17 changed from TPD4E05U06DQAR, which is out of stock at DigiKey CA until February 2027, to TPD4E05U06QDQARQ1, TI's automotive (AEC-Q101) version with the same package, pinout and ratings. The BOM was rebuilt in the powerJackal/stellaNova format, with DigiKey price breaks for every part. Later on 2026-11-04, after the connector simulations: R8, R9 and R41 (IMU SPI) 22 Ω to 100 Ω, the same part as R55, so a 0.3 m IMU cable works at any GPIO speed and 0.5 m at medium or low (see [sim/](sim/README.md#connector-simulations)). That dropped the 22 Ω line from the BOM and adds one 100 Ω resistor to the order (26 instead of 25). The BOM's Cables and tools tab lists what it takes to make the JST GH cables, with its own upload file, [bom/centurion_cables_tools_DigiKey_upload.csv](bom/centurion_cables_tools_DigiKey_upload.csv):
  - GH housings and crimp contacts;
  - JST pre-crimped leads for the ramBar and IMU cables;
  - 28 AWG wire in five colours;
  - an Engineer PA-09 crimper and a 30 AWG stripper.

  It comes to about $500 for three cable sets, with $300 of that being wire. It also has the pin order and wire colour for every jack.

The component plan is [docs/Board_Components.xlsx](docs/Board_Components.xlsx). Where this file and the plan disagree, this file has the later decision.

## Folder map

| Path | What it is |
|---|---|
| `centurion.kicad_pro` | The KiCad project. Open this. It holds the net classes and board rules. |
| `centurion.kicad_pcb` | The board: 4 layers, placed and fully routed. In1 is a solid GND plane, In2 a +3.3V plane, GND poured on top and bottom. |
| `centurion.kicad_dru` | Custom DRC rule (hole clearance, see [PCB layout](#pcb-layout)) |
| `REV_B_IMPROVEMENTS.md` | Non-urgent improvements left out of rev A, from the final layout audit and the simulations |
| `HAND_ROUTING.md` | Record only: the hand-routing to-do list for the earlier 2-layer board. That work was replaced by the 4-layer re-layout. |
| `CLAUDE_DESKTOP_ROUTING.md` | Record only: prompts for having Claude Desktop do that hand routing |
| `sim/` | Signal, connector, USB hot-plug and crosstalk simulations ([sim/README.md](sim/README.md)) |
| `centurion.kicad_sch` | Top sheet. It places the sheets below and wires the RS-485 sheet pins. |
| `power.kicad_sch` | Smart port power input, 5 V buck, 3.3 V LDO, USB-C, battery sense, PGOOD, VBUS sense, test pads |
| `smartport.kicad_sch` | One smart port jack and its MAX33071E. Used twice, as SmartPort_A and SmartPort_B. |
| `mcu.kicad_sch` | STM32G491RET6, decoupling, RESET and BOOT buttons, SWD header, status LEDs, 8 MHz crystal |
| `imu.kicad_sch` | IMU breakout connector (SPI1) and the spare SPI connector (SPI3), both JST-GH |
| `sensors.kicad_sch` | I2C mux and its 8 ports, the pot port, AUX1, the spare I2C header, ESD |
| `usb_jetson.kicad_sch` | Backup 3.3 V UART connector to the Jetson, and the ramBar link (UART, CAN FD transceiver, fused 5 V) |
| `lib/` | Project symbols (now includes MAX33071E), footprints and 3D models. The smart port jack uses the stellaNova footprint with the Molex step model. The TPSM53602 footprint is from powerJackal; KiCad has no model for it, so it gets a plain 5 x 5.5 x 4 mm body. |
| `bom/centurion_revA_BOM.xlsx` | BOM in the same format as powerJackal and stellaNova. It has DigiKey Canada stock and CAD price breaks for every part, read 2026-11-04 (or 2026-10-29/30 for parts shared with those boards). It also has a yellow "boards to build" cell (6), suggested order quantities, a green tip when the next price break is cheaper, and red stock cells. Two columns go past the sibling layout: "On hand" (parts left over from the powerJackal and stellaNova orders, from the "Stock check" sheet) and "Earlier order". Not fitted lines have qty 0; team-stock lines (header strip, shunts) aren't ordered. Tabs: BOM, Price breaks, Stock check, DigiKey upload, Design notes. |
| `bom/centurion_revA_DigiKey_upload.csv` | Upload to DigiKey BOM Manager, with the suggested order quantities. Those are 6 boards plus spares, minus what the powerJackal (2 built) and stellaNova (3 built) orders left over, rounded up to a price break where that costs at most $0.50 more. Lines fully covered by that stock are left out, and so are not-fitted and team-stock lines. To change a quantity, type it in the BOM sheet's yellow "Your order qty" column. Then save the "DigiKey upload" sheet as CSV, deleting its 0-quantity lines first. |
| `docs/Board_Components.xlsx` | Original component plan and open questions |
| `docs/centurion_revA_schematic.pdf` | The schematic as a PDF. Regenerate with `kicad-cli sch export pdf -o docs/centurion_revA_schematic.pdf centurion.kicad_sch` |

The project also uses the UWAT library in `../powerJackal/lib`. Keep the repo folders together.

## Decisions

| Topic | Decision | Notes |
|---|---|---|
| Power | powerJackal's core power section | Already copied and checked pin by pin. PGOOD now goes to the MCU, and the test pads are back. |
| USB power | USB-C alone runs the 3.3 V side. Smart ports alone run everything. Both: the smart ports power the board and USB carries data only. | Automatic, through Q1, D9 and D10 (the powerJackal circuit). The 5 V rail stays off on USB alone. |
| MCU | STM32G491RET6 | Hardware RS-485 DE, newer I2C block, UART FIFOs, CAN FD, USB without a crystal. In stock at DigiKey Canada (558 on 2026-11-02). See [MCU choice](#mcu-choice). |
| RS-485 | One MAX33071EASA+ per smart port, each on its own USART with hardware DE | ±65 V bus fault, ±40 V common mode, ±40 kV HBM ESD, 2 Mbps. Same chip as stellaNova. Replaces last year's plug-in MAX485 modules. |
| Brain link | Two ports, wired the same | Firmware can use port A to read from the brain and port B to write to it, or run both half duplex. No board change either way. |
| Wireless | Allowed, but not on this board | The G491 has no radio. stellaNova on a spare port or the Jetson covers it. |
| Camera | On the Jetson | The STM32 camera option was looked at and dropped: its RAM limits it to about 160 x 120 color or 320 x 240 gray. |
| USB host | Not on this board | The Jetson is the USB host. J15, a spare SPI connector, lets a MAX3421E breakout plug in later. |
| ramBar link | J19, JST-GH 6-pin: 5 V, 3.3 V UART and CAN FD on one cable | ramBar talks to centurion, which passes its data on to the brain. Firmware can use the UART, CAN FD or both. See [ramBar link](#rambar-link-usb_jetson-sheet). |
| IMU | Off-board, on SPI through J5 | The team's own IMU board: a BMI270 with a matching JST GH 8-pin jack, plugged in with a straight cable. See [../imuBoard/README.md](../imuBoard/README.md). The ADXRS453 is dropped. |
| I2C mux | One TCA9548A | 2 encoders, 4 ToF, the lift laser and 1 spare. See [Sensor ports](#sensor-ports). |
| Second I2C bus | AUX1 and the spare I2C header J18 | I2C3 on PC8 and PC9 |
| Turret | Laser on mux channel 2, pot on an ADC pin | The turret turns at most 210°, so no slip ring. A slightly longer cable is fine because the laser has its own mux channel. |
| Sensor connector | JST-GH | Chosen on 2026-11-02 for its latch. Every cable connector is JST-GH: right-angle jacks on the edges, vertical (top entry) inside the board. Qwiic breakouts need a GH-to-Qwiic adapter cable: Qwiic is JST SH (1.0 mm) with pins GND, VCC, SDA, SCL, while these jacks are VCC, SCL, SDA, GND. Cable parts and crimping tools are on the BOM's Cables and tools tab. |
| Reverse polarity | None in v1 | Plan Q7 |
| eFuse | None in v1 | Hot-plug inrush is accepted. Plan Q8. |
| Power budget | Measure it on powerJackal | Plan Q2 |
| Mounting | 4 x #8-32 into the brain mount brackets, 93.92 x 50.80 mm pattern | 4.5 mm non-plated holes. See [Board size and mounting](#board-size-and-mounting). |

### MCU choice

The G491 replaced the planned STM32F446. Both are in stock and cost about the same ($16.59 vs $16.80 CAD at qty 1).

| | STM32G491RET6 | STM32F446RET6 |
|---|---|---|
| RS-485 driver enable in hardware | Yes, on USART2 (PA1) and USART3 (PB14) | No. Firmware toggles a GPIO. |
| UART FIFO | 8 bytes | None |
| I2C | 3, newer block | 4, older block known for lockups |
| SPI | 3 | 4 |
| CAN | 2 x CAN FD | 2 x classic CAN |
| USB | Full speed device, runs from the internal 48 MHz clock | Full speed device and host, needs a crystal |
| Camera interface | No | Yes |
| RAM | 112 KB | 128 KB |
| Speed | 170 MHz | 180 MHz |

Centurion needs 2 I2C buses, 2 SPI, 4 UARTs, 1 CAN FD and about 45 pins, so the G491's 52 I/O pins leave room. The camera goes on the Jetson, so the F446's camera interface isn't needed.

On the 64-pin G491, USART1's only DE pin is PA12, which USB needs. That's why the brain ports use USART2 and USART3, and the Jetson UART uses USART1.

### Board size and mounting

Centurion screws onto the two brain mount brackets (`brainMount-frontSlant-left` and `-right` in the robot CAD) with four #8-32 screws, H1 to H4 on the top sheet. Measured in SolidWorks on 2026-11-02:

| | in | mm |
|---|---|---|
| Hole centres, left to right (between the two brackets) | 3.6976 | 93.92 |
| Hole centres, top to bottom (on one bracket) | 2.000 | 50.80 |
| Bracket hole | 0.175 | 4.45 |
| Board hole, non-plated | 0.177 | 4.50 |

- **Top to bottom is along the bracket's slanted face.** That face is the plane the board sits in, so the board sees exactly 2.000 in. The CAD's X and Y deltas (0.657 in and 1.889 in) are just the slant.
- **Footprint.** `UWAT:MountingHole_4.5mm_8-32` from powerJackal: a 4.5 mm non-plated hole with an 8 mm screw-head keep-out. 4.5 mm is the standard free fit for #8 and slightly larger than the 4.45 mm bracket holes, so small bracket misalignment is fine.
- **Not tied to GND.** The holes have no copper, so the robot frame never connects to the board ground through the screws. Same as powerJackal.
- **Smallest outline.** With the hole centres 4.45 mm from the edges like powerJackal, the board is at least 102.8 x 59.7 mm.

The outline is 103.2 x 62.6 mm, close to the smallest the hole pattern allows. The holes stay on the 93.92 x 50.80 mm pattern.

| | mm | Hole centre to edge |
|---|---|---|
| Width (left to right) | 103.22 | 4.65 left, 4.65 right |
| Height (top to bottom) | 62.6 | 6.15 top, 5.65 bottom |

- **Width.** The hole centres are 4.65 mm from the left and right edges, so the holes' 9.3 mm screw-head keep-outs just fit on the board. The connectors on those edges sit between the holes.
- **Height.** There's 1.5 mm extra at the top and 1 mm at the bottom for routing. The eight top jacks sit between H1 and H2, not above them.
- **History.** On 2026-11-02 the board went from 125 x 69.7 mm, to 113 x 69.7 mm, to 103.2 x 62.6 mm, about 18% less area than the 113 mm version. Moving J18 and J14 to the right edge is what let the top row fit between the holes.
- **No headers on the bottom edge.** Headers and connectors are on the left, right and top edges.

## PCB layout

Four layers, all parts on the top side.

| Layer | Use | Dielectric below it |
|---|---|---|
| F.Cu | Parts and most signals (3.6 m of track), GND pour | 0.1 mm prepreg |
| In1.Cu | Solid GND plane, no tracks | 1.24 mm core |
| In2.Cu | +3.3V plane. 22 slow signals and the USB pair also run here (0.3 m), cutting slots in it. | 0.1 mm prepreg |
| B.Cu | Signals (1.35 m), GND pour, small power fills | |

Every top-layer signal sits 0.1 mm over the solid GND plane, so its return current has an unbroken path. Bottom-layer signals reference the +3.3V plane, which is tied to GND through the decoupling caps. The USB pair is on In2 because J16 is on the left edge while the MCU's USB pins (PA11/PA12) are on its right side, about 60 mm away, and moving it to the top layer didn't fit. That's accepted for rev A at full speed; for rev B, move J16, U13, R38 and R39 next to the MCU (see [sim/README.md](sim/README.md)). Ask the fab for this stackup (1.6 mm, 1 oz outer copper), or their closest standard 4-layer stackup.

| Edge | What's there |
|---|---|
| Top | The 8 mux channels, J6 to J13 (ch0 to ch7), on a 10.6 mm pitch between H1 and H2. Every jack has the same cell behind it: its supply shunt header, then its two pullups. The ESD parts sit between jack pairs. |
| Left | J16 (USB-C) at the top, then the J1 and J2 smart ports, all between H1 and H3 with openings at the edge (same offset as powerJackal; the USB-C shell sticks out 0.575 mm, as GCT's footprint intends). U13 (USB ESD) next to J16, U14 and U15 just inside the smart port jacks. |
| Right | Between H2 and H4, top to bottom: J14 (AUX1), J18 (spare I2C), J17 (pot), all bus 2 / U12. JP1 and JP10 (their supply shunts) stand just inside J14 and J18. J5 (IMU) and J15 (spare SPI) are vertical JST-GH just inside those, with U5 below them. |
| Bottom right | Vertical JST-GH inside the board: J4 (Jetson backup UART) and J19 (ramBar), with the ramBar parts (U16, U17, F4, R53, R54) next to J19. |
| Bottom | No connectors on the edge. The power chain sits in the bottom left, next to the smart ports: the USB power path (D10, Q1), OR diodes, F1, TVS, C1, the buck (U1), then the 3.3 V LDO (U7) under the MCU. |

The board runs left to right from inputs and power, through the MCU, to headers and sensor parts. The MCU sits in the middle with a 3 mm fanout keep-out. Its decoupling caps are just outside the package corners, each with its 3.3 V pad facing its VDD pin. The TCA9548A is above it, under the sensor ports. J3 (SWD, debugging only) is right next to it, then the RESET and BOOT buttons and the status LEDs. The USB pair runs from J16 on the left to PA11/PA12 on the MCU's right side, which is fine at full speed.

**Power stage and crystal.** The buck's input caps (C2, C32, C3) sit in a row right above U1's VIN pins. Its output caps (C4, C5) sit under the VOUT pins, and the feedback divider (R29, R30) sits at the FB pin, which keeps the FB node 3.9 mm long. The crystal Y1 sits next to the MCU's OSC pins, with C22 and C23 right at its pads (OSC traces 7.6 and 5.7 mm).

**Silkscreen.** Connectors and buttons print their name in one label with the reference, right beside the part (`J5 IMU`, `SW1 RESET`, `J19 RAMBAR`...), never under a part body or a screw head. J14 (AUX1) and J18 (spare I2C) had no room on top, so their labels are on the bottom silkscreen, behind the jacks. Every supply shunt header has 3V3 and 5V printed at its two end pins. All text is 0.8 mm tall with a 0.15 mm stroke, and may cross vias because the vias are tented. The test pads are 1.5 mm round pads.

**Net classes and rules** (Board Setup, from `centurion.kicad_pro`):

| Class | Nets | Track |
|---|---|---|
| Power | VIN_OR, VIN_MOD, VPORT A and B, +5V | 0.8 mm |
| USB_Power | VBUS_USB, USB_PWR, 5V_LDO, RAMBAR_5V | 0.5 mm |
| 3V3 | +3.3V, SENS_3V3, SENS_5V, every sensor jack VCC | 0.3 mm. The widest that still enters a 0.5 mm pitch MCU pin with 0.2 mm clearance. |
| Default | Everything else | 0.25 mm |

- Clearance 0.2 mm everywhere. Copper to edge 0.5 mm. Vias 0.6 mm with a 0.3 mm drill.
- Minimum track 0.127 mm (5 mil), only for short neck-downs into fine-pitch pads. After routing, every narrowed power segment is widened back to its class width wherever clearance allows. The narrowest power sections left are short necks at pads: VIN_MOD 0.45 mm and VBUS_USB 0.375 mm.
- Hole clearance is 0.25 mm through `centurion.kicad_dru`. The board-level floor is 0.15 mm only because KiCad's stock GCT USB4105 footprint (J16) puts its outer GND pads 0.19 mm from its own plastic locating holes.

**Copper.** Every net, GND included, is routed as tracks. On top of that, In1 is solid GND, In2 is +3.3V, and GND is poured on the top and bottom layers. The board has 663 vias.
- **Stitching vias:** about every 4 mm, a fence along the board edge, and extra vias wherever the plane had none within 3 mm.
- **Ground-pad vias:** top-side GND pads (decoupling caps, ESD clamps, IC ground pins) have their own via down to the In1 plane.
- **Corners:** every track corner of 90° or sharper was chamfered into two 45° bends on 2026-11-04. The only two left, on U3 pin 32 and D4 pin 2, are inside their own pads.
- **Power-net vias:** every power-net layer change has three vias.
- **Buck module:** short copper fills widen the VIN and 5 V paths right at its pins.
- **Keep-outs:**
  - No bottom-layer tracks under the whole buck stage, or under the crystal and its caps (the pour still fills there).
  - No bottom vias under U1, so its thermal vias land in solid GND (TI).
  - No tracks or vias within 4.5 mm of a mounting-hole centre, where the #8 screw heads sit.

**How it was made.** The board was placed and routed by a script using KiCad 10's Python and Freerouting 2.5. Freerouting was given per-layer costs (`router.layers` in its settings file) that make bottom-layer track 4–6 times as expensive as top-layer track. That cut signal copper on the bottom from 2.6 m to 1.6 m, and the bottom GND pour went from 11 pieces to one sheet. That's why every footprint is linked to its schematic symbol and Update PCB from Schematic finds nothing to change. From here on the `.kicad_pcb` file is the master. The board was then moved to 4 layers and re-routed, which replaced the hand-routing list in [HAND_ROUTING.md](HAND_ROUTING.md). After that, a script chamfered the right-angle corners and removed spurs, tiny jogs and zero-length segments, with a clearance check on every new piece of copper, and the zones were refilled.

### Layout audit, 4-layer board (2026-11-04)

The layout auditor (`../.claude/agents/pcb-layout-auditor.md`) was rerun on the final 4-layer board. It found **no errors**: nothing that risks a respin. It passed the power paths, the buck and LDO, the crystal, ESD order (all 31 protected nets go through their clamp before the IC), pours, DFM and silkscreen labels. These warnings are left, all optional for rev A. Rev A ships without them; they, the notes below and the simulation follow-ups are collected in [REV_B_IMPROVEMENTS.md](REV_B_IMPROVEMENTS.md).

| # | Warning | Measured | Fix (optional) |
|---|---|---|---|
| 1 | RS-485 pairs not routed side by side | Port A: A 24.7 mm, B 28.0 mm (6.1 mm on B.Cu). Port B: 28.2 / 31.1 mm. Median spacing 1.8 and 2.9 mm. | Re-route each pair together on F.Cu. At these bit rates and lengths, with In1 GND 0.1 mm under F.Cu, the board works as is. |
| 2 | CAN pair not routed side by side | CAN_H 23.4 mm, CAN_L 33.7 mm (10.3 mm longer, 18.8 mm on B.Cu). 40% coupled. Order J19, D12, U16 is right. | Re-route CAN_L next to CAN_H on F.Cu. |
| 3 | Holes in the In2 +3.3V plane | The non-USB signals on In2 (about 189 mm) cut off four areas that island removal deletes: 137, 47, 36 and 22 mm², around (157–176, 115–138) and (175–193, 128–140). About 120 mm of B.Cu track runs under them. | Move the non-USB In2 tracks to F.Cu or B.Cu. All 32 +3.3V vias still reach the plane. |
| 4 | USB pair on In2 | 92% coupled at 0.35 mm, 2.3 mm mismatch: fine for full speed. Crossed 19 times by B.Cu tracks. The connector-side part (USB_DP/DN) is 11% coupled. | Rev B: move J16, U13, R38, R39 next to the MCU. |
| 5 | 38 GND pads without a via within 1.5 mm | Worst: U3.15 4.2 mm, U3.27 2.9 mm, U3.47 2.3 mm; ESD clamps U8 to U11 pin 3 at 2.3–2.8 mm; U6.21, U6.12; C29, C31, C11 to C14. | Add a GND via at each pin. |
| 6 | Decoupling a bit far | C15 is 5.5 mm from U6.24 (VCC). C30 is 9.9 mm from U13.5. U3's VDD caps are 2.3–2.7 mm from their pins (guideline 2 mm). | Move C15 and C30 closer. |
| 7 | Silkscreen line width | 635 footprint silk lines are 0.12 mm. PCBWay and JLCPCB list 0.15 mm as their minimum, so the thinnest lines may print faint or broken. Text is 0.8 mm / 0.15 mm: fine for PCBWay, under JLCPCB's 1.0 mm. | Cosmetic only. |
| 8 | Jack-to-clamp distance | 8 of the 16 jack lines are 17.3–17.4 mm from jack to clamp (target under 15 mm). J5 lines are 13.5–19.4 mm, J14 19.7–22.1 mm. | None needed: the order is right. |

Notes from the same audit:
- **Cleanup:** 5 exact duplicate track segments, plus a few more that fully overlap (I2C_AUX_SDA at about (167, 122), GND, +5V, +3.3V). They're harmless: the same copper twice. 21 of the 204 small filler zones fill nothing.
- **Edge stitching:** the bottom edge has two gaps, 18 mm (x 137.7–155.7) and 27 mm (x 157.7–184.7). The other edges are at most 9.7 mm.
- **Vias** are 0.6 / 0.3 mm, a 0.15 mm ring: the minimum at both fabs (JLCPCB recommends 0.20 mm).
- **Board text** says "UWAT VEXU - F26 - REV 1.1", while the files call this rev A.

### Before ordering

1. Generate the fab files (see [Ordering](#ordering)) and upload them to the fab's DFM viewer. Check that the 4 copper layers are in order (Top, In1 GND, In2 +3.3V, Bottom), that the outline is 103.2 x 62.6 mm, and the solder mask between the LQFP-64 and B3QFN pins.
2. Print the board 1:1 and test-fit a real Molex 0955012441 smart port jack and the JST GH connectors. With the team's cable, looking into the jack opening with the latch tab down, the black wire (A) should be on the leftmost contact (pin 1). The footprint matches Molex's 3D model and the 95501 footprint download, but the numbering wasn't checked against Molex's drawing.
3. Check one TL3342 button with a meter: the footprint pairs its pads left/right. If the internal pairing is the other way, NRST is shorted to GND.
4. Ask the fab to plug or fill the vias in U1's thermal pad (TI's recommendation), so solder doesn't wick down them.
5. Recheck stock for the four BOM lines that were out at DigiKey CA on 2026-11-04 (listed under [Fix list](#fix-list)).
6. Optional: fix the "REV 1.1" board text (the files call this rev A). Everything else from the audit waits for rev B ([REV_B_IMPROVEMENTS.md](REV_B_IMPROVEMENTS.md)).

79 reference designators are on F.Fab only, not printed: all the passives in the crowded middle, the jacks (which print their own `J5 IMU`-style labels), U1, U5, U15, U17 and Y1. The assembly drawing (F.Fab) has them all.

## Ordering

The team will most likely use PCBWay, unless JLCPCB is cheaper or faster to Canada. Get both online quotes: the board is 103.2 mm wide, just over both fabs' 100 x 100 mm promo size, so neither $2/$5 offer applies. The width is set by the bracket holes (93.92 mm apart), so it can't shrink to 100 mm.

| Rule | PCBWay | JLCPCB | This board |
|---|---|---|---|
| Track / space | 0.1 / 0.1 mm | 0.1 / 0.1 mm | 0.127 mm necks, 0.2 mm space |
| Via drill / pad | 0.15 mm min | 0.15 / 0.25 mm min | 0.3 / 0.6 mm |
| Silkscreen text | 0.8 mm tall, 0.15 mm stroke | 1.0 mm tall (0.8 mm only on the high-precision option) | 0.8 mm, 0.15 mm stroke: fine for PCBWay |
| Copper to edge | 0.25 mm | 0.2 mm milled | 0.5 mm |
| Solder mask dam | 0.1 mm (green) | 0.1 mm (green) | Check the LQFP-64 and the B3QFN in the fab's DFM viewer |

- DHL bills duties and HST to the receiver unless the order is DDP. Canadian reports put the DHL clearance fee at about $20 on top of shipping. Check whether DDP is offered at checkout.
- For assembly, both fabs add rails and fiducials if they're missing. The board has none of its own.
- Before ordering, upload the Gerbers to the fab's DFM viewer, and print the board 1:1 to test-fit the smart port jacks and the GH connectors.

**Making the fab files** (KiCad 10, with `centurion.kicad_pcb` open):

1. **File → Fabrication Outputs → Gerbers (.gbr)**. Output folder `fab/gerbers/`. Layers: F.Cu, In1.Cu, In2.Cu, B.Cu, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, F.Paste, B.Paste, Edge.Cuts. Tick "Check zone fills before plotting" and "Use Protel filename extensions"; leave the rest at the defaults. Click **Plot**.
2. In the same dialog, **Generate Drill Files**: Excellon, millimetres, decimal zeros, absolute origin, PTH and NPTH in separate files, Gerber map file. Click **Generate Drill File**.
3. Zip `fab/gerbers/` and upload it. On the order form: 4 layers, 1.6 mm, 1 oz outer copper, tented vias, the stackup from [PCB layout](#pcb-layout), and a note asking for plugged or filled vias in U1's thermal pad.
4. For assembly only: **File → Fabrication Outputs → Component Placement (.pos)** as CSV in millimetres, plus the BOM in `bom/`.

The same from a terminal in this folder:

```bash
kicad-cli pcb export gerbers --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts" --check-zones -o fab/gerbers/ centurion.kicad_pcb
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm --generate-map --map-format gerberx2 -o fab/gerbers/ centurion.kicad_pcb
```

## MCU pin map

STM32G491RET6, LQFP-64. Every assignment was checked against ST's pin data (STM32_open_pin_data, `STM32G491R(C-E)Tx.xml`).

| Function | Pin | Peripheral |
|---|---|---|
| Brain port A: TX, RX, DE | PA2, PA3, PA1 | USART2, hardware DE |
| Brain port B: TX, RX, DE | PB10, PB11, PB14 | USART3, hardware DE |
| Jetson backup UART: TX, RX | PC4, PC5 | USART1 |
| USB D-, D+ | PA11, PA12 | USB FS device |
| I2C to the mux: SCL, SDA | PA15, PB7 | I2C1 |
| Second I2C bus (AUX1, J18): SCL, SDA | PC8, PC9 | I2C3 |
| IMU: SCK, MISO, MOSI, CS | PA5, PA6, PA7, PA4 | SPI1, CS as GPIO |
| IMU INT1, INT2 | PA8, PA10 | EXTI 8 and 10 |
| Spare SPI (J15): SCK, MISO, MOSI, CS, INT | PC10, PC11, PB5, PA0, PB9 | SPI3, CS as GPIO, INT on EXTI 9 |
| ramBar UART: TX, RX | PC12, PD2 | UART5 |
| ramBar CAN FD: TX, RX | PB13, PB12 | FDCAN2 |
| Battery voltage | PC0 | ADC1_IN6 |
| Turret pot | PC1 | ADC1_IN7 |
| AUX1 signal pin | PC2 | ADC1_IN8 |
| PGOOD (5 V good, high = good) | PC3 | GPIO in |
| VBUS sense (USB plugged in) | PB2 | GPIO in |
| Mux reset (active low) | PB0 | GPIO out |
| LEDs: MCU, port A, port B (high = on) | PC6, PC7, PB15 | GPIO out |
| SWD: SWDIO, SWCLK, SWO | PA13, PA14, PB3 | |
| NRST, BOOT0 | PG10, PB8 | |
| 8 MHz crystal | PF0, PF1 | HSE |
| Unused, no-connect flags | PA9, PB1, PB4, PB6, PC13, PC14, PC15 | |

PB8 is also BOOT0, so nothing else uses it. PB4 and PB6 are the USB-C PD (UCPD) pins and stay unused.

Some pins moved on 2026-11-02 for the ramBar link. UART5's only TX/RX pins are PC12/PD2 and FDCAN2's free pair is PB12/PB13, so the spare SPI's MOSI, CS and INT and the two IMU interrupts moved to free pins. PA10 (the bootloader's USART1 RX) was meant to stay free, so an IMU interrupt couldn't trigger the bootloader's UART detection. On the 4-layer board (2026-11-03) IMU_INT2 moved from PB1 to PA10 anyway: PB1 (U3 pin 25) is boxed in by the routing of its neighbours on U3's bottom edge. See "Flashing over USB" below for the workaround.

## Firmware notes

- **RS-485 driver enable.** Use the USART's RS-485 mode (DEM bit) on USART2 and USART3. The hardware raises DE before the first bit and drops it after the last stop bit. DE has a 10k pulldown, so the driver stays off while the MCU resets or is being flashed.
- **Echo.** RE is tied low, so each MAX33071E's receiver is always on. The MCU hears its own bytes on RX when it sends. Throw them away, or use them to check for collisions.
- **Two-port split.** To read on port A and write on port B, keep port A's DE low and only transmit on port B. If the brain ever sends on port B, the port B receiver still hears it.
- **Baud rate.** The brain side: `vexGenericSerialEnable(port, 0)` then `vexGenericSerialBaudrate(port, 921600)` or lower. The MAX33071E handles up to 2 Mbps.
- **USB.** Connect the USB D+ pullup (`HAL_PCD_Start`) only while VBUS_SENSE (PB2) reads high. USB runs from HSI48 with the clock recovery system, so no crystal is needed.
- **Flashing over USB (no programmer needed).** The G491 has a bootloader built into ROM. Plug in the USB-C, hold BOOT, tap RESET, let go of BOOT, and it shows up as a DFU device. Flash it with STM32CubeProgrammer (USB, DFU) or `dfu-util`. Firmware can also jump to the bootloader on a command from the Jetson. Flash with the smart ports unplugged: the bootloader also listens on USART2, which is smart port A's RX, and brain traffic there could make it pick that UART instead of USB. It also listens on USART3 at PC10/PC11 (J15's SCK and MISO, held by R57) and I2C2 on PC4/PA8. And on USART1 RX at PA10, which carries the IMU's INT2: flash with the IMU unplugged, or have firmware turn off the IMU's interrupt outputs before it jumps to the bootloader.
- **SWD (J3).** Only for step-through debugging with an ST-LINK (a Nucleo board's ST-LINK works with 6 dupont wires). Not needed to flash.
- **Clock.** Y1 (8 MHz) is fitted. Run SYSCLK from the PLL on HSE. FDCAN needs the crystal's accuracy, and it keeps the USB bootloader independent of the internal oscillator.
- **PGOOD on USB power.** The buck is off, and TI doesn't specify PGOOD below 2 V in, so it may still read high. Use VBAT_SENSE (PC0) to know whether port power is there.
- **Battery sense.** 100k over 22k on VIN_MOD, which is after the OR diodes (D5/D11) and F1, not the battery itself. Scale is 0.1803 V per volt (VIN_MOD = ADC V x 5.545), and full scale (3.3 V) is 18.3 V. Add the B340A drop, about 0.3 to 0.45 V depending on load, to get the battery voltage: a full 14.6 V battery reads about 2.56 V.
- **UCPD dead battery.** Set `UCPD_DBDIS` (`HAL_PWREx_DisableUCPDDeadBattery()`) at startup. It releases the internal USB-C pulldowns on PB4 and PB6.
- **ramBar link.** UART5 at 3.3 V logic, at whatever baud rate both ends agree on. FDCAN2 goes through U16: SHDN and STB are tied low, so the transceiver is always on. R53 terminates this end of the CAN bus; ramBar must put 120 Ω across CANH-CANL at its end too.
- **I2C speed.** 400 kHz works on every mux channel and on bus 2 with the 2.7k / 2.2k pullups. Select one mux channel at a time: several at once put their pullups in parallel.
- **CAN FD.** Run the FDCAN kernel clock at 80 or 160 MHz from the HSE PLL. Above about 1 Mbit/s data rate, enable transmitter delay compensation (DBTP.TDC) and put the data-phase sample point at about 70 to 75 %.
- **Inputs with nothing plugged in.** Turn on internal pulls for IMU_INT1/INT2 (PA8, PA10), SPARE_INT (PB9) and IMU_MISO (PA6), matching the device's polarity.
- **ramBar on USB-only power.** Keep UART5's pins (PC12, PD2) in analog mode until VBAT_SENSE or PGOOD shows smart port power, so the board doesn't back-power an unpowered ramBar.
- **Flashing over USB:** unplug ramBar as well as the smart ports. The ROM bootloader's SPI2 uses PB12 (CAN_RX) as chip select and PB14 (port B DE) as MISO.
- **GPIO speed on the cable pins.** Set SPI1 (J5), SPI3 (J15) and USART1 TX (J4) to GPIO speed low (OSPEEDR 00). The 1.7 ns edges of the fastest setting ring on the JST GH cables (sim/README.md). On J15 and J4 they push 10 to 19 mA into the far chip's clamp diodes. J5's 100 Ω resistors handle a 0.3 m cable at any speed, but even there speed low cuts the MISO crosstalk from 0.88 V to 0.13 V (VIL is 0.99 V), and a 0.5 m cable gets extra SCK edges at the two fastest settings. 17 ns edges are still fine for 10 MHz SPI and 1 Mbaud. Turn USART1 TX on only once the Jetson is up: an idle-high TX into an unpowered Jetson lifts its 3.3 V rail to about 2.5 V.
- **I2C timeouts.** Give every I2C call a timeout, and scan the mux channels at boot so empty ports are skipped. A stuck sensor only blocks its own mux channel. Pulse MUX_RST low to clear it.

## The board as drawn now

149 fitted parts: 55 resistors, 31 capacitors, 19 connectors, 15 ICs, 10 supply-select jumper headers, 9 diodes (3 of them the D6 to D8 status LEDs), 4 polyfuses, 2 LEDs, 2 buttons, 1 crystal and 1 MOSFET. Also 3 not-fitted parts (R36, R51, R52) and 12 test pads.

### Power (power sheet, copied from powerJackal)

| Ref | Part | Job |
|---|---|---|
| J1, J2 | Molex 0955012441 | Smart port jacks A and B, on the smart port sheet |
| D5, D11 | B340A Schottky | Let either port power the board |
| F1 | 2016L150 polyfuse, 1.5 A hold | Input overcurrent |
| D4 | SMBJ16A TVS | Clamps input spikes |
| C1 | 47 µF 50 V electrolytic | Damps hot-plug ringing |
| C2, C3, C32 | 3 x 10 µF 50 V, 1210 | Buck input ceramics at U1's VIN pins. TI asks for 20 µF effective; two 10 µF parts give only about 14.6 µF at 14.6 V because of DC bias, so C32 was added. |
| U1 | TPSM53602 | 5 V buck module, 2 A |
| U7 | MCP1826S | 3.3 V LDO, 1 A |
| J16, U13, C30 | USB4105 USB-C, USBLC6-2SC6, 100 nF | USB link to the Jetson and firmware upload, with ESD. C30 sits at U13's VBUS pin, as ST recommends. |
| Q1, D9, D10 | AO3401A, 2 x SS14 | USB runs the 3.3 V side only while the 5 V rail is off |
| R1, R40, C6 | 100k, 22k, 100 nF | Battery voltage sense |
| R45 | 10k | New. PGOOD pullup, to PC3. |
| R46, R47 | 10k, 15k | New. VBUS sense, 5 V gives 3.0 V on PB2. |
| R48 | 5.1k | New. Holds VBUS at 0 V when no host is plugged in. Same fix as stellaNova R22. |
| TP1 to TP6 | 1.5 mm round pads | New. VIN_MOD, 5V, 3V3, 2 x GND, PGOOD |
| LED1, LED2 | Green | Input power and 5 V on |

### Smart ports (smartport sheet, once per port)

| Port A | Port B | Part | Job |
|---|---|---|---|
| U14 | U15 | MAX33071EASA+ | RS-485 transceiver |
| C25 | C26 | 100 nF | Transceiver decoupling |
| R49 | R50 | 10k | DE pulldown |
| R51 | R52 | 120 Ω, not fitted | Termination. Fit only if the bus rings. |
| TP7 to TP9 | TP10 to TP12 | 1.5 mm round pads | VPORT, RS485_A, RS485_B |

No TVS on A and B: anything that clamps below 14.6 V would conduct if the battery ever touched A or B. The MAX33071E's ±65 V rating covers that.

**Smart port pinout** (checked against the team's cable on 2026-11-02, matching a VEX forum photo of the smart cable). J1 and J2 run pin 1 to 4: A, B, GND, +12 V battery. On the cable that's black = A, red = B, green = GND, yellow = +12 V; red is a data line, not power. A cable crimped the wrong way round swaps the ends (12 V onto A, A onto VPORT). Nothing is damaged, because A and B take ±65 V and D5/D11 block reverse current, but the board won't power up or talk until the cable is flipped.

### MCU (mcu sheet)

| Ref | Part | Job |
|---|---|---|
| U3 | STM32G491RET6 | MCU |
| C9, C12, C13, C14 | 100 nF | One at each VDD pin (16, 32, 48, 64) |
| C10 | 10 µF | Bulk on 3.3 V |
| C18, C19 | 1 µF, 100 nF | VDDA (pin 29) |
| C20 | 100 nF | VREF+ (pin 28) |
| C21 | 100 nF | VBAT (pin 1) |
| C11, SW1 | 100 nF, button | NRST filter and RESET |
| R2, SW2 | 10k, button | BOOT0 pulldown and BOOT |
| J3 | 1 x 6 header | SWD, debugging only: 1 VDD, 2 SWCLK, 3 GND, 4 SWDIO, 5 NRST, 6 SWO. Same order as the Nucleo ST-LINK header (CN4). Kept as plain pins: it only sees a debugger on the bench. |
| D6 to D8, R3 to R5 | Green, orange, red LEDs, 1k | MCU status, port A, port B |
| Y1, C22, C23 | 8 MHz crystal (ABM8AIG, 8 pF load), 2 x 10 pF | Fitted on 2026-11-02 for CAN FD |

Each decoupling cap's Note field says which pin it belongs at.

### IMU and spare SPI (imu sheet)

| Ref | Part | Job |
|---|---|---|
| J5 | JST-GH 8-pin, vertical | IMU board ([../imuBoard](../imuBoard/README.md)): 1 3V3, 2 GND, 3 SCK, 4 MOSI, 5 MISO, 6 CS, 7 INT1, 8 INT2 |
| R8, R9, R41 | 100 Ω | Series resistors on SCK, MOSI and CS. With the pin's own ~30 Ω they roughly match the JST GH cable (about 130 Ω), so a 0.3 m cable works at any GPIO speed and 0.5 m at medium or low (sim/README.md). 22 Ω until 2026-11-04. |
| R58 | 10k | IMU CS pullup to SENS_3V3: keeps the IMU deselected while PA4 is hi-Z (reset, flashing, bootloader) |
| U5 | TPD4E05U06 | ESD on SCK, MOSI, MISO and CS |
| J15, R57 | JST-GH 7-pin, vertical, 10k | R57 pulls SPARE_MISO up so it doesn't float with J15 empty. Spare SPI: 1 3V3, 2 GND, 3 SCK, 4 MOSI, 5 MISO, 6 CS, 7 INT |

Both connectors take 3.3 V from SENS_3V3 (through F2). F2 keeps a shorted cable from burning, but it can't stop the short from pulling +3.3V down (and resetting the MCU) until it trips; see [sim/README.md](sim/README.md#connector-simulations). Keep the IMU cable at 30 cm or less (50 cm at most, with GPIO speed medium or low) and set the SPI pins to GPIO speed low. With R8, R9 and R41 at 100 Ω the simulations show 0.3 m working at any GPIO speed and 0.5 m at medium or low; 1 m fails at every speed. J15 has no series resistors: keep its cable short and its pins at speed low. A USB host breakout on J15 would also need its own switched, current-limited 5 V.

### ramBar link (usb_jetson sheet)

| Ref | Part | Job |
|---|---|---|
| J19 | JST-GH 6-pin, vertical | 1 5V, 2 TX (centurion out), 3 RX (centurion in), 4 GND, 5 CANH, 6 CANL |
| F4 | Polyfuse, 0.75 A hold, 1206 (MF-NSMF075-2) | 5 V to ramBar, so a cable short can't overheat the cable. A short still pulls +5V down until F4 trips: U1 current-limits at about 3.5 A and hiccups (sim/README.md). Holds about 0.52 A at 60 °C, so ramBar can draw up to about 0.5 A. Rated 6 V max, fine on 5 V. |
| R59 | 470 Ω | Series resistor in TX (RAMBAR_TX to the connector side RAMBAR_TX_C): limits current into an unpowered ramBar and damps the cable |
| U16, C27 | TCAN334G, 100 nF | 3.3 V CAN FD transceiver (5 Mbps), always on |
| R53 | 120 Ω | CAN termination at centurion's end |
| R54 | 10k | Holds RX high when ramBar is unplugged |
| U17 | TPD4E05U06 | ESD on TX and RX (two channels unused) |
| D12 | NUP2105L | CAN bus TVS on CANH and CANL. 24 V working, so it doesn't clip CAN's -2 to +7 V common mode the way a 5.5 V array would. |
| J4, R56 | JST-GH 3-pin, vertical, 10k | Jetson backup UART (USART1): 1 TX, 2 RX, 3 GND. R56 holds RX high when the Jetson is unplugged. |

Both links share one cable, so ramBar can start on the plain UART and move to CAN FD later with no board change. CANH and CANL sit next to each other on pins 5 and 6 so they can be twisted together in the cable. The UART is 3.3 V logic and isn't meant for long runs beside motors. CAN FD is the robust one.

### Sensor ports (sensors sheet)

| Mux channel | Port | Jack | Notes |
|---|---|---|---|
| 0 | ENC1 | J6 | |
| 1 | ENC2 | J7 | |
| 2 | LASER (lift, on the turret) | J8 | New jack, pullups R42 and R43 |
| 3 to 6 | TOF1 to TOF4 | J9 to J12 | |
| 7 | SPARE | J13 | Was ToF5 |

| Ref | Part | Job |
|---|---|---|
| U6 | TCA9548A | 8-channel I2C mux, address 0x70 |
| U8 to U12 | 5 x TPD4E05U06 | ESD on every port |
| F2 | Polyfuse, 0.5 A hold (MF-NSMF050-2, same as F3 since 2026-11-04) | Feeds SENS_3V3: the 3.3 V side of every sensor jack, both SPI connectors and the bus 2 pullups |
| C28, C29 | 10 µF | New. Bulk on SENS_3V3 and SENS_5V after the fuses. They soften a sensor hot-plug but don't prevent it: plugging a 10 µF breakout into a live 3.3 V jack still dips SENS_3V3 to about 1.3 to 2.1 V for a few µs (sim/README.md). Plug sensors in with the board off. |
| F3 | Polyfuse, 0.5 A hold (MF-NSMF050-2) | New. Feeds SENS_5V: the 5 V side of every sensor jack and AUX1 |
| JP2 to JP10 | 1 x 3 headers, 2.54 mm, with a shunt | New. Supply select for J6 to J13 and J18, one per jack. See below. |
| J17, R55 | JST-GH 3-pin, 100 Ω | Turret pot: 1 POT_VCC, 2 wiper, 3 GND. POT_VCC comes from +3.3V through R55, the same rail as the ADC's VREF+, so the reading is ratiometric and doesn't drift with sensor load on F2. R55 limits a cable short. |
| R44, C24, R60 | 1k, 100 nF, 1M | Pot filter into PC1. ESD is U12 D2-. R60 pulls POT_IN down so an unplugged pot reads 0. |
| J14, JP1 | JST-GH 5-pin, 1 x 3 header with a shunt | AUX1: VCC, GND, SDA, SCL, signal. JP1 sets VCC to 3.3 V or 5 V (5 V now through F3), same as JP2 to JP10. |
| R34, R35, R36, C31 | 10k, 15k, 0 Ω (not fitted), 10 nF | AUX1 signal divider for 5 V signals, with C31 on PC2 for the ADC. Fit R36 instead only for 3.3 V signals: it puts the signal straight on PC2. |
| J18 | JST-GH 4-pin | Spare I2C on the second bus, shared with AUX1 |

**Jack supply (JP1 to JP10).** Each I2C jack has its own VCC net and a 1 x 3 pin header (2.54 mm, cut from a breakaway strip) with a standard jumper shunt. The middle pin feeds the jack.

- Shunt on pins 1-2 (left, square pad): 3.3 V.
- Shunt on pins 2-3 (right): 5 V.
- No shunt: the jack is unpowered.

JP2 to JP9 sit right under their jacks, with pin 1 on the left. JP1 (AUX1) and JP10 (J18) stand just inside their jacks on the right edge, with pin 1 at the top. Every header has 3V3 and 5V printed at its end pins. Right-angle headers were considered and dropped: each is 12.4 x 8.7 mm against 3.6 x 8.7 mm, and ten of them don't fit under the jacks without a taller board. Only one shunt fits on a 3-pin header, so 3.3 V and 5 V can't be shorted together. A 2-pin "shorted = 3.3 V, open = 5 V" jumper can't choose between two rails on its own. It would also put 5 V on a 3.3 V sensor whenever the shunt shook loose. With three pins, a lost shunt just turns the sensor off. Set the shunts before plugging in sensors.

| Jumper | Jack | VCC net |
|---|---|---|
| JP2 | J6 ENC1 | ENC1_VCC |
| JP3 | J7 ENC2 | ENC2_VCC |
| JP4 | J8 LASER | LASER_VCC |
| JP5 to JP8 | J9 to J12 TOF1 to TOF4 | TOF1_VCC to TOF4_VCC |
| JP9 | J13 SPARE | MUX7_VCC |
| JP10 | J18 I2C_SPARE | I2C_SPARE_VCC |

- **Mux jacks (J6 to J13).** The two I2C pullups follow the jack's VCC. The TCA9548A's pass gates translate between the 3.3 V MCU side and a 5 V channel, which is how TI's datasheet shows mixed-voltage channels, and its channel pins take 5 V. The TPD4E05U06 ESD parts are rated 5.5 V.
- **J18 (bus 2, wired straight to the MCU).** Only VCC changes. The bus pullups R32/R33 stay on SENS_3V3 (the fused 3.3 V) because the MCU pins and J14 share that bus. Most 5 V I2C breakouts read 3.3 V logic. A strict 5 V CMOS part might not.
- **Pullups.** Each jack has 2.7k pullups (R13 to R16, R19 to R28, R42, R43) to its own VCC: that meets the 400 kHz rise time on a 1 m cable and stays under the 3 mA sink limit on a 5 V jack. Bus 2 (R32, R33) uses 2.2k, so two cables on J14 and J18 still meet 400 kHz. Cut the pullup jumpers on breakouts that have their own (SparkFun/Qwiic boards usually do), or the sink current goes over 3 mA.
- **Budget: put ToF sensors and the laser on 5 V.** All 3.3 V jacks share F2 (0.5 A hold), and F2 also feeds the IMU and SPI connectors. Eight VL53-class sensors on 3.3 V add up quickly and load the 3.3 V LDO. VL53 breakouts usually have their own regulator, so run them from 5 V (F3, 0.5 A hold). Keep the encoders, the IMU and anything 3.3 V-only on 3.3 V.
- **USB-only power.** On USB alone only the 3.3 V side runs and the 5 V jacks are off. All jacks on 3.3 V at once can draw about 0.55 A, more than a USB 2.0 port gives. Run sensors from the smart ports, or keep few on 3.3 V when testing on USB.

The JST-GH ports use pin 1 VCC, then SCL, SDA and GND (Pixhawk order). Encoders like the AS5600 and the VL53 ToF sensors each have one fixed address, which is why every one gets its own mux channel. A channel can still hold several devices with different addresses.

## Open questions

- **Lift laser part number.** Mux channel 2 assumes an I2C sensor such as a VL53.
- **LED strip.** Is it in v1? Plan Q14. The spare pin PA9 (TIM1_CH2) can drive one (PA10 now carries IMU_INT2).
- **ramBar.** Its board needs a matching JST-GH 6-pin, a 3.3 V UART, a CAN FD transceiver and a 120 Ω terminator, and must draw under 0.5 A from the 5 V pin.
- **Still open in the plan.** Q3 (lock the footprints), Q9 (smart port current limit), Q11 (soldering), Q12 (V5 packet format).

## Fix list

Done in this update:

1. MCU sheet redrawn for the STM32G491 with global labels. The old local labels that dead-ended (31 isolated labels) are gone.
2. One MAX33071E per smart port, with DE pulldown, decoupling and termination footprint.
3. VBAT_SENSE to PC0. PGOOD to PC3 with a pullup.
4. ENC3's channel is now the lift laser with its own jack. AUX1 and J18 are on the second I2C bus.
5. JP1 has a footprint. The "T0F" and "B00T" typos are fixed.
6. Power flags: the two extra flags on the regulator outputs are removed, and the LDO input has one. The 3 ERC errors are gone.
7. powerJackal's test pads are back, plus A and B pads for each port.
8. Every purchased part has a part number. The BOM is in `bom/`.

Still to do:

1. Add the LED strip circuit if it is in v1.
2. Work through the [Before ordering](#before-ordering) list.
3. Before ordering, recheck the four lines that were out of stock at DigiKey CA on 2026-11-04 (red stock cells in the BOM): TCA9548APWR (restock expected Nov 10), SM04B-GHS-TB and SM03B-GHS-TB (Nov 16), RC0805FR-07470RL (Nov 9).

## Design reviews (2026-11-03)

Five independent reviews ran on rev A. They only read the files, and their findings were then fixed in the schematic and layout. The four layout and electrical reviewers are reusable Claude Code agents in `../.claude/agents/`, and the rules they check are in [../PCB_DESIGN_GUIDELINES.md](../PCB_DESIGN_GUIDELINES.md).

| Review | Result | What changed |
|---|---|---|
| Schematic netlist audit | 0 errors | Pot fed from +3.3V through R55 (ratiometric with VREF+). CAN TVS D12 instead of the 5.5 V array. Pullups R56, R57. Bulk caps C28, C29. C30 on U13 VBUS. Battery-sense diode drop documented. |
| Footprints vs datasheets | 0 errors | ESD arrays moved to a TI-land-pattern footprint (`centurion:TI_DQA_USON-10...`). Molex jack, button and thermal-via items added to "Before ordering". |
| Power and thermal | 2 errors fixed | F3 0.35 A to 0.5 A; F4 0.5 A to 0.75 A; ToF sensors on 5 V; 2 extra vias at every power-net layer change; 8 GND vias at the LDO tab; C32 on the buck input. |
| Signal interfaces | 0 errors | Jack pullups 4.7k to 2.7k, bus 2 to 2.2k; IMU CS pullup R58; RAMBAR_TX series R59; POT_IN pulldown R60; AUX1 ADC cap C31; firmware notes. |
| Layout checklist | 6 errors, 10 warnings; the placement ones fixed by script, the rest in [HAND_ROUTING.md](HAND_ROUTING.md) | Buck caps and FB divider placed at U1's pins; no bottom tracks under the buck stage or crystal; crystal caps at Y1. Also: GND vias at ground pads, an edge via fence, screw-head keep-outs, a 0.15 mm silk stroke, and names beside every connector. Hand routing remains: bottom-layer signals, pairs, ESD order. |
| Layout checklist, rerun on the 4-layer board (2026-11-04) | 0 errors, 8 warnings | All optional for rev A; listed under [Layout audit](#layout-audit-4-layer-board-2026-11-04). |

The three ERC warnings from powerJackal's power sheet were also cleared (see below).

## How this was checked

- KiCad 10 `kicad-cli`: ERC and netlist export, with KiCad's standard symbol and footprint libraries loaded. Every footprint name resolves.
- ERC: 0 errors, 0 warnings. The 3 `multiple_net_names` warnings inherited from powerJackal's power section were cleared on 2026-11-02 without changing any net (all 148 nets checked, same names and same pins before and after):
  - The power sheet's local "5V" and "3V3" labels are now +5V and +3.3V power symbols at the same points, so each rail has one name.
  - The power sheet takes the OR'ed input on one sheet pin, VIN_OR, wired to both smart port sheets' VBAT_OR outputs. Before, two sheet pins (VBAT_A, VBAT_B) sat on the same node. VBAT_OR is each port's D5/D11 cathode, so the two ports stay separate through the diodes: J1.4 reaches only D5's anode and J2.4 only D11's.
- The cached LED symbol on the power sheet was refreshed from KiCad's library on 2026-11-02, which cleared the 2 `lib_symbol_mismatch` warnings. Only a simulator pin-map property differed.
- A script checked the exported netlist against the design: all 64 G491 pins against the pin map, both RS-485 ports end to end, every I2C, SPI, ADC and status net, the LED and DNP parts. 0 problems, and no net with only one connection.
- The G491 pin functions were checked against ST's pin data, and the stock and prices against digikey.ca on 2026-11-02 (G491, MAX33071E), 2026-10-30 (stellaNova parts) and 2026-10-29 (powerJackal parts).

## Sources

- [STM32G491RE product page, ST](https://www.st.com/en/microcontrollers-microprocessors/stm32g491re.html)
- [STM32G491RE datasheet, ST](https://www.st.com/resource/en/datasheet/stm32g491re.pdf)
- [STM32 open pin data, ST](https://github.com/STMicroelectronics/STM32_open_pin_data)
- [MAX33071E, Analog Devices](https://analog.com/en/products/max33071e.html)
- [ArduPilot PR on RS-485 DE, not supported on F4](https://github.com/ArduPilot/ardupilot/pull/26930)
- [powerJackal hot-plug simulation](../powerJackal/sim/README.md)
- [centurion USB hot-plug simulation](sim/README.md): without C33, U7's input could pass its 6.5 V rating on a long, stiff USB cable; with C33 it stays at 5.5 V or less
