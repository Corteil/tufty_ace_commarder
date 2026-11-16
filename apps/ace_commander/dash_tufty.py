"""Tufty's flight screen: a 3D view over an Elite-style dashboard, 320 x 240.

    +--------------------------------------+
    |                                      |
    |        3D view  320 x 180            |   crosshair, messages, game over, wave/score
    |                                      |
    +--------------------------------------+
    | SH ====   [2x2]  .--scanner--.  O  SP ====|   dashboard 320 x 60: three bars each side,
    | EN ====   missiles  '-------'  compass LT ====|   missiles, elliptical scanner, compass
    | FU ====                              CT ====|
    +--------------------------------------+

The scanner is the radar; hostile ships are red, as in the EMF build. Everything is drawn through
a ctx (see ctx_badgeware.py) from whole-number rectangles and a few lines. The game state comes
from game.Game exactly as cockpit.draw_hud reads it, so no rules change. Layout numbers are
constants at the top: change them freely.
"""
import math

from . import cockpit as ck

VIEW_W, VIEW_H = 320, 180
DASH_H = 60
SCREEN_W, SCREEN_H = 320, 240

# scanner (relative to the dashboard centre)
SC_RX, SC_RY = 62, 18
SC_Y = 6                 # ellipse centre, down from the dashboard centre
STICK = 12               # tallest blip stalk, pixels

# gauges: three bars either side. label x, bar x, bar width, first row y, row step, bar height
LEFT = (-157, -141, 48)
RIGHT = (94, 110, 48)
ROW0, ROW_STEP, BAR_H = -17, 13, 8
COMPASS_X, COMPASS_Y, COMPASS_R = 78, 4, 9
MISSILE_X, MISSILE_Y = -84, -7

PANEL = (0.04, 0.04, 0.07)
RULE = (0.38, 0.38, 0.48)
TAU = math.pi * 2
_RING_OUT = tuple((SC_RX * math.cos(i * TAU / 28) - 0.75, SC_Y + SC_RY * math.sin(i * TAU / 28) - 0.75)
                  for i in range(28))
