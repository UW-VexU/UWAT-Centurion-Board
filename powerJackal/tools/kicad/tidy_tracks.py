"""Tidy routed tracks without re-routing:
  1. drop router leftovers: tiny segments, segments lying on top of other segments, and split straight runs
  2. turn acute side branches into square T joints (branch moved along the run so it leaves at 90 degrees)
  3. miter every open 90 degree bend into two 45 degree bends (also a V with a stub at its tip, like a test pad tap)
Bends hidden under a pad or a via are left alone, the copper there is the pad or the via.
The geometry is edited on the board file's segment records (deleting items through pcbnew corrupts the board),
then pcbnew loads the result only to refill the pours.
usage: python3 tidy_tracks.py in.kicad_pcb out.kicad_pcb [scale.json]
scale.json maps a corner key "x,y,layer" to a chamfer scale (1 full, 0.5 half, 0 leave the corner as it is)."""
import sys, re, math, json, uuid, collections
import pcbnew
from pcb_common import OX, OY

IN, OUT = sys.argv[1], sys.argv[2]
SCALE = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
NM = 1_000_000
def nm(v): return int(round(float(v) * NM))
def mm_s(v): return f"{v / NM:.6f}".rstrip("0").rstrip(".")

txt = open(IN).read()
SEG_RE = re.compile(r'^  \(segment( locked)? \(start (\S+) (\S+)\) \(end (\S+) (\S+)\) \(width (\S+)\) \(layer "([^"]+)"\) \(net (\d+)\) \(tstamp [^)]+\)\)\n', re.M)

class Seg:
    __slots__ = ("a", "b", "w", "layer", "net", "locked", "made")
    def __init__(s, a, b_, w, layer, net, locked): s.a, s.b, s.w, s.layer, s.net, s.locked, s.made = a, b_, w, layer, net, locked, False
S = [Seg((nm(m[2]), nm(m[3])), (nm(m[4]), nm(m[5])), nm(m[6]), m[7], int(m[8]), bool(m[1])) for m in SEG_RE.finditer(txt)]
n_in = len(S)

brd = pcbnew.LoadBoard(IN)   # read only: pads and vias
LAYER_ID = {brd.GetLayerName(i): i for i in (pcbnew.F_Cu, pcbnew.B_Cu)}
PADS = list(brd.GetPads())
VIAS = {(v.GetPosition().x, v.GetPosition().y) for v in brd.GetTracks() if v.GetClass() == "PCB_VIA"}
_padcache = {}
def pad_at(layer, p, net):
    k = (layer, p, net)
    if k not in _padcache:
        v = pcbnew.VECTOR2I(int(p[0]), int(p[1])); L = LAYER_ID[layer]; _padcache[k] = None
        for pd in PADS:
            if pd.GetNetCode() == net and pd.IsOnLayer(L) and pd.HitTest(v): _padcache[k] = pd; break
    return _padcache[k]
def blocked(s, p): return p in VIAS or pad_at(s.layer, p, s.net) is not None

log = collections.Counter(); mods = []
def end_pt(s, e): return s.a if e == 0 else s.b
def far_pt(s, e): return s.b if e == 0 else s.a
def set_pt(s, e, p):
    if e == 0: s.a = p
    else: s.b = p
def length(s): return math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1])
def unit(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); return (dx / L, dy / L) if L else (0.0, 0.0)
def dot(u, v): return u[0] * v[0] + u[1] * v[1]
def ip(x, y): return (int(round(x)), int(round(y)))
def nodes():
    m = collections.defaultdict(list)
    for s in S:
        for e in (0, 1): m[(s.layer,) + end_pt(s, e)].append((s, e))
    return m
def ckey(layer, x, y): return f"{x / NM - OX:.2f},{y / NM - OY:.2f},{layer}"
def add_like(s, a, b_, w=None):
    n = Seg(a, b_, w or s.w, s.layer, s.net, s.locked); S.append(n); return n
