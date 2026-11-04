
### i2c

| Case | Result | rise_sensor_ns | rise_mcu_ns | sink_mA | vol_mcu_V | high_mcu_V | undershoot_V |
|---|---|---|---|---|---|---|---|
| mux jack 3.3 V, 0.3 m, no breakout pull-ups | ok | 87.0 | 104.0 | 1.79 | 0.24 | 3.3 | -0.42 |
| mux jack 3.3 V, 0.3 m, breakout 10k pull-ups | ok | 72.0 | 97.0 | 2.07 | 0.28 | 3.3 | -0.38 |
| mux jack 3.3 V, 0.3 m, Qwiic 2.2k pull-ups | **FAIL** | 45.0 | 82.0 | 3.02 | 0.4 | 3.3 | -0.27 |
| mux jack 3.3 V, 1.0 m, no breakout pull-ups | ok, sensor clamp conducts briefly | 147.0 | 127.0 | 1.79 | 0.24 | 3.3 | -0.78 |
| mux jack 3.3 V, 1.0 m, breakout 10k pull-ups | ok, sensor clamp conducts briefly | 119.0 | 119.0 | 2.07 | 0.28 | 3.3 | -0.78 |
| mux jack 3.3 V, 1.0 m, Qwiic 2.2k pull-ups | **FAIL** | 73.0 | 97.0 | 3.02 | 0.4 | 3.3 | -0.76 |
| mux jack 3.3 V, 2.0 m, no breakout pull-ups | ok, sensor clamp conducts briefly | 232.0 | 167.0 | 1.79 | 0.24 | 3.3 | -0.79 |
| mux jack 3.3 V, 2.0 m, breakout 10k pull-ups | ok, sensor clamp conducts briefly | 183.0 | 150.0 | 2.07 | 0.28 | 3.3 | -0.79 |
| mux jack 3.3 V, 2.0 m, Qwiic 2.2k pull-ups | **FAIL** | 116.0 | 118.0 | 3.01 | 0.4 | 3.3 | -0.78 |
| mux jack 5.0 V, 0.3 m, no breakout pull-ups | ok | 84.0 | 86.0 | 2.37 | 0.32 | 3.3 | -0.08 |
| mux jack 5.0 V, 0.3 m, breakout 10k pull-ups | ok | 67.0 | 81.0 | 2.8 | 0.37 | 3.3 | -0.06 |
| mux jack 5.0 V, 0.3 m, Qwiic 2.2k pull-ups | **FAIL** | 39.0 | 72.0 | 4.25 | 0.56 | 3.3 | -0.01 |
| mux jack 5.0 V, 1.0 m, no breakout pull-ups | ok, sensor clamp conducts briefly | 154.0 | 100.0 | 2.37 | 0.32 | 3.3 | -0.81 |
| mux jack 5.0 V, 1.0 m, breakout 10k pull-ups | ok, sensor clamp conducts briefly | 125.0 | 93.0 | 2.8 | 0.37 | 3.3 | -0.8 |
| mux jack 5.0 V, 1.0 m, Qwiic 2.2k pull-ups | **FAIL** | 70.0 | 79.0 | 4.25 | 0.56 | 3.3 | -0.79 |
| mux jack 5.0 V, 2.0 m, no breakout pull-ups | ok, sensor clamp conducts briefly | 263.0 | 121.0 | 2.37 | 0.32 | 3.3 | -0.83 |
| mux jack 5.0 V, 2.0 m, breakout 10k pull-ups | ok, sensor clamp conducts briefly | 201.0 | 113.0 | 2.8 | 0.37 | 3.3 | -0.83 |
| mux jack 5.0 V, 2.0 m, Qwiic 2.2k pull-ups | **FAIL** | 114.0 | 89.0 | 4.25 | 0.56 | 3.3 | -0.81 |
| bus 2, J14 and J18 both 0.3 m, no breakout pull-ups | ok | 126.0 | None | 1.42 | 0.18 | None | None |
| bus 2, J14 and J18 both 0.3 m, two breakouts with 10k | ok | 88.0 | None | 1.99 | 0.26 | None | None |
| bus 2, J14 and J18 both 0.3 m, two Qwiic boards, 2.2k | **FAIL** | 43.0 | None | 3.82 | 0.5 | None | None |
| bus 2, J14 and J18 both 1.0 m, no breakout pull-ups | ok | 243.0 | None | 1.42 | 0.18 | None | None |
| bus 2, J14 and J18 both 1.0 m, two breakouts with 10k | ok | 170.0 | None | 1.99 | 0.26 | None | None |
| bus 2, J14 and J18 both 1.0 m, two Qwiic boards, 2.2k | **FAIL** | 85.0 | None | 3.82 | 0.5 | None | None |
| bus 2, J14 and J18 both 2.0 m, no breakout pull-ups | **FAIL** | 411.0 | None | 1.41 | 0.19 | None | None |
| bus 2, J14 and J18 both 2.0 m, two breakouts with 10k | ok | 291.0 | None | 1.99 | 0.26 | None | None |
| bus 2, J14 and J18 both 2.0 m, two Qwiic boards, 2.2k | **FAIL** | 150.0 | None | 3.82 | 0.5 | None | None |

