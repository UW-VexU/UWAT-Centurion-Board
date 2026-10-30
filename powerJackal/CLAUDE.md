# CLAUDE.md for powerJackal

This folder is the powerJackal board: a VEX V5 smart port power test board, rev A. It is one of three boards in the UWAT-Centurion-Board repo. Read `README.md` and `docs/design_notes.md` before changing anything.

## Source of truth

- The KiCad files are the source of truth: `powerJackal.kicad_sch` and `powerJackal.kicad_pcb`. Edit the design in KiCad.
- `tools/` holds the scripts that generated rev A. They are kept for reference and for the checkers.
- Never run `gen_pcb.py`, `route.py`, `tidy_tracks.py`, `tidy_loop.py`, `hand_routes.py`, `swap_tp.py` or `silk.py` on `powerJackal.kicad_pcb`. They rebuild or rewrite routing and silkscreen and would wipe hand edits. Run them only on copies, if at all.
- `tools/kicad/jackal_design.py` mirrors the rev A parts and nets. The BOM builder checks against it. If parts or nets change in KiCad, update `jackal_design.py` too, or the BOM build fails its check.
- Never edit files in `fab/revA/` after rev A is ordered. Put new outputs in `fab/revB/`.

## Environment

- The board file is KiCad 10.0 format, saved with KiCad 10.0.7. KiCad 9 and older cannot open it. The schematic is still 7.0 format and KiCad 10 upgrades it on save. Commit a format upgrade by itself.
- The back silkscreen text uses Chakra Petch Bold, embedded in the board file (`embedded_fonts yes`). Keep it embedded, or machines without the font fall back to the KiCad font and the long line runs onto J6's pads.
- **kicad-cli:** on Windows it is in the KiCad `bin` folder, for example `C:\Program Files\KiCad\8.0\bin\kicad-cli.exe`.
- **Python scripts:** anything in `tools/kicad/` that imports `pcbnew` must run with KiCad's own Python, for example `"C:\Program Files\KiCad\8.0\bin\python.exe" tools\kicad\corners.py powerJackal.kicad_pcb`.
- **Footprint path:** scripts that load footprints from KiCad's library need the env var `KICAD_FOOTPRINT_DIR` set to KiCad's `footprints` folder.
- **Other dependencies:**
  - `tools/bom/build_bom.py` needs `openpyxl`.
  - `tools/render/` needs `numpy`, `pillow`, Node and Playwright.
- **Coordinates:** board coordinates in the `.kicad_pcb` file are offset by 100 mm. The board's top-left corner is at (100, 100). The checkers subtract that and print board coordinates in mm from the top-left corner. The drill and placement origin is the bottom-left corner.

## Design rules and net classes

- **Rules:**
  - Clearance 0.2 mm, minimum track 0.2 mm.
  - Vias 0.6/0.3 mm, power vias 0.8/0.4 mm.
  - Hole clearance 0.25 mm.
  - 0.5 mm copper keepout along every edge.
  - Copper stays 4.2 mm from each mounting hole center.
- **Net classes:**
  - Power 0.8 mm: VPORT, BENCH_IN, VIN_OR, VFUSE, VIN_MOD, 5V_MOD, 5V, 5V_LDO, 3V3_LDO.
  - Supply3V3 0.3 mm: 3V3.
  - USBPower 0.4 mm: VBUS_USB, USB_PWR.
  - Ground 0.4 mm: GND (poured).
  - Default 0.25 mm: everything else.
- **Pours:** a top GND pour and a bottom GND plane are tied by about 190 stitching vias. VIN_MOD and 5V_MOD have their own top pours around U1.
- **Locked tracks:** many tracks are locked to protect the hand routing. Unlock before moving them.

## Routing style (the board owner checks for these)

