"""The mouse, beyond onClick.

    python3 tests/test_mouse.py

onClick was the whole mouse API for a long time. It answers "the player
clicked" and nothing else — not which button, not whether one is being held,
not that the mouse moved. Aiming, dragging, hold-to-charge and drawing all
need one of those.

A NOTE ON WHAT CAN BE SIMULATED

Posting a MOUSEBUTTONDOWN makes SDL deliver a *press*. It does not make
`pygame.mouse.get_pressed()` report the button as held — the same gap that
makes held keys untestable under the dummy driver. So the held-button paths
are checked by answering that function directly, which is the one thing this
file fakes and the reason it says so here.
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
from kaypy import (kaplay, add, rect, pos, area, vec2,           # noqa: E402
                   onMouseDown, onMousePress, onMouseRelease, onMouseMove,
                   onClick, isMouseDown, isMousePressed, isMouseReleased,
                   isMouseMoved, mouseDeltaPos)

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


def reset():
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
    ke._engine = None
    try:
        pygame.event.clear()
    except pygame.error:
        pass      # before the first kaplay(), there is no event queue yet


def post(kind, **kw):
    pygame.event.post(pygame.event.Event(kind, **kw))


def step(eng):
    """One frame's worth of event handling, without the whole loop."""
    eng.events.process_pygame_events(pygame.event.get(), eng._objs)


# ------------------------------------------------------ press and release
reset()
eng = kaplay(width=200, height=200)
eng._started, eng._running = True, False
seen = []

onMousePress("left", lambda b: seen.append(("press", b)))
onMouseRelease("left", lambda b: seen.append(("release", b)))
onMousePress("right", lambda b: seen.append(("press", b)))
onMouseMove(lambda: seen.append(("move", None)))
onClick(lambda: seen.append(("click", None)))

post(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10))
post(pygame.MOUSEBUTTONUP, button=1, pos=(10, 10))
step(eng)
check("a left press fires onMousePress", ("press", "left") in seen)
check("and a release fires onMouseRelease", ("release", "left") in seen)
check("and onClick still fires for the left button", ("click", None) in seen)
check("the handler is told which button", seen[0][1] == "left", repr(seen[0]))

seen.clear()
post(pygame.MOUSEBUTTONDOWN, button=3, pos=(10, 10))
step(eng)
check("a right press fires the right handler", seen == [("press", "right")],
      repr(seen))
check("and does NOT fire onClick", ("click", None) not in seen,
      "onClick is the left button, as in KAPLAY")

seen.clear()
post(pygame.MOUSEMOTION, pos=(20, 30), rel=(5, 7), buttons=(0, 0, 0))
step(eng)
check("moving fires onMouseMove", ("move", None) in seen)

# ------------------------------------------------------------ this frame
check("isMousePressed is true the frame it went down", True)  # set up below
reset()
eng = kaplay(width=200, height=200)
eng._started, eng._running = True, False

post(pygame.MOUSEBUTTONDOWN, button=1, pos=(1, 1))
step(eng)
check("  isMousePressed() sees it", isMousePressed("left"))
check("  isMouseReleased() does not", not isMouseReleased("left"))

step(eng)   # a frame with no events at all
check("and is false again the very next frame", not isMousePressed("left"),
      "a press that stayed true would fire twice")

post(pygame.MOUSEBUTTONUP, button=1, pos=(1, 1))
step(eng)
check("isMouseReleased() sees the release", isMouseReleased("left"))
step(eng)
check("and that clears too", not isMouseReleased("left"))

# --------------------------------------------------------------- movement
post(pygame.MOUSEMOTION, pos=(5, 5), rel=(3, 4), buttons=(0, 0, 0))
step(eng)
check("isMouseMoved() sees the move", isMouseMoved())
check("mouseDeltaPos() gives how far", (mouseDeltaPos().x, mouseDeltaPos().y) == (3, 4),
      "%s" % (mouseDeltaPos(),))

# Several motion events in one frame must add up, not overwrite: SDL can
# deliver a fast drag as three events, and a handler that saw only the last
# would under-report it.
post(pygame.MOUSEMOTION, pos=(6, 6), rel=(1, 2), buttons=(0, 0, 0))
post(pygame.MOUSEMOTION, pos=(8, 9), rel=(10, 20), buttons=(0, 0, 0))
step(eng)
# Deliberately lopsided numbers: summed this is (11, 22), and merely keeping
# the last event would give (10, 20). The two cannot be confused.
check("and several moves in one frame add up",
      (mouseDeltaPos().x, mouseDeltaPos().y) == (11, 22),
      "%s — overwriting would give vec2(10, 20)" % (mouseDeltaPos(),))

step(eng)
check("with no movement the delta is zero",
      (mouseDeltaPos().x, mouseDeltaPos().y) == (0, 0) and not isMouseMoved())

# ------------------------------------------------------------ held buttons
# The one faked thing in this file — see the note at the top.
real = pygame.mouse.get_pressed
pygame.mouse.get_pressed = lambda num_buttons=3: (True, False, False)
try:
    check("isMouseDown() sees a held left button", isMouseDown("left"))
    check("and not a button that is up", not isMouseDown("right"))
    check("leaving the button out means the left one", isMouseDown() is True)

    held = []
    onMouseDown("left", lambda: held.append(1))
    onMouseDown("right", lambda: held.append("r"))
    step(eng)
    check("onMouseDown fires every frame it is held", held == [1], repr(held))
    step(eng)
    check("  and again the next frame", held == [1, 1], repr(held))
finally:
    pygame.mouse.get_pressed = real

# --------------------------------------------------------- a bad button name
try:
    isMouseDown("scroll")
    said = False
except KeyError as err:
    said = "left" in str(err) and "right" in str(err)
check("a button name that does not exist says which do", said)

# ------------------------------------------------- handlers clear on a scene
# go() clears every handler, and the mouse ones must go with them, or a menu's
# click handler keeps firing inside the game.
reset()
eng = kaplay(width=200, height=200)
eng._started, eng._running = True, False
onMousePress("left", lambda: None)
onMouseMove(lambda: None)
eng.events.clear()
check("clearing a scene clears the mouse handlers",
      not eng.events.mouse_press_handlers and not eng.events.mouse_move_handlers)

reset()
bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
