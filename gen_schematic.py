#!/usr/bin/env python3
"""Generate a minimal LCMXO2-4000HC-TG144 board schematic for KiCad 8.

Connectivity is done with local net labels placed on pin endpoints, so the
schematic is purely label-wired (no wires) -- valid and netlists correctly.
"""
import json, sys, uuid

IODB = sys.argv[1]
OUT = sys.argv[2]
PROJECT = "machxo2-mini"
ROOT = str(uuid.uuid4())

def U(): return str(uuid.uuid4())
def q(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
def f(v): return ("%.3f" % v).rstrip('0').rstrip('.')

# ---------------------------------------------------------------- pin data
d = json.load(open(IODB))
meta = {(m['col'], m['row'], m['pio']): m for m in d['pio_metadata']}
io = {}
for pin, v in d['packages']['TQFP144'].items():
    m = meta[(v['col'], v['row'], v['pio'])]
    c, r = v['col'], v['row']
    side = 'PL' if c == 0 else 'PR' if c == 31 else 'PT' if r == 0 else 'PB'
    idx = r if side in ('PL', 'PR') else c
    name = f"{side}{idx}{v['pio']}"
    if 'function' in m:
        name += '/' + m['function']
    io[int(pin)] = (name, m['bank'])

# Non-PIO pins from Lattice MachXO2-4000 pinout CSV (TQFP144 column).
PWR = {7: 'VCCIO5', 8: 'GND', 16: 'VCCIO4', 18: 'GND', 29: 'GND', 30: 'VCCIO3',
       36: 'VCC', 37: 'VCCIO2', 46: 'GND', 51: 'VCCIO2', 53: 'GND', 64: 'GND',
       66: 'VCCIO2', 72: 'VCC', 79: 'VCCIO1', 80: 'GND', 88: 'VCCIO1', 90: 'GND',
       101: 'GND', 102: 'VCCIO1', 108: 'VCC', 116: 'GND', 118: 'VCCIO0',
       123: 'VCCIO0', 124: 'GND', 129: 'NC', 134: 'GND', 135: 'VCCIO0', 144: 'VCC'}
assert set(io) | set(PWR) == set(range(1, 145)) and not set(io) & set(PWR)

# --------------------------------------------------------- net assignment
fpga_net = {}
for p, n in PWR.items():
    fpga_net[p] = None if n == 'NC' else ('GND' if n == 'GND' else '+3V3')

fixed = {130: 'TMS', 131: 'TCK', 136: 'TDI', 137: 'TDO',
         119: 'PROGRAMN', 110: 'INITN', 109: 'DONE', 120: 'JTAGENB',
         128: 'CLK12',            # PCLKT0_1, primary clock input
         97: 'LED0', 98: 'LED1', 99: 'LED2', 100: 'LED3',
         96: 'BTN0',
         111: 'UART_TX', 112: 'UART_RX'}
for p, n in fixed.items():
    assert p in io, p
    fpga_net[p] = n
free = [p for p in sorted(io) if p not in fixed]
hdrA, hdrB, rest = free[:36], free[36:72], free[72:]
for p in hdrA + hdrB:
    fpga_net[p] = f"IO_{p}"
for p in rest:
    fpga_net[p] = None  # no-connect

# ------------------------------------------------------------- lib symbols
FONT = '(effects (font (size 1.27 1.27)))'
FONTH = '(effects (font (size 1.27 1.27)) hide)'

def prop(name, val, x=0, y=0, hide=False):
    return f'(property {q(name)} {q(val)} (at {f(x)} {f(y)} 0) {FONTH if hide else FONT})'

def pin_s(num, name, typ, x, y, ang, length=2.54):
    return (f'(pin {typ} line (at {f(x)} {f(y)} {ang}) (length {f(length)}) '
            f'(name {q(name)} {FONT}) (number {q(str(num))} {FONT}))')

libs = {}

def two_pin(sym, ref, graphics, pin_type='passive', names=('~', '~'), nums=('1', '2')):
    # pin nums[0] at top, nums[1] at bottom
    libs[sym] = (f'(symbol {q("dssoft:" + sym)} (pin_numbers hide) (pin_names (offset 0) hide) '
                 f'(in_bom yes) (on_board yes) '
                 f'{prop("Reference", ref, 2.54, 1.27)} {prop("Value", sym, 2.54, -1.27)} '
                 f'{prop("Footprint", "", 0, 0, True)} {prop("Datasheet", "", 0, 0, True)} '
                 ''
                 f'(symbol {q(sym + "_0_1")} {graphics}) '
                 f'(symbol {q(sym + "_1_1")} '
                 f'{pin_s(nums[0], names[0], pin_type, 0, 3.81, 270, 1.27)} '
                 f'{pin_s(nums[1], names[1], pin_type, 0, -3.81, 90, 1.27)}))')
    return {nums[0]: (0, 3.81), nums[1]: (0, -3.81)}

ST = '(stroke (width 0.254) (type default))'
R_PINS = two_pin('R', 'R', f'(rectangle (start -1.016 2.54) (end 1.016 -2.54) {ST} (fill (type none)))')
C_PINS = two_pin('C', 'C',
    f'(polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) {ST} (fill (type none))) '
    f'(polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) {ST} (fill (type none))) '
    f'(polyline (pts (xy 0 2.54) (xy 0 0.762)) {ST} (fill (type none))) '
    f'(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) {ST} (fill (type none)))')
LED_PINS = two_pin('LED', 'D',
    f'(polyline (pts (xy -1.27 1.27) (xy 1.27 1.27) (xy 0 -1.27) (xy -1.27 1.27)) {ST} (fill (type none))) '
    f'(polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) {ST} (fill (type none))) '
    f'(polyline (pts (xy 0 2.54) (xy 0 1.27)) {ST} (fill (type none))) '
    f'(polyline (pts (xy 0 -1.27) (xy 0 -2.54)) {ST} (fill (type none)))',
    names=('A', 'K'), nums=('2', '1'))   # KiCad LED footprints: pad1 = K, pad2 = A
SW_PINS = two_pin('SW_Push', 'SW',
    f'(polyline (pts (xy 0 2.54) (xy 0 1.27)) {ST} (fill (type none))) '
    f'(polyline (pts (xy 0 -1.27) (xy 0 -2.54)) {ST} (fill (type none))) '
    f'(polyline (pts (xy -1.016 1.27) (xy 1.016 -1.016)) {ST} (fill (type none))) '
    f'(circle (center 0 -1.27) (radius 0.254) {ST} (fill (type none))) '
    f'(polyline (pts (xy 1.524 0) (xy 2.794 0)) {ST} (fill (type none)))')
FLAG_PINS = {}
libs['PWR_FLAG'] = (f'(symbol "dssoft:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide) '
    f'(in_bom no) (on_board yes) '
    f'{prop("Reference", "#FLG", 0, 1.905, True)} {prop("Value", "PWR_FLAG", 0, 3.81)} '
    f'{prop("Footprint", "", 0, 0, True)} {prop("Datasheet", "", 0, 0, True)} '
    f'(symbol "PWR_FLAG_0_0" {pin_s(1, "pwr", "power_out", 0, 0, 90, 0)}) '
    f'(symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) '
    f'(stroke (width 0) (type default)) (fill (type none)))))')
FLAG_PINS = {'1': (0, 0)}

def box(sym, ref, left, right=(), width=15.24, units=None):
    """Generic box symbol. left/right: lists of (num, name, type).
    units: optional list of (left, right) per unit -> multi-unit symbol."""
    if units is None:
        units = [(left, right)]
    pins_pos = {}  # unit -> {num: (x,y)}
    body = ''
    for ui, (L, Rr) in enumerate(units, start=1):
        n = max(len(L), len(Rr), 1)
        g = (f'(rectangle (start 0 2.54) (end {f(width)} {f(-n * 2.54)}) '
             f'(stroke (width 0.254) (type default)) (fill (type background)))')
        ps = []
        pos = {}
        for i, (num, name, typ) in enumerate(L):
            y = -i * 2.54
            ps.append(pin_s(num, name, typ, -2.54, y, 0))
            pos[str(num)] = (-2.54, y)
        for i, (num, name, typ) in enumerate(Rr):
            y = -i * 2.54
            ps.append(pin_s(num, name, typ, width + 2.54, y, 180))
            pos[str(num)] = (width + 2.54, y)
        body += f'(symbol {q(f"{sym}_{ui}_1")} {g} {" ".join(ps)}) '
        pins_pos[ui] = pos
    multi = len(units) > 1
    libs[sym] = (f'(symbol {q("dssoft:" + sym)} (pin_names (offset 1.016)) '
                 f'{"(pin_numbers hide) " if False else ""}'
                 f'(in_bom yes) (on_board yes) '
                 f'{prop("Reference", ref, 0, 5.08)} {prop("Value", sym, 0, 3.81)} '
                 f'{prop("Footprint", "", 0, 0, True)} {prop("Datasheet", "", 0, 0, True)} '
                 f'{prop("Description", "", 0, 0, True)} {body})')
    return pins_pos

# FPGA: units 1..6 = banks 0..5, unit 7 = power
bank_units = []
for b in range(6):
    pins = [(p, io[p][0], 'bidirectional') for p in sorted(io) if io[p][1] == b]
    bank_units.append((pins, ()))
vcc = [(p, n, 'power_in') for p, n in sorted(PWR.items()) if n.startswith('VCC')]
gnd = [(p, n, 'power_in') for p, n in sorted(PWR.items()) if n == 'GND']
nc = [(p, n, 'no_connect') for p, n in sorted(PWR.items()) if n == 'NC']
bank_units.append((vcc, gnd + nc))
FPGA_PINS = box('LCMXO2-4000HC-TG144', 'U', None, units=bank_units, width=25.4)

LDO_PINS = box('AP2112K-3.3', 'U',
               [(1, 'VIN', 'power_in'), (3, 'EN', 'input'), (2, 'GND', 'power_in')],
               [(5, 'VOUT', 'power_out'), (4, 'NC', 'no_connect')], width=12.7)[1]
OSC_PINS = box('XO_4pin', 'X',
               [(4, 'VDD', 'power_in'), (1, 'OE', 'input'), (2, 'GND', 'power_in')],
               [(3, 'OUT', 'output')], width=12.7)[1]
USB_PINS = box('USB_C_Power', 'J',
               [('A4', 'VBUS', 'passive'), ('A9', 'VBUS', 'passive'), ('B4', 'VBUS', 'passive'),
                ('B9', 'VBUS', 'passive'), ('A5', 'CC1', 'passive'), ('B5', 'CC2', 'passive'),
                ('A6', 'D+', 'passive'), ('B6', 'D+', 'passive'), ('A7', 'D-', 'passive'),
                ('B7', 'D-', 'passive'), ('A8', 'SBU1', 'passive'), ('B8', 'SBU2', 'passive')],
               [('A1', 'GND', 'passive'), ('A12', 'GND', 'passive'), ('B1', 'GND', 'passive'),
                ('B12', 'GND', 'passive'), ('SH', 'SHIELD', 'passive')], width=12.7)[1]

def conn1(n):
    return box(f'Conn_01x{n:02d}', 'J', [(i, f'Pin_{i}', 'passive') for i in range(1, n + 1)], width=5.08)[1]
J6_PINS = conn1(6)
J3_PINS = conn1(3)
C2_PINS = box('Conn_02x20_Odd_Even', 'J',
              [(2 * i + 1, f'Pin_{2*i+1}', 'passive') for i in range(20)],
              [(2 * i + 2, f'Pin_{2*i+2}', 'passive') for i in range(20)], width=7.62)[1]

# ------------------------------------------------------------ placement
items = []     # schematic items
refcount = {"U": 1}

def label(net, x, y, ang):
    just = 'left bottom' if ang in (0, 90) else 'right bottom'
    items.append(f'(label {q(net)} (at {f(x)} {f(y)} {ang}) '
                 f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {q(U())}))')

