"""PC stand-in for the Badgeware API, drawn with Pillow. Only what badgewa.re documents.

Documented (read 2026-11-16):  image.md, color.md, badge.md, buttons.md, vector_shapes.md.
Marked ASSUMED where the docs were silent; check those against a real badge (gate G1).

    import sim.badgeware as bw
    bw.install()                 # puts screen, color, badge, shape, BUTTON_* in builtins
    screen.pen = color.white
    screen.line(0, 0, 100, 50)   # raster line: ints, rounded, not antialiased
    badge.update()               # presents the frame, then clears and reads buttons
    bw.save("frame.png")
"""
import builtins
import time

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 320, 240            # Tufty 2350 panel. ASSUMED: the OS may expose a smaller mode.

BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_UP, BUTTON_DOWN, BUTTON_HOME = (
    "BUTTON_A", "BUTTON_B", "BUTTON_C", "BUTTON_UP", "BUTTON_DOWN", "BUTTON_HOME")
BUTTONS = (BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_UP, BUTTON_DOWN, BUTTON_HOME)


class rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


class _Color(tuple):
    pass


class color:
    @staticmethod
    def rgb(r, g, b, a=255):
        return _Color((int(r), int(g), int(b), int(a)))

    # DawnBringer-16 members the docs name; the rest of the 16 are not listed there.
    black = rgb.__func__(0, 0, 0)
    white = rgb.__func__(255, 255, 255)
    red = rgb.__func__(208, 70, 72)          # ASSUMED value (DB16 red)
    navy = rgb.__func__(52, 101, 136)   # ASSUMED value
    cyan = rgb.__func__(109, 194, 202)       # ASSUMED value


class font:
    smart = "smart"                           # ASSUMED to exist (used by the docs' first-app example)


class _Screen:
    def __init__(self):
        self.width, self.height = WIDTH, HEIGHT
        self.image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        self.pen = color.white
        self.font = font.smart
        self.clip = rect(0, 0, WIDTH, HEIGHT)
        self.antialias = 0
        self._d = ImageDraw.Draw(self.image)
        self._font = ImageFont.load_default()
        self.calls = 0                         # drawing calls since the last badge.update()

    def _rgb(self):
        return tuple(self.pen[:3])

    def _clipped(self, draw):
        c = self.clip
        if (c.x, c.y, c.w, c.h) == (0, 0, WIDTH, HEIGHT):
            draw(self._d)
            return
        scratch = self.image.copy()            # draw on a copy, keep only the clip area
        draw(ImageDraw.Draw(scratch))
        box = (c.x, c.y, c.x + c.w, c.y + c.h)
        self.image.paste(scratch.crop(box), box)

    def clear(self):
        self._d.rectangle([0, 0, WIDTH, HEIGHT], fill=self._rgb())
        self.calls += 1

    def rectangle(self, x, y, w, h):          # filled; ASSUMED filled (docs: "built-in drawing methods")
        x, y, w, h = (round(v) for v in (x, y, w, h))
        self._clipped(lambda d: d.rectangle([x, y, x + w - 1, y + h - 1], fill=self._rgb()))
        self.calls += 1

    def circle(self, x, y, radius):           # ASSUMED filled
        x, y, r = round(x), round(y), round(radius)
        self._clipped(lambda d: d.ellipse([x - r, y - r, x + r, y + r], fill=self._rgb()))
        self.calls += 1

    def line(self, x0, y0, x1, y1):           # 1 px, rounded to ints
        p = tuple(round(v) for v in (x0, y0, x1, y1))
        self._clipped(lambda d: d.line(p, fill=self._rgb(), width=1))
        self.calls += 1

    def measure_text(self, message, size=None):   # documented: returns (width, height) for the current font
        l, t, r, b = self._font.getbbox(str(message))
        return (r - l, 10)                         # ASSUMED native pixel-font height of 10

    def text(self, message, x, y, size=None):     # x, y = top-left (documented); size = integer scale (pixel fonts)
        k = max(1, int(size or 1))
        w, h = self.measure_text(message)
        tmp = Image.new("L", (max(1, w), h), 0)
        ImageDraw.Draw(tmp).text((0, 0), str(message), fill=255, font=self._font)
        if k > 1:
            tmp = tmp.resize((tmp.width * k, tmp.height * k), Image.NEAREST)
        x, y = round(x), round(y)
        col = self._rgb()

        def draw(d):
            self_img = d._image
            self_img.paste(Image.new("RGB", tmp.size, col), (x, y), tmp)
        self._clipped(draw)
        self.calls += 1
        return rect(x, y, tmp.width, tmp.height)

    def triangle(self, x0, y0, x1, y1, x2, y2):   # ASSUMED signature; docs name triangle as a raster primitive
        pts = [(round(x0), round(y0)), (round(x1), round(y1)), (round(x2), round(y2))]
        self._clipped(lambda d: d.polygon(pts, fill=self._rgb()))
        self.calls += 1

    def shape(self, s):                       # shape.line(...) etc. Vector path, slower on real hardware
        s(self)
        self.calls += 1


class shape:
    @staticmethod
    def line(x1, y1, x2, y2, t=1):
        def draw(scr):
            scr._clipped(lambda d: d.line((x1, y1, x2, y2), fill=scr._rgb(), width=max(1, round(t))))
        return draw


class _Badge:
    def __init__(self):
        self._down = set()
        self._prev = set()
        self._pending = set()
        self.frames = 0
        self.led = [0.0] * 4
        self.model = "tufty"
        self.resolution = (WIDTH, HEIGHT)
        self._t0 = time.monotonic()

    @property
    def ticks(self):
        return int((time.monotonic() - self._t0) * 1000)

    # test hook, not part of Badgeware
    def sim_set_buttons(self, *names):
        self._pending = set(names)

    def update(self):
        self.frames += 1
        screen.calls = 0
        self._prev, self._down = self._down, set(self._pending)

    def _q(self, names, button):
        return list(names) if button is None else button in names

    def held(self, button=None):
        return self._q(self._down, button)

    def pressed(self, button=None):
        return self._q(self._down - self._prev, button)

    def released(self, button=None):
        return self._q(self._prev - self._down, button)

    def changed(self, button=None):
        return self._q(self._down ^ self._prev, button)

    def caselights(self, *levels):
        if levels:
            self.led = [float(levels[0])] * 4 if len(levels) == 1 else [float(v) for v in levels]
        return list(self.led)


screen = _Screen()
badge = _Badge()


def save(path):
    screen.image.save(path)


def install():
    """Expose the Badgeware globals the way the launcher does."""
    for name, val in (("screen", screen), ("badge", badge), ("color", color), ("shape", shape),
                      ("font", font), ("rect", rect)):
        setattr(builtins, name, val)
    for b in BUTTONS:
        setattr(builtins, b, b)
    if not hasattr(time, "ticks_ms"):          # MicroPython's time helpers
        time.ticks_ms = lambda: int(time.monotonic() * 1000)
        time.ticks_diff = lambda a, b: a - b
