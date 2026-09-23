"""setCamScale(vec2(2, 0.4)): a different zoom on each axis.

    python3 tests/test_cam_scale.py

The camera's scale used to be one number. Making it two is the kind of
change that appears to work immediately — the world stretches, the sprites
stretch — while leaving behind every place that multiplied by the old
single number and now silently uses only one axis, or crashes on an `int()`
of a vector. Those places are the unglamorous ones: the debug boxes, the
size of drawn text, the mouse position, a circle's radius.

So this measures pixels. A white block is drawn on a black screen and the
lit region is found by reading the surface back, which is the same thing a
player's eye does and does not care how the number got there.

ALSO CHECKED

  * a plain number still means the same on both axes, as it always did
  * screen and world coordinates still convert back into each other, which
    is what makes a mouse click land where it was aimed
  * scale 0 is refused rather than dividing by zero somewhere later
"""
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame                                                     # noqa: E402
import kaypy.engine as ke                                         # noqa: E402
from kaypy import (kaypy, add, pos, rect, color, anchor,          # noqa: E402
                   setCamScale, setCamPos, vec2)

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


def lit_box(eng):
    """Draw one frame and report the bounding box of everything non-black.

    Through pygame.mask rather than pygame.surfarray. surfarray is the
    obvious way to read pixels back and it needs numpy, which kaypy does not
    depend on — `pygame-ce==2.5.8` is the whole of `dependencies`. Written
    that way this file passed on any machine that happened to have numpy
    installed for something else, and failed in CI, which has exactly what
    the package asks for and nothing more. That is the right outcome and a
    bad way to find out.

    pygame.mask is core pygame-ce. from_threshold marks the pixels near
    black; inverting it marks everything that was drawn.
    """
    screen = eng.screen
    screen.fill((0, 0, 0))
    eng.render.draw(eng._objs, screen, eng.camera, False, eng.events.draw_handlers)

    mask = pygame.mask.from_threshold(screen, (0, 0, 0), (14, 14, 14, 255))
    mask.invert()
    rects = mask.get_bounding_rects()
    if not rects:
        return None
    box = rects[0]
    for other in rects[1:]:
        box = box.union(other)
    return (box.left, box.top, box.right - 1, box.bottom - 1)


def measured(scale):
    """The on-screen size of a 100x100 block at the middle of the camera."""
    reset()
    eng = kaypy(width=800, height=600)
    add([rect(100, 100), pos(400, 300), anchor("center"),
         color(255, 255, 255)])
    setCamPos(vec2(400, 300))
    setCamScale(scale)
    box = lit_box(eng)
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return (x1 - x0 + 1, y1 - y0 + 1)


# ------------------------------------------------------- a plain number
size = measured(1)
check("at scale 1 a 100x100 block is about 100x100", size is not None and
      all(abs(n - 100) <= 2 for n in size), "%s" % (size,))

size = measured(2)
check("at scale 2 it is about 200x200", size is not None and
      all(abs(n - 200) <= 3 for n in size), "%s" % (size,))

size = measured(0.5)
check("at scale 0.5 it is about 50x50", size is not None and
      all(abs(n - 50) <= 2 for n in size), "%s" % (size,))

# ------------------------------------------------------ a vector scale
size = measured(vec2(2, 0.4))
check("vec2(2, 0.4) makes it wide and flat",
      size is not None and abs(size[0] - 200) <= 3 and abs(size[1] - 40) <= 3,
      "%s (expected about (200, 40))" % (size,))

size = measured(vec2(0.4, 2))
check("  and vec2(0.4, 2) makes it tall and narrow",
      size is not None and abs(size[0] - 40) <= 3 and abs(size[1] - 200) <= 3,
      "%s (expected about (40, 200))" % (size,))

check("a plain tuple works too", measured((2, 0.4)) == measured(vec2(2, 0.4)))

# ----------------------------------------- the two conversions still agree
#
# A click lands where it was aimed only if screen_to_world undoes
# world_to_screen. With one number that was hard to get wrong; with two,
# using x twice is an easy typo that stretches the world correctly and puts
# every mouse click in the wrong place.
reset()
eng = kaypy(width=800, height=600)
setCamPos(vec2(400, 300))
setCamScale(vec2(2, 0.4))
bad = []
for point in (vec2(0, 0), vec2(400, 300), vec2(770, 90), vec2(-200, 900)):
    back = eng.camera.screen_to_world(eng.camera.world_to_screen(point))
    if abs(back.x - point.x) > 1e-6 or abs(back.y - point.y) > 1e-6:
        bad.append((point, back))
check("world -> screen -> world comes back to the same point", not bad,
      "%s" % (bad[:2] if bad else "4 points checked"))

# The two axes must genuinely differ on screen, or the check above would
# pass for a camera that ignored y entirely.
a = eng.camera.world_to_screen(vec2(500, 400))
b = eng.camera.world_to_screen(vec2(400, 300))
check("  and the axes are scaled by different amounts",
      abs((a.x - b.x) - 200) < 1e-6 and abs((a.y - b.y) - 40) < 1e-6,
      "100 world px -> %.0f across, %.0f down" % (a.x - b.x, a.y - b.y))

# ----------------------------------------------- the camera still moves
reset()
eng = kaypy(width=800, height=600)
add([rect(50, 50), pos(400, 300), anchor("center"), color(255, 255, 255)])
setCamScale(vec2(2, 0.4))
setCamPos(vec2(400, 300))
centred = lit_box(eng)
setCamPos(vec2(300, 300))                 # look 100px to the left
moved = lit_box(eng)
check("moving the camera still moves what you see",
      centred and moved and moved[0] > centred[0],
      "block moved right by %d px when the camera moved left 100"
      % (moved[0] - centred[0] if centred and moved else 0))
check("  by the stretched amount, not the raw one",
      centred and moved and abs((moved[0] - centred[0]) - 200) <= 3,
      "%d px (100 world px at 2x across)"
      % (moved[0] - centred[0] if centred and moved else 0))

# --------------------------------------------------------------- errors
reset()
kaypy(width=800, height=600)


def message(fn):
    try:
        fn()
    except Exception as e:                                       # noqa: BLE001
        return "%s: %s" % (type(e).__name__, e)
    return ""


m = message(lambda: setCamScale(0))
check("a scale of 0 is refused", "zero" in m, m[:62])
m = message(lambda: setCamScale(vec2(2, 0)))
check("  including on one axis only", "zero" in m, m[:62])
m = message(lambda: setCamScale("big"))
check("setCamScale('big') shows both forms",
      "vec2" in m and "setCamScale(2)" in m, m.split("\n")[0][:62])

reset()
done()
