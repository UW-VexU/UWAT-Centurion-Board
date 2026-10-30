"""Fab outputs: Gerbers, drill, pick-and-place, BOM, schematic PDF/PNG, 2D board renders."""
import os, sys, subprocess, csv, shutil, zipfile, json
sys.path.insert(0, os.path.dirname(__file__))
from erc import load
from parts import PART, LINES, ROLE, STOCK

PRJ = '/home/claude/v5dbg/project'
NAME = 'uwat-stellaNova'
OUT = '/home/claude/v5dbg/out'
NETLIST = '/tmp/claude-0/-home-claude/0eeef73e-c7fb-5128-b9bd-a2ea2b0cc62d/scratchpad/v5.net'
PCB = os.path.join(PRJ, NAME + '.kicad_pcb')
SCH = os.path.join(PRJ, NAME + '.kicad_sch')

def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit(f'failed: {a}')
    return r.stdout

def dk_link(mpn):
    return 'https://www.digikey.ca/en/products/result?keywords=' + mpn.replace(' ', '%20')

def bom(comps):
    groups = {}
    for ref in comps:
        p = PART[ref]
        if ref.startswith('TP'):
            continue
        groups.setdefault(p['line'], []).append(ref)
    def keyf(r):
        import re
        m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
    rows = []
    for line, refs in groups.items():
        refs.sort(key=keyf)
        fit = [r for r in refs if not PART[r]['dnp']]
        dnp = [r for r in refs if PART[r]['dnp']]
        L = LINES[line]
        rows.append(dict(refs=refs, fit=fit, dnp=dnp, L=L))
    rows.sort(key=lambda r: keyf(r['refs'][0]))
    for r in rows:
        r['line'] = PART[r['refs'][0]]['line']
    with open(os.path.join(OUT, f'{NAME}-BOM.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Item', 'Qty per board', 'Designators', 'Do not populate', 'Value', 'Description', 'Manufacturer', 'MPN',
                    'DigiKey Canada PN', 'DigiKey CA stock 2026-10-30', 'Unit CAD qty 1', 'Unit CAD qty 10',
                    'Line CAD per board (qty 10 pricing)', 'DigiKey link', 'Footprint'])
        tot1 = tot10 = 0.0
        for i, r in enumerate(rows, 1):
            L = r['L']; st = STOCK.get(r['line'], (None, None, None))
            n = len(r['fit'])
            line10 = n * st[2] if st[2] else 0
            tot1 += n * (st[1] or 0); tot10 += line10
            w.writerow([i, n, ' '.join(r['fit']), ' '.join(r['dnp']), L['value'], L['desc'], L['mfr'], L['mpn'],
                        L['dk'], st[0] if st[0] is not None else '', st[1] or '', st[2] or '', f'{line10:.2f}',
                        dk_link(L['mpn']), L['footprint']])
        w.writerow([])
        w.writerow(['', '', '', '', '', 'Parts total per board', '', '', '', '', f'{tot1:.2f}', '', f'{tot10:.2f}'])
    print(f'parts per board: CAD {tot1:.2f} at qty 1, {tot10:.2f} at qty-10 pricing')
    # JLCPCB-style BOM (fitted SMD/THT parts only)
    with open(os.path.join(OUT, f'{NAME}-BOM-JLCPCB.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Comment', 'Designator', 'Footprint', 'MPN'])
        for r in rows:
            if r['fit']:
                w.writerow([r['L']['value'], ','.join(r['fit']), r['L']['footprint'].split(':')[1], r['L']['mpn']])
    return rows

