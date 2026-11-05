# UWAT-Centurion-Board

KiCad hardware projects for UWAT VEXU.

| Board | Description |
|---|---|
| centurion | Main custom sensor board. STM32G491 with 2 smart port RS-485 links (MAX33071E), I2C mux sensor ports, an SPI IMU connector, USB-C to the Jetson and a UART + CAN FD link to ramBar. Rev A: 4 layers (In1 GND, In2 +3.3V), 103.2 x 62.6 mm, fully routed; ERC, DRC and parity clean, layout audit 0 errors. Ready for fab after the checks in its README's Before ordering list. Non-urgent fixes are deferred to [centurion/REV_B_IMPROVEMENTS.md](centurion/REV_B_IMPROVEMENTS.md). It uses footprints and symbols from `powerJackal/lib`. See [centurion/README.md](centurion/README.md) |
| imuBoard | Centurion IMU board, rev 1.0: a Bosch BMI270 on SPI, which plugs into centurion's J5 with a straight JST GH 8-pin cable. 38 x 24 mm, 2 layers, two #8-32 holes 1 in apart. Routed; ERC, DRC and parity clean. See [imuBoard/README.md](imuBoard/README.md) |
| powerJackal | Smart port power test board, rev A. See [powerJackal/README.md](powerJackal/README.md) |
| stellaNova | VEX V5 wireless debugger. An ESP32-S3 bridges one smart port (RS-485) to WiFi and Bluetooth LE. See [stellaNova/README.md](stellaNova/README.md) |
| rambar | Not in the repo yet |

[PCB_DESIGN_GUIDELINES.md](PCB_DESIGN_GUIDELINES.md) has the layout rules, fab limits (PCBWay and JLCPCB) and a pre-order checklist for all of these boards.

`.claude/agents/` has four Claude Code review agents that work on any KiCad project in this repo: `pcb-footprint-checker` (footprints vs datasheets), `pcb-layout-auditor` (measures the routed copper against the guidelines), `pcb-power-thermal` (rail budget, regulator heat, fuses) and `pcb-signal-checker` (I2C, UART, RS-485, CAN, SPI, USB, clocks, logic levels). They only read files. Ask Claude Code to run one on a board folder, for example "run pcb-layout-auditor on centurion".

## Making Gerber files

These steps work for any board in this repo (KiCad 10). The examples use centurion; for a 2-layer board, leave out In1.Cu and In2.Cu.

### In KiCad

1. Open the board's `.kicad_pcb` in the PCB editor. Run **Inspect → Design Rules Checker** first, with "Refill all zones" ticked. It should show 0 violations and 0 unconnected items.
2. **File → Fabrication Outputs → Gerbers (.gbr)...**
   - **Output directory:** `fab/gerbers/`, inside the board's folder.
   - **Layers:** F.Cu, In1.Cu, In2.Cu, B.Cu, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, F.Paste, B.Paste, Edge.Cuts.
   - **Tick:**
     - Plot reference designators
     - Check zone fills before plotting
     - Use Protel filename extensions
     - Subtract soldermask from silkscreen
   - Leave everything else at its default, then click **Plot**.
3. In the same dialog, click **Generate Drill Files...**
   - **Format:** Excellon
   - **Units:** millimeters
   - **Zeros:** Decimal format
   - **Drill origin:** Absolute
   - **Holes:** untick "PTH and NPTH in single file", so you get separate PTH and NPTH files
   - **Map file:** Gerber X2
   - Click **Generate Drill File**, then close the dialog.
4. Zip everything in `fab/gerbers/`, keeping the files at the top level of the zip with no folder inside it.

### From a terminal

Run this in the board's folder (for example `centurion/`). On Windows, kicad-cli is at `C:\Program Files\KiCad.0in\kicad-cli.exe`.

```bash
kicad-cli pcb export gerbers --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts" --subtract-soldermask --check-zones -o fab/gerbers/ centurion.kicad_pcb
```

```bash
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm --excellon-zeros-format decimal --excellon-separate-th --generate-map --map-format gerberx2 -o fab/gerbers/ centurion.kicad_pcb
```

