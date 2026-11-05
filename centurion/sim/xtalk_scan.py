"""Read-only crosstalk / return-path scan of centurion.kicad_pcb. Writes xtalk_scan.json next to this script."""
import pcbnew, math, json, os, sys, collections

B = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.ToMM
H = {"F.Cu": 0.1, "B.Cu": 0.1}            # trace to its reference plane (stackup), mm
REF = {"F.Cu": "In1.Cu (GND)", "B.Cu": "In2.Cu (+3.3V)"}

def cls(n):
    u = n.upper()
    if n in ("GND",) or u.endswith("VCC") or n in ("+3.3V", "+5V", "SENS_3V3", "SENS_5V") or "VPORT" in u or "VIN_" in u or "5V_LDO" in u or "USB_PWR" in u or "VBUS_USB" in u or "RAMBAR_5V" in u:
        return "power"
    if any(k in u for k in ("AUX1_SIG", "POT_SIG", "POT_IN", "VBAT_SENSE", "VBUS_SENSE", "/FB")): return "analog"
    if "OSC_" in u: return "crystal"
    if any(k in u for k in ("NRST", "BOOT0", "PGOOD", "MUX_RST")): return "control"
    if any(k in u for k in ("USB_D", "USB_DP", "USB_DN")): return "usb"
    if any(k in u for k in ("SWCLK", "SWDIO", "SWO")): return "swd"
    if any(k in u for k in ("SCK", "MOSI", "MISO", "_CS")): return "spi"
    if "CAN" in u: return "can"
    if "RS485" in u and ("_A" in u or "_B" in u) and "/" in n: return "rs485_bus"
    if any(k in u for k in ("SCL", "SDA")): return "i2c"
    return "digital"

# aggressor edge (10-90 %, ns) and swing (V), from the firmware notes and the connector sims
EDGE = {"usb": (4.0, 3.3), "swd": (1.7, 3.3), "spi": (17.0, 3.3), "can": (15.0, 3.3), "i2c": (10.0, 3.3),
        "digital": (4.5, 3.3), "crystal": (20.0, 1.0), "rs485_bus": (12.0, 2.0), "control": (50.0, 3.3), "analog": (1e6, 0.0), "power": (1e6, 0.0)}

segs = []
for t in B.GetTracks():
    if t.GetClass() != "PCB_TRACK": continue
    a, b = t.GetStart(), t.GetEnd()
    segs.append(dict(net=t.GetNetname(), layer=t.GetLayerName(), w=mm(t.GetWidth()), a=(mm(a.x), mm(a.y)), b=(mm(b.x), mm(b.y))))
vias = [dict(net=v.GetNetname(), p=(mm(v.GetPosition().x), mm(v.GetPosition().y))) for v in B.GetTracks() if v.GetClass() == "PCB_VIA"]

def coupling(s1, s2):
    """overlap length and centre spacing for two near-parallel segments on one layer"""
    ax, ay = s1["a"]; bx, by = s1["b"]
    dx, dy = bx - ax, by - ay; L1 = math.hypot(dx, dy)
    cx, cy = s2["a"]; ex, ey = s2["b"]
    fx, fy = ex - cx, ey - cy; L2 = math.hypot(fx, fy)
    if L1 < 0.05 or L2 < 0.05: return None
    ux, uy = dx / L1, dy / L1
    if abs(ux * fy / L2 - uy * fx / L2) > math.sin(math.radians(12)): return None
    t1 = (cx - ax) * ux + (cy - ay) * uy; t2 = (ex - ax) * ux + (ey - ay) * uy
    lo, hi = max(0, min(t1, t2)), min(L1, max(t1, t2))
    if hi - lo < 0.2: return None
    d1 = abs((cx - ax) * uy - (cy - ay) * ux); d2 = abs((ex - ax) * uy - (ey - ay) * ux)
    D = (d1 + d2) / 2
    gap = D - (s1["w"] + s2["w"]) / 2
    return hi - lo, D, gap

pairs = collections.defaultdict(lambda: dict(len=0.0, mingap=9, wD=0.0, layer=set(), at=None))
by_layer = collections.defaultdict(list)
for s in segs: by_layer[s["layer"]].append(s)
for layer, ss in by_layer.items():
    if layer not in H: continue
    for i in range(len(ss)):
        for j in range(i + 1, len(ss)):
            s1, s2 = ss[i], ss[j]
            if s1["net"] == s2["net"]: continue
            c = coupling(s1, s2)
            if not c: continue
            ln, D, gap = c
            if gap > 0.75: continue
            k = tuple(sorted((s1["net"], s2["net"])))
            p = pairs[k]
            p["len"] += ln; p["wD"] += ln * D; p["layer"].add(layer)
            if gap < p["mingap"]: p["mingap"] = gap; p["at"] = s1["a"]
rows = []
for (n1, n2), p in pairs.items():
    c1, c2 = cls(n1), cls(n2)
    if "power" in (c1, c2) and not ({"analog", "crystal"} & {c1, c2}): continue
    D = p["wD"] / p["len"]
    h = H[sorted(p["layer"])[0]] + 0.035
    K = 1 / (1 + (D / h) ** 2)                 # Johnson & Graham coupling estimate
    rows.append(dict(a=n1, b=n2, ca=c1, cb=c2, len=round(p["len"], 2), gap=round(p["mingap"], 3), D=round(D, 3), K=round(K, 4),
                     layer="/".join(sorted(p["layer"])), at=[round(v, 1) for v in p["at"]]))

