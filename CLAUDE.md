# Notes for Claude sessions in this repo
Start with `HANDOVER.md` (state, rules, next steps), then `G1_CHECKLIST.md` and `PLAN.md`.
Key rules: never modify `Corteil/ace_commander` (the EMF build) without Brian's go-ahead; `vendor/` is a
read-only upstream snapshot (change it only via `tools/patches.py`); never commit `ship_data.py` /
`game_data.py`; keep `python tests/run_all.py` green; no custom firmware builds.
