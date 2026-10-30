"""Independent geometric connectivity: which rail each PWR_FLAG lands on."""
import sys, os
sys.argv = ['design.py', '/tmp/claude-0/-home-claude/0eeef73e-c7fb-5128-b9bd-a2ea2b0cc62d/scratchpad/dbg2']
import design
s = design.s
parent = {}
def f(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def u(a, b): parent[f(a)] = f(b)
for a, b in s.wires:
    u(a, b)
    # points lying on wire mid-span
for sym in s.syms:
    for n in sym.pins:
        f(sym.pin(n))
pts = list(parent)
for a, b in s.wires:
    for p in pts:
        if (a[0] == b[0] == p[0] and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])) or \
           (a[1] == b[1] == p[1] and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])):
            u(p, a)
clusters = {}
for sym in s.syms:
    if getattr(sym, 'power', False):
        clusters.setdefault(f(sym.pin('1')), []).append(sym.value)
for k, v in clusters.items():
    if 'PWR_FLAG' in v:
        print('flag cluster:', sorted(set(v)))
