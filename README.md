# MACHXO2-MINI

Minimal FPGA board built around a Lattice MachXO2-4000HC (TQFP-144), designed by DsSoft.

## Specs
- **FPGA:** LCMXO2-4000HC-4TG144C, with 4320 LUTs and on-chip configuration flash
- **Power:** USB-C (power only) feeds an AP2112K-3.3 regulator. Everything runs from a single 3.3 V rail.
- **Clock:** 12 MHz oscillator on pin 128 (PCLKT0_1)
- **I/O:** 4 LEDs, 1 user button, a UART header, and 72 GPIO on two 2×20 headers
- **PCB:** 4 layers (signal / GND / 3V3 / signal)

## Pinout
| Signal | FPGA pin |
|---|---|
| CLK12 | 128 |
| LED0–3 | 97, 98, 99, 100 |
| BTN0 (active-low, enable the internal pull-up) | 96 |
| UART TX / RX | 111 / 112 |

The GPIO header mapping is listed in `rtl/blinky.lpf`. Header pins 1–2 are 3V3 and pins 39–40 are GND.

**J2 JTAG:** 1 = VREF, 2 = TCK, 3 = TDI, 4 = TDO, 5 = TMS, 6 = GND
**J3 UART:** 1 = TX, 2 = RX, 3 = GND

## Programming
Wire any FT2232H board to J2, then:
```
openFPGALoader --detect
openFPGALoader -c ft2232 -f blinky.jed   # write to internal flash
```
Build bitstreams in Lattice Diamond, starting from `rtl/blinky.v` and `rtl/blinky.lpf`.

## Bring-up
1. Inspect the TQFP pins for solder bridges (ideally assemble with JLC, BOM Coming)
2. Measure 3V3 to GND. It must not read as a short.
3. Plug in USB. The PWR LED should light and C17 should read 3.3 V.
4. Run `openFPGALoader --detect` and check that the FPGA is found.
5. Flash the blinky.

## Key parts
| Ref | Part | LCSC |
|---|---|---|
| U1 | LCMXO2-4000HC-4TG144C | C1521625 |
| U2 | AP2112K-3.3TRG1 (Diodes) | C51118 |
| X1 | ASE-12.000MHZ-LC-T (Abracon) | C596950 |
| J1 | HRO TYPE-C-31-M-12 | — |

## Files
- `machxo2-mini.kicad_sch`: the schematic
- `rtl/`: blinky design and its constraints file
- `gen_schematic.py`: the script that generates the schematic
