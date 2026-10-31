"""Single source of truth for every part: value, footprint, sourcing."""

R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
C1210 = 'Capacitor_SMD:C_1210_3225Metric'
LED0603 = 'LED_SMD:LED_0603_1608Metric'

# Shared line items (one BOM line each). dk = DigiKey Canada part number.
LINES = {
    'ESP32':   dict(value='ESP32-S3-WROOM-1-N16R2', footprint='RF_Module:ESP32-S3-WROOM-1', mfr='Espressif', mpn='ESP32-S3-WROOM-1-N16R2', dk='5407-ESP32-S3-WROOM-1-N16R2CT-ND',
                    desc='WiFi + BLE module, 16 MB flash, 2 MB quad PSRAM, -40 to 85 C'),
    'BUCK':    dict(value='AP63301WU-7', footprint='Package_TO_SOT_SMD:TSOT-23-6', mfr='Diodes Inc', mpn='AP63301WU-7', dk='31-AP63301WU-7CT-ND',
                    desc='3.8 to 32 V buck, adjustable, 3 A, 500 kHz'),
    'RS485':   dict(value='MAX33071EASA+', footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', mfr='Analog Devices', mpn='MAX33071EASA+', dk='505-MAX33071EASA+-ND',
                    desc='3.3 V half-duplex RS-485, 2 Mbps, +/-65 V fault protected, true fail-safe. Cheaper drop-in: ST3485EBDR (497-2080-1-ND, 14 V max)'),
    'PORT':    dict(value='V5 smart port (4P4C)', footprint='stellaNova:Molex_43202-4101_RJ9_Horizontal', mfr='Molex', mpn='0432024101', dk='WM5439-ND',
                    desc='4P4C right-angle modular jack'),
    'USBC':    dict(value='USB-C 2.0', footprint='Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal', mfr='GCT', mpn='USB4105-GF-A', dk='2073-USB4105-GF-ACT-ND',
                    desc='USB-C receptacle, 16 pin, USB 2.0'),
    'SD':      dict(value='microSD push-push', footprint='Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5', mfr='Hirose', mpn='DM3AT-SF-PEJM5', dk='HR1964CT-ND',
                    desc='microSD socket with card detect'),
    'TVS':     dict(value='SMAJ18A', footprint='Diode_SMD:D_SMA', mfr='Bourns', mpn='SMAJ18A', dk='SMAJ18ABCT-ND',
                    desc='18 V standoff unidirectional TVS, 400 W'),
    'SCHOTTKY':dict(value='PMEG6020ER', footprint='Diode_SMD:Nexperia_CFP3_SOD-123W', mfr='Nexperia', mpn='PMEG6020ER,115', dk='1727-5217-1-ND',
                    desc='60 V 2 A Schottky'),
    'PTC':     dict(value='PTC 0.5 A 30 V', footprint='Fuse:Fuse_1812_4532Metric', mfr='Bel Fuse', mpn='0ZCG0050AF2C', dk='5923-0ZCG0050AF2CCT-ND',
                    desc='Resettable fuse, 0.5 A hold'),
    'IND':     dict(value='10uH', footprint='Inductor_SMD:L_Wuerth_MAPI-4030', mfr='Wurth', mpn='74438357100', dk='732-11206-1-ND',
                    desc='10 uH WE-MAPI 4030 shielded, Isat 4.6 A, DCR 110 mOhm max'),
    'ESD_USB': dict(value='USBLC6-2SC6', footprint='Package_TO_SOT_SMD:SOT-23-6', mfr='STMicroelectronics', mpn='USBLC6-2SC6', dk='497-5235-1-ND',
                    desc='USB data line ESD'),
    'SW':      dict(value='Tactile', footprint='Button_Switch_SMD:SW_SPST_PTS810', mfr='C&K', mpn='PTS810 SJM 250 SMTR LFS', dk='CKN10502CT-ND',
                    desc='SMD tactile switch 4.2 x 3.2 mm'),
    'LED_G':   dict(value='Green', footprint=LED0603, mfr='Lite-On', mpn='LTST-C191KGKT', dk='160-1446-1-ND', desc='0603 green AlInGaP LED'),
    'LED_O':   dict(value='Orange', footprint=LED0603, mfr='Lite-On', mpn='LTST-C191KFKT', dk='160-1445-1-ND', desc='0603 orange LED'),
    'LED_R':   dict(value='Red', footprint=LED0603, mfr='Lite-On', mpn='LTST-C191KRKT', dk='160-1447-1-ND', desc='0603 red LED'),
    'C10U50':  dict(value='10uF 50V', footprint=C1210, mfr='Samsung', mpn='CL32B106KBJNNNE', dk='1276-3387-1-ND', desc='10 uF 50 V X7R 1210'),
    'C100N':   dict(value='100nF', footprint=C0603, mfr='Yageo', mpn='CC0603KRX7R9BB104', dk='311-1344-1-ND', desc='100 nF 50 V X7R 0603'),
    'C22U':    dict(value='22uF', footprint=C0805, mfr='Murata', mpn='GRM21BR61A226ME51L', dk='490-10511-1-ND', desc='22 uF 10 V X5R 0805'),
    'C10U':    dict(value='10uF', footprint=C0805, mfr='Murata', mpn='GRM21BR61E106KA73K', dk='490-16824-1-ND', desc='10 uF 25 V X5R 0805'),
    'C1U':     dict(value='1uF', footprint=C0603, mfr='TDK', mpn='C1608X5R1H105K080AB', dk='445-7468-1-ND', desc='1 uF 50 V X5R 0603'),
    'C220U':   dict(value='220uF', footprint='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B', mfr='KEMET', mpn='T520B227M006ATE045', dk='399-5755-1-ND',
                    desc='220 uF 6.3 V tantalum polymer, 45 mOhm'),
    'R10K':    dict(value='10k', footprint=R0603, mfr='Yageo', mpn='RC0603FR-1310KL', dk='13-RC0603FR-1310KLCT-ND', desc='10 k 1% 0603'),
    'R100K':   dict(value='100k', footprint=R0603, mfr='Stackpole', mpn='RMCF0603FT100K', dk='RMCF0603FT100KCT-ND', desc='100 k 1% 0603'),
    'R5K1':    dict(value='5.1k', footprint=R0603, mfr='Yageo', mpn='RC0603FR-075K1L', dk='311-5.10KHRCT-ND', desc='5.1 k 1% 0603'),
    'R1K':     dict(value='1k', footprint=R0603, mfr='Yageo', mpn='RC0603FR-071KL', dk='311-1.00KHRCT-ND', desc='1 k 1% 0603'),
    'R22':     dict(value='22', footprint=R0603, mfr='Stackpole', mpn='RMCF0603FT22R0', dk='RMCF0603FT22R0CT-ND', desc='22 ohm 1% 0603'),
    'R120':    dict(value='120', footprint=R0603, mfr='Yageo', mpn='RC0603FR-07120RL', dk='311-120HRCT-ND', desc='120 ohm 1% 0603'),
    'R_UVLO':  dict(value='37.4k', footprint=R0603, mfr='Yageo', mpn='RC0603FR-0737K4L', dk='311-37.4KHRCT-ND', desc='37.4 k 1% 0603'),
    'R_FBT':   dict(value='93.1k', footprint=R0603, mfr='Stackpole', mpn='RMCF0603FT93K1', dk='RMCF0603FT93K1CT-ND', desc='FB divider top, 1% 0603'),
    'R_FBB':   dict(value='30.1k', footprint=R0603, mfr='Yageo', mpn='RC0603FR-0730K1L', dk='311-30.1KHRCT-ND', desc='FB divider bottom, 1% 0603'),
    'C_FF':    dict(value='56pF', footprint=C0603, mfr='KEMET', mpn='C0603C560J5GACTU', dk='399-C0603C560J5GACTUCT-ND', desc='56 pF 50 V C0G 0603 feed-forward'),
    'TP':      dict(value='TP', footprint='TestPoint:TestPoint_Pad_D1.5mm', mfr='', mpn='', dk='', desc='Bare test pad'),
    'HOLE':    dict(value='MountingHole', footprint='MountingHole:MountingHole_4.3mm_M4', mfr='', mpn='', dk='', desc='4.3 mm NPTH'),
}

