import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_ngspice import run
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xtalk_pair.cir")
def pk(v, base, t, t0=1e-9):
    w = [x - base for tt, x in zip(t, v) if tt > t0]
    return max(w), min(w)
cases = [
 # name, params, victim bias, what matters
 ("MUX_RST <- RS485A_DE, 16.8 mm side by side, mux reset idle on R10 10k (MCU pin not driving)",
  dict(LEN=16.8, KL=0.056, KC=0.039, TR=1.7e-9, DIR=-1, RV1=10e3, CV1=5e-12, CV2=5e-12, VV=3.3)),
 ("MUX_RST <- RS485A_DE, same, MCU pin driving it high",
  dict(LEN=16.8, KL=0.056, KC=0.039, TR=1.7e-9, DIR=-1, RV1=30, CV1=5e-12, CV2=5e-12, VV=3.3)),
 ("MUX_RST <- TOF4_SCL falling, 3.85 mm stacked In2/B.Cu (strong), 10k idle",
  dict(LEN=3.85, KL=0.5, KC=0.5, TR=5e-9, DIR=-1, RDRV=60, CLOAD=10e-12, RV1=10e3, CV1=5e-12, CV2=5e-12, VV=3.3)),
 ("AUX1_SIG (ADC) <- RS485B_TX, 9.3 mm, C31 10 nF at the near end, ADC pin far end",
  dict(LEN=9.3, KL=0.05, KC=0.035, TR=1.7e-9, DIR=1, RV1=6e3, CV1=10e-9, CV2=5e-12, VV=1.0)),
 ("AUX1_SIG (ADC) <- RS485B_TX, same, worst: C31 at the far end, ADC pin near end",
  dict(LEN=9.3, KL=0.05, KC=0.035, TR=1.7e-9, DIR=1, RV1=6e3, CV1=5e-12, CV2=10e-9, RV2=1e9, VV=1.0)),
 ("AUX1_SIG_IN (before R34) <- I2C_AUX_SCL falling, 16 mm, cable side open, R34 10k into C31",
  dict(LEN=16.0, KL=0.046, KC=0.032, TR=5e-9, DIR=-1, RDRV=60, RV1=10e3, CV1=15e-12, CV2=10e-12, VV=1.0)),
 ("RS485A_RX <- RS485A_TX, 11.3 mm, RX driven by the MAX33071E (about 50 ohm)",
  dict(LEN=11.3, KL=0.068, KC=0.048, TR=1.7e-9, DIR=1, RV1=50, CV1=5e-12, CV2=5e-12, VV=3.3)),
 ("IMU_INT2 <- SWDIO, 3.6 mm (SWD only while debugging), INT2 driven by the IMU",
  dict(LEN=3.6, KL=0.067, KC=0.047, TR=1.7e-9, DIR=1, RV1=100, CV1=5e-12, CV2=5e-12, VV=3.3)),
]
for name, p in cases:
    v = run(D, **{k: (repr(x)) for k, x in p.items()})
    t = v["time"]; base = p.get("VV", 3.3)
    hi0, lo0 = pk(v["v0"], base, t); hi1, lo1 = pk(v["v10"], base, t)
    print("%-95s near %+7.1f/%+7.1f mV  far %+7.1f/%+7.1f mV" % (name, hi0 * 1e3, lo0 * 1e3, hi1 * 1e3, lo1 * 1e3))
