"""tween() and the easing curves.

    python3 tests/test_tween.py

A tween that silently does nothing raises nothing at all, so every check here
asks what ARRIVED — the values the setter was handed, whether the end value
was hit exactly, whether `.then()` really ran — rather than whether an error
was thrown. That distinction is the whole reason this file exists: the same
feature in the old JavaScript bridge looked perfectly healthy while
`.cancel()` cancelled nothing.

Frames are driven by hand rather than by the engine loop, so a "half a second"
tween takes no real time and the samples are exact.
"""
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaplay import kaplay, vec2, easings                      # noqa: E402
from kaplay.easings import ALL                                # noqa: E402
import kaplay.engine as ke                                    # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-50s %s" % ("ok" if ok else "FAIL", label, detail))


eng = kaplay(width=100, height=100)
timers = eng.timers


def run(seconds, step=1 / 60):
    """Advance the tweens by hand — no real time, exact sample counts."""
    for _ in range(int(round(seconds / step))):
        timers.update(step)


# ------------------------------------------------------------ the curves
check("all thirty-one curves are there", len(ALL) == 31, "%d" % len(ALL))
check("every curve starts at 0 and ends at 1",
      all(abs(f(0)) < 1e-9 and abs(f(1) - 1) < 1e-9 for f in ALL.values()))
check("none of them returns NaN anywhere in between",
      all(f(i / 40) == f(i / 40) for f in ALL.values() for i in range(41)))
check("easeOut arrives slowing down",
      easings.easeOutQuad(0.5) > 0.5, "half-way through, %.2f of the distance"
      % easings.easeOutQuad(0.5))
check("easeIn leaves slowly",
      easings.easeInQuad(0.5) < 0.5, "%.2f" % easings.easeInQuad(0.5))
check("easeOutBack overshoots and comes back",
      max(easings.easeOutBack(i / 100) for i in range(101)) > 1.0,
      "peaks at %.2f" % max(easings.easeOutBack(i / 100) for i in range(101)))
try:
    easings.easeOutWobble
    named = False
except AttributeError as err:
    named = "easeOutWobble" in str(err) and "Bounce" in str(err)
check("a misspelled curve says which names exist", named)

# -------------------------------------------------------------- a number
seen, ended = [], []
timers.tween(0, 100, 0.5, seen.append).then(lambda: ended.append(1))
run(0.6)
check("a number tween is driven every frame", len(seen) >= 28, "%d samples" % len(seen))
check("it rises", seen[0] < seen[len(seen) // 2] < seen[-1])
check("it lands exactly on the end value", seen[-1] == 100, repr(seen[-1]))
check("then() runs once, at the end", ended == [1], repr(ended))

# It must stop. A tween that keeps setting after it finishes would fight
# every other thing that touches the same value.
before = len(seen)
run(0.5)
check("and it stops when it is done", len(seen) == before)

# ---------------------------------------------------------------- a vec2
pts = []
timers.tween(vec2(0, 0), vec2(60, 90), 0.5, pts.append)
run(0.6)
check("a vec2 tween moves both axes",
      (pts[-1].x, pts[-1].y) == (60, 90), "ended at %s" % (pts[-1],))

# -------------------------------------------------------------- a colour
cols = []
timers.tween((0, 0, 0), (255, 128, 64), 0.5, cols.append)
run(0.6)
check("a colour tween blends each channel", cols[-1] == (255, 128, 64),
      "ended at %s" % (cols[-1],))

# --------------------------------------------------------------- easing
flat, eased = [], []
timers.tween(0, 100, 0.5, flat.append)
timers.tween(0, 100, 0.5, eased.append, easings.easeOutQuad)
run(0.6)
mid = len(flat) // 2
check("an easing curve actually changes the path",
      eased[mid] > flat[mid] + 5,
      "half-way: flat %.0f, eased %.0f" % (flat[mid], eased[mid]))
check("both still finish in the same place", flat[-1] == eased[-1] == 100)

custom = []
timers.tween(0, 100, 0.5, custom.append, lambda t: t * t)
run(0.6)
check("a plain Python function works as a curve",
      custom[len(custom) // 2] < flat[mid] - 5,
      "half-way: %.0f" % custom[len(custom) // 2])

# ------------------------------------------------------------ the handle
vals, never = [], []
t = timers.tween(0, 100, 1.0, vals.append).then(lambda: never.append(1))
run(0.25)
partway = len(vals)
t.cancel()
run(2.0)          # well past when it would have finished
check("cancel() stops it dead", len(vals) == partway,
      "%d samples, then %d" % (partway, len(vals)))
check("and a cancelled tween never runs then()", never == [], repr(never))

vals2, ended2 = [], []
t2 = timers.tween(0, 100, 1.0, vals2.append).then(lambda: ended2.append(1))
run(0.2)
t2.finish()
check("finish() jumps to the end", vals2[-1] == 100, repr(vals2[-1]))
check("and runs then()", ended2 == [1])

vals3 = []
t3 = timers.tween(0, 100, 0.5, vals3.append)
run(0.1)
held = len(vals3)
t3.paused = True
run(0.4)
check("paused holds it", len(vals3) == held, "%d, then %d" % (held, len(vals3)))
t3.paused = False
run(0.6)
check("and unpausing lets it finish", vals3[-1] == 100)

# ------------------------------------------------------------- the edges
zero = []
timers.tween(5, 9, 0, zero.append)
run(1 / 60)
check("a zero-length tween sets the end value once", zero[-1] == 9, repr(zero))

many = [[] for _ in range(30)]
for box in many:
    timers.tween(0, 1.0, 0.3, box.append)
run(0.4)
check("thirty at once all finish",
      all(b and b[-1] == 1.0 for b in many),
      "%d/30" % sum(1 for b in many if b and b[-1] == 1.0))

check("finished tweens are not kept for ever",
      len(timers._tweens) == 0, "%d still tracked" % len(timers._tweens))

# A tween started inside a callback is the common case: on a click, on a
# collision, at the end of another tween.
chained = []
timers.tween(0, 10, 0.1, lambda v: None).then(
    lambda: timers.tween(0, 5, 0.1, chained.append))
run(0.3)
check("a tween can start another from then()", chained and chained[-1] == 5,
      "ended at %s" % (chained[-1] if chained else "nothing"))

eng._started = True
eng._running = False
ke._engine = None

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