### spi

| Case | Result | max_V | min_V | clamp_mA | sck_threshold_recross | miso_setup_ns | miso_fmax_MHz | miso_crosstalk_V |
|---|---|---|---|---|---|---|---|---|
| J5 IMU, 0.1 m, very high (OSPEEDR 11) | ok, IMU clamps conduct (6.1 mA) | 4.07 | -0.77 | 6.1 | 0 | 12.9 | 13.5 | 0.48 |
| J5 IMU, 0.1 m, high (10) | ok, IMU clamps conduct (6.1 mA) | 4.06 | -0.77 | 6.1 | 0 | 12.9 | 13.5 | 0.41 |
| J5 IMU, 0.1 m, medium (01) | ok, IMU clamps conduct (4.7 mA) | 4.05 | -0.75 | 4.7 | 0 | 12.6 | 13.4 | 0.22 |
| J5 IMU, 0.1 m, low (00) | ok, IMU clamps conduct (1.0 mA) | 3.98 | -0.69 | 1.0 | 0 | 12.4 | 13.3 | 0.05 |
| J5 IMU, 0.3 m, very high (OSPEEDR 11) | ok, IMU clamps conduct (7.4 mA) | 4.08 | -0.78 | 7.4 | 0 | 10.9 | 12.8 | 0.88 |
| J5 IMU, 0.3 m, high (10) | ok, IMU clamps conduct (7.5 mA) | 4.08 | -0.78 | 7.5 | 0 | 10.8 | 12.8 | 0.84 |
| J5 IMU, 0.3 m, medium (01) | ok, IMU clamps conduct (6.9 mA) | 4.06 | -0.77 | 6.9 | 0 | 10.8 | 12.8 | 0.73 |
| J5 IMU, 0.3 m, low (00) | ok, IMU clamps conduct (3.3 mA) | 4.03 | -0.74 | 3.3 | 0 | 10.6 | 12.7 | 0.13 |
| J5 IMU, 0.5 m, very high (OSPEEDR 11) | **FAIL** | 4.06 | -0.77 | 6.2 | 2 | 8.8 | 12.1 | 0.92 |
| J5 IMU, 0.5 m, high (10) | **FAIL** | 4.06 | -0.77 | 6.1 | 2 | 8.8 | 12.1 | 0.92 |
| J5 IMU, 0.5 m, medium (01) | ok, IMU clamps conduct (6.0 mA) | 4.05 | -0.77 | 6.0 | 0 | 8.8 | 12.1 | 0.88 |
| J5 IMU, 0.5 m, low (00) | ok, IMU clamps conduct (4.4 mA) | 4.05 | -0.75 | 4.4 | 0 | 9.2 | 12.2 | 0.25 |
| J5 IMU, 1.0 m, very high (OSPEEDR 11) | **FAIL** | 4.06 | -0.77 | 6.6 | 2 | 3.1 | 10.7 | 1.01 |
| J5 IMU, 1.0 m, high (10) | **FAIL** | 4.06 | -0.77 | 6.7 | 2 | 3.1 | 10.7 | 0.99 |
| J5 IMU, 1.0 m, medium (01) | **FAIL** | 4.06 | -0.77 | 6.8 | 2 | 2.8 | 10.6 | 0.94 |
| J5 IMU, 1.0 m, low (00) | **FAIL** | 4.05 | -0.77 | 6.3 | 6 | 0.0 | 10.0 | 0.79 |
| J15 spare, 0.1 m, very high (OSPEEDR 11) | **FAIL** | 4.1 | -0.82 | 12.5 | 0 | 13.5 | 13.7 | 0.63 |
| J15 spare, 0.1 m, medium (01) | **FAIL** | 4.1 | -0.8 | 10.5 | 0 | 14.3 | 14.0 | 0.41 |
| J15 spare, 0.1 m, low (00) | ok, IMU clamps conduct (5.6 mA) | 4.06 | -0.76 | 5.6 | 0 | 14.3 | 14.0 | 0.07 |
| J15 spare, 0.3 m, very high (OSPEEDR 11) | **FAIL** | 4.12 | -0.83 | 14.0 | 4 | 11.5 | 13.0 | 0.92 |
| J15 spare, 0.3 m, medium (01) | **FAIL** | 4.11 | -0.82 | 12.9 | 4 | 12.2 | 13.3 | 0.9 |
| J15 spare, 0.3 m, low (00) | **FAIL** | 4.1 | -0.8 | 10.6 | 0 | 12.8 | 13.5 | 0.17 |
| J15 spare, 0.5 m, very high (OSPEEDR 11) | **FAIL** | 4.14 | -0.83 | 15.1 | 4 | 9.2 | 12.3 | 1.09 |
| J15 spare, 0.5 m, medium (01) | **FAIL** | 4.14 | -0.84 | 15.3 | 4 | 9.9 | 12.5 | 1.05 |
| J15 spare, 0.5 m, low (00) | **FAIL** | 4.1 | -0.81 | 11.1 | 4 | 13.6 | 13.8 | 0.35 |
| J15 spare, 1.0 m, very high (OSPEEDR 11) | **FAIL** | 4.15 | -0.82 | 16.6 | 9 | 3.7 | 10.8 | 1.09 |
| J15 spare, 1.0 m, medium (01) | **FAIL** | 4.15 | -0.82 | 16.3 | 6 | 4.1 | 11.0 | 1.09 |
| J15 spare, 1.0 m, low (00) | **FAIL** | 4.09 | -0.79 | 8.9 | 6 | 6.1 | 11.7 | 1.0 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.1 m, very high (OSPEEDR 11) | ok, IMU clamps conduct (6.9 mA) | 4.07 | -0.77 | 6.9 | 0 | 13.6 | 13.7 | 0.79 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.1 m, medium (01) | ok, IMU clamps conduct (5.5 mA) | 4.06 | -0.76 | 5.5 | 0 | 14.1 | 13.9 | 0.41 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.1 m, low (00) | ok, IMU clamps conduct (2.9 mA) | 4.03 | -0.73 | 2.9 | 0 | 13.8 | 13.8 | 0.07 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.3 m, very high (OSPEEDR 11) | **FAIL** | 4.09 | -0.79 | 8.7 | 0 | 11.5 | 13.0 | 1.1 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.3 m, medium (01) | **FAIL** | 4.08 | -0.79 | 8.5 | 0 | 12.1 | 13.2 | 1.0 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.3 m, low (00) | ok, IMU clamps conduct (6.2 mA) | 4.04 | -0.77 | 6.2 | 0 | 13.8 | 13.8 | 0.17 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.5 m, very high (OSPEEDR 11) | **FAIL** | 4.09 | -0.79 | 8.9 | 4 | 9.4 | 12.3 | 1.14 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.5 m, medium (01) | **FAIL** | 4.09 | -0.79 | 8.8 | 4 | 10.1 | 12.6 | 1.1 |
| J5 IMU, old 22 ohm R8/R9/R41, 0.5 m, low (00) | **FAIL** | 4.07 | -0.77 | 6.4 | 4 | 13.1 | 13.6 | 0.33 |
| J5 IMU, old 22 ohm R8/R9/R41, 1.0 m, very high (OSPEEDR 11) | **FAIL** | 4.09 | -0.81 | 11.9 | 4 | 3.8 | 10.8 | 1.16 |
| J5 IMU, old 22 ohm R8/R9/R41, 1.0 m, medium (01) | **FAIL** | 4.07 | -0.79 | 8.4 | 4 | 4.0 | 10.9 | 1.12 |
| J5 IMU, old 22 ohm R8/R9/R41, 1.0 m, low (00) | **FAIL** | 4.05 | -0.78 | 7.8 | 6 | 4.8 | 11.2 | 0.99 |

