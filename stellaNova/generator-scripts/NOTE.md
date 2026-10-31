# Generator scripts

These Python scripts generated the schematic (design.py), placed and routed the board (pcb.py, Freerouting, finish.py), and wrote the outputs (export.py, build_bom.py). They are kept for reference.

The KiCad files in the stellaNova folder are the source of truth for rev A. They used to live in a kicad-project subfolder, and the scripts still use that path. The board is now 2 layers (see AUDIT.md), so pcb.py would also rebuild the old 4-layer layout. After the scripted route, the board got targeted edits: incremental.py (smart port A/B swap, R22), vbus_hand.py and reroute.py (VBUS and LED traces kept 0.5 mm from J1), buck_rework.py (3.3 V buck re-placed and hand routed), battery_clear.py (BOOT and LED traces kept 0.5 mm from battery copper), silkfix.py and silkplace.py (silkscreen sizes and positions), and bundled 3D models. Edit rev A in KiCad directly rather than re-running pcb.py, which would undo those edits.
