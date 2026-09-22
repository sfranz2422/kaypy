"""setData() and getData(): something still there next time.

    python3 tests/test_storage.py

A high score that survives closing the game is what turns a project a student
shows once into one they play again. So the behaviour that matters is not the
happy path — it is what happens when the disk says no.

A game whose save fails must keep running. A student on a locked-down school
account, or with a read-only folder, or a browser in private mode, still has a
game; they just do not have a saved score. What it must never do is crash, and
what it must never do is *lie* — getData() after a failed setData() has to
return what is really stored, not what somebody hoped would be.
"""
import io
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaypy import storage                                       # noqa: E402
from kaypy.storage import setData, getData                      # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def fresh(folder):
    """Point storage at a folder, as if the game script lived there."""
    sys.modules["__main__"].__file__ = os.path.join(folder, "game.py")
    storage._reset_for_tests()


def quietly(call):
    """Run something, keeping whatever it printed."""
    out, sys.stdout = sys.stdout, io.StringIO()
    try:
        value = call()
        return value, sys.stdout.getvalue()
    finally:
        sys.stdout = out


work = tempfile.mkdtemp()
fresh(work)

# ------------------------------------------------------ the ordinary path
check("nothing saved yet gives the default", getData("best", 0) == 0)
check("and None when no default is given", getData("best") is None)

check("setData says it worked", setData("best", 120) is True)
check("and it reads back", getData("best") == 120)

setData("name", "Steve")
setData("unlocked", [1, 2, 3])
setData("muted", False)
setData("nothing", None)

fresh(work)          # forget the cache: a real reload, from the real file
check("a number survives a restart", getData("best") == 120)
check("so does text", getData("name") == "Steve")
check("so does a list", getData("unlocked") == [1, 2, 3])
check("so does False, rather than becoming the default",
      getData("muted", True) is False, "False is a value, not a missing key")
check("and so does None", getData("nothing", "fallback") is None)

# ------------------------------------------------------------- the file
path = pathlib.Path(work) / storage.FILENAME
check("it writes one plain file beside the game", path.is_file(),
      storage.FILENAME)
check("which a student can read", json.loads(path.read_text())["best"] == 120,
      "it is JSON, on purpose — they can open it and delete it")

# ------------------------------------------------- two games, two scores
other = tempfile.mkdtemp()
fresh(other)
check("a different game starts with nothing", getData("best", 0) == 0,
      "one game's score is not another's")
setData("best", 5)
fresh(work)
check("and the first game's score is untouched", getData("best") == 120)

# ------------------------------------------------------ what cannot be saved
fresh(work)


class Enemy:
    pass


try:
    setData("player", Enemy())
    said = ""
except TypeError as err:
    said = str(err)
check("saving a game object is refused", bool(said))
check("and the message says what CAN be saved",
      "numbers" in said and "lists" in said, said[:56])
check("and says what to do instead", "save what you need from it" in said)
check("the refusal saved nothing", getData("player") is None)

# ------------------------------------------------------ when it cannot write
# The case a student on a locked-down account actually hits.
locked = tempfile.mkdtemp()
fresh(locked)
setData("before", 1)
# The FILE, not the folder. Opening an existing file for writing truncates it,
# which needs permission on the file — locking only the directory still lets
# the write through, which is how this check first passed while proving
# nothing.
locked_file = pathlib.Path(locked) / storage.FILENAME
os.chmod(locked_file, 0o400)
try:
    ok, said = quietly(lambda: setData("after", 2))
    check("a save that cannot be written returns False", ok is False)
    check("and explains itself once", "note:" in said and "carries on" in said,
          said.strip()[:50])

    value, again = quietly(lambda: setData("more", 3))
    check("and does not repeat the complaint every time", "note:" not in again)

    check("the game carries on — reading still works", getData("before") == 1)
    fresh(locked)
    check("and what was NOT written is honestly absent",
          getData("after") is None,
          "getData never pretends a failed save worked")
finally:
    os.chmod(locked_file, 0o600)

# --------------------------------------------------------- a corrupt file
broken = tempfile.mkdtemp()
(pathlib.Path(broken) / storage.FILENAME).write_text("{not json at all")
fresh(broken)
value, said = quietly(lambda: getData("best", 0))
check("a corrupt file does not crash the game", value == 0)
check("it says what happened", "note:" in said, said.strip()[:50])
check("and saving again repairs it", setData("best", 7) is True)
fresh(broken)
check("  so the next run is fine", getData("best") == 7)

# A file that is valid JSON but not a dict — someone put a list in it.
odd = tempfile.mkdtemp()
(pathlib.Path(odd) / storage.FILENAME).write_text("[1, 2, 3]")
fresh(odd)
check("a file holding the wrong shape is ignored, not fatal",
      getData("best", 0) == 0)

import shutil                                                   # noqa: E402
for folder in (work, other, locked, broken, odd):
    shutil.rmtree(folder, ignore_errors=True)

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
