"""Connector simulations for centurion: runs every deck over its cases, checks each result against its limit,
writes connectors_results.json and connectors_results.md, and draws connectors_<group>.png.

Run with KiCad's Python (it has ngspice and PIL):
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" sim_connectors.py [i2c spi uart can rs485 power adc]
With no group names it runs them all (a few minutes).
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_ngspice import run
from PIL import Image, ImageDraw, ImageFont

INF = float("inf")
VDD = 3.3
VIL, VIH = 0.3 * VDD, 0.7 * VDD          # STM32G4 FT inputs (DS13122), and the usual CMOS 30/70 %


# ---------------------------------------------------------------- waveform helpers
def cross(t, v, lvl, rising, t0=0.0, t1=INF):
    for i in range(1, len(t)):
        if t[i] < t0:
            continue
        if t[i - 1] > t1:
            break
        if (rising and v[i - 1] < lvl <= v[i]) or (not rising and v[i - 1] > lvl >= v[i]):
            return t[i - 1] + (lvl - v[i - 1]) * (t[i] - t[i - 1]) / (v[i] - v[i - 1])
    return None


def ncross(t, v, lvl, t0=0.0, t1=INF):
    n = 0
    for i in range(1, len(t)):
        if t0 <= t[i] <= t1 and (v[i - 1] - lvl) * (v[i] - lvl) < 0:
            n += 1
    return n


def ncross_h(t, v, lvl, hys=0.1, t0=0.0, t1=INF):
    """Crossings of lvl with hysteresis: a crossing counts only once v gets hys past lvl (receivers have about 0.1 V)."""
    n, state = 0, None
    for tt, x in zip(t, v):
        if tt < t0 or tt > t1:
            continue
        s = 1 if x > lvl + hys / 2 else (-1 if x < lvl - hys / 2 else state)
        if state is not None and s != state:
            n += 1
        state = s
    return n


def clamp_mA(t, v_anode, v_cathode, t0, t1, IS=1e-14, N=1.05, RS=5.0):
    """Peak current (mA) of a DCLAMP diode from the voltage across it (the 0 V sources' branch currents spike numerically)."""
    vt = 0.02585 * N
    peak = 0.0
    for tt, a_, c_ in zip(t, v_anode, v_cathode):
        vd = a_ - c_
        if tt < t0 or tt > t1 or vd < 0.45:
            continue
        lo, hi = 0.0, vd / RS
        for _ in range(50):                       # vd = vt*ln(I/IS + 1) + I*RS, solved by bisection
            m = (lo + hi) / 2
            if vt * math.log(m / IS + 1) + m * RS > vd:
                hi = m
            else:
                lo = m
        peak = max(peak, lo)
    return peak * 1e3


def win(t, v, t0, t1):
    return [x for tt, x in zip(t, v) if t0 <= tt <= t1] or [float("nan")]


def at(t, v, tx):
    for i in range(1, len(t)):
        if t[i] >= tx:
            f = (tx - t[i - 1]) / ((t[i] - t[i - 1]) or 1)
            return v[i - 1] + f * (v[i] - v[i - 1])
    return v[-1]


def sim(deck, **kw):
    v = run(os.path.join(HERE, deck), **kw)
    if not v.get("time"):
        raise RuntimeError("ngspice gave no data for %s %s" % (deck, kw))
    return v


def r(x, n=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, n)


ROWS, PLOTS = [], {}


def row(group, case, ok, note="", **m):
    """One result. ok = within every limit; note = a non-failing remark (shown as 'ok, note')."""
    d = dict(group=group, case=case, ok=bool(ok), note=note if ok else "", **m)
    ROWS.append(d)
    print("  %-4s %-58s %s %s" % ("ok" if ok else "FAIL", case, ", ".join("%s=%s" % kv for kv in m.items()), ("[" + d["note"] + "]") if d["note"] else ""), flush=True)


# ---------------------------------------------------------------- I2C
def group_i2c():
    print("I2C, mux jacks J6..J13 (i2c_mux.cir) and bus 2 J14 + J18 (i2c_bus2.cir)")
    P = PLOTS.setdefault("i2c", [])
    for vccj in (3.3, 5.0):
        for L in (0.3, 1.0, 2.0):
            for rbo, rn in ((1e9, "no breakout pull-ups"), (10e3, "breakout 10k pull-ups"), (2.2e3, "Qwiic 2.2k pull-ups")):
                a = sim("i2c_mux.cir", VCCJ=vccj, LEN=L, RBO=rbo, DRV=0)
                t = a["time"]
                rs = [cross(t, a["sen"], f * vccj, True, 2.24e-6, 3.5e-6) for f in (0.3, 0.7)]
                rm = [cross(t, a["mcu"], f * VDD, True, 2.24e-6, 3.5e-6) for f in (0.3, 0.7)]
                rise_s = (rs[1] - rs[0]) * 1e9 if None not in rs else INF
                rise_m = (rm[1] - rm[0]) * 1e9 if None not in rm else INF
                hi_m = max(win(t, a["mcu"], 3.0e-6, 3.45e-6))
                und = min(win(t, a["sen"], 1.0e-6, 1.5e-6))
                b = sim("i2c_mux.cir", VCCJ=vccj, LEN=L, RBO=rbo, DRV=1)
                vol_s, vol_m = at(b["time"], b["sen"], 2.0e-6), at(b["time"], b["mcu"], 2.0e-6)
                isink = vol_s / 130 * 1e3
                ok = rise_s <= 300 and rise_m <= 300 and isink <= 3.0 and vol_m <= 0.4 and hi_m <= 3.6
                row("i2c", "mux jack %.1f V, %.1f m, %s" % (vccj, L, rn), ok, "sensor clamp conducts briefly" if und < -0.5 else "", rise_sensor_ns=r(rise_s, 0), rise_mcu_ns=r(rise_m, 0),
                    sink_mA=r(isink), vol_mcu_V=r(vol_m), high_mcu_V=r(hi_m), undershoot_V=r(und))
                if rbo > 1e8 and L == 1.0:
                    P.append(("Mux jack, %.1f V, 1 m cable: rising edge" % vccj, t, {"at the sensor": a["sen"], "at the MCU": a["mcu"]}, 2.2e-6, 2.9e-6, -0.5, 5.5))
    for L in (0.3, 1.0, 2.0):
        for rbo, rn in ((1e9, "no breakout pull-ups"), (10e3, "two breakouts with 10k"), (2.2e3, "two Qwiic boards, 2.2k")):
            a = sim("i2c_bus2.cir", LEN1=L, LEN2=L, RBO=rbo, DRV=0)
            t = a["time"]
            rs = [cross(t, a["s1"], f * VDD, True, 2.24e-6, 3.5e-6) for f in (0.3, 0.7)]
            rise_s = (rs[1] - rs[0]) * 1e9 if None not in rs else INF
            b = sim("i2c_bus2.cir", LEN1=L, LEN2=L, RBO=rbo, DRV=1)
            vol_s, vol_m = at(b["time"], b["s1"], 2.0e-6), at(b["time"], b["mcu"], 2.0e-6)
            isink = vol_s / 130 * 1e3
            ok = rise_s <= 300 and isink <= 3.0 and vol_m <= 0.4
            row("i2c", "bus 2, J14 and J18 both %.1f m, %s" % (L, rn), ok, rise_sensor_ns=r(rise_s, 0), sink_mA=r(isink), vol_mcu_V=r(vol_m))


# ---------------------------------------------------------------- SPI
# R8, R9, R41 are 100 ohm since 2026-11-04; "J5 IMU, old 22 ohm" keeps the earlier value for comparison
OLD22 = "J5 IMU, old 22 ohm R8/R9/R41"
PORTS = {"J5 IMU": dict(RSER=100, LSCK=58, LMOSI=54, LMISO=50), "J15 spare": dict(RSER=0, LSCK=36, LMOSI=73, LMISO=91),
         OLD22: dict(RSER=22, LSCK=58, LMOSI=54, LMISO=50)}
SPEEDS = {"very high (OSPEEDR 11)": 1.7e-9, "high (10)": 2.5e-9, "medium (01)": 4.5e-9, "low (00)": 17e-9}


def group_spi():
    print("SPI, J5 IMU and J15 spare (spi_imu.cir), 10 MHz, BMI270 data out 30 ns after SCK")
    P = PLOTS.setdefault("spi", [])
    F, T0 = 10e6, 20e-9
    for port, pk in PORTS.items():
        for L in (0.1, 0.3, 0.5, 1.0):
            for sp, trm in SPEEDS.items():
                if (port.startswith("J15") or port == OLD22) and sp.startswith("high"):
                    continue
                a = sim("spi_imu.cir", LEN=L, FSCK=F, TRM=trm, TCO=30e-9, **pk)
                t = a["time"]
                w0, w1 = T0 + 1 / F, T0 + 5 / F
                vmax = max(max(win(t, a["sck_imu"], w0, w1)), max(win(t, a["mosi_imu"], w0, w1)))
                vmin = min(min(win(t, a["sck_imu"], w0, w1)), min(win(t, a["mosi_imu"], w0, w1)))
                xing = ncross_h(t, a["sck_imu"], 1.65, 0.1, w0, T0 + 4 / F)    # 3 clocks: 6 clean crossings
                extra = max(ncross_h(t, a["sck_imu"], VIH, 0.1, w0, T0 + 4 / F), ncross_h(t, a["sck_imu"], VIL, 0.1, w0, T0 + 4 / F)) - 6
                z = [0.0] * len(t)
                v3 = [VDD] * len(t)
                iclamp = max(clamp_mA(t, a[n], v3, w0, w1) for n in ("sck_imu", "mosi_imu")) + 0 * len(z)
                iclamp = max(iclamp, max(clamp_mA(t, z, a[n], w0, w1) for n in ("sck_imu", "mosi_imu")))
                tf = cross(t, a["sck_mcu"], 1.65, False, T0 + 2 / F)
                tm = cross(t, a["miso_mcu"], 1.65, True, tf) if tf else None
                tr = cross(t, a["sck_mcu"], 1.65, True, tf) if tf else None
                setup = (tr - tm - 4e-9) * 1e9 if tm and tr else -INF
                fmax = 1 / (2 * ((tm - tf) + 4e-9)) / 1e6 if tm else 0
                b = sim("spi_imu.cir", LEN=L, FSCK=F, TRM=trm, TCO=30e-9, MISOSTATIC=1, **pk)
                xt = max(win(b["time"], b["miso_mcu"], w0, w1))
                # functional limits: no extra SCK edges, MISO setup met, crosstalk below VIL; the IMU's clamps may carry up to 10 mA
                ok = xing == 6 and extra <= 0 and setup >= 0 and xt < VIL and iclamp <= 10
                note = "IMU clamps conduct (%.1f mA)" % iclamp if (vmax > 3.6 or vmin < -0.3) else ""
                row("spi", "%s, %.1f m, %s" % (port, L, sp), ok, note, max_V=r(vmax), min_V=r(vmin), clamp_mA=r(iclamp, 1), sck_threshold_recross=max(extra, xing - 6),
                    miso_setup_ns=r(setup, 1), miso_fmax_MHz=r(fmax, 1), miso_crosstalk_V=r(xt))
                if (port, L, sp[:4]) in ((OLD22, 0.3, "very"), ("J5 IMU", 0.3, "very"), ("J5 IMU", 0.5, "low "),
                                         ("J5 IMU", 1.0, "low ")):
                    P.append(("%s, %.1f m, %s: SCK at the far end" % (port, L, sp), t, {"SCK at the IMU": a["sck_imu"], "MISO at the MCU": a["miso_mcu"]},
                              T0 + 1 / F, T0 + 3 / F, -1.0, 4.5))


# ---------------------------------------------------------------- UART
def settle_and_recross(t, v, t0, t1):
    """Edges in [t0, t1]: crossings of the 30/70 % and 50 % levels, with 0.1 V hysteresis (ringing back across counts)."""
    return ncross_h(t, v, VIH, 0.1, t0, t1), ncross_h(t, v, VIL, 0.1, t0, t1), ncross_h(t, v, 1.65, 0.1, t0, t1)


def group_uart():
    print("UART, J4 Jetson (USART1) and J19 ramBar (UART5), uart_link.cir, alternating bits")
    P = PLOTS.setdefault("uart", [])
    T0 = 50e-9
    for side, nm in ((0, "J4 Jetson"), (1, "J19 ramBar")):
        for baud in ((1e6, 3e6) if side else (1e6,)):
            for L in (0.3, 1.0, 2.0):
                for sp, trm in (("very high (11)", 1.7e-9), ("low (00)", 17e-9)):
                    for cab, ck in (("heavy cable", {}), ("light cable", dict(LPM="0.675u", CPM="30p"))):
                        a = sim("uart_link.cir", SIDE=side, LEN=L, BAUD=baud, TRM=trm, **ck)
                        t = a["time"]
                        w0, w1 = T0 + 1 / baud, T0 + 5 / baud
                        fmax, fmin = max(win(t, a["tx_far"], w0, w1)), min(win(t, a["tx_far"], w0, w1))
                        nih, nil, nmid = settle_and_recross(t, a["tx_far"], w0, T0 + 5 / baud - 1e-12)
                        r10 = cross(t, a["tx_far"], 0.33, True, T0 + 1 / baud)
                        r90 = cross(t, a["tx_far"], 2.97, True, r10) if r10 else None
                        rt = (r90 - r10) * 1e9 if r10 and r90 else INF
                        mmax, mmin = max(win(t, a["rx_mcu"], w0, w1)), min(win(t, a["rx_mcu"], w0, w1))
                        clean = nih == 4 and nil == 4 and nmid == 4
                        # centurion's RX pins are FT: up to VDD + 4 V, and -5 mA of negative injection through the clamp is allowed
                        icl = max(clamp_mA(t, a["tx_far"], a["vfar"], w0, w1), clamp_mA(t, [0.0] * len(t), a["tx_far"], w0, w1))
                        ok = clean and rt <= 0.2e9 / baud and mmax <= VDD + 4 and icl <= 10
                        notes = []
                        if fmax > 3.6 or fmin < -0.3:
                            notes.append("far-end clamps conduct (%.1f mA)" % icl)
                        if mmin < -0.3:
                            notes.append("centurion RX clamp conducts briefly (allowed)")
                        note = "; ".join(notes)
                        row("uart", "%s TX, %.0f Mbaud, %.1f m, GPIO speed %s, %s" % (nm, baud / 1e6, L, sp, cab), ok, note, far_max_V=r(fmax), far_min_V=r(fmin), far_clamp_mA=r(icl, 1),
                            far_rise_10_90_ns=r(rt, 1), recross=(nih - 4) + (nil - 4) + (nmid - 4), rx_mcu_max_V=r(mmax), rx_mcu_min_V=r(mmin))
                        if L == 1.0 and baud == 1e6 and cab == "light cable":
                            P.append(("%s TX, 1 m, light cable, GPIO speed %s" % (nm, sp), t, {"at the far RX": a["tx_far"], "centurion RX pin": a["rx_mcu"]},
                                      T0, T0 + 3 / baud, -1.0, 4.5))
    # back-powering an unpowered far end through its RX clamp diode, TX idling high (DC)
    for nm, rs in (("J4 Jetson (no series R)", 30), ("J19 ramBar (R59 470)", 500)):
        for rl in (1e3, 10e3, 100e3):
            vf, i = 0.55, 0.0
            for _ in range(60):                           # diode about 0.55 V at these currents
                i = (VDD - vf) / (rs + rl)
                vf = 0.026 * 1.05 * math.log(max(i, 1e-12) / 1e-14)
            row("uart", "%s, far end unpowered, its rail loaded by %.0fk, TX idle" % (nm, rl / 1e3), i < 1e-3 and i * rl < 1.0, "",
                injected_mA=r(i * 1e3), far_rail_V=r(i * rl))


# ---------------------------------------------------------------- CAN FD
PATTERN = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1]   # 1 = recessive
SYM = {1e6: (870e-9, 1060e-9), 2e6: (435e-9, 530e-9), 5e6: (155e-9, 210e-9)}   # ISO 11898-2 tBit(Bus); 1 Mbit/s scaled


