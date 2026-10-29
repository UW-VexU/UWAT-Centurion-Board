# powerJackal design notes, rev A

How the board works, why it is laid out the way it is, how to test it, and what changed during rev A. The schematic PDF, the board viewer and the wiring map in this folder show the same design visually.

## Power tree

```
J1 smart port (VPORT) --D5--+
                            +-- VIN_OR --F1 1.5 A-- VFUSE --R1 20 mΩ-- VIN_MOD --> U1 TPSM53602 --> 5V_MOD --R2 20 mΩ-- 5V --> J6, LED2
J2 bench input (BENCH_IN) --D3--+                                      |                                                        |
                                                                      D1 TVS, C1 47 µF, C2 + C3 10 µF, C8 100 nF                  D2
                                                                                                                                 |
J7 USB-C (VBUS_USB) --D4-- USB_PWR --Q1-------------------------------------------------------------------------------------- 5V_LDO --> U6 AP7361C --> 3V3_LDO --R12 50 mΩ-- 3V3
```

| Net | Comes from | Feeds |
|---|---|---|
| VPORT | J1 pin 4, smart port battery power | D5 |
| BENCH_IN | J2 pin 1, bench supply | D3 |
| VIN_OR | D5 and D3 cathodes | F1, LED1 through R8 |
| VFUSE | F1 | R1 (U2 shunt) |
| VIN_MOD | R1 | D1, C1 to C3, C8, U1 input |
| 5V_MOD | U1 output | C4, C5, R3 divider, R2 (U3 shunt) |
| 5V | R2 | J6, LED2 through R9, D2, Q1 gate |
| USB_PWR | D4 from USB VBUS | Q1 drain |
| 5V_LDO | D2 or Q1 | C10, U6 input |
| 3V3_LDO | U6 output | C11, R12 (U5 shunt) |
| 3V3 | R12 | ESP32, INA226 supplies, I2C pull-ups, J3, J9 |

### Input

- D5 and D3 (B340A, 40 V 3 A Schottky) OR the smart port and the bench input. Either can be plugged in alone or both at once, and neither can feed the other.
- F1 is a 1.5 A hold, 3 A trip polyfuse right after the OR diodes.
- D1 (SMBJ16A) clamps hot-plug spikes well below the TPSM53602's 38 V absolute maximum. C1 (47 µF electrolytic) damps the ringing.
- VEX publishes no current rating for the smart port power pin. VEX's guidance is to keep an added load at 20 W or less, about 1.6 A at 12.8 V. With 2 A on the 5 V rail this board pulls about 12 W.

### 5 V regulator

- U1 is a TI TPSM53602 module (3.8 to 36 V in, 2 A, 1.4 MHz, inductor inside).
- **Output:** R3 10 kΩ and R4 2.49 kΩ set 5.0 V (datasheet table 7-1). EN is tied to VIN, so it is always on.
- **Capacitors:** input is C2 and C3 (2 x 10 µF 50 V) plus C1 bulk. Output is C4 and C5 (2 x 47 µF). The datasheet asks for 27 µF real at 5 V.
- **Unused pins:** DNC pins 4 and 5 and V5V (pin 13) stay open. NC pins 3, 10, 11 and AGND (12) join the exposed pad.
- **PGOOD:** open drain, pulled up to 3.3 V by R7 and read on GPIO3. Low means the 5 V output is out of regulation. TI only specifies PGOOD with VIN at 2 V or more, so on USB power alone it will most likely read high. Check U2's bus voltage in firmware before trusting it.

### 3.3 V regulator and the USB power switch

