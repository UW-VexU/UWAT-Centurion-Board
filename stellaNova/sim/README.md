# stellaNova hot-plug simulation

`hotplug.cir` simulates plugging a charged V5 battery (14.6 V) into J1 through a smart cable. The cable inductance rings with C1. The question is how high VIN gets, and whether D1 (SMAJ18A) keeps U2 safe.

Result: VIN stays at or under 20.9 V in every case with F1 in place. U2 is rated 35 V. D1 barely conducts. The board is safe as drawn. No change is needed.

## Circuit

- Battery: an ideal 14.6 V step with series resistance `RSRC`.
- Cable: loop inductance `LCAB` and resistance `RCAB`. The VBAT and GND wires are lumped into one leg.
- Board: J1 pin 4 (VBAT_PORT) > F1 > D2 > VIN.
- On VIN: C1, C2, D1, U2 (as a 10 mA load), and R1 to U2 EN.
- D3 and R22 hold VBUS at 0 V, so D3 sees the full VIN in reverse.
- Every part in the file has a comment with its value and where the value came from.

## Run it in LTspice

1. File > Open, set the file type to Netlists, and pick `hotplug.cir`.
2. Click Run. The file steps `LCAB` over 0.3, 0.5, 1, 1.5, 2 and 3 uH, each with D1 removed and fitted. That is 12 runs.
3. Probe `V(vin)`. That is the input rail at TP1, U2 VIN, C1 and D1.
4. Other useful traces: `V(en)` is U2 EN. `I(V_ID1)` is the D1 current. `I(V_IF1)` is the inrush current. `V(port)` is J1 pin 4.
5. View > SPICE Error Log lists the `.meas` results for each step. VIN_PK is the peak rail voltage. ED1 is the D1 energy in joules.

Change a `.param` line to try another case:

| Parameter | Default | What it does |
|---|---|---|
| `RSRC` | 50m | Battery and brain resistance. Try 200m. |
| `KLINK` | 0 | 0 keeps the cable at 0.1 ohm for any length (worst case). 1 adds 28 AWG resistance for the length that gives `LCAB`. |
| `RPTC` | 0.15 | F1 resistance. 0.15 is Rmin, 1.0 is R1max. Set 1m to see the board without F1. |
| `TVS` | 1 | 0 removes D1. |
| `TVSC` | 1 | 1 is a high-breakdown SMAJ18A (22.1 V). 0 is a low one (20.0 V). |
| `CNL` | 1 | 1 uses the C1 DC-bias curve. 0 uses a fixed 7.46 uF. |
| `USB` | 0 | Set `USB=1` and `VBAT=0` for a USB hot-plug. |

## Run it in ngspice

ngspice does not know `.step`. Put a `*` in front of the two `.step` lines and it runs one case. The plain `.meas` lines work. The ones with an expression fail with a harmless warning. The numbers below came from ngspice (the copy in KiCad 10), driven from Python with one run per case.

## Results

Worst case damping: `RSRC` 50 mOhm, cable 0.1 ohm at every length, F1 at Rmin (0.15 ohm). "D1 peak current" and "D1 energy" are the larger of the two D1 corners.

| Loop L | No D1, C(V) | No D1, fixed C | D1 high VBR | D1 low VBR | Inrush peak | D1 peak current | D1 energy |
|---|---|---|---|---|---|---|---|
| 0.3 uH | 14.4 V | 14.4 V | 14.4 V | 14.4 V | 30 A | 0 | 0 |
| 0.5 uH | 14.8 V | 14.9 V | 14.8 V | 14.8 V | 27 A | 0 | 0 |
| 1 uH | 16.8 V | 16.6 V | 16.8 V | 16.8 V | 23 A | 0 | 0 |
| 1.5 uH | 18.2 V | 17.8 V | 18.2 V | 18.2 V | 21 A | 0 | 0 |
| 2 uH | 19.3 V | 18.7 V | 19.3 V | 19.3 V | 19 A | 0 | 0 |
| 3 uH | 20.9 V | 19.8 V | 20.9 V | 20.9 V | 17 A | 25 mA | 0.04 mJ |

Other cases, peak VIN over the whole 0.3 to 3 uH sweep:

- Cable resistance that grows with length (`KLINK=1`): 14.4 V. No overshoot at all.
- `RSRC` 200 mOhm: 18.2 V at 3 uH.
- F1 at R1max (1.0 ohm): 14.4 V. No overshoot.
- USB hot-plug (5.25 V, 1 uH, 0.2 ohm): 6.1 V.

What F1 is worth. With F1 replaced by 1 mOhm, the same sweep gives:

| Loop L | No D1 | D1 high VBR | D1 low VBR | D1 peak current | D1 energy |
|---|---|---|---|---|---|
| 0.3 uH | 16.4 V | 16.4 V | 16.4 V | 0 | 0 |
| 1 uH | 20.9 V | 20.9 V | 20.9 V | 19 mA | 0.03 mJ |
| 2 uH | 23.5 V | 23.5 V | 22.8 V | 3.2 A | 0.34 mJ |
| 3 uH | 25.0 V | 25.0 V | 23.2 V | 5.2 A | 0.53 mJ |

With no resistance at all the peak would be 29.2 V for a fixed C1 and 36.7 V with the DC-bias curve. The real circuit never gets close because of the resistance in the loop.

## Ratings on the VIN rail

D2 stops the current once VIN passes its peak, so VIN holds near the peak until the load drains it. That takes milliseconds. So the peak is compared against the DC rating, not the 400 ms rating.

| Part | Rating | Worst seen, F1 fitted | Margin | Worst seen, F1 shorted |
|---|---|---|---|---|
| U2 AP63301 VIN | 35 V DC, 40 V for 400 ms | 20.9 V | 14.1 V | 25.0 V |
| U2 EN (through R1) | 35 V | 20.9 V | 14.1 V | 25.0 V |
| C1 CL32B106KBJNNNE | 50 V | 20.9 V | 29.1 V | 25.0 V |
| C2 CC0603KRX7R9BB104 | 50 V | 20.9 V | 29.1 V | 25.0 V |
| D2 PMEG6020ER, reverse | 60 V | 14.3 V | 45.7 V | 23.2 V |
| D3 PMEG6020ER, reverse | 60 V | 20.9 V | 39.1 V | 25.0 V |
| D2 surge | IFSM 50 A | 30 A, 4 us wide at half height | 20 A | 41 A |
| F1 0ZCG0050AF2C | 30 V, 100 A | 11 V across it, 30 A | 19 V | n/a |
| D1 SMAJ18A | 400 W at 10/1000 us, 68.5 A at 8/20 us | 25 mA, 0.04 mJ | over 99% | 5.2 A, 0.53 mJ |

U2 has a recommended maximum of 32 V. The worst case stays under that too. D1 at 5.2 A for about 7 us is about 120 W. Its pulse rating at that width is about 4.8 kW.

## Assumptions

- Battery at 14.6 V with 50 to 200 mOhm for the battery and brain. Ideal step, no contact bounce. The brain's own port protection is not modelled.
- Cable: 4-conductor flat cable, 28 AWG (0.213 ohm/m per wire). VBAT and GND are adjacent conductors. Loop inductance is about 0.75 uH/m from the wire geometry. 0.2 uH of the loop is the battery lead and brain. 3 uH is an upper bound. A 1.5 m cable is about 1.3 uH.
- The worst case keeps the cable at 0.1 ohm at every length. Real long cables have more resistance and ring less.
- F1 is a fixed resistor. Its thermal time constant is milliseconds.
- C1 DC-bias curve is read from Samsung's characteristic sheet for CL32B106KBJNNNE. Fit: C(V) = 10 uF/(1+(V/24)^2), within 3% of 10 uF up to 40 V. ESR 5 mOhm from the same sheet. Tolerance (10%) and temperature are not included.
- C2 is 70 nF and has no effect.
- D1 model fits Bourns' SMAJ18A table: 20.0 to 22.1 V at 1 mA, 29.2 V at 13.7 A (10/1000 us), 38.0 V at 68.5 A (8/20 us), under 1 uA at 18 V.
- D2 and D3: fit to about 0.45 V at 2 A. Ratings from distributor listings (60 V, 2 A, 530 mV max, IFSM 50 A). Nexperia's own datasheet could not be downloaded. Capacitance 150 pF is a guess.
- U2 is a 10 mA load. It is in UVLO or its 4 ms soft start during the event.
- The D1 pulse rating at short widths scales the 400 W, 1 ms rating by the square root of the width. That matches Bourns' 8/20 us rating.

## Sources

- Bourns SMAJ series datasheet, 2022-06-17: SMAJ18A row and the forward voltage.
- Bel Fuse 0ZCG series datasheet, Rev. 0ZCG Apr2026: 0ZCG0050AF2C Rmin 0.150 ohm, R1max 1.000 ohm, 30 V, 100 A.
- Samsung Electro-Mechanics characteristic sheet for CL32B106KBJNNNE: DC bias, ESR.
- Diodes Inc AP63300/AP63301 datasheet, DS42002 Rev. 3-2: VIN and EN ratings, quiescent current, soft start.
- Farnell and RS listings for PMEG6020ER,115: 60 V, 2 A, 530 mV, 50 A.
