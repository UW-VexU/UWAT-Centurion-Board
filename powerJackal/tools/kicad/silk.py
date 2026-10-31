"""Silkscreen: small horizontal reference designators placed clear of pads and other text, plus function labels."""
import sys, math
import pcbnew
from pcb_common import *

SRC, PCB = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(SRC)
H_TXT, TH = 0.8, 0.15

def box_of(item, grow=0.0):
    bb = item.GetBoundingBox()
    x0, y0 = toloc(bb.GetOrigin()); x1, y1 = toloc(bb.GetEnd())
    return (min(x0, x1) - grow, min(y0, y1) - grow, max(x0, x1) + grow, max(y0, y1) + grow)

def hit(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]

pads = [box_of(p, 0.2) for p in b.GetPads()]
holes = [(hx, hy, 4.4) for hx, hy in HOLES]
court = {}
for fp in b.GetFootprints():
    pts = []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd: pts.append(box_of(g))
    if pts: court[fp.GetReference()] = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[2] for p in pts), max(p[3] for p in pts))
taken = []

RELAX = [False]
def free(bx, own=None, allow_court=()):
    if bx[0] < 0.6 or bx[1] < 0.6 or bx[2] > W - 0.6 or bx[3] > H - 0.6: return False
    if any(hit(bx, p) for p in pads): return False
    if any(hit(bx, t) for t in taken): return False
    for hx, hy, r in holes:
        cx, cy = min(max(hx, bx[0]), bx[2]), min(max(hy, bx[1]), bx[3])
        if math.hypot(cx - hx, cy - hy) < r: return False
    for ref, c in court.items():
        if ref == own or ref in allow_court or RELAX[0]: continue
        if hit(bx, (c[0] + 0.15, c[1] + 0.15, c[2] - 0.15, c[3] - 0.15)): return False
    return True

def place_text(t, anchor_box, own=None, prefer=("top", "bottom", "left", "right"), gap=0.25, at=None, rings=(0.4, 0.9, 1.5, 2.2, 3.0)):
    """Try spots around anchor_box; t is a text item (already sized). Returns True if placed."""
    t.SetPosition(V(0, 0)); w, h = (lambda bb: (bb[2] - bb[0], bb[3] - bb[1]))(box_of(t))
    x0, y0, x1, y1 = anchor_box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cands = [at] if at else []
    for side in prefer:
        for s in (0, -1, 1, -2, 2, -3, 3):
            if side == "top": cands.append((cx + s * 0.6, y0 - gap - h / 2))
            if side == "bottom": cands.append((cx + s * 0.6, y1 + gap + h / 2))
            if side == "left": cands.append((x0 - gap - w / 2, cy + s * 0.5))
            if side == "right": cands.append((x1 + gap + w / 2, cy + s * 0.5))
    for d in rings:
        for side in prefer:
            if side == "top": cands.append((cx, y0 - gap - h / 2 - d))
            if side == "bottom": cands.append((cx, y1 + gap + h / 2 + d))
            if side == "left": cands.append((x0 - gap - w / 2 - d, cy))
            if side == "right": cands.append((x1 + gap + w / 2 + d, cy))
    for x, y in cands:
        bx = (x - w / 2 - 0.1, y - h / 2 - 0.1, x + w / 2 + 0.1, y + h / 2 + 0.1)
        if free(bx, own):
            t.SetPosition(V(x, y)); taken.append(bx); return True
    return False

def style(t):
    t.SetTextSize(pcbnew.VECTOR2I(mm(H_TXT), mm(H_TXT))); t.SetTextThickness(mm(TH))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)

def label(text, near_box, prefer=("top", "bottom", "left", "right"), size=H_TXT, bold=False, own=None, at=None):
    t = pcbnew.PCB_TEXT(b); t.SetText(text); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.2 if bold else TH))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    b.Add(t)
    if not place_text(t, near_box, own=own, prefer=prefer, at=at):
        print("could not place label", text); b.Remove(t)

