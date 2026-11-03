# Hand routing with Claude Desktop (computer use)

How to have Claude Desktop do the hand routing in [HAND_ROUTING.md](HAND_ROUTING.md) by driving KiCad on your screen.

Part A is for you, the person setting it up. Part B has the prompts to paste into Claude Desktop, one task per conversation.

## A. Setup (you)

1. **Backup.** Commit the current `centurion.kicad_pcb` to git before each Claude Desktop session. Commit again after every task that passes its check. Then a bad session only ever costs one task.
2. **Only one editor at a time.** While Claude Desktop is working, don't have Claude Code (or anyone) edit the project files. KiCad keeps its own copy in memory and would overwrite them, or the other way round.
3. **Computer use.** Turn on computer use in Claude Desktop's settings. Give it access to KiCad when it asks.
4. **Screen.**
   - Open `centurion.kicad_pro` in KiCad 10, open the PCB editor, and maximize it on your main monitor.
   - Close other windows over it.
   - A large monitor helps: Claude reads the screen from screenshots, and small text and dense copper are where it makes mistakes.
5. **KiCad settings to set once.** Claude can also do these, but it's faster if you do:
   - Route → Interactive Router Settings → Mode **Shove**. Tick **Remove redundant tracks** and **Optimize pad connections**.
   - In KiCad's Preferences (display options), set the cursor to the full-window crosshair. It helps Claude see where it's clicking.
   - Grid (top toolbar): 0.1 mm.
6. **Stay nearby.** Claude Desktop asks before some actions, and it's slow: expect a few minutes per trace. Watch the first task all the way through before leaving it alone.
7. **After each session**, you can ask Claude Code to "measure the board". It has scripts that report bottom-layer copper, pair spacing and ESD order, so you can see progress against the targets in HAND_ROUTING.md.

## B. Prompts for Claude Desktop

Start every conversation with the **base prompt**, then paste **one** task prompt. Start a new conversation for the next task. Long conversations make computer use slower and less reliable.

### Base prompt (paste first, every time)

```
You are helping hand-route a 2-layer PCB in KiCad 10, which is open and maximized on my screen (PCB editor, project "centurion"). Use computer use to operate KiCad. The full background is in centurion/HAND_ROUTING.md in the project folder if you want to read it.

The board: 103 x 63 mm, 2 layers. F.Cu (top, red) is for signals. B.Cu (bottom, blue/green) should be an unbroken GND plane; every signal track on B.Cu cuts that plane. GND is poured on both layers (zones); never delete or edit the zones. KiCad's coordinates: the board's top-left corner is (100, 100) and bottom-right is (203.2, 162.6); the cursor position is shown in the status bar at the bottom.

Rules:
1. Change only what the task asks. Never move parts unless the task says so; most are locked on purpose. Never touch the schematic. Never use "Update PCB from Schematic", the autorouter, or "Cleanup Tracks & Vias" on the whole board.
2. Work in small steps and look at a screenshot after each one. If something unexpected happens, press Escape, then Ctrl+Z to undo, and tell me.
3. Prefer F.Cu. Use B.Cu only for a short (< 5 mm) straight hop to cross another top track, at right angles to it.
4. Before starting, run Inspect → Design Rules Checker (with "Test for parity between PCB and schematic" ticked) and note the counts, so you know what was already there. When the task is done: press B (refill zones), save with Ctrl+S, and run DRC again. Report the counts before and after (violations, unconnected items, schematic parity). Your task must not add any; if it did, list them and fix the ones you caused. If you can't, undo your changes and tell me. Until the USB task is done, 1–2 unconnected items on USB_D- (plus a dangling via) are expected.
5. If you are unsure, stop and ask me rather than guess.

KiCad keys you will need:
- Ctrl+F: find a part by reference (e.g. "U9"); it zooms to it.
- Mouse wheel: zoom. Middle-drag: pan. Home: zoom to whole board.
- ` (backtick, left of 1): highlight the net under the cursor; press again to clear.
- Click a track to select it. U: grow the selection to the whole connection (press again to grow more). Delete: delete selection.
- X: route a single track. Click a pad to start, click to place corners, double-click (or click the end pad) to finish. While routing: V = place a via and change layer, / = flip corner direction, Escape = cancel. Page Up = F.Cu, Page Down = B.Cu.
- 6: route a differential pair (only works on nets named with +/- or P/N endings).
- E on a selected track: edit its exact width, layer and end coordinates.
- Appearance panel (right side) → Layers: the eye icon hides/shows a layer. Ctrl+H toggles high-contrast mode (only the active layer is bright).
- Inspect → Net Inspector: track length per net and per layer.
- Hovering a pad shows its number and net in the message panel at the bottom.

