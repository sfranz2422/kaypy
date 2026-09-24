#!/usr/bin/env python3
"""The named colours, and color() accepting them.

    python3 kaypy/tests/test_colors.py

A constant is the easiest thing in a library to get wrong without noticing,
because nothing about a wrong tuple looks wrong. GREEN set to (0, 128, 0)
would draw a perfectly convincing green and quietly disagree with every
Kaplay example a student copies.

The part worth real attention is color(). It used to take three numbers and
nothing else, so `color(RED)` would have set red to a tuple and produced a
crash somewhere far away from the line that caused it. Widening it to accept
what rgb() accepts is what makes the constants usable at all — and widening
a function is exactly when its old callers break, so every old spelling is
checked here too.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# This script never calls run(); the engine starts from atexit when it ends.
# Without a cap that loop runs for ever and the test hangs instead of failing.
os.environ.setdefault("KAYPY_TEST_MAX_FRAMES", "2")

import kaypy                                                      # noqa: E402
from kaypy import (RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, WHITE, BLACK,
                   color, rgb)                                    # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-56s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


# ------------------------------------------------------------ the values
#
# Spelled out rather than computed. A test that builds the expected value the
# same way the code does is a test that agrees with a typo.
EXPECTED = {
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW": (255, 255, 0),
    "MAGENTA": (255, 0, 255),
    "CYAN": (0, 255, 255),
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
}

for name, want in EXPECTED.items():
    got = getattr(kaypy, name)
    check("%s is %s" % (name, want), got == want, str(got))

check("every one is a plain tuple of three ints",
      all(isinstance(v, tuple) and len(v) == 3
          and all(isinstance(c, int) for c in v)
          for v in EXPECTED.values()))

check("all eight are exported by name",
      all(n in kaypy.__all__ for n in EXPECTED),
      str([n for n in EXPECTED if n not in kaypy.__all__]))

# No two of them are the same colour — a copy-paste slip that would leave, say,
# MAGENTA drawing as RED and nothing complaining.
seen = {}
dupes = [n for n, v in EXPECTED.items() if v in seen or seen.setdefault(v, n) is None]
check("no two constants share a value", not dupes, str(dupes))

# ---------------------------------------------------------- color() takes them
c = color(RED)
check("color(RED) works", c.color == (255, 0, 0), str(c.color))
check("  and is the same as rgb(255, 0, 0)", c.color == rgb(255, 0, 0))

for name, want in EXPECTED.items():
    got = color(getattr(kaypy, name)).color
    check("color(%s)" % name, got == want, str(got))

# -------------------------------------------- the spellings that already worked
#
# Widening a function is when its existing callers break. Every form that
# worked before this change has to still work, including the defaults.
check("color(255, 128, 0) still works", color(255, 128, 0).color == (255, 128, 0))
check("color() is still white", color().color == (255, 255, 255))
check("color(200) is a grey", color(200).color == (200, 200, 200))
check('color("#ff8800") works', color("#ff8800").color == (255, 136, 0))
check('color("#f80") works', color("#f80").color == (255, 136, 0))
check("color([10, 20, 30]) works", color([10, 20, 30]).color == (10, 20, 30))

# The one behaviour that changed, on purpose. It used to return (255, 128, 255)
# — a blue nobody asked for, invented silently.
try:
    color(255, 128)
    check("color(255, 128) refuses rather than inventing a blue", False,
          "it returned a colour")
except ValueError as e:
    check("color(255, 128) refuses rather than inventing a blue", True)
    check("  and says what to write instead",
          "three numbers" in str(e), str(e)[:60])

# ------------------------------------------------------- where colours are used
#
# The constants are only worth having if they work in the places a student
# will put them, so use each one for real rather than trusting the tuple.
kaypy.kaypy(width=200, height=150, background=BLUE)
box = kaypy.add([kaypy.rect(20, 20), kaypy.pos(10, 10), color(YELLOW)])
check("a game object can be coloured with a constant",
      box.comp("color").color == (255, 255, 0), str(box.comp("color").color))

check("background= accepts one too",
      tuple(kaypy.current_engine()._background)[:3] == BLUE,
      str(kaypy.current_engine()._background))

kaypy.setBackground(MAGENTA)
check("setBackground(MAGENTA) works",
      tuple(kaypy.current_engine()._background)[:3] == MAGENTA,
      str(kaypy.current_engine()._background))
kaypy.setBackground(10, 20, 30)
check("  and three numbers still work",
      tuple(kaypy.current_engine()._background)[:3] == (10, 20, 30))

outlined = kaypy.add([kaypy.rect(10, 10), kaypy.pos(0, 0),
                      kaypy.outline(2, GREEN)])
# The attribute is outlineColor, not color — OutlineComp holds both a width
# and a colour, so neither gets the bare name.
check("outline() accepts one too",
      tuple(outlined.comp("outline").outlineColor)[:3] == GREEN,
      str(outlined.comp("outline").outlineColor))
check('  and outline(2, "#ff8800") works now as well',
      tuple(kaypy.outline(2, "#ff8800").outlineColor)[:3] == (255, 136, 0))

done()
