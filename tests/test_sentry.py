"""sentry(): the cone, the range, the wall, and the angle that wraps.

    python3 tests/test_sentry.py

A vision cone is mostly arithmetic on angles, and angle arithmetic has one
famous trap: a guard facing 350 degrees looking at something at 10 degrees
is 20 degrees apart, not 340. Subtract the two numbers and compare, and you
get a cone that works perfectly until it happens to straddle zero — which,
since zero is "facing right", is the direction half the guards in any game
are facing.

The other things checked here are the ones that make a stealth game work or
not work at all:

  * range, which KAPLAY has no equivalent of
  * lineOfSight, which must be blocked by a wall and NOT by the target
  * onObjectsSpotted firing on the edge, not sixty times a second
  * checkFrequency actually reducing the work rather than just the reports
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
from kaypy import (kaypy, add, pos, rect, area, sentry, rotate,   # noqa: E402
                   vec2)

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
    """One frame of component updates, at an exact dt."""
    eng._dt = dt
    for obj in list(eng._objs):
        if obj.exists():
            for comp in list(obj._comps.values()):
                comp.update(obj)


def settle(eng, n=20):
    """Enough frames that a check has certainly happened."""
    for _ in range(n):
        frame(eng)


# ------------------------------------------------------------- the cone
#
# Guard at (400, 300) facing right, with a 90-degree cone: 45 degrees either
# side of straight right.
def cone_scene(**opts):
    reset()
    eng = kaypy(width=800, height=600)
    guard = add([rect(20, 20), pos(400, 300), area(),
                 sentry("player", **opts)])
    return eng, guard


eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90)
right = add([rect(10, 10), pos(700, 300), "player"])
settle(eng)
check("something straight ahead is spotted", guard.spotted == [right],
      "%d spotted" % len(guard.spotted))

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90)
add([rect(10, 10), pos(100, 300), "player"])         # directly behind
settle(eng)
check("something behind is not", guard.spotted == [],
      "%d spotted" % len(guard.spotted))

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90)
add([rect(10, 10), pos(400, 100), "player"])         # straight up: 90 off
settle(eng)
check("something at right angles is outside a 90 degree cone",
      guard.spotted == [], "%d spotted" % len(guard.spotted))

# 30 degrees off the middle is inside a 90-degree cone (45 either side) and
# outside a 40-degree one (20 either side). Same geometry, two answers.
import math                                                       # noqa: E402
away = 200
off30 = (400 + away * math.cos(math.radians(30)),
         300 + away * math.sin(math.radians(30)))

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90)
add([rect(10, 10), pos(*off30), "player"])
settle(eng)
check("30 degrees off centre is inside a 90 degree cone",
      len(guard.spotted) == 1)

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=40)
add([rect(10, 10), pos(*off30), "player"])
settle(eng)
check("  and outside a 40 degree one", guard.spotted == [])

# ------------------------------------------------ THE ANGLE THAT WRAPS
#
# Angles come back from atan2 between -180 and 180, so the seam is at
# STRAIGHT LEFT, not at straight right. A guard facing 175 degrees looking
# at something at -175 is ten degrees apart; subtract the two numbers and
# it is 350, which puts it outside every cone.
#
# (The first version of this test used 350 and 10, which is the seam you
# expect from thinking in 0-360 and is not the seam the code has. It passed
# against a deliberately broken implementation, which is the only reason
# this note exists.)
def at(degrees):
    return (400 + away * math.cos(math.radians(degrees)),
            300 + away * math.sin(math.radians(degrees)))


reset()
eng, guard = cone_scene(direction=175, fieldOfView=90)
add([rect(10, 10), pos(*at(185)), "player"])
settle(eng)
check("a cone that straddles straight-left still works",
      len(guard.spotted) == 1,
      "facing 175, target at 185 — 10 apart, or 350 if you subtract")

# And the same trap approached from the other side.
reset()
eng, guard = cone_scene(direction=185, fieldOfView=90)
add([rect(10, 10), pos(*at(175)), "player"])
settle(eng)
check("  in both directions", len(guard.spotted) == 1)

# The seam must not become a hole: something genuinely behind a
# left-facing guard is still out of view.
reset()
eng, guard = cone_scene(direction=180, fieldOfView=90)
add([rect(10, 10), pos(*at(0)), "player"])
settle(eng)
check("  and straight behind is still out of view", guard.spotted == [])

# --------------------------------------------------------- no direction
reset()
eng, guard = cone_scene()
add([rect(10, 10), pos(100, 300), "player"])
add([rect(10, 10), pos(700, 300), "player"])
settle(eng)
check("with no direction it looks every way", len(guard.spotted) == 2,
      "%d spotted" % len(guard.spotted))

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=360)
add([rect(10, 10), pos(100, 300), "player"])
settle(eng)
check("and so does a 360 degree field of view", len(guard.spotted) == 1)

# -------------------------------------------------------------- range
reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90, range=200)
add([rect(10, 10), pos(550, 300), "player"])         # 150 away
settle(eng)
check("something inside the range is spotted", len(guard.spotted) == 1)

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90, range=100)
add([rect(10, 10), pos(550, 300), "player"])         # 150 away
settle(eng)
check("  and outside it is not", guard.spotted == [])

reset()
eng, guard = cone_scene(direction=vec2(1, 0), fieldOfView=90)
add([rect(10, 10), pos(799, 300), "player"])
settle(eng)
check("no range means it sees as far as there is", len(guard.spotted) == 1)

# --------------------------------------------------------- line of sight
#
# A wall between guard and player. Without lineOfSight the guard sees
# through it, which is what KAPLAY does by default and must stay true.
def wall_scene(**opts):
    reset()
    eng = kaypy(width=800, height=600)
    guard = add([rect(20, 20), pos(400, 300), area(),
                 sentry("player", direction=vec2(1, 0), fieldOfView=90,
                        **opts)])
    wall = add([rect(20, 200), pos(550, 200), area(), "wall"])
    player = add([rect(10, 10), pos(700, 300), area(), "player"])
    return eng, guard, wall, player


eng, guard, wall, player = wall_scene()
settle(eng)
check("without lineOfSight a wall does not stop it", len(guard.spotted) == 1)

eng, guard, wall, player = wall_scene(lineOfSight=True)
settle(eng)
check("with lineOfSight a wall does", guard.spotted == [],
      "%d spotted" % len(guard.spotted))

# The target itself must not block the view of the target — it has area(),
# so the ray hits it, and a naive "did the ray hit anything" says blocked.
eng, guard, wall, player = wall_scene(lineOfSight=True)
wall.destroy()
settle(eng)
check("  but the target does not block itself", len(guard.spotted) == 1,
      "the ray hits the player; that is not an obstruction")

# And raycastExclude lets a sentry see past something.
eng, guard, wall, player = wall_scene(lineOfSight=True,
                                      raycastExclude=["wall"])
settle(eng)
check("raycastExclude lets it see past what it is told to ignore",
      len(guard.spotted) == 1)

# ------------------------------------------------- onObjectsSpotted edges
reset()
eng = kaypy(width=800, height=600)
guard = add([rect(20, 20), pos(400, 300), area(),
             sentry("player", direction=vec2(1, 0), fieldOfView=90,
                    range=200)])
player = add([rect(10, 10), pos(700, 300), "player"])   # out of range

calls = []


@guard.onObjectsSpotted
def seen(objects):
    calls.append(len(objects))


settle(eng)
check("nothing spotted, nothing fired", calls == [], calls)

player.pos = vec2(550, 300)                              # into range
settle(eng)
check("it fires when something comes into view", calls == [1], calls)

settle(eng, 60)
check("  and not again while it stays there", calls == [1],
      "%d calls" % len(calls))

player.pos = vec2(700, 300)                              # away again
settle(eng)
check("  nor when it leaves", calls == [1], "%d calls" % len(calls))
check("  and spotted is empty again", guard.spotted == [])

player.pos = vec2(550, 300)                              # and back
settle(eng)
check("  but it fires again on coming back", calls == [1, 1], calls)

# ------------------------------------------------------- checkFrequency
#
# The point of checkFrequency is doing LESS WORK, not reporting less. So
# count how many times the candidates are actually looked at.
reset()
eng = kaypy(width=800, height=600)
looks = []


def watched():
    looks.append(1)
    return []


guard = add([rect(20, 20), pos(400, 300), area(),
             sentry(watched, checkFrequency=10)])
for _ in range(60):                                      # one second
    frame(eng, 1 / 60)
check("checkFrequency=10 looks ten times a second, not sixty",
      9 <= len(looks) <= 11, "%d looks in 60 frames" % len(looks))

reset()
looks.clear()
eng = kaypy(width=800, height=600)
add([rect(20, 20), pos(400, 300), area(), sentry(watched, checkFrequency=60)])
for _ in range(60):
    frame(eng, 1 / 60)
check("  and 60 looks every frame", 55 <= len(looks) <= 60,
      "%d looks" % len(looks))

# ------------------------------------------------- what to look for
reset()
eng = kaypy(width=800, height=600)
dog = add([rect(10, 10), pos(420, 300)])
guard = add([rect(20, 20), pos(400, 300), area(), sentry(dog)])
settle(eng)
check("a sentry can watch one object rather than a tag",
      guard.spotted == [dog])

reset()
eng = kaypy(width=800, height=600)
a = add([rect(10, 10), pos(420, 300), "cat"])
b = add([rect(10, 10), pos(440, 300)])
guard = add([rect(20, 20), pos(400, 300), area(), sentry(["cat", b])])
settle(eng)
check("  or a mix of tags and objects", sorted(
    id(o) for o in guard.spotted) == sorted([id(a), id(b)]),
    "%d spotted" % len(guard.spotted))

# A sentry never spots itself, however wide its view.
reset()
eng = kaypy(width=800, height=600)
guard = add([rect(20, 20), pos(400, 300), area(), sentry("guard"), "guard"])
settle(eng)
check("and never spots itself", guard.spotted == [])

# ------------------------------------------------ facing follows rotate()
reset()
eng = kaypy(width=800, height=600)
turret = add([rect(20, 20), pos(400, 300), area(), rotate(0),
              sentry("player", fieldOfView=60)])
add([rect(10, 10), pos(400, 500), "player"])             # straight down
settle(eng)
check("a turret at angle 0 does not see what is below it",
      turret.spotted == [])

turret.angle = 90                                        # now facing down
settle(eng)
check("  and does once it is turned to face it", len(turret.spotted) == 1,
      "rotate() sets the facing when no direction is given")

# --------------------------------------------------------------- errors
reset()
kaypy(width=800, height=600)


def message(fn):
    try:
        fn()
    except Exception as e:                                       # noqa: BLE001
        return "%s: %s" % (type(e).__name__, e)
    return ""


m = message(lambda: sentry(42))
check("sentry(42) says what it wants", "tag" in m and "sentry(" in m,
      m.split("\n")[0][:58])
m = message(lambda: sentry("player", fieldOfView=400))
check("a field of view over 360 is refused", "360" in m, m[:58])
m = message(lambda: sentry("player", range=0))
check("range=0 is refused", "above zero" in m, m[:58])
m = message(lambda: sentry("player", checkFrequency=0))
check("checkFrequency=0 is refused", "above zero" in m, m[:58])
m = message(lambda: sentry("player", direction="north"))
check("direction='north' explains the two forms",
      "vec2" in m and "degrees" in m, m.split("\n")[0][:58])

reset()
done()
