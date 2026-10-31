# powerJackal firmware specification

What the firmware on the powerJackal board has to do, and everything the hardware gives it to work with. Read this before writing code. The hardware itself is described in [design_notes.md](design_notes.md).

The board is labelled "Smart Port Power Converter - Rev 1-1" on the back. In the repo it is rev A.

## What the firmware is for

The board turns VEX smart port (or bench) power into 5 V and 3.3 V. Three INA226 monitors measure the input, the 5 V rail and the 3.3 V rail. The firmware runs on the ESP32-C3 and has four jobs.

1. Read the three monitors and turn the raw registers into volts, amps and watts.
2. Work out what is powering the board and whether every rail is healthy.
3. Report the numbers over USB serial, for a person and for a logging script.
4. Warn when a limit is crossed, on the serial port and with the status LED.

The radio is not used. No antenna is fitted.

## Hardware the firmware can use

### Pins

| GPIO | Net | Direction | Meaning |
|---|---|---|---|
| 4 | SDA | I2C | Shared I2C bus. 4.7 kΩ pull-up (R5) to 3.3 V |
| 5 | SCL | I2C | Shared I2C bus. 4.7 kΩ pull-up (R6) to 3.3 V |
| 3 | PGOOD | Input | High = 5 V output in regulation. Open drain from U1, 10 kΩ pull-up (R7) |
| 10 | LED_STAT | Output | High = status LED3 on, about 1.3 mA through R20 |
| 9 | BOOT | Input | Low = BOOT button (SW2) pressed. 10 kΩ pull-up (R23). Strapping pin |
| 18, 19 | USB D-, D+ | USB | Built-in USB serial and JTAG. Never use these as GPIO |
| 2, 8 | IO2, IO8 | Strap | Only pull-ups (R21, R22). Leave them as inputs |
| EN | EN | Reset | RESET button (SW1). Not a GPIO |

GPIO0, 1, 6, 7, 20 and 21 are not connected to anything on the board. They cannot be used without rework. UART0 (GPIO20 and 21) has no header, so USB is the only console.

### I2C devices

| Address | Part | Notes |
|---|---|---|
| 0x40 | U2, INA226 | Input monitor. A1 and A0 to GND |
| 0x41 | U3, INA226 | 5 V rail monitor. A1 to GND, A0 to VS |
| 0x45 | U5, INA226 | 3.3 V rail monitor. A1 and A0 to VS |
| any | Device on J3 | Optional STEMMA QT / Qwiic device, for example an OLED (usually 0x3C or 0x3D) |

The bus runs at 400 kHz. Use 100 kHz if a long cable is plugged into J3. The INA226 ALERT pins are not connected, so the firmware must poll.

### Not available to the firmware

- **Port or bench:** D5 and D3 OR the two inputs, so the firmware cannot tell which one is supplying power.
- **USB current:** the USB power path (D4 and Q1) has no monitor.
- **Smart port data:** the RS-485 lines go only to test pads TP8 and TP9, not to the ESP32.
- **Clock time:** there is no real-time clock. Timestamps are milliseconds since boot.

## What each monitor measures

| Monitor | Shunt | Bus voltage pin reads | Current through the shunt is | Full scale |
|---|---|---|---|---|
| U2 "IN" (0x40) | R1, 20 mΩ | VIN_MOD: the input after the OR diode, the fuse F1 and the shunt | Everything the 5 V module takes from the port or bench. This is the whole board on external power, except LED1 (about 1 mA, before F1) | 4.096 A |
| U3 "5V" (0x41) | R2, 20 mΩ | The 5 V rail at J6 | The J6 load, plus LED2 (1.4 mA), plus the 3.3 V side when it runs from the 5 V rail | 4.096 A |
| U5 "3V3" (0x45) | R12, 50 mΩ | The 3.3 V rail | The ESP32, the three INA226s, LED3, the I2C pull-ups, anything on J3, and the J9 load | 1.638 A |

