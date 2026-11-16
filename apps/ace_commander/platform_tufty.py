"""Runs Ace Commander on a Tufty 2350 (Badgeware), with the unmodified game (ace.py).

How it fits together
    tufty_firmware   stand-ins for the Tildagon firmware calls ace.py makes (buttons, event bus,
                     LED ring, app base class)
    ctx_badgeware    the Tildagon's ctx drawing calls, drawn with Badgeware's `screen`
    dash_tufty       the flight screen: 3D view + Elite-style dashboard + LED border
    this file        the loop: read buttons -> send the game button events -> update -> draw ->
                     show; also the Tufty and Pad button map and the Pad / case-light LEDs

Start with start(namespace) from the app's __init__.py (the namespace gives the Badgeware globals),
or build a Host yourself (the PC tests do).
"""
import sys

import tufty_firmware as fw
from ctx_badgeware import Ctx

PKG = "acepkg"        # the game's package name on the badge (the PC tests use "ace_commander")

# Which game button each Tufty button and Pad button stands for. Right-hand names are keys of
# tufty_firmware.PHYSICAL: A-F are the badge's lettered buttons, JOY* the joystick. Edit freely.
# The game's controls (DESIGN.md): joystick = pitch/roll and list moves; C = lasers/select/buy;
# D = missile; E / F = slow / speed up (F also back); A = menu / launch; B = bomb / sell.
TUFTY_MAP = {"A": "A", "B": "B", "C": "C", "UP": "F", "DOWN": "E"}
PAD_MAP = {"U": "JOYUP", "D": "JOYDOWN", "L": "JOYLEFT", "R": "JOYRIGHT",
           "A": "C", "B": "D", "X": "F", "Y": "E", "+": "A", "-": "B"}


class Host:
    def __init__(self, screen, badge, color, shape, rect, buttons, pad=None, pkg=PKG):
        """buttons: {"A": BUTTON_A, "B": ..., "C": ..., "UP": ..., "DOWN": ...} (the badge's
        constants). pad: a qwstpad.QwSTPad or None."""
        self.screen, self.badge, self.pad = screen, badge, pad
        self.buttons = buttons
        fw.install()                                  # before the game package is imported
        ace = __import__(pkg + ".ace", None, None, ("x",))
        ck = __import__(pkg + ".cockpit", None, None, ("x",))
        dash = __import__(pkg + ".dash_tufty", None, None, ("x",))
        self.ace, self.ck = ace, ck
        self.ctx = Ctx(screen, color, shape, ox=dash.SCREEN_W // 2, oy=dash.SCREEN_H // 2)
        self.ff = dash.FlightFrame(screen, color, shape, rect, Ctx, ring=fw.leds.ring)
        self.view_centre = (dash.SCREEN_W // 2, dash.VIEW_H // 2)
        self.centre = (dash.SCREEN_W // 2, dash.SCREEN_H // 2)
        self._ms = None
        # the game draws the flight view with cockpit.draw_world and draw_hud: swap in ours
        ck.draw_world = self._world
        ck.draw_hud = self._hud
        self.app = ace.AceCommander()
        self.down = set()
        self.last_level = -1.0
        self.last_pad_leds = -1
        self.frames = 0

    # drawing -------------------------------------------------------------------------------
    def _world(self, ctx, g):
        self.ff.world(g)

    def _hud(self, ctx, g, ms=None, ring=True):
        self.ff.hud(g, ms)
        ctx.ox, ctx.oy = self.view_centre       # the pause menu is drawn on the view

    # input ---------------------------------------------------------------------------------
    def _wanted(self):
        want = set()
        b = self.badge
        for name, const in self.buttons.items():
            if b.held(const):
                want.add(TUFTY_MAP[name])
        if self.pad is not None:
            try:
                for k, v in self.pad.read_buttons().items():
                    if v and k in PAD_MAP:
                        want.add(PAD_MAP[k])
            except Exception:
                self.pad = None                  # unplugged: carry on with the badge's buttons
        return want

    def poll(self):
        want = self._wanted()
        for n in sorted(self.down - want):
            fw.bus.send(fw.ButtonUpEvent(fw.PHYSICAL[n]))
        for n in sorted(want - self.down):
            fw.bus.send(fw.ButtonDownEvent(fw.PHYSICAL[n]))
        self.down = want

    # LEDs ----------------------------------------------------------------------------------
    def leds_out(self):
        level = max(max(c) for c in fw.leds.ring()) / 255.0
        if level != self.last_level:
            self.last_level = level
            try:
                self.badge.caselights(level)
            except Exception:
                pass
        mask = 15 if level > 0.5 else 0
        if self.pad is not None and mask != self.last_pad_leds:
            self.last_pad_leds = mask
            try:
                self.pad.set_leds(mask)
            except Exception:
                self.pad = None

    # one frame -----------------------------------------------------------------------------
    def step(self, ms):
        self.poll()
        self.app.update(ms)
        self.ctx.ox, self.ctx.oy = self.centre
        self.app.draw(self.ctx)
        self.leds_out()
        self.badge.update()                     # shows the frame, clears, reads the buttons
        self.frames += 1

    def run(self, max_frames=None):
        b = self.badge
        last = b.ticks
        while not fw.App.quit and (max_frames is None or self.frames < max_frames):
            now = b.ticks
            ms = min(100, max(1, now - last))
            last = now
            self.step(ms)


def _pad():
    try:
        from machine import I2C, Pin
        import qwstpad
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)     # ASSUMED Qw/ST pins: check at G1
        return qwstpad.QwSTPad(i2c, qwstpad.DEFAULT_ADDRESS, show_address=False)
    except Exception:
        return None


def start(ns):
    """ns: the app's globals (Badgeware puts screen, badge, color, shape and BUTTON_* there)."""
    buttons = {"A": ns["BUTTON_A"], "B": ns["BUTTON_B"], "C": ns["BUTTON_C"],
               "UP": ns["BUTTON_UP"], "DOWN": ns["BUTTON_DOWN"]}
    Host(ns["screen"], ns["badge"], ns["color"], ns["shape"], ns["rect"], buttons, _pad()).run()
