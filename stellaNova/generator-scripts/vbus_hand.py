"""Hand route for VBUS around the J1 pin field (rev A audit fix). Board coords in mm from origin."""
import sys, pcbnew
from pcb import OX, OY
mm = pcbnew.FromMM
SRC, OUT = sys.argv[1], sys.argv[2]
import shutil; shutil.copy(SRC, OUT)
b = pcbnew.LoadBoard(OUT)
assert len(b.GetDesignSettings().m_NetSettings.m_NetClasses) >= 3
net = b.FindNet('VBUS')
P = lambda x, y: pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
old = [t for t in b.GetTracks() if t.GetNetname() in ('VBUS', '/LED_ACT', '/LED_LINK')]
for t in old:
    b.Remove(t)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.3
paths = [
    # J2 A9/B4 to D5.5, with a branch to via V2 (original geometry)
    (F, [(7.9, 33.22), (7.9, 30.49), (7.48, 30.06), (7.02, 29.6), (6.64, 29.6)]),
    (F, [(7.48, 30.06), (7.81, 29.74)]),
    # J2 A4/B9 to via V1 (original geometry)
    (F, [(3.1, 33.22), (3.1, 32.07), (3.15, 32.01)]),
    (B, [(3.15, 32.01), (5.53, 32.01), (7.81, 29.74)]),
    # long run under the J1 body, below its pin field and above its pegs
    (B, [(7.81, 29.74), (10.4, 29.74), (12.2, 27.94), (29.2, 27.94), (31.175, 25.965), (31.175, 25.9)]),
    # R22 pad 1 -> via V3 -> D3 anode, above the VIN trace
    (F, [(31.175, 24.8), (31.175, 25.9), (33.6, 28.325), (33.6, 28.2)]),
]
n = 0
for layer, pts in paths:
    for a, c in zip(pts, pts[1:]):
        if a == c: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(W)); t.SetLayer(layer); t.SetNet(net)
        b.Add(t); n += 1
for x, y in ((3.15, 32.01), (7.81, 29.74), (31.175, 25.9)):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net)
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
pcbnew.SaveBoard(OUT, b)
print('removed', len(old), 'old items; added', n, 'VBUS segments and 3 vias')