def readme(rows, drc_counts, erc_errors, size, parity=''):
    W, H = size
    lines = [f'# uwat-stellaNova, rev A', '',
             'stellaNova is a VEX V5 wireless debugger. Full name: uwat-stellaNova.', '',
             'It is an ESP32-S3 board that plugs into one VEX V5 smart port, receives whatever the brain writes to that port',
             'over RS-485, and serves it to a laptop, phone or tablet over WiFi or Bluetooth LE. It can also send',
             'commands back to the brain over the same wire (half duplex). Powered from the V5 battery through the',
             'smart port, or from USB-C on the bench.', '',
             '## What is in this folder', '',
             '- `kicad-project/`: open `uwat-stellaNova.kicad_pro` in KiCad 7 or newer. Symbols, footprints and 3D models are all inside.',
             '- `fabrication/`: `uwat-stellaNova-gerbers.zip` is what you upload to the PCB fab. `gerbers/` holds the same files unzipped,',
             '  plus the drill map PDFs. `uwat-stellaNova-CPL-top.csv` is the pick-and-place file for machine assembly.',
             '- `bom/`: `uwat-stellaNova_revA_BOM.xlsx` (prices, order quantities, notes), `uwat-stellaNova_revA_DigiKey_upload.csv`',
             '  (upload in DigiKey BOM Manager), plus a plain CSV BOM and a JLCPCB-style BOM.',
             '- `docs/`: schematic PDF and PNG, layout, assembly and 3D renders, and a STEP model of the assembled board.',
             '- `AUDIT.md`: design audit results. `generator-scripts/`: the scripts that built the design, for reference only.', '',
             '## Ordering the PCB (JLCPCB)', '',
             '- Upload `fabrication/uwat-stellaNova-gerbers.zip`. Layers: 4. Thickness: 1.6 mm. Outer copper: 1 oz. Inner copper: 0.5 oz.',
             '- Default JLCPCB 4-layer stackup is fine (no impedance control needed, USB here is full speed).',
             '- Surface finish: lead-free HASL works. ENIG gives flatter pads for the ESP32 module and USB-C if hand soldering.',
             '- Any solder mask color. Vias are tented in the files.', '',
             '## Board', '',
             f'- {W:g} x {H:g} mm, 4 layers (F.Cu signal, In1 GND, In2 3.3 V, B.Cu signal), 1.6 mm FR4',
             '- ESP32 antenna overhangs the top edge by 6 mm (Espressif\'s preferred placement). Keep metal 15 mm away.',
             '- No mounting holes. The board hangs from its smart cable.',
             '- All parts on the top side, so single-sided assembly. Test pads are on the back.',
             '- USB-C alone gives the 500 mA USB 2.0 default. Worst case the board draws about 480 mA from it,',
             '  so use a powered hub or the brain for long WiFi sessions. R22 keeps VBUS at 0 V on port power',
             '  so a laptop still attaches when plugged in later.',
             '- C6 (220 uF bulk) is not fitted: the buck datasheet characterises 22 to 68 uF of output',
             '  capacitance. Fit it only if a load-step test shows a dip on 3.3 V.', '',
             '- U3 is MAX33071EASA+: its A/B pins survive +/-65 V even unpowered, so a miswired or damaged',
             '  smart cable cannot kill it. ST3485EBDR (497-2080-1-ND, about $2.49) is a cheaper drop-in with',
             '  the same pinout, but its bus pins are only rated 14 V.',
             '- J1 pin field: other nets keep 0.5 mm from J1\'s pins (custom rule in the .kicad_dru), so a solder',
             '  bridge on the hand-soldered jack cannot reach USB or a GPIO.',
             '- Battery copper (VBAT_PORT and the fuse to diode link) keeps 0.5 mm from every other net ("Battery"',
             '  net class), so a bridge or debris cannot put 14 V on an ESP32 pin.',
             '- 3.3 V buck: the 10 uF input cap sits right across the U2 VIN and GND pins, the switch node runs',
             '  straight out to L1, and the output caps sit next to L1. Feedback is on the far side, away from SW.',
             '- SW1 (RESET) and SW2 (BOOT) are C&K PTS810 push buttons. Per the datasheet, pins 1 and 2 are tied',
             '  together, pins 3 and 4 are tied together, and pressing the button joins the two pairs. The',
             '  footprint and wiring match that.',
             '- Do not populate parts (C6, R2, R4) have no paste openings and are left out of the placement file.', '',
             '## Things to know when writing firmware or using it', '',
             '- RS-485 echo: the receiver is always on (RE tied low), so the ESP32 hears its own transmissions on',
             '  RX. Throw away the echoed bytes after each send, or use them to check for bus collisions.',
             '- IO39 to IO42 go to the microSD card, so pin JTAG is not available. Use the built in USB JTAG.',
             '- When the board runs from the smart port with USB unplugged, the USB protection chip lets the D+',
             '  pull-up lift VBUS to about 2 V. Some USB-C to USB-C laptop ports will not turn on until VBUS is',
             '  near 0 V. If a laptop does not see the board, plug USB in first, then the smart cable.', '',
             '## If you use JLCPCB assembly', '',
             '- The BOM lists DigiKey parts. Match each line to an LCSC part in the JLCPCB tool, or hand solder.',
             '- Check every part rotation in the JLCPCB placement preview. KiCad and JLCPCB do not always agree',
             '  on the zero angle, especially for the ESP32 module, USB-C, the diodes and the LEDs.',
             '- J1 (smart port jack) is through-hole. Hand solder it after assembly.', '',
             '## Check before first power-up', '',
             '0. Before ordering, print `docs/uwat-stellaNova-1to1-print.pdf` at 100% scale (not "fit to page")',
             '   and set a real Molex 43202-4101 jack on it. Its pins and the two pegs must line up with the holes.',
             '1. Jack pin map: 1 = RS-485 A, 2 = RS-485 B, 3 = GND, 4 = battery. Contact order is A, B, GND, + as',
             '   on the labelled smart cable photo on the VEX Forum (black A, red B, green GND, yellow +).',
             '   VEX smart cables are straight-through.',
             '2. On the first board, plug a smart cable into J1 and beep each wire through to the pads on the back:',
             '   black to J1.1, red to J1.2, green to J1.3, yellow to J1.4. Also beep each button: SW1 should',
             '   short EN to GND only while pressed, SW2 should short IO0 to GND only while pressed.',
             '3. Power from USB-C first: 3.3 V on TP2. Then plug into the brain with USB unplugged. The PWR LED',
             '   should light. If it does not, unplug: nothing is damaged (D2 blocks reverse, U3 is 65 V rated).',
             '4. Scope A/B during bring-up and confirm the brain releases the bus between transmissions.',
             '5. Load-step 3.3 V (50 to 400 mA) at 10 V and 14.6 V in. Fit C6 only if it dips.', '',
             '## Firmware pin map', '',
             '| Function | GPIO |', '|---|---|',
             '| RS-485 RX / DE / TX | IO9 / IO10 / IO11 (UART RS485 half-duplex mode, RTS = IO10) |',
             '| USB D- / D+ | IO19 / IO20 (USB Serial/JTAG) |',
             '| microSD CLK / CMD / D0 / D1 / D2 / D3 | IO40 / IO41 / IO39 / IO38 / IO2 / IO42 |',
             '| microSD card detect | IO1 (low = card in) |',
             '| LEDs LINK / ACT | IO13 / IO14 (high = on) |',
             '| BOOT / RESET | IO0 / EN |',
             '| UART0 TX / RX (back pads) | IO43 / IO44 |', '',
             'Module is ESP32-S3-WROOM-1-N16R2: set PSRAM to Quad (QSPI) mode, not Octal.', '',
             'Brain side: `vexGenericSerialEnable(port, 0)` then `vexGenericSerialBaudrate(port, 230400)`, or `pros::Serial`.', '',
             '## Verification', '',
             f'- Schematic connectivity check (ERC rules on the KiCad netlist): {erc_errors} errors',
             f'- PCB DRC (KiCad 7 engine): {drc_counts.get("DRC violations", "?")} violations, '
             f'{drc_counts.get("unconnected pads", "?")} unconnected',
             f'- Schematic to PCB parity: {parity}',
             '- Opens in KiCad 7, 8 and 9. KiCad 8/9 will offer to upgrade the files on first save.', '',
             '## BOM (DigiKey Canada, checked 2026-10-30)', '', '| Qty | Refs | Value | MPN | DigiKey CA | Stock | CAD qty 1 |', '|---|---|---|---|---|---|---|']
    for r in rows:
        if r['fit']:
            L = r['L']
            st = STOCK.get(r['line'], ('', '', ''))
            lines.append(f"| {len(r['fit'])} | {' '.join(r['fit'])} | {L['value']} | {L['mfr']} {L['mpn']} | {L['dk']} | {st[0]:,} | ${st[1]:.2f} |")
    dnp = [ref for r in rows for ref in r['dnp']]
    lines += ['', f'Do not populate: {" ".join(dnp)}', '']
    open(os.path.join(OUT, 'README.md'), 'w').write('\n'.join(lines) + '\n')


