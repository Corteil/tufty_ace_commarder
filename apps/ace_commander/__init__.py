# Ace Commander for Tufty 2350 - the file Badgeware runs when the app starts.
# The game itself is the package `acepkg` (unmodified upstream files + dash_tufty), next to this file.
import sys

_here = "/apps/ace_commander"
try:
    _here = __file__.rsplit("/", 1)[0] or _here
except NameError:
    pass
if _here not in sys.path:
    sys.path.insert(0, _here)

import platform_tufty

platform_tufty.start(globals())
