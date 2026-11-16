"""The patched cockpit draws its 3D view into a 320 x 180 rectangle (VIEW_HW 160, VIEW_HH 90)
through the Badgeware shim: the background fill covers exactly that rectangle, ships appear in it,
and with the clip set nothing lands outside."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "apps", "ace_commander"))
import build_app
import scenes
import sim.badgeware as bw
bw.install()
from ctx_badgeware import Ctx

build_app.build()
app = None
for name, a in scenes.frames(os.path.join(REPO, "build"), os.path.join(HERE, "shots", "view_commander.json")):
    if name == "flight":
        app = a
        break
import ace_commander
assert ace_commander.cockpit.__file__.startswith(os.path.join(REPO, "build")), ace_commander.cockpit.__file__

ace_commander.cockpit.VIEW_HW = 160
ace_commander.cockpit.VIEW_HH = 90
S = bw.screen
MARK = (0, 0, 120)
S.pen = bw.color.rgb(*MARK)
S.clear()
ctx = Ctx(S, bw.color, bw.shape, ox=160, oy=90)          # ctx (0, 0) = centre of the view
S.clip = bw.rect(0, 0, 320, 180)
ace_commander.cockpit.draw_world(ctx, app.game)
S.clip = bw.rect(0, 0, 320, 240)

img = S.image
assert img.getpixel((2, 2)) == (0, 0, 0) and img.getpixel((317, 177)) == (0, 0, 0), "view not filled"
assert img.getpixel((160, 185)) == MARK and img.getpixel((5, 200)) == MARK, "drew below the view"
lit = sum(1 for x in range(320) for y in range(180) if sum(img.getpixel((x, y))) > 120)
assert lit > 150, "nothing drawn in the view (%d lit)" % lit
img.save(os.path.join(HERE, "shots", "view_320x180.png"))
print("view 320x180: %d lit pixels inside, nothing outside" % lit)
print("ALL VIEW RECT TESTS PASSED")
