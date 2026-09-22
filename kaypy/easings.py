"""The easing curves — the shape of a tween's motion.

A tween without one moves at a flat, constant rate, which is the single
motion that reads as "a computer did this". `easeOut...` arrives slowing
down, which is what most things in life do; `easeOutBack` and
`easeOutElastic` overshoot and spring back.

Every curve maps 0–1 to 0–1, is exactly 0 at 0 and exactly 1 at 1, and is
named as Kaplay names it, so a curve looked up in Kaplay's documentation is
the curve you get here. The formulas are the standard ones from
easings.net, which is where Kaplay's came from too.

Reached as an object — `easings.easeOutBounce` — rather than as thirty-one
loose names, because that is how Kaplay spells it and because
`from kaypy import *` should not put `easeInOutQuint` in a student's
namespace.
"""
import math

_C1 = 1.70158
_C2 = _C1 * 1.525
_C3 = _C1 + 1
_C4 = 2 * math.pi / 3
_C5 = 2 * math.pi / 4.5


def linear(t):
    return t


def easeInSine(t):
    return 1 - math.cos(t * math.pi / 2)


def easeOutSine(t):
    return math.sin(t * math.pi / 2)


def easeInOutSine(t):
    return -(math.cos(math.pi * t) - 1) / 2


def easeInQuad(t):
    return t * t


def easeOutQuad(t):
    return 1 - (1 - t) ** 2


def easeInOutQuad(t):
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def easeInCubic(t):
    return t ** 3


def easeOutCubic(t):
    return 1 - (1 - t) ** 3


def easeInOutCubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def easeInQuart(t):
    return t ** 4


def easeOutQuart(t):
    return 1 - (1 - t) ** 4


def easeInOutQuart(t):
    return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2


def easeInQuint(t):
    return t ** 5


def easeOutQuint(t):
    return 1 - (1 - t) ** 5


def easeInOutQuint(t):
    return 16 * t ** 5 if t < 0.5 else 1 - (-2 * t + 2) ** 5 / 2


def easeInExpo(t):
    return 0 if t == 0 else 2 ** (10 * t - 10)


def easeOutExpo(t):
    return 1 if t == 1 else 1 - 2 ** (-10 * t)


def easeInOutExpo(t):
    if t == 0:
        return 0
    if t == 1:
        return 1
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def easeInCirc(t):
    return 1 - math.sqrt(1 - t * t)


def easeOutCirc(t):
    return math.sqrt(1 - (t - 1) ** 2)


def easeInOutCirc(t):
    if t < 0.5:
        return (1 - math.sqrt(1 - (2 * t) ** 2)) / 2
    return (math.sqrt(1 - (-2 * t + 2) ** 2) + 1) / 2


def easeInBack(t):
    return _C3 * t ** 3 - _C1 * t * t


def easeOutBack(t):
    return 1 + _C3 * (t - 1) ** 3 + _C1 * (t - 1) ** 2


def easeInOutBack(t):
    if t < 0.5:
        return ((2 * t) ** 2 * ((_C2 + 1) * 2 * t - _C2)) / 2
    return ((2 * t - 2) ** 2 * ((_C2 + 1) * (t * 2 - 2) + _C2) + 2) / 2


def easeInElastic(t):
    if t == 0:
        return 0
    if t == 1:
        return 1
    return -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * _C4)


def easeOutElastic(t):
    if t == 0:
        return 0
    if t == 1:
        return 1
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * _C4) + 1


def easeInOutElastic(t):
    if t == 0:
        return 0
    if t == 1:
        return 1
    if t < 0.5:
        return -(2 ** (20 * t - 10) * math.sin((20 * t - 11.125) * _C5)) / 2
    return (2 ** (-20 * t + 10) * math.sin((20 * t - 11.125) * _C5)) / 2 + 1


def easeOutBounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def easeInBounce(t):
    return 1 - easeOutBounce(1 - t)


def easeInOutBounce(t):
    if t < 0.5:
        return (1 - easeOutBounce(1 - 2 * t)) / 2
    return (1 + easeOutBounce(2 * t - 1)) / 2


class _Easings:
    """The curves, as attributes, with a readable error for a typo.

    A misspelled curve would otherwise be an AttributeError naming a module,
    which tells a student nothing about which names exist.
    """

    def __getattr__(self, name):
        raise AttributeError(
            "No easing called %r. They are named easeIn/easeOut/easeInOut "
            "plus one of Sine, Quad, Cubic, Quart, Quint, Expo, Circ, Back, "
            "Elastic, Bounce — or easings.linear for no easing at all." % name
        )


easings = _Easings()
for _name, _fn in list(globals().items()):
    if _name.startswith("ease") or _name == "linear":
        setattr(easings, _name, _fn)

#: Every curve by name, for anything that wants to enumerate them.
ALL = {n: getattr(easings, n) for n in dir(easings) if not n.startswith("_")}
