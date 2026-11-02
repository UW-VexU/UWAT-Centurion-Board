# centurion: sensor board, rev A

The main custom board for the UWAT VEXU robots. It sits between the V5 brain and the Jetson. It takes power and RS-485 from two V5 smart ports. It reads I2C sensors (encoders and ToF distance sensors) through a mux and has an IMU on SPI. It talks to the Jetson over USB-C or a UART header.

## Status

The schematic is in progress and the PCB is not started. This file records the decisions and the audit findings from 2026-11-01. Nothing in the schematic has been changed by this audit yet.

The component plan is [docs/Board_Components.xlsx](docs/Board_Components.xlsx). Where this file and the plan disagree, this file has the later decision.

## Folder map

| Path | What it is |
|---|---|
| `centurion.kicad_pro` | The KiCad project. Open this. |
| `centurion.kicad_sch` | Top sheet. It links the sheets below. |
| `power.kicad_sch` | Smart port power input, 5 V buck, 3.3 V LDO, USB-C, battery sense |
| `smartport.kicad_sch` | One smart port jack. Used twice, as SmartPort_A and SmartPort_B. |
| `mcu.kicad_sch` | The MCU. Still the ESP32-S3, to be replaced by the STM32F446. |
| `imu.kicad_sch` | ICM-42688-P IMU and the ADXRS453 gyro header |
| `sensors.kicad_sch` | I2C mux, the encoder, ToF and AUX ports, ESD |
| `usb_jetson.kicad_sch` | UART header to the Jetson |
| `lib/` | Project symbols, footprints and 3D models |
| `docs/Board_Components.xlsx` | Component plan and open questions |

The project also uses the UWAT library in `../powerJackal/lib`. Keep the repo folders together.

## Decisions

