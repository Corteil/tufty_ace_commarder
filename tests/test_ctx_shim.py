"""Draw the same upstream frames through upstream's Pillow ctx and through our Badgeware shim,
and check they look alike (lit pixels agree within one pixel). Frames are saved to tests/shots/.

Needs only the vendored upstream (own-data mode), Pillow, and the sim.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
VENDOR = os.path.join(REPO, "vendor")
sys.path.insert(0, os.path.join(VENDOR, "ace_commander", "tests"))
sys.path.insert(0, VENDOR)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "apps", "ace_commander"))

from PIL import Image, ImageChops, ImageFilter
import badge_stubs as bs
from badge_stubs import PilCtx
import sim.badgeware as bw
bw.install()
from ctx_badgeware import Ctx

OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)
bs.install()
import ace_commander
ace_commander.ace.SAVE_PATH = os.path.join(OUT, "shim_commander.json")
if os.path.exists(ace_commander.ace.SAVE_PATH):
    os.remove(ace_commander.ace.SAVE_PATH)
tick = bs.tick
game = ace_commander.ace.game


class Tee:
    """Sends every ctx call and setting to both back ends."""
    def __init__(self, a, b):
        object.__setattr__(self, "_t", (a, b))

    def __getattr__(self, name):
        a, b = self._t
        v = getattr(a, name)
        if callable(v):
            def call(*args, **kw):
                getattr(a, name)(*args, **kw)
                getattr(b, name)(*args, **kw)
                return self
            return call
        return v

    def __setattr__(self, name, value):
        for t in self._t:
            setattr(t, name, value)


def lit(img):
    return img.convert("L").point(lambda v: 255 if v > 40 else 0)


def near(mask):
    return mask.filter(ImageFilter.MaxFilter(3))


def compare(app, name):
    bw.screen.pen = bw.color.black
    bw.screen.clear()
    pil = PilCtx(1)
    mine = Ctx(bw.screen, bw.color, bw.shape, ox=160, oy=120)
    app.draw(Tee(pil, mine))
    a = pil.img
    b = bw.screen.image.crop((40, 0, 280, 240))
    la, lb = lit(a), lit(b)
    na, nb = sum(1 for v in la.tobytes() if v), sum(1 for v in lb.tobytes() if v)
    miss_b = sum(1 for x, y in zip(la.tobytes(), near(lb).tobytes()) if x and not y)   # in upstream, not ours
    miss_a = sum(1 for x, y in zip(lb.tobytes(), near(la).tobytes()) if x and not y)   # in ours, not upstream
    ca = 1 - miss_b / max(1, na)
    cb = 1 - miss_a / max(1, nb)
    side = Image.new("RGB", (240 * 2 + 4, 240), (40, 40, 48))
    side.paste(a, (0, 0))
    side.paste(b, (244, 0))
    side.save(os.path.join(OUT, "shim_" + name + ".png"))
    print("%-16s lit %5d/%5d  upstream-covered %.3f  ours-covered %.3f" % (name, na, nb, ca, cb))
    return ca, cb


results = {}
a = ace_commander.AceCommander()
for _ in range(60):
    tick(a)
results["title"] = compare(a, "title")
tick(a, fresh=["LEFT"])
bs.choose(a, "NEW COMMANDER")
tick(a, fresh=["CONFIRM"])
a.cmdr.add_kills(140)
results["docked"] = compare(a, "docked")
d = a.dock
d.open("GALACTIC CHART")
results["galactic"] = compare(a, "galactic")
d.open("SYSTEM DATA")
results["system"] = compare(a, "system_data")
d.go(0)
tick(a, fresh=["CONFIRM"])
a.launch_t = 0.6 * ace_commander.ace.LAUNCH_TIME
results["tunnel"] = compare(a, "tunnel")
a.launch_t = 99
tick(a)
g = a.game
g.spawn_t = g.rock_t = 1e9
g.objs[:] = []
o = game.Obj(g.types["COBRA MK III"], "ship", -120.0, 60.0, 900.0)
d3 = game._unit(0.6, -0.2, -0.75)
game._look(o.m, d3[0], d3[1], d3[2])
o.state = "break"; o.t = 99; o.aim = [0.6, -0.2, -0.75]
g.objs.append(o)
tick(a, held=["CONFIRM"], ms=40)
results["flight"] = compare(a, "flight")

# Text screens are judged loosely: the sim's stand-in font is not Tufty's font, so glyph
# shapes and sizes differ whatever the shim does. Graphics frames must agree closely.
TEXT_SCREENS = {"docked", "galactic", "system"}
bad = {k: v for k, v in results.items() if min(v) < (0.60 if k in TEXT_SCREENS else 0.90)}
assert not bad, "frames differ too much: %r" % bad
print("ALL CTX SHIM TESTS PASSED")