- U6 is an AP7361C-33 LDO (1 A, SOT-223). Its tab is GND and sits in the ground pour.
- Its input (5V_LDO) comes from the 5 V rail through D2 (SS14), or from USB through D4 (SS14) and Q1.
- **Q1** is an AO3401A P-channel MOSFET. Drain on USB_PWR, source on 5V_LDO, gate on the 5 V rail.
  - **5 V rail off** (USB only): the gate sits at 0 V and Q1 turns on fully, so USB runs the 3.3 V side for flashing on the desk.
  - **5 V rail up** (port or bench power on): the gate is at 5 V and Q1 is off. USB carries data only, so U2 and U3 always include the board's own draw.
  - **No gate pull-down needed:** R3, R4 and LED2 already pull the 5 V rail to 0 V when U1 is off.
  - **No backfeed:** D4 stays in series, so USB cannot leak through Q1's body diode while the rail is up.
- **Handover:** going from USB to port power should not reset the ESP32. By estimate, 5V_LDO stays around 4.2 V during the handover, above the about 3.7 V the LDO needs. This has not been tested on a real board.
- Q1 replaced JP4, a cut-to-open solder jumper. See `images/q1_usb_switch.png` and `images/q1_gate_path.png`.

## Measurement

Three INA226 monitors share the I2C bus. Their VS supply is 3.3 V.

| Monitor | Measures | Address | A1, A0 | Shunt | Full scale (81.92 mV) | Current LSB, CAL |
|---|---|---|---|---|---|---|
| U2 | Port input after F1 | 0x40 | GND, GND | R1 20 mΩ | 4.096 A | 125 µA, 2048 |
| U3 | 5 V rail | 0x41 | GND, VS | R2 20 mΩ | 4.096 A | 125 µA, 2048 |
| U5 | 3.3 V rail | 0x45 | VS, VS | R12 50 mΩ | 1.638 A | 50 µA, 2048 |

- CAL = 0.00512 / (current LSB x shunt). The power LSB is 25 x the current LSB.
- Every monitor reads its rail voltage on VBUS. U2 reads the port voltage after F1.
- The sense traces are Kelvin connections. They leave each shunt pad from its inner edge, away from the power copper.
- The ALERT pins are not connected.
- Shunts are Vishay WSL1206 metal strip, 1%.

## ESP32-C3 pins

The module is an ESP32-C3-MINI-1U-N4X (4 MB flash, U.FL antenna connector, no antenna fitted). Its footprint and symbol come from Espressif's official KiCad library.

