"""Jackal Wiring Map page, generated from kicad/jackal_design.py so every pin, net and small part matches the KiCad design.
usage: python3 make_wiring_map.py <out.html>"""
import sys, os, json, re, html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad"))
import jackal_design as D

PART = {p["ref"]: p for p in D.PARTS}
def net(ref, num):
    n = PART[ref]["pins"][num]
    return n if n else "NC"
def pr(ref, nums, name, note=""):
    nums = [nums] if isinstance(nums, str) else nums
    ns = {net(ref, n) for n in nums}
    assert len(ns) == 1, (ref, nums, ns)
    label = ", ".join(nums) if len(nums) < 5 else f"{nums[0]} … {nums[-1]} ({len(nums)})"
    return {"n": label, "name": name, "net": ns.pop(), "note": note}
def mpn(ref): return PART[ref]["mpn"]

GND_U4 = ["1", "2", "11", "14"] + [str(n) for n in range(36, 54)]
NC_U4 = ["4", "7", "9", "10", "15", "17", "24", "25", "28", "29", "30", "31", "32", "33", "34", "35"]

PARTS = {
    "parts-input": [
        {"ref": "J1", "name": "Smart port jack", "val": f"Molex {mpn('J1')} · 4P4C · footprint is a stand-in, check the Molex drawing", "right": [
            pr("J1", "4", "PWR", "yellow wire · D5, TP1"), pr("J1", "3", "GND", "green wire"),
            pr("J1", "2", "B", "red wire · TP9 only"), pr("J1", "1", "A", "black wire · TP8 only")]},
        {"ref": "D5", "name": "Port OR diode", "val": f"{mpn('D5')} · Schottky 40 V 3 A · SMA", "left": [pr("D5", "2", "A", "J1 PWR")],
         "right": [pr("D5", "1", "K", "joins the bench input")]},
        {"ref": "J2", "name": "Bench input", "val": f"Phoenix {mpn('J2')} · 5.08 mm screw terminal", "right": [
            pr("J2", "1", "+", "D3 anode, 10 to 15 V"), pr("J2", "2", "−", "")]},
        {"ref": "D3", "name": "Bench OR diode", "val": f"{mpn('D3')} · Schottky 40 V 3 A · SMA", "left": [pr("D3", "2", "A", "J2 +")],
         "right": [pr("D3", "1", "K", "joins the port input")]},
        {"ref": "F1", "name": "Polyfuse", "val": f"{mpn('F1')} · 1.5 A hold", "left": [pr("F1", "1", "", "D3, D5, R8")],
         "right": [pr("F1", "2", "", "R1, U2 IN+")]},
        {"ref": "D1", "name": "TVS clamp", "val": f"Littelfuse {mpn('D1')} · SMB · banded end to VIN_MOD", "left": [pr("D1", "1", "K", "banded end")],
         "right": [pr("D1", "2", "A", "")]},
        {"ref": "C1", "name": "Bulk capacitor", "val": f"{mpn('C1')} · 47 µF 50 V", "left": [pr("C1", "1", "+", "next to U1")],
         "right": [pr("C1", "2", "−", "")]},
    ],
    "parts-reg": [
        {"ref": "U1", "name": "TPSM53602 power module", "val": f"TI {mpn('U1')} · B3QFN-14, 5 × 5.5 mm · UWAT library", "ic": True, "left": [
            pr("U1", ["1", "14"], "VIN", "C2, C3, C8 at the pads"),
            pr("U1", "2", "EN", "tied to VIN, always on"),
            pr("U1", ["4"], "DNC", "isolated pad, no copper"),
            pr("U1", ["5"], "DNC", "isolated pad, no copper"),
            pr("U1", "12", "AGND", "into the exposed pad"),
            pr("U1", ["3", "10", "11"], "NC", "into the exposed pad")],
         "right": [
            pr("U1", ["7", "8"], "VOUT", "C4, C5, then R2"),
            pr("U1", "9", "FB", "R3 from 5V_MOD, R4 to GND"),
            pr("U1", "6", "PGOOD", "R7, U4 GPIO3, TP10"),
            pr("U1", "13", "V5V", "internal LDO, leave open"),
            pr("U1", "15", "PGND", "exposed pad, 11 vias")]},
        {"ref": "R3 R4", "name": "Feedback divider", "val": "10 kΩ (R3, RFBT) over 2.49 kΩ (R4, RFBB) · VOUT = 1 V × (1 + 10/2.49) = 5.02 V", "left": [
            pr("R3", "1", "R3 top", "5V_MOD")], "right": [pr("R3", "2", "R3 / R4", "U1 FB"), pr("R4", "2", "R4 bottom", "")]},
    ],
    "parts-sense": [
        {"ref": "U2", "name": "INA226, input side", "val": f"{mpn('U2')} · address 0x40", "ic": True, "left": [
            pr("U2", "10", "IN+", "R1 supply side"), pr("U2", "9", "IN−", "R1 load side"), pr("U2", "8", "VBUS", "port voltage"),
            pr("U2", "1", "A1", ""), pr("U2", "2", "A0", "sets 0x40")],
         "right": [pr("U2", "6", "VS", "C6 0.1 µF to GND"), pr("U2", "4", "SDA", ""), pr("U2", "5", "SCL", ""),
                   pr("U2", "3", "ALERT", "unused"), pr("U2", "7", "GND", "")]},
        {"ref": "U3", "name": "INA226, 5 V side", "val": f"{mpn('U3')} · address 0x41", "ic": True, "left": [
            pr("U3", "10", "IN+", "R2 supply side"), pr("U3", "9", "IN−", "R2 load side"), pr("U3", "8", "VBUS", "rail voltage"),
            pr("U3", "1", "A1", ""), pr("U3", "2", "A0", "sets 0x41")],
         "right": [pr("U3", "6", "VS", "C7 0.1 µF to GND"), pr("U3", "4", "SDA", ""), pr("U3", "5", "SCL", ""),
                   pr("U3", "3", "ALERT", "unused"), pr("U3", "7", "GND", "")]},
        {"ref": "R1", "name": "Input shunt", "val": "20 mΩ 1206 · Kelvin traces from the inner pad edges", "left": [pr("R1", "1", "", "from F1")],
         "right": [pr("R1", "2", "", "to U1")]},
        {"ref": "R2", "name": "5 V shunt", "val": "20 mΩ 1206 · Kelvin traces from the inner pad edges", "left": [pr("R2", "1", "", "from U1")],
         "right": [pr("R2", "2", "", "to the loads")]},
    ],
    "parts-ldo": [
        {"ref": "U6", "name": "3.3 V LDO", "val": f"{mpn('U6')} · SOT-223", "ic": True, "left": [pr("U6", "1", "IN", "C10 10 µF at the pin")],
         "right": [pr("U6", "3", "OUT", "C11 47 µF, then R12"), pr("U6", "2", "GND", "tab in the ground pour")]},
        {"ref": "U5", "name": "INA226, 3.3 V side", "val": f"{mpn('U5')} · address 0x45", "ic": True, "left": [
            pr("U5", "10", "IN+", "R12 supply side"), pr("U5", "9", "IN−", "R12 load side"), pr("U5", "8", "VBUS", "rail voltage"),
            pr("U5", "1", "A1", "with A0, sets 0x45"), pr("U5", "2", "A0", "with A1, sets 0x45")],
         "right": [pr("U5", "6", "VS", "C14 0.1 µF to GND"), pr("U5", "4", "SDA", ""), pr("U5", "5", "SCL", ""),
                   pr("U5", "3", "ALERT", "unused"), pr("U5", "7", "GND", "")]},
        {"ref": "D2", "name": "5 V to LDO diode", "val": f"{mpn('D2')} · SMA", "left": [pr("D2", "2", "A", "rail")],
         "right": [pr("D2", "1", "K", "U6 IN")]},
        {"ref": "Q1", "name": "USB power switch", "val": f"{mpn('Q1')} · P-channel MOSFET · SOT-23", "left": [pr("Q1", "3", "D", "USB_PWR from D4")],
         "right": [pr("Q1", "2", "S", "U6 IN, with D2"), pr("Q1", "1", "G", "5 V rail: rail up = off")]},
        {"ref": "R12", "name": "3.3 V shunt", "val": "50 mΩ 1206", "left": [pr("R12", "1", "", "from U6")],
         "right": [pr("R12", "2", "", "to everything")]},
    ],
    "parts-mcu": [
        {"ref": "U4", "name": "ESP32-C3 module", "val": f"Espressif {mpn('U4')} · 13.2 × 12.5 mm · footprint from Espressif's KiCad library", "ic": True, "left": [
            pr("U4", "3", "3V3", "C12 47 µF, C13 + C15 0.1 µF"),
            pr("U4", "8", "EN", "R17 10 kΩ up, C9 1 µF, SW1"),
            pr("U4", "23", "GPIO9", "R23 10 kΩ up, SW2 BOOT"),
            pr("U4", "22", "GPIO8", "R22 10 kΩ up only"),
            pr("U4", "5", "GPIO2", "R21 10 kΩ up only"),
            pr("U4", "27", "GPIO19 D+", "R24 22 Ω, U7, J7"),
            pr("U4", "26", "GPIO18 D−", "R25 22 Ω, U7, J7"),
            pr("U4", GND_U4, "GND", "pads and centre pad")],
         "right": [
            pr("U4", "18", "GPIO4", "R5 4.7 kΩ to 3V3"),
            pr("U4", "19", "GPIO5", "R6 4.7 kΩ to 3V3"),
            pr("U4", "6", "GPIO3", "R7 10 kΩ to 3V3"),
            pr("U4", "16", "GPIO10", "R20 1 kΩ, LED3"),
            pr("U4", ["12"], "GPIO0", "spare"), pr("U4", ["13"], "GPIO1", "spare"),
            pr("U4", ["20"], "GPIO6", "spare"), pr("U4", ["21"], "GPIO7", "spare"),
            pr("U4", NC_U4, "NC, U0RXD, U0TXD", "not connected")]},
        {"ref": "J7", "name": "USB-C receptacle", "val": f"GCT {mpn('J7')}", "right": [
            pr("J7", ["A4", "A9", "B4", "B9"], "VBUS", "U7 pin 5, D4"), pr("J7", ["A6", "B6"], "D+", "U7, then R24"),
            pr("J7", ["A7", "B7"], "D−", "U7, then R25"), pr("J7", "A5", "CC1", "R14 5.1 kΩ to GND"), pr("J7", "B5", "CC2", "R15 5.1 kΩ to GND"),
            pr("J7", ["A1", "A12", "B1", "B12"], "GND", ""), pr("J7", "S1", "SHIELD", ""), pr("J7", ["A8", "B8"], "SBU", "")]},
        {"ref": "U7", "name": "USB ESD protection", "val": f"{mpn('U7')} · SOT-23-6 · lines pass under the chip", "ic": True, "left": [
            pr("U7", ["1", "6"], "I/O1", "D+"), pr("U7", ["3", "4"], "I/O2", "D−")],
         "right": [pr("U7", "5", "VBUS", ""), pr("U7", "2", "GND", "")]},
        {"ref": "J3", "name": "STEMMA QT to the OLED", "val": f"JST {mpn('J3')}", "right": [
            pr("J3", "1", "GND", "black"), pr("J3", "2", "V+", "red"), pr("J3", "3", "SDA", "blue"), pr("J3", "4", "SCL", "yellow"),
            pr("J3", "MP", "mount", "")]},
    ],
}

