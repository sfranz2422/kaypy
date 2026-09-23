"""say() and ask() — the panel pauses the game, owns the input, answers back.

    python3 tests/test_panel.py

Everything here goes through the real loop with real pygame events posted
into it, rather than by calling the panel's methods directly. Calling
panel.finish() by hand would prove the callback works and nothing about
whether a click ever reaches it — and "the button does nothing" is the only
way this feature can fail in front of a class.

WHAT MUST BE TRUE

  * showing a panel pauses the game, and answering resumes it
  * the panel gets the input, and the game behind it does not
  * a number key answers a multiple choice, and so does a click
  * `answer=` gives the callback True/False; no `answer=` gives it the text
  * a short answer is case- and space-insensitive
  * go() and a new engine both take a panel away with them

WHAT THIS CANNOT TELL YOU

How it looks, and whether the browser version works at all. The DOM view in
webpanel.py only loads under Pyodide; nothing here touches it. What is
checked instead is that the two views are asked for the same things — see
the last section.
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
import kaypy.panel as panel_mod                                 # noqa: E402
from kaypy import (kaypy, add, pos, rect, onUpdate, onClick,     # noqa: E402
                   say, ask, isShowing, isPaused, scene, go)

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
    panel_mod.reset()
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


def press(key, unicode=""):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key,
                                         unicode=unicode, mod=0))


def click(x, y):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         pos=(x, y), button=1))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP,
                                         pos=(x, y), button=1))


def choice_rect(i):
    """Where the view actually drew choice i, read off the view itself.

    Not computed here from the same numbers the view uses — that would agree
    with a broken layout as happily as with a working one.
    """
    view = panel_mod._views.get("view")
    for r, idx in view.rects:
        if idx == i:
            return r
    return None


# ------------------------------------------------------ say() pauses/resumes
reset()
eng = kaypy(width=400, height=300)
closed = []
say("You found the key!", then=lambda: closed.append(1))

check("say() pauses the game", isPaused())
check("  and a panel is showing", isShowing())

asyncio.run(frames(eng, 3))
press(pygame.K_RETURN)
asyncio.run(frames(eng, 3))
# say() has no choices, so it behaves like a short answer: Enter closes it.
check("pressing Enter closes it", not isShowing())
check("  the game is running again", not isPaused())
check("  and the callback ran", closed)

# --------------------------------------------- the game does not see the input
reset()
eng = kaypy(width=400, height=300)
game_clicks = []
onClick(lambda: game_clicks.append(1))
ticks = []
onUpdate(lambda: ticks.append(1))

say("Pay no attention to the game behind the panel.")
asyncio.run(frames(eng, 3))
# Near the top-left corner, which is the dimmed area outside the box — not
# the OK button. A click there SHOULD do nothing at all; the first version
# of this clicked dead centre, hit the button, closed the panel and then
# wondered why the game had started running again.
click(6, 6)
asyncio.run(frames(eng, 3))
check("a click on the panel does not reach the game", not game_clicks,
      "%d got through" % len(game_clicks))
check("  the panel is still up", isShowing())
check("  and onUpdate is not running behind it", not ticks,
      "%d ticks" % len(ticks))

# --------------------------------------------------- multiple choice, by key
reset()
eng = kaypy(width=600, height=400)
got = []


@ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
def checked(correct):
    got.append(correct)


asyncio.run(frames(eng, 3))
press(pygame.K_2, "2")
asyncio.run(frames(eng, 3))
check("a number key answers a multiple choice", got, "%r" % got)
check("  and the right one is True", got == [True], "%r" % got)
check("  the panel closed", not isShowing())

# -------------------------------------------------- multiple choice, by click
reset()
eng = kaypy(width=600, height=400)
got = []


@ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
def checked2(correct):
    got.append(correct)


asyncio.run(frames(eng, 3))
r = choice_rect(2)                       # "def" — the wrong one
check("the view reports where it drew the choices", r is not None,
      "choice 2 at %s" % (tuple(r),) if r else "nothing drawn")
if r:
    click(r.centerx, r.centery)
    asyncio.run(frames(eng, 3))
check("clicking a choice answers it", got, "%r" % got)
check("  and a wrong one is False", got == [False], "%r" % got)

# ------------------------------------------------ no answer= gives you the text
reset()
eng = kaypy(width=600, height=400)
got = []


@ask("Which do you like?", ["cats", "dogs"])
def picked(which):
    got.append(which)


asyncio.run(frames(eng, 3))
press(pygame.K_1, "1")
asyncio.run(frames(eng, 3))
check("without answer=, the callback gets what was picked", got == ["cats"],
      "%r" % got)

# ---------------------------------------------------------- short answer
reset()
eng = kaypy(width=600, height=400)
got = []


@ask("What is the capital of France?")
def typed(reply):
    got.append(reply)


asyncio.run(frames(eng, 3))
for ch in "Paris":
    press(ord(ch), ch)
asyncio.run(frames(eng, 3))
press(pygame.K_RETURN)
asyncio.run(frames(eng, 3))
check("a short answer comes back as typed", got == ["Paris"], "%r" % got)

# ------------------------------------------- short answer, marked, forgivingly
reset()
eng = kaypy(width=600, height=400)
got = []


@ask("What is the capital of France?", answer="paris")
def marked(correct):
    got.append(correct)


asyncio.run(frames(eng, 3))
for ch in "  PARIS ":
    press(ord(ch), ch)
press(pygame.K_RETURN)
asyncio.run(frames(eng, 3))
check("marking ignores case and outside spaces", got == [True], "%r" % got)

# --------------------------------------------------------- backspace works
reset()
eng = kaypy(width=600, height=400)
got = []


@ask("Spell it")
def spelled(reply):
    got.append(reply)


asyncio.run(frames(eng, 3))
for ch in "cart":
    press(ord(ch), ch)
press(pygame.K_BACKSPACE)
for ch in "s":
    press(ord(ch), ch)
press(pygame.K_RETURN)
asyncio.run(frames(eng, 3))
check("backspace takes a letter back", got == ["cars"], "%r" % got)

# ------------------------------------------------ a panel does not survive go()
reset()
eng = kaypy(width=400, height=300)
scene("next", lambda: add([rect(10, 10), pos(0, 0)]))
say("This should not outlive the scene.")
check("a panel is up before go()", isShowing())
go("next")
check("go() takes the panel away", not isShowing())
check("  and leaves the game running", not isPaused())

# ------------------------------------- nor a new engine (a browser IDE re-run)
reset()
eng = kaypy(width=400, height=300)
say("Left up when the page re-runs the game.")
check("a panel is up before the game restarts", isShowing())
eng2 = kaypy(width=400, height=300)
check("starting a new game clears it", not isShowing())
check("  and the new game is not stuck paused", not isPaused())

# This is the only place two engines exist at once, and the first one is now
# orphaned with its atexit frame loop still armed. reset() only ever sees the
# current engine, so this one has to be put down by hand — otherwise the
# whole file passes and then hangs at exit running frames for a game nobody
# is looking at.
eng._started = True
eng._running = False

# --------------------------------------- the two views answer the same calls
#
# webpanel.py only imports under Pyodide, so it cannot be exercised here. What
# can be checked is that panel.py never asks a view for something one of them
# does not have — which is how a feature ends up working on a desktop and
# raising AttributeError in a browser, where nobody would see it until a
# student did.
import ast                                                      # noqa: E402

src = (ROOT / "kaypy" / "panel.py").read_text()
asked = set()
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        if node.value.id == "view":
            asked.add(node.attr)

web = ast.parse((ROOT / "kaypy" / "webpanel.py").read_text())
dom = next(n for n in ast.walk(web)
           if isinstance(n, ast.ClassDef) and n.name == "DomView")
dom_has = {n.name for n in dom.body if isinstance(n, ast.FunctionDef)}
desk = next(n for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.ClassDef) and n.name == "_DesktopView")
desk_has = {n.name for n in desk.body if isinstance(n, ast.FunctionDef)}

# `draw` is desktop-only on purpose — the browser draws itself — and panel.py
# guards it with hasattr. Everything else has to be on both.
shared = asked - {"draw"}
check("every view method panel.py calls exists on the desktop view",
      shared <= desk_has, ", ".join(sorted(shared - desk_has)))
check("  and on the browser view",
      shared <= dom_has, ", ".join(sorted(shared - dom_has)))
check("  and panel.py guards the desktop-only one",
      'hasattr(view, "draw")' in src)

reset()
done()
