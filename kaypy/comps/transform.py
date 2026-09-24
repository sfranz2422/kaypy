"""Small appearance/behavior components: anchor, scale, rotate, color,
opacity, outline, z, fixed()."""
from ..gameobj import Comp
from ..helpers import rgb
from ..vec2 import Vec2, vec2

_ANCHOR_NAMES = {
    "topleft": (-1, -1), "top": (0, -1), "topright": (1, -1),
    "left": (-1, 0), "center": (0, 0), "right": (1, 0),
    "botleft": (-1, 1), "bot": (0, 1), "botright": (1, 1),
}


class AnchorComp(Comp):
    id = "anchor"

    def __init__(self, value):
        self.anchor = self._resolve(value)

    def _resolve(self, value):
        if isinstance(value, str):
            if value not in _ANCHOR_NAMES:
                raise ValueError(f"unknown anchor name {value!r}")
            x, y = _ANCHOR_NAMES[value]
            return Vec2(x, y)
        if isinstance(value, Vec2):
            return value
        raise TypeError(
            "anchor() takes a name like anchor(\"center\") or an offset "
            "vec2(x, y) between -1 and 1 — not a screen position"
        )


def anchor(value):
    return AnchorComp(value)


class ScaleComp(Comp):
    id = "scale"

    def __init__(self, x=1, y=None):
        if y is None:
            y = x
        self.scale = Vec2(x, y)


def scale(x=1, y=None):
    return ScaleComp(x, y)


class RotateComp(Comp):
    """rotate(degrees) — turn the object, clockwise, about its anchor.

    Clockwise because the screen's y axis points down, so a positive angle
    turns the way a clock does, which is what anyone drawing on a screen
    expects. Asteroids is the reason this exists: a ship that cannot turn
    is not a ship.

    The **collision box does not turn with it**, deliberately. It stays the
    upright rectangle the object would have had at angle 0, which is what
    Kaplay does too. A rotating box whose hitbox rotated with it would grow
    and shrink twice a revolution, so an asteroid spinning on the spot would
    catch the player at some angles and not others — a bug nobody would ever
    guess at from the symptom.
    """

    id = "rotate"

    def __init__(self, angle=0):
        self.angle = angle

    def rotateBy(self, degrees):
        """Turn by this much more. `obj.rotateBy(180 * dt())` in onUpdate."""
        self.angle += degrees
        return self.angle

    def rotateTo(self, degrees):
        """Face exactly this way."""
        self.angle = degrees
        return self.angle


def rotate(angle=0):
    return RotateComp(angle)


class ColorComp(Comp):
    id = "color"

    def __init__(self, r=255, g=None, b=None):
        self.color = rgb(r, g, b)


def color(r=255, g=None, b=None):
    """A colour, in any of the spellings rgb() accepts.

    `color(255, 128, 0)`, `color("#ff8800")`, `color(200)` for a grey, and
    `color(RED)` all work, because this hands its arguments straight to
    rgb(). Before that it took three numbers only, so `color(RED)` quietly
    set red to a tuple — the constants would have been useless in the one
    place a beginner would reach for them first.

    THE DEFAULTS HAD TO CHANGE TOO
    
    Handing the arguments to rgb() is not enough on its own. While this read
    `color(r=255, g=255, b=255)`, `color(200)` still arrived at rgb() as
    (200, 255, 255) — rgb()'s "one number is a grey" rule could never fire,
    because g and b were never missing. The defaults are None here for the
    same reason they are None there.

    One behaviour changed on the way: `color(255, 128)` used to return
    (255, 128, 255), silently inventing a blue nobody asked for. It now
    raises the same sentence rgb() has always raised.
    """
    return ColorComp(r, g, b)


class OpacityComp(Comp):
    id = "opacity"

    def __init__(self, n=1.0):
        self.opacity = n


def opacity(n=1.0):
    return OpacityComp(n)


class OutlineComp(Comp):
    id = "outline"

    def __init__(self, width=1, color=(0, 0, 0)):
        self.outlineWidth = width
        self.outlineColor = rgb(color)


def outline(width=1, color=(0, 0, 0)):
    """An outline, in any spelling rgb() accepts.

    A tuple already worked here, so outline(2, GREEN) was fine before this.
    Going through rgb() is for the other spellings — outline(2, "#ff8800")
    and outline(2, 200) — so that every place a colour goes takes the same
    set of forms. One name behaving differently from the rest is the sort of
    thing a student reads as "I did it wrong".
    """
    return OutlineComp(width, color)


class ZComp(Comp):
    id = "z"

    def __init__(self, z=0):
        self.z = z


def z(value=0):
    return ZComp(value)


class FixedComp(Comp):
    """Marks an object as ignoring the camera (stays put on screen)."""
    id = "fixed"

    def __init__(self):
        self.fixed = True


def fixed():
    return FixedComp()
