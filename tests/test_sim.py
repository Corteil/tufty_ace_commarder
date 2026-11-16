"""Checks the Badgeware stand-in behaves as documented (and nothing more)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sim.badgeware as bw

bw.install()
S = bw.screen


def px(x, y):
    return S.image.getpixel((x, y))


# clear + pen
S.pen = color.black
S.clear()
assert px(5, 5) == (0, 0, 0)

# raster line rounds floats to the nearest pixel, one pixel wide
S.pen = color.white
S.line(10.4, 10.4, 20.6, 10.4)
assert px(10, 10) == (255, 255, 255) and px(21, 10) == (255, 255, 255) and px(10, 12) == (0, 0, 0)

# rectangle x,y,w,h covers exactly w x h pixels
S.pen = color.red
S.rectangle(30, 30, 4, 3)
filled = sum(1 for x in range(25, 40) for y in range(25, 40) if px(x, y)[:3] == tuple(color.red[:3]))
assert filled == 12, filled

# clip restricts drawing
S.pen = color.cyan
S.clip = rect(100, 100, 10, 10)
S.rectangle(90, 90, 40, 40)
assert px(95, 95) == (0, 0, 0) and px(105, 105)[:3] == tuple(color.cyan[:3]) and px(115, 115) == (0, 0, 0)
S.pen = color.black                         # black drawn inside a clip must still draw
S.rectangle(100, 100, 5, 5)
assert px(102, 102) == (0, 0, 0)
S.clip = rect(0, 0, bw.WIDTH, bw.HEIGHT)

# shape.line goes through screen.shape and respects thickness
S.pen = color.white
S.shape(shape.line(150, 150, 170, 150, 3))
assert px(160, 149) == (255, 255, 255) and px(160, 151) == (255, 255, 255)

# buttons: pressed / held / released follow the last badge.update()
badge.sim_set_buttons(BUTTON_A)
assert not badge.held(BUTTON_A)             # nothing until update()
badge.update()
assert badge.pressed(BUTTON_A) and badge.held(BUTTON_A) and not badge.released(BUTTON_A)
badge.update()
assert not badge.pressed(BUTTON_A) and badge.held(BUTTON_A)
badge.sim_set_buttons()
badge.update()
assert badge.released(BUTTON_A) and not badge.held() and badge.changed(BUTTON_A)

# case lights: four, 0-1
badge.caselights(0.5)
assert badge.caselights() == [0.5] * 4

# frame can be saved
with tempfile.TemporaryDirectory() as d:
    bw.save(os.path.join(d, "f.png"))
    assert os.path.getsize(os.path.join(d, "f.png")) > 0

print("ALL SIM TESTS PASSED")