def noconn(x, y):
    items.append(f'(no_connect (at {f(x)} {f(y)}) (uuid {q(U())}))')

def text(s, x, y, size=2.0):
    if y > 150: y -= 70
    items.append(f'(text {q(s)} (at {f(x)} {f(y)} 0) '
                 f'(effects (font (size {size} {size})) (justify left bottom)) (uuid {q(U())}))')

def place(sym, prefix, x, y, value, footprint, pinpos, nets, unit=1, ref=None, extra_props='',
          in_bom=True, two=False):
    """nets: {pinnum: netname or None(no-connect)}. Every pin must be in nets."""
    if y > 150: y -= 70
    if ref is None:
        refcount[prefix] = refcount.get(prefix, 0) + 1
        ref = f'{prefix}{refcount[prefix]}'
    hide_ref = ref.startswith('#')
    rx, ry = (x + 2.54, y - 1.27) if two else (x, y - 5.08)
    vx, vy = (x + 2.54, y + 1.27) if two else (x, y - 3.81)
    pins = ''.join(f'(pin {q(str(n))} (uuid {q(U())}))' for n in pinpos)
    items.append(
        f'(symbol (lib_id {q("dssoft:" + sym)}) (at {f(x)} {f(y)} 0) (unit {unit}) '
        f'(in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp no) '
        f'(uuid {q(U())}) '
        f'(property "Reference" {q(ref)} (at {f(rx)} {f(ry)} 0) '
        f'(effects (font (size 1.27 1.27)) (justify left){" hide" if hide_ref else ""})) '
        f'(property "Value" {q(value)} (at {f(vx)} {f(vy)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
        f'(property "Footprint" {q(footprint)} (at {f(x)} {f(y)} 0) {FONTH}) '
        f'(property "Datasheet" "" (at {f(x)} {f(y)} 0) {FONTH}) '
                f'{extra_props}{pins} '
        f'(instances (project {q(PROJECT)} (path {q("/" + ROOT)} (reference {q(ref)}) (unit {unit})))))')
    for n, (px, py) in pinpos.items():
        sx, sy = x + px, y - py
        net = nets[str(n)] if str(n) in nets else nets.get(n, 'MISSING')
        assert net != 'MISSING', (ref, n)
        if net is None:
            noconn(sx, sy)
        elif two:
            label(net, sx, sy, 90 if py > 0 else 270)
        else:
            label(net, sx, sy, 180 if px < 0 else 0)
    return ref