def risk(r):
    """rough peak noise (V) on each side: K/2 of the aggressor swing, scaled down when the run is shorter than the edge"""
    out = []
    for agg, vic, ca, cv in ((r["a"], r["b"], r["ca"], r["cb"]), (r["b"], r["a"], r["cb"], r["ca"])):
        tr, sw = EDGE[ca]
        if sw == 0: continue
        tlen = r["len"] / 150.0                    # ns, about 6.7 ps/mm on FR-4 microstrip
        sat = min(1.0, 2 * tlen / tr)
        out.append((round(r["K"] / 2 * sw * sat, 4), agg, vic, cv))
    return out
for r in rows:
    rk = risk(r); r["noise"] = max(rk) if rk else None
rows.sort(key=lambda r: -(r["noise"][0] if r["noise"] else 0))

# return paths: signal vias far from any GND via, and signal length on B.Cu (reference is the +3.3 V plane)
gnd_v = [v["p"] for v in vias if v["net"] == "GND"]
gnd_pads = []
for f in B.GetFootprints():
    for pd in f.Pads():
        if pd.GetNetname() == "GND" and pd.HasHole() if hasattr(pd, "HasHole") else False:
            q = pd.GetPosition(); gnd_pads.append((mm(q.x), mm(q.y)))
lay_chg = []
for v in vias:
    c = cls(v["net"])
    if c in ("power",) or v["net"] == "GND": continue
    d = min(math.dist(v["p"], g) for g in gnd_v) if gnd_v else 99
    lay_chg.append(dict(net=v["net"], cls=c, at=[round(x, 2) for x in v["p"]], gnd_via_mm=round(d, 2)))
lay_chg.sort(key=lambda x: -x["gnd_via_mm"])
bcu = collections.defaultdict(float)
for s in segs:
    if s["layer"] == "B.Cu" and cls(s["net"]) not in ("power",) and s["net"] != "GND":
        bcu[s["net"]] += math.dist(s["a"], s["b"])

# plane continuity: sample every signal segment and check the reference plane fill under it
def fills(layer):
    out = []
    for z in B.Zones():
        if z.GetIsRuleArea(): continue
        lid = B.GetLayerID(layer)
        if z.IsOnLayer(lid) and z.IsFilled():
            out.append(z.GetFilledPolysList(lid))
    return out
plane = {"F.Cu": fills("In1.Cu"), "B.Cu": fills("In2.Cu")}
def covered(layer, x, y):
    P = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
    return any(poly.Contains(P) for poly in plane[layer])
gaps = collections.defaultdict(float)
for s in segs:
    if s["layer"] not in H or cls(s["net"]) in ("power",) or s["net"] == "GND": continue
    L = math.dist(s["a"], s["b"]); n = max(1, int(L / 0.25))
    for i in range(n):
        x = s["a"][0] + (s["b"][0] - s["a"][0]) * (i + 0.5) / n; y = s["a"][1] + (s["b"][1] - s["a"][1]) * (i + 0.5) / n
        if not covered(s["layer"], x, y): gaps[(s["net"], s["layer"])] += L / n

# crystal neighbourhood
xtal = []
y1 = B.FindFootprintByReference("Y1"); yp = (mm(y1.GetPosition().x), mm(y1.GetPosition().y))
for s in segs:
    if cls(s["net"]) in ("crystal",) or s["net"] == "GND": continue
    for i in range(11):
        x = s["a"][0] + (s["b"][0] - s["a"][0]) * i / 10; y = s["a"][1] + (s["b"][1] - s["a"][1]) * i / 10
        if math.dist((x, y), yp) < 4.0:
            xtal.append((s["net"], s["layer"], round(math.dist((x, y), yp), 2))); break
osc_len = {n: round(sum(math.dist(s["a"], s["b"]) for s in segs if s["net"] == n), 2) for n in ("/MCU/OSC_IN", "/MCU/OSC_OUT")}

out = dict(pairs=rows, layer_changes=lay_chg, bcu=dict(sorted(bcu.items(), key=lambda x: -x[1])),
           plane_gaps={"%s %s" % k: round(v, 2) for k, v in sorted(gaps.items(), key=lambda x: -x[1])},
           crystal=dict(y1=yp, near=sorted(set(xtal), key=lambda x: x[2]), osc_len=osc_len))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "xtalk_scan.json"), "w"), indent=1, default=list)  
print("pairs within 0.75 mm:", len(rows))
for r in rows[:25]:
    print("  %-26s %-26s %-6s len %6.2f gap %.3f K %.3f noise %s" % (r["a"][:26], r["b"][:26], r["layer"], r["len"], r["gap"], r["K"], r["noise"]))
print("signal vias farthest from a GND via:", lay_chg[:12])
print("B.Cu signal length:", {k: round(v, 1) for k, v in list(out["bcu"].items())[:20]})
print("over a plane gap (mm):", dict(list(out["plane_gaps"].items())[:20]))
print("crystal:", out["crystal"])
