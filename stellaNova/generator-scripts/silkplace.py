"""Nudge listed silk texts to the nearest spot that clears other silk (0.12 mm), pads (0.15 mm) and the edge."""
import sys, json, math, pcbnew
PCB = sys.argv[1]; names = sys.argv[2].split('|')
START = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)
texts = [d.Cast() for d in b.GetDrawings() if d.Cast().GetClass() == 'PCB_TEXT' and d.Cast().GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
fps = list(b.GetFootprints())
def obstacles(layer, me):
    obs = []
    for t in texts:
        if t is not me and t.GetLayer() == layer: obs.append(('silk', t.GetEffectiveShape(layer)))
    for d in b.GetDrawings():
        d = d.Cast()
        if d.GetClass() != 'PCB_TEXT' and d.GetLayer() == layer: obs.append(('silk', d.GetEffectiveShape(layer)))
    cu = pcbnew.F_Cu if layer == pcbnew.F_SilkS else pcbnew.B_Cu
    for fp in fps:
        for g in fp.GraphicalItems():
            if g.GetLayer() == layer and (g.GetClass() != 'FP_TEXT' or g.Cast().IsVisible()):
                obs.append(('silk', g.GetEffectiveShape(layer)))
        r = fp.Reference()
        if r.IsVisible() and r.GetLayer() == layer: obs.append(('silk', r.GetEffectiveShape(layer)))
        fab = pcbnew.F_Fab if layer == pcbnew.F_SilkS else pcbnew.B_Fab
        xs, ys = [], []
        for g in fp.GraphicalItems():
            if g.GetLayer() == fab and g.GetClass() != 'FP_TEXT':
                gb = g.GetBoundingBox()
                xs += [int(gb.GetLeft()), int(gb.GetRight())]; ys += [int(gb.GetTop()), int(gb.GetBottom())]
        if xs:
            ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
            for x, y in ((min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))):
                ps.Append(x, y)
            obs.append(('body', ps))
        for p in fp.Pads():
            if p.IsOnLayer(cu) or p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                obs.append(('pad', p.GetEffectiveShape(cu)))
    return obs
edge = b.GetBoardEdgesBoundingBox()
moved = {}
for t in texts:
    if t.GetText() not in names: continue
    obs = obstacles(t.GetLayer(), t)
    if t.GetText() in START:
        t.SetPosition(pcbnew.VECTOR2I(mm(100 + START[t.GetText()][0]), mm(100 + START[t.GetText()][1])))
        t.SetTextAngle(pcbnew.EDA_ANGLE(START[t.GetText()][2], pcbnew.DEGREES_T))
    x0, y0 = t.GetPosition().x, t.GetPosition().y
    best = None
    for r in [i * 0.05 for i in range(0, 41)]:
        cands = [(0, 0)] if r == 0 else [(r * math.cos(a), r * math.sin(a)) for a in [k * math.pi / 12 for k in range(24)]]
        for dx, dy in cands:
            t.SetPosition(pcbnew.VECTOR2I(int(x0 + mm(dx)), int(y0 + mm(dy))))
            sh = t.GetEffectiveShape(t.GetLayer())
            bb = t.GetBoundingBox()
            if bb.GetLeft() < edge.GetLeft() + mm(0.3) or bb.GetRight() > edge.GetRight() - mm(0.3) or \
               bb.GetTop() < edge.GetTop() + mm(0.3) or bb.GetBottom() > edge.GetBottom() - mm(0.3):
                continue
            if any(sh.Collide(o, mm({'silk': 0.12, 'pad': 0.15, 'body': 0.0}[k])) for k, o in obs): continue
            best = (dx, dy); break
        if best: break
    if best is None:
        t.SetPosition(pcbnew.VECTOR2I(x0, y0)); print('NO SPOT for', t.GetText())
    else:
        moved[t.GetText()] = (round(pcbnew.ToMM(x0) - 100 + best[0], 2), round(pcbnew.ToMM(y0) - 100 + best[1], 2))
        print(f'{t.GetText()!r}: moved {math.hypot(*best):.2f} mm to {moved[t.GetText()]}')
pcbnew.SaveBoard(PCB, b)
json.dump(moved, open('/tmp/claude-0/-home-claude/0eeef73e-c7fb-5128-b9bd-a2ea2b0cc62d/scratchpad/silk_moves.json', 'w'))
