# centurion USB hot-plug simulation

`usb_hotplug.cir`: a live USB host port plugged into J16 (USB-C) while the smart ports are unpowered, so USB alone feeds the 3.3 V side. The cable inductance rings with the capacitance on `/Power/5V_LDO`. The question is how high 5V_LDO gets: U7 (MCP1826S) is rated 6.5 V absolute maximum (Microchip DS22057B).

**Result:** without a bulk cap, U7's input goes over 6.5 V in the worst case once the cable loop is about 1 uH or more (roughly a 1 m cable or longer). It reaches 7.2 V at 2 uH and stays there until the board drains it, because D10 stops any current flowing back. **C33 was added on 2026-11-04 for this:** a 47 uF polymer tantalum (KEMET T520B476M010ATE070, 70 mOhm) on 5V_LDO next to Q1. With it, U7 stays at 5.5 V or less in every case simulated.

## Circuit

- Host: a VBUS step (`VHOST`) behind `RHOST` (its bulk cap and ESR), then the cable loop (`LCAB`, `RCAB`) to J16 VBUS.
- On VBUS: C30 (100 nF), R46/R47 (10k/15k to PB2, VBUS_SENSE), R48 (5.1k bleeder), U13's VBUS clamp (USBLC6-2SC6, switchable).
- D10 (SS14) to USB_PWR, then Q1 (AO3401A P-FET, gate on +5V, which sits at 0 V with the smart ports off) to 5V_LDO.
- C33 sits at Q1's source. The 5V_LDO trace (about 60 mm, `LTR`, `RTR`) then runs to C16 (10 uF ceramic, about 9.6 uF at 5 V), D9 and U7.
- U7 is either off (the bound) or a behavioural LDO that charges the +3.3V caps (about 48 uF) at up to 1.4 A.
- Every part in the netlist has a comment with its value and where the value came from.

## Run it

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

## Results

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

## Assumptions

- Ideal step at 1 us with a 10 ns edge, no contact bounce. The host is a stiff source: it has at least 120 uF on VBUS by the USB spec. A host with a fast current-limiting VBUS switch would soften the edge.
- The cable's loop inductance is about 0.5 to 1 uH per metre. Its resistance is 0.07 ohm (short, thick, 5 A-class cable) to 0.2 ohm (typical 1 m cable).
- The 5V_LDO trace from Q1 to C16/U7 is 0.5 to 0.6 mm wide over the inner planes, up to about 60 mm: 50 nH and 0.05 ohm.
- C16: 9.6 uF at 5 V (Samsung DC-bias curve, as in `powerJackal/sim`), ESR 5 mOhm, ESL 0.5 nH.
- C33: 47 uF, ESR 70 mOhm at 100 kHz (KEMET T520 series), ESL 2 nH.
- D10 and D9: SS14 fit to about 0.40 V at 1 A and 0.75 V at 10 A (Vishay: 0.50 V max at 1 A).
- Q1: VDMOS model with the AO3401A's threshold (-0.9 V) and RDS(on) (50 mOhm at -4.5 V), body diode included.
- U13: soft Zener, 6.0 V at 1 mA, about 11 V at 1 A, 1.25 ohm (ST USBLC6-2: VBR 6 V min, VCL 12 V at 1 A and 17 V at 5 A).
- U7: behavioural LDO, 0.3 V dropout, 1.4 A current limit while it charges about 48 uF of +3.3V caps (C17 47 uF at about 30 uF under bias, C10 and C28, C18, eleven 100 nF), 60 mA board load.

## Sources

- Microchip MCP1826/MCP1826S datasheet, DS22057B: VIN absolute maximum 6.5 V.
- ST STM32G491 datasheet DS13122: PB2 is a TT_a (3.6 V-tolerant) I/O.
- ST USBLC6-2 datasheet: VBUS-to-GND breakdown 6 V minimum, clamping 12 V at 1 A and 17 V at 5 A.
- Vishay SS12 to SS16 datasheet: SS14 40 V, 1 A, VF 0.50 V at 1 A, IFSM 40 A.
- AOS AO3401A datasheet: VGS(th) -0.5 to -1.3 V, RDS(on) 50 mOhm at -4.5 V, 30 A pulsed.
- KEMET T520B476M010ATE070 (DigiKey Canada 399-4982-1-ND): 47 uF, 10 V, 70 mOhm at 100 kHz, 3528-21, polymer, 100% surge-current tested.
- Samsung CL32B106KBJNNNE characteristic sheet (DC bias), via `powerJackal/sim/README.md`.
- USB 2.0 specification section 7.2.4.1 (10 uF / 50 uC inrush) and USB Type-C vSafe5V (4.75 to 5.5 V).