ASSIGN = {
    'U1': 'ESP32', 'U2': 'BUCK', 'U3': 'RS485', 'J1': 'PORT', 'J2': 'USBC', 'J3': 'SD',
    'F1': 'PTC', 'D1': 'TVS', 'D2': 'SCHOTTKY', 'D3': 'SCHOTTKY', 'D5': 'ESD_USB',
    'D6': 'LED_G', 'D7': 'LED_O', 'D8': 'LED_R', 'L1': 'IND',
    'C1': 'C10U50', 'C2': 'C100N', 'C3': 'C100N', 'C4': 'C22U', 'C5': 'C22U', 'C6': 'C220U', 'C7': 'C100N',
    'C8': 'C10U', 'C9': 'C100N', 'C10': 'C1U', 'C11': 'C10U', 'C12': 'C100N',
    'R1': 'R100K', 'R2': 'R_UVLO', 'R3': 'R10K', 'R4': 'R120', 'R5': 'R10K', 'R6': 'R10K', 'R7': 'R5K1', 'R8': 'R5K1',
    'R9': 'R10K', 'R10': 'R10K', 'R11': 'R10K', 'R12': 'R10K', 'R13': 'R10K', 'R14': 'R10K',
    'R15': 'R1K', 'R16': 'R1K', 'R17': 'R1K',
    'R18': 'R22', 'R19': 'R22', 'R20': 'R_FBT', 'R21': 'R_FBB', 'C13': 'C_FF', 'R22': 'R5K1',
    'SW1': 'SW', 'SW2': 'SW',
    'TP1': 'TP', 'TP2': 'TP', 'TP3': 'TP', 'TP4': 'TP', 'TP5': 'TP',
}
DNP = {'R2', 'R4', 'C6'}
ROLE = {
    'U1': 'MCU', 'U2': 'Buck', 'U3': 'RS-485', 'J1': 'Smart port', 'J2': 'USB', 'J3': 'microSD',
    'F1': 'Port fuse', 'D1': 'Surge clamp', 'D2': 'Reverse block', 'D3': 'USB OR-ing',
    'D5': 'USB ESD', 'D6': 'Power LED', 'D7': 'Link LED', 'D8': 'Activity LED', 'L1': 'Buck inductor',
    'C1': 'VIN bulk', 'C2': 'VIN HF', 'C3': 'Bootstrap', 'C4': '3V3 out', 'C5': '3V3 out', 'C6': '3V3 bulk (DNP)',
    'C7': 'U3 decouple', 'C8': 'U1 decouple', 'C9': 'U1 decouple', 'C10': 'EN delay', 'C11': 'SD bulk', 'C12': 'SD decouple',
    'R1': 'Buck enable', 'R2': 'UVLO (DNP)', 'R3': 'DE pulldown', 'R4': 'Termination (DNP)', 'R5': 'EN pullup', 'R6': 'BOOT pullup',
    'R7': 'CC1', 'R8': 'CC2', 'R9': 'SD CMD pullup', 'R10': 'SD D0 pullup', 'R11': 'SD D1 pullup', 'R12': 'SD D2 pullup',
    'R13': 'SD D3 pullup', 'R14': 'SD detect pullup', 'R15': 'LED', 'R16': 'LED', 'R17': 'LED', 'R18': 'USB D- series', 'R19': 'USB D+ series', 'R20': 'FB top', 'R21': 'FB bottom', 'C13': 'FB feed-forward', 'R22': 'VBUS discharge',
    'SW1': 'RESET', 'SW2': 'BOOT', 'TP1': 'VIN', 'TP2': '3V3', 'TP3': 'GND', 'TP4': 'U0TXD', 'TP5': 'U0RXD',
}

