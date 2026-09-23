"""follow(): be where another object is — including the frame it moved.

    python3 tests/test_follow.py

THE BUG THIS IS MOSTLY ABOUT

A component's update() runs BEFORE the physics step. For nearly everything
that is right. For a follower it is not, because a follower's whole job is to
agree with where the target ended up, and before physics it can only read
where the target was last frame.

Standing still, that is invisible. On a player mid-jump at 800 px/s it is
thirteen pixels — so a health bar sits correctly while the player walks and
slides off them the instant they jump. It looks like a rendering fault, it
happens only sometimes, and a position readout taken at the wrong moment
shows nothing wrong at all.

So follow() runs in a late pass, after collision. The checks below measure
the gap between follower and target on the frames where the target is moving
FASTEST, because those are the only frames where being one behind shows.

ALSO CHECKED

  * exact locking, with and without an offset, and through a parent
  * speed= chases rather than locks, arrives, and does not overshoot
  * a destroyed target leaves the follower where it stood
  * and the errors a beginner will actually hit say what to do
"""
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kaypy.engine as ke                                        # noqa: E402
from kaypy import (kaypy, add, pos, rect, area, body, follow,     # noqa: E402
                   setGravity, vec2, width, height)

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


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


def frame(eng, dt=1 / 60):
    """One frame, in the engine's own order: updates, then physics, then
    the late pass follow() lives in."""
    eng._dt = dt
    for obj in list(eng._objs):
        if not obj.exists():
            continue
        for comp in list(obj._comps.values()):
            comp.update(obj)
    n = eng.physics.substeps_for(eng._objs, dt)
    for _ in range(n):
        eng.physics.step(eng._objs, dt / n)
        eng.collision.step(eng._objs)
    for obj in list(eng._objs):
        if not obj.exists():
            continue
        for comp in list(obj._comps.values()):
            if comp.wants_late:
                comp.late_update(obj)


# --------------------------------------------------------- it locks on
reset()
eng = kaypy(width=800, height=600)
target = add([rect(20, 20), pos(100, 100)])
mark = add([rect(4, 4), pos(0, 0), follow(target)])
frame(eng)
check("a follower lands on its target",
      mark.pos.x == 100 and mark.pos.y == 100, "%s" % (mark.pos,))

target.pos = vec2(340, 55)
frame(eng)
check("  and goes with it when it is moved",
      mark.pos.x == 340 and mark.pos.y == 55, "%s" % (mark.pos,))

reset()
eng = kaypy(width=800, height=600)
target = add([rect(20, 20), pos(200, 200)])
bar = add([rect(40, 6), pos(0, 0), follow(target, offset=vec2(-4, -30))])
frame(eng)
check("an offset is held exactly",
      (bar.pos.x, bar.pos.y) == (196, 170), "%s" % (bar.pos,))

bar.comp("follow").offset = vec2(10, 10)
frame(eng)
check("  and can be changed while it runs",
      (bar.pos.x, bar.pos.y) == (210, 210), "%s" % (bar.pos,))

# ------------------------------------------- THE ONE THAT MATTERS: no lag
#
# A falling target, sampled on the frames where it is moving fastest. If
# follow() ran with the ordinary updates it would be a whole frame of
# gravity behind here, and nowhere else.
reset()
eng = kaypy(width=800, height=600)
setGravity(1600)
faller = add([rect(20, 20), pos(400, 0), area(), body()])
tag = add([rect(4, 4), pos(0, 0), follow(faller)])

gaps, speed = [], 0.0
for _ in range(30):
    frame(eng)
    gaps.append(abs(tag.pos.y - faller.pos.y))
    speed = max(speed, abs(faller.comp("body").vel.y))
check("a follower does not lag a falling target", max(gaps) == 0,
      "worst gap %.2f px, at up to %.0f px/s" % (max(gaps), speed))

# And the same going up, which is when a jumping player's health bar shows it.
faller.comp("body").vel.y = -900
gaps = []
for _ in range(10):
    frame(eng)
    gaps.append(abs(tag.pos.y - faller.pos.y))
check("  nor a jumping one", max(gaps) == 0, "worst gap %.2f px" % max(gaps))

# A target that gets shoved by collision rather than moving itself: its
# position changes inside collision.step, later still.
reset()
eng = kaypy(width=800, height=600)
setGravity(1600)
lander = add([rect(40, 40), pos(400, 300), area(), body()])
add([rect(width(), 48), pos(0, height() - 48), area(), body(isStatic=True)])
sticker = add([rect(4, 4), pos(0, 0), follow(lander)])
gaps = []
for _ in range(120):
    frame(eng)
    gaps.append(abs(sticker.pos.y - lander.pos.y))
