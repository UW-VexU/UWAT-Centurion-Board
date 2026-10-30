"""Rev A audit fix: keep BOOT and LED_LINK at least 0.5 mm from the battery nets (/VBAT_PORT, Net-(D2-A)).
BOOT now drops to the back layer beside J1 and comes up below F1. The LED_LINK via moves up, away from the VBAT trace.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from pcb import OX, OY
from finish import fill, drc
mm = pcbnew.FromMM
PCB = '/home/claude/v5dbg/project/uwat-stellaNova.kicad_pcb'
P = lambda x, y: pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
near = lambda a, x, y: abs(pcbnew.ToMM(a.x) - OX - x) < 0.01 and abs(pcbnew.ToMM(a.y) - OY - y) < 0.01

REMOVE = {  # (net, kind, endpoints)
    ('/BOOT', 'F', ((25.525, 29.925), (24.748, 29.925))), ('/BOOT', 'F', ((24.748, 29.925), (24.748, 25.668))),
    ('/BOOT', 'F', ((24.748, 25.668), (23.641, 24.56))), ('/BOOT', 'F', ((23.641, 24.56), (23.641, 23.838))),
    ('/BOOT', 'via', ((23.641, 23.838),)), ('/BOOT', 'B', ((23.641, 19.041), (23.641, 23.838))),
    ('/LED_LINK', 'F', ((21.891, 22.064), (21.891, 22.269))), ('/LED_LINK', 'via', ((21.891, 22.269),)),
    ('/LED_LINK', 'B', ((21.891, 22.269), (21.891, 24.638))),
}
F, B = pcbnew.F_Cu, pcbnew.B_Cu
ADD = [('/BOOT', B, [(24.523, 19.041), (24.523, 27.0)]), ('/BOOT', F, [(24.523, 27.0), (24.523, 29.925), (25.525, 29.925)]),
       ('/LED_LINK', B, [(21.891, 22.064), (21.891, 24.638)])]
VIAS = [('/BOOT', 24.523, 27.0), ('/LED_LINK', 21.891, 22.064)]

b = pcbnew.LoadBoard(PCB)
assert len(b.GetDesignSettings().m_NetSettings.m_NetClasses) >= 4
tracks = list(b.GetTracks())
gone = []
for t in tracks:
    for net, kind, pts in REMOVE:
        if t.GetNetname() != net:
            continue
        if kind == 'via' and t.Type() == pcbnew.PCB_VIA_T and near(t.GetPosition(), *pts[0]):
            gone.append(t)
        elif kind != 'via' and t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == (F if kind == 'F' else B):
            s, e = t.GetStart(), t.GetEnd()
            if (near(s, *pts[0]) and near(e, *pts[1])) or (near(s, *pts[1]) and near(e, *pts[0])):
                gone.append(t)
assert len(gone) == len(REMOVE), f'matched {len(gone)} of {len(REMOVE)}'
for net, layer, pts in ADD:
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(0.2)); t.SetLayer(layer)
        t.SetNet(b.FindNet(net)); b.Add(t)
for net, x, y in VIAS:
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
    v.SetNet(b.FindNet(net)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
for t in gone:
    b.Remove(t)
fill(b)
pcbnew.SaveBoard(PCB, b)
b = pcbnew.LoadBoard(PCB)
txt, counts = drc(b, PCB.replace('.kicad_pcb', '-drc.rpt'))
print('DRC', counts)