PART = {}
for ref, key in ASSIGN.items():
    d = dict(LINES[key]); d['line'] = key; d['dnp'] = ref in DNP
    PART[ref] = d

def fields_for(ref):
    p = PART[ref]
    f = {}
    if p.get('mfr'): f['Manufacturer'] = p['mfr']
    if p.get('mpn'): f['MPN'] = p['mpn']
    if p.get('dk'): f['DigiKey'] = p['dk']
    return f

# DigiKey Canada stock and CAD price (qty 1, qty 10), checked live 2026-10-30
STOCK = {
    'ESP32': (4702, 10.61, 9.184), 'BUCK': (13846, 1.52, 1.091), 'RS485': (2956, 12.30, 9.504),
    'PORT': (2540, 2.18, 1.856), 'USBC': (85103, 1.19, 1.004), 'SD': (76375, 5.27, 4.483),
    'TVS': (29489, 0.77, 0.477), 'SCHOTTKY': (375398, 0.74, 0.460), 'PTC': (345670, 0.31, 0.242),
    'IND': (15980, 2.68, 2.544), 'ESD_USB': (63343, 0.80, 0.489), 'SW': (69851, 0.92, 0.793),
    'LED_G': (2712898, 0.24, 0.165), 'LED_O': (195728, 0.22, 0.155), 'LED_R': (1354761, 0.24, 0.165),
    'C10U50': (742985, 1.02, 0.636), 'C100N': (4044224, 0.21, 0.119), 'C22U': (269759, 0.30, 0.168),
    'C10U': (88143, 0.25, 0.141), 'C1U': (105003, 0.25, 0.140), 'C220U': (101454, 2.12, 1.392),
    'R10K': (221620, 0.16, 0.040), 'R100K': (970951, 0.17, 0.035), 'R5K1': (405843, 0.16, 0.040),
    'R1K': (1993948, 0.17, 0.043), 'R120': (49122, 0.16, 0.040), 'R_UVLO': (20441, 0.16, 0.040),
    'R_FBT': (216165, 0.16, 0.033), 'R_FBB': (119797, 0.16, 0.040), 'R22': (2171898, 0.16, 0.033),
    'C_FF': (153858, 0.15, 0.068),
}
