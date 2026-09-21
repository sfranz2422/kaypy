"""What a web page calls to run a game, and what it prints when that fails.

    python3 tests/test_webrun.py

kaplay/webrun.py is the two halves of a run — the program's top level, then
the frame loop — plus the traceback trimming. The trimming is the part worth
testing hardest, because it is the only thing a student sees when their game
does not work, and because trimming too much is a silent failure of its own:
an error whose real cause was dropped is worse than a long traceback.
"""
import asyncio
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kaplay as K                                              # noqa: E402
import kaplay.engine as ke                                      # noqa: E402
from kaplay import webrun                                       # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


class Captured:
    """Whatever the run printed to stderr."""

    def __enter__(self):
        import io
        self._real, sys.stderr = sys.stderr, io.StringIO()
        return self

    def __exit__(self, *exc):
        self.text = sys.stderr.getvalue()
        sys.stderr = self._real
        return False


def reset():
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
    ke._engine = None


# ------------------------------------------------------------ a good run
reset()
os.environ["KAYPY_TEST_MAX_FRAMES"] = "12"
GOOD = """from kaplay import *
kaplay(width=64, height=64)
ticks = []
onUpdate(lambda: ticks.append(1))
"""
with Captured() as out:
    status = webrun.run(GOOD)
check("a good program runs", status == "ok", out.text.strip()[:60])
check("and says nothing while doing it", not out.text.strip())

with Captured() as out:
    loop_status = asyncio.run(webrun.drive())
check("the frame loop runs and returns", loop_status == "ok", out.text.strip()[:60])
check("and the program's own handler ran",
      len(sys.modules["__main__"].ticks) > 5,
      "%d frames" % len(sys.modules["__main__"].ticks))

# The handlers a program registers keep looking things up in its globals for
# as long as the game runs. A bare dict would have gone out of scope.
check("the program's namespace outlives the call",
      isinstance(sys.modules["__main__"].ticks, list))

# ------------------------------------------------- an error in the setup
reset()
with Captured() as out:
    status = webrun.run("from kaplay import *\nkaplay(width=64, height=64)\n"
                        "add([sprite('nope'), pos(0, 0)])\n")
check("an error in the setup is reported as one", status == "error")
check("and names the line in the program",
      "line 3" in out.text, out.text.strip().splitlines()[-1][:60] if out.text else "")
check("and ends with the exception itself",
      out.text.strip().splitlines()[-1].startswith(("KeyError", "RuntimeError")),
      out.text.strip().splitlines()[-1][:60] if out.text else "")

# ---------------------------------------------------------- a syntax error
reset()
with Captured() as out:
    status = webrun.run("from kaplay import *\nkaplay(\n")
check("a syntax error is caught before anything runs", status == "error")
check("and is reported with a line number and the line",
      "SyntaxError on line" in out.text, out.text.strip().splitlines()[0][:60])

# -------------------------------------------------- an error in a handler
# The one that matters most: it happens sixty times a second, long after the
# line that registered it returned.
reset()
BAD_HANDLER = """from kaplay import *
kaplay(width=64, height=64)
player = add([rect(4, 4), pos(0, 0)])


@onUpdate
def move():
    player.pos.x += player.speed
"""
with Captured() as out:
    webrun.run(BAD_HANDLER)
    loop_status = asyncio.run(webrun.drive())
check("an error in a handler stops the game", loop_status == "error")
check("it is reported once, not once a frame",
      out.text.count("AttributeError") == 1,
      "%d times" % out.text.count("AttributeError"))
check("and it points at the handler's own line",
      "line 8" in out.text, [l for l in out.text.splitlines() if "line" in l][:1])

# --------------------------------------------------------- the trimming
# Frames belonging to asyncio, to Python and to the engine are dropped, so the
# first thing read is the student's own code and not kaplay/engine.py.
check("the engine's frames are not shown when the program has its own",
      "engine.py" not in out.text and "asyncio" not in out.text,
      out.text.strip().splitlines()[:1])
check("but the program's line is quoted",
      "player.speed" in out.text)

# What counts as whose code, asked directly. Going through a raised exception
# cannot answer this cleanly: the frame that does the raising is always in
# this test file, which is somebody's own code and correctly kept.
import traceback as _tb                                         # noqa: E402

PKG = os.path.dirname(os.path.abspath(webrun.__file__))


def frame(filename):
    return _tb.FrameSummary(filename, 1, "f")


check("the program's own file is the program's",
      webrun._own_frame(frame("main.py"), PKG))
check("a file beside it is too",
      webrun._own_frame(frame("/home/someone/mygame/helper.py"), PKG))
check("the engine's files are not",
      not webrun._own_frame(frame(os.path.join(PKG, "engine.py")), PKG))
check("nor is asyncio",
      not webrun._own_frame(frame("/usr/lib/python3.11/asyncio/runners.py"), PKG))
check("nor is anything with no real file",
      not webrun._own_frame(frame("<string>"), PKG))

# The reverse case: an error with nothing of the student's on the stack is a
# kaypy bug, and hiding the engine's frames there would leave an empty
# traceback pointing nowhere. Built by raising inside a file compiled under
# the package's own path, then dropping this file's frame from the top — which
# is exactly the shape a real engine-only error has.
scope = {}
exec(compile("def boom():\n    raise ValueError('inside the engine')\n",
             os.path.join(PKG, "pretend.py"), "exec"), scope)
try:
    scope["boom"]()
except ValueError as err:
    err.__traceback__ = err.__traceback__.tb_next      # drop this file's frame
    text = webrun.format_error(err)
check("an error with no program frames still shows a traceback",
      "pretend.py" in text, text.splitlines()[-1][:60])
check("and says it looks like a kaypy bug", "bug in kaypy" in text,
      text.splitlines()[0][:60])

# ------------------------------------------------------ no game at all
reset()
with Captured() as out:
    status = asyncio.run(webrun.drive())
check("a program that never called kaplay() says so", status == "error")
check("and says what to do about it", "kaplay()" in out.text,
      out.text.strip()[:60])

reset()
bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