Points that matter when reading the numbers:

- **The input voltage reads low.** U2's bus pin sits after the OR diode and F1. The real port or bench voltage is about 0.3 to 0.6 V higher, rising with current.
- **U3 includes the 3.3 V side.** On external power the LDO is fed from the 5 V rail through D2, so the LDO's input current shows up on U3. The J6 load alone is about `I_5V - I_3V3 - 1.6 mA`.
- **U5 includes the board itself.** The J9 load alone is `I_3V3` minus the board's own draw. A tare command handles this (see Features).
- **On USB power, nothing measures USB.** U5 still shows the 3.3 V side, which is then the whole USB load.

## INA226 setup

### Registers

| Reg | Name | Access | Use |
|---|---|---|---|
| 0x00 | Configuration | R/W | Averaging, conversion times, mode. Bit 15 = reset |
| 0x01 | Shunt voltage | R | Signed, 2.5 µV per bit, ±81.92 mV full scale |
| 0x02 | Bus voltage | R | Unsigned, 1.25 mV per bit |
| 0x03 | Power | R | Unsigned, 25 x current LSB per bit |
| 0x04 | Current | R | Signed, current LSB per bit. Valid only after CAL is written |
| 0x05 | Calibration | R/W | CAL value below |
| 0x06 | Mask/Enable | R/W | Bit 3 CVRF = new conversion ready. Bit 2 OVF = math overflow |
| 0x07 | Alert limit | R/W | Not useful here, ALERT is not wired |
| 0xFE | Manufacturer ID | R | Reads 0x5449 ("TI") |
| 0xFF | Die ID | R | Reads 0x2260 |

All registers are 16 bits, most significant byte first.

### Calibration

CAL = 0.00512 / (current LSB x shunt resistance). All three monitors use CAL = 2048 (0x0800).

| Monitor | Shunt | Current LSB | Power LSB | CAL |
|---|---|---|---|---|
| U2 | 0.020 Ω | 125 µA | 3.125 mW | 2048 |
| U3 | 0.020 Ω | 125 µA | 3.125 mW | 2048 |
| U5 | 0.050 Ω | 50 µA | 1.25 mW | 2048 |

CAL resets to 0 whenever an INA226 resets or loses power. Read register 0x05 back now and then, and rewrite it if it is not 2048.

### Configuration value

Configuration = 0x4000 | AVG << 9 | VBUSCT << 6 | VSHCT << 3 | MODE. Bit 14 always reads 1.

| Setting | Value | Code |
|---|---|---|
| Averaging (AVG) | 16 samples | 010 |
| Bus conversion time (VBUSCT) | 1.1 ms | 100 |
| Shunt conversion time (VSHCT) | 1.1 ms | 100 |
| Mode | Shunt and bus, continuous | 111 |

That gives **0x4527**. Each monitor then produces a fresh result every 16 x (1.1 + 1.1) ms = 35.2 ms, about 28 per second.

Other useful averaging codes: 000 = 1, 001 = 4, 011 = 64, 100 = 128. For catching fast events such as hot-plug inrush, use AVG 1 with 140 µs conversions (codes 000), which gives a result about every 0.28 ms.

### Conversions to real units

```
bus volts    = bus register x 0.00125
shunt volts  = signed shunt register x 0.0000025
amps         = signed current register x current LSB
watts        = power register x 25 x current LSB
```

Amps can also be computed as shunt volts / shunt resistance. Doing both is a good self-check during bring-up.

### Example code (Arduino)

A minimal register layer. It is a starting point, not finished firmware.

