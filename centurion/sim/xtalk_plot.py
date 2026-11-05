"""Plot the worst crosstalk cases from xtalk_sim.py: victim noise in mV (both ends), aggressor edge in grey.
Writes xtalk_worst.png next to this script. Run with KiCad's Python: xtalk_plot.py"""
import os, sys, math
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_ngspice import run
DECK = os.path.join(HERE, "xtalk_pair.cir")
CASES = [  # title, deck params, time window (ns), victim limit note
    ("MUX_RST (idle, 10k) under TOF4_SCL falling: 3.85 mm stacked In2 / B.Cu", dict(LEN=3.85, KL=0.5, KC=0.5, TR=5e-9, DIR=-1, RDRV=60, CLOAD=10e-12, RV1=10e3, CV1=5e-12, CV2=5e-12, VV=3.3), 120, "mux resets below about -2300 mV"),
    ("MUX_RST (idle, 10k) beside RS485A_DE: 16.8 mm side by side on B.Cu", dict(LEN=16.8, KL=0.056, KC=0.039, TR=1.7e-9, DIR=-1, RV1=10e3, CV1=5e-12, CV2=5e-12, VV=3.3), 120, "mux resets below about -2300 mV"),
    ("AUX1_SIG at the ADC beside RS485B_TX: 9.3 mm, C31 at the far end (worst)", dict(LEN=9.3, KL=0.05, KC=0.035, TR=1.7e-9, DIR=1, RV1=6e3, CV1=5e-12, CV2=10e-9, RV2=1e9, VV=1.0), 40, "1 ADC count = 0.8 mV"),
    ("RS485A_RX (driven by the MAX33071E) beside RS485A_TX: 11.3 mm", dict(LEN=11.3, KL=0.068, KC=0.048, TR=1.7e-9, DIR=1, RV1=50, CV1=5e-12, CV2=5e-12, VV=3.3), 40, "logic margin about 1000 mV"),
]
W, H, PAD = 1100, 320, 70
img = Image.new("RGB", (W, H * len(CASES) + 48), "white"); d = ImageDraw.Draw(img)
try:
    font, big = ImageFont.truetype("arial.ttf", 14), ImageFont.truetype("arialbd.ttf", 15)
except OSError:
    font = big = ImageFont.load_default()
COL = {"near end": (31, 119, 180), "far end": (214, 39, 40)}
for p, (title, prm, tw, note) in enumerate(CASES):
    v = run(DECK, **{k: repr(x) for k, x in prm.items()})
    t = [x * 1e9 for x in v["time"]]
    base = prm["VV"]
    near = [(x - base) * 1e3 for x in v["v0"]]; far = [(x - base) * 1e3 for x in v["v10"]]
    agg = v["a0"]
    keep = [i for i, tt in enumerate(t) if tt <= tw]
    lo = min(min(near[i] for i in keep), min(far[i] for i in keep)); hi = max(max(near[i] for i in keep), max(far[i] for i in keep))
    span = max(hi - lo, 5.0); lo -= 0.15 * span; hi += 0.15 * span
    y0 = p * H; xl, xr, yt, yb = PAD + 10, W - 20, y0 + 54, y0 + H - 35
    X = lambda x: xl + x / tw * (xr - xl)
    Y = lambda mv: yb - (mv - lo) / (hi - lo) * (yb - yt)
    d.text((xl, y0 + 8), title, fill="black", font=big)
    d.rectangle([xl, yt, xr, yb], outline=(120, 120, 120))
    raw = (hi - lo) / 6; mag = 10 ** math.floor(math.log10(raw)); step = min((m * mag for m in (1, 2, 5, 10) if m * mag >= raw))
    g = math.ceil(lo / step) * step
    while g <= hi:
        d.line([xl, Y(g), xr, Y(g)], fill=(225, 225, 225) if abs(g) > 1e-9 else (160, 160, 160))
        d.text((8, Y(g) - 7), "%+.0f mV" % g if step >= 1 else "%+.1f mV" % g, fill=(90, 90, 90), font=font); g += step
    for k in range(6):
        tx = k * tw / 5; d.text((X(tx) - 14, yb + 6), "%.0f ns" % tx, fill=(90, 90, 90), font=font)
    amin, amax = min(agg[i] for i in keep), max(agg[i] for i in keep)
    if amax - amin > 1e-6:      # aggressor, scaled into the panel, grey
        pts = [(X(t[i]), yb - (agg[i] - amin) / (amax - amin) * (yb - yt) * 0.9 - 0.05 * (yb - yt)) for i in keep]
        d.line(pts, fill=(185, 185, 185), width=2)
    for lab, s in (("near end", near), ("far end", far)):
        d.line([(X(t[i]), Y(s[i])) for i in keep], fill=COL[lab], width=2)
    pk = min(min(near[i] for i in keep), min(far[i] for i in keep)); pp = max(max(near[i] for i in keep), max(far[i] for i in keep))
    x = xl
    for lab, c in (("victim, near end", COL["near end"]), ("victim, far end", COL["far end"]), ("aggressor edge (scaled)", (150, 150, 150))):
        d.line([x, y0 + 37, x + 22, y0 + 37], fill=c, width=3); d.text((x + 28, y0 + 29), lab, fill=c, font=font); x += 40 + 8 * len(lab)
    d.text((x + 10, y0 + 29), "peak %+.1f / %+.1f mV   (%s)" % (pp, pk, note), fill="black", font=font)
d.text((10, H * len(CASES) + 6), "Lossless coupled-line model (xtalk_pair.cir): the ringing after the first spike lasts longer here than on the real board,", fill=(90, 90, 90), font=font)
d.text((10, H * len(CASES) + 24), "where copper and FR-4 losses damp it. The peaks are the numbers that matter.", fill=(90, 90, 90), font=font)
img.save(os.path.join(HERE, "xtalk_worst.png"))
print("wrote xtalk_worst.png")
