"""Helpers to pull symbols out of KiCad .kicad_sym libraries (text level, flattening 'extends')."""
import re
LIBDIR = "/usr/share/kicad/symbols"

def block_at(text, i):
    """Return the balanced s-expression starting at index i (text[i] == '(')."""
    depth = 0; j = i; instr = False
    while j < len(text):
        c = text[j]
        if instr:
            if c == '\\': j += 2; continue
            if c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: return text[i:j + 1]
        j += 1
    raise ValueError("unbalanced")

def find_symbol(libtext, name):
    m = re.search(r'\n\s*\(symbol "%s"' % re.escape(name), libtext)
    if not m: raise KeyError(name)
    i = libtext.index('(', m.start())
    return block_at(libtext, i)

def prop(block, key):
    m = re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(key), block)
    return m.group(1) if m else None

def flat_symbol(lib, name):
    """Symbol text with 'extends' resolved, named 'lib:name' as schematics expect."""
    text = open(f"{LIBDIR}/{lib}.kicad_sym").read()
    blk = find_symbol(text, name)
    m = re.search(r'\(extends "([^"]+)"\)', blk)
    if m:
        parent = m.group(1)
        pblk = find_symbol(text, parent)
        pm = re.search(r'\(extends "([^"]+)"\)', pblk)
        if pm: pblk = flat_symbol_text(text, pm.group(1), parent, pblk)
        # child's properties replace the parent's
        out = pblk
        for key in ("Reference", "Value", "Footprint", "Datasheet", "ki_keywords", "ki_description", "ki_fp_filters"):
            v = prop(blk, key)
            if v is None: continue
            out = re.sub(r'(\(property "%s" ")((?:[^"\\]|\\.)*)(")' % re.escape(key), lambda mm: mm.group(1) + v.replace('\\', '\\\\') + mm.group(3), out, count=1)
        out = out.replace('(symbol "%s"' % parent, '(symbol "%s"' % name, 1)
        out = re.sub(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(parent), lambda mm: '(symbol "%s_%s_%s"' % (name, mm.group(1), mm.group(2)), out)
        blk = out
    return blk.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, name), 1)

def flat_symbol_text(text, gparent, parent, pblk):
    g = find_symbol(text, gparent)
    out = g.replace('(symbol "%s"' % gparent, '(symbol "%s"' % parent, 1)
    out = re.sub(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(gparent), lambda mm: '(symbol "%s_%s_%s"' % (parent, mm.group(1), mm.group(2)), out)
    return out

PIN_RE = re.compile(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: (\d+))?\)\s*\(length ([\d.]+)\)(\s*hide)?\s*\(name "((?:[^"\\]|\\.)*)"(?:.|\n)*?\(number "((?:[^"\\]|\\.)*)"', re.S)

def pins_of(symtext):
    """number -> (x, y, angle, name, etype) in library coordinates (y up)."""
    out = {}
    for m in PIN_RE.finditer(symtext):
        etype, shape, x, y, ang, length, hid, name, num = m.groups()
        out.setdefault(num, []).append((float(x), float(y), int(ang or 0), name, etype))
    return out
