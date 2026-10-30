"""Assemble the release zip. Contents sit at the zip root (no wrapper folder), so unzipping inside
a new folder such as "uwat-stellaNova" puts everything directly in it.

/usr/bin/python3 package.py   (run after export.py and the BOM build)
"""
import os, shutil, zipfile

OUT = '/home/claude/v5dbg/out'
BOM = '/home/claude/v5dbg/bom'
GEN = '/home/claude/v5dbg/gen'
STAGE = '/home/claude/v5dbg/release'
ZIP = '/home/claude/v5dbg/uwat-stellaNova-revA.zip'
NAME = 'uwat-stellaNova'

if os.path.exists(STAGE):
    shutil.rmtree(STAGE)
os.makedirs(STAGE)
J = lambda *p: os.path.join(STAGE, *p)

for f in ('README.md', 'AUDIT.md'):
    shutil.copy(os.path.join(OUT, f), J(f))
shutil.copytree(os.path.join(OUT, 'kicad-project'), J('kicad-project'),
                ignore=shutil.ignore_patterns('*.dsn', '*.ses', '*-bak', '*.lck', '_autosave*', '*.unlock.json', '*.reroute.json'))

os.makedirs(J('fabrication', 'gerbers'))
for fn in os.listdir(os.path.join(OUT, 'gerbers')):
    shutil.copy(os.path.join(OUT, 'gerbers', fn), J('fabrication', 'gerbers', fn))
shutil.copy(os.path.join(OUT, f'{NAME}-gerbers.zip'), J('fabrication', f'{NAME}-gerbers.zip'))
shutil.copy(os.path.join(OUT, f'{NAME}-CPL-top.csv'), J('fabrication', f'{NAME}-CPL-top.csv'))

os.makedirs(J('bom'))
for fn in ('uwat-stellaNova_revA_BOM.xlsx', 'uwat-stellaNova_revA_DigiKey_upload.csv'):
    shutil.copy(os.path.join(BOM, fn), J('bom', fn))
for fn in (f'{NAME}-BOM.csv', f'{NAME}-BOM-JLCPCB.csv'):
    shutil.copy(os.path.join(OUT, fn), J('bom', fn))

os.makedirs(J('docs'))
for fn in (f'{NAME}-schematic.pdf', f'{NAME}-schematic.png', f'{NAME}.step', f'{NAME}-1to1-print.pdf'):
    shutil.copy(os.path.join(OUT, fn), J('docs', fn))
for fn in sorted(os.listdir(os.path.join(OUT, 'renders'))):
    shutil.copy(os.path.join(OUT, 'renders', fn), J('docs', fn))

os.makedirs(J('generator-scripts'))
for fn in sorted(os.listdir(GEN)):
    if fn.endswith('.py') or fn == 'nc_pins.json':
        shutil.copy(os.path.join(GEN, fn), J('generator-scripts', fn))
for fn in ('build_bom.py', 'dk_prices_2026-10-30.json'):
    shutil.copy(os.path.join(BOM, fn), J('generator-scripts', fn))
open(J('generator-scripts', 'NOTE.md'), 'w').write(
    '# Generator scripts\n\n'
    'These Python scripts generated the schematic (design.py), placed and routed the board (pcb.py, Freerouting, '
    'finish.py), and wrote the outputs (export.py, build_bom.py). They are kept for reference.\n\n'
    'The KiCad files in kicad-project are the source of truth for rev A. After the scripted route, the board got '
    'targeted edits: incremental.py (smart port A/B swap, R22), vbus_hand.py and reroute.py (VBUS and LED traces '
    'kept 0.5 mm from J1), buck_rework.py (3.3 V buck re-placed and hand routed), battery_clear.py (BOOT and LED '
    'traces kept 0.5 mm from battery copper), silkfix.py and silkplace.py (silkscreen sizes and positions), and bundled 3D models. '
    'Edit rev A in KiCad directly rather than re-running pcb.py, which would undo those edits.\n')

if os.path.exists(ZIP):
    os.remove(ZIP)
with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(STAGE):
        dirs.sort()
        for fn in sorted(files):
            p = os.path.join(root, fn)
            z.write(p, os.path.relpath(p, STAGE))
n = sum(len(f) for _, _, f in os.walk(STAGE))
print('wrote', ZIP, n, 'files', round(os.path.getsize(ZIP) / 1e6, 1), 'MB')
