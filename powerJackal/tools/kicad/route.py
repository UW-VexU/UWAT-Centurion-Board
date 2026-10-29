"""Autoroute with Freerouting, import the session, add pours and hole keepouts, fill, save.
usage: python3 route.py <board.kicad_pcb> <workdir> [passes]"""
import sys, os, re, subprocess, math
import pcbnew
from pcb_common import *

PCB, WORK = sys.argv[1], sys.argv[2]
PASSES = sys.argv[3] if len(sys.argv) > 3 else "60"
JAR = os.path.join(WORK, "freerouting.jar")

def sexp(text):
    tokens = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    stack = [[]]
    for t in tokens:
        if t == "(": stack.append([])
        elif t == ")": x = stack.pop(); stack[-1].append(x)
        else: stack[-1].append(t.strip('"'))
    return stack[0][0]

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def autoroute(board):
    dsn, ses = os.path.join(WORK, "jk.dsn"), os.path.join(WORK, "jk.ses")
    if os.path.exists(ses): os.remove(ses)
    pcbnew.ExportSpecctraDSN(board, dsn)
    r = subprocess.run(["xvfb-run", "-a", "java", "-jar", JAR, "-de", dsn, "-do", ses, "-mp", PASSES, "-inc", "Ground", "-dct", "0", "-da"],
                       cwd=WORK, capture_output=True, text=True, timeout=1800)
    open(os.path.join(WORK, "fr.log"), "w").write(r.stdout + r.stderr)
    return ses

def import_ses(board, ses):
    s = sexp(open(ses).read())
    routes = find(s, "routes")[0]
    res = float(find(routes, "resolution")[0][2])   # units per um
    k = 1.0 / res / 1000.0                          # -> mm
    nets = {board.GetNetInfo().GetNetItem(i).GetNetname(): board.GetNetInfo().GetNetItem(i) for i in range(board.GetNetCount())}
    n_t = n_v = 0
    for net in find(find(routes, "network_out")[0], "net"):
        ni = nets[net[1]]
        for w in find(net, "wire"):
            path = find(w, "path")[0]
            layer = pcbnew.F_Cu if path[1] == "F.Cu" else pcbnew.B_Cu
            width = float(path[2]) * k
            c = [float(v) * k for v in path[3:]]
            pts = [(c[i], -c[i + 1]) for i in range(0, len(c), 2)]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
                t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(ni); board.Add(t); n_t += 1
        for v in find(net, "via"):
            m = re.search(r"_(\d+):(\d+)_um", v[1]); d, dr = int(m.group(1)) / 1000, int(m.group(2)) / 1000
            x, y = float(v[2]) * k, -float(v[3]) * k
            via = pcbnew.PCB_VIA(board); via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); via.SetWidth(mm(d)); via.SetDrill(mm(dr))
            via.SetNet(ni); board.Add(via); n_v += 1
    return n_t, n_v

