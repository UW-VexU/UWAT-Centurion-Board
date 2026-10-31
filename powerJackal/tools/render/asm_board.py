"""Make a copy of the board for the assembly view: no values, one reference per part, centred and sized to fit its body.
usage: python3 asm_board.py <board.kicad_pcb> <out.kicad_pcb>"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.FromMM
SPARE = pcbnew.User_9
WANT = {}

def body_box(fp):
    box = None
    for it in fp.GraphicalItems():
        if it.GetClass() in ("FP_SHAPE", "PCB_SHAPE", "MGRAPHIC") and it.GetLayer() == pcbnew.F_Fab:
            bb = it.GetBoundingBox()
            if box is None: box = bb
            else: box.Merge(bb)
    if box is None:
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            if box is None: box = bb
            else: box.Merge(bb)
    return box

for fp in b.GetFootprints():
    ref = fp.GetReference()
    fp.Value().SetLayer(SPARE)
    fab_ref = None
    for it in fp.GraphicalItems():
        if it.GetClass() in ("FP_TEXT", "PCB_TEXT") and it.GetLayer() == pcbnew.F_Fab:
            if "REFERENCE" in it.GetText() and fab_ref is None: fab_ref = it
            else: it.SetLayer(SPARE)
    if ref.startswith("H"):
        if fab_ref: fab_ref.SetLayer(SPARE)
        continue
    t = fab_ref or fp.Reference()
    if t is fp.Reference(): t.SetLayer(pcbnew.F_Fab)
    box = body_box(fp)
    w, h = pcbnew.ToMM(box.GetWidth()), pcbnew.ToMM(box.GetHeight())
    vertical = h > w * 1.15
    long_, short = (h, w) if vertical else (w, h)
    n = len(ref)
    size = min(0.55 * short, 0.92 * long_ / (n * 0.95), 1.6)
    size = max(size, 0.45)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(max(0.08, size * 0.14)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    # the text angle is stored relative to the footprint, so take the footprint rotation back out
    t.SetTextAngle(pcbnew.EDA_ANGLE(((90 if vertical else 0) - fp.GetOrientationDegrees()) % 360, pcbnew.DEGREES_T))
    t.SetPosition(box.GetCenter())
    if hasattr(t, "SetLocalCoord"): t.SetLocalCoord()
    t.SetVisible(True)
    WANT[ref] = 90 if vertical else 0

# board-level fab or comment texts would only clutter the drawing
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.F_Fab and d.GetClass() == "PCB_TEXT": d.SetLayer(SPARE)
b.Save(sys.argv[2])

def ref_text(fp):
    for it in fp.GraphicalItems():
        if it.GetClass() in ("FP_TEXT", "PCB_TEXT") and it.GetLayer() == pcbnew.F_Fab and "REFERENCE" in it.GetText(): return it
    return fp.Reference()

# KiCad 7 stores footprint text angles one way and reads them back another, so check the saved file and turn any that came out wrong
for _ in range(2):
    c = pcbnew.LoadBoard(sys.argv[2]); bad = 0
    for fp in c.GetFootprints():
        ref = fp.GetReference()
        if ref not in WANT: continue
        t = ref_text(fp)
        if round(t.GetDrawRotation().AsDegrees()) % 180 != WANT[ref]:
            t.SetTextAngle(pcbnew.EDA_ANGLE((t.GetTextAngle().AsDegrees() + 90) % 360, pcbnew.DEGREES_T)); bad += 1
    if not bad: break
    c.Save(sys.argv[2])
# no copper pours: the assembly + copper view shows the routed tracks, pads and vias only.
# Done on the saved text, because removing zones through pcbnew corrupts the next LoadBoard.
s = open(sys.argv[2]).read(); out = []; i = 0; nz = 0
while True:
    j = s.find("\n  (zone", i)
    if j < 0: out.append(s[i:]); break
    out.append(s[i:j]); k = j + 1; depth = 0
    while True:
        ch = s[k]
        if ch == "(": depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0: break
        elif ch == '"':
            k += 1
            while s[k] != '"': k += 2 if s[k] == "\\" else 1
        k += 1
    i = k + 1; nz += 1
open(sys.argv[2], "w").write("".join(out))
print("assembly copy written,", nz, "zones dropped")
