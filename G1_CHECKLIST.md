# G1: first run on a real Tufty 2350 + Qw/ST Pad

Everything so far was checked on the PC sim against the *documented* Badgeware API. These steps
find out where the badge differs. Do them in order; each says what to send back.

## 0. Prepare
1. `python tools/build_app.py` -> `build/deploy/apps/ace_commander/` (the game) and copy `apps/ace_test/`
   (the probe) alongside it.
2. Plug the Tufty in over USB; it mounts as a drive, or use Thonny/mpremote. Copy both folders into `/apps/`.
3. Attach the Qw/ST Pad to the Qw/ST socket.

## 1. Probe (`ace_test`)  - answers most open questions in one go
Run it from the launcher. It shows: screen size, ms per frame, a spinning cube (A toggles raster
`screen.line` vs vector `shape.line`), an I2C scan, the Pad's raw bits, `qwstpad` import status, and
`LOOP_MODE`. Send back a photo/the text of each, especially:
- [ ] resolution (320x240 or 160x120 low-res?)
- [ ] frames per second with raster lines vs vector lines
- [ ] I2C scan: is `0x21` found? If the scan is empty, the pins in `ace_test` (GP4/GP5) are wrong:
      find the Qw/ST pins in Pimoroni's Tufty pinout and edit `apps/ace_test/__init__.py` and `platform_tufty._pad`
- [ ] does `import qwstpad` work? (If not, the driver is not in the firmware: copy `qwstpad.py` from
      github.com/pimoroni/qwstpad-micropython to `/lib` or the app folder)
- [ ] `LOOP_MODE`: does the launcher call `update()` for you, or run the file as a loop?

## 2. Ace Commander
Run it from the launcher. Check in this order and note the first thing that fails:
- [ ] starts (if not: the traceback; most likely `__file__`/sys.path in `__init__.py`, or `acepkg` import)
- [ ] title screen draws and reacts to Tufty A/B/C/UP/DOWN
- [ ] Pad buttons work (D-pad moves menus, A confirms, + launches)
- [ ] NEW COMMANDER -> docked -> launch tunnel -> flight; frame rate in flight (show with the game's
      Settings "ms" option)
- [ ] flight: radar and dashboard look right; LED border flashes red when hit; case lights follow it
- [ ] hyperspace jump streaks and stardust
- [ ] saving: quit to title, re-run, is the commander still there? (If not, the app folder may be read-only)
- [ ] leaving the app: does the game's exit return to the launcher? (HOME button should always work)

## 3. Likely fixes (by symptom)
| Symptom | Where to look |
|---|---|
| Colours wrong / washed out | `ctx_badgeware.Ctx.rgb` (0-1 -> 0-255) |
| Text too big/small | `NATIVE_TEXT_H` in `ctx_badgeware.py` |
| Lines look broken or slow | `ctx_badgeware.py` stroke (raster vs `shape.line`) |
| Circles/planets wrong | `circle` may be filled or outline only: see `Ctx.arc` |
| Triangles missing (filled sun/planet) | `triangle` signature in `Ctx.fill` |
| Frame rate low | `ms` figure: split world vs dashboard time; reduce stars/labels |
| Pad ignored | pins / address / I2C bus already used by firmware (`platform_tufty._pad`) |
| Wrong buttons | `TUFTY_MAP`, `PAD_MAP` in `platform_tufty.py` |

Send back what happened at each unchecked step and I'll fix the code against the real behaviour.

## Results, 2026-11-19 (Brian's Tufty, serial cf39515354ec6c00, on the Pi)
**Firmware:** it came with Badgeware v2.0.1 (bw-1.27.0, 2026-02-26), on which the probe stopped at
`font.smart` (v2 had only `font.load` and files in `/rom/fonts`). Updated (Brian asked) to **v3.1.1
with-filesystem** (bw-1.29.0, 2026-09-23) from github.com/pimoroni/tufty2350 (checksum checked;
`machine.bootloader()` then the UF2 on the RP2350 drive). Both `secrets.py` kept; backup in
`~/Code/tufty_backup_2026-11-19/`. v3 changed the API ("your custom apps will break"): fonts,
`screen.text`, alpha on the destination; an app ends with `run(update)` and the launcher calls
`update()` each frame (no `badge.update()` in it); `badge.mode(HIRES)` for 320x240.

Section 1 (probe), all on v3.1.1:
- [x] resolution: **320x240** with `badge.mode(HIRES)` (160x120 without)
- [x] frame time: **14 ms raster lines, 15 ms vector lines** (cube + text): vector (anti-aliased) is fine
- [x] I2C0 on GP4 / GP5: **0x21** (Qw/ST Pad) and 0x51; GP4 / GP5 were right
- [x] `import qwstpad`: **yes**, in the firmware; `QwSTPad(i2c, 0x21).read_buttons()` lists pressed buttons
- [x] Pad raw bits: idle `0000011110000000`, change when pressed
- [x] loop mode: `run(update)` (v3)
- Found: `screen.clear()` after `screen.pen = color.black` gave a **blue** background: check v3's clear
  / pen before porting the game's drawing (the game needs black).
- Careful: **BUTTON_A is GPIO7**; opening I2C on GP6 / GP7 dropped the Tufty off USB (RESET fixed it).
- Files: `/system` is read-only from MicroPython; apps are copied onto the TUFTY drive (double-tap
  RESET or the Mass Storage app), which the Pi mounts at `/media/pi/TUFTY` (`apps/<name>/`).

Next: section 2 needs the port brought to v3 (`ctx_badgeware.py`, `platform_tufty.py` loop as
`run(update)`, the sim updated to v3) and synced with the game (see ace_commander
`hosts/NEXT_SESSION.md`, part A).
