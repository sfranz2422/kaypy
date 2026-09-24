#!/usr/bin/env python3
"""A message looks like a message, and a question looks like a question.

    python3 tests/test_say_panel.py

THE BUG THIS EXISTS FOR

    say("Bran the Smith: the well has never once run dry.")

drew a panel with a TEXT BOX in it. The player could click into it and type,
and whatever they typed was thrown away, because a say() handler is called
with nothing. On the desktop the hint underneath read "Type your answer,
then press Enter." On a line of dialogue.

Neither renderer was wrong on its own. Both worked out what a panel looks
like from the only thing they could see — whether it had choices:

    if p.choices:  ...one button per choice...
    else:          ...a text box...

and a say() has no choices, exactly like a short-answer ask(). Two renderers
guessing the same thing from the same missing fact is not one bug twice, it
is one missing field. finish() was making the same guess a third time, from
three negatives.

So a Panel now records whether it is asking anything, and this file checks
that both renderers read it — including the browser one, which is where a
class actually meets it and which nothing had ever tested, because it needs
a DOM. It gets a small fake one below.
"""
from __future__ import annotations

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Zero frames: this file holds panels still and looks at them, and never
# wants the loop to turn. With a frame budget the engines each try to run at
# interpreter exit, after pygame.quit(), and bury the results under a screen
# of "video system not initialized".
os.environ.setdefault("KAYPY_TEST_MAX_FRAMES", "0")

import pygame                                                 # noqa: E402
from kaypy import *                                           # noqa: E402
import kaypy.engine as ke                                     # noqa: E402
import kaypy.panel as panel                                   # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-58s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


def fresh():
    ke._engine = None
    panel.reset()
    return kaypy(width=400, height=300)


# ==================================================== what a panel knows

fresh()
say("A message.")
check("say() makes a panel that is NOT asking anything",
      panel._current is not None and panel._current.asks is False,
      "asks=%r" % (panel._current.asks if panel._current else None))
panel._current.finish()

ask("A question?", then=lambda reply: None)
check("ask() makes one that is", panel._current.asks is True)
panel._current.finish(None, "x")

ask("Pick one", ["a", "b"], answer=1, then=lambda ok: None)
check("  and so does a multiple choice", panel._current.asks is True)
panel._current.finish(1, "b")


# ==================================================== what the handler gets

fresh()
got = []

say("Told you.", then=lambda *a: got.append(a))
panel._current.finish(None, "typed into a box that should not exist")
check("a say() handler is given nothing, whatever arrives with it",
      got == [(None,)] or got == [()], str(got))

got.clear()
ask("Your name?", then=lambda reply: got.append(reply))
panel._current.finish(None, "Steve")
check("a short answer hands over what was typed", got == ["Steve"], str(got))

got.clear()
ask("2 + 2?", ["3", "4"], answer=1, then=lambda ok: got.append(ok))
panel._current.finish(1, "4")
check("  and a marked question hands over True or False", got == [True], str(got))


# ============================================ the desktop view's keyboard

fresh()
say("Nothing to type here.")
view = panel._views["view"]
for ch in "hello":
    view._key(pygame.event.Event(pygame.KEYDOWN, key=ord(ch), unicode=ch))
check("typing at a message does not fill an invisible box",
      panel._current is not None and panel._current.typed == "",
      "typed %r" % panel._current.typed)

view._key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
check("  and Enter closes it", panel._current is None)

fresh()
ask("Type something", then=lambda reply: None)
view = panel._views["view"]
for ch in "abc":
    view._key(pygame.event.Event(pygame.KEYDOWN, key=ord(ch), unicode=ch))
check("typing at a question still fills the box",
      panel._current.typed == "abc", "typed %r" % panel._current.typed)

# What the desktop view actually PUTS THERE, not merely that it drew
# something. The first version of this check only asserted that draw() did
# not raise — and drawing a text box on a message does not raise. Swapping
# the branch back sailed straight through it.
#
# So the pixels are read: kaypy paints a short answer's box white and a
# message's button green, and the two cannot be confused.
screen = pygame.Surface((400, 300))
engine = ke.current_engine()