def bits_check(t, vd, T0, TB, delay, hi_thr, lo_thr, sample=0.75, dominant_is_low=True):
    """Sample each bit at `sample` of the bit after the bus delay; return (errors, worst margin)."""
    errs, margin = 0, INF
    for k, b in enumerate(PATTERN):
        x = at(t, vd, T0 + delay + (k + sample) * TB)
        want_dom = (b == 0) if dominant_is_low else (b == 1)
        m = (x - hi_thr) if want_dom else (lo_thr - x)
        margin = min(margin, m)
        errs += m < 0
    return errs, margin


def group_can():
    print("CAN FD, J19 to ramBar (rambar_can.cir)")
    P = PLOTS.setdefault("can", [])
    T0 = 200e-9
    for rate in (1e6, 2e6, 5e6):
        TB = 1 / rate
        for L in (0.5, 1.0, 2.0):
            for rt, rn in ((120, "ramBar terminated"), (1e9, "ramBar NOT terminated")):
                a = sim("rambar_can.cir", TB=TB, LEN=L, RTRB=rt)
                t = a["time"]
                vd = [h - l for h, l in zip(a["hr"], a["lr"])]
                delay = cross(t, vd, 0.7, True, T0) - T0
                errs, margin = bits_check(t, vd, T0, TB, delay, 0.9, 0.5)
                t_f = cross(t, vd, 0.7, False, T0 + 5 * TB)                     # recessive bit after 5 dominant
                t_r = cross(t, vd, 0.7, True, t_f) if t_f else None
                width = (t_r - t_f) if t_f and t_r else INF
                lo, hi = SYM[rate]
                n_edges = sum(1 for k in range(1, len(PATTERN)) if PATTERN[k] != PATTERN[k - 1]) + 1
                glitches = ncross_h(t, vd, 0.7, 0.4, T0, T0 + 27 * TB) - n_edges     # 0.5 / 0.9 V thresholds
                vod_dom = min(vd[i] for i in range(len(t)) if T0 + delay + 3 * TB < t[i] < T0 + delay + 4.9 * TB)
                ok = errs == 0 and lo <= width <= hi and glitches <= 0
                row("can", "%.0f Mbit/s, %.1f m, %s" % (rate / 1e6, L, rn), ok, sample_errors=errs, sample_margin_V=r(margin),
                    recessive_bit_ns=r(width * 1e9, 0), limits_ns="%d..%d" % (lo * 1e9, hi * 1e9), glitches=max(glitches, 0), vod_dominant_V=r(vod_dom))
                if L == 1.0 and rate == 5e6:
                    P.append(("CAN FD 5 Mbit/s, 1 m, %s: VOD at ramBar" % rn, t, {"VOD at ramBar": vd}, T0, T0 + 26 * TB, -0.5, 3.0))


