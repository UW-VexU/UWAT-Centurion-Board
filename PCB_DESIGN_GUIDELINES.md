# PCB design guidelines

Layout rules, conventions and checks for UWAT VEXU boards (centurion, powerJackal, stellaNova, rambar). Collected from vendor datasheets, application notes, IPC summaries and fab capability pages in November 2026, while reviewing centurion rev A. The numbers in the examples are centurion's, but the rules apply to any of our 2-layer boards.

Sources are listed at the end. Some items could not be checked against a primary source; they're marked *unverified*.

## 1. Trace width and current

Widths for **1 oz outer-layer copper**, from the IPC-2221 external formula (I = 0.048 x dT^0.44 x A^0.725):

| Current | 10 °C rise | 20 °C rise |
|---|---|---|
| 0.5 A | 0.12 mm | 0.08 mm |
| 1 A | 0.30 mm | 0.20 mm |
| 2 A | 0.78 mm | 0.51 mm |
| 3 A | 1.37 mm | 0.90 mm |

- Treat the 10 °C column as the default. IPC-2152 tends to come out slightly narrower for outer layers, so 2221 errs safe.
- **Vias.** A 0.3 mm drill carries roughly 1.4 to 1.8 A at a 10 °C rise. Budget about 1 A per via, and use 2 to 4 vias wherever a 2 A path changes layer.
- **Use a pour, not a trace,** for converter VIN, VOUT and PGND, for SOT-223 LDO tabs, and for anything above about 1.5 A.
- **Neck-downs** (thin sections where a track enters a fine-pitch pad) are fine. They must never sit in the middle of a power run.

## 2. Ground and copper pours (2-layer)

- **Bottom layer = ground plane.** Treat the bottom as almost-solid GND. Signals that must use the bottom should be short hops that come straight back up. Every long bottom trace is a slot that makes return currents detour.
- **No slots under sensitive signals.** No other-net trace should cross under a USB pair, an RS-485 or CAN pair, a crystal, SPI lines, or a switching converter's input loop. To check, turn on the bottom pour by itself in KiCad and look for long thin channels.
- **Stitching vias.** Rule of thumb: space them at most λ/20 apart, where λ is set by edge rate, not clock rate. For USB full speed (about 4 ns edges) that is about 80 mm, so a 4 mm grid is plenty. The stitching vias that really matter are:
  - next to every IC GND pin and decoupling cap;
  - next to ESD-array GND pins;
  - beside the layer-change vias of critical signals;
  - along the board edge.
- **Thermal reliefs.**
  - Use reliefs on ordinary SMD and through-hole GND pads, so they solder well.
  - Use solid connections on exposed thermal pads, SOT-223 tabs and high-current pins.
  - Make relief spokes as wide as the net's trace width.
  - Check that the pour didn't silently put a relief on an exposed pad.
- **Islands and slivers.**
  - Remove floating copper islands (KiCad: island removal = Always); a floating island is an antenna, not a shield.
  - Set the minimum pour width to 0.25 mm or more, and the pour clearance to 0.25 to 0.3 mm (more than the 0.2 mm track clearance).
- **GND routed as tracks under the pour is harmless.** The tracks merge into the pour. What matters is that the plane stays continuous.

## 3. Switching regulators and power modules

Examples are from TI's TPSM53602 datasheet; the same rules apply to most buck modules.

- **Input caps.** At least 20 µF of ceramic (X5R/X7R, rated above VIN max) right at the VIN pins to PGND, plus a bulk cap for transients. An electrolytic counts as the bulk cap, not the ceramic.
- **Output caps.** Ceramics go closest to the module. Meet the datasheet's minimum COUT for your VOUT.
- **AGND to PGND** connects at one point.
- **Feedback.** The divider goes right at the FB pin. Take the top of the divider from the regulation point. Keep the FB node short and away from VIN/VOUT copper.
- **DNC pins** (do not connect) get isolated pads that touch nothing, not even the pour. NC pins go wherever the datasheet says; for the TPSM53602 that's PGND. EN never floats.
- **Thermal.** Datasheet thermal numbers assume a big 4-layer, 2 oz board, so a 2-layer, 1 oz board runs hotter. To compensate:
  - put several vias from the thermal pad to the bottom pour;
  - keep as much unbroken PGND copper as possible on both layers;
  - tell the fab whether vias in pads should be filled, plugged or tented.

