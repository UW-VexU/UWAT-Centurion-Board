# powerJackal hot-plug simulation

Two netlists:

- `hotplug.cir`: a charged V5 battery (14.6 V) plugged into J1, the smart port, through a smart cable.
- `hotplug_bench.cir`: a live 15 V bench supply connected to J2 on long leads.

In both, the lead inductance rings with the VIN_MOD capacitors. The question is how high VIN_MOD gets, and whether D1 (SMBJ16A) keeps U1 and U2 safe.

Result: with C1 fitted, VIN_MOD stays at or under 15.0 V on the smart port and 19.0 V on the bench. U1 is rated 38 V. D1 barely conducts. The board is safe as drawn. No change is needed. C1 does most of the damping, so keep it fitted.

## Circuit

- Smart port: battery (14.6 V step plus `RSRC`) > cable (`LCAB`, `RCAB`) > J1 pin 4 (VPORT) > D5 > VIN_OR.
- Bench: supply (15 V step plus `RPSU`) > leads (`LLEAD`, `RLEAD`) > J2 pin 1 (BENCH_IN) > D3 > VIN_OR.
- Then VIN_OR > F1 > VFUSE > R1 (20 mOhm shunt) > VIN_MOD.
- On VIN_MOD: C1 (47 uF electrolytic), C2 and C3 (10 uF ceramics), C8, D1, U1 (as a 10 mA load), U2 VBUS and IN-.
- R8 and LED1 hang on VIN_OR. The unused input (J2 or J1) is left open.
- Every part in the files has a comment with its value and where the value came from.

## Run it in LTspice

1. File > Open, set the file type to Netlists, and pick `hotplug.cir` or `hotplug_bench.cir`.
2. Click Run. `hotplug.cir` steps `LCAB` over 0.3 to 3 uH. `hotplug_bench.cir` steps `LLEAD` over 0.5 to 4 uH. Each length runs with D1 removed and fitted.
3. Probe `V(vinmod)`. That is the input rail at TP2, U1 VIN and EN, U2 and D1.
4. Other useful traces: `V(vfuse)` is U2 IN+. `I(V_ID1)` is the D1 current. `I(V_IF1)` is the inrush current. `V(vinor)` is the OR node.
5. View > SPICE Error Log lists the `.meas` results for each step. VIN_PK is the peak rail voltage. ED1 is the D1 energy in joules.

Change a `.param` line to try another case:

| Parameter | Default | What it does |
|---|---|---|
| `RSRC` (port) | 50m | Battery and brain resistance. Try 200m. |
| `KLINK` (port) | 0 | 0 keeps the cable at 0.1 ohm for any length (worst case). 1 adds 28 AWG resistance for the length that gives `LCAB`. |
| `RPSU`, `RLEAD` (bench) | 20m, 50m | Supply output resistance and lead resistance. |
| `RPTC` | 0.07 | F1 resistance. 0.07 is Rmin, 0.18 is R1max. |
| `ESRC1` | 0.05 | C1 ESR. Panasonic allows up to 0.14 ohm. |
| `TVS` | 1 | 0 removes D1. |
| `TVSC` | 1 | 1 is a high-breakdown SMBJ16A (19.7 V). 0 is a low one (17.8 V). |
| `CNL` | 1 | 1 uses the C2 and C3 DC-bias curve. 0 uses a fixed value. |

To see the board without C1, put a `*` in front of the `R_C1`, `L_C1` and `C_C1` lines.

## Run it in ngspice

ngspice does not know `.step`. Put a `*` in front of the `.step` lines and it runs one case. The plain `.meas` lines work. The ones with an expression fail with a harmless warning. The numbers below came from ngspice (the copy in KiCad 10), driven from Python with one run per case.

## Results, smart port (J1)

Worst case damping: `RSRC` 50 mOhm, cable 0.1 ohm at every length, F1 at Rmin (0.07 ohm), C1 ESR 0.05 ohm. "D1 peak current" and "D1 energy" are the larger of the two D1 corners.

