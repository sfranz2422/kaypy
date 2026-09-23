"""The on-screen joystick holds keys down, so old games work on a phone.

    python3 tests/test_joystick.py

The whole promise is that a thumb is indistinguishable from a keyboard. So
what is checked is not "the overlay drew something" but that every way a game
can ask about a key agrees with every other way:

    onKeyDown       reads what is held, every frame
    isKeyDown       the same question, asked rather than answered
    onKeyPress      the event queue, once, on the way down
    onKeyRelease    the event queue, once, on the way up

A joystick that satisfied three of those and not the fourth would work in
most lessons and fail in whichever one a student happened to write.

AND MULTI-TOUCH, WHICH IS NOT A LUXURY

A platformer needs run and jump together. Tracked by one pointer, pressing
jump would release right — so the games this exists for would be the ones it
broke. Two fingers are put down here and both are expected to hold.
"""
import asyncio
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "100000"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame                                                   # noqa: E402
import kaypy.engine as ke                                       # noqa: E402
from kaypy import (kaypy, add, pos, rect, onKeyDown, onKeyPress,  # noqa: E402
                   onKeyRelease, isKeyDown)
from kaypy.events import resolve_key                            # noqa: E402

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
    try:
        pygame.event.clear()
    except pygame.error:
        pass


async def frames(engine, n):
    engine._running = True
    engine._started = False
    task = asyncio.ensure_future(engine.run_async())
    for _ in range(n):
        if task.done():
            break
        await asyncio.sleep(0)
    engine._running = False
    await asyncio.wait_for(task, timeout=10)


def finger(fid, x, y, kind):
    """A touch, in the 0..1 coordinates SDL actually delivers."""
    w, h = ke._engine._width, ke._engine._height
    pygame.event.post(pygame.event.Event(
        kind, finger_id=fid, touch_id=1, x=x / w, y=y / h, dx=0, dy=0,
        pressure=1.0))


# ------------------------------------------------ where the controls are
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
check("joystick=True gives the engine one", j is not None)
check("  with a d-pad and two buttons", len(j.buttons) == 2,
      " ".join(b["key"] for b in j.buttons))
check("  sending space and z by default",
      [b["key"] for b in j.buttons] == ["space", "z"])

cx, cy = j.pad_centre
LEFT = (cx - int(j.pad_r * 0.7), cy)
RIGHT = (cx + int(j.pad_r * 0.7), cy)
UP = (cx, cy - int(j.pad_r * 0.7))
A = j.buttons[0]["centre"]

# ------------------------------------ the middle of the pad is not a direction
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
check("the middle of the d-pad holds nothing", not j._keys_at(*j.pad_centre),
      "a resting thumb must not be 'left'")

# ------------------------------------------------- onKeyDown, and isKeyDown
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
cx, cy = j.pad_centre
LEFT = (cx - int(j.pad_r * 0.7), cy)
RIGHT = (cx + int(j.pad_r * 0.7), cy)
A = j.buttons[0]["centre"]

walked, asked = [], []


@onKeyDown("right")
def go():
    walked.append(1)
    asked.append(isKeyDown("right"))


finger(1, RIGHT[0], RIGHT[1], pygame.FINGERDOWN)
asyncio.run(frames(eng, 5))
check("a thumb on the d-pad fires onKeyDown", walked, "%d frames" % len(walked))
check("  and isKeyDown agrees with it", asked and all(asked),
      "%r" % asked[:4])

finger(1, RIGHT[0], RIGHT[1], pygame.FINGERUP)
asyncio.run(frames(eng, 3))
before = len(walked)
asyncio.run(frames(eng, 4))
check("lifting the thumb stops it", len(walked) == before,
      "%d more" % (len(walked) - before))
check("  and isKeyDown says so too", not isKeyDown("right"))

# --------------------------------------------- onKeyPress and onKeyRelease
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
A = j.buttons[0]["centre"]
jumps, lands = [], []
onKeyPress("space", lambda: jumps.append(1))
onKeyRelease("space", lambda: lands.append(1))

finger(2, A[0], A[1], pygame.FINGERDOWN)
asyncio.run(frames(eng, 4))
check("a button fires onKeyPress", jumps, "%d" % len(jumps))
check("  exactly once while held", len(jumps) == 1, "%d times" % len(jumps))

finger(2, A[0], A[1], pygame.FINGERUP)
asyncio.run(frames(eng, 4))
check("and onKeyRelease on the way up", lands == [1], "%r" % lands)

# ------------------------------------------------------------- multi-touch
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
cx, cy = j.pad_centre
RIGHT = (cx + int(j.pad_r * 0.7), cy)
A = j.buttons[0]["centre"]

finger(1, RIGHT[0], RIGHT[1], pygame.FINGERDOWN)
asyncio.run(frames(eng, 2))
finger(2, A[0], A[1], pygame.FINGERDOWN)
asyncio.run(frames(eng, 2))

check("running and jumping at once both hold",
      isKeyDown("right") and isKeyDown("space"),
      "right=%s space=%s" % (isKeyDown("right"), isKeyDown("space")))

# Letting go of the button must not let go of the direction.
finger(2, A[0], A[1], pygame.FINGERUP)
asyncio.run(frames(eng, 2))
check("  letting go of jump keeps running",
      isKeyDown("right") and not isKeyDown("space"),
      "right=%s space=%s" % (isKeyDown("right"), isKeyDown("space")))

# ------------------------------------------------------------- diagonals
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
cx, cy = j.pad_centre
d = int(j.pad_r * 0.5)
finger(3, cx + d, cy - d, pygame.FINGERDOWN)
asyncio.run(frames(eng, 3))
check("a thumb between up and right holds both",
      isKeyDown("up") and isKeyDown("right"),
      "up=%s right=%s" % (isKeyDown("up"), isKeyDown("right")))

# --------------------------------------------------- the mouse counts as one
#
# So the thing can be tried on a laptop. Without this it could only be tested
# by picking up a phone, which is how a control scheme goes unexercised.
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
cx, cy = j.pad_centre
LEFT = (cx - int(j.pad_r * 0.7), cy)
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=LEFT, button=1))
asyncio.run(frames(eng, 3))
check("the mouse works as a finger", isKeyDown("left"))
pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=LEFT, button=1))
asyncio.run(frames(eng, 3))
check("  and lets go", not isKeyDown("left"))

# ------------------------------------------------- nothing held without one
reset()
eng = kaypy(width=600, height=400)           # no joystick
check("without joystick=True there is none", eng.joystick is None)
check("  and nothing is held", not eng.events.virtual_keys)

# ------------------------------------------- a panel takes the thumb off
#
# Otherwise the player answers a question and comes back to a character that
# has been walking into a wall the whole time.
reset()
eng = kaypy(width=600, height=400, joystick=True)
j = eng.joystick
cx, cy = j.pad_centre
RIGHT = (cx + int(j.pad_r * 0.7), cy)
finger(1, RIGHT[0], RIGHT[1], pygame.FINGERDOWN)
asyncio.run(frames(eng, 3))
check("holding right before a question", isKeyDown("right"))

from kaypy import say                                           # noqa: E402
say("Mind the gap.")
asyncio.run(frames(eng, 3))
check("  a panel lets go of it", not isKeyDown("right"),
      "or the player returns to a character still walking")

# ------------------------------------------------- the buttons are choosable
reset()
eng = kaypy(width=600, height=400, joystick=["space", "x"])
check("the two buttons can be chosen",
      [b["key"] for b in eng.joystick.buttons] == ["space", "x"],
      " ".join(b["key"] for b in eng.joystick.buttons))

reset()
done()