# ---------------------------------------------------------------- RS-485
def group_rs485():
    print("RS-485, J1/J2 smart port to the V5 brain (rs485_smartport.cir)")
    P = PLOTS.setdefault("rs485", [])
    T0 = 500e-9
    for baud in (921.6e3, 2e6):
        TB = 1 / baud
        for L in (0.3, 1.0, 2.0):
            for (rtc, rtb), tn in (((1e9, 1e9), "no termination"), ((1e9, 120), "120 ohm at the brain only"), ((120, 120), "R51 fitted and 120 at the brain")):
                a = sim("rs485_smartport.cir", BAUD=baud, LEN=L, RTC=rtc, RTB=rtb)
                t = a["time"]
                vd = [x - y for x, y in zip(a["ab"], a["bb"])]
                delay = cross(t, vd, 0.0, False, T0) - T0
                # logic 0 drives A below B; bits_check wants the "dominant" (0) bits above hi_thr, so flip the sign
                vneg = [-x for x in vd]
                errs, margin = bits_check(t, vneg, T0, TB, delay, 0.2, -0.2, sample=0.5)
                n_edges = sum(1 for k in range(1, len(PATTERN)) if PATTERN[k] != PATTERN[k - 1]) + 1
                glitches = ncross_h(t, vd, 0.0, 0.4, T0, T0 + 27 * TB) - n_edges     # -0.2 / +0.2 V thresholds
                swing = max(win(t, vd, T0 + delay + 6.5 * TB, T0 + delay + 10.9 * TB))
                ok = errs == 0 and glitches <= 0
                row("rs485", "%.2f Mbaud, %.1f m, %s" % (baud / 1e6, L, tn), ok, sample_errors=errs, sample_margin_V=r(margin), glitches=max(glitches, 0),
                    vod_low_V=r(-min(win(t, vd, T0 + delay + 1 * TB, T0 + delay + 4.9 * TB))))
                if L == 2.0 and baud == 2e6:
                    P.append(("RS-485 2 Mbaud, 2 m, %s: A-B at the brain" % tn, t, {"A-B at the brain": vd}, T0, T0 + 26 * TB, -3.5, 3.5))