| Loop L | No D1, C(V) | No D1, fixed C | D1 high VBR | D1 low VBR | Inrush peak | D1 peak current | D1 energy |
|---|---|---|---|---|---|---|---|
| 0.3 uH | 14.4 V | 14.4 V | 14.4 V | 14.4 V | 43 A | 0 | 0 |
| 0.5 uH | 14.4 V | 14.4 V | 14.4 V | 14.4 V | 41 A | 0 | 0 |
| 1 uH | 14.4 V | 14.4 V | 14.4 V | 14.4 V | 38 A | 0 | 0 |
| 1.5 uH | 14.4 V | 14.4 V | 14.4 V | 14.4 V | 35 A | 0 | 0 |
| 2 uH | 14.4 V | 14.4 V | 14.4 V | 14.4 V | 34 A | 0 | 0 |
| 3 uH | 15.0 V | 15.0 V | 15.0 V | 15.0 V | 31 A | 0 | 0 |

Cable resistance that grows with length, `RSRC` 200 mOhm, or F1 and C1 ESR at their maximum: 14.4 V or less. No overshoot.

Without C1: 16.3 V at 1 uH, 18.8 V at 2 uH, 20.4 V at 3 uH. D1 (low corner) then takes 2.3 A and 0.44 mJ at 3 uH.

## Results, bench input (J2)

Worst case damping: supply 20 mOhm, leads 50 mOhm, F1 at Rmin, C1 ESR 0.05 ohm.

| Lead L | No D1, C(V) | No D1, fixed C | D1 high VBR | D1 low VBR | Inrush peak | D1 peak current | D1 energy |
|---|---|---|---|---|---|---|---|
| 0.5 uH | 14.8 V | 14.8 V | 14.8 V | 14.8 V | 54 A | 0 | 0 |
| 1 uH | 14.8 V | 14.8 V | 14.8 V | 14.8 V | 48 A | 0 | 0 |
| 2 uH | 16.0 V | 15.9 V | 16.0 V | 16.0 V | 41 A | 0 | 0 |
| 3 uH | 17.1 V | 17.1 V | 17.1 V | 17.1 V | 37 A | 0 | 0 |
| 4 uH | 18.0 V | 17.9 V | 18.0 V | 18.0 V | 35 A | 3 mA | 0.02 mJ |

Stiffer supply and leads (10 mOhm and 30 mOhm): 19.0 V at 4 uH, 60 A inrush at 0.5 uH, D1 93 mA and 0.35 mJ.

Without C1 (same damping as the main table):

| Lead L | No D1 | D1 high VBR | D1 low VBR | D1 peak current | D1 energy |
|---|---|---|---|---|---|
| 1 uH | 19.4 V | 19.4 V | 19.4 V | 0.36 A | 0.21 mJ |
| 2 uH | 22.2 V | 22.2 V | 20.7 V | 7.9 A | 0.91 mJ |
| 4 uH | 25.0 V | 24.0 V | 21.0 V | 11.4 A | 1.73 mJ |

## Ratings on the VIN_MOD rail

D5 or D3 stops the current once VIN_MOD passes its peak, so the rail holds near the peak until the load drains it. So the peak is compared against the DC rating.

