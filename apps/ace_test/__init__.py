# ace_test - hardware/API probe for porting ace_commander to Tufty 2350 (Badgeware).
# Shows: resolution, ms/frame, spinning wireframe cube drawn with shape.line,
# and a Qw/ST Pad probe over I2C (scan + raw TCA9555 input state).
# Copy this folder to /apps on the TUFTY drive (double-tap RESET).
import math
import time

# Set True if the launcher does not call update() for you and nothing runs.
LOOP_MODE = False

# Qw/ST pins: ASSUMED GP4 (SDA) / GP5 (SCL) on I2C0 - verify on first run.
I2C_ID, SDA_PIN, SCL_PIN = 0, 4, 5
TCA_REG_INPUT0 = 0x00  # TCA9555 input port 0 (port 1 follows)

screen.font = font.smart

VERTS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
         (0, 4), (1, 5), (2, 6), (3, 7)]

i2c = None
found = []
pad_addr = None
idle = None
err = ""
last = time.ticks_ms()
ms = 0


def init_i2c():
    global i2c, found, pad_addr, idle, err
    try:
        from machine import I2C, Pin
        i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
        found = i2c.scan()
        for a in (0x21, 0x23, 0x25, 0x27):
            if a in found:
                pad_addr = a
                break
        if pad_addr is not None:
            idle = read_pad()
    except Exception as e:
        err = "i2c: " + str(e)


def read_pad():
    b = i2c.readfrom_mem(pad_addr, TCA_REG_INPUT0, 2)
    return b[0] | (b[1] << 8)


init_i2c()

# Pimoroni firmware may ship a qwstpad driver (pimoroni-pico has one). Probe for it.
qwstpad = None
pad = None
try:
    import qwstpad
    if i2c is not None and pad_addr is not None:
        pad = qwstpad.QwSTPad(i2c, pad_addr)
except Exception as e:
    err = "qwstpad: " + str(e)


def draw_cube(t, cx, cy, size):
    ca, sa = math.cos(t), math.sin(t)
    cb, sb = math.cos(t * 0.7), math.sin(t * 0.7)
    pts = []
    for x, y, z in VERTS:
        x, z = x * ca - z * sa, x * sa + z * ca
        y, z = y * cb - z * sb, y * sb + z * cb
        k = size / (3.5 - z)
        pts.append((cx + x * k, cy + y * k))
    screen.pen = color.white
    for a, b in EDGES:
        screen.shape(shape.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], 1))


def update():
    global last, ms, err
    now = time.ticks_ms()
    ms = time.ticks_diff(now, last)
    last = now
    w, h = screen.width, screen.height

    draw_cube(now / 1000.0, w * 0.72, h * 0.5, h * 0.8)

    screen.pen = color.white
    screen.text("%dx%d  %dms" % (w, h, ms), 2, 2)
    screen.text("model %s" % badge.model, 2, 14)
    screen.text("i2c %s" % [hex(a) for a in found], 2, 26)

    if pad_addr is None:
        screen.text("no pad (0x21-27)", 2, 38)
    else:
        try:
            raw = read_pad()
            diff = raw ^ idle
            screen.text("pad 0x%02x" % pad_addr, 2, 38)
            screen.text("raw  %s" % "{:016b}".format(raw), 2, 50)
            screen.text("diff %s" % "{:016b}".format(diff), 2, 62)
        except Exception as e:
            err = "pad: " + str(e)
    screen.text("qwstpad mod: %s" % ("yes" if qwstpad else "no"), 2, 74)
    if pad is not None:
        try:
            btns = pad.read_buttons()  # expected: dict like {'A': True, ...}
            screen.text("drv %s" % [k for k in btns if btns[k]], 2, 86)
        except Exception as e:
            err = "drv: " + str(e)
    if err:
        screen.text(err, 2, h - 14)

    pressed = badge.held()
    if pressed:
        screen.text("held %s" % pressed, 2, h - 26)
    badge.update()


if LOOP_MODE:
    while True:
        update()