## 4. LDOs, decoupling and crystals

- **LDO heat.** Dissipation is (VIN - VOUT) x I. For 5 V to 3.3 V at 0.5 A that is 0.85 W, or about a 53 °C rise for a SOT-223 on a JEDEC board. At 1 A it is not viable. Pour GND on the tab with vias, and check the real load.
- **MCU decoupling.** For each VDD pin:
  - one 100 nF cap within about 2 mm;
  - its own short trace to the pin;
  - a GND via right at the cap pad.

  Add 4.7 to 10 µF bulk for the whole MCU. VDDA/VREF+ get about 1 µF plus 10 to 100 nF at the pins. (Values from ST's F1/F4/H7 material; *unverified for STM32G4*, so check AN5093.)
- **Crystals** (ST AN2867):
  - as close to the MCU as possible, with symmetric load caps;
  - a GND guard around the oscillator traces;
  - solid GND underneath, with no other nets under the crystal on either layer;
  - the ground area tied to the nearest MCU VSS pin;
  - high-frequency signals kept away;
  - no test points on the oscillator nets.

## 5. USB, RS-485, CAN and other cable signals

- **USB full speed (12 Mbps).** Impedance control matters from about 165 mm of trace. Below that, close is good enough.
  - Route D+/D- tightly coupled and length-matched, with no vias, over unbroken GND, with GND on both sides where possible.
  - True 90 Ω on a 2-layer 1.6 mm board needs coplanar-with-ground geometry. Use an impedance calculator if you need it.
- **ESD arrays** (USBLC6, TPD4E05U06, TVS diodes):
  - put them as close to the connector as possible;
  - route the signal connector → ESD pad → IC, so the transient passes the clamp first;
  - give the GND connection a short, wide path, with a via at the pin;
  - keep unprotected traces away from the connector-to-ESD stretch.
- **CAN and RS-485.**
  - The TVS goes at the connector, and so does any termination. If termination is on the board, split it (2 x 60 Ω with a cap to GND).
  - Bypass caps go at the transceiver, each with two vias.
  - Route each pair coupled, over solid GND.
  - **Use a CAN-rated TVS** (NUP2105L, ESD2CAN24 or similar). A 5.5 V unidirectional array clips CAN's -2 to +7 V common-mode range.
- **Long cables** (for example a 30 cm SPI cable):
  - put 22 to 47 Ω series resistors at the source;
  - run a GND next to each signal at the connector;
  - pull up any input that can float when the cable is unplugged.

## 6. Fab rules: PCBWay and JLCPCB

| Rule | PCBWay | JLCPCB | Safe for both |
|---|---|---|---|
| Track / space | 0.1 / 0.1 mm | 0.1 / 0.1 mm | 0.127 mm or more |
| Min drill | 0.15 mm | 0.15 mm (0.25 mm via pad) | 0.3 mm drill, 0.6 mm pad |
| Annular ring | 0.15 mm | 0.18 mm min, 0.25 mm recommended | 0.25 mm |
| Silkscreen | 0.8 mm tall, 0.15 mm stroke | 1.0 mm tall (0.8 mm only on the high-precision option) | 1.0 mm / 0.15 mm |
| Silk to pad | not stated | 0.15 mm | 0.15 mm |
| Copper to edge | 0.25 mm | 0.2 mm milled, 0.4 mm V-cut | 0.5 mm |
| Solder mask dam | 0.1 mm green, 0.115 mm other colours | 0.1 mm green, 0.13 mm black/white | Check fine-pitch QFN/LQFP in the DFM viewer |

- **Assembly.** Both fabs add rails, tooling holes and fiducials if missing. If you add your own, use 2 or 3 fiducials: 1 mm copper, 2 mm mask opening, at least 3.35 mm from the edge.
- **General.**
  - Tent or plug every via except deliberate thermal-pad vias.
  - Courtyards must not overlap.
  - Test pads should be 1.0 mm or larger (centurion uses 1.5 mm round).
  - Keep copper well clear of mounting-hole screw heads and washers.
- **Before ordering,** in this order:
  1. KiCad DRC with the fab's rules.
  2. The fab's online DFM check on the Gerbers.
  3. A 1:1 paper print to test-fit connectors.
- **Price.** Both fabs' cheap promos stop at 100 x 100 mm, so a board even slightly bigger costs several times more. Keep boards inside that size when the mechanics allow it.
- **Shipping to Canada.**
  - DHL bills duties and 13% HST to the receiver unless the order is DDP, plus a clearance fee of about $20 (forum reports, June 2025).
  - Check whether DDP is offered at checkout.
  - Canada's China surtax order was amended in February 2026 (SOR/2026-33). Check whether it covers PCBs before ordering. *Unverified.*

## 7. After the autorouter (Freerouting)

**What to inspect:**
- acute angles, stubs and unnecessary vias, especially on differential pairs;
- power nets that daisy-chain through thin neck-downs;
- long bottom-layer detours that slice the GND plane;
- traces under the crystal, or under a buck module and its input-cap loop;
- decoupling caps reached by a long trace instead of directly at the pin;
- crossings under the connector-to-ESD segments.

**Cleanup order:**
1. Hand-route power, the crystal, USB and the differential pairs, then lock them.
2. Delete and re-push long bottom-layer runs.
3. Remove redundant vias and stubs.
4. Re-pour and view each layer's pour alone to look for slots.
5. Add stitching vias at IC and ESD GND pins.
6. Run DRC and the fab's DFM check.
7. Clean up the silkscreen.

## 8. Schematic hygiene

- **One name per net.** KiCad's `multiple_net_names` warning means two labels or power symbols sit on the same wire.
  - Electrically it's harmless, but only one name wins. The priority is global label, then power symbol, then local label, then hierarchical label, then sheet pin.
  - Net classes, DRC rules and PCB net names all use the winning name, so a rule written for the losing name silently doesn't apply.
  - Fix it by deleting or replacing the redundant label. A power symbol is better than a local label for a rail.
  - Don't hide it with ERC exclusions. Exclusions are keyed to positions and UUIDs, and have been reported lost on edits.
- **Aim for 0 ERC warnings.** A warning everyone has learned to ignore will hide the real short.
- **Text notes.** When a schematic file is edited by script, multi-line text must use `\n` escapes, not raw line breaks. Otherwise KiCad silently drops everything after the note.

## 9. Pre-order checklist (ordered by respin risk)

1. ☐ Converter DNC pins are isolated pads; NC pins and EN are tied as the datasheet says; AGND joins PGND at one point.
2. ☐ The feedback divider sits at the FB pin and gives the right output voltage.
3. ☐ Converter input ceramics are at the VIN pins; output caps meet the datasheet minimum.
4. ☐ Exposed pads connect solidly, with several vias; via fill or plug is specified to the fab.
5. ☐ LDO dissipation is calculated for the worst case; the tab has a GND pour with vias.
6. ☐ Power paths of 2 A or more are pours or traces of 0.8 mm or more, with no thin necks mid-run and 2 to 4 vias per layer change.
7. ☐ Every footprint's pinout, polarity and pin-1 mark matches the datasheet.
8. ☐ Each VDD pin has its own 100 nF cap within about 2 mm with a GND via; VDDA/VREF+ caps sit at the pins.
9. ☐ Crystal and load caps are within a few mm of the MCU, symmetric, with solid GND under them and no other nets.
10. ☐ The bottom layer is close to solid GND, with no slots under USB, CAN, RS-485, SPI, the crystal or the converter loop.
11. ☐ USB D+/D- is coupled, length-matched, has no vias and runs over continuous GND.
12. ☐ ESD and TVS parts sit at the connectors, signals route through the protection pads, and GND is short with a via.
13. ☐ No unprotected trace runs beside the connector-to-ESD segments.
14. ☐ Termination is near the connector; transceiver bypass caps each have 2 vias.
15. ☐ The input protection order is right (fuse, OR diodes, TVS), with a short TVS GND return.
16. ☐ IC and ESD GND pins have stitching vias, and the board edge is stitched.
17. ☐ There are no floating islands; minimum pour width is 0.25 mm or more; pour clearance is 0.25 to 0.3 mm.
18. ☐ Thermal reliefs are on ordinary pads; power and thermal pads are solid.
19. ☐ Mounting-hole keep-outs clear the screw heads; copper-to-edge is 0.5 mm.
20. ☐ Solder mask dams on fine-pitch parts are 0.1 mm or more (0.13 mm if not green).
21. ☐ Silkscreen is at least 0.8 mm (PCBWay) or 1.0 mm (JLC) tall, kept off pads, with polarity marks and connector names.
22. ☐ Inputs that can float with a cable unplugged have pull-ups or pull-downs.
23. ☐ For assembly, there are fiducials or fab-added rails, no overlapping courtyards, and the pick-and-place rotations are checked.
24. ☐ ERC is at 0 errors and 0 warnings, and DRC is clean with schematic parity.
25. ☐ Autorouter cleanup is done, followed by DRC with the fab's rules and the fab's online DFM check.

## Sources

- TI TPSM53602 datasheet, SNVSBD0B (Sep 2021): https://www.ti.com/lit/ds/symlink/tpsm53602.pdf
- TI TCAN33xG datasheet, SLLSEQ7F (May 2025), §7.5.1: https://www.ti.com/lit/ds/symlink/tcan334.pdf
- Microchip MCP1826/S, DS22057B: https://ww1.microchip.com/downloads/en/DeviceDoc/22057B.pdf
- ST AN2867, oscillator design guide: https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf
- ST AN5093, STM32G4 hardware guide (not read; the download timed out): https://www.st.com.cn/resource/en/application_note/an5093-getting-started-with-stm32g4-series--hardware-development-boards-stmicroelectronics.pdf
- TI ESD layout guidance: https://www.ti.com/document-viewer/ja-jp/TPD1E05U06-Q1/datasheet/layout and https://ti.com/document-viewer/TPD4E002/datasheet/layout
- USBLC6 layout (secondary sources): https://www.embeddedrelated.com/parts/p/USBLC6-2SC6 and https://community.st.com/t5/other-hardware/routing-for-usblc6-2sc6/m-p/737192
- USB FS routing: https://blog.mbedded.ninja/electronics/communication-protocols/usb-protocol/how-to-route-usb-tracks and https://resources.altium.com/p/routing-requirements-usb-20-2-layer-pcb
- Trace width tables: https://resources.altium.com/p/pcb-trace-width-vs-current-table-high-voltage-design and https://jlcpcb.com/blog/304-copper-weight-and-trace-width-finding-the-optimal-balance
- 2-layer grounding: https://onlinedocs.microchip.com/oxy/GUID-52972CAB-8C1D-44E1-99A1-4899C2769960-en-US-2/GUID-FCA6F4C8-473A-497F-A0AE-42F4DEE9B54F.html and https://resources.altium.com/pcb-design-blog/understanding-ground-planes-in-your-two-layer-pcb
- Via stitching: https://www.flux.ai/p/blog/via-stitching-pcb-guide and https://sierraconnect.protoexpress.com/t/optimizing-via-stitching-placement-on-4-layer-pcbs/2700
- Thermal reliefs: https://jlcpcb.com/blog/thermal-relief-pad-design
- PCBWay capabilities: https://www.pcbway.com/capabilities.html and fiducials: https://www.pcbway.com/blog/PCB_Manufacturing_Information/Fiducial_Mark_PCB_Knowledge_542b3c29.html
- JLCPCB capabilities: https://jlcpcb.com/capabilities/pcb-capabilities ; silkscreen: https://jlcpcb.com/blog/character-design-specifications ; rails and fiducials: https://api.jlcpcb.com/help/article/How-to-add-edge-rails/fiducials-for-PCB-assembly-order ; assembly FAQ: https://jlcpcb.com/help/article/98-pcb-assembly-faqs
- Shipping to Canada: https://forum.kicad.info/t/alternatives-to-jlcpcb-or-pcbway-for-canadian-hobbyist/61624 ; https://www.dhl.com/discover/en-ca/ship-with-dhl/start-shipping/understanding-duties-and-taxes ; China surtax amendment: https://gazette.gc.ca/rp-pr/p2/2026/2026-03-11/html/sor-dors33-eng.html
- KiCad net naming and ERC: https://docs.kicad.org/9.0/en/eeschema/eeschema.html ; exclusion bugs: https://gitlab.com/kicad/code/kicad/-/issues/21410 and https://gitlab.com/kicad/code/kicad/-/issues/15274
