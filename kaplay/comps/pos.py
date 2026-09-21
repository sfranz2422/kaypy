from ..gameobj import Comp
from ..vec2 import vec2, Vec2


class PosComp(Comp):
    id = "pos"

    def __init__(self, x=0, y=0):
        if isinstance(x, Vec2):
            self.pos = Vec2(x.x, x.y)
        else:
            self.pos = vec2(x, y)

    def move(self, dx, dy=None):
        """Move by a velocity in pixels PER SECOND (scaled by dt each frame)."""
        engine = self._engine_ref()
        dt = engine.dt() if engine else 0.0
        if dy is None and isinstance(dx, Vec2):
            self.pos = self.pos + dx * dt
        else:
            self.pos = self.pos + vec2(dx, dy) * dt

    def moveTo(self, target, speed=None):
        """Move toward target. With speed, moves at that rate (px/s);
        without, jumps straight there."""
        if isinstance(target, (tuple, list)):
            target = vec2(*target)
        elif not isinstance(target, Vec2):
            target = vec2(target, 0)
        if speed is None:
            self.pos = Vec2(target.x, target.y)
            return
        engine = self._engine_ref()
        dt = engine.dt() if engine else 0.0
        direction = target - self.pos
        dist = direction.len()
        step = speed * dt
        if dist <= step or dist == 0:
            self.pos = Vec2(target.x, target.y)
        else:
            self.pos = self.pos + direction.unit() * step

    def _engine_ref(self):
        from ..engine import current_engine
        return current_engine()

    def add(self, obj):
        self._obj = obj


def pos(x=0, y=0):
    return PosComp(x, y)