check("  nor one that is pushed out of a floor", max(gaps) == 0,
      "worst gap %.2f px, landed at y=%.1f" % (max(gaps), lander.pos.y))

# ------------------------------------------------------- speed= chases
reset()
eng = kaypy(width=800, height=600)
player = add([rect(20, 20), pos(500, 0)])
pet = add([rect(10, 10), pos(0, 0), follow(player, speed=200)])

frame(eng)
moved = pet.pos.x
check("speed= chases instead of locking", 0 < moved < 10,
      "moved %.2f px in one frame (200 px/s)" % moved)

for _ in range(200):
    frame(eng)
check("  and arrives", abs(pet.pos.x - 500) < 0.001 and abs(pet.pos.y) < 0.001,
      "%s" % (pet.pos,))

# Sitting on the target it must stay there, not jitter across it. moveTo
# clamps the last step; without that a chaser oscillates forever.
resting = set()
for _ in range(20):
    frame(eng)
    resting.add((pet.pos.x, pet.pos.y))
check("  and sits still once it gets there", len(resting) == 1,
      sorted(resting))

# ------------------------------------------------- the target is destroyed
reset()
eng = kaypy(width=800, height=600)
enemy = add([rect(20, 20), pos(250, 250)])
hp = add([rect(30, 5), pos(0, 0), follow(enemy)])
frame(eng)
where = (hp.pos.x, hp.pos.y)
enemy.destroy()
for _ in range(10):
    frame(eng)
check("a destroyed target leaves the follower where it stood",
      (hp.pos.x, hp.pos.y) == where, "%s" % (hp.pos,))
check("  and the follower still exists", hp.exists())

# ------------------------------------------------------------ through a parent
#
# pos() is relative to a parent. A world-space target has to come back into
# the parent's frame, or the follower lands at double the offset — which
# looks right until the parent is anywhere but the origin.
reset()
eng = kaypy(width=800, height=600)
target = add([rect(20, 20), pos(300, 120)])
parent = add([rect(50, 50), pos(200, 100)])
child = parent.add([rect(4, 4), pos(0, 0), follow(target)])
frame(eng)
from kaypy.geometry import get_world_pos                          # noqa: E402
world = get_world_pos(child)
check("a parented follower ends up on the target in WORLD space",
      (world.x, world.y) == (300, 120),
      "world %s, local %s" % (world, child.pos))

# --------------------------------------------------------------- the errors
reset()
kaypy(width=800, height=600)


def message(fn):
    try:
        fn()
    except Exception as e:                                        # noqa: BLE001
        return "%s: %s" % (type(e).__name__, e)
    return ""


m = message(lambda: follow("player"))
check("follow(\"player\") explains what it wants",
      "game object" in m and "add(" in m, m.split("\n")[0][:60])

loose = add([rect(10, 10)])
m = message(lambda: follow(loose))
check("following something with no pos() says so", "pos()" in m, m[:70])

m = message(lambda: add([rect(4, 4), follow(add([rect(2, 2), pos(0, 0)]))]))
check("and so does following WITHOUT a pos() of your own",
      "pos()" in m and "moves" in m, m[:70])

m = message(lambda: follow(add([rect(2, 2), pos(0, 0)]), speed=0))
check("speed=0 is refused rather than standing still forever",
      "pixels per second" in m, m[:70])

# --------------------------------------------- the late pass costs nothing
#
# Every component in the game is asked whether it wants the late pass, every
# frame. If that were expensive it would be a tax on games with no follower
# in them at all, which is most of them.
reset()
eng = kaypy(width=800, height=600)
for i in range(200):
    add([rect(4, 4), pos(i, i), area()])
import time                                                       # noqa: E402
start = time.perf_counter()
for _ in range(60):
    frame(eng)
whole = time.perf_counter() - start
start = time.perf_counter()
for _ in range(60):
    for obj in list(eng._objs):
        for comp in list(obj._comps.values()):
            if comp.wants_late:
                comp.late_update(obj)
late = time.perf_counter() - start
check("the late pass is a rounding error on a 200-object scene",
      late < whole * 0.15,
      "%.1f ms of %.1f ms for 60 frames" % (late * 1000, whole * 1000))

reset()
done()