| Topic | Decision | Notes |
|---|---|---|
| Power | Reuse the powerJackal power section. Leave out its MCU, terminal blocks and current sensors. | Already drawn. See [Power check](#power-check-against-powerjackal). |
| MCU | STM32F446 | It has the DCMI camera interface and more I2C and SPI than the F405. It is the chip on the Nucleo-F446RE used for prototyping. The package waits on the pin plan. |
| Wireless | Allowed | The plan's Q1 answer ("Not allowed") is out of date. |
| I2C mux | One TCA9548A | Spare I2C goes to headers. Removing mux B was intended. |
| Sensor ports | One jack per port. ENC3 gets its jack back. | The connector type is still open. |
| Reverse polarity | None in v1 | Plan Q7 |
| eFuse | None in v1 | Hot-plug inrush is accepted. Plan Q8. |
| Power budget | Measure it on powerJackal | Plan Q2. powerJackal's INA226 monitors read the port current. |

### Board size

The board has to fit its spot on the robot, so its size is limited. The outline and the mounting hole pattern will be measured from the robot CAD. The pattern is still to come and will be added here once it is measured. Until then, the PCB is not started. Check the parts count and the STM32 package against that space before the layout.

### STM32F446 vs F405

| | F446 | F405 |
|---|---|---|
| Camera interface (DCMI) | Yes | No, only the F407 has it |
| I2C | 4 | 3 |
| SPI | 4 | 3 |
| USART and UART | 6 | 6 |
| Speed | 180 MHz | 168 MHz |
| Flash and RAM | 512 KB and 128 KB | 1 MB and 192 KB |

A parallel camera uses about 11 to 14 pins. Add 2 RS-485 ports, 2 I2C buses, the SPI IMU, USB, SWD, LEDs and battery sense, and the 64-pin STM32F446RET6 (about 50 I/O pins) is tight. If the pin plan does not fit, the 100-pin STM32F446VET6 is the same chip with more pins.

## The board as drawn now

94 parts on 7 sheets: 38 resistors, 16 capacitors, 13 connectors, 11 ICs, 10 diodes and LEDs, 2 polyfuses, 2 buttons, 1 MOSFET and 1 solder jumper.

### Power

Copied from powerJackal.

| Ref | Part | Job |
|---|---|---|
| J1, J2 | Molex 0955012441 | Smart port jacks A and B. Power and RS-485 from the V5 brain. |
| D5, D11 | B340A Schottky | Let either port power the board |
| F1 | 2016L150 polyfuse, 1.5 A hold | Input overcurrent |
| D4 | SMBJ16A TVS | Clamps input spikes |
| C1 | 47 µF 50 V electrolytic | Bulk cap. Damps hot-plug ringing. |
| U1 | TPSM53602 | 5 V buck module, 2 A |
| U7 | MCP1826S | 3.3 V LDO, 1 A |
| J16 | USB4105 USB-C | Firmware upload and the Jetson link |
| U13 | USBLC6-2SC6 | USB ESD |
| Q1, D9, D10 | AO3401A and 2 x SS14 | Let USB run the 3.3 V side on the bench |
| R1, R40, C6 | 100k, 27k, 100 nF | Battery voltage sense (VBAT_SENSE) |
| LED1, LED2 | Green LEDs | Input power and 5 V on |

### MCU and motion sensing

| Ref | Part | Job |
|---|---|---|
| U3 | ESP32-S3-WROOM-1-N8 | MCU, with reset and boot buttons and 3 status LEDs. To be replaced by the STM32F446. |
| U5 | ICM-42688-P | 6-axis IMU (gyro and accelerometer) on the board, SPI |
| J5 | 1 x 6 header | Plug-in ADXRS453 gyro module, SPI |

### Sensor ports

| Ref | Part | Job |
|---|---|---|
| U6 | TCA9548A | 8-channel I2C mux |
| J6, J7, J9 to J13 | 4-pin JST-GH | Encoder and ToF ports |
| J14, JP1 | 5-pin JST-GH and a solder jumper | AUX1 port. JP1 picks 3.3 V or 5 V. |
| U8 to U12 | 5 x TPD4E05U06 | ESD on every port |
| F2 | Polyfuse, 0.35 A hold | Feeds the 3.3 V of all the sensor ports |
| R10 to R36 | 4.7k pull-ups and the AUX1 divider | Pull-ups on every mux channel |

### Jetson link

| Ref | Part | Job |
|---|---|---|
| J16 | USB-C | Main link, through the MCU's USB |
| J4 | 1 x 3 header | Backup 3.3 V UART |

### Mux channels

| Channel | Port | Jack |
|---|---|---|
| 0 | ENC1 | J6 |
| 1 | ENC2 | J7 |
| 2 | ENC3 | None. It was removed, see finding 2. |
| 3 to 7 | ToF1 to ToF5 | J9 to J13 |

The ENC ports are for I2C encoders. Magnetic angle sensors like the AS5600 share one fixed address, so they need the mux.

The ports are 4-pin JST-GH: pin 1 is 3.3 V, then SCL, SDA and GND. That is the Pixhawk order. Qwiic uses GND, 3.3 V, SDA, SCL.

AUX1 (J14) is a 5-pin JST-GH with VCC, GND, SDA, SCL and a signal pin. JP1 sets VCC to 3.3 V or 5 V. The signal pin reaches the MCU through a 10k / 15k divider for 5 V signals. R36, a 0 Ω resistor, bypasses the divider for 3.3 V signals. Fit one or the other.

## Sensors

| Sensor | Count | How it connects | Where it sits |
|---|---|---|---|
| ToF distance (plan: VL53L4CX) | 5 | Mux channels 3 to 7 | Off the board, around the robot edges |
| Encoders | 3 | Mux channels 0 to 2. ENC3's jack is missing. | Off the board |
| IMU (ICM-42688-P) | 1 | SPI | On the board |
| Gyro (ADXRS453 module) | 1 | SPI header | Plugs into the board |
| AUX port | 1 | I2C and a signal pin | Off the board, for anything |
| Battery voltage | 1 | Divider to an ADC pin | On the board |

That is 11 sensor connections: 8 through the mux, AUX1, the IMU and the gyro. 10 of them are external cables (the 8 mux ports, AUX1 and the gyro header). With battery sense, the board makes 12 measurements.

- **Not in the plan.** The plan names no encoder part and does not list the ADXRS453. Both came from the schematic.
- **Why the mux.** All 5 ToF sensors share one I2C address. So do I2C encoders like the AS5600.
- **Sensor power.** All the sensor ports share F2's 350 mA. At about 20 mA per ToF and 7 mA per AS5600-type encoder, that leaves plenty of margin.

## Other connections

- **2 smart ports to the V5 brain.** Power works now. RS-485 still needs its transceivers.
- **Jetson.** USB-C, with the UART header as a backup.

## Still to add

| Item | Status |
|---|---|
| STM32F446 with crystal, SWD, BOOT0 and RESET | Decided |
| 2 x RS-485 transceivers (MAX33071E, from stellaNova) | Needed |
| ENC3 jack | Decided |
| Spare I2C header, and AUX1 on the second I2C bus | Decided |
| Camera connector | Open. Which camera, and does it go to the STM32 or the Jetson? |
| LED strip driver | Open. Is it in v1? |
| Test pads and mounting holes | PCB stage. The holes wait on the CAD pattern. |

## Power check against powerJackal

The power and smart port sheets were compared with powerJackal pin by pin. The wiring matches.

- **Copied.** The smart port jack (Molex 0955012441) and B340A diodes, the 2016L150 polyfuse, the SMBJ16A TVS, the 47 µF 50 V electrolytic, the TPSM53602 with its feedback resistors, the MCP1826S, and the USB-C jack with its CC resistors, USBLC6 and USB power switch. The power LEDs came over too. Every part number is the same.
- **Left out on purpose.** The ESP32-C3, the terminal blocks, and the INA226 current sensors with their shunts.
- **Also left out.** The test pads (VPORT, VIN_MOD, 5V, 3V3, GND, PGOOD) and the 4 mounting holes. Bring the test pads back at the PCB stage. The mounting holes follow the robot's pattern instead, see [Board size](#board-size).
- **PGOOD.** On powerJackal the buck's power-good pin has a 10k pull-up and goes to the MCU. Here it goes nowhere.
- **3.3 V bulk.** There is one 47 µF on 3.3 V instead of two. powerJackal had one on each side of its current shunt, and this board has no shunt.
- **USB power.** USB-C can run the 3.3 V side when the smart ports are off. This comes with the powerJackal design. The plan says the board is powered from V5, not VBUS. It is kept for flashing on the bench unless decided otherwise.
- **TVS (plan Q4).** The input matches powerJackal. Its hot-plug simulation keeps VIN_MOD at or under 15.0 V on a smart port, against the TPSM53602's 38 V rating. See [../powerJackal/sim/README.md](../powerJackal/sim/README.md). The SMBJ16A stays off at a full 14.6 V battery.

## Findings

1. **The MCU is wired only to power, its LEDs and its buttons.** The MCU sheet uses local labels where the other sheets use global labels with the same names. Local labels do not cross sheets. So I2C, SPI, the Jetson UART, USB, the mux reset and the AUX signal all dead-end. This is 47 of the 72 ERC items (31 isolated labels and 16 local or global name clashes). It goes away with the STM32 redraw if the new sheet uses global labels.
2. **Commit `6a7e7cc` removed 25 sensor parts.** Its message only mentions the power sheet. Mux B fed AUX1, AUX2, AUX3 and a 2x7 spare I2C header with 5 ports (J17). One mux is now the plan, so most of this was meant to go. Three things were left behind:
   - Mux channel 2 (ENC3) goes to an ESD chip with no jack.
   - AUX1's SDA and SCL now reach only their pull-ups and ESD.
   - The MCU still has a second I2C bus and a mux B reset pin.

   The second I2C bus could run AUX1 and a spare header. That is what "the rest of the I2C to headers" covers.
3. **There is no RS-485 transceiver.** The smart port data lines end at labels, and the MCU has TX, RX and DE pins for each port with nothing to drive. The plan puts a transceiver on the board for each port. stellaNova's MAX33071E fits: 3.3 V, half duplex, ±65 V fault protection. ST3485EB is its cheaper drop-in. The F446's USARTs may not have the hardware driver-enable output that the ESP32 and the STM32G4 have. If not, firmware toggles DE as a GPIO. Check in RM0390 before the pin plan.
4. **VBAT_SENSE does not reach an ADC pin.** A full 14.6 V battery gives about 3.1 V at the divider, inside the STM32's 3.3 V ADC range.
5. **PGOOD is not connected.** See [Power check](#power-check-against-powerjackal).
6. **Two parts have no footprint.** R2, the ESP32 enable pull-up, goes away with the ESP32. JP1, the AUX1 voltage jumper, needs one.
7. **The 3 ERC errors are power flags only.** Two extra power flags sit on the regulator outputs, and the LDO input needs one because it is fed through a diode.
8. **Small items.**
   - The values T0F1 to T0F5 and B00T use a zero instead of the letter O.
   - Most passives have no part number yet.
   - The LED and USB-C symbols differ from their library copies.

## Plan vs schematic

| Block | Plan | Schematic now |
|---|---|---|
| MCU | ESP32-C6 first, STM32 in the later rows | ESP32-S3. To become the STM32F446. |
| RS-485 | One transceiver per port | Missing |
| IMU | LSM6DSL first, ICM-42688-P as a backup | ICM-42688-P and an ADXRS453 header |
| Sensor connectors | Qwiic (JST-SH), a 3.3 / 5 V jumper per channel | JST-GH, one jumper on AUX1 |
| 5 V and 3.3 V | LTM8023 and TLV757P | TPSM53602 and MCP1826S from powerJackal |
| USB-C | One port for upload and the Jetson link, ESD, 5.1k CC | Matches |
| Battery sense | 100k / 27k and 100 nF | Matches, not wired to the MCU |
| ESD | USB and RS-485 lines | USB and sensor ports. No RS-485 yet. |
| LED strip | Connector, buffer, bulk cap, load switch, polyfuse | Not drawn |
| Clock, SWD, BOOT0 | For the STM32 | Comes with the STM32 sheet |

## Open questions

- **Sensor connector.** JST-SH (Qwiic) or JST-GH. JST-SH is the recommendation. The plan picked it, sensor breakouts plug straight in with premade cables, and powerJackal's STEMMA QT jack is already in the UWAT library. A dab of hot glue or a zip tie keeps the cable in. Switching changes the pin order, so the ports get rewired, not just new footprints.

  | | JST-SH (Qwiic, STEMMA QT) | JST-GH |
  |---|---|---|
  | Pin spacing | 1.0 mm | 1.25 mm |
  | Latch | No, friction fit | Yes, it locks |
  | What plugs straight in | Most sensor breakouts (VL53 ToF, LSM6 IMU, AS5600) | Drone gear (Pixhawk). Hobby breakouts need adapter cables. |
  | Pin order | GND, 3.3 V, SDA, SCL | Pixhawk: VCC, SCL, SDA, GND |

- **Board size.** The outline and mounting hole pattern, measured from the robot CAD. See [Board size](#board-size).
- **IMU.** LSM6DSL from the plan or the ICM-42688-P now drawn. Is the ADXRS453 header staying?
- **Camera.** Which camera is it, and does it go to the STM32 or to the Jetson? It decides how many pins the STM32 needs.
- **LED strip.** Is it in v1? How many LEDs? Plan Q14.
- **Still open in the plan.** Q3 (lock the footprints), Q9 (smart port current limit), Q11 (soldering), Q12 (V5 baud rate and packets).

## Fix list

To do once schematic edits start.

1. Redraw the MCU sheet for the STM32F446 with global labels. Include the crystal, SWD header, BOOT0 and RESET buttons, USB on PA11 and PA12, and decoupling. Plan the pins in STM32CubeMX first.
2. Add one RS-485 transceiver per smart port.
3. Wire VBAT_SENSE to an ADC pin and PGOOD to a GPIO with a pull-up.
4. Give ENC3 its jack back. Put AUX1 and a spare I2C header on the second I2C bus.
5. Swap the sensor jacks if JST-SH is chosen.
6. Clean up the power flags and give JP1 a footprint.
7. Add the LED strip circuit if it is in v1.
8. At the PCB stage, draw the outline and mounting holes from the CAD pattern, and add powerJackal's test pads.

## How this was checked

- KiCad 10.0.7 `kicad-cli`: ERC and netlist export.
- After the move from `centurion_sensor_board/` to `centurion/`, the netlist matched Tina's branch: 94 parts and 124 nets.
- The power and smart port sheets were compared with the powerJackal netlist pin by pin, by part number.
- Parts history was traced through the git commits on `sensor-board-schematic`.

## Sources

- [STM32F446RE datasheet, ST](https://st.com/resource/en/datasheet/stm32f446re.pdf)
- [STM32F405xx and STM32F407xx datasheet](https://cdn.sparkfun.com/assets/4/c/b/0/2/stm32f405rg-1851084.pdf)
- [powerJackal hot-plug simulation](../powerJackal/sim/README.md)