# ---------------------------------------------------------------- power at the jacks
def group_power():
    print("Power at the jacks (jack_power.cir): hot-plug and dead shorts")
    P = PLOTS.setdefault("power", [])
    RAIL = {1: ("SENS_3V3 jack", "RF2", (0.15, 0.70)), 2: ("SENS_5V jack", "RF3", (0.15, 0.70)), 3: ("J19 ramBar 5 V", "RF4", (0.10, 0.40))}
    TP = 20e-6
    for plug, (nm, rf, (rmin, rmax)) in RAIL.items():
        caps = (10e-6, 22e-6) if plug < 3 else (47e-6, 100e-6, 220e-6)
        for c in caps:
            for rv in (rmin, rmax):
                L = 0.5 if plug < 3 else 1.0
                a = sim("jack_power.cir", PLUG=plug, CDEV=c, LEN=L, **{rf: rv})
                t = a["time"]
                m = {k: min(win(t, a[k], TP, 1)) for k in ("p33", "s3", "p5", "s5")}
                ipk = max((x - y) / (0.2 * L + 1e-3) for x, y in zip(a["jc"], a["dev"]))
                dmax = max(win(t, a["dev"], TP, 1))
                ok = m["p33"] >= 3.0 and m["s3"] >= 3.0 and m["p5"] >= 4.5 and m["s5"] >= 4.5
                row("power", "plug %.0f uF into %s, %.1f m, fuse %.2f ohm" % (c * 1e6, nm, L, rv), ok, "", min_3V3=r(m["p33"]), min_SENS_3V3=r(m["s3"]),
                    min_5V=r(m["p5"]), min_SENS_5V=r(m["s5"]), inrush_A=r(ipk, 1), device_peak_V=r(dmax))
                if rv == rmax and ((plug == 1 and c == 10e-6) or (plug == 3 and c == 100e-6)):
                    P.append(("Plug %.0f uF into %s (%.1f m), fuse %.2f ohm" % (c * 1e6, nm, L, rv), t,
                              {"+3.3V": a["p33"], "SENS_3V3": a["s3"], "+5V": a["p5"], "SENS_5V": a["s5"]}, 0, 120e-6, 0, 5.5))
        if plug < 3:
            cv = "C28V" if plug == 1 else "C29V"
            for cb in ("47u", "100u"):
                a = sim("jack_power.cir", PLUG=plug, CDEV=10e-6, LEN=0.5, **{rf: rmax, cv: cb})
                t = a["time"]
                m = {k: min(win(t, a[k], TP, 1)) for k in ("p33", "s3", "p5", "s5")}
                ok = m["p33"] >= 3.0 and m["s3"] >= 3.0 and m["p5"] >= 4.5 and m["s5"] >= 4.5
                row("power", "what if %s were %sF: plug 10 uF into %s, fuse %.2f ohm" % (cv[:3], cb, nm, rmax), ok, "", min_3V3=r(m["p33"]),
                    min_SENS_3V3=r(m["s3"]), min_5V=r(m["p5"]), min_SENS_5V=r(m["s5"]))
        for rv in (rmin, rmax):
            a = sim("jack_power.cir", PLUG=plug, SHORT=1, LEN=0.3, TSTOP="3m", **{rf: rv})
            t = a["time"]
            end = {k: a[k][-1] for k in ("p33", "s3", "p5", "s5")}
            i_sh = a["dev"][-1] / 0.05
            hiccup = end["p5"] < 2.0
            ok = end["p33"] >= 3.0 and end["p5"] >= 4.5
            row("power", "dead short on %s, fuse %.2f ohm" % (nm, rv), ok, "", fault_A=r(i_sh, 2), during_3V3=r(end["p33"]), during_SENS_3V3=r(end["s3"]),
                during_5V=r(end["p5"]), during_SENS_5V=r(end["s5"]), U1_hiccup=hiccup)
            if rv == rmax:
                P.append(("Dead short on %s, fuse %.2f ohm (U1's hiccup not modelled)" % (nm, rv), t, {"+3.3V": a["p33"], "SENS_3V3": a["s3"], "+5V": a["p5"], "SENS_5V": a["s5"]},
                          0, 3e-3, 0, 5.5))