def layout_views(rd):
    """2D board views, KiCad editor style: copper + pads + outlines + reference labels."""
    import numpy as np
    import pcbnew
    from PIL import Image
    tmp = os.path.join(OUT, '_tmp_layout'); os.makedirs(tmp, exist_ok=True)
    b = pcbnew.LoadBoard(PCB)
    for z in [z for z in b.Zones() if not z.GetIsRuleArea()]:   # pours hide the tracks
        b.Remove(z)
    nz = os.path.join(tmp, 'nopour.kicad_pcb'); pcbnew.SaveBoard(nz, b)
    PX = 60   # pixels per mm

    def mask(layers):
        svg = os.path.join(tmp, layers.replace(',', '_') + '.svg'); png = svg[:-4] + '.png'
        run('kicad-cli', 'pcb', 'export', 'svg', '-l', layers + ',Edge.Cuts', '--page-size-mode', '2',
            '--exclude-drawing-sheet', '--black-and-white', '-o', svg, nz)
        head = open(svg).read(4000)
        import re as _re
        wmm = float(_re.search(r'width="([\d.]+)mm"', head).group(1)); hmm = float(_re.search(r'height="([\d.]+)mm"', head).group(1))
        run('rsvg-convert', '-w', str(int(wmm * PX)), '-h', str(int(hmm * PX)), svg, '-o', png)
        return np.array(Image.open(png).convert('RGBA')).astype(float)[..., 3] / 255.0

    edge = mask('Edge.Cuts')
    def lay(name):
        return np.clip(mask(name) - edge, 0, 1)

    def compose(path, bg, stack, board_fill=None):
        img = np.zeros(edge.shape + (3,)); img[:] = bg
        if board_fill is not None:   # tint the board area so the outline reads clearly
            from scipy import ndimage
            inside = ndimage.binary_fill_holes(edge > 0.3)
            img[inside] = board_fill
        for m, col, a in stack:
            k = (m * a)[..., None]
            img = img * (1 - k) + np.array(col) / 255.0 * k
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        nonbg = np.any(np.abs(img - np.array(bg)) > 0.02, axis=2)
        ys, xs = np.nonzero(nonbg); m = 2 * PX
        im = im.crop((max(xs.min() - m, 0), max(ys.min() - m, 0), min(xs.max() + m, im.width), min(ys.max() + m, im.height)))
        im.save(path); print('wrote', path)

    fcu, bcu, fab, silk = lay('F.Cu'), lay('B.Cu'), lay('F.Fab'), lay('F.Silkscreen')
    bg = (0.0, 0.063, 0.137)
    compose(os.path.join(rd, f'{NAME}-layout-top.png'), bg,
            [(bcu, (77, 127, 196), 0.80), (fcu, (200, 52, 52), 0.90), (fab, (175, 175, 175), 0.95),
             (silk, (242, 237, 161), 0.95), (edge, (208, 210, 205), 1.0)])
    mask_f = lay('F.Mask')
    compose(os.path.join(rd, f'{NAME}-assembly-top.png'), (1.0, 1.0, 1.0),
            [(mask_f, (200, 200, 200), 1.0), (silk, (150, 150, 150), 0.8), (fab, (20, 20, 20), 1.0),
             (edge, (0, 0, 0), 1.0)], board_fill=(0.97, 0.97, 0.94))
    shutil.rmtree(tmp)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'gerbers'))
    comps, nets = load(NETLIST)
    rows = bom(comps)
    g = os.path.join(OUT, 'gerbers') + '/'
    run('kicad-cli', 'pcb', 'export', 'gerbers', '-l',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts',
        '--subtract-soldermask', '-o', g, PCB)
    run('kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '-u', 'mm', '--excellon-separate-th',
        '--generate-map', '--map-format', 'pdf', '-o', g, PCB)
    zp = os.path.join(OUT, f'{NAME}-gerbers.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(g)):
            if not fn.endswith('.pdf'):
                z.write(os.path.join(g, fn), fn)
    run('kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'front',
        '-o', os.path.join(OUT, f'{NAME}-CPL-top.csv'), PCB)
    run('kicad-cli', 'sch', 'export', 'pdf', '-o', os.path.join(OUT, f'{NAME}-schematic.pdf'), SCH)
    run('kicad-cli', 'pcb', 'export', 'pdf', '-l', 'F.Cu,F.Silkscreen,F.Fab,Edge.Cuts', '--black-and-white',
        '-o', os.path.join(OUT, f'{NAME}-1to1-print.pdf'), PCB)   # kicad-cli plots PCB PDFs at 1:1
    run('pdftoppm', '-r', '200', '-png', '-singlefile', os.path.join(OUT, f'{NAME}-schematic.pdf'),
        os.path.join(OUT, f'{NAME}-schematic'))
    # README with live verification numbers
    import re as _re
    from erc import check
    _, _, errs, _ = check(NETLIST, os.path.join(os.path.dirname(__file__), 'nc_pins.json'))
    rpt = open(os.path.join(PRJ, NAME + '-drc.rpt')).read()
    counts = {k: int(v) for v, k in _re.findall(r'\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)', rpt)}
    from pcb import W, H
    import pcbnew
    brd = pcbnew.LoadBoard(PCB)
    pad_net = {(n['ref'], n['pin']): name for name, nodes in nets.items() for n in nodes}
    fps = list(brd.GetFootprints())
    bad = sum(1 for fp in fps for pd in fp.Pads() if pd.GetNumber() and pad_net.get((fp.GetReference(), pd.GetNumber()), pd.GetNetname()) != pd.GetNetname())
    parity = f'{len(fps)} of {len(comps)} footprints, {bad} pad net mismatches'
    readme(rows, counts, len(errs), (W, H), parity)
    # KiCad project copy (sources only)
    kp = os.path.join(OUT, 'kicad-project')
    os.makedirs(kp)
    for fn in os.listdir(PRJ):
        src = os.path.join(PRJ, fn)
        if fn.endswith(('.dsn', '.ses', '-bak', '.lck')) or fn.startswith(('_autosave', '~')):
            continue
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(kp, fn))
        else:
            shutil.copy(src, kp)
    # 3D: STEP with all models, then textured renders
    step = os.path.join(OUT, f'{NAME}.step')
    run('kicad-cli', 'pcb', 'export', 'step', '--subst-models', '-f', '-o', step, PCB)
    rd = os.path.join(OUT, 'renders'); os.makedirs(rd)
    layout_views(rd)
    run('xvfb-run', '-a', '-s', '-screen 0 2200x1900x24', '/usr/local/bin/python3',
        os.path.join(os.path.dirname(__file__), 'render3d.py'), PCB, step, os.path.join(rd, NAME))
    for fn in os.listdir(rd):
        if '-tex-' in fn:
            os.remove(os.path.join(rd, fn))
    print('BOM lines', len(rows), 'outputs in', OUT, 'DRC', counts, 'ERC errors', len(errs))

if __name__ == '__main__':
    main()