### uart

| Case | Result | far_max_V | far_min_V | far_clamp_mA | far_rise_10_90_ns | recross | rx_mcu_max_V | rx_mcu_min_V |
|---|---|---|---|---|---|---|---|---|
| J4 Jetson TX, 1 Mbaud, 0.3 m, GPIO speed very high (11), heavy cable | **FAIL** | 4.12 | -0.82 | 12.7 | 1.3 | 0 | 4.79 | -0.79 |
| J4 Jetson TX, 1 Mbaud, 0.3 m, GPIO speed very high (11), light cable | **FAIL** | 4.12 | -0.82 | 12.9 | 1.4 | 0 | 4.9 | -0.8 |
| J4 Jetson TX, 1 Mbaud, 0.3 m, GPIO speed low (00), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.59 | -0.28 | 0.0 | 12.3 | 0 | 4.79 | -0.79 |
| J4 Jetson TX, 1 Mbaud, 0.3 m, GPIO speed low (00), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.51 | -0.2 | 0.0 | 12.2 | 0 | 4.9 | -0.8 |
| J4 Jetson TX, 1 Mbaud, 1.0 m, GPIO speed very high (11), heavy cable | **FAIL** | 4.14 | -0.84 | 15.7 | 1.7 | 0 | 5.11 | -0.76 |
| J4 Jetson TX, 1 Mbaud, 1.0 m, GPIO speed very high (11), light cable | **FAIL** | 4.12 | -0.82 | 12.8 | 1.6 | 0 | 5.48 | -0.77 |
| J4 Jetson TX, 1 Mbaud, 1.0 m, GPIO speed low (00), heavy cable | ok, far-end clamps conduct (3.7 mA); centurion RX clamp conducts briefly (allowed) | 4.04 | -0.74 | 3.7 | 8.6 | 0 | 5.1 | -0.76 |
| J4 Jetson TX, 1 Mbaud, 1.0 m, GPIO speed low (00), light cable | ok, far-end clamps conduct (1.3 mA); centurion RX clamp conducts briefly (allowed) | 4.0 | -0.7 | 1.3 | 8.3 | 0 | 5.48 | -0.77 |
| J4 Jetson TX, 1 Mbaud, 2.0 m, GPIO speed very high (11), heavy cable | **FAIL** | 4.16 | -0.86 | 18.9 | 2.7 | 0 | 4.97 | -0.78 |
| J4 Jetson TX, 1 Mbaud, 2.0 m, GPIO speed very high (11), light cable | **FAIL** | 4.15 | -0.85 | 17.4 | 2.4 | 0 | 5.37 | -0.77 |
| J4 Jetson TX, 1 Mbaud, 2.0 m, GPIO speed low (00), heavy cable | **FAIL** | 4.1 | -0.8 | 10.2 | 8.6 | 0 | 4.97 | -0.78 |
| J4 Jetson TX, 1 Mbaud, 2.0 m, GPIO speed low (00), light cable | ok, far-end clamps conduct (9.7 mA); centurion RX clamp conducts briefly (allowed) | 4.1 | -0.8 | 9.7 | 8.4 | 0 | 5.37 | -0.77 |
| J19 ramBar TX, 1 Mbaud, 0.3 m, GPIO speed very high (11), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 21.1 | 0 | 4.77 | -0.81 |
| J19 ramBar TX, 1 Mbaud, 0.3 m, GPIO speed very high (11), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 15.6 | 0 | 4.84 | -0.81 |
| J19 ramBar TX, 1 Mbaud, 0.3 m, GPIO speed low (00), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 25.3 | 0 | 4.77 | -0.8 |
| J19 ramBar TX, 1 Mbaud, 0.3 m, GPIO speed low (00), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 20.9 | 0 | 4.84 | -0.81 |
| J19 ramBar TX, 1 Mbaud, 1.0 m, GPIO speed very high (11), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 50.6 | 0 | 5.19 | -0.76 |
| J19 ramBar TX, 1 Mbaud, 1.0 m, GPIO speed very high (11), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 34.1 | 0 | 5.51 | -0.77 |
| J19 ramBar TX, 1 Mbaud, 1.0 m, GPIO speed low (00), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 57.8 | 0 | 5.19 | -0.76 |
| J19 ramBar TX, 1 Mbaud, 1.0 m, GPIO speed low (00), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 40.8 | 0 | 5.51 | -0.77 |
| J19 ramBar TX, 1 Mbaud, 2.0 m, GPIO speed very high (11), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 96.5 | 0 | 5.07 | -0.76 |
| J19 ramBar TX, 1 Mbaud, 2.0 m, GPIO speed very high (11), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 61.0 | 0 | 5.51 | -0.77 |
| J19 ramBar TX, 1 Mbaud, 2.0 m, GPIO speed low (00), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 102.2 | 0 | 5.07 | -0.76 |
| J19 ramBar TX, 1 Mbaud, 2.0 m, GPIO speed low (00), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 68.6 | 0 | 5.5 | -0.77 |
| J19 ramBar TX, 3 Mbaud, 0.3 m, GPIO speed very high (11), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 21.1 | 0 | 4.77 | -0.81 |
| J19 ramBar TX, 3 Mbaud, 0.3 m, GPIO speed very high (11), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 15.6 | 0 | 4.84 | -0.81 |
| J19 ramBar TX, 3 Mbaud, 0.3 m, GPIO speed low (00), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 25.3 | 0 | 4.77 | -0.8 |
| J19 ramBar TX, 3 Mbaud, 0.3 m, GPIO speed low (00), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 20.9 | 0 | 4.84 | -0.81 |
| J19 ramBar TX, 3 Mbaud, 1.0 m, GPIO speed very high (11), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 50.6 | 0 | 5.19 | -0.76 |
| J19 ramBar TX, 3 Mbaud, 1.0 m, GPIO speed very high (11), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 34.1 | 0 | 5.51 | -0.77 |
| J19 ramBar TX, 3 Mbaud, 1.0 m, GPIO speed low (00), heavy cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | 0.0 | 0.0 | 57.8 | 0 | 5.19 | -0.76 |
| J19 ramBar TX, 3 Mbaud, 1.0 m, GPIO speed low (00), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 40.8 | 0 | 5.51 | -0.77 |
| J19 ramBar TX, 3 Mbaud, 2.0 m, GPIO speed very high (11), heavy cable | **FAIL** | 3.3 | 0.0 | 0.0 | 96.5 | 0 | 5.06 | -0.77 |
| J19 ramBar TX, 3 Mbaud, 2.0 m, GPIO speed very high (11), light cable | ok, centurion RX clamp conducts briefly (allowed) | 3.3 | -0.0 | 0.0 | 61.0 | 0 | 5.5 | -0.77 |
| J19 ramBar TX, 3 Mbaud, 2.0 m, GPIO speed low (00), heavy cable | **FAIL** | 3.3 | 0.0 | 0.0 | 102.2 | 0 | 5.06 | -0.77 |
| J19 ramBar TX, 3 Mbaud, 2.0 m, GPIO speed low (00), light cable | **FAIL** | 3.3 | 0.0 | 0.0 | 68.6 | 0 | 5.51 | -0.77 |
| J4 Jetson (no series R), far end unpowered, its rail loaded by 1k, TX idle | **FAIL** | None | None | None | None | None | None | None |
| J4 Jetson (no series R), far end unpowered, its rail loaded by 10k, TX idle | **FAIL** | None | None | None | None | None | None | None |
| J4 Jetson (no series R), far end unpowered, its rail loaded by 100k, TX idle | **FAIL** | None | None | None | None | None | None | None |
| J19 ramBar (R59 470), far end unpowered, its rail loaded by 1k, TX idle | **FAIL** | None | None | None | None | None | None | None |
| J19 ramBar (R59 470), far end unpowered, its rail loaded by 10k, TX idle | **FAIL** | None | None | None | None | None | None | None |
| J19 ramBar (R59 470), far end unpowered, its rail loaded by 100k, TX idle | **FAIL** | None | None | None | None | None | None | None |

