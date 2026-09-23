"""isGrounded() means standing on something, not "I overlapped it this frame".

    python3 tests/test_grounded.py

Resting on a floor is a TOUCH. Collision resolution can only see an OVERLAP.
So deriving "am I standing on something" from "did I get pushed out of
something" is wrong on every frame where the body does not sink into the
floor — and it reports the player in mid-air while they are plainly standing
still.

A frame of zero length does it every time: nothing moves, so nothing
overlaps, so nothing resolves. That never happens natively, where
clock.tick(60) sleeps and dt is never zero. In a browser the clock is not
paced and it happens constantly, which is how this shipped: a bean resting on
the floor printed "landed" over and over, and isGrounded() flicked false
often enough to let a player jump again in mid-air.

WHAT IS CHECKED

  * resting is grounded, on every frame, including empty ones
  * onGround fires once on landing and not again
  * and the probe has not made the player grounded when they are NOT:
    in the air, or falling, or alongside a wall rather than on top of one
"""
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kaypy.engine as ke                                       # noqa: E402
from kaypy import (kaypy, add, pos, rect, area, body,           # noqa: E402
                   setGravity, width, height)

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


def frame(eng, dt):
    """One frame of physics, driven directly.

    Not through the engine loop: the whole point is to control dt exactly,
    including setting it to zero, which the loop's own clock will not do on
    demand.
    """
    objs = eng._objs
    n = eng.physics.substeps_for(objs, dt)
    for _ in range(n):
        eng.physics.step(objs, dt / n)
        eng.collision.step(objs)


def platformer():
    eng = kaypy(width=800, height=600)
    setGravity(1600)
    player = add([rect(40, 40), pos(400, 300), area(), body()])
    add([rect(width(), 48), pos(0, height() - 48), area(),
         body(isStatic=True)])
    return eng, player


# ------------------------------------------------- resting, on every frame
reset()
eng, player = platformer()
lands = []
player.onGround(lambda: lands.append(1))

for _ in range(90):
    frame(eng, 1 / 60)
check("a body falls and lands", player.isGrounded(),
      "y=%.1f" % player.pos.y)
check("  onGround fired once", len(lands) == 1, "%d times" % len(lands))

states = []
for i in range(20):
    # Every other frame takes no time at all. This is the shape of the bug.
    frame(eng, 1 / 60 if i % 2 == 0 else 0.0)
    states.append(player.isGrounded())
check("still grounded through zero-length frames", all(states),
      "".join("G" if s else "." for s in states))
check("  and onGround did not fire again", len(lands) == 1,
      "%d times" % len(lands))

# A run of nothing-frames, which is what a stalled tab delivers.
for _ in range(10):
    frame(eng, 0.0)
check("and through a run of them", player.isGrounded())
check("  still without firing again", len(lands) == 1, "%d times" % len(lands))

# ---------------------------------------------- but NOT when in the air
#
# The probe reaches one pixel down. If it reached further, or ignored where
# the floor is, everything above would pass while the player hovered — and a
# player who can jump in mid-air is a worse bug than the one being fixed.
reset()
eng, player = platformer()
player.pos.y = 100                       # well above the floor
for _ in range(2):
    frame(eng, 1 / 60)
check("a body in mid-air is not grounded", not player.isGrounded(),
      "y=%.1f" % player.pos.y)

reset()
eng, player = platformer()
for _ in range(90):
    frame(eng, 1 / 60)
player.comp("body").vel.y = -600         # jumping
frame(eng, 1 / 60)
check("a body on the way up is not grounded", not player.isGrounded(),
      "y=%.1f vel=%.0f" % (player.pos.y, player.comp("body").vel.y))

# ------------------------------------------------ a wall is not a floor
reset()
eng = kaypy(width=800, height=600)
setGravity(1600)
# A tall wall, and a body pressed against its side in mid-air.
add([rect(40, 400), pos(300, 100), area(), body(isStatic=True)])
climber = add([rect(40, 40), pos(260, 200), area(), body()])
climber.comp("body").vel.y = 0
for _ in range(2):
    frame(eng, 1 / 60)
check("standing beside a wall is not standing on it",
      not climber.isGrounded(), "y=%.1f" % climber.pos.y)

# ------------------------------------- a moving platform still counts
reset()
eng = kaypy(width=800, height=600)
setGravity(1600)
plat = add([rect(200, 20), pos(300, 400), area(), body(isStatic=True)])
rider = add([rect(30, 30), pos(340, 300), area(), body()])
for _ in range(60):
    frame(eng, 1 / 60)
check("a body lands on a small platform", rider.isGrounded(),
      "y=%.1f" % rider.pos.y)
for _ in range(6):
    frame(eng, 0.0)
check("  and stays grounded on empty frames", rider.isGrounded())

reset()
done()
