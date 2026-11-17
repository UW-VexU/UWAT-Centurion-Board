# ramBar: next steps

What is left before ramBar can be ordered, as of 2026-11-17. The schematic is close to done. The layout has not started. For how the board works, see [README.md](README.md).

## Schematic

### Must do before layout

1. **Run ERC in KiCad.** Inspect → Electrical Rules Checker. The 2026-11-17 changes were checked with a script that rebuilds the netlist, not with KiCad. Fix anything ERC flags.
2. **Run Tools → Update PCB from Schematic once.** This pulls every footprint into `rambar.kicad_pcb` and shows any footprint that doesn't load. All three libraries (`UWAT`, `centurion`, `rambar`) load relative to the repo, so it should work on any machine.
3. **Decide 5 or 7 sensors.** The schematic has 7 slots (S1 to S7). If the arc gets 5, mark the two unused sensors and their parts as not fitted. See [Sensor count and spacing](#sensor-count-and-spacing).
4. **Add mounting holes** once the bracket design says how the flex attaches. There are none in the schematic yet.

### Nice to have

- **Pin notes on the MCU decoupling caps.** Say which pin each cap sits at, as Centurion does: C21 at VBAT (pin 1), C22 to C24 at VDD (pins 24, 36, 48), C52 and C50 at VDDA and VREF+ (pins 21 and 20), C25 as bulk. It speeds up placement.
- **Not-fitted 120 Ω across RS485_A and RS485_B,** like Centurion's R51. It costs nothing and covers a bus that rings.
- **J3 (SWD header).** It is through-hole and needs its own stiffener on a flex. Switching to SMD pads or a Tag-Connect footprint avoids that. Flashing goes over USB anyway, so J3 is only for debugging.

### Before ordering

- Recheck DigiKey Canada stock for every line, especially STM32G491CET6, VL53L4CDV0DH/1 and CL10A475KO8NNNC. Stock was not checked on 2026-11-17.
- The design concept's checkpoint: bench test that the sensors see clear Cups and that the error stays under 5 mm before ordering this board.
- Ask the Q&A about custom boards under VUR12, as the concept plans.

## Layout

### Decisions needed first

These set the outline and placement, so they come before anything is placed.

1. **Where the electronics end goes.** The power block, MCU, J1 (smart port), J16 (USB-C) and J2 (Centurion link) need one stiffened area. The options are:
   - a tail off one end of the arc,
   - a wider section behind the middle of the arc, which halves the trace run to the end sensors,
   - a small separate rigid board joined to a sensor-only flex.
2. **Arc geometry.** The concept uses a 62 mm radius at the sensor face over 150°. That makes the sensor strip about 162 mm long when laid flat. Confirm it against the carriage CAD.
3. **Sensor count and spacing.** See below.
4. **Fab and stackup.** Likely a 2-layer flex at JLCPCB, with FR4 stiffeners. Check their flex limits (minimum track and space, via size, stiffener types and thickness, through-hole assembly on flex) before setting the design rules.

### Sensor count and spacing

| Fitted | Spacing on the arc | Distance along the flat strip |
|---|---|---|
| 7 | 25° | about 27.1 mm |
| 5 | 37.5° | about 40.6 mm |

With 7 positions on the board, 5 sensors can still be fitted at S1, S2, S4, S6 and S7 (-75°, -50°, 0°, +50°, +75°). The firmware's estimate matrix changes, but the math still works. A board with 5 positions at 37.5° matches the concept's simulation exactly but can't take 7 later.

The distances use 62 mm. The flex itself sits a little outside the sensor face (sensor height plus copper), so take the exact radius from the bracket CAD.

### Stiffeners

- One FR4 stiffener under the whole electronics end. J1, J16, J3 and C1 are through-hole, so their stiffener goes on the component side.
- A small stiffener under each sensor, so bending the strip doesn't change where a sensor points.
- Draw stiffeners on a user layer (for example User.1, named Stiffener) and send it to the fab as a drawing, as their order form asks.

### Placement

- Copy the power block's placement from `centurion.kicad_pcb`: C2, C32 and C3 at U1's VIN pins, C4 and C5 at VOUT, R29 and R30 at the FB pin. Keep the order J1 → D5 → F1 → D4 and C1 close to the smart port jack.
- U13 right beside J16, and C30 right at U13's VBUS pin. On Centurion C30 ended up 9.9 mm away, which its review flagged.
- U17 and D12 right beside J2, between the jack and the parts they protect. U16 and R53 next to them.
- U14 (RS-485) next to J1.
- Each sensor's 100 nF and 4.7 µF at its supply pins, and its XSHUT and GPIO1 resistors next to it.
- Y1, C29 and C51 right at the MCU's PF0 and PF1 pins, with no other signals under them.
- Put the crowded parts (MCU, buck, LDO) on the stiffened area only.

### Routing

- The strip carries 7 XSHUT, 7 GPIO1, 2 I2C buses (4 lines), +3.3V and GND, about 20 lines. On 2 layers that fits in a strip about 8 to 10 mm wide. Placing the MCU behind the middle of the arc halves the run.
- Keep each I2C bus's SCL and SDA next to each other, with GND on the other layer. A hatched GND pour bends better than a solid one in the flexing part.
- Route the RS-485 pair and the CAN pair side by side. Centurion's review flagged both for being split.
- No vias in bend areas. Run traces at right angles to the bend line, and stagger the top and bottom traces so they don't sit on top of each other.
- Track widths from the Carry-Over note: 0.8 mm for VPORT, VIN_OR, VIN_MOD and +5V, 0.5 mm for VBUS_USB, USB_PWR, 5V_LDO and 5V_J19. Three vias wherever a power net changes layer.

### Concerns

- **Ceramic caps crack if the board bends under them.** C2, C3, C16 and C32 (1210) and C4, C5 and C17 (1206) stay on the stiffener, away from any bend line, with their long side parallel to the bend.
- **LDO heat.** U7 can burn about 0.5 W at the worst-case load. Centurion spreads that heat through 8 vias into a solid GND plane, which a 2-layer flex doesn't have. Give U7's tab the biggest copper pour the stiffened area allows, and measure its temperature at bring-up.
- **Buck thermal vias.** U1's ThermalVia footprint expects plugged vias and a GND plane. Ask the fab whether they can plug vias on flex. If not, solder can wick down them.
- **Connector strain.** The smart port cable is stiff and gets pulled. J1, J16 and J2 need the stiffener and screws close by, so the force doesn't reach the flex.
- **Sensor view.** Keep each sensor's 25° exclusion cone clear of stiffener edges, other parts, the bracket and the held game piece (15 to 20 mm clearance, from the concept).
- **Impact.** The strip sits where stacks and robots hit. Plan a printed guard and keep parts off the edges that face out.
- **Assembly.** VL53L4CD needs dry (convection) reflow and no washing. Leave the protective liner on through soldering and peel it off at the end.

### Checks before ordering

- DRC clean, with zones refilled.
- Schematic and board in sync (no parity errors).
- Print the outline 1:1 and fit it on the printed arc bracket with a real smart port cable and a JST-GH cable plugged in.
- Run the repo's review agents on the `rambar` folder (`pcb-layout-auditor`, `pcb-footprint-checker`, `pcb-power-thermal`, `pcb-signal-checker`). They were written for rigid boards, so read their flex findings with that in mind.
- Generate the Gerbers and check them with `tools/gerbcheck.py`, as in the main README.