```cpp
#include <Arduino.h>
#include <Wire.h>

constexpr int PIN_SDA = 4;
constexpr int PIN_SCL = 5;
constexpr int PIN_PGOOD = 3;   // high = 5 V in regulation
constexpr int PIN_LED = 10;    // high = LED on
constexpr int PIN_BOOT = 9;    // low = BOOT pressed, read only after boot

struct Monitor { const char *name; uint8_t addr; float currentLsb; uint16_t cal; };
Monitor MON[] = {
  {"IN",  0x40, 125e-6f, 2048},
  {"5V",  0x41, 125e-6f, 2048},
  {"3V3", 0x45,  50e-6f, 2048},
};
constexpr uint16_t INA_CONFIG = 0x4527;   // AVG 16, 1.1 ms bus and shunt, continuous

bool inaWrite(uint8_t addr, uint8_t reg, uint16_t value) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(value >> 8);
  Wire.write(value & 0xFF);
  return Wire.endTransmission() == 0;
}

bool inaRead(uint8_t addr, uint8_t reg, uint16_t &value) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(addr, (uint8_t)2) != 2) return false;
  value = (uint16_t)Wire.read() << 8;
  value |= Wire.read();
  return true;
}

bool inaInit(const Monitor &m) {
  uint16_t id;
  if (!inaRead(m.addr, 0xFE, id) || id != 0x5449) return false;
  if (!inaRead(m.addr, 0xFF, id) || id != 0x2260) return false;
  inaWrite(m.addr, 0x00, 0x8000);   // reset, this also clears CAL
  delay(1);
  return inaWrite(m.addr, 0x00, INA_CONFIG) && inaWrite(m.addr, 0x05, m.cal);
}

struct Reading { float volts, shuntVolts, amps, watts; bool ok; };

Reading inaSample(const Monitor &m) {
  Reading r{};
  uint16_t bus, shunt, cur, pwr;
  r.ok = inaRead(m.addr, 0x02, bus) && inaRead(m.addr, 0x01, shunt) &&
         inaRead(m.addr, 0x04, cur) && inaRead(m.addr, 0x03, pwr);
  r.volts = bus * 1.25e-3f;
  r.shuntVolts = (int16_t)shunt * 2.5e-6f;
  r.amps = (int16_t)cur * m.currentLsb;
  r.watts = pwr * 25.0f * m.currentLsb;
  return r;
}

void setup() {
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);   // do not stall when no USB host is listening
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_PGOOD, INPUT);
  pinMode(PIN_BOOT, INPUT_PULLUP);
  Wire.begin(PIN_SDA, PIN_SCL, 400000);
  for (auto &m : MON) Serial.printf("%s 0x%02X %s\n", m.name, m.addr, inaInit(m) ? "ok" : "MISSING");
}
```

## Power states

The firmware decides the power state from U2's bus voltage first. PGOOD only means something when the 5 V module has real input.

| State | How to detect it | What is true |
|---|---|---|
| USB only | U2 bus below 3 V and U5 bus about 3.3 V | Q1 feeds the 3.3 V side from USB. The 5 V rail is off. J6 has no output |
| External power | U2 bus above 6 V | The 5 V module runs. USB carries data only. All three monitors are meaningful |
| Input too low | U2 bus from 3 to 6 V | The module needs at least 6 V in to hold 5 V. The 5 V rail may sag |
| 5 V fault | External power and PGOOD low | The 5 V output is below 92 % (4.6 V) or above 107 % (5.35 V) of target |

Handover from USB to external power should not reset the ESP32. It is worth testing.

- **Log the reset reason at boot** with `esp_reset_reason()`. A brownout reset after plugging in power means the handover failed.
- **A short on J6 can reset the board.** The 5 V module goes into hiccup mode at about 3.5 A. That takes the 3.3 V side down with it, unless USB is plugged in to take over.

## Values to expect

These are design estimates. Confirm them on the first board and update this table.

