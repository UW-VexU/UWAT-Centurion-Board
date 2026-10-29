"""Swap test point footprints in place on a routed board (no re-route): every footprint whose design entry uses a
different footprint than the board gets the new one at the same position, rotation, net and reference text.
usage: python3 swap_tp.py board.kicad_pcb"""
import sys
import pcbnew
from pcb_common import *

PCB = sys.argv[1]
b = pcbnew.LoadBoard(PCB)
want = {p["ref"]: p for p in D.PARTS}
nets = {n.GetNetname(): n for n in b.GetNetsByName().values()}
swapped = []
for old in list(b.GetFootprints()):
    ref = old.GetReference(); p = want.get(ref)
    if p is None: continue
    lib, name = p["fp"].split(":")
    if old.GetFPID().GetLibItemName() == name: continue
    new = load_fp(p["fp"])
    new.SetReference(ref); new.SetValue(p["value"]); new.SetPath(old.GetPath())
    new.SetPosition(old.GetPosition()); new.SetOrientation(old.GetOrientation())
    o, n = old.Reference(), new.Reference()
    n.SetPosition(o.GetPosition()); n.SetTextAngle(o.GetTextAngle()); n.SetVisible(o.IsVisible()); n.SetLayer(o.GetLayer())
    n.SetTextSize(o.GetTextSize()); n.SetTextThickness(o.GetTextThickness())
    if not p["in_bom"]: new.SetAttributes(new.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
    for pad in new.Pads():
        net = p["pins"].get(pad.GetNumber())
        if net: pad.SetNet(nets[net_name(net)])
    op = {pd.GetNumber(): (pd.GetPosition(), pd.GetSize()) for pd in old.Pads()}
    for pad in new.Pads():   # copper must match the old land exactly so routing stays valid
        assert op[pad.GetNumber()][0] == pad.GetPosition() and op[pad.GetNumber()][1] == pad.GetSize(), ref
    b.Remove(old); b.Add(new); swapped.append(ref)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save(PCB)
print("swapped", len(swapped), swapped)
