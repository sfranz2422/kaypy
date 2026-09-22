"""Every Python block in README.md actually runs.

    python3 tests/test_readme_code.py

`test_guide_code.py` covers GUIDE.md, but only its *whole programs* — blocks
that begin `from kaypy import *`. The README is almost entirely fragments, so
until now nothing checked it at all, and the README is the first thing anyone
reads. A broken snippet there is the first impression.

Fragments cannot run on their own — they mention `player`, `ship`, `level`, a
scene that gets built elsewhere. So each one is run on top of a small preamble
that supplies exactly those names. That means this checks what a fragment can
be checked for: that every kaypy name in it exists, takes those arguments, and
does not raise. It cannot check that the surrounding prose is true.

Blocks that are deliberately not runnable — a line shown as the wrong way to
write something — are listed in SKIP with the reason, so the count of what was
skipped is visible rather than silent.
"""
import os
import pathlib
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "2"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The lesson assets, so loadSprite("images/bean.png") in a snippet is real.
os.chdir(ROOT / "examples")

BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)

# The names a fragment may lean on. Deliberately built with the real engine,
# not stubs: a snippet that calls player.jump() should fail here if body()
# stops providing jump().
PREAMBLE = """
from kaypy import *

kaplay(width=320, height=240)

loadSprite("bean", "images/bean.png")
loadSprite("ship", "images/bean.png")
loadSprite("grass", "images/grass.png")
loadSprite("coin", "images/coin.png")
loadSprite("spike", "images/spike.png")

SPEED = 320
player_score = 0
spawn = vec2(10, 10)

player = add([sprite("bean"), pos(50, 50), area(), body(), anchor("bot"), "player"])
ship = player
level = addLevel(["="], {"tileWidth": 16, "tileHeight": 16,
                         "tiles": {"=": lambda: [sprite("grass"), area()]}})


def build_the_level():
    pass


def show_score(score):
    pass


def jump():
    pass
"""

# Blocks that are illustrations of what NOT to write, or prose in code font.
SKIP = {}

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-46s %s" % ("ok" if ok else "FAIL", label, detail))


def first_line(block):
    return next((l for l in block.splitlines() if l.strip()), "")[:44]


blocks = BLOCK_RE.findall((ROOT / "README.md").read_text())
check("the README has python in it", len(blocks) >= 8, "%d blocks" % len(blocks))

ran = skipped = 0
for i, block in enumerate(blocks, 1):
    if i in SKIP:
        skipped += 1
        print("  skip %-46s %s" % (first_line(block), SKIP[i]))
        continue

    whole = block.lstrip().startswith("from kaypy import *")
    source = block if whole else PREAMBLE + "\n" + block

    import kaypy.engine as ke
    ke._engine = None
    try:
        exec(compile(source, "README block %d" % i, "exec"), {})
        ok, why = True, ""
    except Exception as exc:
        ok, why = False, "%s: %s" % (type(exc).__name__, str(exc).split("\n")[0][:70])
    finally:
        if ke._engine is not None:
            # Stop the atexit hook trying to run a game at interpreter exit,
            # against a video system that will be long gone by then.
            ke._engine._started = True
            ke._engine._running = False
            ke._engine = None

    ran += 1
    check("block %2d %s" % (i, "(whole program)" if whole else "(fragment)  "),
          ok, why or first_line(block))

check("every block was either run or skipped on purpose",
      ran + skipped == len(blocks), "%d run, %d skipped" % (ran, skipped))

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