| Situation | IN (U2) | 5V (U3) | 3V3 (U5) | PGOOD |
|---|---|---|---|---|
| USB only, nothing on J6 or J9 | About 0 V, about 0 A | Under 0.5 V, about 0 A | 3.25 to 3.35 V, 20 to 40 mA | Probably 1. Ignore it |
| Bench 12 V, no loads | 11.4 to 11.8 V, 15 to 35 mA | 4.9 to 5.1 V, 25 to 45 mA | 3.25 to 3.35 V, 20 to 40 mA | 1 |
| Plus LOAD1 (10 Ω) on J6 | About 0.25 A | About 0.53 A | No change | 1 |
| Plus LOAD2 (two 10 Ω) on J6 instead | About 0.49 A | About 1.03 A | No change | 1 |
| Plus LOAD3 (22 Ω) on J9 | Plus about 0.07 A | Plus 0.15 A | Plus 0.15 A | 1 |
| Full 2 A on J6 at 12 V in | About 0.96 A, about 11 W | About 2.03 A | No change | 1 |
| Smart port, V5 battery | Battery voltage (11 to 14.4 V) minus 0.3 to 0.6 V | As bench | As bench | 1 |

Background numbers behind the table:

- **5 V rail:** 5.02 V nominal. Worst case 4.88 to 5.13 V with the 1 % feedback resistors. U3 reads R2's drop lower, 40 mV at 2 A.
- **3.3 V rail:** MCP1826, ±0.5 % typical and ±2.5 % worst case. U5 reads R12's drop lower, 7.5 mV at 150 mA.
- **ESP32-C3 draw:** about 20 to 35 mA with the radio off.
- **INA226 draw:** about 0.33 mA each.
- **LEDs:** LED2 draws 1.4 mA from the 5 V rail and LED3 1.3 mA from the 3.3 V rail when on.
- **5 V stage efficiency:** TI lists 91 % at 2 A. Expect about 85 to 92 % from 0.5 to 2 A, and much less at light load.

## Derived values

| Value | Formula | Notes |
|---|---|---|
| 5 V stage efficiency | 100 x P_5V / P_IN | Show it only on external power with I_5V above about 0.2 A. It includes R2 and wiring losses |
| J6 load current | I_5V - I_3V3 - 1.6 mA | External power only. The 1.6 mA is LED2 plus the LDO's own draw |
| J9 load current | I_3V3 - tare value | Tare with nothing plugged into J9 or J3 |
| Port power, estimated | (V_IN + 0.4 V) x I_IN | Adds back the OR diode drop. Rough |
| Energy | Sum of P x dt per rail | Report Wh. Reset with the reset command or the BOOT button |
| Charge | Sum of I x dt per rail | Report mAh |
| Min, max, average | Per rail, since the last reset | Volts, amps and watts |

Use `micros()` for dt, since sample times drift.

## Limits and warnings

Suggested starting values. Keep them as named constants so they are easy to tune after bring-up.

| Check | Warn when | Why |
|---|---|---|
| Input voltage high | U2 bus above 15.5 V | Above the bench range. TVS diode D1 starts to conduct near 17.8 V |
| Input voltage low | U2 bus from 6 to 10.5 V | Below the battery range |
| Input below regulation | U2 bus from 3 to 6 V | The 5 V rail is not guaranteed |
| Input current | U2 above 1.4 A | Fuse F1 holds 1.5 A at room temperature, less when warm |
| Port power | U2 power above 18 W. Alarm above 20 W | VEX guidance is 20 W or less of added load on a smart port |
| 5 V voltage | Outside 4.85 to 5.15 V, external power only | Normal tolerance plus the shunt drop |
| 5 V current | U3 above 1.9 A | The module is rated 2 A, including the board's own draw |
| 3.3 V voltage | Outside 3.20 to 3.40 V | MCP1826 worst case tolerance |
| 3.3 V current | U5 above 0.5 A | U6 heats up. At 0.5 A it dissipates about 0.65 W |
| PGOOD | Low while U2 bus is above 6 V | 5 V output out of regulation |
| Over range | Shunt register at +32767 or -32768 | The reading is clipped at full scale |
| Sensor missing | No answer at 0x40, 0x41 or 0x45, or a wrong ID | Board fault or bad solder joint |

