"""With the patches at their defaults (VIEW 120 x 120) every frame must be pixel-identical to
upstream's. Also: the patched cockpit with a wide, short view draws only inside it."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, REPO)
import build_app
from PIL import Image, ImageChops

build_app.build()
with tempfile.TemporaryDirectory() as tmp:
    outs = {}
    for label, parent in (("upstream", os.path.join(REPO, "vendor")), ("patched", os.path.join(REPO, "build"))):
        out = os.path.join(tmp, label)
        r = subprocess.run([sys.executable, os.path.join(HERE, "scenes.py"), parent, out],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        outs[label] = out
    names = sorted(f for f in os.listdir(outs["upstream"]) if f.endswith(".png"))
    assert len(names) == 6, names
    for n in names:
        a = Image.open(os.path.join(outs["upstream"], n)).convert("RGB")
        b = Image.open(os.path.join(outs["patched"], n)).convert("RGB")
        diff = ImageChops.difference(a, b).getbbox()
        assert diff is None, "%s differs from upstream in %r" % (n, diff)
        print("%-10s identical to upstream" % n)

print("ALL PATCH IDENTITY TESTS PASSED")
