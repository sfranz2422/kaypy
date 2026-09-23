"""pause() freezes the world and leaves the picture up.

    python3 tests/test_pause.py

Pausing is easy to get half right. The obvious implementation stops calling
onUpdate and declares victory — and then gravity still pulls, timers still
come due, and a held arrow key still walks the player off the screen behind
the menu you just opened. So this checks each of those separately, by
running real frames on the real loop rather than by inspecting a flag.

WHAT PAUSED HAS TO MEAN

  * onUpdate stops
  * timers stop, and do not all fire at once on resume
  * gravity stops, and the player does not accumulate fall speed
  * collisions stop being reported
  * .move() moves nothing, even from a key handler that still runs
  * the frame is still drawn, so the game is visible behind a panel

AND WHAT IT MUST NOT MEAN

Input keeps arriving. A pause menu has to hear the key that un-pauses it,
so handlers still fire; what makes that safe is dt being zero. Both halves
of that are checked, because either one alone is a bug: handlers that stop
firing make the menu unusable, and a non-zero dt makes the world move.
"""
import asyncio
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# A high ceiling rather than 0 or unset. 0 now means run NO frames (see
# tests/test_max_frames.py), which would make every "while paused" check
# below pass by running nothing at all — and the first version of this file
# did exactly that. Unset means no limit, which risks a hang. A big number
# is bounded and never reached, because frames() stops the loop itself.
os.environ["KAYPY_TEST_MAX_FRAMES"] = "100000"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame                                                   # noqa: E402
import kaypy.engine as ke                                       # noqa: E402
from kaypy import (kaypy, add, pos, rect, area, body, setGravity,  # noqa: E402
                   onUpdate, onKeyDown, wait, pause, resume, isPaused,
                   dt, time, onCollide)

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
    _held.clear()
    try:
        pygame.event.clear()
    except pygame.error:
        pass


# Held keys, the same way tools/test_guide.py does it: under the dummy video
# driver nothing is ever really held, and onKeyDown asks SDL rather than
# reading the event queue. Without this, the one check that matters most —
# that a key handler still runs while paused but moves nothing — could not
# be written at all.
_held = set()


class _Keys:
    def __getitem__(self, code):
        return code in _held

    def __len__(self):
        return 512


pygame.key.get_pressed = lambda: _Keys()


async def frames(engine, n):
    """Run n real frames of the engine's own loop.

    _running is set back to True first. Stopping the loop is how this
    function ends, so without it every call after the first would return
    having run nothing — and a "while paused" check that runs no frames
    passes whatever the engine does.
    """
    engine._running = True
    engine._started = False      # run_async() returns at once if it is set
    task = asyncio.ensure_future(engine.run_async())
    for _ in range(n):
        if task.done():
            break
        await asyncio.sleep(0)
    engine._running = False
    await asyncio.wait_for(task, timeout=10)


# --------------------------------------------------------- onUpdate stops
reset()
eng = kaypy(width=200, height=200)
ticks = []
onUpdate(lambda: ticks.append(1))

asyncio.run(frames(eng, 6))
ran_before = len(ticks)
check("onUpdate runs while the game is going", ran_before > 0,
      "%d frames" % ran_before)

pause()
check("isPaused() says so", isPaused())
asyncio.run(frames(eng, 6))
check("and stops while paused", len(ticks) == ran_before,
      "%d more" % (len(ticks) - ran_before))

resume()
check("isPaused() is false again", not isPaused())
asyncio.run(frames(eng, 6))
check("and starts again on resume", len(ticks) > ran_before,
      "%d more" % (len(ticks) - ran_before))

# ------------------------------------------------------------- dt is zero
reset()
eng = kaypy(width=200, height=200)
seen = []
onUpdate(lambda: seen.append(dt()))
asyncio.run(frames(eng, 4))
check("dt is above zero while running", seen and max(seen) > 0,
      "max %.4f" % (max(seen) if seen else 0))

