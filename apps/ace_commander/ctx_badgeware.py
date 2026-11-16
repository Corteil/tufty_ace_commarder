"""A ctx (canvas) look-alike drawing with Badgeware's raster calls.

Ace Commander's drawing code is written for the Tildagon's ctx on a 240x240 screen with
the origin at the centre. This class accepts the same calls and draws them on Tufty's
`screen`, with ctx (0, 0) placed at pixel (ox, oy).

Only the ctx calls the game uses are implemented (found by grep in upstream):
rgb, rgba, begin_path, move_to, line_to, rectangle, arc, fill, stroke, text, save,
restore, and the settable font_size, line_width, text_align, text_baseline.

Choices, all open to correction after the first hardware run (gate G1):
- lines are raster `screen.line` (ints, 1 px); thicker ones use `shape.line` (vector)
- a circle outline is a ring of short raster lines (no outline circle is documented)
- a filled path is a fan of raster triangles; it is only correct for convex shapes,
  which is all upstream fills (the station's hull)
- text uses a pixel font at an integer scale chosen from font_size
"""
import math

NATIVE_TEXT_H = 10            # ASSUMED pixel height of the default font at scale 1


class Ctx:
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"

    def __init__(self, screen, color, shape, ox=160, oy=120):
        self.screen, self.color, self.shape_mod = screen, color, shape
        self.ox, self.oy = ox, oy
        self.font_size = 14
        self.line_width = 1.5
        self.text_align = "center"
        self.text_baseline = "middle"
        self._rgba = (255, 255, 255, 255)
        self._pen_dirty = True
        self._path = []
        self._shape = None
        self._cur = (0, 0)
        self._stack = []

    # state ---------------------------------------------------------------
    def save(self):
        self._stack.append((self._rgba, self.font_size, self.line_width, self.text_align, self.text_baseline))
        return self

    def restore(self):
        if self._stack:
            (self._rgba, self.font_size, self.line_width,
             self.text_align, self.text_baseline) = self._stack.pop()
            self._pen_dirty = True
        return self

    def rgb(self, r, g, b):
        return self.rgba(r, g, b, 1.0)

    def rgba(self, r, g, b, a):
        self._rgba = (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5), int(a * 255 + 0.5))
        self._pen_dirty = True
        return self

    def _pen(self):
        if self._pen_dirty:
            self.screen.pen = self.color.rgb(*self._rgba)
            self._pen_dirty = False

    def _px(self, x, y):
        return (math.floor(self.ox + x + 0.5), math.floor(self.oy + y + 0.5))

    # paths ---------------------------------------------------------------
    def begin_path(self):
        self._path = []
        self._shape = None
        return self

    def move_to(self, x, y):
        self._cur = (x, y)
        self._path.append([(x, y)])
        return self

    def line_to(self, x, y):
        if not self._path:
            self._path.append([self._cur])
        self._path[-1].append((x, y))
        self._cur = (x, y)
        return self

    def rectangle(self, x, y, w, h):
        self._shape = ("rect", x, y, w, h)
        return self

    def arc(self, x, y, r, a0, a1, d):
        self._shape = ("arc", x, y, r, a0, a1)
        return self

    # painting ------------------------------------------------------------
    def fill(self):
        sh = self._shape
        if sh and sh[0] == "rect":
            self._fill_rect(sh[1], sh[2], sh[3], sh[4])
        elif sh and sh[0] == "arc":
            self._pen()
            x, y = self._px(sh[1], sh[2])
            self.screen.circle(x, y, round(sh[3]))
        else:
            self._pen()
            for pts in self._path:
                if len(pts) > 2:
                    p = [self._px(*q) for q in pts]
                    for i in range(1, len(p) - 1):          # triangle fan
                        self.screen.triangle(p[0][0], p[0][1], p[i][0], p[i][1], p[i + 1][0], p[i + 1][1])
        self._shape = None
        self._path = []
        return self

    def _fill_rect(self, x, y, w, h):
        x0, y0 = self._px(min(x, x + w), min(y, y + h))
        x1, y1 = self._px(max(x, x + w), max(y, y + h))
        if w != 0 and x1 <= x0:          # a thin rectangle (the radar's 1 px axes sit on half
            x1 = x0 + 1                  # pixels) must still cover a pixel, not round away
        if h != 0 and y1 <= y0:
            y1 = y0 + 1
        if x1 > x0 and y1 > y0:
            self._pen()
            self.screen.rectangle(x0, y0, x1 - x0, y1 - y0)

    def _seg(self, x0, y0, x1, y1):
        a, b = self._px(x0, y0), self._px(x1, y1)
        self._pen()
        if self.line_width <= 1.5:
            self.screen.line(a[0], a[1], b[0], b[1])
        else:
            self.screen.shape(self.shape_mod.line(a[0], a[1], b[0], b[1], self.line_width))

    def stroke(self):
        sh = self._shape
        if sh and sh[0] == "rect":
            _, x, y, w, h = sh
            for a, b in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                         ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
                self._seg(a[0], a[1], b[0], b[1])
        elif sh and sh[0] == "arc":
            _, cx, cy, r, a0, a1 = sh
            full = abs(a1 - a0) >= 2 * math.pi - 1e-6
            n = max(8, min(48, int(r * 0.9)))
            sweep = (2 * math.pi) if full else (a1 - a0)
            px, py = cx + r * math.cos(a0), cy + r * math.sin(a0)
            for i in range(1, n + 1):
                a = a0 + sweep * i / n
                qx, qy = cx + r * math.cos(a), cy + r * math.sin(a)
                self._seg(px, py, qx, qy)
                px, py = qx, qy
        for sub in self._path:
            for i in range(len(sub) - 1):
                self._seg(sub[i][0], sub[i][1], sub[i + 1][0], sub[i + 1][1])
        self._shape = None
        self._path = []
        return self

    # text ----------------------------------------------------------------
    def text(self, s):
        s = str(s)
        scale = max(1, int(self.font_size / NATIVE_TEXT_H + 0.5))
        w, h = self.screen.measure_text(s)
        w, h = w * scale, h * scale
        x, y = self._px(*self._cur)
        if self.text_align == "center":
            x -= w // 2
        elif self.text_align == "right":
            x -= w
        if self.text_baseline == "middle":
            y -= h // 2
        elif self.text_baseline in ("bottom", "alphabetic"):
            y -= h
        self._pen()
        self.screen.text(s, x, y, scale)
        self._path = []
        return self