def on_seg(p, s, tol):
    a, c = s.a, s.b; L2 = (c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2
    if L2 == 0: return math.hypot(p[0] - a[0], p[1] - a[1]) <= tol
    k = ((p[0] - a[0]) * (c[0] - a[0]) + (p[1] - a[1]) * (c[1] - a[1])) / L2
    if k < -1e-6 or k > 1 + 1e-6: return False
    return math.hypot(a[0] + k * (c[0] - a[0]) - p[0], a[1] + k * (c[1] - a[1]) - p[1]) <= tol

# ---------------- 1. leftovers
TINY = 0.05 * NM
def collapse_tiny():
    m = nodes()
    for s in S:
        if length(s) >= TINY: continue
        a, c = s.a, s.b
        if a == c: S.remove(s); log["zero-length segment removed"] += 1; return True
        if a in VIAS and c in VIAS: continue
        ka = blocked(s, a) or len(m[(s.layer,) + a]) > 2
        kc = blocked(s, c) or len(m[(s.layer,) + c]) > 2
        keep, drop = (c, a) if (c in VIAS or (kc and not ka)) else (a, c)
        if drop in VIAS: continue
        for (o, e) in m[(s.layer,) + drop]:
            if o is not s: set_pt(o, e, keep)
        S.remove(s); log["tiny segment removed"] += 1; return True
    return False

def remove_overlaps():
    tol = 0.002 * NM
    for A in S:
        for B in S:
            if B is A or B.net != A.net or B.layer != A.layer or length(B) < length(A): continue
            if on_seg(A.a, B, tol) and on_seg(A.b, B, tol):
                if A.w > B.w: B.w = A.w
                m = nodes()
                for e in (0, 1):   # anything hanging off A's ends must land on a real node of B
                    p = end_pt(A, e)
                    others = [o for (o, _) in m[(A.layer,) + p] if o is not A and o is not B]
                    if others and p not in (B.a, B.b):
                        q = B.b; B.b = p; add_like(B, p, q)
                S.remove(A); log["overlapping segment removed"] += 1; return True
    return False

def merge_straight():
    m = nodes()
    for k, lst in m.items():
        if len(lst) != 2: continue
        (s1, e1), (s2, e2) = lst
        if s1 is s2 or s1.w != s2.w: continue
        p = end_pt(s1, e1)
        if blocked(s1, p): continue
        if dot(unit(p, far_pt(s1, e1)), unit(p, far_pt(s2, e2))) > -0.99995: continue
        set_pt(s1, e1, far_pt(s2, e2)); s1.locked = s1.locked or s2.locked; S.remove(s2)
        log["straight run merged"] += 1; return True
    return False
def clean():
    while collapse_tiny() or remove_overlaps() or merge_straight(): pass
clean()

# ---------------- 2. acute side branches -> square T joints
def fix_acute_branch():
    m = nodes()
    for k, lst in m.items():
        if len(lst) != 3: continue
        J = end_pt(*lst[0]); layer = lst[0][0].layer
        if blocked(lst[0][0], J) or SCALE.get(ckey(layer, *J), 1) == 0: continue
        U = [unit(J, far_pt(s, e)) for (s, e) in lst]
        for ia, ib, ic in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            if dot(U[ia], U[ib]) > -0.99995: continue                      # a and b form the straight run
            for run in (ib, ia):
                if dot(U[ic], U[run]) <= 0.01: continue                     # the branch leans toward this side
                tb, eb = lst[run]; tc, ec = lst[ic]
                K = far_pt(tc, ec); u = U[run]
                d = (K[0] - J[0]) * u[0] + (K[1] - J[1]) * u[1]; Lb = length(tb)
                if d <= 0.05 * NM or d > Lb + 0.02 * NM: continue
                q = far_pt(tb, eb)
                Jn = q if abs(d - Lb) <= 0.02 * NM else ip(J[0] + u[0] * d, J[1] + u[1] * d)
                if Jn != q: set_pt(tb, 1 - eb, Jn); add_like(tb, Jn, q)
                set_pt(tc, ec, Jn)
                mods.append(dict(kind="T joint", key=ckey(layer, *J), x=Jn[0] / NM - OX, y=Jn[1] / NM - OY))
                log["acute branch squared"] += 1; return True
    return False
while fix_acute_branch(): pass
clean()

def square_branch():
    m = nodes()
    for k, lst in m.items():
        if len(lst) != 3: continue
        J = end_pt(*lst[0]); layer = lst[0][0].layer
        key = ckey(layer, *J)
        if blocked(lst[0][0], J) or SCALE.get(key, 1) == 0: continue
        U = [unit(J, far_pt(s, e)) for (s, e) in lst]
        for ia, ib, ic in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            if dot(U[ia], U[ib]) > -0.99995: continue
            if max(dot(U[ic], U[ia]), dot(U[ic], U[ib])) <= 0.01: continue     # branch is not acute to the run
            tc, ec = lst[ic]; K = far_pt(tc, ec); u = U[ia]
            d = (K[0] - J[0]) * u[0] + (K[1] - J[1]) * u[1]
            M = ip(K[0] - u[0] * d, K[1] - u[1] * d)                        # J -> M square off the run, M -> K parallel to it
            if math.dist(J, M) < 0.05 * NM or math.dist(M, K) < 0.05 * NM: continue
            mk = unit(M, K)
            if any(abs(dot(mk, unit(K, far_pt(o, e)))) > 0.99 for (o, e) in m[(layer,) + K] if o is not tc): continue   # would lie on K's run
            set_pt(tc, 1 - ec, M); add_like(tc, M, K)    # tc now runs J -> M
            mods.append(dict(kind="branch squared", key=key, x=M[0] / NM - OX, y=M[1] / NM - OY))
            log["acute branch rebuilt square"] += 1; return True
    return False
while square_branch(): pass
clean()

# ---------------- 3. miter open 90 degree bends
def target(w): return max(0.5 * NM, 1.5 * w)
def miter_pass():
  plan = []
  for k, lst in nodes().items():
      J = end_pt(*lst[0]); s0 = lst[0][0]
      if blocked(s0, J): continue
      key = ckey(s0.layer, *J); sc = SCALE.get(key, 1)
      if sc == 0: continue
      U = [unit(J, far_pt(s, e)) for (s, e) in lst]
      pair = None
      if len(lst) == 2 and -0.087 <= dot(*U) < 0.985: pair = (0, 1, None)   # 95 degrees or sharper
      elif len(lst) == 3:
          for i, j, st in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
              if abs(dot(U[i], U[j])) < 0.02 and dot(U[st], U[i]) < -0.70 and dot(U[st], U[j]) < -0.70: pair = (i, j, st)   # V with a stub at its tip
      if not pair: continue
      i, j, st = pair; (si, ei), (sj, ej) = lst[i], lst[j]
      w = min(si.w, sj.w)
      c = min(target(w), 0.45 * length(si), 0.45 * length(sj)) * sc
      if c < 0.08 * NM: continue
      plan.append((si, ei, sj, ej, lst[st] if st is not None else None, J, c, w, key))
  for (si, ei, sj, ej, stub, J, c, w, key) in plan:
      ui, uj = unit(J, far_pt(si, ei)), unit(J, far_pt(sj, ej))
      A = ip(J[0] + ui[0] * c, J[1] + ui[1] * c); B = ip(J[0] + uj[0] * c, J[1] + uj[1] * c)
      set_pt(si, ei, A); set_pt(sj, ej, B); add_like(si, A, B, w)
      if stub: ss, es = stub; set_pt(ss, es, ip((A[0] + B[0]) / 2, (A[1] + B[1]) / 2))
      mods.append(dict(kind="miter" + (" with stub" if stub else ""), key=key, x=J[0] / NM - OX, y=J[1] / NM - OY))
      log["90 degree bend mitered" + (" (V with stub)" if stub else "")] += 1
  return len(plan)
def v_to_t():
    """A short V whose two legs continue as one straight line (a fork onto a vertical or horizontal run) becomes a plain T."""
    m = nodes()
    for k, lst in m.items():
        if len(lst) != 3: continue
        J = end_pt(*lst[0]); layer = lst[0][0].layer; key = ckey(layer, *J)
        if blocked(lst[0][0], J) or SCALE.get(key, 1) == 0: continue
        U = [unit(J, far_pt(s, e)) for (s, e) in lst]
        for i, j, st in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            if not (abs(dot(U[i], U[j])) < 0.02 and dot(U[st], U[i]) < -0.70 and dot(U[st], U[j]) < -0.70): continue
            (si, ei), (sj, ej), (ss, es) = lst[i], lst[j], lst[st]
            A, B = far_pt(si, ei), far_pt(sj, ej)
            if blocked(si, A) or blocked(sj, B): continue
            na = [(o, e) for (o, e) in m[(layer,) + A] if o is not si]; nb = [(o, e) for (o, e) in m[(layer,) + B] if o is not sj]
            if len(na) != 1 or len(nb) != 1: continue
            ab = unit(A, B)
            if dot(unit(A, far_pt(*na[0])), ab) > -0.999 or dot(unit(B, far_pt(*nb[0])), ab) < 0.999: continue
            if abs(dot(U[st], ab)) > 0.02: continue
            tt = (J[0] - A[0]) * ab[0] + (J[1] - A[1]) * ab[1]
            if not (0.05 * NM < tt < math.dist(A, B) - 0.05 * NM): continue
            Pp = ip(A[0] + ab[0] * tt, A[1] + ab[1] * tt)
            set_pt(si, ei, Pp); set_pt(sj, ej, Pp); set_pt(ss, es, Pp)
            mods.append(dict(kind="fork to T", key=key, x=J[0] / NM - OX, y=J[1] / NM - OY))
            log["fork turned into a T"] += 1; return True
    return False
while v_to_t(): pass
clean()
for _ in range(4):
    if not miter_pass(): break
    clean()
clean()

# ---------------- 4. straight pad entries: a diagonal into a pad becomes straight run, 45, straight stub along the pad axis
FPS = {}
for pd in PADS:
    fp = pd.GetParent().Cast(); FPS.setdefault(fp.GetReference(), (fp, [p for p in fp.Pads()]))
DIAG = [(s1 / math.sqrt(2), s2 / math.sqrt(2)) for s1 in (1, -1) for s2 in (1, -1)]
AXES = ((1, 0), (-1, 0), (0, 1), (0, -1))
hand = []
tried = set()
def straighten():
    m = nodes(); done = 0
    for s in list(S):
        if s.made: continue
        for e in (0, 1):
            E = end_pt(s, e); pd = pad_at(s.layer, E, s.net)
            if not pd or pd.GetShape() == pcbnew.PAD_SHAPE_CIRCLE: continue
            V = far_pt(s, e); d = unit(E, V)
            if max(abs(d[0]), abs(d[1])) > 0.9998: continue
            fp = pd.GetParent().Cast(); ref = f"{fp.GetReference()}.{pd.GetNumber()}"
            key = f"pad {ref} {s.layer} {V[0] / NM - OX:.2f},{V[1] / NM - OY:.2f}"
            if SCALE.get(key, 1) == 0 or key in tried: continue
            tried.add(key)
            lstV = m[(s.layer,) + V]
            if len(lstV) != 2 or blocked(s, V): hand.append(ref + " (bend point is a junction, pad or via)"); continue
            (s2, e2) = [(o, k) for (o, k) in lstV if o is not s][0]
            W = far_pt(s2, e2); h = unit(V, W)
            C = (pd.GetPosition().x, pd.GetPosition().y); bb = pd.GetBoundingBox()
            hw, hh = bb.GetWidth() / 2, bb.GetHeight() / 2
            fc = (fp.GetPosition().x, fp.GetPosition().y); out = unit(fc, C)
            npads = len(FPS[fp.GetReference()][1])
            best = None
            for a in AXES:
                if dot(a, d) <= 0.2: continue
                if dot(a, out) < -0.3: continue                                     # never back under the part
                along_long = (abs(a[0]) and hw >= hh) or (abs(a[1]) and hh >= hw)
                if npads > 2 and max(hw, hh) > 1.4 * min(hw, hh) and not along_long: continue   # IC pin: leave along its length only
                half = hw if a[0] else hh
                L = half + max(0.3 * NM, 0.75 * s.w)
                F = (C[0] + a[0] * L, C[1] + a[1] * L)
                if pad_at(s.layer, ip(*F), s.net): continue                        # stub must end clear of every pad
                for g in DIAG:
                    if dot(g, a) < 0.5 or dot(g, d) < 0.3 or dot(g, h) < 0.5: continue
                    det = g[0] * (-h[1]) - g[1] * (-h[0])
                    if abs(det) < 1e-9: continue
                    rx, ry = V[0] - F[0], V[1] - F[1]
                    k = (rx * (-h[1]) - ry * (-h[0])) / det; tt = (g[0] * ry - g[1] * rx) / det
                    Vn = (V[0] + h[0] * tt, V[1] + h[1] * tt)
                    if k < 0.15 * NM or (W[0] - Vn[0]) * h[0] + (W[1] - Vn[1]) * h[1] < 0.15 * NM: continue
                    score = (3 if dot(a, out) > 0.5 else 1) - abs(tt) / NM * 0.3 - k / NM * 0.05
                    if best is None or score > best[0]: best = (score, ip(*F), ip(*Vn))
            if not best: hand.append(ref + " (no clean straight entry fits)"); continue
            _, F, Vn = best
            set_pt(s, e, (int(C[0]), int(C[1]))); set_pt(s, 1 - e, F); s.made = True; add_like(s, F, Vn).made = True; set_pt(s2, e2, Vn)
            mods.append(dict(kind="straight pad entry", key=key, x=Vn[0] / NM - OX, y=Vn[1] / NM - OY,
                             pts=[[q[0] / NM - OX, q[1] / NM - OY] for q in ((int(C[0]), int(C[1])), F, Vn, W)]))
            log["pad entry straightened"] += 1; done += 1
            return True
    return False
for _ in range(400):
    if not straighten(): break
clean()
for _ in range(2):
    if not miter_pass(): break
    clean()
if hand: open(OUT + ".hand.txt", "w").write("\n".join(sorted(set(hand))) + "\n")

# ---------------- write back: old segment records out, new ones in, then refill the pours
def rec(s):
    return (f'  (segment{" locked" if s.locked else ""} (start {mm_s(s.a[0])} {mm_s(s.a[1])}) (end {mm_s(s.b[0])} {mm_s(s.b[1])}) '
            f'(width {mm_s(s.w)}) (layer "{s.layer}") (net {s.net}) (tstamp {uuid.uuid4()}))\n')
first = SEG_RE.search(txt).start()
body = SEG_RE.sub("", txt)
out = body[:first] + "".join(rec(s) for s in S) + body[first:]
open(OUT, "w").write(out)
b = pcbnew.LoadBoard(OUT)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)
json.dump(mods, open(OUT + ".mods.json", "w"), indent=0)
print("segments", n_in, "->", len(S), dict(log))
