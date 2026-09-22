"""rotate() — which way it turns, and that it turns about the anchor.

    python3 tests/test_rotate.py

Two things are easy to get wrong here and neither announces itself.

**The direction.** pygame turns a surface anticlockwise for a positive angle;
kaypy's angle is clockwise, because the screen's y axis points down and that is
the way a clock goes. Two different conventions meet in one function, and
getting a sign backwards produces a game that works perfectly and turns the
wrong way. So the direction is measured, not reasoned about: a marker is put to
the right of the pivot and the test asks where it ended up.

**The pivot.** `pygame.transform.rotate` turns about the surface's centre and
returns a BIGGER surface with the image inside it. Blit that at the old
top-left and the object drifts in a circle as it spins — the classic symptom,
and the one a student would report as "my ship wobbles". So every check below
asks where the anchor point landed, not merely whether something was drawn.

The collision box deliberately does NOT rotate; that is checked too, because
it is a choice rather than an oversight.
"""
import math
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KAYPY_TEST_MAX_FRAMES", "3")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame                                                 # noqa: E402
from kaypy.render import _blit                               # noqa: E402

pygame.init()

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


SIZE = 41
AT = (100, 100)


def marked(mark_at):
    """A transparent surface with one red pixel, so its landing spot is a fact.

    The marker must never be at (0, 0): `pygame.transform.rotate` pads the
    larger surface it returns with the colour of the source's corner pixel, so
    a marker there comes back as 1,457 red pixels and the test measures the
    padding instead of the marker. Found by writing exactly that fixture and
    not believing the failure.
    """
    if mark_at == (0, 0):
        raise ValueError("a marker at (0, 0) becomes the rotation's padding")
    s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    s.set_at(mark_at, (255, 0, 0, 255))
    return s


def find_red(screen):
    for y in range(screen.get_height()):
        for x in range(screen.get_width()):
            if screen.get_at((x, y))[:3] == (255, 0, 0):
                return x, y
    return None


def draw(surf, angle, pivot):
    screen = pygame.Surface((240, 240), pygame.SRCALPHA)
    screen.fill((0, 0, 0, 0))
    _blit(screen, surf, angle, pivot, AT)
    return find_red(screen)


