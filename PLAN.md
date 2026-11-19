# Plan: Ace Commander on Tufty 2350 (and the later EMF badge update)

Status: P0 and P1 done on the PC 2026-11-16 (see Progress). **Updated 2026-11-18** for upstream v0.3.0 (see the next section). No Tufty or Pad run yet, so G1 is still the next hardware step.
Rule: **nothing in `Corteil/ace_commander` (EMF build) changes until Brian gives the go-ahead.** It is only read.

## Update 2026-11-18: upstream is now v0.3.0
`vendor/` is still the build-59 snapshot (22db6ef, 2026-11-15). Upstream has since released
v0.2.0 (builds 60-75) and v0.3.0 (builds 76-90, main at 8c8a37c / merge df89e06), and the
Hardcore Mode branch is merged, so the "don't sync from the branch" rule no longer applies.

**Trial sync (scratch copy, nothing committed):** `sync_from_ace.py` takes 69 files; all 11
patches in `tools/patches.py` still apply; `test_sim` and **`test_host` pass (the real v0.3.0
game runs title -> new commander -> docked -> launch -> flight on the Tufty stand-ins)**. Four
render tests fail:
- `test_patch_identity`, `test_view_rect`, `test_dashboard`: `tests/scenes.py` launches with C
  on Status; since build 77 **A launches** (C opens Options). One-line fix (`fresh=["A"]`).
- `test_ctx_shim`: the launch tunnel's coverage is 0.796 against the 0.90 bar (title and flight
  still agree). Look at the frame side by side before changing the bar: the tunnel now shows
  your own ship model (build 40) and the slot shapes changed (build 29); possibly a shim gap.

**What changed upstream and what it means here** (most of it is rules and needs nothing):
| Upstream (build) | Tufty impact |
|---|---|
| Buttons: A launches, C on Status opens Options; tabs Status, Inventory, Market, Equip ship, Shipyard, Hangar, charts; Repair Shop and ship stats are sub-screens; Inventory C sells all (70-82) | `PAD_MAP` still right (Pad + = A); fix `scenes.py`; check the new screens on the centred 240 layout |
| Old-firmware fallback removed (current firmware only): `events.joystick` and `frontboards.common` are required | already provided by `tufty_firmware.py` |
| Ship types (78-84): `Game.max_speed`, `max_missiles` (0-5 pylons), `fuel_max` (0-100, 0 = no hyperdrive), `turn_k`, `tough` | **`dash_tufty` must follow them**: SP bar against `g.max_speed` (not 40), missile lamps = `g.max_missiles` (a column of up to 5, none on the Worm/Shuttle), FU bar against `g.fuel_max` and blank when 0 (now `ck.MAX_FUEL`) |
| Four views and per-view stardust (60, 76) | `game.view_dust` uses its own +-500 / `DUST_MID` numbers, not patch 7's `DUST_X`: side and rear views won't fill 320 wide. New patch, or move the numbers into `DUST_X` upstream |
| Hardcore Mode (manual ECM: E+F together; armed missiles) | Pad X+Y together = ECM; check the Pad sends both in one frame |
| Keyboard keys (`k_*`) and text entry: Galactic chart search on B (88), commander NAME (89) | Tufty has no keyboard: the game falls back to its keyboard page, which a Pad can't type into. **Provide `app_components.dialog.TextDialog` in `tufty_firmware.py`**: a D-pad letter grid with the firmware's interface (`text`, `message`, `_result`, `_keys`, `masked`, `draw`); the game draws it with `find.small_dialog`. Register it to the host (upstream lesson, build 89: the real firmware only gives buttons to the focused app) |
| CONTROLS setting (87): flips flight pitch / roll; tilt gone on Tufty | nothing (the setting works on the D-pad) |
| Escape pods, stolen ships, police spotting, Elite weapon ranges (78-86) | rules only |
| LEDs: laser colours, ECM violet, jump flashes per view (60-76) | the LED border shows them; check the colours read on the border |
| Saves: commander version 5 (ship, hangar, name) | `commander.json` in the app folder: writability still unknown (G1) |

**Revised next actions**
1. Sync to v0.3.0 (`tools/sync_from_ace.py ~/Code/ace_commander` at main), fix `scenes.py`,
   look at the tunnel frame, keep the tests green.