def drc(board, path):
    pcbnew.WriteDRCReport(board, path, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(path).read()
    items = []
    for blk in re.split(r"\n(?=\[)", txt):
        m = re.match(r"\[(\w+)\]", blk)
        if not m: continue
        locs = [(float(a), float(b2)) for a, b2 in re.findall(r"@\(([-\d.]+) mm, ([-\d.]+) mm\)", blk)]
        items.append((m.group(1), locs, blk))
    return items

def repair(board, rounds=4):
    """Rip up router tracks involved in clearance errors, then let Freerouting finish whatever is open."""
    for r in range(rounds):
        items = drc(board, os.path.join(WORK, "drc_route.txt"))
        bad = [i for i in items if i[0] in ("clearance", "shorting_items", "tracks_crossing", "hole_clearance", "copper_edge_clearance")]
        open_ = [i for i in items if i[0] == "unconnected_items" and "Zone" not in i[2] and "[GND]" not in i[2]]
        print(f"repair round {r}: {len(bad)} clearance, {len(open_)} open")
        if not bad and not open_: return True
        kill = set()
        if r >= 1:   # opens that survived a round: clear unlocked copper around both ends so the router has room
            for kind, locs, blk in open_:
                for (x, y) in locs:
                    for t in board.GetTracks():
                        if t.IsLocked(): continue
                        bb = t.GetBoundingBox(); bb.Inflate(mm(3.0))
                        if bb.Contains(pcbnew.VECTOR2I(mm(x), mm(y))): kill.add(t.m_Uuid.AsString())
        for kind, locs, blk in bad:
            for t in board.GetTracks():
                if t.IsLocked(): continue
                for (x, y) in locs:
                    if t.GetClass() == "PCB_TRACK" and t.HitTest(pcbnew.VECTOR2I(mm(x), mm(y)), mm(0.05)): kill.add(t.m_Uuid.AsString())
                    if t.GetClass() == "PCB_VIA" and math.dist(toloc(t.GetPosition()), (x - OX, y - OY)) < 0.05: kill.add(t.m_Uuid.AsString())
        for t in list(board.GetTracks()):
            if t.m_Uuid.AsString() in kill: board.Remove(t)
        ses = autoroute(board)
        for t in list(board.GetTracks()):
            if not t.IsLocked(): board.Remove(t)
        import_ses(board, ses)
    return False

def unconnected(board):
    board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(False)

def drop_dangling_router_tracks(board):
    """Delete short router segments that end in the air (left over where the router met a pre-route mid-segment).
    A segment is only dropped if the board has no more open connections without it."""
    n = 0
    for _ in range(5):
        items = drc(board, os.path.join(WORK, "drc_dangle.txt"))
        pts = [locs[0] for kind, locs, blk in items if kind == "track_dangling" and locs]
        if not pts: break
        cands = [t for t in list(board.GetTracks()) if t.GetClass() == "PCB_TRACK" and not t.IsLocked()
                 and any(t.HitTest(pcbnew.VECTOR2I(mm(x), mm(y)), mm(0.05)) for (x, y) in pts)]
        base = unconnected(board); dropped = 0
        for t in cands:
            board.Remove(t)
            if unconnected(board) > base: board.Add(t)   # it carries a real connection: keep it
            else: dropped += 1
        n += dropped
        if not dropped: break
    return n

def zone(board, net, layer, pts, prio=0, clearance=0.25, conn=pcbnew.ZONE_CONNECTION_THERMAL, name=""):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if net is not None: z.SetNetCode(net.GetNetCode())
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(OX + x), mm(OY + y))
    z.SetLocalClearance(mm(clearance)); z.SetMinThickness(mm(0.25))
    z.SetPadConnection(conn); z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.45))
    z.SetAssignedPriority(prio)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name: z.SetZoneName(name)
    board.Add(z); return z

def keepout(board, cx, cy, r, n=32):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True); z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for i in range(n):
        a = 2 * math.pi * i / n; o.Append(mm(OX + cx + r * math.cos(a)), mm(OY + cy + r * math.sin(a)))
    z.SetZoneName("hole keepout"); board.Add(z)

def net(board, name): return board.FindNet(name)

def edge_keepout(board, m=0.5):
    """Thin no-track, no-via frame along the board edge so the router stays clear of it."""
    for x0, y0, x1, y1 in ((0, 0, W, m), (0, H - m, W, H), (0, 0, m, H), (W - m, 0, W, H)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True); z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): o.Append(mm(OX + x), mm(OY + y))
        z.SetZoneName("edge keepout"); board.Add(z)

