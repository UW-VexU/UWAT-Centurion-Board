"""Import a Freerouting .ses into the board, add outer GND pours, fill, run DRC.

/usr/bin/python3 finish.py <board.kicad_pcb> <routes.ses>
"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
from sexp import parse, find, findall

mm = pcbnew.FromMM


def import_ses(board, ses_path):
    t = parse(open(ses_path).read())
    routes = find(t, 'routes')
    res = find(routes, 'resolution')
    unit, per = str(res[1]), float(res[2])
    scale = {'um': 1000.0, 'mm': 1e6, 'mil': 25400.0}[unit] / per      # SES units -> nm
    layers = {board.GetLayerName(l): l for l in range(pcbnew.PCB_LAYER_ID_COUNT)}
    vias = tracks = 0
    lib = find(routes, 'library_out')
    padstacks = {}
    if lib:
        for ps in findall(lib, 'padstack'):
            m = re.search(r'_(\d+):(\d+)_um', ps[1])
            if m:
                padstacks[ps[1]] = (int(m.group(1)), int(m.group(2)))
    for net in findall(find(routes, 'network_out'), 'net'):
        name = net[1]
        ni = board.FindNet(name)
        if ni is None:
            raise KeyError(f'net {name} not on board')
        for w in findall(net, 'wire'):
            path = find(w, 'path')
            layer = layers[str(path[1])]
            width = int(float(path[2]) * scale)
            coords = [float(c) for c in path[3:] if not isinstance(c, list)]
            pts = [(int(coords[i] * scale), int(-coords[i + 1] * scale)) for i in range(0, len(coords), 2)]
            for a, b in zip(pts, pts[1:]):
                if a == b:
                    continue
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(*a)); tr.SetEnd(pcbnew.VECTOR2I(*b))
                tr.SetWidth(width); tr.SetLayer(layer); tr.SetNet(ni)
                board.Add(tr); tracks += 1
        for v in findall(net, 'via'):
            ps = v[1]
            x, y = float(v[2]), float(v[3])
            d, dr = padstacks.get(ps, (600, 300))
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(int(x * scale), int(-y * scale)))
            via.SetWidth(mm(d / 1000)); via.SetDrill(mm(dr / 1000)); via.SetNet(ni)
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            board.Add(via); vias += 1
    return tracks, vias


def remove_dangling(board):
    """Iteratively drop track segments with a free end (router leftovers)."""
    removed = 0
    while True:
        pts = {}
        tracks = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
        vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
        for t in tracks:
            for p in (t.GetStart(), t.GetEnd()):
                k = (p.x, p.y, t.GetLayer()); pts[k] = pts.get(k, 0) + 1
        pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
        def anchored(p, layer, net):
            for v in vias:
                if v.GetNetCode() == net and (v.GetPosition() - p).EuclideanNorm() <= v.GetWidth() // 2:
                    return True
            for pd in pads:
                if pd.GetNetCode() == net and pd.IsOnLayer(layer) and pd.HitTest(p):
                    return True
            return False
        dead = []
        for t in tracks:
            for p in (t.GetStart(), t.GetEnd()):
                if pts[(p.x, p.y, t.GetLayer())] == 1 and not anchored(p, t.GetLayer(), t.GetNetCode()):
                    dead.append(t); break
        if not dead:
            return removed
        for t in dead:
            board.Remove(t); removed += 1


def outer_pours(board):
    gnd = board.FindNet('GND')
    from pcb import OX, OY, W, H
    x0, y0, x1, y1 = mm(OX), mm(OY), mm(OX + W), mm(OY + H)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd)
        ol = z.Outline(); ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(x, y)
        z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.25)); z.SetThermalReliefSpokeWidth(mm(0.3))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(0)
        z.SetZoneName('GND pour ' + board.GetLayerName(layer))
        board.Add(z)


def fill(board):
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def drc(board, path):
    pcbnew.WriteDRCReport(board, path, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(path).read()
    counts = {k: int(v) for v, k in re.findall(r'\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)', txt)}
    return txt, counts


if __name__ == '__main__':
    pcb, ses = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(pcb)
    # the SES holds only new routing; locked fanout and stitching copper stays as placed
    n_t, n_v = import_ses(board, ses)
    n_dead = remove_dangling(board)
    print('removed dangling segments:', n_dead)
    if '--pours' in sys.argv:
        outer_pours(board)
    fill(board)
    pcbnew.SaveBoard(pcb, board)
    board = pcbnew.LoadBoard(pcb)
    rpt = pcb.replace('.kicad_pcb', '-drc.rpt')
    txt, counts = drc(board, rpt)
    # second pass: drop any segment DRC still calls dangling, then refill and re-check
    dang = re.findall(r'\[track_dangling\].*?\n.*?\n\s*@\(([\d.]+) mm, ([\d.]+) mm\): Track \[([^\]]*)\] on (\S+), length ([\d.]+) mm', txt)
    if dang:
        for x, y, net, layer, ln in dang:
            pt = pcbnew.VECTOR2I(mm(float(x)), mm(float(y)))
            for t in list(board.GetTracks()):
                if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == net and board.GetLayerName(t.GetLayer()) == layer \
                   and abs(pcbnew.ToMM(t.GetLength()) - float(ln)) < 0.01 and t.HitTest(pt):
                    board.Remove(t); break
        fill(board); pcbnew.SaveBoard(pcb, board)
        board = pcbnew.LoadBoard(pcb)
        txt, counts = drc(board, rpt)
        print('removed', len(dang), 'dangling segments reported by DRC')
    print(f'imported {n_t} track segments, {n_v} vias')
    print('DRC:', counts)