# ---------------------------------------------------------------- ADC inputs
def group_adc():
    print("ADC inputs, AUX1 on PC2 and the turret pot on PC1 (adc_inputs.cir)")
    LSB = VDD / 4096
    for fs in (10e3, 100e3, 500e3):
        for cyc in (2.5, 12.5, 47.5, 247.5):
            ts = cyc / 42.5e6
            if ts > 0.5 / fs:
                continue
            a = sim("adc_inputs.cir", FS=fs, TSMP=ts)
            t = a["time"]
            k = int((t[-1] - 0.5 / fs - 12e-9 - ts) * fs) - 1          # the last whole sample
            te = 0.5 / fs + 12e-9 + ts + k / fs
            rb = 7.5e3 * 1e6 / (7.5e3 + 1e6)
            dc_aux = 4.0 * 15e3 / (25e3 + 1e3)                        # the nodes' DC values with nothing sampling
            dc_pot = 3.3 * rb / (rb + 2.5e3 + 100)
            e_aux = (at(t, a["ca"], te) - dc_aux) / LSB
            e_pot = (at(t, a["cp"], te) - dc_pot) / LSB
            ok = abs(e_aux) <= 2 and abs(e_pot) <= 2
            row("adc", "%.0f kS/s per channel, %.1f ADC cycles (%.0f ns) sampling" % (fs / 1e3, cyc, ts * 1e9), ok, "", aux1_error_LSB=r(e_aux, 1), pot_error_LSB=r(e_pot, 1))
    g = 4095 * (1 - 10e3 / (10e3 + 100))
    row("adc", "pot gain error from R55 (100 ohm) with a 10k pot, at full scale (DC, calibrates out)", True, "", error_counts=r(g, 0), error_pct=r(100 * 100 / 10.1e3, 2))
    worst = max(abs(4096 * (p - (p * 10e3 * 1e6 / (p * 10e3 + 1e6)) / ((p * 10e3 * 1e6 / (p * 10e3 + 1e6)) + (1 - p) * 10e3))) for p in [i / 100 for i in range(1, 100)])
    row("adc", "pot linearity error from R60 (1M pull-down) on a 10k pot, worst position (DC)", True, "", error_counts=r(worst, 1))