pause()
asyncio.run(frames(eng, 4))
check("and exactly zero while paused", eng.dt() == 0.0, "dt=%r" % eng.dt())

# -------------------------------------------------- time() stops too
#
# Otherwise a wave() or a tween resumes further along its curve than where
# it stopped, and anything bobbing jumps the instant the game comes back.
before = time()
asyncio.run(frames(eng, 6))
check("time() does not run on while paused", time() == before,
      "%.4f -> %.4f" % (before, time()))

# ------------------------------------------- a key handler still fires...
reset()
eng = kaypy(width=400, height=400)
player = add([rect(10, 10), pos(100, 100)])
fired = []


@onKeyDown("right")
def walk():
    fired.append(1)
    player.move(300, 0)


_held.add(pygame.K_RIGHT)
pause()
start_x = player.pos.x
asyncio.run(frames(eng, 8))

check("a held key still reaches its handler while paused", fired,
      "%d times" % len(fired))
check("  ...and moves the player nowhere, because dt is zero",
      player.pos.x == start_x, "x %.2f -> %.2f" % (start_x, player.pos.x))

resume()
asyncio.run(frames(eng, 8))
check("  ...and moves it again once resumed", player.pos.x > start_x,
      "x %.2f" % player.pos.x)
_held.clear()

# ------------------------------------------------------------ gravity stops
reset()
eng = kaypy(width=400, height=400)
setGravity(2000)
faller = add([rect(10, 10), pos(100, 0), area(), body()])

asyncio.run(frames(eng, 5))
fell_to = faller.pos.y
check("gravity pulls while running", fell_to > 0, "y %.2f" % fell_to)

pause()
asyncio.run(frames(eng, 10))
check("gravity stops while paused", faller.pos.y == fell_to,
      "y %.2f" % faller.pos.y)
# Speed must not accumulate either: a body that kept gaining velocity while
# paused would drop like a stone the moment the menu closed.
vel = getattr(faller, "vel", None)
if vel is not None:
    check("  and falling speed does not build up behind the menu",
          abs(vel.y) < 1e6, "vel.y %.2f" % vel.y)

resume()
asyncio.run(frames(eng, 5))
check("and pulls again on resume", faller.pos.y > fell_to,
      "y %.2f" % faller.pos.y)

# -------------------------------------------------------------- timers stop
reset()
eng = kaypy(width=200, height=200)
rang = []
wait(0.05, lambda: rang.append(1))

pause()
for _ in range(4):
    asyncio.run(frames(eng, 5))
check("a timer does not come due while paused", not rang)

resume()
for _ in range(30):
    asyncio.run(frames(eng, 5))
    eng.timers.update(0.02)
check("and does once the game is going again", rang)

# ---------------------------------------------------------- collisions stop
reset()
eng = kaypy(width=200, height=200)
add([rect(20, 20), pos(50, 50), area(), "a"])
add([rect(20, 20), pos(55, 50), area(), "b"])
hits = []
onCollide("a", "b", lambda x, y: hits.append(1))

pause()
asyncio.run(frames(eng, 6))
check("overlapping things do not collide while paused", not hits)

resume()
asyncio.run(frames(eng, 6))
check("and do once resumed", hits, "%d hits" % len(hits))

# ------------------------------------------------- the frame is still drawn
#
# The whole point is a panel over a visible game. If pausing skipped the
# draw, the last frame would still be on screen by luck rather than design
# — and anything drawn in onDraw, which is where a panel lives, would stop.
reset()
eng = kaypy(width=64, height=64, background=(10, 20, 30))
drawn = []
from kaypy import onDraw, drawRect                              # noqa: E402
onDraw(lambda: drawn.append(1) or drawRect(pos=None, width=4, height=4,
                                           color=(255, 0, 0)))
pause()
asyncio.run(frames(eng, 5))
check("the frame is still drawn while paused", drawn,
      "%d draws" % len(drawn))

reset()
done()
