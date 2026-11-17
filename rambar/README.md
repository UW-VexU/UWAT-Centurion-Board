# ramBar: arc ToF sensor strip, rev A

A flex board for the lift carriage. Up to seven ST VL53L4CD distance sensors sit on an arc and point at the claw drop point. An STM32G491CET6 reads them, works out where the stack center is in the claw frame, subtracts the target, and sends that error to the V5 brain over a smart port (RS-485) and to Centurion over a JST-GH cable (UART and CAN FD). The idea and the math are in the "Arc ToF Rambar" design concept. The power section is Centurion's, copied part for part, as set out in [docs/UWAT_VEXU_Power_Block_Carry_Over.docx](docs/UWAT_VEXU_Power_Block_Carry_Over.docx).

## Status

- Schematic rev A, updated 2026-11-17. The PCB is not started (`rambar.kicad_pcb` is empty).
- The 2026-11-17 update was checked with a script that rebuilds the netlist from the schematic file. KiCad's own ERC has not been run on it yet. Run it before starting the layout.
- Every BOM part has a manufacturer part number. DigiKey Canada stock was not checked on 2026-11-17.

## Board at a glance

| | |
|---|---|
| Type | Flex PCB, with stiffeners under the connectors, the power block, the MCU and each sensor |
| Sensors | 7 x VL53L4CD (S1 to S7). Fit 5 or 7, see [Sensors](#sensors) |
| MCU | STM32G491CET6, LQFP-48. Same G491 family as Centurion |
| Inputs | J1 smart port (11 to 14.6 V), J2 link from Centurion (5 V), J16 USB-C (5 V, for flashing) |
| Links | RS-485 to the brain (J1), UART and CAN FD to Centurion (J2), USB to a laptop (J16) |
| Rails | +5V from the buck (smart port power only), +3.3V from the LDO (every source). Every load runs from +3.3V |

## Decisions

| Topic | Decision | Why |
|---|---|---|
| Power | Centurion's power block with the same parts, values and footprints, plus D13 and the J19 sense divider for the Centurion link | The Carry-Over note. The circuit was tested on powerJackal |
| Sensor count | 7 slots | The concept baseline is 5. Its simulation shows 7 cuts the error from 2.7 to 2.3 mm RMS. Fit what the arc layout uses |
| I2C mux | None | Each VL53L4CD takes a new address in software. One XSHUT line per sensor lets firmware wake them one at a time and give each its own address. A mux only helps with fixed-address chips (Centurion's encoders) or when GPIOs run out. Here it would add a part, a channel-select write before every read, and flex area |
| I2C buses | Odd sensors on I2C1, even sensors on I2C2 | Neighbours sit on different buses, so the two firing groups read in parallel |
| XSHUT | 10k pull-down on every sensor | Every sensor waits in standby through reset, flashing and boot until firmware wakes it. It also keeps XSHUT3 clean on PB6, where the G4's USB-C dead-battery pull-down sits |
| GPIO1 | Its own interrupt pin per sensor, 10k pull-up | Seven separate EXTI lines (0, 1, 2, 4, 13, 14, 15) |
| SWO | Not used | PB3 is XSHUT5 and all 38 I/O pins are in use. SWD debugging still works, and printf can go over USB |
| Centurion link | The mirror of Centurion's ramBar link: TCAN334G, NUP2105L, TPD4E05U06, 120 Ω terminator, 10k RX pull-up, 470 Ω TX resistor | Each end of the cable protects and terminates itself |

## Sensors

| Sensor | Ref | Bus | XSHUT | GPIO1 | Caps | XSHUT pull-down, GPIO1 pull-up |
|---|---|---|---|---|---|---|
| S1 | U2 | I2C1 | PB1 | PA0 | C11, C12 | R4, R5 |
| S2 | U3 | I2C2 | PB5 | PA1 | C13, C14 | R10, R11 |
| S3 | U4 | I2C1 | PB6 | PB2 | C45, C47 | R12, R14 |
| S4 | U5 | I2C2 | PB9 | PB4 | C46, C48 | R13, R15 |
| S5 | U6 | I2C1 | PB3 | PC13 | C19, C20 | R16, R71 |
| S6 | U8 | I2C2 | PA4 | PC14 | C53, C54 | R72, R73 |
| S7 | U9 | I2C1 | PA5 | PC15 | C55, C56 | R74, R75 |

- Number S1 to S7 along the arc, left to right. Then neighbours always sit on different buses.
- With 7 fitted, the 150° arc puts them 25° apart. For 5 on the same layout, fit S1, S2, S4, S6 and S7 (-75°, -50°, 0°, +50°, +75°) and leave S3 and S5 off. The other option is a layout with 5 positions 37.5° apart, as in the concept. This is still open.
- Each sensor has 100 nF and 4.7 µF at its supply pins, as the datasheet shows.
- I2C pull-ups are 3.3k (R6 to R9), one pair per bus.
- Current: 24 mA average and 40 mA peak per sensor while ranging. Firing in two groups keeps at most four at peak (160 mA). On J19 power the board stays near 310 mA, under Centurion's 0.5 A F4.

## MCU pin map

STM32G491CET6, LQFP-48. Checked against ST's pin data (STM32_open_pin_data, `STM32G491C(C-E)Tx.xml`).

| Function | Pin | Peripheral |
|---|---|---|
| Sensor XSHUT, S1 to S7 | PB1, PB5, PB6, PB9, PB3, PA4, PA5 | GPIO out |
| Sensor GPIO1, S1 to S7 | PA0, PA1, PB2, PB4, PC13, PC14, PC15 | EXTI 0, 1, 2, 4, 13, 14, 15 |
| I2C1 (S1, S3, S5, S7): SCL, SDA | PA15, PB7 | I2C1 |
| I2C2 (S2, S4, S6): SDA, SCL | PA8, PA9 | I2C2 |
| Smart port RS-485: TX, RX, DE | PB10, PB11, PB14 | USART3, hardware DE |
| Centurion UART: TX, RX | PA2, PA3 | USART2 |
| Centurion CAN FD: RX, TX | PB12, PB13 | FDCAN2 |
| USB D-, D+ | PA11, PA12 | USB FS device |
| Battery voltage (VIN_MOD) | PA6 | ADC2_IN3 |
| VBUS sense (USB plugged in) | PA7 | GPIO in |
| J19 sense (Centurion's 5 V present) | PB0 | GPIO in |
| PGOOD (5 V good, high = good) | PA10 | GPIO in |
| Status LED D21 (high = on) | PB15 | GPIO out |
| SWD: SWDIO, SWCLK | PA13, PA14 | |
| NRST, BOOT0 | PG10, PB8 | |
| 8 MHz crystal | PF0, PF1 | HSE |

## Firmware notes

- Call `HAL_PWREx_DisableUCPDDeadBattery()` first thing. PA9 (I2C2_SCL) and PA10 (PGOOD) sit high at power-up, which turns on 5.1k pull-downs on PB6 (XSHUT3) and PB4 (TOF_INT4) until this runs.
- Sensor start-up: every XSHUT starts low because of its pull-down. Raise one, wait for that sensor to boot, give it its new address, then move to the next.
- Fire the odd sensors, then the even ones, so light from one sensor doesn't land in its neighbour.
- PC13, PC14 and PC15 carry interrupts only. They are weak pins and must not source current.
- Poll J19_SENSE (PB0). It shares EXTI line 0 with TOF_INT1 on PA0.
- Flash over USB (hold BOOT, tap RESET, let go of BOOT) with the Centurion cable unplugged. The ROM bootloader also listens on USART2, and PA3 is the Centurion UART.
- Don't drive UART TX toward Centurion until J19_SENSE shows its 5 V, so RamBar doesn't feed Centurion's 3.3 V through the pin. Centurion follows the same rule.
- Tell VBAT_SENSE, VBUS_SENSE and J19_SENSE apart to know the power source. PGOOD may read high on USB or J19 power. VIN_MOD = ADC voltage x 5.545.

## Flex layout notes

- J1, J16, J2, the power block, the MCU, the buttons and each sensor need FR4 stiffeners. C1, J1, J3 and J16's shell legs are through-hole, so their stiffener goes on the component side.
- Keep the 1210 and 1206 ceramics (C2, C3, C16, C32, C4, C5, C17) off bend lines, with their long side parallel to the bend.
- U7 can burn about 0.5 W. Give its tab the biggest copper pour the stiffened area allows, and measure it at bring-up.
- Ask the fab whether they can plug U1's thermal vias.
- Keep each sensor's 25° exclusion cone clear of stiffener edges, other parts and the robot.
- Plug in the Centurion cable only while Centurion is off (Carry-Over note).
- VL53L4CD assembly: dry (convection) reflow and no washing. Peel the liner off after soldering.

## Folder map

| Path | What it is |
|---|---|
| `rambar.kicad_pro`, `.kicad_sch`, `.kicad_pcb` | The KiCad 10 project. One flat sheet |
| `fp-lib-table`, `sym-lib-table` | Load UWAT from `../powerJackal/lib`, centurion from `../centurion/lib`, and the MCU symbol from `rambar.kicad_sym`. Keep the repo folders together |
| `bom/Rambar_Parts_List.xlsx` | Parts list. The Schematic BOM tab is generated from the schematic and has every part number |
| `docs/UWAT_VEXU_Power_Block_Carry_Over.docx` | Which power parts come from Centurion and how the three power inputs work |
| `datasheets/` | VL53L4CD datasheet and ULD driver guide |
| `KiCADv6/`, `lib/`, `zips/`, `LQFP_491CET6_STM.step` | Vendor downloads for the MCU. The schematic uses KiCad's own LQFP-48 footprint instead |

## Open questions

- 5 or 7 sensor positions on the arc (see [Sensors](#sensors)).
- Mounting holes and the stiffener outline, from the carriage CAD.
- The concept's checkpoint: bench test that the sensors see clear Cups before ordering this board.
- VUR12: ask the Q&A about custom boards, as the concept plans.