def passive(kind, x, y, value, top, bot, fp):
    pins, sym, pre = {'R': (R_PINS, 'R', 'R'), 'C': (C_PINS, 'C', 'C'),
                      'LED': (LED_PINS, 'LED', 'D'), 'SW': (SW_PINS, 'SW_Push', 'SW')}[kind]
    keys = list(pins)  # [top, bottom]
    return place(sym, pre, x, y, value, fp, pins, {keys[0]: top, keys[1]: bot}, two=True)

FP_R = 'Resistor_SMD:R_0603_1608Metric'
FP_C = 'Capacitor_SMD:C_0603_1608Metric'
FP_C10 = 'Capacitor_SMD:C_0805_2012Metric'
FP_LED = 'LED_SMD:LED_0603_1608Metric'

# --- FPGA units -------------------------------------------------------
text('MachXO2-4000HC (TQFP-144) - single 3.3 V supply, internal config flash', 20, 18, 3)
ux = [45, 125, 205, 285, 365, 445]
for b in range(6):
    pos = FPGA_PINS[b + 1]
    nets = {str(p): fpga_net[int(p)] for p in pos}
    place('LCMXO2-4000HC-TG144', 'U', ux[b], 35, 'LCMXO2-4000HC-4TG144C',
          'Package_QFP:TQFP-144_20x20mm_P0.5mm', pos, nets, unit=b + 1, ref='U1')
    text(f'Bank {b}  (VCCIO{b} = 3.3 V)', ux[b], 28, 1.8)
