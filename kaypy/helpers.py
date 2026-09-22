"""The small Kaplay names — the ones a copied example reaches for.

None of these is load-bearing on its own. Together they are the difference
between a Kaplay example found on the internet running as written and failing
on its third line with a NameError, which is the thing kaypy exists to avoid:
"KAPLAY's documentation still tells you what to write" is only true while the
names in it exist.

Every one is Kaplay's own name with Kaplay's own arguments and its own return
type. Where Kaplay is loose about types — `rgb()` taking three numbers or one
hex string — that looseness is copied too, because a student pasting an
example should not have to know which spelling their source used.
"""
import math
import random as _random


def time():
    """Seconds since kaplay() started. Kaplay's clock, not the wall clock.

    Pauses when the game does, which is the whole point of not using
    `time.time()` — a sine wave driven by wall time jumps when a game is
    paused and resumed.
    """
    from .engine import current_engine
    return current_engine().elapsed()


def destroy(obj):
    """Remove one object. `obj.destroy()` does the same thing."""
    if obj is not None and hasattr(obj, "destroy"):
        obj.destroy()


def destroyAll(tag):
    """Remove every object carrying a tag. Returns how many went."""
    from .engine import current_engine
    doomed = current_engine().get(tag)
    for obj in doomed:
        obj.destroy()
    return len(doomed)


def isKeyDown(key):
    """Is this key held right now?

    The polling counterpart to `onKeyDown`. Some logic reads better asked
    than answered: `if isKeyDown("shift")` inside a handler you already have,
    rather than a second handler that sets a flag.
    """
    import pygame
    from .events import resolve_key

    try:
        return bool(pygame.key.get_pressed()[resolve_key(key)])
    except (KeyError, IndexError, pygame.error):
        return False


def rgb(r=255, g=None, b=None):
    """A colour, as a plain (r, g, b) tuple.

    Kaplay takes three numbers or one hex string, so this does too:
    `rgb(255, 128, 0)`, `rgb("#ff8800")`, `rgb("#f80")`, or `rgb(200)` for a
    grey. Two numbers is not a colour anyone meant, so it says so rather than
    inventing the third.
    """
    if isinstance(r, str):
        text = r.lstrip("#")
        if len(text) == 3:
            text = "".join(c * 2 for c in text)
        if len(text) != 6:
            raise ValueError(
                "rgb(%r): a hex colour looks like '#ff8800' or '#f80'" % r)
        try:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            raise ValueError(
                "rgb(%r): that is not hex — try '#ff8800'" % r) from None
    if isinstance(r, (tuple, list)):
        return tuple(int(c) for c in r)[:3]
    if g is None and b is None:
        return (int(r), int(r), int(r))          # rgb(200) is a grey
    if b is None:
        raise ValueError(
            "rgb() takes three numbers, one hex string, or one number for a "
            "grey — rgb(%r, %r) is missing the blue." % (r, g))
    return (int(r), int(g), int(b))


def lerp(a, b, t):
    """Blend from a to b. Works on numbers and on vec2."""
    from .vec2 import Vec2

    if isinstance(a, Vec2) or isinstance(b, Vec2):
        return Vec2(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)
    return a + (b - a) * t


def clamp(value, low, high):
    """Keep a number inside a range. Tolerates the bounds being swapped."""
    if low > high:
        low, high = high, low
    return max(low, min(high, value))


def chance(probability):
    """True that often. `chance(0.2)` is true one time in five."""
    return _random.random() < probability


def wave(low, high, t, func=math.sin):
    """A value swinging between low and high, forever.

        y = wave(100, 200, time() * 2)

    Kaplay's own signature. The fourth argument lets you swap the shape of
    the swing; `math.cos` starts at the top instead of the middle.
    """
    return low + (func(t) + 1) / 2 * (high - low)


def deg2rad(degrees):
    return math.radians(degrees)


def rad2deg(radians):
    return math.degrees(radians)