Report warnings as a list of names, for example `IN_POWER_HIGH, V5_LOW`.

## Features to code

### Must have (first version)

1. **USB serial console** at 115200 baud. On boot print a banner: firmware version, board name, reset reason and ESP32 chip temperature (`temperatureRead()`).
2. **I2C start-up.** Scan the bus and list every address found. Check the IDs of the three INA226s, then write the configuration and CAL.
3. **Measurement loop.** Read all three monitors at least 10 times per second, or each time CVRF says a new result is ready.
4. **Power state detection** as described above, including the PGOOD rules.
5. **Limit checks** from the table above, shown on serial and on the LED.
6. **Two output modes:** a readable dashboard line and CSV for logging (formats below).

### Should have

7. Min, max and average per rail. Energy (Wh) and charge (mAh) per rail since reset.
8. 5 V stage efficiency, J6 and J9 load estimates, and a tare command.
9. BOOT button actions (below).
10. Serial commands (below).
11. **I2C error handling.** Retry a failed read once and mark a monitor offline after repeated failures. If SDA is stuck low, clock SCL nine times to free the bus.
12. **Watchdog.** If a reading takes too long, it should recover the I2C bus or reset, not hang.

### Could have (later)

13. An OLED status screen on J3 (below).
14. JSON lines output for a PC logging or plotting script.
15. **Fast capture mode** for hot-plug and inrush. Switch to AVG 1 with 140 µs conversions, wait for U2 current to cross a trigger level, record a few hundred samples, then print them.
16. Save settings (output mode, rate, limits) in flash with the `Preferences` library.
17. **Wi-Fi telemetry**, but only if a U.FL antenna is fitted. Never run the radio without an antenna.

## Serial interface

### Output modes

Dashboard (default), one line every 500 ms:

```
EXT  IN 11.72 V 0.252 A 2.95 W | 5V 5.01 V 0.534 A 2.68 W | 3V3 3.30 V 0.031 A 0.10 W | eff 91% | PGOOD 1 | OK
```

CSV, one header line then one row per sample:

```
t_ms,source,in_v,in_a,in_w,v5_v,v5_a,v5_w,v33_v,v33_a,v33_w,eff_pct,pgood,warnings
12345,EXT,11.72,0.252,2.95,5.01,0.534,2.68,3.30,0.031,0.10,91,1,
```

Use a dot as the decimal point and no thousands separators. Leave the warnings column empty when there are none, and separate several warnings with spaces.

### Commands

One command per line, not case sensitive. Answer each with a short confirmation.

| Command | Action |
|---|---|
| `help` | List the commands |
| `mode dash`, `mode csv`, `mode json` | Choose the output format |
| `rate <ms>` | Print interval, for example `rate 100` |
| `avg <n>` | INA226 averaging: 1, 4, 16, 64, 128, 256, 512 or 1024 |
| `stats` | Print min, max, average, energy and charge per rail |
| `reset` | Clear min, max, average, energy and charge |
| `tare` | Store the current I_3V3 as the board's own draw |
| `scan` | Scan the I2C bus and list addresses |
| `info` | Banner again: version, uptime, reset reason, chip temperature, sensor status |
| `led on`, `led off`, `led auto` | Override the status LED |

## Status LED and BOOT button

### LED3 (GPIO10)

| Pattern | Meaning |
|---|---|
| Slow blink, 1 s period | USB power only |
| On | External power, no warnings |
| Fast blink, 5 times a second | At least one warning |
| Two short flashes every 2 s | Fault: a monitor is missing, or PGOOD is low with input present |

### BOOT button (GPIO9)

After boot, GPIO9 works as a normal input. It reads low while the button is pressed.

- **Short press:** reset the stats, energy and charge.
- **Hold for 2 s:** step to the next output mode.

Holding BOOT while pressing RESET, or at power-up, starts the ROM download mode instead of the firmware. That is the recovery path, so do not reuse the button for anything that needs holding at start-up.

