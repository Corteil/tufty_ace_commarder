"""Stand-ins for the Tildagon firmware modules that ace.py imports, so the game runs unchanged on Tufty.

Call install() BEFORE importing the game package. It puts these into sys.modules:
    app (App base class), events.input (BUTTON_TYPES, ButtonDownEvent, ButtonUpEvent),
    events.joystick, frontboards.common, system.eventbus (eventbus), tildagonos (a 12-LED ring
    that only records what was written), system.patterndisplay.events.

Button matching copies upstream's tests/badge_stubs.py, which copies the firmware's rules: a
physical button belongs to every button kind listed among its parents. The 2026 board's
buttons are composite, e.g. the joystick-up is both a system UP and a joystick UP.
Nothing here imports Pillow or anything PC-only: it must run on the badge.
"""
import sys


class Button:
    def __init__(self, name, group, parent=None):
        self.name = name
        self.group = group
        if isinstance(parent, Button):
            self.parents = [parent]
        elif parent is None:
            self.parents = []
        else:
            self.parents = parent

    def __hash__(self):
        return hash((self.name, self.group))

    def __eq__(self, other):
        return self.name == other.name and self.group == other.group

    @property
    def all_parents(self):
        out = []
        for p in self.parents:
            out.append(p)
            out += p.all_parents
        return out

    def __contains__(self, other):
        return other == self or any(other == p for p in self.all_parents)

    def __repr__(self):
        return "%s.%s" % (self.group, self.name)


TYPES = {k: Button(k, "System") for k in ("UP", "DOWN", "LEFT", "RIGHT", "CONFIRM", "CANCEL")}
FB = {k: Button(k, "Frontboard") for k in "ABCDEF"}
JOY = {k: Button(k, "Joystick") for k in ("UP", "DOWN", "LEFT", "RIGHT", "SELECT")}

# What a Tufty or Pad button counts as: the 2026 board's composite buttons (see badge_stubs.PHYSICAL).
PHYSICAL = {
    "A": Button("A", "TwentyTwentySix", [TYPES["UP"], FB["A"]]),
    "B": Button("B", "TwentyTwentySix", [TYPES["RIGHT"], FB["B"]]),
    "C": Button("C", "TwentyTwentySix", [TYPES["CONFIRM"], FB["C"]]),
    "D": Button("D", "TwentyTwentySix", [TYPES["DOWN"], FB["D"]]),
    "E": Button("E", "TwentyTwentySix", [TYPES["LEFT"], FB["E"]]),
    "F": Button("F", "TwentyTwentySix", [TYPES["CANCEL"], FB["F"]]),
    "JOYUP": Button("JOYUP", "TwentyTwentySix", [TYPES["UP"], JOY["UP"]]),
    "JOYDOWN": Button("JOYDOWN", "TwentyTwentySix", [TYPES["DOWN"], JOY["DOWN"]]),
    "JOYLEFT": Button("JOYLEFT", "TwentyTwentySix", [TYPES["LEFT"], JOY["LEFT"]]),
    "JOYRIGHT": Button("JOYRIGHT", "TwentyTwentySix", [TYPES["RIGHT"], JOY["RIGHT"]]),
    "JOYFIRE": Button("JOYFIRE", "TwentyTwentySix", [TYPES["CONFIRM"], JOY["SELECT"]]),
}


class ButtonDownEvent:
    requires_focus = True

    def __init__(self, button):
        self.button = button


class ButtonUpEvent:
    requires_focus = True

    def __init__(self, button):
        self.button = button


class App:
    """What the game's app class inherits: it only needs overlays and minimise()."""
    quit = False

    def __init__(self):
        self.overlays = []

    def minimise(self):
        App.quit = True          # the host's loop sees this and ends


class Bus:
    def __init__(self):
        self.handlers = {}
        self.emitted = []

    def on(self, event_type, handler, app):
        self.handlers.setdefault(event_type, []).append(handler)

    def remove(self, event_type, handler, app):
        try:
            self.handlers[event_type].remove(handler)
        except (KeyError, ValueError):
            pass

    def emit(self, event):
        self.emitted.append(type(event).__name__)
        if len(self.emitted) > 20:
            del self.emitted[0]

    def send(self, event):
        for h in self.handlers.get(type(event), []):
            h(event)


class Leds:
    """tildagonos.leds: 19 entries, the front ring is 1 to 12. Only records writes."""
    count = 19

    def __init__(self):
        self.values = [(0, 0, 0)] * 19
        self.writes = 0

    def __setitem__(self, i, rgb):
        self.values[i] = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def __getitem__(self, i):
        return self.values[i]

    def write(self):
        self.writes += 1

    def __len__(self):
        return 19

    def ring(self):
        return self.values[1:13]


class PatternDisable:
    pass


class PatternEnable:
    pass


bus = Bus()
leds = Leds()


def _module(name, **attrs):
    import types
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


def install():
    """Register the stand-ins. Safe to call again (starts from a clean bus and LEDs)."""
    global bus, leds
    bus = Bus()
    leds = Leds()
    App.quit = False
    _module("app", App=App)
    _module("events")
    _module("events.input", BUTTON_TYPES=TYPES, ButtonDownEvent=ButtonDownEvent, ButtonUpEvent=ButtonUpEvent)
    _module("events.joystick", JOYSTICK_BUTTON_TYPES=JOY)
    _module("frontboards")
    _module("frontboards.common", FRONTBOARD_BUTTON_TYPES=FB)
    _module("system")
    _module("system.eventbus", eventbus=bus)
    ns = type("T", (), {})()
    ns.leds = leds
    ns.set_led_power = lambda on: None
    _module("tildagonos", tildagonos=ns)
    _module("system.patterndisplay")
    _module("system.patterndisplay.events", PatternDisable=PatternDisable, PatternEnable=PatternEnable)
    for name in ("imu", "events.keyboard", "system.scheduler"):    # not on Tufty: the game copes without
        sys.modules.pop(name, None)
    return bus, leds
