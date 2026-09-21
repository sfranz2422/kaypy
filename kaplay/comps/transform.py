"""Small appearance/behavior components: anchor, scale, color, opacity,
outline, z, fixed()."""
from ..gameobj import Comp
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


class ColorComp(Comp):
    id = "color"

    def __init__(self, r=255, g=255, b=255):
        self.color = (r, g, b)


def color(r=255, g=255, b=255):
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
        self.outlineColor = color


def outline(width=1, color=(0, 0, 0)):
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
