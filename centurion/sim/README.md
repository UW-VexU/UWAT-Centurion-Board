# centurion simulations

Two sets, both run with the ngspice that ships with KiCad 10 (or open any `.cir` in LTspice):

- [Connector simulations](#connector-simulations): every cable connector, with its real parts, its routed trace lengths and a model cable. Added 2026-11-04.
- [USB hot-plug](#usb-hot-plug): the 5V_LDO spike when USB is plugged in, which led to C33.

## USB hot-plug

`usb_hotplug.cir`: a live USB host port plugged into J16 (USB-C) while the smart ports are unpowered, so USB alone feeds the 3.3 V side. The cable inductance rings with the capacitance on `/Power/5V_LDO`. The question is how high 5V_LDO gets: U7 (MCP1826S) is rated 6.5 V absolute maximum (Microchip DS22057B).

**Result:** without a bulk cap, U7's input goes over 6.5 V in the worst case once the cable loop is about 1 uH or more (roughly a 1 m cable or longer). It reaches 7.2 V at 2 uH and stays there until the board drains it, because D10 stops any current flowing back. **C33 was added on 2026-11-04 for this:** a 47 uF polymer tantalum (KEMET T520B476M010ATE070, 70 mOhm) on 5V_LDO next to Q1. With it, U7 stays at 5.5 V or less in every case simulated.

### Circuit

- Host: a VBUS step (`VHOST`) behind `RHOST` (its bulk cap and ESR), then the cable loop (`LCAB`, `RCAB`) to J16 VBUS.
- On VBUS: C30 (100 nF), R46/R47 (10k/15k to PB2, VBUS_SENSE), R48 (5.1k bleeder), U13's VBUS clamp (USBLC6-2SC6, switchable).
- D10 (SS14) to USB_PWR, then Q1 (AO3401A P-FET, gate on +5V, which sits at 0 V with the smart ports off) to 5V_LDO.
- C33 sits at Q1's source. The 5V_LDO trace (about 60 mm, `LTR`, `RTR`) then runs to C16 (10 uF ceramic, about 9.6 uF at 5 V), D9 and U7.
- U7 is either off (the bound) or a behavioural LDO that charges the +3.3V caps (about 48 uF) at up to 1.4 A.
- Every part in the netlist has a comment with its value and where the value came from.

### Run it

- **ngspice (installed with KiCad 10):** run these with KiCad's Python, `C:\Program Files\KiCad\10.0\bin\python.exe`.
  - `run_ngspice.py usb_hotplug.cir LCAB=2u FIX=1 FIXAT=1 CB=47u RB=70m` runs one case and prints the peak of every node.
  - `sweep_usb_hotplug.py` runs every case below and writes `results.json`.
  - `plot_usb_hotplug.py LCAB=1u` draws `usb_hotplug_1u.png`.
- **LTspice:** File > Open, set the type to Netlists, pick `usb_hotplug.cir`, and Run. It steps `LCAB` over 0.3 to 2 uH. Probe `V(ldoin)`, which is U7's input.

| Parameter | Default | What it does |
|---|---|---|
| `VHOST` | 5.5 | Host VBUS. USB 2.0 is 4.75 to 5.25 V; USB-C vSafe5V goes to 5.5 V. |
| `RHOST` | 20m | Host output impedance. |
| `LCAB` | 1u | Cable loop inductance, VBUS plus GND. About 0.5 to 1 uH per metre. |
| `RCAB` | 0.07 | Cable plus contacts, VBUS plus GND. 0.07 is a short, thick cable; 0.2 is typical. |
| `CLAMP` | 0 | 1 lets U13's VBUS clamp conduct from 6 V. |
| `LDO` | 0 | 1 lets U7 start and load its input. |
| `FIX`, `CB`, `RB` | 0, 47u, 0.3 | 1 adds a capacitor `CB` with series resistance `RB`. The default netlist is the board without C33. |
| `FIXAT` | 0 | Where the capacitor sits: 0 at C16 and U7, 1 at Q1 (where C33 is). |
| `LTR`, `RTR` | 50n, 0.05 | The 5V_LDO trace from Q1 to C16 and U7. |

### Results

Peak `V(5V_LDO)` at U7 in volts. U7's absolute maximum is 6.5 V.

**Worst corner:**
- Host: 5.5 V with 20 mOhm.
- Cable: 0.07 ohm.
- Protection: U13 not clamping, and U7 not loading its input.

| On 5V_LDO | 0.3 uH | 0.5 uH | 1 uH | 1.5 uH | 2 uH |
|---|---|---|---|---|---|
| Without C33 (C16 only) | 5.51 | 5.90 | **6.55** | **6.95** | **7.23** |
| Without C33, U13 clamping | 5.51 | 5.90 | **6.55** | **6.95** | **7.22** |
| Without C33, U7 loading | 5.24 | 5.49 | 6.07 | 6.42 | **6.66** |
| **With C33 (47 uF, 70 mOhm, at Q1), as built** | **5.29** | **5.29** | **5.29** | **5.33** | **5.52** |
| 47 uF, 0.05 ohm, at C16 (C1's EEU-FR1H470, low end) | 5.28 | 5.29 | 5.29 | 5.30 | 5.35 |
| 47 uF, 0.15 ohm, at C16 | 5.28 | 5.28 | 5.28 | 5.28 | 5.29 |
| 47 uF, 0.3 ohm, at C16 | 5.26 | 5.26 | 5.27 | 5.27 | 5.27 |
| 47 uF, 0.7 ohm, at C16 | 5.22 | 5.22 | 5.22 | 5.22 | 5.22 |
| 47 uF, 1.5 ohm, at C16 | 5.14 | 5.14 | 5.36 | 5.54 | 5.65 |
| 22 uF, 0.5 ohm, at C16 | 5.30 | 5.30 | 5.30 | 5.30 | 5.31 |
| 100 uF, 0.5 ohm, at C16 | 5.07 | 5.07 | 5.07 | 5.08 | 5.08 |
| 22 uF polymer, 40 mOhm, at C16 | 5.31 | 5.32 | 5.36 | 5.65 | 5.91 |
| Snubber, 1 ohm + 22 uF ceramic, at C16 | 5.31 | 5.31 | 5.31 | 5.51 | 5.68 |

**Typical corner:**
- Host: 5.25 V with 50 mOhm.
- Cable: 0.2 ohm.
- Protection: U13 clamping, and U7 loading its input.

| On 5V_LDO | 0.3 uH | 0.5 uH | 1 uH | 1.5 uH | 2 uH |
|---|---|---|---|---|---|
| Without C33 | 4.98 | 4.98 | 4.98 | 5.03 | 5.13 |
| With C33, as built | 4.94 | 4.94 | 4.94 | 4.94 | 4.95 |

What else the runs show:

- **U13's VBUS clamp doesn't help.** ST only gives a 6 V minimum breakdown, and the clamp is soft above that, so it hardly conducts below 8 V.
- **U7 starting up only takes the edge off.** It loads its input once it starts, which lowers the peak by about 0.5 V.
- **The 5V_LDO trace helps a little.** Its 0.05 ohm damps the ring; leaving it out raises the bare-board peaks by about 0.35 V. C33 works the same whether it sits at Q1 or at C16: its 47 uF dwarfs the trace's 15 to 50 nH.
- **PB2 (VBUS_SENSE) is a 3.6 V-tolerant pin (TT_a, ST DS13122).** Without C33, the worst-case VBUS peak of 7.6 V puts up to 4.6 V on it through 6 kOhm. With C33, VBUS peaks at 5.5 to 6.05 V, so PB2 sees 3.6 V or less.
- **Inrush current.**
  - **Peak current.** With C33 it's 8 to 17 A for a few microseconds (12 A at most without it). That's fine for D10 (IFSM 40 A), Q1 (30 A pulsed) and C33 (T520 is 100% surge tested).
  - **Charge.** In the first 100 us the board takes about 180 uC without C33 and about 380 uC with it (typical corner, U7 charging +3.3V). USB 2.0 asks a device to look like no more than 10 uF (50 uC). The board already went over that before C33. It's common and works with laptops and the Jetson, but a hub port may see VBUS dip briefly when the board is plugged in.

### Assumptions

- Ideal step at 1 us with a 10 ns edge, no contact bounce. The host is a stiff source: it has at least 120 uF on VBUS by the USB spec. A host with a fast current-limiting VBUS switch would soften the edge.
- The cable's loop inductance is about 0.5 to 1 uH per metre. Its resistance is 0.07 ohm (short, thick, 5 A-class cable) to 0.2 ohm (typical 1 m cable).
- The 5V_LDO trace from Q1 to C16/U7 is 0.5 to 0.6 mm wide over the inner planes, up to about 60 mm: 50 nH and 0.05 ohm.
- C16: 9.6 uF at 5 V (Samsung DC-bias curve, as in `powerJackal/sim`), ESR 5 mOhm, ESL 0.5 nH.
- C33: 47 uF, ESR 70 mOhm at 100 kHz (KEMET T520 series), ESL 2 nH.
- D10 and D9: SS14 fit to about 0.40 V at 1 A and 0.75 V at 10 A (Vishay: 0.50 V max at 1 A).
- Q1: VDMOS model with the AO3401A's threshold (-0.9 V) and RDS(on) (50 mOhm at -4.5 V), body diode included.
- U13: soft Zener, 6.0 V at 1 mA, about 11 V at 1 A, 1.25 ohm (ST USBLC6-2: VBR 6 V min, VCL 12 V at 1 A and 17 V at 5 A).
- U7: behavioural LDO, 0.3 V dropout, 1.4 A current limit while it charges about 48 uF of +3.3V caps (C17 47 uF at about 30 uF under bias, C10 and C28, C18, eleven 100 nF), 60 mA board load.

### Sources

- Microchip MCP1826/MCP1826S datasheet, DS22057B: VIN absolute maximum 6.5 V.
- ST STM32G491 datasheet DS13122: PB2 is a TT_a (3.6 V-tolerant) I/O.
- ST USBLC6-2 datasheet: VBUS-to-GND breakdown 6 V minimum, clamping 12 V at 1 A and 17 V at 5 A.
- Vishay SS12 to SS16 datasheet: SS14 40 V, 1 A, VF 0.50 V at 1 A, IFSM 40 A.
- AOS AO3401A datasheet: VGS(th) -0.5 to -1.3 V, RDS(on) 50 mOhm at -4.5 V, 30 A pulsed.
- KEMET T520B476M010ATE070 (DigiKey Canada 399-4982-1-ND): 47 uF, 10 V, 70 mOhm at 100 kHz, 3528-21, polymer, 100% surge-current tested.
- Samsung CL32B106KBJNNNE characteristic sheet (DC bias), via `powerJackal/sim/README.md`.
- USB 2.0 specification section 7.2.4.1 (10 uF / 50 uC inrush) and USB Type-C vSafe5V (4.75 to 5.5 V).

## Connector simulations

Every connector that leaves the board was simulated: the I2C sensor jacks, the SPI ports, both UARTs, ramBar's CAN FD, the smart ports and the analog inputs. So was what happens to the supply rails when something is plugged into a powered jack or its supply pin is shorted. Each case is checked against a limit. `sim_connectors.py` runs all 180 cases and writes:

- every result to `connectors_results.md` and `connectors_results.json`;
- one plot per interface to `connectors_<group>.png`.

### Run it

- **Everything:** `sim_connectors.py`, with KiCad's Python. It takes about 10 minutes.
- **One group:** `sim_connectors.py spi`. The groups are i2c, spi, uart, can, rs485, power and adc.
- **One case:** `run_ngspice.py spi_imu.cir LEN=0.3 TRM=17n` prints the peak of every node.

| Deck | What it covers | Plot |
|---|---|---|
| `i2c_mux.cir` | J6 to J13: MCU pin, R11/R12, U6 TCA9548A, the jack's 2.7k pull-ups, U8 to U11, cable, sensor | `connectors_i2c.png` |
| `i2c_bus2.cir` | J14 and J18 together on bus 2: R32/R33 2.2k, U12, two cables | |
| `spi_imu.cir` | J5 (R8, R9, R41 at 100 ohm, U5) or J15 (`RSER=0`); `RSER=22` is J5's old value. SCK and MOSI out, MISO back. The cable is three coupled wires. | `connectors_spi.png` |
| `uart_link.cir` | J4 Jetson (`SIDE=0`) or J19 ramBar (`SIDE=1`, with R59 and U17), both directions | `connectors_uart.png` |
| `rambar_can.cir` | J19 CAN FD: U16, R53, D12, twisted pair, ramBar's transceiver and termination | `connectors_can.png` |
| `rs485_smartport.cir` | J1/J2: U14/U15, the R51 option, smart cable, the brain's receiver | `connectors_rs485.png` |
| `jack_power.cir` | Plugging a device into, or shorting, SENS_3V3, SENS_5V or J19's 5 V pin | `connectors_power.png` |
| `adc_inputs.cir` | AUX1 (J14 pin 5) and the pot (J17) into the ADC | |

`connectors.lib` holds the shared models.

### Results

| Interface | Verdict | What the runs show | What to do |
|---|---|---|---|
| I2C mux jacks, J6 to J13 | **OK to 2 m**, on 3.3 V or 5 V | <ul><li>Rise time (30 to 70 %) at the sensor: 87 to 154 ns at 0.3 to 1 m, 232 / 263 ns at 2 m (Fast-mode limit 300 ns).</li><li>The MCU sees 0.24 / 0.32 V low. The sensor sinks 1.8 / 2.4 mA (3.3 V / 5 V jack).</li></ul> | <ul><li>Cut the pull-ups on Qwiic/SparkFun boards. Their 2.2k makes the sensor sink 3.0 mA (3.3 V) or 4.3 mA (5 V), and the MCU sees 0.56 V low. Breakouts with 10k pull-ups are fine.</li><li>On 1 m and longer cables the sensor's clamp conducts briefly on falling edges, to about -0.8 V. That's harmless.</li></ul> |
| I2C bus 2, J14 and J18 | **OK to 1 m each** | Rise 126 / 243 ns with two 0.3 / 1 m cables, and 411 ns with two 2 m cables. | With cables on both connectors, keep each 1 m or less, or run bus 2 at 100 kHz. The same Qwiic rule applies. |
| SPI, J5 (IMU) | **OK to 0.3 m at any speed, 0.5 m at medium or low** | <ul><li>R8, R9 and R41 are 100 ohm since 2026-11-04 (they were 22 ohm).</li><li>0.1 and 0.3 m: OK at every GPIO speed. Crosstalk on MISO is 0.05 to 0.48 V at 0.1 m and 0.13 to 0.88 V at 0.3 m, against the MCU's 0.99 V VIL.</li><li>0.5 m: OK at medium and low. At high and very high, SCK rings back across the IMU's thresholds (extra clock edges).</li><li>1 m: extra SCK edges at every speed.</li><li>MISO setup at 10 MHz: 11 to 13 ns up to 0.3 m, 9 ns at 0.5 m, 0 to 3 ns at 1 m.</li><li>The IMU's clamps carry 1 to 7.5 mA on the overshoot.</li><li>With the old 22 ohm (still run as "old 22 ohm"), 0.3 m only worked at speed low, because the crosstalk reached 1.0 to 1.1 V at faster speeds, and 0.5 m failed at every speed.</li></ul> | <ul><li>Set the SPI1 pins to GPIO speed low anyway: at 0.3 m it keeps the crosstalk at 0.13 V instead of 0.88 V.</li><li>Keep the IMU cable at 0.3 m or less, 0.5 m at most.</li></ul> |
| SPI, J15 (spare) | **0.1 m, speed low** | No series resistors, so the far device's clamps carry 10 to 17 mA from 0.3 m up. 0.3 m at speed low works (no extra edges, 0.17 V crosstalk), with 10.6 mA in the clamps. | Set the SPI3 pins to speed low and keep the cable short. |
| UART, J4 (Jetson) | **Needs GPIO speed low** | <ul><li>At fast GPIO speed: 4.1 V at the Jetson's pin and 12 to 19 mA in its clamp.</li><li>At speed low: 3.5 V and no clamp current at 0.3 m; 1.3 mA at 1 m; about 10 mA at 2 m.</li></ul> | Set the USART1 TX pin to speed low and keep the cable 1 m or less. |
| UART, J19 (ramBar) | **OK** | R59 keeps the line clean: 3.3 V at most, no clamp current. Rise is 16 to 60 ns, which is fine to 3 Mbaud at 1 m or less and to 1 Mbaud at 2 m. | Nothing. |
| UART, unpowered far end | **Watch it** | A TX idling high into an unpowered Jetson or ramBar lifts that board's 3.3 V rail to 1.7 to 2.7 V through its RX clamp (0.03 to 2.5 mA). | Turn USART1 TX on only once the Jetson is up. Treat UART5 as in the firmware notes. |
| CAN FD, J19 | **OK** | All 18 cases pass (1, 2 and 5 Mbit/s; 0.5 to 2 m): every bit read correctly at 75 % with at least 0.5 V margin. At 5 Mbit/s the recessive bit after 5 dominant bits is 196 to 198 ns (ISO 11898-2 tBit(Bus): 155 to 210 ns). | ramBar still needs its 120 ohm. Without it the bus rings to 3 V, and it only works because the cable is short. |
| RS-485, J1/J2 | **OK** | All 18 cases pass (0.92 and 2 Mbaud; 0.3 to 2 m; with or without termination), with at least 1.5 V margin at mid-bit. | Leave R51/R52 unfitted. |
| Sensor plugged into a live jack | **Dips the shared rail** | <ul><li>A 10 uF breakout on a 3.3 V jack pulls SENS_3V3 to 1.3 to 2.1 V for about 5 us, depending on F2's resistance. A 22 uF one pulls it to 0.75 to 1.8 V. +3.3V itself stays above 2.7 V.</li><li>On a 5 V jack, SENS_5V drops to 1.2 to 3.1 V.</li><li>Inrush is 8 to 15 A peak.</li><li>C28/C29 at 100 uF only halve the dip.</li></ul> | Plug sensors in with the board off: the other sensors and the IMU share SENS_3V3 and can reset. |
| ramBar plugged in live | **Dips +5V** | With 47 to 220 uF on ramBar's input, +5V and SENS_5V dip to 2.5 to 4.4 V. +3.3V holds, thanks to D9 and C33. | Connect ramBar with the board off, or give ramBar an inrush limiter. |
| Short on a jack's VCC or J19 pin 1 | **Resets the board** | <ul><li>3.3 V jack: U7 hits its 2.2 A limit and +3.3V falls to 0.6 to 1.7 V.</li><li>5 V jack or J19: U1 hits about 3.1 A and +5V falls under 2 V, where U1 hiccups (94 ms off), or to 2.7 V.</li><li>The polyfuses take tens of ms or more to trip: MF-NSMF050 about 14 ms at 5 A, nothing specified at 2 to 3 A. U1's hiccup may keep them from ever heating up.</li></ul> | The polyfuses protect the cables, not the rails: a shorted sensor or ramBar cable resets centurion until it's unplugged or the fuse trips. If that matters, rev B could use current-limited load switches instead. |
| ADC, AUX1 and pot | **OK at 10 kS/s or slower** | <ul><li>At 10 kS/s per channel the error is -1.8 LSB (AUX1) and -0.5 LSB (pot). At 100 kS/s it's -9.7 / -4.5 LSB, because the ADC's sampling cap drains C31/C24 faster than the resistors refill them.</li><li>R55 gives a 1 % gain error with a 10k pot. R60 bows the reading by up to 6 counts.</li></ul> | Sample each at 10 kS/s or slower, or calibrate. |

Every check and its limit:

| Group | Limits |
|---|---|
| I2C | Rise (30 to 70 %) of 300 ns or less; sensor sink of 3 mA or less; low at the MCU of 0.4 V or less. |
| SPI | No extra SCK edges at the IMU (0.1 V hysteresis); MISO setup of at least 0 after the 4 ns tsu(MI); MISO crosstalk below VIL; IMU clamp of 10 mA or less. |
| UART | No extra edges; far-end rise of 20 % of a bit or less; far-end clamp of 10 mA or less; centurion's FT RX pin at VDD + 4 V or less. |
| Back-powering | 1 mA or less, and the far rail below 1 V. |
| CAN | Every bit correct at 75 % (0.5 / 0.9 V thresholds); no glitches; recessive bit within the ISO 11898-2 limits. |
| RS-485 | Every bit correct at 50 % (+/-0.2 V); no glitches. |
| Power | +3.3V and SENS_3V3 at 3.0 V or more; +5V and SENS_5V at 4.5 V or more. |
| ADC | 2 LSB or less. |

### Models and where the numbers come from

Shared models are in `connectors.lib`. Each value is a datasheet number unless marked as an estimate.

| Part | Model | Source |
|---|---|---|
| STM32G491 pins | Ideal edge behind 30 Ω (estimate), 5 pF, GND clamp. Edge per OSPEEDR at 10 pF: 00 17 ns, 01 4.5 ns, 10 2.5 ns, 11 1.7 ns. VIL/VIH 0.99/2.31 V. SPI MISO setup 4 ns. ADC CADC 5 pF, RADC about 0.75 kΩ (estimate, back-calculated from Table 61). | DS13122 Rev 4, Tables 53 to 55, 60, 61, 83 |
| TCA9548A (U6) | NMOS pass gate, gate at 3.3 V, fitted to Ron 12 Ω and Vpass 1.9 V (both typ). Cio 20 pF upstream, 5.5 pF per channel. | SCPS207H §5.5 |
| TPD4E05U06 (U5, U8 to U12, U17) | 0.5 pF, GND clamp only, breakdown 6.5 to 8.5 V. | SLVSBO7O, SLVSCO7C |
| NUP2105L (D12) | 26 pF per line (30 max), bidirectional, 24 V working, 26.2 V breakdown min. | onsemi NUP2105L/D Rev 12 |
| TCAN334G (U16 and ramBar's) | Dominant CANH 2.93 V, CANL 0.87 V, VOD 2.05 V into 60 Ω (datasheet: CANH ≥ 2.45 V, CANL 0.5 to 1.25 V, VOD 1.6 to 3.0 V). Recessive 1.85 V through 25 kΩ. 20 pF per pin. Driver edge 15 ns (datasheet tr 17 ns, tf 9 ns typ). Receiver 0.5/0.9 V. | SLLSEQ7F |
| MAX33071E (U14, U15) | VOD 1.62 V into 54 Ω, 2.1 V into 100 Ω (min 1.5/2.0 V). Edges 12 ns (8 typ, 15 max). RIN 96 kΩ, 50 pF across A-B. | ADI 19-100900 Rev 2 |
| BMI270 (IMU on J5) | 5 pF inputs. Data out 30 ns after SCK (tSDO max). 40 Ω output (estimate: not given). Abs max on its pins: VDDIO + 0.3 V, so 3.6 V. SPI 10 MHz max. | BST-BMI270-DS000-08 |
| Polyfuses | Cold resistance only. MF-NSMF050 (F2, F3): 0.15 to 0.70 Ω, trips in ≤ 0.1 s at 8 A (typ about 14 ms at 5 A). MF-NSMF075 (F4): 0.10 to 0.40 Ω, ≤ 0.2 s at 8 A (typ about 30 ms at 5 A), 6 V max. | Bourns MF-NSMF Rev AF |
| U1 TPSM53602 | 5.0 V, current limit 3.5 A (typ), output caps about 60 µF. Below 2.0 V out it hiccups (94 ms off). The hiccup itself isn't simulated; the run flags it. | SNVSBD0B |
| U7 MCP1826S | Dropout 0.25 V, current limit 2.2 A (typ into a short). | DS22057B |
| JST GH cable (estimate) | One wire over its return: 0.66 µH and 46 pF per metre (120 Ω, 5.5 ns/m, a heavy cable). A light cable, 30 pF/m and 150 Ω, is also run for overshoot. For SPI, three side-by-side wires (SCK, MOSI, MISO) with 0.9 µH/m each, 25 pF/m to the return, 15 pF/m between neighbours and k = 0.5. The only GND wire on J5 is pin 2. 28 AWG copper. | Parallel-wire formulas; 3M 3365 ribbon listing as a cross-check |
| VEX smart cable (estimate) | Flat 4-wire modular cable, 100 Ω differential, 5 ns/m. | Same |
| On-board traces | Lumped: 0.3 nH and 0.15 pF per mm (0.15 to 0.25 mm over the 0.1 mm prepreg), with lengths measured from the routed board. | `centurion.kicad_pcb` |

### What these models leave out

- **SPI cable coupling is an estimate.** The crosstalk figures scale with it.
  - The overshoot doesn't depend on it. With no coupling at all, a 0.3 m cable still rings to 4.6 V at the IMU with the old 22 ohm: a 52 ohm source drives a cable of about 130 ohm.
  - That's why R8, R9 and R41 are now 100 ohm, about 130 ohm with the pin's own resistance. Slow edges help too.
- **Fuse trips and U1's hiccup aren't simulated.** The polyfuses are fixed resistors, and the trip times above come from the datasheet curves. U1 never hiccups in the run; the run only flags when +5V drops below 2 V.
- **Transceivers are behavioural.** They have the datasheet's levels, edges and input loads, but no loop delay. Receivers are capacitors plus generic clamp diodes.
- **Cables are 10-section ladders.** They're good to a few hundred MHz, which covers edges down to about 1.5 ns. ngspice's lossless T line stalls on these runs, so it isn't used.
- **The ADC case is the worst case.** Each sample starts from 0 V, as if a 0 V channel was converted just before it.

## Crosstalk and return paths

Checked 2026-11-04 on the autorouted board, before hand routing. Rerun these after the board changes.

### Run it

| Step | Command | What it does |
|---|---|---|
| 1 | `xtalk_scan.py ../centurion.kicad_pcb` | Finds every pair of nets that run side by side within 0.75 mm on F.Cu or B.Cu. Also lists signal vias far from a ground via, signal length on B.Cu, signals over a gap in their reference plane, and what passes near Y1. Writes `xtalk_scan.json` |
| 2 | `xtalk_inner.py ../centurion.kicad_pcb` | The same for traces routed on In2.Cu, both side by side and stacked over B.Cu. Writes `xtalk_inner.json` |
| 3 | `xtalk_sim.py` | Simulates the worst pairs with `xtalk_pair.cir`, using the real driver and load on each victim |
| 4 | `xtalk_plot.py` | Plots the four worst cases to `xtalk_worst.png`: victim noise in mV at both ends, with the aggressor's edge for timing |

Run all three with KiCad's Python, from this folder.

### Stackup

Top-layer traces sit 0.1 mm over In1, which is a solid GND plane. Bottom-layer traces sit 0.1 mm under In2, the +3.3V plane. A trace that close to a plane keeps its field tight, so side-by-side crosstalk is small.

### Results

- **Side-by-side crosstalk is small.**
  - 172 net pairs run within 0.75 mm of each other. The Johnson and Graham estimate gives at most about 5 mV of noise on any of them.
  - The simulation of the worst cases gives:

    | Victim | Aggressor | Noise |
    |---|---|---|
    | MUX_RST idling on R10 | RS485A_DE, 16.8 mm alongside | −30 mV |
    | AUX1_SIG at the ADC | RS485B_TX, 9.3 mm alongside | ±10 mV spikes a few ns long, which C31 filters |
    | RS485A_RX | RS485A_TX | 12 mV |
    | AUX1_SIG_IN | I2C_AUX_SCL | −10 mV |

- **The worst single spot is stacked coupling on In2.** TOF4_SCL runs on In2 for 3.9 mm directly under MUX_RST on B.Cu, 0.1 mm apart. A falling SCL edge pulls the idle MUX_RST down by about 140 mV. The mux only resets below about 1.0 V, so there is still 2 V of margin.
- **The crystal is clean.** OSC_IN is 7.4 mm and OSC_OUT 5.7 mm. Within 4 mm of Y1 there are only slow or static nets (VBAT_SENSE, PGOOD, NRST, POT_SIG), and no clocks or data lines.
- **The top layer has a solid reference everywhere.** Every place a top-layer trace seems to leave the In1 plane is just the clearance hole around a via.
- **In2 is not a solid plane.** The autorouter put 306 mm of signal traces on In2. The longest are USB D+ and D−, about 58 mm each, running across the middle of the board. Each In2 trace cuts a slot in the +3.3V plane.
  - Ten B.Cu signals cross the USB slot. Most have no GND pour beside them, so at the crossing their return current has to go around the slot or jump planes through decoupling caps. They are MUX_RST, I2C_MUX_SCL, VBUS_SENSE, POT_SIG, NRST, SWO, RS485A_DE, IMU_INT2, IMU_CS and +5V.
  - All of them are slow (I2C, control lines, an interrupt, chip select, sense lines), so in practice this means a little more noise and EMI rather than errors.
  - **Moving the pair off In2 was tried on 2026-11-04 and doesn't fit.** Three attempts, all in a scratch copy:
    - **Grid router:** USB D- found no path on F.Cu or B.Cu.
    - **Freerouting, full middle reroute** with In1 and In2 closed: about 160 of 192 connections stayed unrouted after 20 passes.
    - **Freerouting, a 2.5 mm band** around the USB path: about 190 of 310 stayed unrouted.
  - **The cause is placement.** J16 (USB-C) is on the left edge, and the MCU's USB pins (U3 45 and 46) are on its right side. That leaves about 60 mm across the MCU fan-out, where F.Cu and B.Cu are full.
  - **Rev A keeps the pair on In2.** The simulations above show the slot is harmless for these slow nets.
  - **For rev B,** put J16, U13 and R38/R39 near U3's right side. The pair is then about 10 to 15 mm long on F.Cu, and In2 stays solid.

### What these checks leave out

The coupling coefficients are textbook estimates, not a field solve. The simulations model each pair alone, with no third net nearby. Simultaneous switching through the planes is not modelled.
