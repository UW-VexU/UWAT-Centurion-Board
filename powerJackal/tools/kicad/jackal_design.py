"""Jackal (Centurion family) smart port power test board, Rev A.
Single source of truth for the schematic and the PCB: parts, values, footprints, part numbers and pin-to-net maps.
Nets named here are the label names on the schematic and the net names on the board."""

NC = None  # pin left unconnected (gets a no-connect flag)

# blocks: schematic sections, drawn left to right, top to bottom
BLOCKS = [
    ("in",   "1  POWER INPUT",              (10.16, 15.24),  (125.73, 83.82)),
    ("v5",   "2  5 V REGULATOR",            (139.7, 15.24),  (160.02, 83.82)),
    ("mcu",  "6  ESP32-C3 MCU",             (304.8, 15.24),  (104.14, 154.94)),
    ("sense","3  CURRENT SENSE",            (10.16, 102.87), (175.26, 104.14)),
    ("v33",  "4  3.3 V REGULATOR",          (189.23, 102.87),(110.49, 60.96)),
    ("io",   "7  I2C, LEDS, OUTPUTS",       (304.8, 173.99), (104.14, 77.47)),
    ("usb",  "5  USB-C",                    (10.16, 210.82), (175.26, 73.66)),
    ("tp",   "8  TEST POINTS, MECHANICAL",  (189.23, 167.64),(105.41, 116.84)),
]

def P(ref, lib, value, fp, pins, block, mpn="", mfr="", dnp=False, in_bom=True, rot=0, note=""):
    return dict(ref=ref, lib=lib, value=value, fp=fp, pins=pins, block=block, mpn=mpn, mfr=mfr, dnp=dnp, in_bom=in_bom, rot=rot, note=note)

R0805 = "Resistor_SMD:R_0805_2012Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
TPFP = "UWAT:TestPad_3.4x1.8mm"   # bare copper pad, nothing to buy