# small parts: every two-pin part not drawn above
DRAWN = {"J1", "D5", "J2", "D3", "F1", "D1", "C1", "U1", "U2", "U3", "R1", "R2", "U6", "U5", "D2", "Q1", "R12", "U4", "J7", "U7", "J3"}
WHERE = {"C2": "at U1 VIN", "C3": "at U1 VIN", "C8": "at U1 VIN", "C4": "at U1 VOUT", "C5": "at U1 VOUT", "R3": "RFBT, sets 5.0 V with R4",
         "R4": "RFBB", "C6": "at U2 VS", "C7": "at U3 VS", "C14": "at U5 VS", "C10": "at U6 IN", "C11": "at U6 OUT", "C12": "at U4 pin 3",
         "C13": "at U4 pin 3", "C15": "at U4 pin 3", "R17": "EN pull-up", "C9": "EN delay with R17, per Espressif", "SW1": "RESET",
         "SW2": "BOOT, hold for download mode", "R21": "GPIO2 strap", "R22": "GPIO8 strap, must be high to download", "R23": "GPIO9 pull-up",
         "R24": "USB D+ series, next to U7", "R25": "USB D− series, next to U7", "R14": "USB-C sink resistor", "R15": "USB-C sink resistor",
         "D4": "USB power diode, then Q1", "R5": "I2C pull-up", "R6": "I2C pull-up",
         "R7": "PGOOD pull-up", "R20": "status LED, about 1.3 mA", "LED3": "blinks from firmware", "R8": "input LED", "LED1": "lit = power in",
         "R9": "5 V LED", "LED2": "lit = 5 V rail up", "J6": "5 V out, pin 1 is +", "J9": "3.3 V out, pin 1 is +"}
