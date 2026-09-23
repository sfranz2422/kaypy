"""raycast(): the first thing in the way, and the awkward cases.

    python3 tests/test_raycast.py

Most of a ray-vs-box test is easy and most of the bugs are in three places,
all of which produce something that works fine in a demo and fails in a
game:

  * an axis-aligned ray. The slab maths divides by each direction
    component, and a ray pointing straight right has dy = 0. Games cast
    almost nothing BUT axis-aligned rays — a guard facing left, a check for
    floor underneath — so a bug here is a bug everywhere that matters.

  * a ray starting inside a box. The entry time goes negative, and reported
    as-is it puts the hit behind the caster: a guard standing in a doorway
    sees straight through the door it is standing in.

  * picking the nearest hit rather than the first one found. Objects are
    tested in creation order, so "the wall in front of you" and "the wall
    you added first" are only the same thing by luck.

Every distance below is worked out by hand from the geometry, so the test
disagrees with the code rather than agreeing with it by construction.
"""
import math
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kaypy.engine as ke                                        # noqa: E402
from kaypy import kaypy, add, pos, rect, area, raycast, vec2      # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


def reset():
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
        ke._engine = None


def near(a, b, tol=1e-6):
    return abs(a - b) <= tol


# A box from (200, 100) to (240, 140). Every expectation below is measured
# off those four numbers.
def scene():
    reset()
    eng = kaypy(width=800, height=600)
    box = add([rect(40, 40), pos(200, 100), area(), "wall"])
    return eng, box


# ------------------------------------------------------- straight along x
eng, box = scene()
hit = raycast(vec2(0, 120), vec2(1, 0))
check("a ray pointing right hits the near face",
      hit is not None and hit.obj is box and near(hit.distance, 200),
      "distance %.1f (expected 200)" % (hit.distance if hit else -1))
check("  at the point on that face",
      hit and near(hit.point.x, 200) and near(hit.point.y, 120),
      "%s" % (hit.point if hit else None))
check("  facing back the way the ray came",
      hit and hit.normal == vec2(-1, 0), "%s" % (hit.normal if hit else None))

# Coming the other way, the far face, and the opposite normal.
hit = raycast(vec2(800, 120), vec2(-1, 0))
check("a ray pointing left hits the other face",
      hit is not None and near(hit.distance, 560),
      "distance %.1f (expected 560)" % (hit.distance if hit else -1))
check("  with the normal the other way round",
      hit and hit.normal == vec2(1, 0), "%s" % (hit.normal if hit else None))

# ------------------------------------------------------- straight along y
hit = raycast(vec2(220, 0), vec2(0, 1))
check("a ray pointing down hits the top face",
      hit is not None and near(hit.distance, 100),
      "distance %.1f (expected 100)" % (hit.distance if hit else -1))
check("  facing up", hit and hit.normal == vec2(0, -1),
      "%s" % (hit.normal if hit else None))

# --------------------------------------------------------------- misses
check("a ray above the box misses", raycast(vec2(0, 50), vec2(1, 0)) is None)
check("a ray pointing away misses", raycast(vec2(0, 120), vec2(-1, 0)) is None)
check("a ray past the end of the box misses",
      raycast(vec2(0, 141), vec2(1, 0)) is None)

# The edge itself: y = 140 is the bottom edge, and should still count.
hit = raycast(vec2(0, 140), vec2(1, 0))
check("a ray exactly along the bottom edge still hits", hit is not None,
      "distance %.1f" % (hit.distance if hit else -1))

# -------------------------------------------------------------- diagonal
#
# From (160, 60) heading down-right at 45 degrees: it reaches x=200 and
# y=100 at the same moment, the box's top-left corner, 40 px along each
# axis, so sqrt(40^2 + 40^2) along the ray.
hit = raycast(vec2(160, 60), vec2(1, 1))
check("a diagonal ray hits the corner at the right distance",
      hit is not None and near(hit.distance, math.hypot(40, 40), 1e-4),
      "distance %.3f (expected %.3f)"
      % (hit.distance if hit else -1, math.hypot(40, 40)))

# The direction need not be a unit vector, and the distance is in pixels
# either way — otherwise every caller has to remember to normalise.
a = raycast(vec2(0, 120), vec2(1, 0))
b = raycast(vec2(0, 120), vec2(17, 0))
check("a direction that is not a unit vector gives the same distance",
      near(a.distance, b.distance), "%.1f vs %.1f" % (a.distance, b.distance))

# --------------------------------------------------- starting inside a box
hit = raycast(vec2(220, 120), vec2(1, 0))
check("a ray that starts inside a box hits it at distance 0",
      hit is not None and hit.obj is box and near(hit.distance, 0),
      "distance %.1f" % (hit.distance if hit else -1))
check("  and the hit is where the ray started, not behind it",
      hit and near(hit.point.x, 220) and near(hit.point.y, 120),
      "%s" % (hit.point if hit else None))

# ------------------------------------------------------- the NEAREST hit
#
# The far wall is added first, so "first found" and "nearest" differ.
reset()
kaypy(width=800, height=600)
far = add([rect(40, 40), pos(500, 100), area(), "far"])
close = add([rect(40, 40), pos(200, 100), area(), "close"])
hit = raycast(vec2(0, 120), vec2(1, 0))
check("the nearest box wins, not the one added first",
      hit is not None and hit.obj is close,
      "hit the %s one" % ("close" if hit and hit.obj is close else "far"))

# ------------------------------------------------------------- exclude
hit = raycast(vec2(0, 120), vec2(1, 0), exclude=["close"])
check("exclude skips a tag and finds what is behind it",
      hit is not None and hit.obj is far and near(hit.distance, 500),
      "distance %.1f (expected 500)" % (hit.distance if hit else -1))
check("exclude also takes a single tag as a string",
      raycast(vec2(0, 120), vec2(1, 0), exclude="close").obj is far)
check("excluding everything finds nothing",
      raycast(vec2(0, 120), vec2(1, 0), exclude=["close", "far"]) is None)

# ------------------------------------------------------- max_distance
check("max_distance stops the ray short",
      raycast(vec2(0, 120), vec2(1, 0), max_distance=100) is None)
check("  and lets through what is inside it",
      raycast(vec2(0, 120), vec2(1, 0), max_distance=250) is not None)

# --------------------------------------------- only area() can be hit
reset()
kaypy(width=800, height=600)
add([rect(40, 40), pos(200, 100)])                  # no area()
check("an object with no area() is not in the way",
      raycast(vec2(0, 120), vec2(1, 0)) is None)

reset()
kaypy(width=800, height=600)
gone = add([rect(40, 40), pos(200, 100), area()])
gone.destroy()
check("nor is a destroyed one", raycast(vec2(0, 120), vec2(1, 0)) is None)

# --------------------------------------------------------------- errors
reset()
kaypy(width=800, height=600)
try:
    raycast(vec2(0, 0), vec2(0, 0))
    msg = ""
except Exception as e:                                           # noqa: BLE001
    msg = str(e)
check("a direction of vec2(0, 0) is refused, with an example",
      "does not go anywhere" in msg and "raycast(" in msg, msg.split("\n")[0])

# --------------------------------------------------------- tuples are fine
reset()
kaypy(width=800, height=600)
add([rect(40, 40), pos(200, 100), area()])
check("plain tuples work as well as vec2",
      raycast((0, 120), (1, 0)) is not None)

reset()
done()
