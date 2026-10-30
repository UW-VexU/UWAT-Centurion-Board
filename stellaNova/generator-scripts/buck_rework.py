"""Rev A audit fix: re-place the 3.3 V buck (U2) so the input cap bridges VIN and GND right at the pins,
SW goes straight out to L1 away from FB/EN, and the output caps sit at L1 on top copper.

stage 1 (place): /usr/bin/python3 buck_rework.py place
  moves parts, strips the old copper of the buck nets, lays the hand-routed power copper, saves.
Coordinates are board mm (origin top-left).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from pcb import OX, OY, check_overlaps

mm = pcbnew.FromMM
PCB = '/home/claude/v5dbg/project/uwat-stellaNova.kicad_pcb'
P = lambda x, y: pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))

NEW = {   # ref: (x, y, rot)
    'U2': (41.5, 32.3, 0),
    'C1': (41.5, 35.75, 0), 'C2': (41.5, 38.1, 0),
    'L1': (45.8, 32.6, 0), 'C3': (43.65, 29.4, 0),
    'C4': (46.8, 36.75, 270), 'C5': (44.8, 36.75, 270),
    'C13': (38.1, 29.1, 270), 'R20': (39.6, 29.1, 270), 'R21': (41.1, 29.1, 90),
    'R1': (37.9, 32.3, 0), 'R2': (37.7, 33.8, 180),
    'C6': (36.6, 38.2, 0),
}
STRIP_NETS = {'VIN', '/SW', '/BST', '/FB', 'Net-(U2-EN)'}

# hand-routed copper: (net, layer, width, [points])
F, B = pcbnew.F_Cu, pcbnew.B_Cu
ROUTES = [
    # input loop: U2 VIN/GND straight into C1, C2 beside C1
    ('VIN', F, 0.6, [(40.363, 33.25), (40.025, 35.75)]),
    ('GND', F, 0.6, [(42.637, 33.25), (42.975, 35.75)]),
    ('VIN', F, 0.4, [(40.675, 38.1), (40.4, 37.0)]),
    ('GND', F, 0.4, [(42.325, 38.1), (42.975, 37.0)]),
    # switch node: straight out to L1, bootstrap cap above
    ('/SW', F, 0.6, [(42.637, 32.3), (44.615, 32.3)]),
    ('/SW', F, 0.4, [(44.475, 29.4), (44.615, 30.9)]),
    ('/BST', F, 0.3, [(42.825, 29.4), (42.637, 31.35)]),
    # output: L1 straight into C4, C4 to C5, grounds tied on top
    ('+3V3', F, 0.6, [(46.985, 32.6), (46.985, 34.3), (46.8, 35.8)]),
    ('+3V3', F, 0.6, [(46.8, 35.8), (44.8, 35.8)]),
    ('GND', F, 0.6, [(44.8, 37.7), (46.8, 37.7)]),
    ('GND', F, 0.6, [(44.8, 37.7), (43.3, 36.6)]),
    # feedback: three FB pads in a row, then down to pin 1 (far side from SW)
    ('/FB', F, 0.25, [(38.1, 29.925), (41.1, 29.925)]),
    ('/FB', F, 0.25, [(40.38, 29.925), (40.363, 31.35)]),
    # enable
    ('Net-(U2-EN)', F, 0.25, [(38.725, 32.3), (40.363, 32.3)]),
    ('Net-(U2-EN)', F, 0.25, [(38.725, 32.3), (38.525, 33.8)]),
    # VIN trunk: D2 -> D3 -> down the left side -> C1, taps to R1 and D1
    ('VIN', F, 0.4, [(28.8, 27.2), (30.83, 27.2), (33.03, 29.4), (36.0, 29.4)]),
    ('VIN', F, 0.4, [(36.4, 28.2), (36.0, 28.6), (36.0, 29.4), (36.0, 30.6), (36.0, 32.3), (36.0, 35.45), (39.8, 35.45)]),
    ('VIN', F, 0.4, [(36.0, 32.3), (37.075, 32.3)]),
    ('VIN', F, 0.4, [(39.7, 24.8), (38.6, 25.9), (37.5, 25.9), (36.9, 26.5), (36.9, 27.6), (36.6, 28.0)]),
    ('VIN', B, 0.4, [(36.0, 30.6), (33.5, 30.6)]),          # to TP1 on the back
]
VIAS = [  # (net, x, y)
    ('VIN', 36.0, 30.6),
    ('GND', 43.35, 33.85), ('GND', 43.4, 37.6), ('GND', 46.8, 38.75), ('GND', 41.1, 27.35),
    ('GND', 37.3, 34.6), ('GND', 38.4, 36.6), ('GND', 34.9, 26.2), ('GND', 35.6, 26.2),
    ('+3V3', 38.1, 27.35), ('+3V3', 39.6, 27.35), ('+3V3', 45.8, 35.8), ('+3V3', 35.062, 36.7),
]
# short stubs from pads to their plane vias
STUBS = [
    ('GND', F, 0.3, [(41.1, 28.275), (41.1, 27.35)]),
    ('+3V3', F, 0.3, [(38.1, 28.275), (38.1, 27.35)]),
    ('+3V3', F, 0.3, [(39.6, 28.275), (39.6, 27.35)]),
    ('GND', F, 0.3, [(36.875, 33.8), (37.3, 34.6)]),
    ('GND', F, 0.3, [(38.137, 38.2), (38.4, 36.6)]),
    ('+3V3', F, 0.3, [(35.062, 38.2), (35.062, 36.7)]),
    ('GND', F, 0.3, [(35.7, 24.8), (34.9, 26.2)]),
    ('GND', F, 0.3, [(35.7, 24.8), (35.6, 26.2)]),
]


def run_place():
    b = pcbnew.LoadBoard(PCB)
    assert len(b.GetDesignSettings().m_NetSettings.m_NetClasses) >= 3
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    # old copper to strip: buck nets everywhere, plus GND/+3V3 fanout copper at the moved parts' old pads
    old_pads = [(p.GetPosition(), p.GetNetname()) for r in NEW for p in fps[r].Pads() if p.GetNetname() in ('GND', '+3V3')]
    tracks = list(b.GetTracks())
    strip = []
    for t in tracks:
        n = t.GetNetname()
        if n in STRIP_NETS:
            strip.append(t); continue
        if n in ('GND', '+3V3'):
            pts = [t.GetPosition()] if t.Type() == pcbnew.PCB_VIA_T else [t.GetStart(), t.GetEnd()]
            if any(nn == n and (q - pp).EuclideanNorm() < mm(1.3) for q in pts for pp, nn in old_pads):
                strip.append(t)
    for r, (x, y, rot) in NEW.items():
        fp = fps[r]
        fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
    newpads = [p for r in NEW for p in fps[r].Pads()]
    for t in tracks:
        if t in strip or t.GetNetname() not in ('GND', '+3V3'):
            continue
        sh = t.GetEffectiveShape(pcbnew.F_Cu) if t.IsOnLayer(pcbnew.F_Cu) else None
        if sh is not None and any(p.GetNetname() != t.GetNetname() and p.GetEffectiveShape(pcbnew.F_Cu).Collide(sh, mm(0.25)) for p in newpads):
            strip.append(t)
    nets = {n: b.FindNet(n) for n in ('VIN', '/SW', '/BST', '/FB', 'Net-(U2-EN)', 'GND', '+3V3')}
    for net, layer, w, pts in ROUTES + STUBS:
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w)); t.SetLayer(layer)
            t.SetNet(nets[net]); t.SetLocked(True); b.Add(t)
    for net, x, y in VIAS:
        v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetNet(nets[net]); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLocked(True); b.Add(v)
    print('stripping', len(strip), 'old copper items')
    for t in strip:
        b.Remove(t)
    pcbnew.SaveBoard(PCB, b)
    b = pcbnew.LoadBoard(PCB)
    for i in check_overlaps(b):
        print('ISSUE', i)


if __name__ == '__main__':
    if sys.argv[1] == 'place':
        run_place()