_RING_IN = tuple((SC_RX // 2 * math.cos(i * TAU / 16) - 0.5, SC_Y + SC_RY // 2 * math.sin(i * TAU / 16) - 0.5)
                 for i in range(16))
_COMPASS = tuple((COMPASS_X + COMPASS_R * math.cos(i * TAU / 16) - 0.75,
                  COMPASS_Y + COMPASS_R * math.sin(i * TAU / 16) - 0.75) for i in range(16))


def _bar(ctx, col, row, label, frac, rgb):
    lx, bx, w = col
    y = ROW0 + row * ROW_STEP
    ck.text(ctx, label, lx, y + BAR_H // 2, 9, ck.GREY, -1)
    ctx.rgb(*ck.DIM).rectangle(bx, y, w, BAR_H).fill()
    if frac > 0:
        ctx.rgb(*rgb).rectangle(bx, y, w * min(1.0, frac), BAR_H).fill()


def _blip_colour(o):
    if o.kind == "ship":
        if o.role == "pirate" or o.state == "attack" or o.state == "break":
            return ck.RED
        if o.role == "police":
            return ck.POLICE_BLUE
        return ck.WHITE
    return ck.COLOUR[o.kind]


def _stalk(ctx, bx, by, h, size):
    if h >= 0:
        ctx.rectangle(bx, by - h, 1, h).fill()
    else:
        ctx.rectangle(bx, by, 1, -h).fill()
    ctx.rectangle(bx - size // 2, by - h - size // 2, size, size).fill()


def _scanner(ctx, g):
    ctx.rgb(*RULE)
    for px, py in _RING_OUT:
        ctx.rectangle(px, py, 1.5, 1.5).fill()
    for px, py in _RING_IN:
        ctx.rectangle(px, py, 1, 1).fill()
    ctx.rectangle(-SC_RX, SC_Y - 0.5, 2 * SC_RX, 1).fill()
    ctx.rectangle(-0.5, SC_Y - SC_RY, 1, 2 * SC_RY).fill()
    R, R2 = ck._RADAR_R, ck._RADAR_R2
    for o in g.objs:                 # whole numbers, like cockpit.draw_hud
        x = int(o.x)
        z = int(o.z)
        if x * x + z * z > R2:
            continue
        bx = x * SC_RX // R
        by = SC_Y - z * SC_RY // R
        h = int(o.y) * STICK // R
        h = STICK if h > STICK else (-4 if h < -4 else h)
        ctx.rgb(*_blip_colour(o))
        _stalk(ctx, bx, by, h, 3)
    sp = g.space
    if sp is not None:
        st = sp.station
        if st is not None and -R < st.x < R and -R < st.z < R:
            x, z = int(st.x), int(st.z)
            if x * x + z * z <= R2:
                h = int(max(-6000.0, min(22000.0, st.y))) * STICK // R
                h = STICK if h > STICK else (-4 if h < -4 else h)
                ctx.rgb(*ck.station_colour(sp.gov))
                _stalk(ctx, x * SC_RX // R, SC_Y - z * SC_RY // R, h, 5)
        if not sp.witch:
            _compass(ctx, sp)


def _compass(ctx, sp):
    ctx.rgb(*RULE)
    for px, py in _COMPASS:
        ctx.rectangle(px, py, 1.5, 1.5).fill()
    st = sp.station
    if sp.safe and st is not None:
        x, y, z, rgb = st.x, st.y, st.z, ck.station_colour(sp.gov)
    else:
        x, y, z, rgb = sp.px, sp.py, sp.pz, ck.PLANET
    d = math.sqrt(x * x + y * y + z * z)
    if d < 1:
        return
    k = (COMPASS_R - 2) / d
    dx, dy = COMPASS_X + int(x * k), COMPASS_Y - int(y * k)
    if z >= 0:
        ctx.rgb(*rgb).rectangle(dx - 1.5, dy - 1.5, 3, 3).fill()
    else:
        ctx.rgb(rgb[0] * 0.4, rgb[1] * 0.4, rgb[2] * 0.4).rectangle(dx - 1, dy - 1, 2, 2).fill()


def draw_dashboard(ctx, g):
    """ctx origin at the dashboard's centre; the dashboard fills 320 x 60 about it."""
    ctx.rgb(*PANEL).rectangle(-SCREEN_W // 2, -DASH_H // 2, SCREEN_W, DASH_H).fill()
    ctx.rgb(*RULE).rectangle(-SCREEN_W // 2, -DASH_H // 2, SCREEN_W, 1).fill()
    _bar(ctx, LEFT, 0, "SH", g.shield / 100.0, ck.CYAN)
    _bar(ctx, LEFT, 1, "EN", g.hull / 100.0, ck.GREEN if g.hull > 30 else ck.RED)
    fuel = g.fuel / ck.MAX_FUEL if g.fuel is not None else 0
    _bar(ctx, LEFT, 2, "FU", fuel, ck.RED if fuel < 0.25 else ck.GREEN)
    _bar(ctx, RIGHT, 0, "SP", g.speed / 40.0, ck.CYAN if g.jumping else ck.GREEN)
    _bar(ctx, RIGHT, 1, "LT", g.heat, ck.RED if g.hot else ck.YELLOW)
    _bar(ctx, RIGHT, 2, "CT", (g.cabin - ck.COOL_CABIN) / (255.0 - ck.COOL_CABIN), ck.ct_colour(g.cabin))
    for i in range(4):               # missiles, 2 x 2
        ctx.rgb(*(ck.GREEN if i < g.missiles else ck.DIM))
        ctx.rectangle(MISSILE_X + (i % 2) * 8, MISSILE_Y + (i // 2) * 8, 6, 6).fill()
    _scanner(ctx, g)


def _sun_gauges(ctx, g, sp):
    """CT and AL across the top of the view, as cockpit._sun_gauges but inside the 180 high view."""
    top = -ck.VIEW_HH + 4
    ctx.rgba(0, 0, 0, 0.6).rectangle(-74, top, 148, 17).fill()
    ck.text(ctx, "CT", -66, top + 7, 9, ck.GREY)
    ck.text(ctx, "AL", 66, top + 7, 9, ck.GREY)
    ctx.rgb(*ck.DIM).rectangle(-58, top + 5, 50, 4).fill()
    ctx.rgb(*ck.DIM).rectangle(8, top + 5, 50, 4).fill()
    t = (g.cabin - ck.COOL_CABIN) * 50 // (255 - ck.COOL_CABIN)
    ctx.rgb(*ck.ct_colour(g.cabin)).rectangle(-58, top + 5, t, 4).fill()
    d = math.sqrt(sp.sx * sp.sx + sp.sy * sp.sy + sp.sz * sp.sz) - sp.sr
    a = int(50 * d / (ck.SUN_GAUGE_ALT * sp.sr))
    ctx.rgb(*ck.CYAN).rectangle(8, top + 5, 0 if a < 0 else 50 if a > 50 else a, 4).fill()


def draw_view_overlay(ctx, g, ms=None):
    """ctx origin at the view's centre (the view is 320 x 180): crosshair, sun gauges, combat
    wave/score, messages, game over, energy bomb flash."""
    hh = ck.VIEW_HH
    if not getattr(g, "autodock", False):
        ctx.rgb(*ck.GREEN)
        ctx.rectangle(6, -0.75, 8, 1.5).fill()
        ctx.rectangle(-14, -0.75, 8, 1.5).fill()
        ctx.rectangle(-0.75, 6, 1.5, 8).fill()
        ctx.rectangle(-0.75, -14, 1.5, 8).fill()
    sp = g.space
    if sp is not None and g.cabin > ck.COOL_CABIN:
        _sun_gauges(ctx, g, sp)
    if sp is None:                   # combat practice: wave (yellow) and score (white)
        wave, score = str(g.wave), str(g.score)
        width = (len(wave) + len(score)) * 10 - 6 + 9
        x = -width / 2.0
        ctx.rgb(*ck.YELLOW)
        x += ck.number(ctx, g.wave, x, -hh + 4, ck._BIG, -1) + 9
        ctx.rgb(*ck.WHITE)
        ck.number(ctx, g.score, x, -hh + 4, ck._BIG, -1)
    if ms is not None:
        ctx.rgb(*ck.GREY)
        ck.number(ctx, ms, ck.VIEW_HW - 4, -hh + 3, ck._SMALL, 1)
    if g.bomb_t > 0:
        ctx.rgba(1, 1, 1, min(1.0, g.bomb_t * 2.0)).rectangle(
            -ck.VIEW_HW, -hh, 2 * ck.VIEW_HW, 2 * hh).fill()
    if g.over and g.ejected:
        ctx.rgba(0, 0, 0, 0.8).rectangle(-100, -50, 200, 100).fill()
        ck.text(ctx, "ESCAPE POD", 0, -30, 24, ck.YELLOW)
        ck.text(ctx, "ship and cargo lost", 0, -2, 13, ck.WHITE)
        ck.text(ctx, "C: to the station" if g.again.endswith("station") else g.again, 0, 22, 12, ck.GREY)
        ck.text(ctx, "F: title screen", 0, 38, 12, ck.GREY)
    elif g.over:
        ctx.rgba(0, 0, 0, 0.8).rectangle(-100, -50, 200, 100).fill()
        ck.text(ctx, "GAME OVER", 0, -30, 26, ck.RED)
        ck.text(ctx, "SCORE %d   KILLS %d" % (g.score, g.kills), 0, -2, 14, ck.WHITE)
        ck.text(ctx, g.again, 0, 22, 12, ck.GREY)
        ck.text(ctx, "F: title screen", 0, 38, 12, ck.GREY)
    elif g.msg_t > 0:
        ctx.rgba(0, 0, 0, 0.6).rectangle(-78, -hh + 24, 156, 18).fill()
        ck.text(ctx, g.msg, 0, -hh + 33, 14, ck.YELLOW)


class FlightFrame:
    """Draws one flight frame on a Badgeware `screen`: view on top, dashboard below."""

    def __init__(self, screen, color, shape, rect, ctx_class):
        self.screen, self.rect = screen, rect
        self.view = ctx_class(screen, color, shape, ox=SCREEN_W // 2, oy=VIEW_H // 2)
        self.dash = ctx_class(screen, color, shape, ox=SCREEN_W // 2, oy=VIEW_H + DASH_H // 2)
        ck.VIEW_HW, ck.VIEW_HH = VIEW_W // 2, VIEW_H // 2

    def draw(self, g, ms=None):
        s = self.screen
        s.clip = self.rect(0, 0, VIEW_W, VIEW_H)
        ck.draw_world(self.view, g)
        draw_view_overlay(self.view, g, ms)
        s.clip = self.rect(0, VIEW_H, SCREEN_W, DASH_H)
        draw_dashboard(self.dash, g)
        s.clip = self.rect(0, 0, SCREEN_W, SCREEN_H)
