"""Upstream game frames used by the shim and patch tests.

    frames(parent)  yields (name, app) for six states: title, docked, galactic chart,
                    system data, launch tunnel, flight.
    python tests/scenes.py PARENT OUTDIR   draws them with upstream's Pillow ctx (scale 1)
                    into OUTDIR/*.png, using the ace_commander package found in PARENT.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STUBS = os.path.join(REPO, "vendor", "ace_commander", "tests")


def frames(parent, save_path):
    sys.path.insert(0, STUBS)
    sys.path.insert(0, parent)
    import badge_stubs as bs
    bs.install()
    import ace_commander
    mod = ace_commander.ace
    game = mod.game
    mod.SAVE_PATH = save_path
    import random
    random.seed(3)
    if os.path.exists(save_path):
        os.remove(save_path)
    tick = bs.tick
    a = ace_commander.AceCommander()
    for _ in range(60):
        tick(a)
    yield "title", a
    tick(a, fresh=["LEFT"])
    bs.choose(a, "NEW COMMANDER")
    tick(a, fresh=["CONFIRM"])
    a.cmdr.add_kills(140)
    yield "docked", a
    d = a.dock
    d.open("GALACTIC CHART")
    yield "galactic", a
    d.open("SYSTEM DATA")
    yield "system", a
    d.go(0)
    tick(a, fresh=["CONFIRM"])
    a.launch_t = 0.6 * mod.LAUNCH_TIME
    yield "tunnel", a
    a.launch_t = 99
    tick(a)
    g = a.game
    g.spawn_t = g.rock_t = 1e9
    g.objs[:] = []
    for name, kind, pos, nose in (
            ("COBRA MK III", "ship", (-120.0, 60.0, 900.0), (0.6, -0.2, -0.75)),
            ("VIPER", "ship", (380.0, -150.0, 1900.0), (-0.5, 0.3, -0.8)),
            ("ASTEROID", "rock", (-700.0, -420.0, 2600.0), (1, 0.2, 0))):
        o = game.Obj(g.types[name], kind, *pos)
        d3 = game._unit(*nose)
        game._look(o.m, d3[0], d3[1], d3[2])
        if kind == "ship":
            o.state = "break"; o.t = 99; o.aim = list(nose)
        g.objs.append(o)
    tick(a, held=["CONFIRM"], ms=40)
    yield "flight", a


if __name__ == "__main__":
    parent, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    os.makedirs(out, exist_ok=True)
    from PIL import Image
    n = 0
    for name, app in frames(parent, os.path.join(out, "commander.json")):
        sys.path.insert(0, STUBS)
        from badge_stubs import PilCtx
        c = PilCtx(1)
        app.draw(c)
        c.img.save(os.path.join(out, name + ".png"))
        n += 1
    print("%d frames" % n)
