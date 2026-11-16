"""Build the badge app folder: vendored upstream + documented patches -> build/ace_commander/.

    python tools/build_app.py

Copies the vendored game's runtime .py files (not tests or tools), applies tools/patches.py,
and fails if any patch does not match. Output: build/ace_commander/ (gitignored). The folder
must be called ace_commander because upstream's modules import each other as that package.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from patches import PATCHES

SRC = os.path.join(REPO, "vendor", "ace_commander")
DEST = os.path.join(REPO, "build", "ace_commander")


def build(dest=DEST, patches=PATCHES):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for name in sorted(os.listdir(SRC)):
        if name.endswith(".py") and os.path.isfile(os.path.join(SRC, name)):
            shutil.copy2(os.path.join(SRC, name), os.path.join(dest, name))
    tufty = os.path.join(REPO, "apps", "ace_commander")      # Tufty-only modules join the package
    for name in sorted(os.listdir(tufty)):
        if name.endswith(".py") and name != "__init__.py":
            shutil.copy2(os.path.join(tufty, name), os.path.join(dest, name))
    for name, old, new, count in patches:
        path = os.path.join(dest, name)
        text = open(path).read()
        found = text.count(old)
        if found != count:
            sys.exit("patch failed: %s: expected %d match(es), found %d for:\n%s" % (name, count, found, old))
        open(path, "w").write(text.replace(old, new))
    return dest


if __name__ == "__main__":
    out = build()
    print("built %s with %d patches" % (out, len(PATCHES)))
