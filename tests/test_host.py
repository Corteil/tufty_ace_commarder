"""Run upstream's real ace.py through the Tufty host on the PC sim: title -> new commander ->
docked -> launch -> flight, with the Tufty buttons and a fake Qw/ST Pad. No upstream test stubs
are used: only tufty_firmware, ctx_badgeware, dash_tufty and the sim."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "apps", "ace_commander"))
import build_app
import sim.badgeware as bw
bw.install()
build_app.build()
sys.path.insert(0, os.path.join(REPO, "build"))     # the package, called ace_commander here
import platform_tufty as pt
import tufty_firmware as fw


class FakePad:
    def __init__(self):
        self.state = {}
        self.leds = 0
        self.keys = "UDLRABXY+-"

    def read_buttons(self):
        return {k: bool(self.state.get(k)) for k in self.keys}

    def set_leds(self, mask):
        self.leds = mask


pad = FakePad()
buttons = {"A": bw.BUTTON_A, "B": bw.BUTTON_B, "C": bw.BUTTON_C, "UP": bw.BUTTON_UP, "DOWN": bw.BUTTON_DOWN}
host = pt.Host(bw.screen, bw.badge, bw.color, bw.shape, bw.rect, buttons, pad, pkg="ace_commander")
app = host.app
OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)


def step(n=1, ms=40, pad_keys=(), tufty=()):
    pad.state = {k: True for k in pad_keys}
    bw.badge.sim_set_buttons(*tufty)
    for _ in range(n):
        host.step(ms)
        bw.badge.sim_set_buttons(*tufty)       # the sim reads buttons at update()


def tap(pad_keys=(), tufty=()):
    step(1, pad_keys=pad_keys, tufty=tufty)
    step(1)


def shot(name):
    bw.screen.image.save(os.path.join(OUT, "host_" + name + ".png"))


# 1. title screen, then NEW COMMANDER with the Pad's A (-> the game's C = confirm)
step(30)
assert app.mode == "menu", app.mode
app.menu = app.choices().index("NEW COMMANDER")
tap(["A"])
assert app.mode == "level", app.mode
tap(["A"])
assert app.mode == "docked", app.mode
shot("docked")

# 2. launch with the Pad's + (-> the game's A = launch from Status)
tap(["+"])
assert app.mode == "launch", app.mode
tunnel_seen = False
for _ in range(200):
    step(1, ms=100)
    if app.mode == "launch" and app.launch_t > 1.0 and not tunnel_seen:
        tunnel_seen = True
        im = bw.screen.image
        lit = [x for x in range(320) if any(im.getpixel((x, y)) != (0, 0, 0) for y in range(0, 240, 2))]
        assert lit and lit[0] < 40, "launch tunnel is not using the full 320 width"
        assert all(im.getpixel((x, 12)) == (0, 0, 0) for x in range(100, 220)), "docked screen left behind the tunnel"
        shot("launch")
    if app.mode == "flight":
        break
assert tunnel_seen
assert app.mode == "flight", app.mode
g = app.game
g.spawn_t = g.rock_t = 1e9
g.objs[:] = []

# 3. controls: D-pad up is the joystick, X speeds up, A fires
step(1, pad_keys=["U"])
assert app.pad.held("j_up") and not app.pad.held("j_down")
step(1)
s0 = g.speed
step(15, pad_keys=["X"])
assert g.speed > s0, (s0, g.speed)
fired = lit_ring = False
for i in range(4):
    step(1, pad_keys=["A"])
    if g.beam > 0:
        if not fired:
            shot("flight_laser")
        fired = True
        lit_ring = lit_ring or any(c != (0, 0, 0) for c in fw.leds.ring())
assert fired, "laser did not fire"
assert lit_ring, "laser colour not on the LED ring"
step(6)
# Tufty's own buttons work too: A (menu) pauses
tap(tufty=["BUTTON_A"])
assert app.paused, "Tufty button A did not open the menu"
shot("flight_menu")
tap(tufty=["BUTTON_A"])
step(2)

# 4. hit flash -> red LEDs -> red border round the view, case lights and Pad LEDs follow
g.flash = 0.3
step(1)
assert max(c[0] for c in fw.leds.ring()) == 255
img = bw.screen.image
assert img.getpixel((160, 1)) == (255, 0, 0), img.getpixel((160, 1))
assert bw.badge.led == [1.0] * 4 and pad.leds == 15, (bw.badge.led, pad.leds)
shot("flight_hit")
g.flash = 0.0
step(8)
assert max(max(c) for c in fw.leds.ring()) < 255

# stardust spreads across the whole 320 wide view
g.jumping = True
xs = []
for _ in range(60):
    step(1)
    xs += [int(p[0]) * 208 // max(1, int(p[2])) for p in g.dust if p[2] > 30]
g.jumping = False
assert max(xs) > 120 and min(xs) < -120, (min(xs), max(xs))

# 5. the E lamp lights while the ECM is going; the S lamp follows the safe zone
from ace_commander import dash_tufty as dash
g.ecm_t = 1.0
step(1)
px = bw.screen.image.getpixel((160 + dash.E_X, 210 + dash.E_Y - 5))
assert px[2] > 200 and px[0] > 100 and px[1] < 50, px          # violet
g.ecm_t = 0.0
step(1)

# 6. leaving: the game's exit calls minimise(), which stops the loop
fw.App.quit = False
host.run(max_frames=host.frames + 3)
assert host.frames > 0
print("host drove the real game: title -> docked -> launch -> flight, %d frames" % host.frames)
print("ALL HOST TESTS PASSED")
