"""Run this repo's tests:  python tests/run_all.py   (the vendored upstream suite is separate:
vendor/ace_commander/tests/run_all.py, which needs Elite data for 9 of its 18 files)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
failed = []
for name in ("test_sim.py", "test_ctx_shim.py", "test_patch_identity.py", "test_view_rect.py", "test_dashboard.py", "test_host.py"):
    r = subprocess.run([sys.executable, os.path.join(HERE, name)], capture_output=True, text=True)
    last = [l for l in r.stdout.strip().split("\n") if l and not l.startswith("PERF")]
    print("%-24s %s" % (name, "ok" if r.returncode == 0 else "FAILED"), "-", last[-1] if last else "")
    if r.returncode:
        failed.append(name)
        print(r.stdout[-1500:], r.stderr[-2500:])
sys.exit(1 if failed else 0)
