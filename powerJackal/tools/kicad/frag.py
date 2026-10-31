"""List GND pour fragments and which are not tied to the main GND body (via vias / TH pads)."""
import sys, math
import pcbnew
from pcb_common import *
b = pcbnew.LoadBoard(sys.argv[1])
zt = [z for z in b.Zones() if z.GetZoneName() == "GND top"][0]
zb = [z for z in b.Zones() if z.GetZoneName() == "GND bottom"][0]
pt, pb = zt.GetFilledPolysList(pcbnew.F_Cu), zb.GetFilledPolysList(pcbnew.B_Cu)
frags = [("T", i, pt.Outline(i)) for i in range(pt.OutlineCount())] + [("B", i, pb.Outline(i)) for i in range(pb.OutlineCount())]
links = [v.GetPosition() for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
links += [p.GetPosition() for p in b.GetPads() if p.GetNetname() == "GND" and p.GetDrillSize().x > 0]
def inside(f, p): return f[2].PointInside(p)
par = list(range(len(frags)))
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for p in links:
    hit = [k for k, f in enumerate(frags) if inside(f, p)]
    for k in hit[1:]: par[find(k)] = find(hit[0])
groups = {}
for k in range(len(frags)): groups.setdefault(find(k), []).append(k)
main = max(groups.values(), key=lambda g: sum(abs(frags[k][2].Area()) for k in g))
smd = [p for p in b.GetPads() if p.GetNetname() == "GND" and p.GetDrillSize().x == 0]
for g in groups.values():
    if g is main: continue
    for k in g:
        f = frags[k]; bb = f[2].BBox()
        pads = [f"{p.GetParentAsString()}.{p.GetNumber()}" for p in smd if f[0] == "T" and inside(f, p.GetPosition())]
        print(f"isolated {f[0]}{f[1]} area {abs(f[2].Area())/1e12:.2f} mm2 bbox x {pcbnew.ToMM(bb.GetLeft())-OX:.1f}..{pcbnew.ToMM(bb.GetRight())-OX:.1f} y {pcbnew.ToMM(bb.GetTop())-OY:.1f}..{pcbnew.ToMM(bb.GetBottom())-OY:.1f} pads {pads}")
# SMD GND pads not inside any top fragment
for p in smd:
    if not any(inside(f, p.GetPosition()) for f in frags if f[0] == "T"):
        print("GND pad outside top pour:", p.GetParentAsString(), p.GetNumber(), [round(v, 2) for v in toloc(p.GetPosition())])
