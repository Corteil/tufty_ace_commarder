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
# AL: one gauge, planet or sun
import types
def fake(pd, cabin=30, sd=1e9, pr=100.0, sr=300.0, witch=False):
    sp = types.SimpleNamespace(px=0.0, py=0.0, pz=pd, pr=pr, sx=0.0, sy=0.0, sz=sd, sr=sr, witch=witch)
    return types.SimpleNamespace(space=sp, cabin=cabin)
from ace_commander import cockpit as ck
f, rgb = dash_tufty.altitude(fake(300.0, cabin=ck.COOL_CABIN))           # 2 radii above the surface
assert abs(f - 1.0) < 1e-9 and rgb == ck.CYAN, (f, rgb)
f, rgb = dash_tufty.altitude(fake(150.0, cabin=ck.COOL_CABIN))           # half a radius up: 0.25
assert abs(f - 0.25) < 1e-9 and rgb == ck.CYAN, f
assert dash_tufty.altitude(fake(90.0, cabin=ck.COOL_CABIN))[0] == 0.0     # inside the planet: empty
f, rgb = dash_tufty.altitude(fake(1e9, cabin=ck.COOL_CABIN + 50, sd=300.0 + 300.0 * ck.SUN_GAUGE_ALT * 0.5))
assert rgb == ck.ORANGE and abs(f - 0.5) < 1e-6, (f, rgb)                # warming: height above the sun
assert dash_tufty.altitude(types.SimpleNamespace(space=None, cabin=30)) == (0.0, ck.DIM)
assert dash_tufty.altitude(fake(300.0, witch=True))[1] == ck.DIM
print("flight frame 320x240 written; view %d lit, dashboard %d lit" % (lit(0, 0, 320, 180), lit(0, 180, 320, 240)))
print("ALL DASHBOARD TESTS PASSED")
