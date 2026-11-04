# UWAT-Centurion-Board

KiCad hardware projects for UWAT VEXU.

| Board | Description |
|---|---|
| centurion | Main custom sensor board. STM32G491 with 2 smart port RS-485 links (MAX33071E), I2C mux sensor ports, an SPI IMU connector, USB-C to the Jetson and a UART + CAN FD link to ramBar. Schematic done, PCB placed and autorouted (2 layers, 103.2 x 62.6 mm, 2 connections left); hand routing next, see [centurion/HAND_ROUTING.md](centurion/HAND_ROUTING.md). It uses footprints and symbols from `powerJackal/lib`. See [centurion/README.md](centurion/README.md) |
| imuBoard | Centurion IMU board, rev 1.0: a Bosch BMI270 on SPI, which plugs into centurion's J5 with a straight JST GH 8-pin cable. 38 x 24 mm, 2 layers, two #8-32 holes 1 in apart. Routed; ERC, DRC and parity clean. See [imuBoard/README.md](imuBoard/README.md) |
| powerJackal | Smart port power test board, rev A. See [powerJackal/README.md](powerJackal/README.md) |
| stellaNova | VEX V5 wireless debugger. An ESP32-S3 bridges one smart port (RS-485) to WiFi and Bluetooth LE. See [stellaNova/README.md](stellaNova/README.md) |
| rambar | Not in the repo yet |

[PCB_DESIGN_GUIDELINES.md](PCB_DESIGN_GUIDELINES.md) has the layout rules, fab limits (PCBWay and JLCPCB) and a pre-order checklist for all of these boards.

`.claude/agents/` has four Claude Code review agents that work on any KiCad project in this repo: `pcb-footprint-checker` (footprints vs datasheets), `pcb-layout-auditor` (measures the routed copper against the guidelines), `pcb-power-thermal` (rail budget, regulator heat, fuses) and `pcb-signal-checker` (I2C, UART, RS-485, CAN, SPI, USB, clocks, logic levels). They only read files. Ask Claude Code to run one on a board folder, for example "run pcb-layout-auditor on centurion".

Other folders:

- `tinaOnboarding`: electrical onboarding materials.
- `ul_*`, `0955012401` and similar folders: downloaded part libraries.