def prune_dangling(board):
    """Remove pre-route stubs whose via the router never used (via touched by tracks on one layer only)."""
    removed = 0
    while True:
        tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
        vias = [v for v in board.GetTracks() if v.GetClass() == "PCB_VIA" and v.IsLocked()]   # only our own escape vias
        pads = list(board.GetPads())
        def touching(pt, layer=None):
            return [t for t in tracks if (t.GetStart() == pt or t.GetEnd() == pt) and (layer is None or t.GetLayer() == layer)]
        dead = None
        for v in vias:
            p = v.GetPosition()
            if v.GetNetname() == "GND": continue
            lay = {t.GetLayer() for t in touching(p)}
            if len(lay) < 2: dead = v; break
        if dead is None: break
        p = dead.GetPosition(); board.Remove(dead); removed += 1
        # walk back along the stub to its pad
        while True:
            ts = touching(p)
            if len(ts) != 1: break
            t = ts[0]
            if not t.IsLocked(): break
            q = t.GetEnd() if t.GetStart() == p else t.GetStart()
            board.Remove(t); tracks.remove(t)
            if any(pd.HitTest(q) for pd in pads) or len(touching(q)) != 1: break
            p = q
    return removed

def pours(board):
    g = net(board, "GND")
    full = [(0, 0), (W, 0), (W, H), (0, H)]
    zone(board, g, pcbnew.F_Cu, full, 0, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL, name="GND top")
    zone(board, g, pcbnew.B_Cu, full, 0, conn=pcbnew.ZONE_CONNECTION_THT_THERMAL, name="GND bottom")
    U1 = board.FindFootprintByReference("U1")
    ux, uy = toloc(U1.GetPosition())
    # TPSM53602: VIN pads (left edge) out to C2, C3 and C8, VOUT pads (right edge) out to C4 and C5
    zone(board, net(board, "/VIN_MOD"), pcbnew.F_Cu, [(ux - 5.2, uy - 3.6), (ux - 1.85, uy - 3.6), (ux - 1.85, uy + 3.6), (ux - 5.2, uy + 3.6)], 2, conn=pcbnew.ZONE_CONNECTION_FULL, name="VIN_MOD")
    zone(board, net(board, "/5V_MOD"), pcbnew.F_Cu, [(ux + 1.9, uy - 3.2), (ux + 5.1, uy - 3.2), (ux + 5.1, uy + 3.3), (ux + 1.9, uy + 3.3)], 2, conn=pcbnew.ZONE_CONNECTION_FULL, name="5V_MOD")
    U1.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    board.FindFootprintByReference("J7").SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

