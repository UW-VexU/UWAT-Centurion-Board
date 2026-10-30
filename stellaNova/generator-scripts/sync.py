"""Check (and optionally fix) schematic-to-board parity without moving anything.

/usr/bin/python3 sync.py <board> <netlist> [--fix]
Reports: missing/extra footprints, footprint ID mismatches, value mismatches, pad net mismatches.
With --fix it updates values and sourcing fields in place (no placement or routing changes).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from erc import load
from parts import PART

pcb, net = sys.argv[1], sys.argv[2]
fix = '--fix' in sys.argv
comps, nets = load(net)
pad_net = {(n['ref'], n['pin']): name for name, nodes in nets.items() for n in nodes}
board = pcbnew.LoadBoard(pcb)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
issues = []
for ref in sorted(set(comps) - set(fps)):
    issues.append(f'missing on board: {ref}')
for ref in sorted(set(fps) - set(comps)):
    issues.append(f'extra on board: {ref}')
for ref, c in comps.items():
    fp = fps.get(ref)
    if not fp:
        continue
    fid = fp.GetFPIDAsString()
    if c['fp'] and fid != c['fp']:
        issues.append(f'{ref}: footprint {fid} != schematic {c["fp"]}')
    if fp.GetValue() != c['value']:
        issues.append(f'{ref}: value "{fp.GetValue()}" != "{c["value"]}"')
        if fix:
            fp.SetValue(c['value'])
    if str(fp.GetPath().AsString()).strip('/') != c['tstamp']:
        issues.append(f'{ref}: path mismatch')
    for pad in fp.Pads():
        num = pad.GetNumber()
        if not num:
            continue
        want = pad_net.get((ref, num))
        if want and pad.GetNetname() != want:
            issues.append(f'{ref}.{num}: net {pad.GetNetname()} != {want}')
    if fix:
        model = {'J3': 'Hirose_DM3AT-SF-PEJM5', 'J1': 'Molex_43202-4101', 'SW1': 'CK_PTS810', 'SW2': 'CK_PTS810',
                 'F1': 'BelFuse_0ZCG_1812'}.get(ref)
        if model:
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL(); m.m_Filename = '${KIPRJMOD}/3dmodels/' + model + '.step'
            fp.Models().push_back(m)
        p = PART[ref]
        for k, f in (('mfr', 'Manufacturer'), ('mpn', 'MPN'), ('dk', 'DigiKey')):
            if p.get(k):
                fp.SetProperty(f, p[k])
if fix:
    pcbnew.SaveBoard(pcb, board)
print(f'{len(comps)} schematic parts, {len(fps)} footprints, {len(issues)} parity issues')
for i in issues:
    print('  ', i)
