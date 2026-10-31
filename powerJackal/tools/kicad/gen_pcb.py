"""Build powerJackal.kicad_pcb: outline, holes, footprints placed per pcb_place.PLACE, nets from jackal_design."""
import sys, os, json, math
import pcbnew
from pcb_common import *
from pcb_place import PLACE

OUT = sys.argv[1]   # always a scratch path: never point this at the real board, it would overwrite the routing
UUIDS = json.load(open(os.path.join(HERE, "uuids.json")))

def build():
    b = pcbnew.BOARD()
    b.SetCopperLayerCount(2)
    ds = b.GetDesignSettings()
    ds.m_MinClearance = mm(0.2)
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_ViasMinAnnularWidth = mm(0.1)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_HoleClearance = mm(0.25)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_SolderMaskMinWidth = mm(0.1)
    ds.SetBoardThickness(mm(1.6))
    # net classes
    ns = ds.m_NetSettings
    for name, (tw, cl, vd, vdr, nets) in CLASSES.items():
        nc = ns.m_DefaultNetClass if name == "Default" else pcbnew.NETCLASS(name)
        nc.SetTrackWidth(mm(tw)); nc.SetClearance(mm(cl)); nc.SetViaDiameter(mm(vd)); nc.SetViaDrill(mm(vdr))
        if name != "Default": ns.m_NetClasses[name] = nc
    # nets
    names = sorted({n for p in D.PARTS for n in p["pins"].values() if n})
    NET = {}
    for n in names:
        ni = pcbnew.NETINFO_ITEM(b, net_name(n)); b.Add(ni); NET[n] = ni
    for cname, (tw, cl, vd, vdr, nets) in CLASSES.items():
        for n in nets:
            if n in NET: NET[n].SetNetClass(ns.m_NetClasses[cname])
    # outline with rounded corners
    r = 1.5
    def seg(x0, y0, x1, y1):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1)); b.Add(s)
    def arc(cx, cy, sx, sy, ang):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        s.SetCenter(V(cx, cy)); s.SetStart(V(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T), True); b.Add(s)
    seg(r, 0, W - r, 0); seg(W, r, W, H - r); seg(W - r, H, r, H); seg(0, H - r, 0, r)
    arc(r, r, 0, r, 90); arc(W - r, r, W - r, 0, 90); arc(W - r, H - r, W, H - r, 90); arc(r, H - r, r, H, 90)
    # footprints
    for p in D.PARTS:
        ref = p["ref"]
        if ref not in PLACE: raise SystemExit("no placement for " + ref)
        fp = load_fp(p["fp"])
        fp.SetReference(ref); fp.SetValue(p["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + UUIDS["symbols"][ref]))
        x, y, rot = PLACE[ref]
        fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
        if p["mpn"]: fp.SetProperty("MPN", p["mpn"])
        if p["mfr"]: fp.SetProperty("Manufacturer", p["mfr"])
        if not p["in_bom"]: fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        b.Add(fp)
        for pad in fp.Pads():
            n = p["pins"].get(pad.GetNumber())
            if n: pad.SetNet(NET[n])
    return b, NET

# ---------------- pre-routes (locked)
def track(b, net, pts, w, layer=pcbnew.F_Cu):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1)); t.SetWidth(mm(w))
        t.SetLayer(layer); t.SetNet(net); t.SetLocked(True); b.Add(t)

def via(b, net, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetNet(net); v.SetLocked(True); b.Add(v)

def add_net(b, NET, name):
    ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); NET[name] = ni; return ni

def kelvin_finish(b):
    """After routing: move the Kelvin lines and INA226 sense pins back onto the real nets and land them on the pads."""
    from pcb_place import rot_pt
    part = {p["ref"]: p for p in D.PARTS}
    for u, r, c in SENSE:
        ux, uy, ur = PLACE[u]
        G = lambda lx, ly: (ux + rot_pt(lx, ly, ur)[0], uy + rot_pt(lx, ly, ur)[1])
        pins = part[u]["pins"]
        real = {f"KS_{u}_P": b.FindNet(net_name(pins["10"])), f"KS_{u}_N": b.FindNet(net_name(pins["9"]))}
        for pd in fpads(b, u)["10"] + fpads(b, u)["9"] + fpads(b, u)["8"]:
            pd.SetNet(real[pd.GetNetname()])
        for tr in list(b.GetTracks()):
            if tr.GetNetname() in real: tr.SetNet(real[tr.GetNetname()])
        track(b, real[f"KS_{u}_P"], [G(4.9, -2.55), G(4.9, -3.15)], 0.25)
        track(b, real[f"KS_{u}_N"], [G(4.9, -1.65), G(4.9, -1.05)], 0.25)
        for name in real:
            ni = b.FindNet(name)
            if ni: b.Remove(ni)

def fpads(b, ref):
    fp = b.FindFootprintByReference(ref)
    out = {}
    for pd in fp.Pads(): out.setdefault(pd.GetNumber(), []).append(pd)
    return out

def pad_xy(pd): return toloc(pd.GetPosition())

