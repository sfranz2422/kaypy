"""move(dir, speed): drifts an object in a straight line forever.
offscreen(destroy=True): cleans it up once it leaves the screen.
tile(isObstacle=): marks an object as occupying a square on a grid."""
from ..gameobj import Comp
from ..vec2 import vec2, Vec2


class MoveComp(Comp):
    id = "move"

    def __init__(self, direction, speed):
        if isinstance(direction, Vec2):
            self.direction = direction.unit()
        else:
            self.direction = vec2(*direction).unit()
        self.speed = speed

    def add(self, obj):
        self._obj = obj

    def update(self, obj):
        if obj.has("pos"):
            obj.comp("pos").move(self.direction * self.speed)


def move(direction, speed):
    return MoveComp(direction, speed)


class OffscreenComp(Comp):
    id = "offscreen"

    def __init__(self, destroy=False, distance=64):
        self.destroy = destroy
        self.distance = distance

    def add(self, obj):
        self._obj = obj

    def update(self, obj):
        from ..engine import current_engine
        from ..geometry import get_world_pos
        engine = current_engine()
        p = get_world_pos(obj)
        d = self.distance
        if (p.x < -d or p.x > engine.width() + d or
                p.y < -d or p.y > engine.height() + d):
            if self.destroy:
                obj.destroy()


def offscreen(destroy=False, distance=64):
    return OffscreenComp(destroy=destroy, distance=distance)


class TileComp(Comp):
    id = "tile"

    def __init__(self, isObstacle=False):
        self.isObstacle = isObstacle

    def add(self, obj):
        self._obj = obj


def tile(isObstacle=False):
    return TileComp(isObstacle=isObstacle)
