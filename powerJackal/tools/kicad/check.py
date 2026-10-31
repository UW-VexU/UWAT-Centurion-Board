"""Run DRC and summarise. usage: python3 check.py board.kicad_pcb report.txt"""
import sys, re, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pcbnew.WriteDRCReport(b, sys.argv[2], pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(sys.argv[2]).read()
print("\n".join(l for l in txt.splitlines() if l.startswith("**")))
kinds = collections.Counter(re.findall(r"^\[(\w+)\]", txt, re.M))
print(dict(kinds))
