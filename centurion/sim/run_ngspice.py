"""Run a SPICE netlist with the ngspice that ships with KiCad (bin/ngspice.dll), one case at a time.

LTspice-only lines (.step, .meas, .options plotwinsize) are dropped; .param values can be overridden.
Use from Python:   from run_ngspice import run; vecs = run("usb_hotplug.cir", LCAB="1u", FIX=1)
or from a shell:   python run_ngspice.py usb_hotplug.cir LCAB=1u FIX=1   (prints the peak of each node voltage)
Run it with KiCad's Python ("C:\\Program Files\\KiCad\\10.0\\bin\\python.exe") so the DLL and its folder are found.
"""
import ctypes, os, re, sys, tempfile

DLL = os.environ.get("NGSPICE_DLL", r"C:\Program Files\KiCad\10.0\bin\ngspice.dll")


class VecInfo(ctypes.Structure):
    _fields_ = [("v_name", ctypes.c_char_p), ("v_type", ctypes.c_int), ("v_flags", ctypes.c_short),
                ("v_realdata", ctypes.POINTER(ctypes.c_double)), ("v_compdata", ctypes.c_void_p), ("v_length", ctypes.c_int)]


_log = []
_SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
_Exit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
_cb_char = _SendChar(lambda s, i, p: (_log.append(s.decode(errors="replace")), 0)[1])
_cb_stat = _SendStat(lambda s, i, p: 0)
_cb_exit = _Exit(lambda st, unl, quit_, i, p: 0)
_ng = None


def _lib():
    global _ng
    if _ng is None:
        os.add_dll_directory(os.path.dirname(DLL))
        _ng = ctypes.CDLL(DLL)
        _ng.ngGet_Vec_Info.restype = ctypes.POINTER(VecInfo)
        _ng.ngSpice_CurPlot.restype = ctypes.c_char_p
        _ng.ngSpice_AllVecs.restype = ctypes.POINTER(ctypes.c_char_p)
        _ng.ngSpice_Init(_cb_char, _cb_stat, _cb_exit, None, None, None, None)
    return _ng


def netlist(path, **params):
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        low = line.strip().lower()
        if low.startswith((".step", ".meas", ".options plotwinsize")):
            continue
        m = re.match(r"\s*\.param\s+(\w+)\s*=", line, re.I)
        if m and m.group(1) in params:
            line = ".param %s=%s" % (m.group(1), params[m.group(1)])
        out.append(line)
    return "\n".join(out) + "\n"


def run(path, **params):
    """Run one case; returns {vector name: list of floats} for the transient plot."""
    ng = _lib()
    _log.clear()
    fd, tmp = tempfile.mkstemp(suffix=".cir")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(netlist(path, **params))
    try:
        ng.ngSpice_Command(b"destroy all")
        ng.ngSpice_Command(b"remcirc")
        ng.ngSpice_Command(("source " + tmp.replace("\\", "/")).encode())
        ng.ngSpice_Command(b"run")
    finally:
        os.remove(tmp)
    if any("error" in l.lower() and "warning" not in l.lower() for l in _log[-40:]):
        sys.stderr.write("".join(l + "\n" for l in _log[-40:]))
    plot = ng.ngSpice_CurPlot()
    names = ng.ngSpice_AllVecs(plot)
    vecs, i = {}, 0
    while names[i]:
        n = names[i].decode()
        vi = ng.ngGet_Vec_Info(("%s.%s" % (plot.decode(), n)).encode()).contents
        if vi.v_realdata:
            vecs[n.lower()] = [vi.v_realdata[k] for k in range(vi.v_length)]
        i += 1
    return vecs


if __name__ == "__main__":
    cir = sys.argv[1]
    kw = dict(a.split("=", 1) for a in sys.argv[2:])
    v = run(cir, **kw)
    t = v.get("time", [])
    print("points:", len(t))
    for name in sorted(v):
        if name != "time":
            print("  %-22s peak %9.4f   end %9.4f" % (name, max(v[name]), v[name][-1]))
