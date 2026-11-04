"""Sweep usb_hotplug.cir in ngspice: cable length x corner x fix. Writes results.json and prints tables.

Run with KiCad's Python:  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" sweep_usb_hotplug.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_ngspice import run

HERE = os.path.dirname(os.path.abspath(__file__))
CIR = os.path.join(HERE, "usb_hotplug.cir")
LS = ["0.3u", "0.5u", "1u", "1.5u", "2u"]
CORNERS = {
    "worst": dict(VHOST=5.5, RHOST="20m", RCAB=0.07, CLAMP=0, LDO=0),
    "worst + U13 clamp": dict(VHOST=5.5, RHOST="20m", RCAB=0.07, CLAMP=1, LDO=0),
    "worst + U7 load": dict(VHOST=5.5, RHOST="20m", RCAB=0.07, CLAMP=0, LDO=1),
    "typical": dict(VHOST=5.25, RHOST="50m", RCAB=0.2, CLAMP=1, LDO=1),
}
FIXES = {
    "none": dict(FIX=0),
    "C33 as built: 47uF polymer, 70 mohm, at Q1": dict(FIX=1, FIXAT=1, CB="47u", RB="70m"),
    "47uF, 0.3 ohm": dict(FIX=1, CB="47u", RB=0.3),
    "47uF, 0.15 ohm": dict(FIX=1, CB="47u", RB=0.15),
    "100uF, 0.5 ohm": dict(FIX=1, CB="100u", RB=0.5),
    "22uF polymer, 40 mohm": dict(FIX=1, CB="22u", RB="40m"),
    "snubber 1 ohm + 22uF ceramic (13uF at 5V)": dict(FIX=2, CB="13u", RB=1.0),
    "47uF, 0.05 ohm (C1's EEU-FR1H470, low end)": dict(FIX=1, CB="47u", RB="0.05"),
    "47uF, 0.7 ohm (small SMD electrolytic)": dict(FIX=1, CB="47u", RB=0.7),
    "47uF, 1.5 ohm (high-ESR SMD electrolytic)": dict(FIX=1, CB="47u", RB=1.5),
    "22uF, 0.5 ohm": dict(FIX=1, CB="22u", RB=0.5),
}


def measure(v):
    t, vl, vb, i = v["time"], v["ldoin"], v["vbus"], v["v_id10#branch"]
    iu13 = v.get("v_iu13#branch", [0] * len(t))
    q100 = sum(0.5 * (i[k] + i[k - 1]) * (t[k] - t[k - 1]) for k in range(1, len(t)) if t[k] <= 101e-6)
    k_pk = max(range(len(t)), key=lambda k: vl[k])
    return {"vldo_pk": max(vl), "t_pk_us": (t[k_pk] - 1e-6) * 1e6, "vbus_pk": max(vb), "iin_pk": max(i),
            "iu13_pk": max(iu13), "q100_uC": q100 * 1e6, "vldo_end": vl[-1]}


if __name__ == "__main__":
    results = {}
    cases = [(c, f) for c in CORNERS for f in FIXES if f == "none" or c in ("worst", "typical")]
    for n, (corner, fix) in enumerate(cases):
        for L in LS:
            r = measure(run(CIR, LCAB=L, **CORNERS[corner], **FIXES[fix]))
            results["%s|%s|%s" % (corner, fix, L)] = r
        print("[%d/%d] %s / %s: peak 5V_LDO %s" % (n + 1, len(cases), corner, fix,
              " ".join("%.2f" % results["%s|%s|%s" % (corner, fix, L)]["vldo_pk"] for L in LS)), flush=True)
    json.dump({"LS": LS, "CORNERS": CORNERS, "FIXES": FIXES, "results": results}, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    print("wrote results.json")
