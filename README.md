# UWAT-Centurion-Board

KiCad hardware projects for UWAT VEXU.

| Board | Description |
|---|---|
| centurion | Main custom sensor board. Schematic in progress (power, MCU, IMU, sensors, smart ports, USB to Jetson). It uses footprints and symbols from `powerJackal/lib`. See [centurion/README.md](centurion/README.md) |
| powerJackal | Smart port power test board, rev A. See [powerJackal/README.md](powerJackal/README.md) |
| stellaNova | VEX V5 wireless debugger. An ESP32-S3 bridges one smart port (RS-485) to WiFi and Bluetooth LE. See [stellaNova/README.md](stellaNova/README.md) |
| rambar | Not in the repo yet |

Other folders:

- `tinaOnboarding`: electrical onboarding materials.
- `ul_*`, `0955012401` and similar folders: downloaded part libraries.
