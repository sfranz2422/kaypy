"""Standalone sanity script: proves kaplay/events.py's key-name map is
built lazily, on first real use, rather than at `import kaplay` time.

Why this matters: pygame-ce's pygame.K_LEFT etc. are plain constants on
native CPython, available the instant you `import pygame`, well before
pygame.init() runs — so building a dict of them right at module level
(as events.py used to) is completely safe there. But pygbag's WASM build
of pygame apparently doesn't populate those attributes until AFTER
pygame.init() — and `import kaplay` reaches kaplay/events.py (via
engine.py's `from .events import EventManager`) before a script's own
kaplay() call has had a chance to run pygame.init(). That crashed every
single web export with `AttributeError: module 'pygame' has no attribute
'K_LEFT'` before a single line of the game script ran — caught by
actually driving a real build in a real browser, not by inspection.

This doesn't (can't, without a WASM pygame build) reproduce the missing
attribute itself; it proves the actual fix — that kaplay never touches
pygame.K_* until something real (onKeyDown/onKeyPress/onKeyRelease, or
the frame loop) asks for it, which only happens after kaplay() has run
pygame.init() on every platform, web included.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "1"

import kaplay.events as ev  # noqa: E402

assert ev._KEY_MAP is None, (
    "KEY_MAP was built at import time — this crashes on pygbag's WASM "
    "pygame build, which doesn't populate pygame.K_* until pygame.init()"
)
print("confirmed: importing kaplay.events never touches pygame.K_*")

import kaplay  # noqa: E402

kaplay.kaplay(width=100, height=100)
assert ev._KEY_MAP is None, "kaplay() itself must not build the key map either"
print("confirmed: kaplay() (which calls pygame.init()) still doesn't build KEY_MAP")

kaplay.onKeyDown("left", lambda: None)
assert ev._KEY_MAP is not None, "the key map should build on its first real use"
assert ev.resolve_key("left") is not None
print("confirmed: KEY_MAP builds lazily on first onKeyDown/onKeyPress/onKeyRelease call")

print("ALL LAZY KEY-MAP CHECKS PASSED")
