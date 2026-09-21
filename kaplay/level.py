"""addLevel(): draw a map as a picture made of characters. Each entry in
tiles is a function returning a component list — called once per tile,
so every tile gets its own object rather than all sharing one."""
from .vec2 import Vec2, vec2
from .comps.pos import pos as pos_comp


class Level:
    def __init__(self, config):
        self.tileWidth = config.get("tileWidth", 64)
        self.tileHeight = config.get("tileHeight", 64)
        origin = config.get("pos", Vec2(0, 0))
        self.origin = origin if isinstance(origin, Vec2) else vec2(*origin)
        self.objs = []

    def tile2Pos(self, col, row) -> Vec2:
        return Vec2(
            self.origin.x + col * self.tileWidth,
            self.origin.y + row * self.tileHeight,
        )

    def get(self, tag):
        return [o for o in self.objs if o.exists() and o.is_(tag)]


def addLevel(layout, config):
    from .engine import current_engine
    engine = current_engine()
    level = Level(config)
    tiles_map = config.get("tiles", {})

    for row_idx, row_str in enumerate(layout):
        for col_idx, ch in enumerate(row_str):
            if ch == " ":
                continue
            maker = tiles_map.get(ch)
            if maker is None:
                continue
            comp_list = maker()
            p = level.tile2Pos(col_idx, row_idx)
            obj = engine.add([pos_comp(p.x, p.y), *comp_list])
            level.objs.append(obj)

    return level
