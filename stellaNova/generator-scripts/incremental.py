"""Rev A update on top of the routed board: swap RS-485 A/B at J1, add R22 (VBUS discharge),
mark C6 DNP, fix L1 value and the back silk pin map. Existing routing is locked so
Freerouting only adds the new connections.

/usr/bin/python3 incremental.py <old_routed.kicad_pcb> <out.kicad_pcb> [check x y rot]
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from erc import load
from parts import PART
import pcb
from pcb import P, mm, NETLIST, OX, OY

old, out = sys.argv[1], sys.argv[2]
comps, nets = load(NETLIST)
# work on a copy inside the project folder so the board loads the project's net classes
import shutil
if os.path.abspath(old) != os.path.abspath(out):
    shutil.copy(old, out)
b = pcbnew.LoadBoard(out)
assert len(b.GetDesignSettings().m_NetSettings.m_NetClasses) >= 3, 'project net classes not loaded'
FP = lambda ref: next(f for f in b.GetFootprints() if f.GetReference() == ref)


def pad_clear(board, fp, clr=0.2):
    """Smallest gap from fp's pads to other-net copper on the same layers (mm)."""
    worst = 99.0
    items = [t for t in board.GetTracks()] + [p for f in board.GetFootprints() if f is not fp for p in f.Pads()]
    for pad in fp.Pads():
        ps = pad.GetEffectivePolygon()
        for it in items:
            if it.GetNetCode() == pad.GetNetCode() and pad.GetNetCode() > 0:
                continue
            for layer in (pcbnew.F_Cu,):
                if not (pad.IsOnLayer(layer) and it.IsOnLayer(layer)):
                    continue
                sh = it.GetEffectiveShape(layer)
                # smallest test clearance that collides = upper bound on the gap
                for g in (0.0, 0.1, 0.15, 0.2, 0.25):
                    if ps.Collide(sh, mm(g)):
                        worst = min(worst, g)
                        break
    return worst


# 1. RS-485: swap J1.1 / J1.2 (old routing is removed further down, after all footprint edits,
#    because this pcbnew build loses SWIG footprint types once anything is removed)
j1 = FP('J1')
for pad in j1.Pads():
    if pad.GetNumber() == '1':
        pad.SetNet(b.FindNet('/RS485_A'))
    elif pad.GetNumber() == '2':
        pad.SetNet(b.FindNet('/RS485_B'))

# 2. R22 VBUS discharge
x, y, rot, side = pcb.PLACE['R22']
if len(sys.argv) > 4 and sys.argv[3] == 'check':
    x, y, rot = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
c = comps['R22']; part = PART['R22']
fp = pcb.load_fp(c['fp'] or part['footprint'])
fp.SetReference('R22'); fp.SetValue(c['value'])
fp.SetPath(pcbnew.KIID_PATH('/' + c['tstamp']))
fp.SetProperty('Sheetfile', pcb.NAME + '.kicad_sch'); fp.SetProperty('Sheetname', '')
for k, f in (('mfr', 'Manufacturer'), ('mpn', 'MPN'), ('dk', 'DigiKey')):
    fp.SetProperty(f, part[k])
b.Add(fp)
fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(rot)
pn = {n['pin']: name for name, nodes in nets.items() for n in nodes if n['ref'] == 'R22'}
for pad in fp.Pads():
    pad.SetNet(b.FindNet(pn[pad.GetNumber()]))
fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
gap = pad_clear(b, fp)
print(f'R22 at ({x}, {y}, {rot}): nearest other-net F.Cu copper gap >= {gap} mm')
if len(sys.argv) > 4 and sys.argv[3] == 'check':
    sys.exit(0)

# 3. C6 DNP, L1 value
c6 = FP('C6')
c6.SetAttributes(c6.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
FP('L1').SetValue(comps['L1']['value'])

# 4. back silk pin map
n_txt = 0
for d in b.GetDrawings():
    d = d.Cast()
    if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().startswith('Smart port 1='):
        d.SetText('Smart port 1=A 2=B 3=GND 4=VBAT'); n_txt += 1
print('silk pin map updated:', n_txt)

# 5. collect everything first: this pcbnew build loses SWIG types after the first Remove()
tracks = list(b.GetTracks())
pours = [z for z in b.Zones() if z.GetZoneName().startswith('GND pour')]
drop = [t for t in tracks if t.GetNetname() in ('/RS485_A', '/RS485_B')]
keep = [t for t in tracks if t.GetNetname() not in ('/RS485_A', '/RS485_B')]

# lock existing copper so the SES carries only the new routes
unlocked = []
for t in keep:
    if not t.IsLocked():
        unlocked.append(str(t.m_Uuid.AsString()))
        t.SetLocked(True)
json.dump(unlocked, open(out + '.unlock.json', 'w'))
print('removing', len(drop), 'A/B track items and', len(pours), 'outer pours')
for t in drop:
    b.Remove(t)
for z in pours:
    b.Remove(z)
pcbnew.SaveBoard(out, b)
b = pcbnew.LoadBoard(out)
print('DSN', pcbnew.ExportSpecctraDSN(b, out.replace('.kicad_pcb', '.dsn')), 'locked', len(unlocked), 'tracks')