Please confirm you can see KiCad's PCB editor with the centurion board, then wait for the task.
```

### Task prompts (one per conversation, roughly in this order)

Each task matches a step in HAND_ROUTING.md, which has more background if Claude asks why.

**Task 1: the open connection and dangling vias**

```
Task: run Inspect → Design Rules Checker with "Test for parity" ticked. It should list 2 unconnected items and 2 dangling vias.
- MUX7_SCL: U11 pad 2 (≈182.9, 115.7) is not connected to the rest of its trace, which ends at about (187.6, 112.2) near jack J13. Route that gap with X on F.Cu. Make sure the net then runs jack J13 pin 2 → U11 pad 2 → onward (U11 is its ESD clamp).
- USB_D-: leave it; a later task reroutes the whole USB pair.
- Dangling via on RS485A_TX at about (126.5, 129.4): click it in the DRC list, check that it doesn't join a track on both layers, then select it and press Delete.
Then do the end-of-task checks. Expected afterwards: 1 unconnected (USB_D-) and 1 dangling via (on USB_D-); nothing else.
```

**Task 2: ESD order on the sensor jacks**

```
Task: on the sensor jacks J6–J13 (top edge), every I2C line must run jack → ESD clamp → mux (U6, the 24-pin chip at about (142, 122)), so the clamp sees a static zap before the mux does. The clamps are U8 (≈119.8, 115.3) for J6/J7, U9 (≈141.0, 115.3) for J8/J9, U10 (≈162.2, 115.3) for J10/J11, U11 (≈183.4, 115.3) for J12/J13. Jack pin 2 is SCL and pin 3 is SDA.

Start with J7 pin 3 (net /Sensors/ENC2_SDA). It currently reaches U6 pin 6 before its clamp U8 pin 5. Delete that net's tracks and re-route it on F.Cu as J7 pin 3 → U8 pin 5 → U6 pin 6, and reconnect the pullup resistor R16 anywhere between J7 and U8.

Then the longest detours, each to be rerouted jack → clamp → U6 on F.Cu, as short as you can: J12 pin 3 (TOF4_SDA, 37 mm now, clamp U11 pin 4), J10 pin 3 (TOF2_SDA, 27 mm, U10 pin 4), J6 pin 3 (ENC1_SDA, 27 mm, U8 pin 4). Only do more if those went well; HAND_ROUTING.md step 2 has the full list. Report which ones you changed. Then do the end-of-task checks.
```

**Task 3: CAN pair to ramBar**

```
Task: route the CAN pair as a pair. Nets /USB_Jetson/CAN_H and /USB_Jetson/CAN_L run from connector J19 (pins 5 and 6, bottom right, ≈(184, 152)) to the TVS diode D12 (≈178.4, 152.7), then to transceiver U16 (≈181.4, 147.5, pins 7 = CANH and 6 = CANL), then to the 120 Ω resistor R53 (≈187.3, 144.4). Right now CAN_L reaches U16 before D12, which is wrong for ESD, and both have bits on B.Cu.

Delete both nets' existing tracks, then route them again on F.Cu only, the two tracks side by side (0.25 mm wide, 0.2–0.3 mm gap) the whole way, in the order J19 → D12 → U16 → R53. Use X for each track (route CAN_H first, then CAN_L right beside it). Check with Net Inspector that both nets have 0 mm on B.Cu. Then do the end-of-task checks.
```

**Task 4: RS-485 pair, smart port A**

```
Task: route smart port A's RS-485 pair as a pair. Nets /SmartPort_A/RS485_A and /SmartPort_A/RS485_B run from the 4P4C jack J1 (pins 1 and 2, left edge ≈(115, 127)) to transceiver U14 (≈127.5, 127.5; pin 6 = A, pin 7 = B), with branches to the 120 Ω resistor R51 (≈131.5, 132.4) and test pads TP8 (A) and TP9 (B).