2. `dash_tufty`: SP / missiles / FU from the ship (table above); a fifth missile lamp.
3. `TextDialog` stand-in for search and the name (D-pad letter grid).
4. `view_dust` width for the side views (patch, or upstream).
5. G1 on hardware (`G1_CHECKLIST.md`, unchanged).
6. **Repo layout: decided 2026-11-19 (Brian): A, one repo.** `Corteil/ace_commander` now has
   `hosts/` (left out of the badge's app store tarball) with the Raspberry Pi host in
   `hosts/pi/` (P0 merged, PR #23: the unchanged game on firmware stand-ins, as this repo's
   `tufty_firmware.py` does). **This port moves to `ace_commander/hosts/tufty/` after G1**: its
   stand-ins, shim, dashboard and build patches go there, the patches becoming real settings
   in the core (view size, `DUST_X`), and this repo is archived or kept as a pointer.
7. Since v0.3.0 (main at ac80435): build 91 fits eight Options lines on the round screen
   (docked and title pages; centred 240 layout here too), and build 92 makes the missile
   sights red only for a dangerous ship, white for a low-risk one, with one rule
   `cockpit.hostile(o)` shared with the radar. **`dash_tufty`'s scanner should call
   `cockpit.hostile`** rather than its own test, so the two badges colour ships alike.

## Progress
- **P0 done.** `tools/sync_from_ace.py` + `vendor/ace_commander/` (pinned in `vendor/UPSTREAM`, 57 tracked files, no Elite data). `sim/badgeware.py` is a PC fake of the documented Badgeware API; `tests/test_sim.py` checks it. `apps/ace_test` runs on the sim.
- **Baseline of the vendored upstream suite without Elite data: 9 of 18 test files pass, 9 fail**, identical to running it in the upstream clone. The failures all need `ship_data.py`/`game_data.py` or Elite names (e.g. start system LAVE, Cobra Mk III), so they can only be run where Brian has generated that data. The 9 passing ones are the equipment effects, traffic, witchspace, loader, original ships, original data, install, bench and run tests.
- **API finding that changes P1:** Badgeware's `screen` has raster `line(x0,y0,x1,y1)`, `rectangle(x,y,w,h)`, `circle(x,y,r)` (ints, rounded, not antialiased), a `clip` rectangle and `window()`. The ctx shim should use `screen.line` (not `shape.line`) and `clip` for the 3D view. Not yet confirmed on hardware: whether `circle` is filled, and the line speed.

- **P1a done (shim).** `apps/ace_commander/ctx_badgeware.py` implements the ctx calls the game uses on Badgeware's raster `screen` calls. `tests/test_ctx_shim.py` draws six upstream frames (title, docked, galactic chart, system data, launch tunnel, flight) through upstream's Pillow ctx and through the shim and compares them: flight, tunnel and title agree to within a pixel (94-100%); text screens only to about 73-86%, because the sim's stand-in font is not Tufty's. The shim found one real bug (thin 1 px radar axes rounding away), now fixed.
- **P1b done (patch layer).** `tools/build_app.py` copies the vendored game to `build/ace_commander/` and applies the documented edits in `tools/patches.py` (7 entries, each must match an exact count or the build stops). They make the 3D view size a setting (`cockpit.VIEW_HW`, `VIEW_HH`; defaults 120 and 120). `tests/test_patch_identity.py` proves that at the defaults all six frames are pixel-identical to upstream; `tests/test_view_rect.py` draws the world into a 320x180 view through the shim (planet, ship, nothing outside the view). Run all with `python tests/run_all.py`.
- **Known follow-ups from this step:** stardust and explosion extents in `game.py` are sized for the 240 view, so they will not fill 320 wide until patched too; the horizontal field of view widens at 320 with FOCAL unchanged (decide: keep or scale); the bomb flash is drawn by the old HUD function, so the dashboard must repeat it.
- **P1c done (dashboard).** `apps/ace_commander/dash_tufty.py`: Elite-style flight screen, 3D view 320x180 over a 320x60 dashboard (shield, energy and fuel bars left; speed, laser heat and cabin temperature right; 2x2 missile lamps; elliptical scanner with stalks and red hostiles; compass), plus the view overlay (crosshair, messages, game over, wave/score, bomb flash, sun gauges) that used to live in `draw_hud`. `FlightFrame` draws a whole frame on a Badgeware `screen` using the clip rectangle. `tests/test_dashboard.py` renders it on the sim (`tests/shots/flight_320x240.png`). Static labels redraw every frame, which may cost time on the badge: measure at G1.
- **Altitude gauge (Brian, 2026-11-16): one AL gauge for both dangers.** `dash_tufty.altitude()`: height above the planet (cyan, full at 2 radii = the safe-zone size, empty on the surface) and, while the cabin is warming, height above the sun (orange). Combat practice and witchspace show an empty dim bar. The old CT/AL pair at the top of the view is gone on Tufty; CT stays as a dashboard bar. Dashboard bars: left SH EN FU LT, right SP CT AL. Tufty only; EMF behaviour unchanged.
- **Dashboard changes (Brian, 2026-11-16):** missile lamps are a column of four between the left bars and the scanner; an **S lamp** (as in Elite's hub) lights green inside the station's safe zone (`Space.safe`). Open: an E lamp if the game gains an ECM; a lock indication on the missile lamps.
- **P1d done (host): upstream's real `ace.py` runs unmodified on Tufty's API.** Decision (Brian, 2026-11-16): instead of rewriting ace.py, `apps/ace_commander/tufty_firmware.py` stands in for the Tildagon firmware calls it makes (app base class, button events with the 2026 board's composite buttons, event bus, a 12-LED ring that records writes); `platform_tufty.py` is the loop (buttons -> game button events -> update -> draw -> `badge.update()`) and swaps `cockpit.draw_world/draw_hud` for the Elite-style frame. Deploy layout (`python tools/build_app.py` -> `build/deploy/apps/ace_commander/`): entry `__init__.py`, `icon.png`, `tufty_firmware.py`, `platform_tufty.py`, `ctx_badgeware.py`, and the game as package `acepkg/`. `tests/test_host.py` drives the real game on the sim: title -> new commander -> docked -> launch -> flight, with Tufty buttons and a fake Pad.
- **LEDs as a border (Brian's idea):** the 12 ring LED values the game writes are painted as a 3 px frame inside the 3D view (`dash_tufty.draw_led_border`, same LED angles as ace.py, so jump flashes appear on the side the streaks leave). Case lights follow the peak brightness; the Pad's 4 LEDs light on strong flashes. **E lamp** (ECM active, violet) added beside the S lamp.
- **Button map (edit in `platform_tufty.py`):** Pad D-pad = joystick; Pad A = C (fire/confirm/buy); Pad B = D (missile); Pad X/Y = F/E (speed up, back / slow down); Pad + = A (menu, launch); Pad - = B (bomb, sell). Tufty A/B/C = the same letters; Tufty UP/DOWN = F/E.
- **Jump / launch effects (2026-11-16):** hyperspace streaks and jump stardust already draw across the 320x180 view (checked on the sim). Fixed: the host now clears the screen every frame (the launch tunnel was drawing over the docked screen); launch and docking tunnels use the full 320x240 (`platform_tufty._draw_tunnel`); stardust spread is a setting (`game.DUST_X`, patch 7, 500 at Tildagon, 667 here). Not changed: FOCAL (horizontal FOV is wider, vertical narrower than the badge's), docked/menu/chart screens (still the 240 layout, centred).
- **Unverified until G1:** how Badgeware starts an app (entry runs `__init__.py` as a module and the loop never returns), `__file__` in the entry, how an app exits to the launcher (the game's exit only ends our loop), the Pad's I2C pins and driver import, `badge.caselights` argument form, and whether the app folder is writable (commander saves).
- **G1 checklist written (`G1_CHECKLIST.md`).** Docked/chart screens stay on the centred 240 layout (a 320 rewrite is cosmetic, ~50 hard-coded positions; deferred).
- **Still to do (P1 left-overs):** full-screen (320 wide) layouts for the other screens, and a first-run checklist for G1. The frame side-by-sides are in `tests/shots/` (not committed).

## What exists (read from ace_commander, build ~56)
- About 8,000 lines of game plus 6,000 of tests. Full game: title, commander and saves, galaxy, charts, market, equipment, docking, missions, witchspace.
- **Rules have no badge imports** and run on a PC: `game`, `galaxy`, `commander`, `market`, `equipment`, `missions`, `describe`, `content`, `original_data`, `original_ships`, `letters`.
- **Drawing uses a canvas-style `ctx`** on a 240x240 screen with the origin at the centre: `cockpit`, `docked`, `chart`, `title`, `viewer`, `bench`, `briefing`. About 20 distinct ctx calls are used (rgb, rectangle, move_to/line_to/stroke, text, arc, fill).
- **Tildagon-specific code is confined to `ace.py`** (input via the event bus, 12-LED ring, IMU tilt, loop, PERF logging) and `app.py` (loader).
- Elite-derived data (`ship_data.py`, `game_data.py`) is generated locally and **gitignored**. The game's own data (`original_*`) is committed and used when those are missing. Same rule here: never commit generated Elite data.
- Measured on the Tildagon: about 40-50 ms a frame, GC hitches from float garbage, a line costs about 0.35 ms, text about 4 ms.

## Target (Tufty 2350 + Qw/ST Pad)
- 320x240 screen (Badgeware may default to a lower-resolution mode and scale: check), RP2350 dual core, PSRAM, 16 MB flash.
- App = folder in `/apps` with `__init__.py` and `icon.png`; the app draws with `screen`/`shape`/`color`/`badge`. Pad driver `qwstpad` (MIT).
- Inputs: 5 front buttons (A, B, C, UP, DOWN) + Pad (U D L R A B X Y + -). No joystick, IMU or keyboard, so tilt steering is dropped.
- Outputs: 4 case lights (`badge.caselights`), 4 Pad LEDs (`set_leds`). Ring LEDs map to these.

## Flight screen layout (decided 2026-11-16): mirror BBC Elite
Brian's requirement: the game display mirrors the BBC Elite screen as closely as possible, with the **radar (scanner) underneath the space view**.
- The BBC screen is 4:3 like the Tufty's 320x240, so it scales by an even 1.25.
- **Space view on top, dashboard underneath.** Working numbers: view 320x180, dashboard 320x60 (BBC 256x144 over 256x48, scaled 1.25; check the original split before fixing). Both are constants, easy to tune.
- **Scanner (radar) centred in the dashboard**, drawn as the elliptical 3D scanner with blips and stalks, hostile ships in red (as the EMF build). Compass beside it.
- **Gauges left and right of the scanner** as the BBC dashboard: shields (fore/aft), fuel, cabin and laser temperature, altitude on one side; speed, roll, pitch and the four energy banks on the other; missile indicators.
- Docked screens, charts and the title use the full 320x240 (BBC-style full-width text screens), not the old 240x240 box.
- Our own drawing only: the layout follows the original, but no bitmaps, fonts or art copied from it.

## Architecture
```
tufty_ace_commarder/
  apps/ace_commander/        # what gets copied to the badge
    core/ or flat copies of the rules modules (vendored, see Sync)
    platform_tufty.py        # input, LEDs, clock, storage, loop
    ctx_badgeware.py         # ctx shim over screen/shape
    __init__.py, icon.png
  apps/ace_test/             # hardware probe (exists)
  sim/                       # PC fakes of screen/shape/color/badge + Pillow renderer
  tools/sync_from_ace.py     # copy rules + UI modules from a pinned ace_commander commit
  tests/                     # existing suite, run against sim
  PLAN.md
```
Platform contract (what each host must provide): `Display` (the ctx subset), `Input` (the logical actions: pitch/roll axes, fire, missile, speed up/down, menu, confirm/back, bomb), `Leds` (hit, safe, tunnel pulses), `Store` (commander.json), `Clock`.

## Phases

### P0 - Set up, no hardware (start now)
1. `sync_from_ace.py`: copies a pinned commit's rules, UI modules and tests; records the commit hash in `UPSTREAM`.
2. `sim/`: fake Badgeware (`screen`, `shape`, `color`, `badge`, `io`) drawing with Pillow, plus a fake Pad. Get the existing test suite and `render.py` shots running against it.
3. Check each Badgeware API call against the docs and the web playground (try.badgewa.re) before relying on it.
4. Licensing check: Elite data stays local and gitignored; confirm the Tufty repo's visibility.
Done when: the upstream tests pass on a PC inside this repo.

### P1 - Playable on the sim, in the Elite layout (needs only code)
1. `ctx_badgeware.py`: implements the ~20 ctx calls on `screen`: path segments drawn with raster `screen.line`, rectangles with `screen.rectangle`, arcs with `screen.circle` or line segments, text with `screen.text`; settable origin and the `clip` rectangle for the view. Thick lines (ctx.line_width > 1) need a plan: several offset raster lines, or `shape.line` for those only.
2. **View rectangle.** Parameterise `cockpit.py`: the world is drawn into a view of `VW x VH` centred at `(VX, VY)` instead of the fixed 240x240 centred on 0,0 (about 15 hard-coded 120/240 sites: culling, dust, explosions, tunnel, flash fills).
3. **New dashboard** (`dash_tufty.py`) replaces `draw_hud` on Tufty: scanner under the view, gauges either side. Built from rectangles and a few lines (rectangles are the cheap call), whole-number maths.
4. `platform_tufty.py`: logical actions from Tufty buttons + Pad; LEDs mapped to case lights and Pad LEDs.
5. Other screens use the full 320x240 via a screen-size constant.
Done when: sim frames for title, flight (with scanner and gauges), launch and docking tunnels, and docked screens look right at 320x240.

### G1 - First hardware run (when a Tufty and Pad are available)
Run `apps/ace_test`: resolution/mode, ms per frame, `shape.line` cost, I2C pins, `qwstpad` import, Pad bits, and whether the launcher calls `update()` or runs a loop. Fix P1 assumptions from the results.

### P2 - Controls
Default mapping (change after trying): Pad D-pad pitch/roll; Pad A fire; Pad B missile; Pad X/Y speed up/down; Pad + menu; Pad - bomb; Tufty buttons as spares (back, confirm, view). D-pad is digital, so add ramped turn rate and ease-out. Docked tabs: L/R change tab, U/D move lists, A confirm, B back. Charts: D-pad moves the cursor, Tufty UP/DOWN steps screens. Drop the tilt option.

### P3 - Polish the Elite look
Scanner details (ellipse grid, stalks, enemy colours), gauge ticks and colours, compass, missile indicators, text screens spaced for 320 wide. The Tildagon layout is not touched (see the EMF section).

### P4 - Speed on RP2350
Measure in the real loop, then: whole-number maths in hot loops (already largely done upstream), `@micropython.native/viper` for projection and clipping, batch lines, text caching for static screens, and check GC behaviour with a larger heap. Option: second core for rules, only if profiling says so. Target 20+ fps in the busiest scene (station + planet + 12 ships).

### P5 - Optional extras
Keebdeck: needs alternative firmware and soldering for I2C, so it is later and optional (commander name entry, shortcuts). Multiple Pads for two-player or spare buttons: not planned.

## EMF badge update (only after go-ahead)
**The EMF screen layout does not change.** The current 240x240 round-screen design works; the Elite-style layout is Tufty only. Any EMF layout improvement is proposed separately, with before/after shots, and only done if Brian agrees it is better. The layout code is split per platform (`dash_tufty.py` for Tufty; the existing HUD stays the EMF one), so one cannot alter the other.
Goal: both badges built from one set of game files. Changes to `Corteil/ace_commander`, in order:
1. **No behaviour change.** Replace hard-coded 120/240 in `cockpit.py` and friends with a view rectangle and `W`/`H` constants set to the current values on the Tildagon (240x240 view, existing HUD). Check by rendering the existing test shots before and after: they must be pixel-identical, and move Tildagon-only code from `ace.py` into `platform_tildagon.py` behind the platform contract above.
2. Fold in any rule fixes and new tests found while porting.
3. Re-run the full test suite, compile every file with the badge's own `mpy-cross` (per CLAUDE.md), and have Brian run it on a badge. Say clearly that PC tests don't prove badge behaviour.
4. Choose the long-term layout (decision for Brian):
   - **A. Monorepo**: `ace_commander` holds `core/` plus `platform_tildagon/` and `platform_tufty/`; this repo becomes archived or a thin release repo. The EMF folder must still be called `ace_commander` and install to `/apps/ace_commander/`.
   - **B. Two repos with a sync script** (as now): less churn, but fixes must be copied across.
   Recommendation: A once P3 works.
5. Build numbers and `CLAUDE.md`/`DESIGN.md` updated; Tufty gets its own build counter.

## Risks and open questions
- Qw/ST pin numbers and whether the OS already owns that I2C bus: unknown until G1.
- 3D view shrinks to 320x180 (was 240x240): check that ships, station and planet still read well, and that the culling constants follow the view.
- `ctx` shim cost: path-to-line batching might be slow; P4 may replace it with native drawing.
- Badgeware resolution mode (low-res scaled vs 320x240) changes line quality and speed.
- Text-heavy docked screens were about 100 ms on the Tildagon; check on Tufty.
- RP2 floats are heap objects too: expect the same garbage pattern unless the hot loops stay integer.
- Pad has no analogue stick: steering feel needs tuning.
- Keebdeck not usable out of the box.
- The app hook (`update()` vs loop) is undocumented in the pages read.

## Next actions
1. P1 shim and host, tested on the sim (render the same scene through upstream's Pillow ctx and through the shim, and compare).
2. Dashboard (scanner and gauges) for the Elite layout.
3. Wait for hardware, then G1.
