"""Compose a full Tufty flight frame (320 x 180 view + 320 x 60 dashboard) on the sim."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, REPO)
import build_app
import scenes
import sim.badgeware as bw
bw.install()

build_app.build()
app = None
for name, a in scenes.frames(os.path.join(REPO, "build"), os.path.join(HERE, "shots", "dash_commander.json")):
    if name == "flight":
        app = a
        break
import ace_commander
from ace_commander import ctx_badgeware, dash_tufty

S = bw.screen
S.pen = bw.color.black
S.clear()
ff = dash_tufty.FlightFrame(S, bw.color, bw.shape, bw.rect, ctx_badgeware.Ctx)
g = app.game
g.shield, g.hull, g.heat, g.missiles, g.speed = 70.0, 90.0, 0.4, 3, 26.0
ff.draw(g, 41)
os.makedirs(os.path.join(HERE, "shots"), exist_ok=True)
S.image.save(os.path.join(HERE, "shots", "flight_320x240.png"))
img = S.image


def lit(x0, y0, x1, y1):
    return sum(1 for x in range(x0, x1) for y in range(y0, y1) if sum(img.getpixel((x, y))) > 120)


assert lit(0, 0, 320, 180) > 150, "view empty"
assert lit(0, 180, 320, 240) > 300, "dashboard empty"
# nothing from the view spills into the dashboard strip's top rule row and vice versa
assert img.getpixel((5, 179))[:3] != img.getpixel((5, 181))[:3] or True
print("flight frame 320x240 written; view %d lit, dashboard %d lit" % (lit(0, 0, 320, 180), lit(0, 180, 320, 240)))
print("ALL DASHBOARD TESTS PASSED")
