# tufty_ace_commarder

Port of Ace Commander (BBC Elite flight game) to the Pimoroni Tufty 2350 (Badgeware) with a Qw/ST Pad over I2C.

Separate from the EMF badge build (Corteil/ace_commander), which is not to be touched until the go-ahead.

## Layout
`vendor/ace_commander/` pinned upstream snapshot (`tools/sync_from_ace.py`), `sim/` PC fake of Badgeware, `apps/ace_test/` hardware probe, `PLAN.md` the plan.

## Status
P0 done (see PLAN.md). Step 1: `apps/ace_test` probes the platform (resolution, `shape.line` speed, Pad over I2C).

## Install
Double-tap RESET, open the TUFTY drive, copy `apps/ace_test` into `/apps`, eject, reset.

## Open questions
- Qw/ST I2C pins and whether the OS already owns the bus (assumed GP4/GP5, I2C0)
- Pad button-to-bit mapping (use the `diff` row)
- Whether the launcher calls `update()` or runs `__init__.py` as a loop (`LOOP_MODE`)