| Pin | GPIO | Use |
|---|---|---|
| 3 | 3V3 | C12 47 µF plus C13 and C15 100 nF |
| 8 | EN | R17 10 kΩ to 3V3, C9 1 µF to GND (Espressif's values), SW1 RESET to GND |
| 5 | GPIO2 | Boot strap, held high by R21 10 kΩ |
| 6 | GPIO3 | PGOOD from U1 (R7 pull-up) |
| 18 | GPIO4 | I2C SDA (R5 4.7 kΩ pull-up) |
| 19 | GPIO5 | I2C SCL (R6 4.7 kΩ pull-up) |
| 22 | GPIO8 | Boot strap, must be high to download, R22 10 kΩ |
| 23 | GPIO9 | BOOT strap, R23 10 kΩ pull-up, SW2 to GND |
| 16 | GPIO10 | Status LED3 through R20 1 kΩ (about 1.3 mA) |
| 26, 27 | GPIO18, GPIO19 | USB D- and D+ through R25 and R24 (22 Ω) and the U7 ESD chip |
| 12, 13, 20, 21, 30, 31 | GPIO0, 1, 6, 7, 20, 21 | Free, not connected |
| 4, 7, 9, 10, 15, 17, 24, 25, 28, 29, 32 to 35 | none | NC inside the module |
| 1, 2, 11, 14, 36 to 53 | GND | Ground |

Notes on the free pins:

- **GPIO0 and GPIO1:** these are the 32 kHz crystal pins. No crystal is fitted, so they work as normal pins and analog inputs.
- **GPIO20 and GPIO21:** these are UART0. The ROM prints boot messages on GPIO21 at power-up.
- **Ideas for rev B:**
  - An RS-485 transceiver on two free pins, to listen to the smart port data lines.
  - The INA226 ALERT pins joined onto one free pin, for interrupts.

## USB-C

- USB 2.0 only, through a GCT USB4105-GF-A receptacle.
- R14 and R15 must be two separate 5.1 kΩ resistors (one per CC pin). Without them a USB-C to USB-C cable won't turn on 5 V.
- U7 (USBLC6-2SC6) is right beside J7. The data lines pass straight through it under the chip, which is the layout its datasheet shows.
- Each pair of A and B row pins is joined by a short 45 degree link that stays clear of the next pin.

## Connectors

| Ref | Part | Pins |
|---|---|---|
| J1 | Molex 0955012441, 4P4C smart port jack | 1 RS485_A, 2 RS485_B, 3 GND, 4 VPORT. RS-485 only goes to TP8 and TP9 |
| J2 | Phoenix 1935161, 5.08 mm screw terminal | 1 + (10 to 15 V), 2 GND |
| J6 | Phoenix 1803277, 3.81 mm header | 1 + 5 V, 2 GND. Plug: Phoenix 1803578 |
| J9 | Phoenix 1803277, 3.81 mm header | 1 + 3.3 V, 2 GND. Plug: Phoenix 1803578 |
| J3 | JST SM04B-SRSS-TB, STEMMA QT / Qwiic | 1 GND, 2 3V3, 3 SDA, 4 SCL |
| J7 | GCT USB4105-GF-A, USB-C | USB 2.0 data and VBUS |

Plug-in test loads live off the board. Clamp a cement resistor's leads in a 1803578 plug:

- **LOAD1**, 10 Ω: 0.5 A at 5 V.
- **LOAD2**, two 10 Ω in parallel: 1 A at 5 V. Use it on J6 only.
- **LOAD3**, 22 Ω: 150 mA at 3.3 V.

## Test pads

TP1 to TP6 and TP8 to TP10 are bare 3.4 x 1.8 mm copper pads with no paste, so there is nothing to buy. They use the same land as a Keystone 5015, so a test loop can be soldered on later.

| Pad | Net |
|---|---|
| TP1 | VPORT |
| TP2 | VIN_MOD |
| TP3 | 5V |
| TP4 | 3V3 |
| TP5, TP6 | GND |
| TP8, TP9 | RS485_A, RS485_B |
| TP10 | PGOOD |

## Layout

### Rules

| Rule | Value |
|---|---|
| Clearance | 0.2 mm |
| Minimum track | 0.2 mm |
| Vias | 0.6 mm pad, 0.3 mm drill (power vias 0.8 / 0.4) |
| Hole clearance | 0.25 mm. A custom rule allows 0.15 mm between J7's shell pegs and its own GND pins |
| Copper to edge | 0.5 mm keepout along every edge |
| Holes | Copper stays 4.2 mm from each mounting hole center (keepout rule areas) |

| Net class | Track | Nets |
|---|---|---|
| Power | 0.8 mm | VPORT, BENCH_IN, VIN_OR, VFUSE, VIN_MOD, 5V_MOD, 5V, 5V_LDO, 3V3_LDO |
| Supply3V3 | 0.3 mm | 3V3 |
| USBPower | 0.4 mm | VBUS_USB, USB_PWR |
| Ground | 0.4 mm | GND (poured) |
| Default | 0.25 mm | Everything else |

### Pours and vias

- **Ground:** a top ground pour and a bottom ground plane, tied by about 190 stitching vias.
- **U1 pours:** VIN_MOD and 5V_MOD each have their own top pour around U1's input and output caps.
- **Thermal vias:** U1's exposed pad has 11.
- **Pad connections:** surface mount pads join the pours solidly. Through-hole pads use thermal spokes (0.45 mm, 4 per layer) so they are easy to hand solder.

### Routing style

Keep to these when editing the layout:

- Traces enter a pad straight along the pad's long or short axis, never at an angle.
- 45 degree bends only, no 90 degree corners on a trace. Square corners are fine inside a pad or at a via.
- A branch joins a run with a square T. Never a V-shaped fork at a pad.
- One width per run. No thin and thick segments overlapping at a joint.
- No top-layer trace runs under the body of a part it does not connect to. Use the bottom layer to pass under parts.
- Kelvin sense lines leave the shunt pads from their inner edges.

`tools/kicad/` has checkers for these rules (`corners.py`, `junctions.py`, `under_parts.py`, `kelvin_check.py`).

### Check status for rev A

- **DRC:** 0 errors, 0 unconnected.
- **Warnings:** 4 silkscreen overlaps, and 7 silkscreen-past-edge warnings where connector outlines hang over the board edge by design. Library warnings depend on which KiCad libraries are installed.
- **Routing checks:** 0 angled pad entries, 0 sharp corners, 0 overlapping runs, no top-layer traces under other parts' bodies.
- **Netlist:** the schematic netlist matches the board.

## Assembly

- **Top side only.** Hand assembly works with a stencil.
- **Pads under the body:** U1 (TPSM53602) and U4 (ESP32-C3 module) need solder paste and a hot plate or hot air. The INA226s are 0.5 mm pitch VSSOP-10.
- **Silkscreen:** R21, R23 and LED3 have no reference designator printed because there is no room. LED3 has its "STAT" label. Use the assembly view in the board viewer to place them.

## Bring-up and test

1. **Before power:** check for shorts between VIN_MOD, 5V, 3V3 and GND with a meter.
2. **Bench input:** apply 12 V on J2 with a 0.3 A current limit.
   - LED1 (input) and LED2 (5 V) light up.
   - TP3 reads 5.0 V and TP4 reads 3.3 V.
   - Then raise the current limit to 2 A.
3. **USB only:** with port and bench power off, plug in USB-C. The ESP32 enumerates as a USB serial device, and Q1 feeds the 3.3 V side.
4. **I2C:** scan the bus. Expect 0x40, 0x41 and 0x45 (plus the OLED if one is plugged into J3).
5. **Loads:** plug LOAD1, then LOAD2, into J6, and LOAD3 into J9. Check that U3 reads about 0.5 A and 1 A, and U5 about 150 mA plus the board's own draw.
6. **USB handover:** with USB plugged in, turn on bench power. U5's current should stay put and the ESP32 should not reset.
7. **Hot-plug:** probe TP2 (VIN_MOD) against TP6 with a short ground spring while plugging into a live port.
   - The spike should stay well under 36 V.
   - The port should not drop out from the inrush into C1 to C3.

## Revision history

All changes below happened during rev A design, before any boards were made.

| Change | Why |
|---|---|
| Redesign around the TPSM53602 module and ESP32-C3 on a 72.4 x 47.0 mm board | Smaller, fewer parts, USB-C flashing and serial on one cable |
| Keystone test loops replaced by bare 3.4 x 1.8 mm copper pads | Nothing to buy, same land so loops can still be added |
| Full routing cleanup: straight pad entries, square T taps, 45 degree bends, one width per run, no top traces under other parts | Clean, reviewable layout. See `images/trace_cleanup_before_after.png` |
| U5 address 0x44 to 0x45 (A0 moved from GND to VS) | Lets U5's address pins share one short trace. Firmware must use 0x45 |
| TP10, C11, TP4 moved, R3 and R4 up 0.5 mm, SW1 down 0.5 mm, ESP32 support parts lined up with their pins | Room for straight pad entries |
| SCL moved to the bottom layer past D2 and U6 | It ran under both bodies on top, 0.2 mm from U6's tab. See `images/scl_and_j2_ground.png` |
| JP4 solder jumper replaced by Q1, an automatic USB power switch | No jumper to cut. USB powers the board only when port and bench power are off |