# ---------------------------------------------------------------- plots
COLORS = [(214, 39, 40), (31, 119, 180), (44, 160, 44), (148, 103, 189), (255, 127, 14)]


def draw(name, panels):
    if not panels:
        return
    W, H, PAD = 1100, 330, 55
    img = Image.new("RGB", (W, H * len(panels)), "white")
    d = ImageDraw.Draw(img)
    try:
        font, big = ImageFont.truetype("arial.ttf", 14), ImageFont.truetype("arialbd.ttf", 15)
    except OSError:
        font = big = ImageFont.load_default()
    for p, (title, t, series, t0, t1, v0, v1) in enumerate(panels):
        y0 = p * H
        xl, xr, yt, yb = PAD + 10, W - 20, y0 + 32, y0 + H - 35
        X = lambda x: xl + (x - t0) / (t1 - t0) * (xr - xl)
        Y = lambda v: yb - (min(max(v, v0), v1) - v0) / (v1 - v0) * (yb - yt)
        d.text((xl, y0 + 8), title, fill="black", font=big)
        d.rectangle([xl, yt, xr, yb], outline=(120, 120, 120))
        step = 0.5 if v1 - v0 <= 6 else 1.0
        v = math.ceil(v0 / step) * step
        while v <= v1 + 1e-9:
            d.line([xl, Y(v), xr, Y(v)], fill=(225, 225, 225))
            d.text((8, Y(v) - 7), "%.1f V" % v, fill=(90, 90, 90), font=font)
            v += step
        span = t1 - t0
        unit, us = (1e-9, "ns") if span < 2e-6 else (1e-6, "us")
        for k in range(6):
            tx = t0 + k * span / 5
            d.text((X(tx) - 18, yb + 6), "%.0f %s" % ((tx - t0) / unit, us) if span / unit >= 10 else "%.1f %s" % ((tx - t0) / unit, us), fill=(90, 90, 90), font=font)
        for i, (lab, vv) in enumerate(series.items()):
            pts = [(X(tt), Y(x)) for tt, x in zip(t, vv) if t0 <= tt <= t1]
            if len(pts) > 2:
                d.line(pts, fill=COLORS[i % 5], width=2)
            d.text((xr - 220, yt + 8 + 18 * i), "- " + lab, fill=COLORS[i % 5], font=font)
    img.save(os.path.join(HERE, "connectors_%s.png" % name))


