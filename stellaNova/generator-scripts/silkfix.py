"""Apply silkscreen size rules to the routed board in place: text >= 0.8 mm tall, 0.15 mm stroke."""
import sys, pcbnew
PCB = sys.argv[1]
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)
moves = {}   # text -> (x, y) board coords, filled in after a strict DRC pass
if len(sys.argv) > 2:
    import json; moves = json.loads(sys.argv[2])
n = 0
for d in b.GetDrawings():
    d = d.Cast()
    if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        h = pcbnew.ToMM(d.GetTextHeight())
        if h < 0.8:
            d.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); n += 1
        d.SetTextThickness(max(d.GetTextThickness(), mm(0.15)))
        if d.GetText() in moves:
            x, y = moves[d.GetText()]; d.SetPosition(pcbnew.VECTOR2I(mm(100 + x), mm(100 + y)))
for fp in b.GetFootprints():
    r = fp.Reference()
    if r.IsVisible() and r.GetLayer() == pcbnew.F_SilkS:
        r.SetTextThickness(max(r.GetTextThickness(), mm(0.15)))
print('texts enlarged', n)
pcbnew.SaveBoard(PCB, b)