### can

| Case | Result | sample_errors | sample_margin_V | recessive_bit_ns | limits_ns | glitches | vod_dominant_V |
|---|---|---|---|---|---|---|---|
| 1 Mbit/s, 0.5 m, ramBar terminated | ok | 0 | 0.5 | 998.0 | 870..1060 | 0 | 2.05 |
| 1 Mbit/s, 0.5 m, ramBar NOT terminated | ok | 0 | 0.5 | 996.0 | 870..1060 | 0 | 2.29 |
| 1 Mbit/s, 1.0 m, ramBar terminated | ok | 0 | 0.5 | 998.0 | 870..1060 | 0 | 2.05 |
| 1 Mbit/s, 1.0 m, ramBar NOT terminated | ok | 0 | 0.5 | 996.0 | 870..1060 | 0 | 2.29 |
| 1 Mbit/s, 2.0 m, ramBar terminated | ok | 0 | 0.5 | 997.0 | 870..1060 | 0 | 2.04 |
| 1 Mbit/s, 2.0 m, ramBar NOT terminated | ok | 0 | 0.5 | 996.0 | 870..1060 | 0 | 2.29 |
| 2 Mbit/s, 0.5 m, ramBar terminated | ok | 0 | 0.5 | 498.0 | 435..530 | 0 | 2.05 |
| 2 Mbit/s, 0.5 m, ramBar NOT terminated | ok | 0 | 0.5 | 496.0 | 435..530 | 0 | 2.29 |
| 2 Mbit/s, 1.0 m, ramBar terminated | ok | 0 | 0.5 | 498.0 | 435..530 | 0 | 2.05 |
| 2 Mbit/s, 1.0 m, ramBar NOT terminated | ok | 0 | 0.5 | 496.0 | 435..530 | 0 | 2.29 |
| 2 Mbit/s, 2.0 m, ramBar terminated | ok | 0 | 0.5 | 497.0 | 435..530 | 0 | 2.04 |
| 2 Mbit/s, 2.0 m, ramBar NOT terminated | ok | 0 | 0.5 | 496.0 | 435..530 | 0 | 2.29 |
| 5 Mbit/s, 0.5 m, ramBar terminated | ok | 0 | 0.5 | 198.0 | 155..210 | 0 | 2.05 |
| 5 Mbit/s, 0.5 m, ramBar NOT terminated | ok | 0 | 0.5 | 196.0 | 155..210 | 0 | 2.29 |
| 5 Mbit/s, 1.0 m, ramBar terminated | ok | 0 | 0.5 | 198.0 | 155..210 | 0 | 2.05 |
| 5 Mbit/s, 1.0 m, ramBar NOT terminated | ok | 0 | 0.5 | 196.0 | 155..210 | 0 | 2.29 |
| 5 Mbit/s, 2.0 m, ramBar terminated | ok | 0 | 0.5 | 197.0 | 155..210 | 0 | 2.04 |
| 5 Mbit/s, 2.0 m, ramBar NOT terminated | ok | 0 | 0.5 | 196.0 | 155..210 | 0 | 2.29 |