| Part | Rating | Worst seen, C1 fitted | Margin | Worst seen, no C1 |
|---|---|---|---|---|
| U1 TPSM53602 VIN | 38 V abs max, 36 V recommended | 19.0 V | 19.0 V | 25.0 V |
| U1 EN (tied to VIN) | VIN + 0.3 V | equal to VIN | met | met |
| U2 INA226 VBUS, IN+, IN- | 40 V | 19.1 V | 20.9 V | 25.0 V |
| U2 IN+ to IN- | 40 V | 1.2 V | 38.8 V | 0.9 V |
| C1 EEU-FR1H470 | 50 V | 19.0 V | 31.0 V | n/a |
| C2, C3 CL32B106KBJNNNE | 50 V | 19.0 V | 31.0 V | 25.0 V |
| C8 CC0805KRX7R9BB104 | 50 V | 19.0 V | 31.0 V | 25.0 V |
| D3, D5 B340A, reverse | 40 V | 9.8 V | 30.2 V | 25.1 V |
| D3, D5 surge | IFSM 100 A (8.3 ms) | 60 A, 14 us wide at half height | 40 A | 46 A |
| F1 2016L150/33DR | 33 V, 40 A | 6.7 V across it, 60 A for about 14 us | 26 V | n/a |
| D1 SMBJ16A | 600 W at 10/1000 us | 93 mA, 0.35 mJ | over 99% | 11.4 A, 1.73 mJ |

F1's 40 A is the fault current it can interrupt at 33 V. A 14 us inrush with under 7 V across it does not trip it and is not that stress. Its I2t is under 0.04 A2s. D1 at 11.4 A for about 11 us is about 240 W. Its pulse rating at that width is about 5.7 kW.

## Assumptions

- Smart port: battery at 14.6 V with 50 to 200 mOhm for the battery and brain. 4-conductor flat cable, 28 AWG, about 0.75 uH/m loop inductance, 0.2 uH of the loop in the battery lead and brain. The worst case keeps the cable at 0.1 ohm at every length.
- Bench: 15 V, the top of the J2 range. The supply output cap makes it a stiff source. Two loose 1 m leads are about 1 to 2 uH. 4 uH is an upper bound.
- Ideal step, no contact bounce.
- F1 is a fixed resistor. Its thermal time constant is milliseconds.
- C1: 47 uF, ESR 0.05 to 0.14 ohm, ESL 8 nH. Panasonic gives 0.14 ohm max impedance at 100 kHz. The real ESR is not published, so it is bracketed.
- C2 and C3: DC-bias curve read from Samsung's characteristic sheet for CL32B106KBJNNNE. Fit: C(V) = C0/(1+(V/24)^2). ESR 5 mOhm each. Tolerance and temperature not included.
- D1 model: 17.8 to 19.7 V at 1 mA, 26.0 V at 23.1 A (10/1000 us), under 1 uA at 16 V.
- D3 and D5: fit to about 0.41 V at 3 A.
- U1 is a 10 mA load while it starts. U2 input currents are ignored.
- The D1 pulse rating at short widths scales the 600 W, 1 ms rating by the square root of the width.

## Sources

- TI TPSM53602 datasheet, SNVSBD0B: VIN 38 V abs max, EN up to VIN + 0.3 V, 36 V recommended, 20 uF minimum ceramic input.
- TI INA226 datasheet, SBOS547C: IN+, IN- and VBUS -0.3 to 40 V, differential +/-40 V.
- Diodes Inc B320/A/B to B360/A/B datasheet, DS13005 Rev. 9-2: B340A 40 V, 3 A, IFSM 100 A, VF 0.50 V at 3 A.
- Littelfuse 2016L series table (as listed by DigiKey and Farnell): 2016L150/33 1.5 A hold, 3 A trip, 33 V, 40 A, Rmin 0.07 ohm, R1max 0.18 ohm. Littelfuse's own PDF could not be downloaded.
- SMBJ16A JEDEC ratings (as listed by Future Electronics for the Littelfuse part, and matching Bourns' SMAJ16A row): VBR 17.8 to 19.7 V at 1 mA, VC 26.0 V at 23.1 A, 600 W. Littelfuse's own PDF could not be downloaded.
- Panasonic product page for EEU-FR1H470: 47 uF, 50 V, 0.14 ohm max at 100 kHz.
- Samsung Electro-Mechanics characteristic sheet for CL32B106KBJNNNE: DC bias, ESR.
