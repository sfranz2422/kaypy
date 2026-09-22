"""onDraw, and the functions that only work inside it.

    python3 tests/test_drawing.py

These draw to a surface, so what can be checked here is stronger than usual:
the surface is real, and the pixels it ends up with are the answer. A
rectangle drawn red means a red pixel where the rectangle is, and a
background-coloured pixel where it is not.

The two things worth being strict about, because both fail silently:

  * a draw call made outside onDraw must RAISE, not quietly do nothing. A
    drawing that never appears is close to undebuggable for a beginner.
  * `fixed=True` must ignore the camera and `fixed=False` must not, or a HUD
    slides off the screen the first time the camera moves.
"""
import asyncio
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame                                                   # noqa: E402
import kaypy.engine as ke                                       # noqa: E402
from kaypy import (kaplay, onDraw, drawRect, drawCircle, drawLine,  # noqa: E402
                   drawLines, drawText, vec2, rgb, setCamPos)

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def reset():
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
    ke._engine = None


def render(eng):
    """One draw pass, exactly as the frame loop does it."""
    eng.screen.fill(eng._background)
    eng.render.draw(eng._objs, eng.screen, eng.camera, False,
                    eng.events.draw_handlers)
    return eng.screen


def at(screen, x, y):
    return tuple(screen.get_at((int(x), int(y))))[:3]


BG = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# ------------------------------------ outside onDraw, it must say so
reset()
try:
    drawRect(pos=vec2(0, 0), width=10, height=10)
    said = "it did not raise at all"
except RuntimeError as err:
    said = str(err)
check("drawing outside onDraw raises", "onDraw" in said,
      said.splitlines()[0][:56])
check("and the message shows what to write", "@onDraw" in said)

# ------------------------------------------------------- it actually draws
reset()
eng = kaplay(width=200, height=200, background=BG)
eng._started, eng._running = True, False


@onDraw
def paint():
    drawRect(pos=vec2(20, 20), width=40, height=40, color=RED, fixed=True)
    drawCircle(pos=vec2(150, 50), radius=20, color=BLUE, fixed=True)
    drawLine(p1=vec2(0, 190), p2=vec2(200, 190), width=4, color=RED, fixed=True)


screen = render(eng)
check("a rectangle puts its colour on the screen", at(screen, 30, 30) == RED,
      "%s at (30,30)" % (at(screen, 30, 30),))
check("and only where it is", at(screen, 90, 30) == BG,
      "%s at (90,30)" % (at(screen, 90, 30),))
check("its top-left corner is where pos says", at(screen, 21, 21) == RED
      and at(screen, 18, 18) == BG)
check("a circle draws, centred on pos", at(screen, 150, 50) == BLUE,
      "%s at the centre" % (at(screen, 150, 50),))
check("and is round — its corner is empty", at(screen, 134, 34) == BG)
check("a line draws", at(screen, 100, 190) == RED,
      "%s on the line" % (at(screen, 100, 190),))

# ------------------------------------------------------------- anchoring
reset()
eng = kaplay(width=200, height=200, background=BG)
eng._started, eng._running = True, False


@onDraw
def centred():
    drawRect(pos=vec2(100, 100), width=40, height=40, color=RED,
             anchor="center", fixed=True)


screen = render(eng)
check("anchor='center' centres it on pos", at(screen, 100, 100) == RED
      and at(screen, 82, 82) == RED and at(screen, 78, 78) == BG,
      "the square spans 80..120")

try:
    reset()
    eng = kaplay(width=100, height=100)
    eng._started, eng._running = True, False
    onDraw(lambda: drawRect(pos=vec2(0, 0), width=5, height=5, anchor="nope"))
    render(eng)
    said = False
except ValueError as err:
    said = "anchor" in str(err)
check("an anchor name that does not exist is rejected", said,
      "the same error a game object gives")

# ------------------------------------------------- the camera, and fixed
reset()
eng = kaplay(width=200, height=200, background=BG)
eng._started, eng._running = True, False


@onDraw
def both():
    drawRect(pos=vec2(100, 100), width=20, height=20, color=RED,
             anchor="center", fixed=True)
    drawRect(pos=vec2(100, 100), width=20, height=20, color=BLUE,
             anchor="center")           # world space — moves with the camera


screen = render(eng)
check("before the camera moves, both are in the middle",
      at(screen, 100, 100) in (RED, BLUE))

setCamPos(vec2(150, 100))       # look 50px to the right
screen = render(eng)
check("fixed=True ignores the camera", at(screen, 100, 100) == RED,
      "a HUD stays put")
check("and world space follows it", at(screen, 50, 100) == BLUE,
      "%s at (50,100) — the world square slid left" % (at(screen, 50, 100),))

# ------------------------------------------------------------ text, lines
reset()
eng = kaplay(width=200, height=200, background=BG)
eng._started, eng._running = True, False


@onDraw
def words():
    drawText(text="HI", pos=vec2(10, 10), size=40, color=RED, fixed=True)
    drawLines(points=[vec2(10, 150), vec2(60, 150), vec2(60, 180)],
              width=3, color=BLUE, fixed=True)


screen = render(eng)
painted = sum(1 for x in range(0, 120) for y in range(0, 60)
              if at(screen, x, y) != BG)
check("drawText puts pixels on the screen", painted > 20,
      "%d non-background pixels" % painted)
check("drawLines draws each segment",
      at(screen, 30, 150) == BLUE and at(screen, 60, 170) == BLUE)

# --------------------------------------------------- order and clearing
reset()
eng = kaplay(width=100, height=100, background=BG)
eng._started, eng._running = True, False
order = []
onDraw(lambda: order.append("first"))
onDraw(lambda: order.append("second"))
render(eng)
check("handlers run in the order they were added", order == ["first", "second"],
      repr(order))

eng.events.clear()
order.clear()
render(eng)
check("and a scene change clears them", order == [],
      "or a menu's HUD is still drawn over the game")

# An onDraw that raises must not be swallowed — it is the student's bug.
reset()
eng = kaplay(width=100, height=100)
eng._started, eng._running = True, False
onDraw(lambda: drawRect(pos=vec2(0, 0), width=10, height=10, color="not a colour"))
try:
    render(eng)
    raised = False
except Exception:                                              # noqa: BLE001
    raised = True
check("a mistake inside onDraw surfaces, not swallowed", raised)

# ...and the guard is released even so, or every later draw call would think
# a frame was still being drawn.
from kaypy import drawing                                      # noqa: E402
check("and the draw window closes even after an error",
      drawing._target is None)

reset()
bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