### rs485

| Case | Result | sample_errors | sample_margin_V | glitches | vod_low_V |
|---|---|---|---|---|---|
| 0.92 Mbaud, 0.3 m, no termination | ok | 0 | 3.1 | 0 | 3.3 |
| 0.92 Mbaud, 0.3 m, 120 ohm at the brain only | ok | 0 | 2.05 | 0 | 2.25 |
| 0.92 Mbaud, 0.3 m, R51 fitted and 120 at the brain | ok | 0 | 1.51 | 0 | 1.71 |
| 0.92 Mbaud, 1.0 m, no termination | ok | 0 | 3.1 | 0 | 3.3 |
| 0.92 Mbaud, 1.0 m, 120 ohm at the brain only | ok | 0 | 2.05 | 0 | 2.25 |
| 0.92 Mbaud, 1.0 m, R51 fitted and 120 at the brain | ok | 0 | 1.5 | 0 | 1.7 |
| 0.92 Mbaud, 2.0 m, no termination | ok | 0 | 3.1 | 0 | 3.3 |
| 0.92 Mbaud, 2.0 m, 120 ohm at the brain only | ok | 0 | 2.04 | 0 | 2.24 |
| 0.92 Mbaud, 2.0 m, R51 fitted and 120 at the brain | ok | 0 | 1.5 | 0 | 1.7 |
| 2.00 Mbaud, 0.3 m, no termination | ok | 0 | 3.1 | 0 | 3.3 |
| 2.00 Mbaud, 0.3 m, 120 ohm at the brain only | ok | 0 | 2.05 | 0 | 2.25 |
| 2.00 Mbaud, 0.3 m, R51 fitted and 120 at the brain | ok | 0 | 1.5 | 0 | 1.71 |
| 2.00 Mbaud, 1.0 m, no termination | ok | 0 | 3.1 | 0 | 3.3 |
| 2.00 Mbaud, 1.0 m, 120 ohm at the brain only | ok | 0 | 2.05 | 0 | 2.25 |
| 2.00 Mbaud, 1.0 m, R51 fitted and 120 at the brain | ok | 0 | 1.5 | 0 | 1.7 |
| 2.00 Mbaud, 2.0 m, no termination | ok | 0 | 3.1 | 0 | 3.3 |
| 2.00 Mbaud, 2.0 m, 120 ohm at the brain only | ok | 0 | 2.04 | 0 | 2.24 |
| 2.00 Mbaud, 2.0 m, R51 fitted and 120 at the brain | ok | 0 | 1.5 | 0 | 1.7 |

