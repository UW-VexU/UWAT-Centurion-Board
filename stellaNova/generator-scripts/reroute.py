"""Re-route chosen nets with everything else locked, keeping them out of a box (J1 pin field).

prep : /usr/bin/python3 reroute.py prep <board> NET1,NET2 x0,y0,x1,y1
post : /usr/bin/python3 reroute.py post <board> <ses>
Board coords are mm from the board origin (OX, OY). Work happens in place, in the project folder,
so the board keeps the project's net classes.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from pcb import OX, OY

mm = pcbnew.FromMM
stage, PCB = sys.argv[1], sys.argv[2]
STATE = PCB + '.reroute.json'

if stage == 'prep':
    nets = sys.argv[3].split(',')
    x0, y0, x1, y1 = [float(v) for v in sys.argv[4].split(',')]
    b = pcbnew.LoadBoard(PCB)
    assert len(b.GetDesignSettings().m_NetSettings.m_NetClasses) >= 3, 'project net classes not loaded'
    tracks = list(b.GetTracks())
    pours = [z for z in b.Zones() if z.GetZoneName().startswith('GND pour')]
    drop = [t for t in tracks if t.GetNetname() in nets]
    keep = [t for t in tracks if t.GetNetname() not in nets]
    unlocked = []
    for t in keep:
        if not t.IsLocked():
            unlocked.append(str(t.m_Uuid.AsString())); t.SetLocked(True)
    # temporary keepout box on both outer layers
    ko = pcbnew.ZONE(b)
    ko.SetIsRuleArea(True); ko.SetDoNotAllowTracks(True); ko.SetDoNotAllowVias(True)
    ko.SetDoNotAllowPads(False); ko.SetDoNotAllowCopperPour(False); ko.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); ko.SetLayerSet(ls)
    ol = ko.Outline(); ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(mm(OX + x), mm(OY + y))
    ko.SetZoneName('tmp reroute keepout')
    b.Add(ko)
    json.dump({'unlocked': unlocked, 'nets': nets}, open(STATE, 'w'))
    print(f'removing {len(drop)} items on {nets}, {len(pours)} outer pours; locked {len(unlocked)} others')
    for t in drop:
        b.Remove(t)
    for z in pours:
        b.Remove(z)
    pcbnew.SaveBoard(PCB, b)
    b = pcbnew.LoadBoard(PCB)
    print('DSN', pcbnew.ExportSpecctraDSN(b, PCB.replace('.kicad_pcb', '.dsn')))

elif stage == 'post':
    from finish import import_ses, remove_dangling, outer_pours, fill, drc
    ses = sys.argv[3]
    st = json.load(open(STATE))
    b = pcbnew.LoadBoard(PCB)
    n_t, n_v = import_ses(b, ses)
    n_dead = remove_dangling(b)
    unlock = set(st['unlocked'])
    tracks = list(b.GetTracks())
    kos = [z for z in b.Zones() if z.GetZoneName() == 'tmp reroute keepout']
    seen, dup = {}, []
    for t in tracks:
        if str(t.m_Uuid.AsString()) in unlock:
            t.SetLocked(False)
        if t.Type() == pcbnew.PCB_TRACE_T:
            a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            k = (t.GetNetCode(), t.GetLayer(), t.GetWidth(), min(a, c), max(a, c))
            if k in seen: dup.append(t)
            else: seen[k] = t
    for t in dup:
        b.Remove(t)
    for z in kos:
        b.Remove(z)
    outer_pours(b)
    fill(b)
    pcbnew.SaveBoard(PCB, b)
    b = pcbnew.LoadBoard(PCB)
    txt, counts = drc(b, PCB.replace('.kicad_pcb', '-drc.rpt'))
    os.remove(STATE)
    print(f'imported {n_t} segments, {n_v} vias; dangling removed {n_dead}; duplicates removed {len(dup)}')
    print('DRC:', counts)
