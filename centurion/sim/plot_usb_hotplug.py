"""Plot V(5V_LDO) after a USB hot-plug for each fix, one panel per corner, as a PNG (PIL only, no matplotlib).

Usage: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" plot_usb_hotplug.py [LCAB=1u] [out.png]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
from run_ngspice import run
from sweep_usb_hotplug import CIR, CORNERS, FIXES as ALL_FIXES
FIXES = {k: ALL_FIXES[k] for k in ("none", "C33 as built: 47uF polymer, 70 mohm, at Q1", "47uF, 0.3 ohm", "47uF, 0.05 ohm (C1's EEU-FR1H470, low end)", "22uF polymer, 40 mohm", "snubber 1 ohm + 22uF ceramic (13uF at 5V)")}

L = next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("LCAB=")), "1u")
out = next((a for a in sys.argv[1:] if a.endswith(".png")), os.path.join(os.path.dirname(CIR), "usb_hotplug_%s.png" % L))
PANELS = ["worst", "typical"]
COLORS = [(214, 39, 40), (31, 119, 180), (44, 160, 44), (148, 103, 189), (255, 127, 14), (23, 190, 207)]
T0, T1, V0, V1 = 0.0, 60e-6, 0.0, 8.0
W, H, PAD, LEG = 1500, 520, 60, 400
img = Image.new("RGB", (W, H * len(PANELS)), "white")
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("arial.ttf", 15)
    big = ImageFont.truetype("arialbd.ttf", 17)
except OSError:
    font = big = ImageFont.load_default()
for p, corner in enumerate(PANELS):
    y0 = p * H
    x_l, x_r, y_t, y_b = PAD, W - LEG, y0 + 40, y0 + H - PAD

    def X(t):
        return x_l + (t - T0) / (T1 - T0) * (x_r - x_l)

    def Y(v):
        return y_b - (v - V0) / (V1 - V0) * (y_b - y_t)
    d.text((x_l, y0 + 10), "U7 input (5V_LDO) after plugging in USB, %s cable loop, %s corner" % (L.replace("u", " uH"), corner), fill="black", font=big)
    for v in range(0, 9):
        d.line([(x_l, Y(v)), (x_r, Y(v))], fill=(230, 230, 230))
        d.text((x_l - 30, Y(v) - 8), "%d V" % v, fill="black", font=font)
    for k in range(0, 7):
        t = k * 10e-6
        d.line([(X(t), y_t), (X(t), y_b)], fill=(230, 230, 230))
        d.text((X(t) - 12, y_b + 6), "%d us" % (k * 10), fill="black", font=font)
    d.line([(x_l, Y(6.5)), (x_r, Y(6.5))], fill=(200, 0, 0), width=2)
    d.text((x_r - 170, Y(6.5) - 20), "U7 abs max 6.5 V", fill=(200, 0, 0), font=font)
    d.rectangle([x_l, y_t, x_r, y_b], outline="black")
    for i, (name, fx) in enumerate(FIXES.items()):
        v = run(CIR, LCAB=L, **CORNERS[corner], **fx)
        t, vl = v["time"], v["ldoin"]
        pts = [(X(tt - 1e-6 + T0), Y(vv)) for tt, vv in zip(t, vl) if T0 <= tt - 1e-6 <= T1]
        d.line(pts, fill=COLORS[i % len(COLORS)], width=2)
        ly = y_t + 10 + i * 46
        d.line([(x_r + 15, ly + 8), (x_r + 45, ly + 8)], fill=COLORS[i % len(COLORS)], width=3)
        d.text((x_r + 52, ly), name, fill="black", font=font)
        d.text((x_r + 52, ly + 18), "peak %.2f V" % max(vl), fill=COLORS[i % len(COLORS)], font=font)
img.save(out)
print("saved", out)