SMALL = []
for p in D.PARTS:
    r = p["ref"]
    if r in DRAWN or r.startswith("H") or r.startswith("TP") or len(p["pins"]) != 2: continue
    a, b = p["pins"].get("1"), p["pins"].get("2")
    val = p["value"] + (f" · {p['mpn']}" if p["mpn"] else "")
    SMALL.append([r, val, a or "", b or "", WHERE.get(r, "")])
tps = [p for p in D.PARTS if p["ref"].startswith("TP")]
for p in tps:
    SMALL.append([p["ref"], "bare copper pad, 3.4 × 1.8 mm", p["pins"]["1"], "", "test point"])

# net list straight from the design
NETS = {}
for p in D.PARTS:
    for num, n in p["pins"].items():
        if n: NETS.setdefault(n, []).append(f"{p['ref']}.{num}")
def order(n):
    pri = ["VPORT", "BENCH_IN", "VIN_OR", "VFUSE", "VIN_MOD", "5V_MOD", "FB", "5V", "VBUS_USB", "USB_PWR", "5V_LDO", "3V3_LDO", "3V3", "SDA", "SCL",
           "PGOOD", "USB_DP", "USB_DN", "C3_DP", "C3_DN", "CC1", "CC2", "EN", "BOOT", "IO2", "IO8", "LED_STAT"]
    return (pri.index(n) if n in pri else 99, n)
def compress(pins):
    by = {}
    for x in pins:
        ref, num = x.split(".", 1); by.setdefault(ref, []).append(num)
    out = []
    for ref, nums in by.items():
        if len(nums) > 6: out.append(f"{ref} ({len(nums)} pins)")
        else: out.append(f"{ref} {' '.join(nums)}")
    return ", ".join(out)
NETLIST = [[n, compress(NETS[n])] for n in sorted(NETS, key=order) if n != "GND"] + [["GND", compress(NETS["GND"])]]
ncs = [f"{p['ref']}.{num}" for p in D.PARTS for num, n in p["pins"].items() if n is None]
NETLIST.append(["no connect", compress(ncs)])

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiring_template.html")).read()
data = (f"const PARTS = {json.dumps(PARTS, ensure_ascii=False, indent=0)};\n"
        f"const SMALL = {json.dumps(SMALL, ensure_ascii=False)};\n"
        f"const NETS = {json.dumps(NETLIST, ensure_ascii=False)};\n")
out = src.replace("/*__DATA__*/", data)
open(sys.argv[1], "w").write(out)
print("parts drawn", sum(len(v) for v in PARTS.values()), "small", len(SMALL), "nets", len(NETLIST), "bytes", len(out))
