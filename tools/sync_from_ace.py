"""Copy a pinned snapshot of Corteil/ace_commander into vendor/ace_commander/.

Usage (from this repo's root):
    python tools/sync_from_ace.py PATH_TO_ACE_COMMANDER_CLONE

- Copies every file git tracks in the source (so generated, gitignored Elite data
  such as ship_data.py / game_data.py is never copied).
- Refuses a source with uncommitted changes, so UPSTREAM always names real history.
- Writes UPSTREAM with the commit hash. The vendored copy is read-only by convention:
  Tufty-specific code lives outside vendor/. The folder is called ace_commander
  because upstream's tests import the app as that package.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEST = os.path.join(REPO, "vendor", "ace_commander")


def git(src, *args):
    return subprocess.run(["git", "-C", src] + list(args), check=True,
                          capture_output=True, text=True).stdout


def main(src):
    src = os.path.abspath(src)
    if git(src, "status", "--porcelain").strip():
        sys.exit("source has uncommitted changes: commit or stash first")
    commit = git(src, "rev-parse", "HEAD").strip()
    date = git(src, "log", "-1", "--format=%cI").strip()
    subject = git(src, "log", "-1", "--format=%s").strip()
    files = [f for f in git(src, "ls-files").split("\n") if f]
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    for f in files:
        out = os.path.join(DEST, f)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copy2(os.path.join(src, f), out)
    with open(os.path.join(REPO, "vendor", "UPSTREAM"), "w") as fh:
        fh.write("repo:    https://github.com/Corteil/ace_commander\n")
        fh.write("commit:  %s\ndate:    %s\nsubject: %s\nfiles:   %d\n" % (commit, date, subject, len(files)))
    print("synced %d files from %s" % (len(files), commit[:10]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
