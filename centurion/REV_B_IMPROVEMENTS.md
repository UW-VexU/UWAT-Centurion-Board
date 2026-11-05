# Centurion: improvements for rev B

None of these block rev A. They come from the 2026-11-04 checks on the final rev A board:
- the layout audit: 0 errors, 8 warnings;
- the crosstalk and signal simulations in [sim/](sim/README.md).

Rev A is ordered as is. Pick from this list when the board is next re-laid out. Coordinates are KiCad absolute (board corner at (100, 100)).

Items are grouped by area, roughly most useful first within each group.

## Planes and stackup

1. **Move the USB connector next to the MCU.** Put J16, U13, R38 and R39 by U3's right side, near PA11/PA12.
   - Today the pair runs about 60 mm on In2 from the left edge. It cuts a slot in the +3.3V plane, and bottom-layer tracks cross it 19 times.
   - Moved, the pair is about 10–15 mm long on F.Cu and In2 can be solid.
   - The connector-side piece (USB_DP/DN) is also only 11% coupled.
   - The D+ via at (164.3, 132.2) is 3.3 mm from the nearest GND via.
2. **Take the other signals off In2.** About 189 mm of 22 slow nets run there, including:
   - TOF3/TOF4 I2C, I2C_AUX, AUX1_SIG_IN
   - IMU SPI, POT_IN, NRST, BOOT0, LED_MCU

   They cut four islands out of the +3.3V plane, which island removal then deletes:
   - 137 mm² at (157–176, 115–138)
   - 47 mm² at (175–193, 128–140)
   - 36 mm² at (145–155, 116–126)
   - 22 mm² at (160–170, 114–119)

   About 120 mm of B.Cu track runs under those holes with no plane above it.

   This also removes the worst crosstalk case on the board: MUX_RST picks up −141 mV under TOF4_SCL, where the two are stacked between In2 and B.Cu.

## Differential pairs

3. **Route the RS-485 pairs side by side on F.Cu.**
   - Port A: A is 24.7 mm, B is 28.0 mm with 6.1 mm on B.Cu and 3 vias.
   - Port B: 28.2 / 31.1 mm.
   - Today the wires are never within 0.8 mm of each other; median spacing is 1.8 mm (A) and 2.9 mm (B).
4. **Route the CAN pair side by side on F.Cu.**
   - CAN_H is 23.4 mm. CAN_L is 33.7 mm, 10.3 mm longer, with 18.8 mm on B.Cu.
   - Only 40% coupled.
   - Keep the order: J19, then D12, then U16.

## Grounding and decoupling

5. **Add GND vias at 38 ground pads** that have none within 1.5 mm. The worst:
   - MCU: U3.15 at 4.2 mm (153.3, 140.2), U3.27 at 2.9 mm, U3.47 at 2.3 mm.
   - ESD clamps: U8, U9, U10 and U11 pin 3 at 2.3–2.8 mm, pin 8 at 1.95 mm; U5.3 at 2.0 mm.
   - Mux: U6.21 at 2.5 mm, U6.12 at 2.1 mm.
   - Caps: C29 2.8, C31 2.3, C11 2.3, C12 2.1, C13 2.0, C14 1.9 mm.
6. **Move decoupling caps closer.**
   - C15 is 5.5 mm from U6.24 (mux VCC, at (144.9, 118.4)).
   - C30 is 9.9 mm from U13.5 (USB ESD VBUS). It moves with item 1 anyway.
   - U3's VDD caps are 2.3–2.7 mm from their pins; the guideline is 2 mm.
7. **Close the stitching gaps on the bottom edge.** They are 18 mm (x 137.7–155.7) and 27 mm (x 157.7–184.7). The other edges are at most 9.7 mm.
8. **Crystal window.** Move these off the area around Y1:
   - the VBAT_SENSE B.Cu run (3.7 mm) and its via at (152.0, 137.0)
   - the PGOOD via at (152.0, 140.6)

   They're outside the keep-out and shielded by In1, so this is tidy-up only. The USB pair also runs 8 mm through this window on In2; item 1 fixes that.

