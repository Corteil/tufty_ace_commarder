# Handover: hardware session (Tufty 2350 + Qw/ST Pad on the Raspberry Pi)

For the next Claude session, run on the same Raspberry Pi Brian uses for EMF badge development,
with the Tufty and Pad physically connected. Read this first, then `G1_CHECKLIST.md`, then `PLAN.md`.

## Goal of this session
Get Ace Commander running on the real Tufty 2350 with the Pad, and correct every place the code
assumed Badgeware behaviour that the real badge does not have (step G1 in PLAN.md).

## Ground rules (Brian's decisions, do not change without asking)
- All Tufty work stays in this repo (`Corteil/tufty_ace_commarder`; the spelling "commarder" is deliberate).
- **Do not touch `Corteil/ace_commander` (the EMF badge build)** until Brian gives the go-ahead. The
  local snapshot in `vendor/` is read-only; changes to upstream code go through `tools/patches.py`
  (build-time text patches, which fail loudly if upstream changes).
- The EMF screen layout must not change unless an improvement is proposed with before/after shots and he agrees.
- No custom firmware builds. Code in MicroPython/CircuitPython/Python.
- Elite-derived data (`ship_data.py`, `game_data.py`) must never be committed (gitignored upstream;
  the game falls back to its own `original_*` data).
- Commit messages end with the Co-Authored-By / Claude-Session lines from the session's attribution reminder.

## State of the code (all verified on a PC simulator only, never on hardware)
- Upstream `ace.py` runs **unmodified** through `apps/ace_commander/tufty_firmware.py` (stand-ins for
  Tildagon firmware: buttons, event bus, 12-LED ring, app base class) and `platform_tufty.py` (main loop,
  Tufty + Pad button maps, LED mirroring, hooks that swap in the Elite-style flight screen).
- `ctx_badgeware.py` implements the Tildagon `ctx` drawing calls on Badgeware's `screen` (raster lines,
  triangle-fan fills, integer text scale).
- `pkg/dash_tufty.py`: 320x180 3D view + 320x60 dashboard (SH EN FU LT | SP CT AL bars, scanner, compass,
  missile column, S and E lamps), LED ring painted as a border round the view.
- Launch/docking tunnel fills 320x240; stardust spread widened via patch (`DUST_X`). Docked, menu and chart
  screens still use the centred 240 layout. FOCAL is unchanged, so the horizontal FOV is wider than on the badge.
- Build: `python tools/build_app.py` -> `build/deploy/apps/ace_commander/` (entry files + package `acepkg/`).
  Tests: `python tests/run_all.py` (6 files, all pass; needs Pillow). `tests/shots/` holds renders.
- `sim/badgeware.py` is a Pillow fake of the **documented** Badgeware API; where it guessed, it is marked
  "ASSUMED". Real hardware overrides it: when behaviour differs, fix the code *and* the sim, then the tests.

## Known unknowns to resolve first (cheapest first)
1. How the launcher starts an app: `__init__.py` imported as a module vs run as a script, whether the app
   must call `badge.update()` itself or the launcher does (probe prints `LOOP_MODE`), and what `__file__` is.
2. How an app returns to the launcher (HOME?). The game's exit only stops our loop (`App.quit`).
3. Qw/ST I2C pins and bus on the Tufty (code assumes GP4/GP5 on I2C0, **a guess**), Pad address 0x21, and
   whether `qwstpad` is in the firmware (else copy it from github.com/pimoroni/qwstpad-micropython).
4. Resolution mode (320x240 vs 160x120), default text height (`NATIVE_TEXT_H = 10` assumed), whether
   `screen.circle` is filled, the `screen.triangle` signature, `badge.caselights()` argument form.
5. Speed: raster `screen.line` vs `shape.line`, and ms per flight frame (game Settings has an "ms" overlay).
6. Whether the app folder is writable (commander save files).

## Working on the Pi
Brian's Pi setup was not recorded in this repo; check rather than assume.
- Check what is there: `python3 --version`, `pip list | grep -i -E "pillow|mpremote|thonny"`, `ls ~` and the
  EMF badge tooling already in use (e.g. `mpremote`, `mip`, `rshell`). Reuse the tools he already has.
- Clone: `gh repo clone Corteil/tufty_ace_commarder` (or `git clone https://github.com/Corteil/tufty_ace_commarder`).
- Tests need Pillow only: `pip install pillow --break-system-packages` if missing.
- Serial access to the badge: it shows up as `/dev/ttyACM*`; the user must be in the `dialout` group. Check
  `ls /dev/ttyACM*` before and after plugging in the Tufty, since the EMF badge uses the same device names:
  **unplug the EMF badge or confirm which port is which**, and use the Tufty's port explicitly.
- Typical loop: `python tools/build_app.py`, copy `build/deploy/apps/ace_commander/` to the badge's `/apps/`
  (mpremote `fs cp -r`, or mount as a drive if the Tufty exposes one), run it, watch the REPL for tracebacks,
  fix, repeat. Keep the probe (`apps/ace_test`) on the badge for hardware questions.
- Don't flash firmware or erase the badge's filesystem; if a launcher or firmware update seems needed, ask Brian.

## Suggested order
1. Run `apps/ace_test`, record every answer in `G1_CHECKLIST.md` (add a "Results" section), and update
   `sim/badgeware.py` and the ASSUMED values to match.
2. Fix the entry/loop/exit behaviour; get the title screen on the real display.
3. Pad input, then flight, then speed work (only after measuring).
4. Commit small and often; keep `python tests/run_all.py` green.
5. Only when Brian asks: the EMF refactor path in PLAN.md (applies the same patches to `ace_commander`).

## Open design items (optional, ask first)
- Lock indicator on the missile lamps; a fourth row on the dashboard's right side.
- Keebdeck Basic keypad support; 320-wide layouts for docked/chart screens; FOCAL for the wider view.
- Known sizing leftovers: explosion extents and the pause menu are still drawn at the 240 scale.

## Brian
GitHub `Corteil`; maker/embedded; prefers Python/MicroPython/CircuitPython. Likes decisions shown as renders
and explained briefly. He has asked that proposals which change the EMF design come with before/after images.