Both commands were checked on centurion on 2026-11-04. They produce 16 files, about 0.8 MB zipped.

For a 4-layer board, the copper files are, in order:

| File | Layer | Centurion |
|---|---|---|
| `.gtl` | Top | Signals |
| `.g1` | Inner 1 | GND plane |
| `.g2` | Inner 2 | +3.3V plane |
| `.gbl` | Bottom | Signals |

The other files:
- `.gto` / `.gbo`: silkscreen
- `.gts` / `.gbs`: solder mask
- `.gtp` / `.gbp`: paste
- `.gm1`: board outline
- `-PTH.drl` / `-NPTH.drl`: drills

Fabs read the layer order from these extensions.

### Checking the files

`tools/gerbcheck.py` reads the Gerber and drill files with its own reader, not KiCad's exporter, and checks them against the board file:
- **Drills:** hole and slot counts per size.
- **Layers:** copper, mask and paste, to 0.08 mm.
- **Netlist:** connectivity rebuilt from the Gerber copper and the plated holes alone, then checked against every pad's net. It reports shorts and opens.

It also draws preview PNGs from the Gerbers. It works for 2- and 4-layer boards. Run it from the repo root, with KiCad's Python:

```bash
"C:\Program Files\KiCad.0in\python.exe" tools/gerbcheck.py centurion/centurion.kicad_pcb centurion/fab/gerbers
```

It ends with `RESULT: PASS` (exit code 0) or `RESULT: FAIL` and the reasons. The previews go to `fab/gerbcheck/`.

On 2026-11-05 it passed centurion rev A (125 nets, 0 shorts, 0 opens) and imuBoard (13 nets). To make sure it catches faults, it was also run on a deliberately broken copy of centurion's files, with one MUX_RST track cut and one via drill deleted. It reported both opens and the missing drill.

It doesn't check the silkscreen beyond drawing it, or how the fab processes the files. Still look at the fab's Gerber viewer and approve their production files.

### Ordering at JLCPCB

On 2026-11-04, five centurion boards cost C$40.39 plus C$37.41 UPS shipping at JLCPCB. At PCBWay they cost US$98.76 with DHL, about C$135–140. So JLCPCB is the first choice. Duties and HST are extra at both.

1. Upload the zip, then check the layer order and the outline size in JLCPCB's Gerber viewer.
2. **Settings:**

   | Setting | Value |
   |---|---|
   | Base material | FR-4 |
   | Layers | 4 (read from the files) |
   | Thickness | 1.6 mm |
   | Color | Green |
   | Silkscreen | White |
   | Material type | FR4 TG135 is fine |
   | Surface finish | ENIG if it's cheap, otherwise HASL lead-free. ENIG pads are flat, which helps the 0.5 mm-pitch MCU and the QFN parts. |
   | Via covering | Tented |
   | Outer copper | 1 oz |
   | Impedance control | None |
   | Mark on PCB | "Remove Mark" or "Specify a location", so the order number doesn't land on a crowded area |
3. **Stackup:** pick **JLC04161H-3313**. Its 0.1 mm prepreg is what centurion's simulations assumed. Their default 7628 stackup, with about 0.2 mm prepreg, also works.
4. **Optional:** "Epoxy filled & capped" via covering covers TI's advice to plug the thermal vias under centurion's U1. Skip it if it costs much.

Centurion's silkscreen text is 0.8 mm tall, under JLCPCB's 1.0 mm minimum, so the labels may print a little soft. The copper isn't affected.

[PCB_DESIGN_GUIDELINES.md](PCB_DESIGN_GUIDELINES.md) has both fabs' limits.

`fab/` isn't git-ignored. Commit the zip you actually sent if you want a record of each order; otherwise regenerate it from the board file.

Other folders:

- `tools`: `gerbcheck.py`, the Gerber checker (see [Checking the files](#checking-the-files)).
- `tinaOnboarding`: electrical onboarding materials.
- `ul_*`, `0955012401` and similar folders: downloaded part libraries.
