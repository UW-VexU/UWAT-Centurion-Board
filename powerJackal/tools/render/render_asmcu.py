"""Render the 'assembly + copper' view of any board (same look as the page tab) for quick before/after checks.
usage: python3 render_asmcu.py board.kicad_pcb out.png workdir [px_per_mm]"""
import sys, os, subprocess, math
import numpy as np
from PIL import Image
import pcbnew
PCB, OUTP, WORK = sys.argv[1:4]; S = float(sys.argv[4]) if len(sys.argv) > 4 else 40
HERE = os.path.dirname(os.path.abspath(__file__)); os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, os.path.join(HERE, "..", "kicad"))
from pcb_common import W, H, OX, OY
ASM = os.path.join(WORK, "asm.kicad_pcb")
subprocess.run([sys.executable, os.path.join(HERE, "asm_board.py"), PCB, ASM], check=True, capture_output=True)
def layer(name, pcb):
    svg = os.path.join(WORK, name.replace(".", "_") + ".svg"); png = svg[:-4] + ".png"
    subprocess.run(["kicad-cli", "pcb", "export", "svg", "-l", name + ",Edge.Cuts", "--black-and-white", "--page-size-mode", "2",
                    "--exclude-drawing-sheet", "--drill-shape-opt", "0", "-o", svg, pcb], check=True, capture_output=True)
    subprocess.run(["node", os.path.join(HERE, "svg2png.mjs"), svg, png, str(S)], check=True, capture_output=True, cwd=HERE)
    return 1.0 - np.asarray(Image.open(png).convert("L")).astype(np.float32) / 255.0
# every layer is exported together with Edge.Cuts, so all images share the same frame: the board outline box
L = {k: layer(v, ASM) for k, v in {"f": "F.Cu", "b": "B.Cu", "m": "F.Mask", "fab": "F.Fab"}.items()}
E = layer("Edge.Cuts", ASM)
ys, xs = np.nonzero(E > 0.5); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
def crop(a): return a[y0:y1 + 1, x0:x1 + 1]
def only(a): return np.clip(crop(a) - crop(E), 0, 1)
col = np.zeros(crop(E).shape + (3,), np.float32); col[:] = (20, 21, 23)
for a, c, al in ((only(L["b"]), (78, 138, 232), 0.85), (only(L["f"]), (232, 88, 62), 1.0), (only(L["m"]), (212, 172, 90), 1.0), (only(L["fab"]), (238, 238, 234), 1.0)):
    m = (a * al)[..., None]; col = col * (1 - m) + np.array(c, np.float32) * m
Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(OUTP)
print("rendered", OUTP, col.shape)
