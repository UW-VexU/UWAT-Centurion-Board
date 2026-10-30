"""Project-local symbols: V5 smart port connector, SN65HVD75DR, VIN power rail."""
import copy
from sexp import Sym as S, dump, find, findall
from libs import flatten

LIB = 'stellaNova'

def _eff(size=1.27, hide=False, justify=None):
    e = [S('effects'), [S('font'), [S('size'), size, size]]]
    if justify:
        e.append([S('justify'), S(justify)])
    if hide:
        e.append(S('hide'))
    return e

def _prop(k, v, at, hide=False, justify=None):
    return [S('property'), k, v, [S('at'), at[0], at[1], 0], _eff(hide=hide, justify=justify)]

def _pin(kind, x, y, rot, length, name, num):
    return [S('pin'), S(kind), S('line'), [S('at'), x, y, rot], [S('length'), length],
            [S('name'), name, _eff()], [S('number'), num, _eff()]]

def v5_port(prefix=True):
    n = 'V5_SmartPort'
    sym = [S('symbol'), f'{LIB}:{n}' if prefix else n,
           [S('pin_names'), [S('offset'), 1.016]], [S('in_bom'), S('yes')], [S('on_board'), S('yes')],
           _prop('Reference', 'J', (-5.08, 8.89), justify='left'),
           _prop('Value', 'V5_SmartPort', (-5.08, -7.62), justify='left'),
           _prop('Footprint', 'stellaNova:Molex_43202-4101_RJ9_Horizontal', (0, -10.16), hide=True),
           _prop('Datasheet', 'https://kb.vex.com/hc/en-us/articles/360036143012', (0, -12.7), hide=True),
           _prop('ki_description', 'VEX V5 smart port, 4P4C: RS-485 half-duplex pair plus raw battery. '
                 'Contact order A, B, GND, + (labelled smart cable photo, VEX Forum). Cables are straight-through.',
                 (0, 0), hide=True),
           _prop('ki_keywords', 'VEX V5 smart port RJ9 4P4C RS485', (0, 0), hide=True),
           [S('symbol'), f'{n}_0_1',
            [S('rectangle'), [S('start'), -5.08, 7.62], [S('end'), 7.62, -5.08],
             [S('stroke'), [S('width'), 0.254], [S('type'), S('default')]], [S('fill'), [S('type'), S('background')]]]],
           [S('symbol'), f'{n}_1_1',
            _pin('passive', -10.16, 5.08, 0, 5.08, 'VBAT', '4'),
            _pin('passive', -10.16, 2.54, 0, 5.08, 'GND', '3'),
            _pin('passive', -10.16, 0, 0, 5.08, 'DATA_B', '2'),
            _pin('passive', -10.16, -2.54, 0, 5.08, 'DATA_A', '1')]]
    return sym

def _rename(flat, old, new, prefix, props):
    s = copy.deepcopy(flat)
    s[1] = f'{LIB}:{new}' if prefix else new
    for c in s:
        if isinstance(c, list) and c and c[0] == 'symbol':
            c[1] = c[1].replace(old + '_', new + '_', 1)
        if isinstance(c, list) and c and c[0] == 'property' and c[1] in props:
            c[2] = props[c[1]]
    return s

def sn65hvd75(prefix=True):
    f = flatten('Interface_UART', 'MAX3485')
    return _rename(f, 'MAX3485', 'MAX33071E', prefix, {
        'Value': 'MAX33071EASA+',
        'Footprint': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
        'Datasheet': 'https://www.analog.com/media/en/technical-documentation/data-sheets/MAX33070E-MAX33071E.pdf',
        'ki_description': '3.3 V half-duplex RS-485 transceiver, 65 V fault protected A/B, true fail-safe, 2 Mbps, SOIC-8 '
                          'standard pinout. Pin compatible: ST3485EBDR, SN65HVD75DR',
        'ki_keywords': 'RS485 RS-485 transceiver half duplex 3.3V fault protected',
    })

def vin_rail(prefix=True):
    f = flatten('power', '+BATT')
    s = _rename(f, '+BATT', 'VIN', prefix, {'Value': 'VIN', 'ki_description': 'Power symbol: buck input rail after protection',
                                             'ki_keywords': 'power-flag VIN'})
    for u in findall(s, 'symbol'):
        for p in findall(u, 'pin'):
            nm = find(p, 'name')
            if nm[1] == '+BATT':
                nm[1] = 'VIN'
    return s

def ap63301(prefix=True):
    f = flatten('Regulator_Switching', 'AP63200WU')
    return _rename(f, 'AP63200WU', 'AP63301WU', prefix, {
        'Value': 'AP63301WU-7',
        'Footprint': 'Package_TO_SOT_SMD:TSOT-23-6',
        'Datasheet': 'https://www.diodes.com/assets/Datasheets/AP63300-AP63301.pdf',
        'ki_description': '3.8 to 32 V in, 3 A synchronous buck, adjustable (0.8 V FB), 500 kHz, TSOT-26',
        'ki_keywords': 'buck step-down regulator adjustable',
    })

def write_lib(path):
    root = [S('kicad_symbol_lib'), [S('version'), 20220914], [S('generator'), S('kicad_symbol_editor')],
            v5_port(False), sn65hvd75(False), vin_rail(False), ap63301(False)]
    open(path, 'w').write(dump(root) + '\n')

def register(sch):
    sch.use(f'{LIB}:V5_SmartPort', v5_port())
    sch.use(f'{LIB}:MAX33071E', sn65hvd75())
    sch.use(f'{LIB}:VIN', vin_rail())
    sch.use(f'{LIB}:AP63301WU', ap63301())