def button_colour(make):
    fresh()
    make()
    view = panel._views["view"]
    panel.draw(screen, engine)
    return screen.get_at(view.button_rect.center)[:3]


msg = button_colour(lambda: say("Hello."))
check("a message's control is drawn as a BUTTON, not a box",
      msg == (80, 150, 60), "rgb%s" % (msg,))

sa = button_colour(lambda: ask("Name?", then=lambda r: None))
check("  and a short answer's is still a white box",
      sa == (255, 255, 255), "rgb%s" % (sa,))

fresh()
ask("Pick", ["a", "b"], answer=0, then=lambda r: None)
panel.draw(screen, engine)
view = panel._views["view"]
check("  and a multiple choice draws one hit area per choice",
      len(view.rects) == 2, "%d areas" % len(view.rects))


# ============================================== the browser view's markup
#
# webpanel.py is the renderer a class actually meets, and it had never been
# tested, because it imports `js` and there is no browser here. So it gets a
# small fake DOM: enough for _build to run against the real code rather than
# against a description of it.

class FakeNode:
    def __init__(self, tag):
        self.tag = tag
        self.children = []
        self.className = ""
        self.textContent = ""
        self.type = ""
        self.placeholder = ""
        self.value = ""
        self.style = types.SimpleNamespace()
        self.attrs = {}
        self.listeners = []

    def appendChild(self, node):
        self.children.append(node)

    def setAttribute(self, k, v):
        self.attrs[k] = v

    def addEventListener(self, *a):
        self.listeners.append(a)

    def removeEventListener(self, *a):
        pass

    def focus(self):
        pass

    def remove(self):
        pass

    def contains(self, other):
        return False

    def getBoundingClientRect(self):
        return types.SimpleNamespace(left=0, top=0, width=400, height=300)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


class FakeDoc:
    def __init__(self):
        self.body = FakeNode("body")
        self.head = FakeNode("head")
        self.styles = {}

    def createElement(self, tag):
        return FakeNode(tag)

    def getElementById(self, el_id):
        return self.styles.get(el_id)


fake_js = types.SimpleNamespace()
fake_js.document = FakeDoc()
fake_js.window = FakeNode("window")
sys.modules["js"] = fake_js

from kaypy import webpanel                                    # noqa: E402


def build(p):
    """Build the real DOM view for that panel, and hand back its nodes."""
    fake_js.document = FakeDoc()
    view = webpanel.DomView(p)
    return list(view.veil.walk()), view


nodes, _ = build(panel.Panel("A message.", asks=False))
check("a MESSAGE builds no text box in the browser",
      not [n for n in nodes if n.tag == "input"],
      "%d inputs" % len([n for n in nodes if n.tag == "input"]))
buttons = [n for n in nodes if n.tag == "button"]
check("  but it does build a button", len(buttons) == 1,
      "%d buttons" % len(buttons))
hints = [n.textContent for n in nodes if "kaypy-hint" in n.className]
check("  and the hint does not tell you to type an answer",
      hints and "Type your answer" not in hints[0], str(hints)[:52])

nodes, _ = build(panel.Panel("Your name?", asks=True))
check("a SHORT ANSWER still builds one",
      len([n for n in nodes if n.tag == "input"]) == 1)
hints = [n.textContent for n in nodes if "kaypy-hint" in n.className]
check("  and says so", hints and "Type your answer" in hints[0], str(hints)[:52])

nodes, _ = build(panel.Panel("Pick", choices=["a", "b", "c"], asks=True))
check("a MULTIPLE CHOICE builds a button per choice",
      len([n for n in nodes if "kaypy-choice" in n.className]) == 3)
check("  and no text box", not [n for n in nodes if n.tag == "input"])


# ---- clicking the message's button answers it -------------------------
p = panel.Panel("Click me.", asks=False, then=lambda *a: got.append("clicked"))
got.clear()
nodes, view = build(p)
go = [n for n in nodes if n.tag == "button"][0]
# The real listener that _build registered, called the way a click would.
for kind, fn, *_rest in go.listeners:
    if kind == "click":
        fn(None)
check("clicking a message's button closes it",
      got == ["clicked"], str(got))

done()
