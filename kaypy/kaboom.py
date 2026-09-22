"""addKaboom(pos): a small procedural explosion (expanding, fading
rings) so effects work without requiring a bundled 'kaboom' sprite."""


def addKaboom(position, scale=1.0):
    from .engine import current_engine
    from .comps.pos import pos as pos_comp
    from .comps.shapes import circle
    from .comps.transform import color as color_comp, opacity as opacity_comp, anchor as anchor_comp, z as z_comp

    engine = current_engine()
    rings = [
        (28 * scale, (255, 220, 80), 0.35),
        (20 * scale, (255, 140, 30), 0.30),
        (12 * scale, (255, 255, 255), 0.22),
    ]
    made = []
    for radius, col, life in rings:
        obj = engine.add([
            pos_comp(position.x, position.y),
            anchor_comp("center"),
            circle(radius),
            color_comp(*col),
            opacity_comp(1.0),
            z_comp(1000),
        ])
        made.append(obj)
        _attach_fade(engine, obj, life)
    return made[0]


def _attach_fade(engine, obj, life):
    state = {"t": 0.0}

    def step():
        state["t"] += engine.dt()
        frac = min(state["t"] / life, 1.0)
        obj.opacity = max(0.0, 1.0 - frac)
        if frac >= 1.0:
            obj.destroy()

    obj.onUpdate(step)