### power

| Case | Result | min_3V3 | min_SENS_3V3 | min_5V | min_SENS_5V | inrush_A | device_peak_V |
|---|---|---|---|---|---|---|---|
| plug 10 uF into SENS_3V3 jack, 0.5 m, fuse 0.15 ohm | **FAIL** | 2.96 | 2.11 | 4.97 | 4.89 | 9.1 | 3.26 |
| plug 10 uF into SENS_3V3 jack, 0.5 m, fuse 0.70 ohm | **FAIL** | 3.2 | 1.28 | 4.98 | 4.9 | 8.4 | 3.17 |
| plug 22 uF into SENS_3V3 jack, 0.5 m, fuse 0.15 ohm | **FAIL** | 2.7 | 1.78 | 4.96 | 4.88 | 10.4 | 3.26 |
| plug 22 uF into SENS_3V3 jack, 0.5 m, fuse 0.70 ohm | **FAIL** | 3.13 | 0.75 | 4.97 | 4.89 | 9.4 | 3.16 |
| what if C28 were 47uF: plug 10 uF into SENS_3V3 jack, fuse 0.70 ohm | **FAIL** | 3.25 | 2.52 | 4.99 | 4.91 | None | None |
| what if C28 were 100uF: plug 10 uF into SENS_3V3 jack, fuse 0.70 ohm | **FAIL** | 3.27 | 2.85 | 4.99 | 4.91 | None | None |
| dead short on SENS_3V3 jack, fuse 0.15 ohm | **FAIL** | None | None | None | None | None | None |
| dead short on SENS_3V3 jack, fuse 0.70 ohm | **FAIL** | None | None | None | None | None | None |
| plug 10 uF into SENS_5V jack, 0.5 m, fuse 0.15 ohm | **FAIL** | 3.29 | 3.23 | 4.58 | 3.07 | 12.9 | 4.96 |
| plug 10 uF into SENS_5V jack, 0.5 m, fuse 0.70 ohm | **FAIL** | 3.29 | 3.23 | 4.9 | 1.2 | 11.2 | 4.84 |
| plug 22 uF into SENS_5V jack, 0.5 m, fuse 0.15 ohm | **FAIL** | 3.29 | 3.23 | 4.24 | 2.67 | 14.6 | 4.96 |
| plug 22 uF into SENS_5V jack, 0.5 m, fuse 0.70 ohm | **FAIL** | 3.29 | 3.23 | 4.83 | 0.55 | 12.2 | 4.84 |
| what if C29 were 47uF: plug 10 uF into SENS_5V jack, fuse 0.70 ohm | **FAIL** | 3.29 | 3.23 | 4.97 | 3.83 | None | None |
| what if C29 were 100uF: plug 10 uF into SENS_5V jack, fuse 0.70 ohm | **FAIL** | 3.29 | 3.23 | 4.98 | 4.34 | None | None |
| dead short on SENS_5V jack, fuse 0.15 ohm | **FAIL** | None | None | None | None | None | None |
| dead short on SENS_5V jack, fuse 0.70 ohm | **FAIL** | None | None | None | None | None | None |
| plug 47 uF into J19 ramBar 5 V, 1.0 m, fuse 0.10 ohm | **FAIL** | 3.29 | 3.23 | 3.79 | 3.71 | 11.4 | 4.99 |
| plug 47 uF into J19 ramBar 5 V, 1.0 m, fuse 0.40 ohm | **FAIL** | 3.29 | 3.23 | 4.36 | 4.29 | 7.0 | 4.97 |
| plug 100 uF into J19 ramBar 5 V, 1.0 m, fuse 0.10 ohm | **FAIL** | 3.29 | 3.23 | 3.15 | 3.08 | 12.1 | 4.82 |
| plug 100 uF into J19 ramBar 5 V, 1.0 m, fuse 0.40 ohm | **FAIL** | 3.29 | 3.23 | 3.95 | 3.88 | 7.2 | 4.52 |
| plug 220 uF into J19 ramBar 5 V, 1.0 m, fuse 0.10 ohm | **FAIL** | 3.29 | 3.23 | 2.47 | 2.39 | 12.6 | 3.04 |
| plug 220 uF into J19 ramBar 5 V, 1.0 m, fuse 0.40 ohm | **FAIL** | 3.29 | 3.23 | 3.44 | 3.36 | 7.4 | 2.86 |
| dead short on J19 ramBar 5 V, fuse 0.10 ohm | **FAIL** | None | None | None | None | None | None |
| dead short on J19 ramBar 5 V, fuse 0.40 ohm | **FAIL** | None | None | None | None | None | None |