pos = FPGA_PINS[7]
place('LCMXO2-4000HC-TG144', 'U', 45, 200, 'LCMXO2-4000HC-4TG144C',
      'Package_QFP:TQFP-144_20x20mm_P0.5mm', pos, {str(p): fpga_net[int(p)] for p in pos},
      unit=7, ref='U1')
text('U1 power: HC core regulator -> VCC = 3.3 V', 30, 190, 1.8)

# --- Decoupling -------------------------------------------------------
text('Decoupling: one 100 nF per VCC / VCCIO pin, at the pin (16x) + 2x 10 uF bulk', 140, 190, 1.8)
for i in range(16):
    passive('C', 145 + i * 10, 205, '100n', '+3V3', 'GND', FP_C)
for i in range(2):
    passive('C', 310 + i * 10, 205, '10u', '+3V3', 'GND', FP_C10)

# --- Power: USB-C -> AP2112K-3.3 -------------------------------------
text('Power in: USB-C (power only) -> 3.3 V LDO', 30, 245, 1.8)
usb_nets = {'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS', 'A5': 'CC1', 'B5': 'CC2',
            'A6': None, 'B6': None, 'A7': None, 'B7': None, 'A8': None, 'B8': None,
            'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND'}
place('USB_C_Power', 'J', 45, 255, 'USB_C_Receptacle',
      'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', USB_PINS, usb_nets)
passive('R', 80, 260, '5k1', 'CC1', 'GND', FP_R)
passive('R', 90, 260, '5k1', 'CC2', 'GND', FP_R)
place('AP2112K-3.3', 'U', 115, 255, 'AP2112K-3.3', 'Package_TO_SOT_SMD:SOT-23-5', LDO_PINS,
      {'1': 'VBUS', '3': 'VBUS', '2': 'GND', '5': '+3V3', '4': None})