def fixed_text(text, x, y, size, bold=False, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(b); t.SetText(text); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * (0.2 if bold else 0.15)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if layer == pcbnew.B_SilkS: t.SetMirrored(True); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetPosition(V(x, y)); b.Add(t)
    if layer == pcbnew.F_SilkS: taken.append(box_of(t, 0.1))

# board title on the back, read from the bottom side (mirrored, so x runs right to left)
B = pcbnew.B_SilkS
for i, (txt, y, s, bold) in enumerate([("JACKAL", 11.6, 3.0, True), ("smart port power tester  rev A", 15.6, 1.2, False),
                                      ("UWAT VEXU  Centurion family", 17.9, 1.0, False),
                                      ("Check the J1 pinout with a meter first", 21.1, 0.8, False),
                                      ("ESP32-C3: USB-C flashes and prints", 22.7, 0.8, False),
                                      ("Stuck? Hold BOOT, tap RESET", 24.3, 0.8, False),
                                      ("USB powers 3V3 only with port power off", 25.9, 0.8, False),
                                      ("INA226: 0x40 in, 0x41 5V, 0x45 3V3", 27.5, 0.8, False)]):
    fixed_text(txt, 45.1, y, s, bold=bold, layer=B)

# function labels next to the parts that matter to a user holding the board
TP_NAMES = {"TP1": "VPORT", "TP2": "VIN", "TP3": "5V", "TP4": "3V3", "TP5": "GND", "TP6": "GND", "TP8": "A", "TP9": "B", "TP10": "PG"}
LABELS = {"J1": "SMART PORT", "J2": "BENCH 10-15V", "J6": "5V OUT", "J9": "3V3 OUT", "J7": "USB", "J3": "I2C",
          "SW1": "RST", "SW2": "BOOT", "LED1": "IN", "LED2": "5V", "LED3": "STAT"}
AT = {"J1": (8.5, 22.3)}
REF_AT = {"J1": (4.6, 15.6), "J2": (8.6, 28.65)}
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
def pad_box(ref, num, grow=0.0):
    for p in fps[ref].Pads():
        if p.GetNumber() == num: return box_of(p, grow)
# pin hints first (they have the least room), then function labels, then test point names
for ref, num, text in (("J2", "1", "+"), ("J6", "1", "+"), ("J9", "1", "+")):
    label(text, pad_box(ref, num, 0.3), prefer=("right", "left", "top", "bottom"), size=1.2, bold=True, own=ref)
for ref, text in LABELS.items():
    label(text, court[ref], prefer=("top", "bottom", "left", "right") if not ref.startswith("J") else ("bottom", "top", "left", "right"), own=ref, at=AT.get(ref))
for ref, text in TP_NAMES.items():
    fps[ref].Reference().SetVisible(False)
    label(text, court[ref], prefer=("left", "bottom", "top", "right") if ref == "TP8" else ("bottom", "top", "right", "left"))

# reference designators: small, horizontal, clear of pads
for fp in b.GetFootprints():
    r = fp.Reference(); ref = fp.GetReference()
    if ref.startswith("H") or ref in TP_NAMES: r.SetVisible(False); continue
    style(r); r.SetTextAngleDegrees(fp.GetOrientationDegrees()); r.SetKeepUpright(True); r.SetLayer(pcbnew.F_SilkS); r.SetVisible(True)
    if ref in REF_AT:   # big connectors: reference on their own body, so it can't be read as the neighbour's
        r.SetTextAngleDegrees(0); x, y = REF_AT[ref]; r.SetPosition(V(x, y)); taken.append(box_of(r, 0.1)); continue
    if not place_text(r, court.get(ref, box_of(fp)), own=ref):
        RELAX[0] = True   # second try: allow the text over a neighbour's body outline, still never on a pad
        ok = place_text(r, court.get(ref, box_of(fp)), own=ref)
        RELAX[0] = False
        if not ok:   # last try: any free spot on or near the part (2.5 mm around its courtyard), nearest to its centre first
            c = court.get(ref, box_of(fp)); cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
            r.SetPosition(V(0, 0)); bb = box_of(r); w, h = bb[2] - bb[0], bb[3] - bb[1]
            spots = [(c[0] - 2.5 + i * 0.25, c[1] - 2.5 + j * 0.25) for i in range(int((c[2] - c[0] + 5) / 0.25) + 1)
                     for j in range(int((c[3] - c[1] + 5) / 0.25) + 1)]
            spots.sort(key=lambda q: math.hypot(q[0] - cx, q[1] - cy))
            RELAX[0] = True
            for x, y in spots:
                bx = (x - w / 2 - 0.1, y - h / 2 - 0.1, x + w / 2 + 0.1, y + h / 2 + 0.1)
                if free(bx, ref): r.SetPosition(V(x, y)); taken.append(bx); ok = True; break
            RELAX[0] = False
        if not ok:   # crowded spot: try once more with smaller text before giving up
            r.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6))); r.SetTextThickness(mm(0.12))
            c = court.get(ref, box_of(fp)); cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
            r.SetPosition(V(0, 0)); bb = box_of(r); w, h = bb[2] - bb[0], bb[3] - bb[1]
            spots = [(c[0] - 0.5 + i * 0.1, c[1] - 0.5 + j * 0.1) for i in range(int((c[2] - c[0] + 1) / 0.1) + 1)
                     for j in range(int((c[3] - c[1] + 1) / 0.1) + 1)]
            spots.sort(key=lambda q: math.hypot(q[0] - cx, q[1] - cy))
            for x, y in spots:   # only right at the part and never over a neighbour's body, so the label can't be misread
                bx = (x - w / 2 - 0.08, y - h / 2 - 0.08, x + w / 2 + 0.08, y + h / 2 + 0.08)
                if free(bx, ref): r.SetPosition(V(x, y)); taken.append(bx); ok = True; print("small ref", ref, round(x, 2), round(y, 2)); break
        if not ok: r.SetVisible(False); print("hid ref", ref)

b.GetDesignSettings().SetAuxOrigin(V(0, H))   # bottom-left corner: drill and placement origin for the fab
b.GetDesignSettings().SetGridOrigin(V(0, H))
pcbnew.SaveBoard(PCB, b)
from gen_pcb import fix_project
fix_project(PCB)
print("silkscreen done")