### adc

| Case | Result | aux1_error_LSB | pot_error_LSB |
|---|---|---|---|
| 10 kS/s per channel, 2.5 ADC cycles (59 ns) sampling | ok | -1.8 | -0.5 |
| 10 kS/s per channel, 12.5 ADC cycles (294 ns) sampling | ok | -1.8 | -0.5 |
| 10 kS/s per channel, 47.5 ADC cycles (1118 ns) sampling | ok | -1.8 | -0.5 |
| 10 kS/s per channel, 247.5 ADC cycles (5824 ns) sampling | ok | -1.6 | -0.5 |
| 100 kS/s per channel, 2.5 ADC cycles (59 ns) sampling | **FAIL** | -9.8 | -4.5 |
| 100 kS/s per channel, 12.5 ADC cycles (294 ns) sampling | **FAIL** | -9.7 | -4.5 |
| 100 kS/s per channel, 47.5 ADC cycles (1118 ns) sampling | **FAIL** | -9.6 | -4.5 |
| 500 kS/s per channel, 2.5 ADC cycles (59 ns) sampling | **FAIL** | -45.4 | -22.0 |
| 500 kS/s per channel, 12.5 ADC cycles (294 ns) sampling | **FAIL** | -45.2 | -22.0 |
| pot gain error from R55 (100 ohm) with a 10k pot, at full scale (DC, calibrates out) | ok | None | None |
| pot linearity error from R60 (1M pull-down) on a 10k pot, worst position (DC) | ok | None | None |
