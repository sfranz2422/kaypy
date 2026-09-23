"""A body standing still must stay on exactly the same pixel.

    python3 tests/test_resting.py

THE BUG THIS EXISTS FOR

A bean standing on the floor of a platformer visibly twitched — one pixel
up, one pixel down, a few times a second, in a browser but not on a
desktop. Measured off the canvas it was unmistakable: the identical run of
pixel rows, redrawn one row lower every third or fourth frame.

The bean was not moving. Every frame it sank a fraction of a pixel under
gravity and every frame the push-out lifted it back, and it landed within
about a hundred-thousandth of a pixel of where it started — the width of a
32-bit float near y=512, which is the precision pygame.FRect keeps and
therefore the precision the push-out has. Half the time that left it at
512.00001, half the time at 511.99999, and a renderer that truncates to
whole pixels draws those on different rows.

So this file measures the DRAWN position, not pos.y. Watching pos.y is how
the bug survived a first attempt at fixing it: pos.y looked stable to a
decimal place or two and the bean went on twitching.

WHAT IS CHECKED

  * a resting body's drawn position never changes, under steady frames,
    under browser-shaped ragged frames, and under a burst of empty ones
  * it does not sit there accumulating fall speed
  * and none of that has cost anything: it still falls, still lands where
    it should, and cannot jump twice.
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
    """One frame of physics at an exact dt — including zero, which the
    engine's own clock will not produce on demand."""
    objs = eng._objs
    n = eng.physics.substeps_for(objs, dt)
    for _ in range(n):
        eng.physics.step(objs, dt / n)
        eng.collision.step(objs)


def drawn_y(obj):
    """Where the renderer would actually put it. The screen has no
    sub-pixels, so this — not pos.y — is what a player sees."""
    from kaypy.geometry import get_topleft
    return int(get_topleft(obj).y)


def platformer():
    eng = kaypy(width=800, height=600)
    setGravity(1600)
    player = add([rect(40, 40), pos(400, 300), area(), body()])
    add([rect(width(), 48), pos(0, height() - 48), area(),
         body(isStatic=True)])
    return eng, player


def settle(eng, player):
    for _ in range(90):
        frame(eng, 1 / 60)
    assert player.isGrounded(), "the body never landed; test is meaningless"


# ------------------------------------------------------- steady frames
reset()
eng, player = platformer()
settle(eng, player)

seen = set()
exact = set()
for _ in range(60):
    frame(eng, 1 / 60)
    seen.add(drawn_y(player))
    exact.add(repr(player.pos.y))
check("steady 60fps: never moves", len(seen) == 1, sorted(seen))
# Not "close enough". One unit in the last place of a double is the whole
# bug: 497.99999999999994 and 498.0 are the same position to any person
# and different pixels to int().
check("  and holds the identical value, to the last bit",
      len(exact) == 1, ", ".join(sorted(exact)))

# --------------------------------------------- browser-shaped frames
#
# The real pattern off a browser: mostly short frames, the odd long one,
# and near-zero frames in bursts. dt is capped at 0.05 by the engine.
reset()
eng, player = platformer()
settle(eng, player)

ragged = [1 / 60, 0.0004, 0.0002, 1 / 120, 0.05, 0.0, 0.0, 1 / 60,
          0.0009, 1 / 240, 0.0, 1 / 60]
seen = set()
exact = set()
vels = []
for i in range(120):
    frame(eng, ragged[i % len(ragged)])
    seen.add(drawn_y(player))
    exact.add(repr(player.pos.y))
    vels.append(player.comp("body").vel.y)
check("ragged browser frames: never moves", len(seen) == 1, sorted(seen))
check("  and still to the last bit", len(exact) == 1,
      ", ".join(sorted(exact)))
check("  and fall speed never builds up", max(vels) < 30.0,
      "peak vel.y = %.1f" % max(vels))

# ------------------------------------------------ a burst of nothing
reset()
eng, player = platformer()
settle(eng, player)
resting = drawn_y(player)
for _ in range(30):
    frame(eng, 0.0)
check("a stalled tab does not move it", drawn_y(player) == resting,
      "%d -> %d" % (resting, drawn_y(player)))
check("  and it is still grounded afterwards", player.isGrounded())

# ---------------------------------------------- none of this broke falling
#
# Parking a resting body is only safe if "resting" is still strict. If the
# snap or the velocity reset leaked into bodies that are in the air, the
# checks above would pass while gravity quietly stopped working.
reset()
eng, player = platformer()
player.pos.y = 100
ys = []
for _ in range(6):
    frame(eng, 1 / 60)
    ys.append(player.pos.y)
check("a body in the air still accelerates downward",
      all(ys[i] - ys[i - 1] > ys[i - 1] - ys[i - 2] for i in range(2, 6)),
      "y: " + ", ".join("%.1f" % y for y in ys))
check("  and is not grounded up there", not player.isGrounded())

reset()
eng, player = platformer()
settle(eng, player)
floor_y = player.pos.y
player.comp("body").vel.y = -800                 # jump
frame(eng, 1 / 60)
check("a jump is not cancelled by the ground under it",
      player.comp("body").vel.y < -700 and player.pos.y < floor_y,
      "vel=%.0f y=%.1f" % (player.comp("body").vel.y, player.pos.y))
check("  and mid-jump is not grounded", not player.isGrounded())

# A very short frame right after take-off: barely off the floor, still
# within the probe's reach. Reporting grounded here is a free double jump.
reset()
eng, player = platformer()
settle(eng, player)
player.comp("body").vel.y = -800
frame(eng, 0.0005)
check("nor is it grounded on a near-zero frame after take-off",
      not player.isGrounded(), "y=%.2f" % player.pos.y)

# And it must land properly at the end of all that.
reset()
eng, player = platformer()
settle(eng, player)
rest = player.pos.y
player.comp("body").vel.y = -800
for i in range(200):
    frame(eng, ragged[i % len(ragged)])
check("and it comes back down and lands where it started",
      player.isGrounded() and abs(player.pos.y - rest) < 0.01,
      "y=%.3f (was %.3f)" % (player.pos.y, rest))

reset()
done()
