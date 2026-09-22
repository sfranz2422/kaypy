"""health() and lifespan(): hit points, and things that clean up after themselves.

    python3 tests/test_health_lifespan.py

The one that matters most here is that onDeath fires EXACTLY once. An enemy
hit twice in the frame it dies — two bullets, or a bullet and a spike — is
ordinary, and a death handler that runs twice drops two coins, plays two
sounds, and adds two to the score. It is the sort of bug that looks like
generosity until someone notices.
"""
import asyncio
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kaypy.engine as ke                                       # noqa: E402
from kaypy import (kaplay, add, rect, pos, opacity, health,      # noqa: E402
                   lifespan, sprite)

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def reset():
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
    ke._engine = None


def refused(call, kind=ValueError):
    """Did that call refuse, with the kind of error a student can read?"""
    try:
        call()
        return False
    except kind:
        return True


def frame(eng, dt=1 / 60):
    """Advance one frame's worth of component updates."""
    eng._dt = dt
    for obj in list(eng._objs):
        if obj.exists():
            for comp in list(obj._comps.values()):
                comp.update(obj)


# =====================================================================
# health()
# =====================================================================
reset()
eng = kaplay(width=100, height=100)
eng._started, eng._running = True, False

enemy = add([rect(10, 10), pos(0, 0), health(3), "enemy"])
events = []
enemy.onHurt(lambda n: events.append(("hurt", n)))
enemy.onHeal(lambda n: events.append(("heal", n)))
enemy.onDeath(lambda: events.append("death"))

check("health(3) starts at 3", enemy.hp == 3, repr(enemy.hp))
check("and remembers its maximum", enemy.maxHP == 3)
check("it is alive", enemy.isAlive())

enemy.hurt(1)
check("hurt(1) takes one off", enemy.hp == 2, repr(enemy.hp))
check("and fires onHurt with the amount", ("hurt", 1) in events, repr(events))
check("nothing has died yet", "death" not in events)

enemy.heal(1)
check("heal(1) puts one back", enemy.hp == 3)
check("and fires onHeal", ("heal", 1) in events)

enemy.heal(10)
check("healing never goes above the maximum", enemy.hp == 3, repr(enemy.hp))
before = len([e for e in events if e[0] == "heal"])
enemy.heal(5)
check("and healing at full health fires nothing",
      len([e for e in events if e[0] == "heal"]) == before)

enemy.hurt(3)
check("hurt to zero fires onDeath", "death" in events)
check("and the object is NOT destroyed by it", enemy.exists(),
      "so it can play an animation or drop a coin first")

# The one that matters.
events.clear()
enemy.hurt(1)
enemy.hurt(1)
check("hitting something already dead holds no second funeral",
      "death" not in events, repr(events))

# setHP crossing zero counts as death too.
reset()
eng = kaplay(width=100, height=100)
eng._started, eng._running = True, False
target = add([rect(4, 4), pos(0, 0), health(5)])
deaths = []
target.onDeath(lambda: deaths.append(1))
target.setHP(0)
check("setHP(0) fires onDeath as well", deaths == [1], repr(deaths))
target.setHP(0)
check("and not again", deaths == [1])

check("hurt() with a negative amount is refused", refused(lambda: target.hurt(-3)))
check("heal() with a negative amount is refused", refused(lambda: target.heal(-2)))
check("health() with no number is refused", refused(lambda: health(None), TypeError))

# =====================================================================
# lifespan()
# =====================================================================
reset()
eng = kaplay(width=100, height=100)
eng._started, eng._running = True, False

bullet = add([rect(4, 4), pos(0, 0), lifespan(0.5), "bullet"])
check("a bullet with a lifespan starts alive", bullet.exists())

for _ in range(20):
    frame(eng, dt=0.02)          # 0.4s
check("and is still there before its time", bullet.exists(), "0.4s of 0.5s")

for _ in range(10):
    frame(eng, dt=0.02)          # 0.6s total
check("then destroys itself", not bullet.exists())

# fading
reset()
eng = kaplay(width=100, height=100)
eng._started, eng._running = True, False
puff = add([rect(4, 4), pos(0, 0), opacity(1), lifespan(1.0, fade=0.5)])

for _ in range(20):
    frame(eng, dt=0.02)          # 0.4s — well before the fade begins
# Not 25 frames (exactly 0.5s, where the fade starts): twenty-five additions
# of 0.02 land a hair under half a second, so the fade begins one frame early
# and the opacity is 0.9999999999999991 rather than 1. That is float
# arithmetic, not a bug, and pinning a test to the exact instant a boundary is
# crossed tests the arithmetic rather than the behaviour.
check("before the fade begins it is fully opaque",
      puff.comp("opacity").opacity == 1, repr(puff.comp("opacity").opacity))

for _ in range(12):
    frame(eng, dt=0.02)          # ~0.74s — a quarter into the fade
half = puff.comp("opacity").opacity
check("during the fade it is part-way out", 0 < half < 1, "%.2f" % half)

for _ in range(25):          # 0.64s so far + 0.5s = past its one second
    frame(eng, dt=0.02)
check("and at the end it is gone", not puff.exists())

# fade without opacity(): a note, once, and the object still goes away
reset()
eng = kaplay(width=100, height=100)
eng._started, eng._running = True, False
import io                                                       # noqa: E402

plain = add([rect(4, 4), pos(0, 0), lifespan(0.2, fade=0.1)])
out, sys.stdout = sys.stdout, io.StringIO()
try:
    for _ in range(20):
        frame(eng, dt=0.02)
    said = sys.stdout.getvalue()
finally:
    sys.stdout = out
check("fading without opacity() explains itself", "opacity(" in said,
      said.strip()[:52])
check("and says it once, not every frame", said.count("note:") == 1,
      "%d times" % said.count("note:"))
check("and the object still goes away on time", not plain.exists())

check("lifespan with a negative time is refused", refused(lambda: lifespan(-1)))
check("a fade longer than the life is clamped, not an error",
      lifespan(1, fade=5).fade == 1)

reset()
bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