def fill(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

def stitch(board, pitch=2.54, ring=0.5):
    """Drop GND vias wherever both GND pours have room, on a grid, plus at least one per isolated top or bottom fragment."""
    g = net(board, "GND")
    zt = [z for z in board.Zones() if z.GetZoneName() == "GND top"][0]
    zb = [z for z in board.Zones() if z.GetZoneName() == "GND bottom"][0]
    pt, pb = zt.GetFilledPolysList(pcbnew.F_Cu), zb.GetFilledPolysList(pcbnew.B_Cu)
    drills = [toloc(v.GetPosition()) for v in board.GetTracks() if v.GetClass() == "PCB_VIA"]
    drills += [toloc(p.GetPosition()) for p in board.GetPads() if p.GetDrillSize().x > 0]
    pads = [p.GetBoundingBox() for p in board.GetPads()]
    def ok(x, y):
        for k in range(9):
            dx, dy = (0, 0) if k == 0 else (ring * math.cos(k * math.pi / 4), ring * math.sin(k * math.pi / 4))
            v = pcbnew.VECTOR2I(mm(OX + x + dx), mm(OY + y + dy))
            if not pt.Contains(v) or not pb.Contains(v): return False
        if any(math.dist((x, y), d) < 1.3 for d in drills): return False
        v = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
        for bb in pads:
            bb2 = pcbnew.BOX2I(bb.GetOrigin(), bb.GetSize()); bb2.Inflate(mm(0.35))
            if bb2.Contains(v): return False
        return True
    added = []
    def add(x, y):
        via = pcbnew.PCB_VIA(board); via.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))); via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3))
        via.SetNet(g); board.Add(via); drills.append((x, y)); added.append((x, y))
    n = int(W / pitch)
    for i in range(1, n + 1):
        for j in range(1, int(H / pitch) + 1):
            x, y = i * pitch - 0.6, j * pitch - 0.6
            if ok(x, y): add(x, y)
    # fragments that the grid missed: search them on a fine grid
    for poly, other in ((pt, pb), (pb, pt)):
        for k in range(poly.OutlineCount()):
            ol = poly.Outline(k)
            bb = ol.BBox()
            x0, y0 = pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY
            x1, y1 = pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY
            if any(x0 <= a <= x1 and y0 <= b2 <= y1 and ol.PointInside(pcbnew.VECTOR2I(mm(OX + a), mm(OY + b2))) for a, b2 in added): continue
            done = False
            y = y0 + 0.4
            while y < y1 and not done:
                x = x0 + 0.4
                while x < x1:
                    if ol.PointInside(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))) and ok(x, y): add(x, y); done = True; break
                    x += 0.25
                y += 0.25
    # last resort for fragments still cut off from the main GND body: fine search with tighter margins
    for k in range(3):
        iso = isolated(board, pt, pb)
        if not iso: break
        for ol in iso:
            bb = ol.BBox()
            x0, y0 = pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY
            x1, y1 = pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY
            best = None
            y = y0 + 0.2
            while y < y1:
                x = x0 + 0.2
                while x < x1:
                    v = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
                    if ol.PointInside(v) and all(ol.PointInside(pcbnew.VECTOR2I(mm(OX + x + 0.33 * math.cos(a)), mm(OY + y + 0.33 * math.sin(a)))) and
                                                 pt.Contains(pcbnew.VECTOR2I(mm(OX + x + 0.33 * math.cos(a)), mm(OY + y + 0.33 * math.sin(a)))) and pb.Contains(pcbnew.VECTOR2I(mm(OX + x + 0.33 * math.cos(a)), mm(OY + y + 0.33 * math.sin(a)))) for a in [i * math.pi / 4 for i in range(8)]) \
                       and all(math.dist((x, y), d) > 0.9 for d in drills) and not any(pcbnew.BOX2I(bb2.GetOrigin(), bb2.GetSize()).Contains(v) for bb2 in pads):
                        best = (x, y); break
                    x += 0.1
                if best: break
                y += 0.1
            if best: add(*best)
        fill(board)
        pt, pb = zt.GetFilledPolysList(pcbnew.F_Cu), zb.GetFilledPolysList(pcbnew.B_Cu)
    left = isolated(board, pt, pb)
    if left: print("still isolated GND fragments:", len(left))
    return len(added)

def isolated(board, pt, pb):
    frags = [pt.Outline(i) for i in range(pt.OutlineCount())] + [pb.Outline(i) for i in range(pb.OutlineCount())]
    links = [v.GetPosition() for v in board.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
    links += [p.GetPosition() for p in board.GetPads() if p.GetNetname() == "GND" and p.GetDrillSize().x > 0]
    par = list(range(len(frags)))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for p in links:
        hit = [k for k, o in enumerate(frags) if o.PointInside(p)]
        for k in hit[1:]: par[f(k)] = f(hit[0])
    groups = {}
    for k in range(len(frags)): groups.setdefault(f(k), []).append(k)
    main = max(groups.values(), key=lambda g: sum(abs(frags[k].Area()) for k in g))
    return [frags[k] for g in groups.values() if g is not main for k in g]

if __name__ == "__main__":
    b = pcbnew.LoadBoard(PCB)
    edge_keepout(b)
    for hx, hy in HOLES: keepout(b, hx, hy, 4.2)
    if "--noroute" not in sys.argv:
        ses = autoroute(b)
        print("tracks, vias:", import_ses(b, ses))
        print("clean:", repair(b))
        print("dangling stubs removed:", prune_dangling(b))
        from gen_pcb import kelvin_finish
        kelvin_finish(b)
        print("dangling router segments removed:", drop_dangling_router_tracks(b))
        print("open connections after cleanup:", unconnected(b))
    pours(b); fill(b)
    print("stitch vias:", stitch(b)); fill(b)
    pcbnew.SaveBoard(PCB, b)
    print("saved", PCB)
