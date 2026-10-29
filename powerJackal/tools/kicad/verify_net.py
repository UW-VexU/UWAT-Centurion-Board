import re, sys, collections
sys.path.insert(0, '.')
import jackal_design as D
txt = open(sys.argv[1]).read()
nets = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "((?:[^"\\]|\\.)*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', txt, re.S):
    name, body = m.groups()
    nodes = set(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"', body))
    nets[name.lstrip('/')] = nodes
want = collections.defaultdict(set); nc = set()
for p in D.PARTS:
    for pin, net in p["pins"].items():
        if net is None: nc.add((p["ref"], pin))
        else: want[net].add((p["ref"], pin))
bad = 0
got_by_node = {}
for n, nodes in nets.items():
    for nd in nodes: got_by_node[nd] = n
for net, nodes in want.items():
    for nd in nodes:
        g = got_by_node.get(nd)
        if g != net: bad += 1; print("MISMATCH", nd, "want", net, "got", g)
for nd in nc:
    g = got_by_node.get(nd)
    if g and not g.startswith("unconnected"): bad += 1; print("NC pin on a net", nd, g)
extra = [n for n in nets if not n.startswith("unconnected") and n not in want]
print("nets in netlist:", len([n for n in nets if not n.startswith('unconnected')]), "designed:", len(want), "extra:", extra)
print("problems:", bad)
