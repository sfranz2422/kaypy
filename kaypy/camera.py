"""The camera: where the world is looked at from, and how big it looks.

THE SCALE IS A VECTOR, NOT A NUMBER

    setCamScale(2)                 twice as big, both ways
    setCamScale(vec2(2, 0.4))      twice as wide and squashed flat

A single number is the common case and stays the common case — it simply
means the same amount on both axes. Two lets the world be stretched: a
letterboxed cutscene, a squash as something lands, a deliberately wrong
aspect ratio for a dream sequence.

Keeping one number internally and a second "scaleY" beside it was the other
option, and it is the one that rots: every place that multiplies by the
scale has to remember there are two of them, and the places that forget are
the ones nobody looks at — the debug boxes, the text size, the mouse
position. Storing a Vec2 means the type itself carries the reminder, and
anything that does arithmetic on it gets both axes or fails loudly.
"""
from .vec2 import Vec2, vec2


def _as_scale(value):
    """A scale as a Vec2, from a number or a vec2."""
    if isinstance(value, Vec2):
        s = Vec2(value.x, value.y)
    elif isinstance(value, (tuple, list)) and len(value) == 2:
        s = vec2(*value)
    elif isinstance(value, (int, float)):
        s = Vec2(value, value)
    else:
        raise TypeError(
            "setCamScale(%r) — the scale is a number, or a vec2 for a "
            "different amount on each axis.\n"
            "    setCamScale(2)                 # twice as big\n"
            "    setCamScale(vec2(2, 0.4))      # wide and squashed"
            % (value,))
    if s.x == 0 or s.y == 0:
        raise ValueError(
            "setCamScale(%r) — a scale of zero makes the world infinitely "
            "small, and everything after it divides by zero. Use a small "
            "number instead." % (value,))
    return s


class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pos = Vec2(width / 2, height / 2)
        self.scale = Vec2(1.0, 1.0)
        self.shake_amount = 0.0
        self._frame_shake_offset = Vec2(0, 0)

    def setPos(self, pos):
        self.pos = Vec2(pos.x, pos.y)

    def setScale(self, n):
        self.scale = _as_scale(n)

    def shake(self, amount=8):
        self.shake_amount = amount

    def begin_frame(self):
        """Called once per frame by the render system: decays shake and
        freezes this frame's random offset so every object drawn this
        frame shakes together."""
        if self.shake_amount <= 0:
            self._frame_shake_offset = Vec2(0, 0)
            return
        import random
        a = self.shake_amount
        self._frame_shake_offset = Vec2(random.uniform(-a, a), random.uniform(-a, a))
        self.shake_amount *= 0.9
        if self.shake_amount < 0.2:
            self.shake_amount = 0

    def world_to_screen(self, world_pos: Vec2) -> Vec2:
        center = Vec2(self.width / 2, self.height / 2)
        # Vec2 * Vec2 multiplies componentwise, so this is the same line it
        # was when the scale was a number — and it stretches correctly.
        return (world_pos - self.pos) * self.scale + center + self._frame_shake_offset

    def screen_to_world(self, screen_pos) -> Vec2:
        if not isinstance(screen_pos, Vec2):
            screen_pos = Vec2(screen_pos[0], screen_pos[1])
        center = Vec2(self.width / 2, self.height / 2)
        return (screen_pos - center) / self.scale + self.pos
