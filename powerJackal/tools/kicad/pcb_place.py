"""Placement for the Jackal board, 72.4 x 47.0 mm. Coordinates are board-local mm (origin top-left, y down),
rotation in degrees (KiCad CCW). The four #8-32 holes sit on the VEX 0.5 in grid, 63.5 x 38.1 mm apart."""
import math

def rot_pt(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a))

def sense_cell(u, r, c, x, y, rot):
    """INA226 at (x, y) plus its shunt and VS bypass cap. Cell local frame (rot 0): INA226 rot 0, shunt rot 270 to the
    right of pins 10/9 with pad 1 (IN+ side) on top, cap below the shunt. rot 90 puts the shunt above the INA226,
    current enters from the left and leaves upward."""
    out = {u: (x, y, rot % 360)}
    sx, sy = rot_pt(5.0, -2.1, rot); out[r] = (x + sx, y + sy, (270 + rot) % 360)
    cx, cy = rot_pt(5.0, 2.8, rot); out[c] = (x + cx, y + cy, rot % 360)
    return out

PLACE = {
    # ---- inputs, left edge
    "J1": (14.3, 13.6, 270),
    "J2": (4.6, 26.1, 270),
    "D5": (21.5, 15.6, 90),
    "D3": (14.0, 26.1, 180),
    "F1": (22.0, 22.6, 270),
    "R8": (15.1, 30.7, 270),
    "LED1": (15.1, 34.3, 90),
    "TP1": (22.5, 10.4, 0),
    "TP8": (12.6, 7.5, 0),
    "TP9": (19.1, 7.5, 0),
    # ---- 5 V regulator (TPSM53602: VIN pads on the left, VOUT pads on the right, FB side up)
    "U1": (39.1, 13.6, 90),
    "C2": (33.1, 11.5, 180),
    "C3": (33.1, 15.7, 180),
    "C8": (36.6, 8.7, 90),
    "C1": (24.6, 5.0, 0),
    "D1": (38.1, 4.0, 0),
    "TP2": (31.6, 2.2, 0),
    "R4": (40.5, 8.0, 90),       # RFBB: FB pad down next to U1 pin 9, GND up
    "R3": (42.7, 8.0, 270),      # RFBT: FB pad down, 5V_MOD pad up
    "C4": (44.9, 11.6, 0),
    "C5": (44.9, 15.6, 0),
    # ---- current sense
    **sense_cell("U2", "R1", "C6", 31.1, 20.5, 180),
    **sense_cell("U3", "R2", "C7", 55.6, 15.6, 90),
    **sense_cell("U5", "R12", "C14", 57.4, 32.1, 90),
    # ---- 5 V outputs
    "J6": (64.35, 16.6, 90),
    "R9": (50.1, 5.0, 0),
    "LED2": (53.6, 5.0, 180),
    "TP3": (59.1, 5.0, 0),
    # ---- 3.3 V regulator
    "U6": (49.1, 27.1, 90),
    "D2": (43.1, 27.1, 90),
    "C10": (46.9, 33.2, 0),
    "C11": (52.875, 33.1, 0),
    "J9": (64.35, 30.1, 90),
    "TP4": (62.4, 37.8, 90),
    # ---- USB
    "J7": (18.1, 43.33, 0),
    "U7": (18.1, 36.1, 270),
    "R14": (12.3, 36.8, 90),
    "R15": (12.3, 33.3, 90),
    "D4": (21.1, 29.7, 180),
    "R24": (21.6, 34.963, 0),    # USB D+ series, inline on the pre-route
    "R25": (21.6, 32.6, 0),      # USB D- series
    "Q1": (39.35, 29.65, 180),   # USB power switch, left of D2
    # ---- MCU: ESP32-C3-MINI-1U turned 180 so USB D-/D+ face the USB-C side
    "U4": (31.1, 40.1, 180),
    "C9": (39.0, 36.85, 90),      # EN delay cap, next to EN
    "R21": (39.0, 41.112, 90),    # GPIO2 strap pull-up
    "C13": (39.0, 44.5, 90),     # 3V3 decoupling at pin 3
    "R17": (41.8, 33.2, 90),     # EN pull-up
    "C15": (41.8, 36.6, 270),
    "C12": (41.8, 40.65, 90),    # 3V3 bulk
    "R22": (26.988, 31.9, 0),      # GPIO8 strap pull-up
    "SW2": (46.0, 39.4, 90),     # BOOT
    "SW1": (52.1, 39.9, 90),     # RESET
    "R23": (48.8, 45.4, 0),      # GPIO9 (BOOT) pull-up, between the buttons
    # ---- I2C, LEDs
    "R5": (31.1, 26.1, 0),
    "R6": (31.1, 28.1, 0),
    "R7": (39.1, 25.1, 90),
    "J3": (59.3, 43.65, 0),
    "R20": (33.612, 32.4, 0),
    "LED3": (37.0, 32.4, 180),
    # ---- test points, holes
    "TP5": (11.6, 3.0, 0),
    "TP6": (59.6, 23.1, 0),
    "TP10": (38.5, 21.6, 0),
    "H1": (4.45, 4.45, 0), "H2": (67.95, 4.45, 0), "H3": (4.45, 42.55, 0), "H4": (67.95, 42.55, 0),
}