## Optional OLED on J3

J3 is a STEMMA QT / Qwiic port with 3.3 V, GND, SDA and SCL, on the same bus as the INA226s.

- **Driver:** most small OLEDs use an SSD1306 or SH1106 at 0x3C or 0x3D. Use the bus scan to find the address, then a library such as Adafruit_SSD1306 or U8g2.
- **Suggested pages:** one line per rail (volts, amps, watts), then a stats page and an efficiency page. Step pages with a BOOT short press if the stats reset moves elsewhere.
- **Refresh rate:** update the screen about 5 times a second, so it does not slow down the measurements.
- **It counts as load.** A typical OLED draws 10 to 20 mA from the 3.3 V rail, which shows up on U5. Tare again with it plugged in.

## Accuracy

- **Shunts:** ±1 %.
- **INA226 gain error:** 0.1 % worst case.
- **INA226 shunt offset:** 2.5 µV typical, 10 µV worst case. That is about 0.5 mA on U2 and U3 and 0.2 mA on U5.
- **Bus voltage:** about 0.1 % plus a few millivolts.
- **Overall:** expect currents within about 1 % plus 0.5 mA, and voltages within about 0.2 %.
- **Better accuracy:** for better than this, compare against a good multimeter and store a gain correction per monitor.

Readings below a few milliamps are mostly offset and noise. Show them as near zero, not as exact values.

## Toolchain

### Arduino IDE

- Install the "esp32 by Espressif Systems" package in Boards Manager.
- **Board:** ESP32C3 Dev Module.
- **USB CDC On Boot:** Enabled. Without it, `Serial` does not go to USB.
- **Flash size:** 4MB.
- **JTAG adapter:** Integrated USB JTAG, if you want to debug.
- Pick the board's COM port and upload. No buttons are needed.

### PlatformIO

```ini
[env:powerjackal]
platform = espressif32
board = esp32-c3-devkitm-1
framework = arduino
monitor_speed = 115200
build_flags =
  -DARDUINO_USB_MODE=1
  -DARDUINO_USB_CDC_ON_BOOT=1
```

Keep the firmware in `powerJackal/firmware/` so it lives next to the hardware it belongs to.

### Things to keep in mind

- **Do not touch GPIO18 and GPIO19.** Reconfiguring them breaks USB until you use the BOOT recovery.
- **Do not burn eFuses.** Secure boot and disabling USB JTAG are permanent.
- **Keep Wi-Fi and Bluetooth off** unless an antenna is fitted.
- **No USB host:** on smart port power with no laptop attached, serial output just goes nowhere. `setTxTimeoutMs(0)` keeps the loop from stalling.

## Bring-up test for the firmware

Run these in order on the first assembled board. The hardware side of each step is in the bring-up section of [design_notes.md](design_notes.md#bring-up-and-test).

1. **USB only.**
   - The banner prints, and the scan finds 0x40, 0x41 and 0x45.
   - U5 reads about 3.3 V and 20 to 40 mA. U2 and U3 read about 0.
   - The LED blinks slowly.
2. **Bench at 12 V with a 0.3 A limit.**
   - The state changes to external power without a reset. Check the reset reason with `info`.
   - U3 reads about 5.0 V. PGOOD is 1. The LED stays on.
3. **LOAD1, then LOAD2, on J6.**
   - U3 rises by about 0.5 A, then about 1 A.
   - Efficiency shows 85 to 92 %. Check against a multimeter on J6.
4. **LOAD3 on J9.**
   - U5 rises by about 0.15 A.
   - Run `tare` first, then confirm the J9 load estimate reads about 150 mA.
5. **Limits.** Raise the bench voltage past 15.5 V for a moment, or lower it under 10.5 V, and confirm the warnings and the fast blink.
6. **Logging.** Switch to CSV, log a few minutes into a file, and plot it.