GROUPS = dict(i2c=group_i2c, spi=group_spi, uart=group_uart, can=group_can, rs485=group_rs485, power=group_power, adc=group_adc)

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if a in GROUPS] or list(GROUPS)
    for g in want:
        GROUPS[g]()
        draw(g, PLOTS.get(g, []))
    path = os.path.join(HERE, "connectors_results.json")
    old = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    keep = [x for x in old if x["group"] not in want]
    json.dump(keep + ROWS, open(path, "w", encoding="utf-8"), indent=1)
    allrows = keep + ROWS
    with open(os.path.join(HERE, "connectors_results.md"), "w", encoding="utf-8") as f:
        for g in GROUPS:
            rows = [x for x in allrows if x["group"] == g]
            if not rows:
                continue
            keys = [k for k in rows[0] if k not in ("group", "case", "ok", "note")]
            f.write("\n### %s\n\n| Case | Result | %s |\n|---|---|%s\n" % (g, " | ".join(keys), "---|" * len(keys)))
            for x in rows:
                f.write("| %s | %s | %s |\n" % (x["case"], ("ok, " + x["note"] if x.get("note") else "ok") if x["ok"] else "**FAIL**", " | ".join(str(x.get(k)) for k in keys)))
    print("\n%d cases, %d fail. Wrote connectors_results.json, connectors_results.md and the PNGs." % (len(ROWS), sum(not x["ok"] for x in ROWS)))
