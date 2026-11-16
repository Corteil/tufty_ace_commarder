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