passive('C', 150, 260, '10u', 'VBUS', 'GND', FP_C10)
passive('C', 160, 260, '10u', '+3V3', 'GND', FP_C10)
passive('R', 175, 255, '1k', '+3V3', 'PWR_LED', FP_R)
passive('LED', 175, 268, 'PWR', 'PWR_LED', 'GND', FP_LED)
for i, net in enumerate(['VBUS', 'GND', '+3V3']):
    place('PWR_FLAG', '#FLG', 195 + i * 12, 258, 'PWR_FLAG', '', FLAG_PINS, {'1': net},
          in_bom=False)

# --- Config / JTAG ----------------------------------------------------
text('Configuration + JTAG (program with any FT2232H / openFPGALoader / Diamond Programmer)', 230, 245, 1.8)
passive('R', 235, 260, '10k', '+3V3', 'PROGRAMN', FP_R)
passive('SW', 235, 275, 'PROGRAM', 'PROGRAMN', 'GND', 'Button_Switch_SMD:SW_SPST_TL3342')
passive('R', 248, 260, '10k', '+3V3', 'INITN', FP_R)
passive('R', 261, 260, '10k', '+3V3', 'DONE', FP_R)
passive('R', 274, 260, '10k', 'JTAGENB', 'GND', FP_R)
passive('R', 287, 260, '4k7', 'TCK', 'GND', FP_R)
passive('R', 300, 260, '4k7', '+3V3', 'TMS', FP_R)
passive('R', 313, 260, '4k7', '+3V3', 'TDI', FP_R)
place('Conn_01x06', 'J', 340, 255, 'JTAG', 'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
      J6_PINS, {'1': '+3V3', '2': 'TCK', '3': 'TDI', '4': 'TDO', '5': 'TMS', '6': 'GND'})
text('JTAG: 1=VREF 2=TCK 3=TDI 4=TDO 5=TMS 6=GND', 330, 250, 1.27)

# --- Clock ------------------------------------------------------------
text('12 MHz XO -> PCLKT0_1 (optional; internal OSCH is +/-5%)', 380, 245, 1.8)
place('XO_4pin', 'X', 395, 255, '12MHz', 'Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
      OSC_PINS, {'4': '+3V3', '1': '+3V3', '2': 'GND', '3': 'CLK12'})
passive('C', 430, 260, '100n', '+3V3', 'GND', FP_C)

# --- User I/O ---------------------------------------------------------
text('User I/O: 4 LEDs, 1 button (enable internal pull-up), UART header', 30, 295, 1.8)
for i in range(4):
    passive('R', 35 + i * 12, 305, '1k', f'LED{i}', f'LED{i}_A', FP_R)
    passive('LED', 35 + i * 12, 318, f'LED{i}', f'LED{i}_A', 'GND', FP_LED)
for i in range(4):
    pass
# fix: LED anode should be driven by the resistor; nets above go FPGA->R->LED(A)->K->GND
passive('SW', 100, 310, 'USER', 'BTN0', 'GND', 'Button_Switch_SMD:SW_SPST_TL3342')
place('Conn_01x03', 'J', 125, 305, 'UART', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
      J3_PINS, {'1': 'UART_TX', '2': 'UART_RX', '3': 'GND'})
text('UART: 1=TX(out) 2=RX(in) 3=GND - FT2232H channel B works', 115, 300, 1.27)

# --- GPIO headers -----------------------------------------------------
text('GPIO breakout: 2x 2x20, pins 1/2 = 3V3, 39/40 = GND', 170, 295, 1.8)
for hi, (hx, plist) in enumerate([(185, hdrA), (260, hdrB)]):
    nets = {'1': '+3V3', '2': '+3V3', '39': 'GND', '40': 'GND'}
    for k, p in enumerate(plist):
        nets[str(k + 3)] = f'IO_{p}'
    place('Conn_02x20_Odd_Even', 'J', hx, 305, f'GPIO_{"AB"[hi]}',
          'Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical', C2_PINS, nets)

# ------------------------------------------------------------------ emit
sch = (f'(kicad_sch (version 20230121) (generator eeschema) '
       f'(uuid {q(ROOT)}) (paper "A2") '
       f'(title_block (title "MachXO2-4000HC minimal board") (company "DsSoft") (rev "A")) '
       f'(lib_symbols {" ".join(libs.values())}) '
       f'{" ".join(items)} '
       f'(sheet_instances (path "/" (page "1"))))\n')
open(OUT, 'w').write(sch)

# emit pin map for the constraint file
with open(OUT.rsplit('/', 1)[0] + '/pinmap.json', 'w') as fh:
    json.dump({'fixed': fixed, 'hdrA': hdrA, 'hdrB': hdrB, 'unused': rest,
               'names': {p: io[p][0] for p in io}}, fh, indent=1)
print('ok', len(items), 'items; unused IO:', len(rest))
