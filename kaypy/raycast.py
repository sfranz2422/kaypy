"""raycast(origin, direction): what does a straight line hit first?

    hit = raycast(guard.pos, vec2(1, 0))
    if hit and hit.obj.is_("player"):
        print("I see you")

Line of sight, a laser sight, a bullet that arrives instantly, "is there
floor under me", "what did I click on". All the same question: starting
here and going that way, what is the first thing in the way?

Returns a `Hit` — `.obj`, `.point`, `.distance`, `.normal` — or `None` if
the ray reaches nothing. Only objects with `area()` can be hit, because an
area() box is what kaypy means by "solid enough to bump into". Pass
`exclude` a list of tags to ignore some of them:

    raycast(guard.pos, facing, exclude=["enemy"])   # walls stop me, guards don't

HOW IT WORKS, AND THE TWO THINGS THAT GO WRONG

Each box is tested with the slab method: work out when the ray enters and
leaves the box's x range, and the same for y, and the ray is inside the box
during the overlap of those two spans. It is a handful of divisions and no
loops, which matters when a dozen guards each cast a ray every frame.

The two ways it is usually got wrong are both about direction components of
zero, and both produce a bug that only shows up on axis-aligned rays — which
is to say, on exactly the rays a game actually casts:

  * a ray pointing straight along an axis has one component zero, and the
    slab maths divides by it. In IEEE floating point 1/0.0 is +inf rather
    than an error, and the comparisons that follow work out correctly, so
    the honest implementation is to let it happen rather than to add special
    cases which have to be right. What does NOT work is 0/0, which is nan,
    and nan silently fails every comparison it is in. So the origin sitting
    exactly on a boundary is handled explicitly below.

  * a ray that starts INSIDE a box. The entry time is then negative — the
    box began before the ray did. Reporting that as a hit at a negative
    distance puts the hit point behind the caster, and a guard standing in
    a doorway sees through the door it is standing in. Here it counts as a
    hit at distance zero, which is what "I am touching this" should mean.

WHY IT TAKES A DIRECTION AND NOT A SECOND POINT

Because "as far as it goes" is the common case, and a length is awkward to
invent for it. For a ray between two points, subtract them — the direction
does not have to be a unit vector, and `distance` is in pixels either way.
"""
from __future__ import annotations

import math

from .vec2 import Vec2, vec2


class Hit:
    """What a ray ran into."""

    __slots__ = ("obj", "point", "distance", "normal")

    def __init__(self, obj, point, distance, normal):
        #: The game object that was hit.
        self.obj = obj
        #: Where, in world coordinates.
        self.point = point
        #: How far along the ray, in pixels.
        self.distance = distance
        #: Which way the surface faces — vec2(-1, 0) for the left side of a
        #: box, and so on. What you bounce off.
        self.normal = normal

    def __repr__(self):
        return ("Hit(obj=%r, point=%r, distance=%.2f, normal=%r)"
                % (self.obj, self.point, self.distance, self.normal))


def _hit_box(ox, oy, dx, dy, rect, max_distance):
    """Where this ray meets this box, or None. Returns (distance, normal)."""
    near = 0.0
    far = max_distance if max_distance is not None else math.inf
    normal_axis, normal_sign = None, 0.0

    for axis in (0, 1):
        o = ox if axis == 0 else oy
        d = dx if axis == 0 else dy
        lo = rect.left if axis == 0 else rect.top
        hi = rect.right if axis == 0 else rect.bottom

        if d == 0.0:
            # Parallel to this pair of edges: it either never leaves the slab
            # or never enters it. No division, and in particular no 0/0.
            if o < lo or o > hi:
                return None
            continue

        t1 = (lo - o) / d
        t2 = (hi - o) / d
        # The face the ray goes IN through always faces back along the ray:
        # travelling right you arrive at a left-facing face, and travelling
        # left at a right-facing one. That depends only on the direction, so
        # swapping t1 and t2 below — which only puts them in order — must
        # not touch it. (Negating it here instead passes every test with a
        # rightward ray and gets every leftward one backwards.)
        sign = -1.0 if d > 0 else 1.0
        if t1 > t2:
            t1, t2 = t2, t1

        if t1 > near:
            near = t1
            normal_axis, normal_sign = axis, sign
        if t2 < far:
            far = t2
        if near > far:
            return None

    if normal_axis is None:
        # The origin is inside the box: nothing pushed `near` off zero.
        return 0.0, Vec2(0, 0)

    normal = (Vec2(normal_sign, 0) if normal_axis == 0
              else Vec2(0, normal_sign))
    return near, normal


def raycast(origin, direction, exclude=None, max_distance=None, ignore=None):
    """The first area() the ray hits, as a Hit, or None.

    `ignore` is a list of particular objects to pass through, as against
    `exclude`, which is tags. It exists for the commonest way to get a
    surprising answer out of this function: casting from an object's own
    position. The origin is then inside that object's own box, which is a
    hit, at distance zero, before anything else — so a guard checking
    whether it can see the player learns only that it can see itself.
    """
    from .engine import current_engine
    from .geometry import get_world_rect

    origin = vec2(origin) if not isinstance(origin, Vec2) else origin
    direction = vec2(direction) if not isinstance(direction, Vec2) else direction

    length = direction.len()
    if length == 0:
        raise ValueError(
            "raycast(origin, direction) — the direction cannot be vec2(0, 0), "
            "because a ray with no direction does not go anywhere.\n"
            "    raycast(player.pos, vec2(1, 0))      # to the right\n"
            "    raycast(a.pos, b.pos - a.pos)        # from a towards b")
    unit = Vec2(direction.x / length, direction.y / length)

    if exclude is None:
        skip = ()
    elif isinstance(exclude, str):
        skip = (exclude,)
    else:
        skip = tuple(exclude)

    passthrough = set()
    if ignore is not None:
        passthrough = {id(o) for o in
                       ([ignore] if not isinstance(ignore, (list, tuple, set))
                        else ignore)}

    engine = current_engine()
    best = None
    for obj in engine._objs:
        if not (obj.exists() and obj.has("area")):
            continue
        if id(obj) in passthrough:
            continue
        if skip and any(obj.is_(tag) for tag in skip):
            continue
        found = _hit_box(origin.x, origin.y, unit.x, unit.y,
                         get_world_rect(obj), max_distance)
        if found is None:
            continue
        distance, normal = found
        if best is None or distance < best.distance:
            best = Hit(obj,
                       Vec2(origin.x + unit.x * distance,
                            origin.y + unit.y * distance),
                       distance, normal)
    return best