Delete both nets' tracks, then route them on F.Cu only, side by side (0.25 mm, 0.2–0.3 mm gap): J1 → U14, then short branches to R51, TP8, TP9. Check Net Inspector shows 0 mm on B.Cu for both. Then do the end-of-task checks.
```

**Task 5: RS-485 pair, smart port B**

```
Task: same as for port A, but for nets /SmartPort_B/RS485_A and /SmartPort_B/RS485_B: jack J2 (pins 1 and 2, ≈(115, 140)) → transceiver U15 (≈127.5, 138.8; pin 6 = A, pin 7 = B), with branches to R52 (≈131.1, 134.7), TP11 (A) and TP12 (B). F.Cu only, side by side. Then do the end-of-task checks.
```

**Task 6: USB pair**

```
Task: route the USB data pair as a differential pair. Nets USB_D+ and USB_D- run from the 22 Ω resistors R38 (≈110.3, 120.5, pad 2) and R39 (≈114.1, 120.4, pad 2) to the MCU U3 pins 46 (D+) and 45 (D-), which are on U3's RIGHT side at about (164.7, 134.2) and (164.7, 134.8). Leave the short part between the USB-C connector J16, U13 and R38/R39 alone.

1. First set up the pair rule: File → Board Setup → Design Rules → Net Classes. Add a class "USB" with Track width 0.25, DP Width 0.25, DP Gap 0.2. In the Netclass assignments table below, add patterns USB_D+ and USB_D- with class USB. OK.
2. Move R39 (press M with it selected; it is not locked) so it sits right next to R38 with its pads parallel, about 1.5–2 mm apart, and re-route the two short tracks from U13 to them.
3. Delete all tracks and vias of USB_D+ and USB_D- between R38/R39 and U3 (USB_D- is mostly unrouted already; delete its stub and dangling via near (114.2, 122.3)).
4. Press 6, click R38's pad 2, and route the pair on F.Cu to U3 pins 46/45. Suggested path: east along y ≈ 119–120, below the row of small ESD chips, to about x = 167, then south to y ≈ 134 and in to the pins from the right. Shove mode will push other tracks aside; that's fine.
5. Check with Net Inspector: both nets 0 mm on B.Cu, lengths within 2 mm of each other. Then do the end-of-task checks; after this task DRC should be 0 / 0 / 0.
```

**Task 7 (repeat as needed): move bottom-layer tracks to the top**

```
Task: reduce signal tracks on B.Cu. Open Inspect → Net Inspector and sort by B.Cu length. Skip GND. Take the first [3] nets in the list (tell me which).

For each net: highlight it, select its B.Cu track segments (click, then U), delete them, and re-route the gap on F.Cu. Where it must cross another F.Cu track, use the shortest possible B.Cu hop (V to drop a via, a short straight track at right angles, V again to come back up) and keep each hop under 5 mm.

Long runs along the very edge of the board are acceptable on B.Cu; runs across the middle are not. After each net, press B and run DRC; fix anything you caused before starting the next net. Report each net's B.Cu length before and after. Then do the end-of-task checks.
```

**Task 8: GND vias at ground pads**

```
Task: add a GND via next to ground pads that have none within about 1.5 mm. For each pad in this list: start a track from the pad with X, go about 1 mm away from the part on F.Cu, press V to place a via, and finish (double-click). The via takes the GND net. Keep it clear of other tracks (DRC will tell you).

Pads: [paste the list from HAND_ROUTING.md step 7, or ask Claude Code for the current list]

Then do the end-of-task checks.
```

**Task 9: two silkscreen labels**

```
Task: add two silkscreen labels. Place → Add Text, layer F.Silkscreen, text height 0.8 mm, thickness 0.15 mm. Text "J14 AUX1" next to connector J14 (right edge, ≈(200, 116.7)) and "J18 I2C" next to J18 (≈(200, 127.5)), each where it's clearly beside its own connector, not over any pad and not under a connector body. If there is no room on the top, put them on B.Silkscreen behind the connectors instead (mirrored text is fine on the bottom). Then do the end-of-task checks.
```

## Tips if it struggles

- If Claude misreads which pad it's on, ask it to hover the pad and read the net name in the bottom message panel before clicking.
- If a route keeps failing, have it hide B.Cu (eye icon) and zoom in further.
- If a session goes badly, close KiCad without saving, `git checkout centurion.kicad_pcb`, and restart that task in a fresh conversation.
- Ask Claude Code to "measure the board" after a few tasks to see the numbers move.
