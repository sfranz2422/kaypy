"""The small Kaplay names, and the object-free onCollide.

    python3 tests/test_helpers.py

None of these is load-bearing on its own. Together they are the difference
between a Kaplay example found on the internet running as written and dying on
its third line with a NameError — and "KAPLAY's documentation still tells you
what to write" is only true while the names in it exist. So the first check is
simply that `from kaplay import *` brings every one of them in, which is the
failure a student would actually hit.
"""
import math
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Aliased, because `from kaplay import *` binds the NAME kaplay to the
# kaplay() function and would shadow the module itself.
import kaplay as _mod                                         # noqa: E402
import kaplay.engine as ke                                    # noqa: E402
from kaplay import *                                          # noqa: E402,F403

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-48s %s" % ("ok" if ok else "FAIL", label, detail))


# --------------------------------------------------- the names are there
WANTED = ["time", "destroy", "destroyAll", "isKeyDown", "rgb", "lerp",
          "clamp", "chance", "wave", "deg2rad", "rad2deg", "onCollide",
          "tween", "easings", "rotate"]
here = set(dir(_mod))
missing = [n for n in WANTED if n not in here]
check("every new name is star-imported", not missing, "missing %s" % missing)
check("and every name in __all__ really exists",
      not [n for n in _mod.__all__ if not hasattr(_mod, n)],
      [n for n in _mod.__all__ if not hasattr(_mod, n)] or "")

# ------------------------------------------------------------- the maths
check("lerp blends numbers", lerp(0, 10, 0.25) == 2.5)
p = lerp(vec2(0, 0), vec2(10, 20), 0.5)
check("lerp blends vec2", (p.x, p.y) == (5, 10), "%s" % (p,))
check("clamp keeps a number in range",
      (clamp(5, 0, 10), clamp(-3, 0, 10), clamp(99, 0, 10)) == (5, 0, 10))
check("clamp tolerates swapped bounds", clamp(5, 10, 0) == 5)
check("deg2rad and rad2deg are inverses",
      abs(rad2deg(deg2rad(137)) - 137) < 1e-9)

swing = [wave(100, 200, t / 10) for t in range(200)]
check("wave stays between its bounds",
      min(swing) >= 99.99 and max(swing) <= 200.01,
      "%.1f to %.1f" % (min(swing), max(swing)))
check("wave actually swings", max(swing) - min(swing) > 90)
check("wave takes a different shape function",
      abs(wave(0, 10, 0, math.cos) - 10) < 1e-9, "cos starts at the top")

# chance() is random, so check the distribution rather than one roll.
rolls = sum(1 for _ in range(4000) if chance(0.25))
check("chance(0.25) is true about a quarter of the time",
      800 < rolls < 1200, "%d/4000" % rolls)
check("chance(0) is never true", not any(chance(0) for _ in range(200)))
check("chance(1) is always true", all(chance(1) for _ in range(200)))

# ------------------------------------------------------------- the colour
check("rgb takes three numbers", rgb(255, 128, 0) == (255, 128, 0))
check("rgb takes a hex string", rgb("#ff8800") == (255, 136, 0))
check("rgb takes short hex", rgb("#f80") == (255, 136, 0))
check("rgb takes one number as a grey", rgb(200) == (200, 200, 200))
check("rgb passes a tuple through", rgb((1, 2, 3)) == (1, 2, 3))
for bad, why in (("#ff88", "wrong length"), ("#gggggg", "not hex")):
    try:
        rgb(bad)
        said = False
    except ValueError as err:
        said = "#ff8800" in str(err)
    check("rgb(%r) explains itself" % bad, said, why)
try:
    rgb(255, 128)
    said = False
except ValueError as err:
    said = "missing the blue" in str(err)
check("rgb with two numbers says what is missing", said)

# --------------------------------------------------------- the game clock
eng = kaplay(width=100, height=100)
check("time() starts at zero", time() == 0, repr(time()))
eng._dt = 0.1
eng._elapsed += 0.5
check("time() is the game's clock, not the wall's", time() == 0.5, repr(time()))

# --------------------------------------------------------------- destroy
a = add([rect(4, 4), pos(0, 0), "mob"])
b = add([rect(4, 4), pos(0, 0), "mob"])
c = add([rect(4, 4), pos(0, 0), "boss"])
check("destroy() removes one", (destroy(a), a.exists()) == (None, False))
check("destroyAll() removes a whole tag and counts them",
      destroyAll("mob") == 1 and not b.exists(), "b gone: %s" % (not b.exists()))
check("and leaves other tags alone", c.exists())
check("destroy(None) is harmless", destroy(None) is None)

# --------------------------------------------------------------- the keys
check("isKeyDown is false for an unpressed key", isKeyDown("space") is False)
check("isKeyDown on a nonsense key says no rather than raising",
      isKeyDown("banana") is False)

ke._engine = None
eng._started = True
eng._running = False

# ------------------------------------------------- the object-free onCollide
eng2 = kaplay(width=200, height=200)
hits = []


@onCollide("bullet", "enemy")
def hit(bullet, enemy):
    hits.append((bullet.is_("bullet"), enemy.is_("enemy")))
    bullet.destroy()
    enemy.destroy()


# The enemy is added FIRST, so the collision system meets it before the
# bullet. The handler must still be given them in the order the tags were
# named, or a student's `bullet.destroy()` destroys the enemy.
add([rect(10, 10), pos(52, 52), area(), "enemy"])
add([rect(10, 10), pos(50, 50), area(), "bullet"])
eng2.collision.step(eng2._objs)
check("onCollide(tagA, tagB) fires on a new touch", len(hits) == 1, repr(hits))
check("and hands them over in the order the tags were named",
      hits == [(True, True)], repr(hits))

# It must not fire again every frame — that is onCollideUpdate's job.
add([rect(10, 10), pos(80, 80), area(), "enemy"])
add([rect(10, 10), pos(81, 81), area(), "bullet"])
eng2.collision.step(eng2._objs)
before = len(hits)
eng2.collision.step(eng2._objs)
check("it fires once per touch, not once per frame", len(hits) == before,
      "%d, then %d" % (before, len(hits)))

# Objects made later are covered, which is the reason to prefer it.
add([rect(10, 10), pos(120, 120), area(), "enemy"])
add([rect(10, 10), pos(121, 121), area(), "bullet"])
eng2.collision.step(eng2._objs)
check("objects created later are covered too", len(hits) == before + 1)

quiet = []
onCollide("ghost", "wall", lambda g, w: quiet.append(1))
add([rect(10, 10), pos(160, 160), area(), "ghost"])
eng2.collision.step(eng2._objs)
check("a pair that never meets never fires", quiet == [])

eng2._started = True
eng2._running = False
ke._engine = None

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
