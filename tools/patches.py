"""Documented edits applied to the vendored upstream files by tools/build_app.py.

Each entry: (file, old, new, expected_count). The build stops if `old` is not found exactly
`expected_count` times, so an upstream change that moves these lines is noticed at once.

Purpose: make the 3D view's size a setting. Upstream hard-codes a 240x240 view centred on the
ctx origin (half-size 120). With VIEW_HW / VIEW_HH at their defaults (120, 120) every patched
line behaves exactly as before; tests/test_patch_identity.py proves that frame by frame.
These same edits are what the later (approved) refactor of Corteil/ace_commander would make.
"""

VIEW_FILL_OLD = "rectangle(-120, -120, 240, 240)"
VIEW_FILL_NEW = "rectangle(-VIEW_HW, -VIEW_HH, 2 * VIEW_HW, 2 * VIEW_HH)"

PATCHES = [
    # 1. the settings themselves
    ("cockpit.py",
     "NEAR = 30.0      # nothing closer than this is drawn\n",
     "NEAR = 30.0      # nothing closer than this is drawn\n"
     "# Half the 3D view's width and height in pixels, about the ctx origin. 120 and 120 is the\n"
     "# Tildagon's 240x240 view. Set both before drawing to use another size.\n"
     "VIEW_HW = 120\n"
     "VIEW_HH = 120\n",
     1),
    # 2. is a ship (or its box) wholly outside the view?
    ("cockpit.py",
     "    if sx - pr > 120 or sx + pr < -120 or sy - pr > 120 or sy + pr < -120:\n        return False\n",
     "    if sx - pr > VIEW_HW or sx + pr < -VIEW_HW or sy - pr > VIEW_HH or sy + pr < -VIEW_HH:\n        return False\n",
     1),
    # 3. the enemy beam: skip when its ground point is below the view; line runs to just past the bottom
    ("cockpit.py", "    if gy > 120:\n        return\n", "    if gy > VIEW_HH:\n        return\n", 1),
    ("cockpit.py", "    ctx.line_to(gx * 0.25, 126)\n", "    ctx.line_to(gx * 0.25, VIEW_HH + 6)\n", 1),
    # 4. a sphere (sun, planet) wholly outside the view
    ("cockpit.py",
     "    if x - r > 120 or x + r < -120 or y - r > 120 or y + r < -120:\n        return None\n",
     "    if x - r > VIEW_HW or x + r < -VIEW_HW or y - r > VIEW_HH or y + r < -VIEW_HH:\n        return None\n",
     1),
    # 5. does a circle cover the whole view?
    ("cockpit.py",
     "    x = abs(c[0]) + 120\n    y = abs(c[1]) + 120\n",
     "    x = abs(c[0]) + VIEW_HW\n    y = abs(c[1]) + VIEW_HH\n",
     1),
    # 6. whole-view fills: tunnel and world backgrounds, sun, planet, and the bomb flash
    ("cockpit.py", VIEW_FILL_OLD, VIEW_FILL_NEW, 5),
    # 7. stardust: how far sideways it is spread (500 is the Tildagon's; a wider view needs more)
    ("game.py", "WITCH_DUST = 3 ",
     "DUST_X = 500            # stardust spreads this far either side (500 fills the 240 wide view)\nWITCH_DUST = 3 ", 1),
    ("game.py", "[random.randint(-500, 500), random.randint(-500, 500),",
     "[random.randint(-DUST_X, DUST_X), random.randint(-500, 500),", 2),
    ("game.py", "p[0] = random.randint(-500, 500)", "p[0] = random.randint(-DUST_X, DUST_X)", 2),
    ("game.py", "abs(p[0]) > 700", "abs(p[0]) > DUST_X * 7 // 5", 1),
]