SENSE = [("U2", "R1", "C6"), ("U3", "R2", "C7"), ("U5", "R12", "C14")]
def prerouted(b, NET):
    from pcb_place import rot_pt
    part = {p["ref"]: p for p in D.PARTS}
    for u, r, c in SENSE:
        ux, uy, ur = PLACE[u]
        G = lambda lx, ly: (ux + rot_pt(lx, ly, ur)[0], uy + rot_pt(lx, ly, ur)[1])
        pins = part[u]["pins"]
        # Kelvin sense lines run in the gap between the shunt pads and enter each pad from its inner edge.
        # While the router runs they sit on private nets and stop short of the pads, so no load current can be
        # routed onto them. kelvin_finish() puts them back on the real nets and adds the last 0.6 mm into each pad.
        n_in, n_out = add_net(b, NET, f"KS_{u}_P"), add_net(b, NET, f"KS_{u}_N")
        for pd in fpads(b, u)["10"]: pd.SetNet(n_in)
        for num in ("9", "8"):
            for pd in fpads(b, u)[num]: pd.SetNet(n_out)
        track(b, n_in, [G(2.2, -1.0), G(3.25, -1.0), G(3.25, -2.55), G(4.9, -2.55)], 0.25)    # IN+
        track(b, n_out, [G(2.2, -0.5), G(3.75, -0.5), G(3.75, -1.65), G(4.9, -1.65)], 0.25)   # IN-
        track(b, n_out, [G(2.2, 0.0), G(2.2, -0.5)], 0.25)                                     # VBUS tied to IN- at the pins
        g = NET["GND"]
        track(b, g, [G(2.2, 0.5), G(3.6, 0.5)], 0.25); via(b, g, *G(3.6, 0.5))                    # pin 7 GND straight to a via
        track(b, g, [G(5.91, 2.8), G(5.91, 4.1)], 0.4); via(b, g, *G(5.91, 4.1))                  # bypass cap GND
        track(b, NET["3V3"], [G(2.2, 1.0), G(2.95, 1.0), G(3.75, 1.8), G(4.09, 1.8), G(4.09, 2.8)], 0.3)   # VS to its bypass cap
        v3 = NET["3V3"]
        track(b, v3, [G(4.09, 2.8), G(4.09, 4.4)], 0.3); via(b, v3, *G(4.09, 4.4))                # escape via for the bypass cap 3V3 side
        a1, a0 = pins["1"], pins["2"]
        # an address pin tied to VS: escape via, then a bottom-side run to the bypass cap's 3V3 via
        if a1 == "3V3":
            track(b, v3, [G(-2.2, -1.0), G(-3.2, -1.0), G(-3.6, -1.6)], 0.3); via(b, v3, *G(-3.6, -1.6))
            track(b, v3, [G(-3.6, -1.6), G(-4.3, -0.9), G(-4.3, 4.4), G(4.09, 4.4)], 0.3, pcbnew.B_Cu)
        if a0 == "3V3":
            track(b, v3, [G(-2.2, -0.5), G(-3.4, -0.5), G(-3.8, 0.1)], 0.3); via(b, v3, *G(-3.8, 0.1))
            track(b, v3, [G(-3.8, 0.1), G(-4.3, 0.6), G(-4.3, 4.4), G(4.09, 4.4)], 0.3, pcbnew.B_Cu)
        if a1 == "GND" and a0 == "GND":
            track(b, g, [G(-2.2, -0.5), G(-2.2, -1.0), G(-3.0, -2.0)], 0.25); via(b, g, *G(-3.0, -2.0))
        elif a1 == "GND":
            track(b, g, [G(-2.2, -1.0), G(-3.0, -2.0)], 0.25); via(b, g, *G(-3.0, -2.0))
        elif a0 == "GND":
            track(b, g, [G(-2.2, -0.5), G(-3.3, -0.5), G(-3.6, 0.1)], 0.25); via(b, g, *G(-3.6, 0.1))
    # U2's VS cap sits behind the input power path: give its 3V3 side a bottom-side link to R5 (I2C pull-up, 3V3)
    ux, uy, ur = PLACE["U2"]
    cv = (ux + rot_pt(4.09, 4.4, ur)[0], uy + rot_pt(4.09, 4.4, ur)[1])
    r5x, r5y, _ = PLACE["R5"]
    v3 = NET["3V3"]
    track(b, v3, [cv, (cv[0] + 1.29, cv[1] + 1.1), (r5x - 2.8, r5y - 2.4), (r5x - 1.8, r5y - 1.4), (r5x - 0.91, r5y - 1.4)], 0.3, pcbnew.B_Cu)
    via(b, v3, r5x - 0.91, r5y - 1.4); track(b, v3, [(r5x - 0.91, r5y - 1.4), (r5x - 0.91, r5y)], 0.3)
    # USB-C fan-out: DN pads joined behind the pad row, DP pads in front, both straight up into the USBLC6
    jx, jy, _ = PLACE["J7"]; py = jy - 3.68
    ux7, uy7, _ = PLACE["U7"]; ytop = uy7 + 1.3      # just inside the USBLC6 bottom pads (pins 4 and 6)
    dn, dp = NET["USB_DN"], NET["USB_DP"]
    track(b, dn, [(jx - 0.75, py), (jx - 0.75, ytop)], 0.25)
    track(b, dn, [(jx + 0.25, py), (jx + 0.25, py + 1.05), (jx - 0.75, py + 1.05), (jx - 0.75, py)], 0.25)
    track(b, dp, [(jx + 0.75, py), (jx + 0.75, py - 1.05)], 0.25)
    track(b, dp, [(jx + 0.75, py - 1.05), (jx + 0.75, ytop)], 0.25)
    track(b, dp, [(jx - 0.25, py), (jx - 0.25, py - 1.05), (jx + 0.75, py - 1.05)], 0.25)
    # USBLC6 VBUS (pin 5) escapes through a via just below it, between the two USB lines; GND (pin 2) through a via above
    track(b, NET["VBUS_USB"], [(ux7, uy7 + 1.137), (ux7, uy7 + 1.8)], 0.4); via(b, NET["VBUS_USB"], ux7, uy7 + 1.8)
    track(b, NET["GND"], [(ux7, uy7 - 1.137), (ux7, uy7 - 2.15)], 0.4); via(b, NET["GND"], ux7, uy7 - 2.15)
    # USBLC6 to the ESP32-C3 module (USB pins on its left edge): D- loops over the top, D+ runs straight across
    U7, U4 = fpads(b, "U7"), fpads(b, "U4")
    u7dp, u7dn = pad_xy(U7["1"][0]), pad_xy(U7["3"][0])
    mdn, mdp = pad_xy(U4["26"][0]), pad_xy(U4["27"][0])
    R24, R25 = fpads(b, "R24"), fpads(b, "R25")
    r24a, r24b, r25a, r25b = pad_xy(R24["1"][0]), pad_xy(R24["2"][0]), pad_xy(R25["1"][0]), pad_xy(R25["2"][0])
    cdp, cdn = NET["C3_DP"], NET["C3_DN"]
    track(b, dp, [u7dp, r24a], 0.25)                                                         # D+: USBLC6 pin 1 into R24
    track(b, cdp, [r24b, (mdp[0] - 1.7, r24b[1]), (mdp[0] - 1.7, mdp[1]), mdp], 0.25)        # R24 to GPIO19
    track(b, dn, [u7dn, (u7dn[0], r25a[1]), r25a], 0.25)                                       # D-: USBLC6 pin 3 up and into R25
    track(b, cdn, [r25b, (mdn[0] - 1.0, r25b[1]), (mdn[0] - 1.0, mdn[1]), mdn], 0.25)         # R25 to GPIO18
    # the USBLC6 passes each line under the chip (pin 1 to 6, pin 3 to 4): draw those links so the pair is fixed copper end to end
    track(b, dp, [pad_xy(U7["1"][0]), pad_xy(U7["6"][0])], 0.25)
    track(b, dn, [pad_xy(U7["3"][0]), pad_xy(U7["4"][0])], 0.25)
    # TPSM53602 local ties: EN straight to the VIN pad beside it; the NC pins (3, 10, 11) and AGND (12) drop into the
    # exposed GND pad, which makes AGND meet PGND at one point right at the module
    P = fpads(b, "U1")
    en, v1 = pad_xy(P["2"][0]), pad_xy(P["1"][0])
    track(b, NET["VIN_MOD"], [en, (v1[0], en[1])], 0.25)
    ep = pad_xy([q for q in P["15"] if q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD][0])
    for num in ("3", "10", "11", "12"):
        x, y = pad_xy(P[num][0])
        track(b, NET["GND"], [(x, y), (x, ep[1] + (1.1 if y > ep[1] else -1.1))], 0.3)

def fix_project(pcb_path):
    """Net class patterns and library tables, which the KiCad 7 Python API cannot set directly."""
    d = os.path.dirname(pcb_path); pro = pcb_path[:-len(".kicad_pcb")] + ".kicad_pro"
    j = json.load(open(pro))
    j["net_settings"]["netclass_patterns"] = [{"netclass": c, "pattern": net_name(n)} for c, v in CLASSES.items() if c != "Default" for n in v[4]]
    j["meta"]["filename"] = os.path.basename(pro)
    json.dump(j, open(pro, "w"), indent=2)
    open(os.path.join(d, "fp-lib-table"), "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "UWAT")(type "KiCad")(uri "${KIPRJMOD}/../lib/UWAT.pretty")(options "")(descr "UWAT VEXU parts"))\n)\n')
    open(os.path.join(d, "sym-lib-table"), "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "UWAT")(type "KiCad")(uri "${KIPRJMOD}/../lib/UWAT.kicad_sym")(options "")(descr "UWAT VEXU parts"))\n)\n')

if __name__ == "__main__":
    b, NET = build()
    prerouted(b, NET)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pcbnew.SaveBoard(OUT, b)
    fix_project(OUT)
    print("board saved", OUT, "footprints:", len(b.GetFootprints()))
