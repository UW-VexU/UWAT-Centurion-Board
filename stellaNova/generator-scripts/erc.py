"""ERC-style checks on a KiCad netlist (kicad-cli sch export netlist)."""
import re, sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, find, findall

def load(path):
    t = parse(open(path).read())
    comps = {}
    for c in findall(find(t, 'components'), 'comp'):
        comps[find(c, 'ref')[1]] = dict(value=find(c, 'value')[1],
                                        fp=(find(c, 'footprint') or [None, ''])[1],
                                        tstamp=(find(c, 'tstamps') or [None, ''])[1])
    nets = {}
    for n in findall(find(t, 'nets'), 'net'):
        name = find(n, 'name')[1]
        nodes = []
        for nd in findall(n, 'node'):
            nodes.append(dict(ref=find(nd, 'ref')[1], pin=find(nd, 'pin')[1],
                              func=(find(nd, 'pinfunction') or [None, ''])[1],
                              type=(find(nd, 'pintype') or [None, ''])[1]))
        nets[name] = nodes
    return comps, nets

def check(netpath, ncpath, flagged=('VIN', '+3V3', 'GND', 'VBUS')):
    comps, nets = load(netpath)
    nc = set(tuple(x) for x in json.load(open(ncpath)))
    errs, warns = [], []
    for name, nodes in nets.items():
        real = [n for n in nodes if not n['ref'].startswith('#')]
        types = [n['type'] for n in nodes]
        if len(nodes) == 1:
            n = nodes[0]
            if (n['ref'], n['pin']) in nc:
                continue
            errs.append(f'unconnected pin {n["ref"]}.{n["pin"]} ({n["func"]}) on {name}')
            continue
        for n in nodes:
            if (n['ref'], n['pin']) in nc:
                errs.append(f'NC-flagged pin {n["ref"]}.{n["pin"]} is connected on {name}')
            if n['type'] == 'no_connect':
                errs.append(f'no_connect pin {n["ref"]}.{n["pin"]} wired on {name}')
        drivers = [n for n in nodes if n['type'] in ('power_out',)]
        if any(t == 'power_in' for t in types) and not drivers and name not in flagged:
            errs.append(f'power input not driven on {name}: ' + ', '.join(f'{n["ref"]}.{n["pin"]}' for n in nodes if n['type'] == 'power_in'))
        outs = [n for n in nodes if n['type'] in ('output', 'power_out')]
        if len(outs) > 1:
            errs.append(f'multiple outputs on {name}: ' + ', '.join(f'{n["ref"]}.{n["pin"]}({n["type"]})' for n in outs))
        if len(real) < 2 and not name.startswith('unconnected'):
            warns.append(f'net {name} has only {len(real)} real part pin(s)')
    return comps, nets, errs, warns

if __name__ == '__main__':
    comps, nets, errs, warns = check(sys.argv[1], sys.argv[2])
    print(f'{len(comps)} components, {len(nets)} nets')
    for e in errs: print('ERROR', e)
    for w in warns: print('warn ', w)
    if '-v' in sys.argv:
        for name, nodes in sorted(nets.items()):
            if name.startswith('unconnected'): continue
            print(f'{name:22s}', ' '.join(f'{n["ref"]}.{n["pin"]}' for n in nodes if not n['ref'].startswith('#')))
    print('ERC-equivalent errors:', len(errs))
