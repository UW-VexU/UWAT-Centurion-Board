"""Minimal KiCad S-expression reader/writer."""
import re

class Sym(str):
    """Bare atom (unquoted)."""
    pass

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)

def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError(f'parse error at {pos}: {text[pos:pos+40]!r}')
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            lst = stack.pop()
            stack[-1].append(lst)
        elif m.group(3) is not None:
            stack[-1].append(m.group(3).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\'))
        else:
            stack[-1].append(Sym(m.group(4)))
    return stack[0][0] if len(stack[0]) == 1 else stack[0]

def q(s):
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return f'"{s}"'

def fmt(x):
    if isinstance(x, float):
        s = f'{x:.4f}'.rstrip('0').rstrip('.')
        return '0' if s in ('-0', '') else s
    return str(x)

def dump(e, indent=0):
    """Serialize. Lists of atoms stay on one line; nested lists break lines."""
    if isinstance(e, Sym):
        return str(e)
    if isinstance(e, str):
        return q(e)
    if isinstance(e, (int, float)):
        return fmt(e)
    # list
    parts = []
    simple = all(not isinstance(c, list) for c in e)
    if simple or len(e) <= 1:
        return '(' + ' '.join(dump(c) for c in e) + ')'
    head = []
    i = 0
    while i < len(e) and not isinstance(e[i], list):
        head.append(dump(e[i])); i += 1
    out = '(' + ' '.join(head)
    pad = '  ' * (indent + 1)
    small = [c for c in e[i:]]
    # keep short leaf lists inline
    for c in small:
        s = dump(c, indent + 1)
        if isinstance(c, list) and len(s) < 60 and '\n' not in s and all(not isinstance(cc, list) for cc in c):
            out += ' ' + s
        else:
            out += '\n' + pad + s
    out += ')'
    return out

def find(e, key):
    """First child list whose head is key."""
    for c in e:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None

def findall(e, key):
    return [c for c in e if isinstance(c, list) and c and c[0] == key]
