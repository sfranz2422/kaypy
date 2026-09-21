"""area(): the collision box. Both objects in a collision need one —
an object without area() is invisible to collision, and that's the
single most common reason a collision "doesn't work"."""
from ..gameobj import Comp


class AreaComp(Comp):
    id = "area"

    def add(self, obj):
        self._obj = obj

    def get_rect(self):
        from ..geometry import get_world_rect
        return get_world_rect(self._obj)

    def isHovering(self) -> bool:
        from ..engine import current_engine
        mx, my = current_engine().mousePos()
        return self.get_rect().collidepoint(mx, my)


def area():
    return AreaComp()