## ESD placement

9. **Move the sensor-jack ESD clamps closer to the jacks.**
   - 8 of the 16 mux-jack lines are 17.3–17.4 mm from jack to clamp, against a target under 15 mm: ENC1_SDA, ENC2_SCL, LASER_SDA, TOF1_SCL, TOF2_SDA, TOF3_SCL, TOF4_SDA, MUX7_SCL.
   - J5 (IMU) lines are 13.5–19.4 mm, and J14 lines 19.7–22.1 mm.
   - The order (jack, clamp, then IC) is already right on all 31 protected nets.

## Fab margins and silkscreen

10. **Footprint silk lines from 0.12 mm to 0.15 mm.** All 635 are 0.12 mm, under the PCBWay and JLCPCB minimum, so they may print faint or broken.
11. **Text at 1.0 mm tall if the board might go to JLCPCB.** It's 0.8 mm now, which only PCBWay (or JLCPCB's high-precision option) prints.
12. **Vias with a 0.2 mm ring,** for example 0.6 / 0.2 mm or 0.7 / 0.3 mm. The current 0.6 / 0.3 mm leaves a 0.15 mm ring: the minimum at both fabs, and JLCPCB recommends 0.20 mm.
13. **Print more reference designators.** 79 are on F.Fab only: the passives in the crowded middle, U1, U5, U15, U17 and Y1. A looser rev B layout should fit most of them.
14. **Board text revision.** The copper text says "UWAT VEXU - F26 - REV 1.1", while the files call this rev A. Pick one scheme and use it on both.

## Routing cleanup

15. **Remove duplicate copper.** There are 16 fully overlapped segments, 5 of them exact duplicates; the most are on I2C_AUX_SDA, around (166.8–168.7, 121.6–122.8). GND, +5V and +3.3V have some too.

    21 of the 204 small filler zones fill nothing. Both are harmless, but they make editing confusing.
16. **Shorten the worst detours** (routed vs straight-line, mm):

    | Net | Routed | Straight-line |
    |---|---|---|
    | SPARE_MISO | 90.5 | 31.0 |
    | SPARE_MOSI | 73.0 | 29.2 |
    | RAMBAR_RX | 87.3 | 37.6 |
    | RS485B_RX | 77.5 | 39.8 |
    | JETSON_TX | 75.2 | 38.0 |
    | AUX1_SIG | 72.9 | 32.2 |
    | SPARE_INT | 67.1 | 32.0 |
    | VBAT_SENSE | 44.9 | 19.4 |
    | CAN_L | 33.7 | 15.6 |
17. **RAMBAR_RX:** U17.4 hangs on a 2.4 mm stub off J19.3. Route the line through the clamp pad instead.
18. **SENS_3V3** narrows to 0.15–0.2 mm mid-run, for example at (166.9, 120.2). That's fine for F2's 0.5 A, but widen it to the 0.3 mm class width where there's room.
19. **Bottom-layer signals:** 1.34 m of signal track is on B.Cu. Long runs away from the edge are +3.3V (18 mm at x 127.8, y 137–155) and +5V (16.6 mm). With item 2 done, these at least get a solid plane above them.

## Circuit (from the simulations)

20. **Sensor hot-plug.** Plugging a breakout into a live 3.3 V jack pulls SENS_3V3 down to 0.75–2.1 V for about 5 µs. That can reset the other sensors and the IMU. Rev A's rule is to plug sensors in with the board off ([sim/README.md](sim/README.md)). For rev B, consider a per-jack inrush limit, such as a load switch with soft start, or a small series resistor and local cap.
21. **IMU SPI over the cable.** At the fastest GPIO speed, MISO picks up 0.88 V of crosstalk in the cable, against a 0.99 V threshold. Rev A handles it with firmware (SPI1 pins at GPIO speed low), R8/R9/R41 at 100 Ω, and R1 on the IMU board. For rev B, a twisted or ground-separated cable, or GND wires between the signals in the pinout, would remove the firmware dependency.