- Traces enter a pad straight along a pad axis, never diagonally.
- 45 degree bends only, no 90 degree corners on a trace.
- Branches join a run with a square T. No V-shaped forks at pads.
- One width per run. No thin and thick segments overlapping at a joint.
- No top-layer trace under the body of a part it does not connect to. Hop to the bottom layer with vias instead.
- Kelvin sense lines leave each shunt pad from its inner edge: R1 for U2, R2 for U3, R12 for U5.

## Checks to run after any layout change

1. `kicad-cli pcb drc -o drc.rpt powerJackal.kicad_pcb`.
   - Must show 0 errors and 0 unconnected items.
   - Rev A also has 4 silkscreen overlap warnings and 7 silkscreen-past-edge warnings (connectors hang over the edge by design).
2. Run the checkers with KiCad's Python, from `tools/kicad/`, passing the board path:
   - `corners.py` expects 0 acute corners and 0 angled pad entries.
   - `junctions.py` expects 0 mid-segment taps, 0 overlapping runs and 0 mixed widths.
   - `under_parts.py` prints only `done`.
   - `kelvin_check.py` prints `Kelvin lines clean`.
3. `place_check.py` reports 3 courtyard overlaps of 0.02 to 0.04 mm in rev A (C13/R21, C15/R17, LED3/R20). These are touching outlines, measured with the line width. KiCad's own DRC passes them.

## Outputs to regenerate after a change

- **Schematic PDF:** `kicad-cli sch export pdf -o docs/powerJackal_revA_schematic.pdf powerJackal.kicad_sch`.
- **Gerbers, drill and placement:** use the commands in `README.md`. The gerber export uses `--subtract-soldermask --use-drill-file-origin`. The drill export uses `--excellon-separate-th --drill-origin plot`.
- **BOM:** `python tools/bom/build_bom.py bom` writes the xlsx and the DigiKey CSV. Part data lives in `P`, DigiKey price breaks in `BREAKS` and product links in `LINK`, at the top of `build_bom.py`. The builder needs `openpyxl`.
- **Board viewer and wiring map:**
  - `tools/render/build_v3.py <board> <workdir>` rebuilds `docs/board_viewer/` and needs Node and Playwright.
  - `tools/wiring/make_wiring_map.py docs/powerJackal_wiring_map.html` rebuilds the wiring map from `jackal_design.py`.
- **Docs:** update the revision table in `docs/design_notes.md` and any affected numbers in `README.md`.

## Parts and pricing

- Source from DigiKey Canada (digikey.ca). Check stock and price in CAD.
- The BOM records the DigiKey part number, stock and the full CAD price-break table read from digikey.ca, with the date checked. Update the date when prices are rechecked.
- The xlsx prices each line at the break for its order qty with a `LOOKUP` on the Price breaks tab. Keep each part's breaks in increasing quantity there.
- Every BOM line has a digikey.ca product link in `LINK` in `build_bom.py`. The number at the end of a link picks the page, so open each new link once and check it shows the right MPN.
- Prefer parts with large DigiKey stock and packages that are easy to hand solder.

## Key facts

- **INA226 addresses:** U2 0x40 (port input), U3 0x41 (5 V), U5 0x45 (3.3 V).
- **INA226 calibration:** CAL 2048 for all three. Current LSB 125 µA for U2 and U3, 50 µA for U5.
- **ESP32-C3 pins:**
  - SDA GPIO4, SCL GPIO5, PGOOD GPIO3, status LED GPIO10.
  - USB on GPIO18 and GPIO19.
  - Straps: GPIO2, GPIO8 and GPIO9 are pulled high. GPIO9 is BOOT.
  - Free: GPIO0, 1, 6, 7, 20, 21.
- **Q1 (AO3401A):** passes USB power only while the 5 V rail is off. Its gate is on the 5 V rail, through a via pair to D2's 5 V pad.
- **Open items before ordering:** check the J1 smart port pinout with a meter, and check the J1 footprint against the Molex 0955012441 drawing.

## Writing style for docs in this folder

- Plain, short sentences.
- No em dashes or en dashes, and no semicolons.
- Use Helvetica in any Word documents or slide decks made for this project.