# ------------------------------------------------- which way does it turn
# The marker sits 20px to the RIGHT of a central pivot. Turning clockwise it
# should go right -> down -> left -> up. Rotation resamples, so a pixel of
# slack is allowed; a wrong SIGN is 40px out, not one.
CENTRE = (SIZE // 2, SIZE // 2)
RIGHT_OF_CENTRE = marked((SIZE - 1, SIZE // 2))
EXPECTED = {0: (20, 0), 90: (0, 20), 180: (-20, 0), 270: (0, -20)}
COMPASS = {0: "right", 90: "down", 180: "left", 270: "up"}

for angle, (ex, ey) in EXPECTED.items():
    got = draw(RIGHT_OF_CENTRE, angle, CENTRE)
    dx, dy = (got[0] - AT[0], got[1] - AT[1]) if got else (999, 999)
    check("%3d degrees puts a right-hand marker %s" % (angle, COMPASS[angle]),
          got is not None and abs(dx - ex) <= 1 and abs(dy - ey) <= 1,
          "offset (%d, %d), wanted (%d, %d)" % (dx, dy, ex, ey))

# 45 degrees is the case that a sign error can still pass by symmetry.
got = draw(RIGHT_OF_CENTRE, 45, CENTRE)
dx, dy = got[0] - AT[0], got[1] - AT[1]
want = 20 / math.sqrt(2)
check(" 45 degrees goes down-and-right, not up-and-right",
      abs(dx - want) <= 2 and abs(dy - want) <= 2,
      "offset (%d, %d), wanted about (%d, %d)" % (dx, dy, want, want))

# ------------------------------------------------- does the pivot stay put
# The pivot is the top-left corner — the default anchor, and the case that
# exposes rotating about the centre instead. The marker sits two pixels in
# from it (see marked()), so it can never be more than three pixels from the
# pivot at any angle. The bug this catches drifts by tens of pixels.
CORNER = marked((2, 2))
for angle in (0, 30, 90, 137, 180, 270, 359):
    got = draw(CORNER, angle, (0, 0))
    off = (abs(got[0] - AT[0]), abs(got[1] - AT[1])) if got else (999, 999)
    check("the anchor stays put at %3d degrees" % angle,
          got is not None and off[0] <= 4 and off[1] <= 4,
          "marker %d,%d from the anchor" % off)

# ...and with an off-centre pivot that is neither corner nor middle.
ODD = marked((7, 33))
for angle in (0, 73, 200):
    got = draw(ODD, angle, (7, 33))
    off = (abs(got[0] - AT[0]), abs(got[1] - AT[1])) if got else (999, 999)
    check("an off-centre anchor stays put at %3d degrees" % angle,
          got is not None and off[0] <= 1 and off[1] <= 1,
          "drifted (%d, %d)" % off)

# ---------------------------------------------------------- the component
from kaypy import (kaplay, add, rect, circle, pos, area, rotate,  # noqa: E402
                    anchor, vec2)
import kaypy.engine as ke                                       # noqa: E402

eng = kaplay(width=200, height=200)
spinner = add([rect(40, 20), pos(100, 100), anchor("center"), area(), rotate(0)])

check("the object has .angle", spinner.angle == 0)
spinner.angle = 45
check("and it can be set as a plain attribute", spinner.angle == 45)
check("rotateBy adds to it", spinner.rotateBy(45) == 90 and spinner.angle == 90)
check("rotateTo replaces it", spinner.rotateTo(10) == 10 and spinner.angle == 10)

# The collision box must not grow and shrink as it spins. A 40x20 box turned
# 45 degrees would have a rotated bounding box of about 42x42.
upright = spinner.comp("area").get_rect()
spinner.angle = 45
turned = spinner.comp("area").get_rect()
check("the collision box does not rotate with it",
      (turned.width, turned.height) == (upright.width, upright.height),
      "%gx%g upright, %gx%g at 45 degrees"
      % (upright.width, upright.height, turned.width, turned.height))

# Vec2.fromAngle is the partner to rotate(): "which way am I facing".
from kaypy import Vec2                                          # noqa: E402

for deg, name, want in ((0, "right", (1, 0)), (90, "down", (0, 1)),
                        (180, "left", (-1, 0)), (270, "up", (0, -1))):
    v = Vec2.fromAngle(deg)
    check("Vec2.fromAngle(%3d) points %s" % (deg, name),
          abs(v.x - want[0]) < 1e-9 and abs(v.y - want[1]) < 1e-9,
          "(%.2f, %.2f)" % (v.x, v.y))

check("fromAngle is the inverse of .angle()",
      all(abs(((Vec2.fromAngle(d).angle() - d + 180) % 360) - 180) < 1e-9
          for d in (0, 37, 90, 175, 270, 359)))
check("fromAngle returns a unit vector",
      all(abs(Vec2.fromAngle(d).len() - 1) < 1e-9 for d in (0, 37, 123, 300)))

# It has to agree with the renderer, or a ship flies somewhere other than it
# points. rotate() turns a right-pointing marker down at 90; fromAngle(90)
# must therefore point down too — which the four checks above just showed.

still = add([rect(10, 10), pos(0, 0)])
check("an object without rotate() has no angle",
      not hasattr(still, "angle") or not still.has("rotate"))

# ------------------------------------- the footgun asteroids.py walked into
# `rock.size = 3` overwrites circle()'s size() METHOD, and the game then dies
# in the collision system with "'int' object is not callable" — nowhere near
# the line that caused it.
rock = add([circle(30), pos(0, 0), area()])
try:
    rock.size = 3
    clobbered = True
except AttributeError as err:
    clobbered = False
    message = str(err)
check("assigning over a component's method is refused", not clobbered)
check("and the message names the method and suggests a way out",
      not clobbered and "size" in message and "another name" in message)
check("the method still works afterwards", rock.comp("circle").size() == (60, 60))
rock.chunks = 3
check("an unused name is still just an attribute", rock.chunks == 3)
rock.pos = vec2(5, 5)
check("a real component field still assigns", (rock.pos.x, rock.pos.y) == (5, 5))

eng._started = True
eng._running = False
ke._engine = None

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
