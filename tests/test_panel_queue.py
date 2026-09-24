#!/usr/bin/env python3
"""Two panels opened at once are asked one after the other, not one instead
of the other.

    python3 tests/test_panel_queue.py

THE BUG THIS EXISTS FOR

    @ask("What is your name?")
    def greeted(reply):
        print("Hello, " + reply)

    @ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
    def checked(correct):
        if correct:
            print("open sesame")

Two decorators, the obvious way to write a quiz, and the first question never
appeared. Both decorators run as the file is read, microseconds apart, and
_show() closed whatever was already up on the assumption that a panel only
goes away once somebody has answered it. So the first panel was built and
immediately thrown away, `greeted` was never called, and nothing was printed
or raised to explain it.

It reached a teacher before it reached a test, which is the part worth fixing
properly: the suite had panels opened one at a time and never two at once.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KAYPY_TEST_MAX_FRAMES", "2")

from kaypy import *                                            # noqa: E402
import kaypy.engine as ke                                      # noqa: E402
import kaypy.panel as panel                                    # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-56s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


def answer(index=None, text=None):
    """Answer whatever is on screen.

    Guarded, because every regression this file exists to catch ends with no
    panel where one should be — and `panel._current.finish()` on a None then
    raises AttributeError, burying a clear result under a stack trace. A test
    that crashes tells you something broke; this says which thing.
    """
    if panel._current is None:
        check("  (a panel should have been showing here)", False,
              "nothing was up, so the rest of this section cannot run")
        return False
    panel._current.finish(index, text)
    return True


def fresh():
    ke._engine = None
    panel.reset()
    return kaypy(width=200, height=150)


# --------------------------------------------- the program that was broken
fresh()
said = []

@ask("What is your name?")
def greeted(reply):
    said.append("hello " + reply)

@ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
def checked(correct):
    said.append("correct" if correct else "wrong")

check("the FIRST question is the one on screen",
      panel._current is not None and panel._current.text == "What is your name?",
      panel._current.text if panel._current else "nothing is showing")
check("  and the second is waiting, not discarded", len(panel._queue) == 1,
      "%d waiting" % len(panel._queue))
check("  neither handler has run yet", said == [], str(said))

answer(None, "Steve")
check("answering the first runs its handler", said == ["hello Steve"], str(said))
check("  and the second question comes up by itself",
      panel._current is not None
      and panel._current.text == "Which keyword starts a loop?",
      panel._current.text if panel._current else "nothing is showing")
check("  with nothing left in the queue", len(panel._queue) == 0)

answer(1, "for")
check("answering the second runs its handler too",
      said == ["hello Steve", "correct"], str(said))
check("  and no panel is left up", panel._current is None)

# ------------------------------------------------- the game stays paused
#
# Between two panels the game must not run. Resuming for a frame and pausing
# again would flash the game behind the questions, which reads as a bug.
fresh()

@say("First")
def one():
    pass

@say("Second")
def two():
    pass

check("@say used as a decorator makes ONE panel, not two",
      len(panel._queue) == 1, "%d waiting behind it" % len(panel._queue))
check("the engine is paused while a panel is up", ke.current_engine().isPaused())
answer()
check("  and still paused with another one waiting",
      ke.current_engine().isPaused(), "queue: %d" % len(panel._queue))
answer()
check("  and running again once the last one is answered",
      not ke.current_engine().isPaused())

# ------------------------------------------------------ close() and the queue
#
# close() takes away the panel on screen. What it must NOT do is silently
# cancel the questions behind it — a game that closes a panel from code is
# dismissing that one, not abandoning the quiz.
fresh()
order = []

@ask("one")
def a(reply):
    order.append("a")

@ask("two")
def b(reply):
    order.append("b")

close()
check("close() moves on to the next question rather than cancelling it",
      panel._current is not None and panel._current.text == "two",
      panel._current.text if panel._current else "nothing is showing")
check("  and does not run the dismissed panel's handler", order == [], str(order))

# --------------------------------------------------------- three in a row
fresh()
seen = []
for n in ("q1", "q2", "q3"):
    ask(n, then=(lambda name: (lambda reply: seen.append(name)))(n))

check("three panels queue up", len(panel._queue) == 2, "%d waiting" % len(panel._queue))
for _ in range(3):
    if panel._current is not None:
        panel._current.finish(None, "x")

check("  and all three are asked, in the order they were written",
      seen == ["q1", "q2", "q3"], str(seen))

# -------------------------------------------------- a new run starts clean
#
# In the browser the page stays and the game is run again. A question still
# waiting from last time is not a question about this run.
fresh()

@ask("left over")
def stale(reply):
    pass

@ask("also left over")
def stale2(reply):
    pass

check("a panel and a queue exist before the reset", len(panel._queue) == 1)
fresh()
check("a new engine starts with no panel", panel._current is None)
check("  and an empty queue", len(panel._queue) == 0, "%d waiting" % len(panel._queue))

done()
