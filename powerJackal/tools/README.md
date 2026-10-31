# powerJackal tools

These scripts generated the rev A design. They ran on Linux with KiCad 7.0 (the `pcbnew` Python module and `kicad-cli`), Python 3 and Node.

The KiCad files one folder up are now the source of truth. Use these scripts for checking and for regenerating documents, not for rebuilding the board.

## Safe to use on the real board (read only)

Run these with KiCad's own Python so `pcbnew` imports. On Windows that is for example `"C:\Program Files\KiCad\8.0\bin\python.exe"`. Run them from `tools/kicad/` and pass the board path, for example `..\..\powerJackal.kicad_pcb`.

| Script | What it checks | Rev A result |
|---|---|---|
| `kicad/check.py <board> <report>` | DRC through pcbnew, with a count per violation type | 0 errors, 0 unconnected |
| `kicad/corners.py <board>` | Every trace corner and every pad entry. Flags acute corners and traces that enter a pad at an angle | 0 acute, 0 angled entries |
| `kicad/junctions.py <board>` | Taps that land mid-segment, overlapping runs of one net, joints where widths change | 0, 0, 0 |
| `kicad/under_parts.py <board>` | Top-layer traces under the body of a part they do not connect to | none |
| `kicad/kelvin_check.py <board>` | INA226 sense lines touch nothing but their shunt pads. Also prints USB pair lengths | clean |
| `kicad/place_check.py <board>` | Courtyard overlaps and parts off the board | 3 touching outlines of 0.02 to 0.04 mm (line width), KiCad DRC passes them |
| `kicad/verify_net.py <netlist>` | A KiCad netlist export against `jackal_design.py` | 0 problems |
| `kicad/frag.py <board>` | Ground pour fragments not tied to the main ground | |

## Document builders

| Script | Output |
|---|---|
| `bom/build_bom.py <outdir>` | `powerJackal_revA_BOM.xlsx` (with formulas) and `powerJackal_revA_DigiKey_upload.csv`. Needs `openpyxl`. Part data is the list `P` at the top. It checks the BOM against `kicad/jackal_design.py` |
| `wiring/make_wiring_map.py <out.html>` | The wiring map page, from `kicad/jackal_design.py` and `wiring/wiring_template.html` |
| `render/build_v3.py <board> <workdir>` | `docs/board_viewer/` (views and the page). Needs `numpy`, `pillow`, `kicad-cli`, Node and Playwright. Run `npm install playwright` and `npx playwright install chromium` in `render/` first |
| `render/render_asmcu.py <board> <out.png> <workdir> [px_per_mm]` | A quick assembly plus copper picture of any board, for before and after checks |
| `kicad/export_fab.sh <board> <outdir>` | Gerbers, drill, zip and placement file (bash, works in Git Bash) |

## Generator pipeline (reference only)

This is how rev A was built, in order. Do not run any of it on the real board.

1. **`kicad/jackal_design.py`:** parts, values, footprints, part numbers and the pin-to-net map. The single source the other scripts read.
2. **`kicad/gen_lib.py`:** builds the UWAT library (`../lib`). Needs `ESPLIB` pointing at a clone of Espressif's kicad-libraries.
3. **`kicad/gen_sch.py <outdir>`:** writes the schematic. Every pin gets a short wire and a net label. Symbol UUIDs are stable and cached in `kicad/uuids.json`.
4. **`kicad/pcb_place.py` and `kicad/gen_pcb.py <out.kicad_pcb>`:** placement table and the unrouted board.
5. **`kicad/route.py`:** Freerouting autoroute, pours and keepouts. Needs `freerouting.jar` in its work folder.
6. **Cleanup:** `kicad/tidy_tracks.py`, `kicad/hand_routes.py` and `kicad/tidy_loop.py` tidy the autorouted copper, then apply the hand routes and rerun DRC. `hand_routes.py` edits board records as text, because deleting items through `pcbnew` corrupted boards in KiCad 7.
7. **`kicad/silk.py <in> <out>`:** silkscreen labels and reference designator placement.
8. **`kicad/swap_tp.py`:** swaps test point footprints in place.

`kicad/pcb_common.py` holds shared helpers, board size, hole positions and net classes. It looks for KiCad's standard footprints in `KICAD_FOOTPRINT_DIR`, or `/usr/share/kicad/footprints` if that is not set.