PARTS = [
    # ---------------- 1 power input
    P("J1", "Connector:4P4C", "Smart port 4P4C", "UWAT:Molex_95501-2441_4P4C_Horizontal",
      {"1": "RS485_A", "2": "RS485_B", "3": "GND", "4": "VPORT"}, "in", "0955012441", "Molex",
      note="Pin map assumes the usual black, red, green, yellow order. Check with a meter."),
    P("D5", "Device:D_Schottky", "B340A", "Diode_SMD:D_SMA", {"1": "VIN_OR", "2": "VPORT"}, "in", "B340A-13-F", "Diodes Incorporated", rot=180),
    P("J2", "Connector:Screw_Terminal_01x02", "Bench 10-15V", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
      {"1": "BENCH_IN", "2": "GND"}, "in", "1935161", "Phoenix Contact"),
    P("D3", "Device:D_Schottky", "B340A", "Diode_SMD:D_SMA", {"1": "VIN_OR", "2": "BENCH_IN"}, "in", "B340A-13-F", "Diodes Incorporated", rot=180),
    P("F1", "Device:Polyfuse", "1.5A hold", "UWAT:Fuse_Littelfuse_2016L", {"1": "VIN_OR", "2": "VFUSE"}, "in", "2016L150/33DR", "Littelfuse"),
    P("R8", "Device:R", "10k", R0805, {"1": "VIN_OR", "2": "LED1_A"}, "in", "RC0805FR-0710KL", "Yageo"),
    P("LED1", "Device:LED", "Green", "LED_SMD:LED_0805_2012Metric", {"1": "GND", "2": "LED1_A"}, "in", "LTST-C171GKT", "Lite-On"),

    # ---------------- 2 5 V regulator
    P("D1", "Device:D_Zener", "SMBJ16A", "Diode_SMD:D_SMB", {"1": "VIN_MOD", "2": "GND"}, "v5", "SMBJ16A", "Littelfuse"),
    P("C1", "Device:C_Polarized", "47u 50V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", {"1": "VIN_MOD", "2": "GND"}, "v5", "EEU-FC1H470", "Panasonic"),
    P("C2", "Device:C", "10u 50V", C1210, {"1": "VIN_MOD", "2": "GND"}, "v5", "CL32B106KBJNNNE", "Samsung Electro-Mechanics"),
    P("C3", "Device:C", "10u 50V", C1210, {"1": "VIN_MOD", "2": "GND"}, "v5", "CL32B106KBJNNNE", "Samsung Electro-Mechanics"),
    P("C8", "Device:C", "100n", C0805, {"1": "VIN_MOD", "2": "GND"}, "v5", "CC0805KRX7R9BB104", "Yageo"),
    P("R9", "Device:R", "2.2k", R0805, {"1": "5V", "2": "LED2_A"}, "v5", "RC0805FR-072K2L", "Yageo"),
    P("LED2", "Device:LED", "Green", "LED_SMD:LED_0805_2012Metric", {"1": "GND", "2": "LED2_A"}, "v5", "LTST-C171GKT", "Lite-On"),
    P("U1", "UWAT:TPSM53602", "TPSM53602", "UWAT:Texas_B3QFN-14-1EP_5x5.5mm_P0.65mm_ThermalVia",
      {"1": "VIN_MOD", "14": "VIN_MOD", "2": "VIN_MOD", "3": "GND", "10": "GND", "11": "GND", "15": "GND", "12": "GND",
       "4": NC, "5": NC, "6": "PGOOD", "7": "5V_MOD", "8": "5V_MOD", "9": "FB", "13": NC},
      "v5", "TPSM53602RDAR", "Texas Instruments", note="EN tied to VIN. DNC pins 4, 5 and V5V (13) stay unconnected."),
    P("R3", "Device:R", "10k", R0805, {"1": "5V_MOD", "2": "FB"}, "v5", "RC0805FR-0710KL", "Yageo", note="RFBT"),
    P("R4", "Device:R", "2.49k", R0805, {"1": "FB", "2": "GND"}, "v5", "RC0805FR-072K49L", "Yageo", note="RFBB, sets 5.0 V"),
    P("C4", "Device:C", "47u 10V", C1206, {"1": "5V_MOD", "2": "GND"}, "v5", "GRM31CR61A476ME15L", "Murata"),
    P("C5", "Device:C", "47u 10V", C1206, {"1": "5V_MOD", "2": "GND"}, "v5", "GRM31CR61A476ME15L", "Murata"),

    # ---------------- 3 current sense
    P("R1", "Device:R", "20m 1%", R1206, {"1": "VFUSE", "2": "VIN_MOD"}, "sense", "WSL1206R0200FEA", "Vishay Dale"),
    P("U2", "Sensor_Energy:INA226", "INA226 0x40", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
      {"10": "VFUSE", "9": "VIN_MOD", "8": "VIN_MOD", "6": "3V3", "7": "GND", "1": "GND", "2": "GND", "4": "SDA", "5": "SCL", "3": NC},
      "sense", "INA226AIDGSR", "Texas Instruments"),
    P("C6", "Device:C", "100n", C0805, {"1": "3V3", "2": "GND"}, "sense", "CC0805KRX7R9BB104", "Yageo"),
    P("R2", "Device:R", "20m 1%", R1206, {"1": "5V_MOD", "2": "5V"}, "sense", "WSL1206R0200FEA", "Vishay Dale"),
    P("U3", "Sensor_Energy:INA226", "INA226 0x41", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
      {"10": "5V_MOD", "9": "5V", "8": "5V", "6": "3V3", "7": "GND", "1": "GND", "2": "3V3", "4": "SDA", "5": "SCL", "3": NC},
      "sense", "INA226AIDGSR", "Texas Instruments"),
    P("C7", "Device:C", "100n", C0805, {"1": "3V3", "2": "GND"}, "sense", "CC0805KRX7R9BB104", "Yageo"),
    P("R12", "Device:R", "50m 1%", R1206, {"1": "3V3_LDO", "2": "3V3"}, "sense", "WSL1206R0500FEA", "Vishay Dale"),
    P("U5", "Sensor_Energy:INA226", "INA226 0x45", "Package_SO:VSSOP-10_3x3mm_P0.5mm",
      {"10": "3V3_LDO", "9": "3V3", "8": "3V3", "6": "3V3", "7": "GND", "1": "3V3", "2": "3V3", "4": "SDA", "5": "SCL", "3": NC},
      "sense", "INA226AIDGSR", "Texas Instruments"),
    P("C14", "Device:C", "100n", C0805, {"1": "3V3", "2": "GND"}, "sense", "CC0805KRX7R9BB104", "Yageo"),

    # ---------------- 4 3.3 V regulator
    P("D2", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "5V_LDO", "2": "5V"}, "v33", "SS14-E3/61T", "Vishay", rot=180),
    P("C10", "Device:C", "10u 50V", C1210, {"1": "5V_LDO", "2": "GND"}, "v33", "CL32B106KBJNNNE", "Samsung Electro-Mechanics"),
    P("U6", "Regulator_Linear:AP7361C-33E", "AP7361C-33E", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
      {"1": "5V_LDO", "2": "GND", "3": "3V3_LDO"}, "v33", "AP7361C-33E-13", "Diodes Incorporated"),
    P("C11", "Device:C", "47u 10V", C1206, {"1": "3V3_LDO", "2": "GND"}, "v33", "GRM31CR61A476ME15L", "Murata"),

    # ---------------- 5 USB-C
    P("J7", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
      {"A4": "VBUS_USB", "A9": "VBUS_USB", "B4": "VBUS_USB", "B9": "VBUS_USB", "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND",
       "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN", "A8": NC, "B8": NC},
      "usb", "USB4105-GF-A", "GCT"),
    P("R14", "Device:R", "5.1k", R0805, {"1": "CC1", "2": "GND"}, "usb", "RC0805FR-075K1L", "Yageo"),
    P("R15", "Device:R", "5.1k", R0805, {"1": "CC2", "2": "GND"}, "usb", "RC0805FR-075K1L", "Yageo"),
    P("U7", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
      {"1": "USB_DP", "6": "USB_DP", "3": "USB_DN", "4": "USB_DN", "5": "VBUS_USB", "2": "GND"}, "usb", "USBLC6-2SC6", "STMicroelectronics"),
    P("D4", "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA", {"1": "USB_PWR", "2": "VBUS_USB"}, "usb", "SS14-E3/61T", "Vishay", rot=180),
    P("Q1", "Transistor_FET:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23",
      {"1": "5V", "2": "5V_LDO", "3": "USB_PWR"}, "usb", "AO3401A", "Alpha & Omega Semiconductor",
      note="USB power switch. On only while the 5 V rail is down, so USB powers the board only with robot and bench power off."),
    P("R24", "Device:R", "22", R0805, {"1": "USB_DP", "2": "C3_DP"}, "usb", "RC0805FR-0722RL", "Yageo", note="USB D+ series resistor, per Espressif's checklist"),
    P("R25", "Device:R", "22", R0805, {"1": "USB_DN", "2": "C3_DN"}, "usb", "RC0805FR-0722RL", "Yageo", note="USB D- series resistor"),

    # ---------------- 6 MCU
    P("U4", "UWAT:ESP32-C3-MINI-1U", "ESP32-C3-MINI-1U-N4X", "UWAT:ESP32-C3-MINI-1U",
      {"1": "GND", "2": "GND", "3": "3V3", "4": NC, "5": "IO2", "6": "PGOOD", "7": NC, "8": "EN", "9": NC, "10": NC, "11":
       "GND", "12": NC, "13": NC, "14": "GND", "15": NC, "16": "LED_STAT", "17": NC, "18": "SDA", "19": "SCL", "20": NC, "21":
       NC, "22": "IO8", "23": "BOOT", "24": NC, "25": NC, "26": "C3_DN", "27": "C3_DP", "28": NC, "29": NC, "30": NC,
       "31": NC, "32": NC, "33": NC, "34": NC, "35": NC, "36": "GND", "37": "GND", "38": "GND", "39": "GND", "40": "GND",
       "41": "GND", "42": "GND", "43": "GND", "44": "GND", "45": "GND", "46": "GND", "47": "GND", "48": "GND", "49": "GND",
       "50": "GND", "51": "GND", "52": "GND", "53": "GND"},
      "mcu", "ESP32-C3-MINI-1U-N4X", "Espressif Systems", note="No antenna fitted. GPIO18/19 are the built-in USB serial and JTAG port."),
    P("C12", "Device:C", "47u 10V", C1206, {"1": "3V3", "2": "GND"}, "mcu", "GRM31CR61A476ME15L", "Murata"),
    P("C13", "Device:C", "100n", C0805, {"1": "3V3", "2": "GND"}, "mcu", "CC0805KRX7R9BB104", "Yageo"),
    P("C15", "Device:C", "100n", C0805, {"1": "3V3", "2": "GND"}, "mcu", "CC0805KRX7R9BB104", "Yageo"),
    P("R17", "Device:R", "10k", R0805, {"1": "3V3", "2": "EN"}, "mcu", "RC0805FR-0710KL", "Yageo", note="EN pull-up, 10k and 1u delay"),
    P("C9", "Device:C", "1u", C0805, {"1": "EN", "2": "GND"}, "mcu", "C2012X7R1H105K125AB", "TDK"),
    P("SW1", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "EN", "2": "GND"}, "mcu", "TL3342F160QG", "E-Switch"),
    P("SW2", "Switch:SW_Push", "BOOT", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "BOOT", "2": "GND"}, "mcu", "TL3342F160QG", "E-Switch",
      note="GPIO9 low at reset = download mode. GPIO9 has an internal pull-up."),
    P("R21", "Device:R", "10k", R0805, {"1": "3V3", "2": "IO2"}, "mcu", "RC0805FR-0710KL", "Yageo", note="GPIO2 strap held high"),
    P("R22", "Device:R", "10k", R0805, {"1": "3V3", "2": "IO8"}, "mcu", "RC0805FR-0710KL", "Yageo", note="GPIO8 strap held high, needed for download mode"),
    P("R23", "Device:R", "10k", R0805, {"1": "3V3", "2": "BOOT"}, "mcu", "RC0805FR-0710KL", "Yageo", note="GPIO9 pull-up, per Espressif's checklist"),

    # ---------------- 7 I2C, LEDs, outputs
    P("R5", "Device:R", "4.7k", R0805, {"1": "3V3", "2": "SDA"}, "io", "RC0805FR-074K7L", "Yageo"),
    P("R6", "Device:R", "4.7k", R0805, {"1": "3V3", "2": "SCL"}, "io", "RC0805FR-074K7L", "Yageo"),
    P("R7", "Device:R", "10k", R0805, {"1": "3V3", "2": "PGOOD"}, "io", "RC0805FR-0710KL", "Yageo"),
    P("J3", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "STEMMA QT", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
      {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"}, "io", "SM04B-SRSS-TB", "JST"),
    P("R20", "Device:R", "1k", R0805, {"1": "LED_STAT", "2": "LED3_A"}, "io", "RC0805FR-071KL", "Yageo"),
    P("LED3", "Device:LED", "Green", "LED_SMD:LED_0805_2012Metric", {"1": "GND", "2": "LED3_A"}, "io", "LTST-C171GKT", "Lite-On"),
    P("J6", "Connector_Generic:Conn_01x02", "5V OUT", "Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal",
      {"1": "5V", "2": "GND"}, "io", "1803277", "Phoenix Contact"),
    P("J9", "Connector_Generic:Conn_01x02", "3V3 OUT", "Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal",
      {"1": "3V3", "2": "GND"}, "io", "1803277", "Phoenix Contact"),

    # ---------------- 8 test points, mechanical
    P("TP1", "Connector:TestPoint", "VPORT", TPFP, {"1": "VPORT"}, "tp", in_bom=False),
    P("TP2", "Connector:TestPoint", "VIN_MOD", TPFP, {"1": "VIN_MOD"}, "tp", in_bom=False),
    P("TP3", "Connector:TestPoint", "5V", TPFP, {"1": "5V"}, "tp", in_bom=False),
    P("TP4", "Connector:TestPoint", "3V3", TPFP, {"1": "3V3"}, "tp", in_bom=False),
    P("TP5", "Connector:TestPoint", "GND", TPFP, {"1": "GND"}, "tp", in_bom=False),
    P("TP6", "Connector:TestPoint", "GND", TPFP, {"1": "GND"}, "tp", in_bom=False),
    P("TP8", "Connector:TestPoint", "RS485_A", TPFP, {"1": "RS485_A"}, "tp", in_bom=False),
    P("TP9", "Connector:TestPoint", "RS485_B", TPFP, {"1": "RS485_B"}, "tp", in_bom=False),
    P("TP10", "Connector:TestPoint", "PGOOD", TPFP, {"1": "PGOOD"}, "tp", in_bom=False),
    P("H1", "Mechanical:MountingHole", "#8-32", "UWAT:MountingHole_4.5mm_8-32", {}, "tp", in_bom=False),
    P("H2", "Mechanical:MountingHole", "#8-32", "UWAT:MountingHole_4.5mm_8-32", {}, "tp", in_bom=False),
    P("H3", "Mechanical:MountingHole", "#8-32", "UWAT:MountingHole_4.5mm_8-32", {}, "tp", in_bom=False),
    P("H4", "Mechanical:MountingHole", "#8-32", "UWAT:MountingHole_4.5mm_8-32", {}, "tp", in_bom=False),
]

# nets that need a PWR_FLAG so ERC sees them as driven
PWR_FLAGS = ["GND", "VPORT", "BENCH_IN", "VIN_OR", "VIN_MOD", "5V", "5V_LDO", "3V3", "VBUS_USB"]

NOTES = {
    "in": ["D5 and D3 OR the two inputs. Either can be plugged in alone or both at once.",
           "Meter the J1 pinout before the first plug-in. A wrong pinout can put battery on GND."],
    "v5": ["TPSM53602 set to 5.0 V: RFBT 10k, RFBB 2.49k (datasheet Table 7-1). 1.4 MHz fixed.",
           "EN tied to VIN. AGND joins PGND at the module. Input 2 x 10u, output 2 x 47u."],
    "sense": ["Route IN+ and IN- as Kelvin traces from the inside edge of each shunt pad.",
              "Addresses: U2 0x40, U3 0x41, U5 0x45."],
    "v33": ["5V_LDO is fed by 5V through D2, or by USB through D4 and Q1.",
            "Q1's gate sits on the 5 V rail: robot or bench power on turns Q1 off, so USB only carries data."],
    "usb": ["Separate 5.1k on each CC pin. USB D+/D- reach GPIO19/GPIO18 through 22 ohm R24, R25."],
    "mcu": ["USB-C is the built-in USB serial and JTAG port: flash and print over one cable.",
            "Hold BOOT, tap RESET for download mode. R21, R22 hold the GPIO2 and GPIO8 straps high.",
            "UART0 (GPIO20/21) is not broken out. USB-C is the console."],
    "tp": ["Test points are bare 3.4 x 1.8 mm copper pads, nothing to buy.",
           "Same land as a Keystone 5015, so a loop can be soldered on later."],
}
