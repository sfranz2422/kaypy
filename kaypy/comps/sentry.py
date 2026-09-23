"""sentry("player"): notice when something comes into view.

    guard = add([
        sprite("ghosty"), pos(400, 300), area(),
        sentry("player", direction=vec2(1, 0), fieldOfView=70,
               range=260, lineOfSight=True),
    ])

    @guard.onObjectsSpotted
    def seen(objects):
        say("Hey! Stop right there.")

A guard with a torch, a turret, a security camera, a fish that notices
crumbs. The component answers one question every so often — *which of the
things I care about can I see right now?* — and tells you when the answer
stops being empty.

WHAT COUNTS AS SEEING

Three tests, each of which can be left out:

    direction + fieldOfView   a cone. Without them it looks all ways.
    range                     how far. Without it, forever.
    lineOfSight               walls stop it. Without it, they do not.

`fieldOfView` is the whole width of the cone in degrees, so 90 means 45
either side of `direction`, and 360 is everywhere. If the object also has
`rotate()`, leaving `direction` out means it looks wherever it is facing —
turn the guard and the cone turns with it.

RANGE IS NOT KAPLAY'S, AND IS HERE ANYWAY

KAPLAY's sentry has no distance at all: a guard facing right can see you on
the far side of a scrolling level, through the whole rest of the game. That
is a reasonable default for a library and a bad one for the first stealth
game somebody writes, where the interesting question is always *how close
can I get*. Leave `range` out and it behaves exactly as KAPLAY's does, so
their examples still mean what they say.

WHY onObjectsSpotted FIRES ON THE EDGE

It is called when the sentry goes from seeing nothing to seeing something,
not on every frame it can see you — which would be sixty alarms a second
and sixty lines of dialogue on top of each other. Go out of sight and come
back and it fires again. `.spotted` is the current list, for the frames in
between:

    if guard.spotted:
        chase(guard.spotted[0])

CHECKING SIXTY TIMES A SECOND IS USUALLY WASTE

Every check walks the candidates, and with `lineOfSight` casts a ray at
each. A dozen guards doing that every frame is real work in a browser, to
answer a question that has not changed in 16 milliseconds. So
`checkFrequency` is how many times a second to look, defaulting to ten —
a tenth of a second late to notice an intruder is not something a player
can perceive, and it is six times less work.
"""
from ..gameobj import Comp, GameObj
from ..vec2 import Vec2, vec2


class SentryComp(Comp):
    id = "sentry"

    def __init__(self, candidates, direction=None, fieldOfView=None,
                 range=None, lineOfSight=False, raycastExclude=None,
                 checkFrequency=10):
        if isinstance(candidates, (str, GameObj)):
            candidates = [candidates]
        elif not (callable(candidates) or isinstance(candidates, (list, tuple))):
            raise TypeError(
                "sentry(%r) — say what to look for: a tag, a game object, a "
                "list of either, or a function returning a list.\n"
                "    sentry(\"player\")\n"
                "    sentry([player, dog])" % (candidates,))
        self.candidates = candidates

        if fieldOfView is not None and not 0 < fieldOfView <= 360:
            raise ValueError(
                "sentry(fieldOfView=%r) — the field of view is the whole "
                "width of the cone in degrees, so it goes from just above 0 "
                "to 360 (all the way round)." % (fieldOfView,))
        if range is not None and range <= 0:
            raise ValueError(
                "sentry(range=%r) — the range is how far it can see, in "
                "pixels, so it must be above zero. Leave it out to see "
                "forever." % (range,))
        if checkFrequency <= 0:
            raise ValueError(
                "sentry(checkFrequency=%r) — that is how many times a second "
                "to look, so it must be above zero." % (checkFrequency,))

        self.direction = None if direction is None else _as_direction(direction)
        self.fieldOfView = fieldOfView
        self.range = range
        self.lineOfSight = lineOfSight
        self.raycastExclude = raycastExclude
        self.checkFrequency = checkFrequency

        #: What it can see, as of the last check.
        self.spotted = []
        self._handlers = []
        self._since = 0.0

    # ---- what the object is facing ----------------------------------------

    @property
    def directionAngle(self):
        """Where it is looking, in degrees. None means all ways."""
        d = self._facing()
        return None if d is None else d.angle()

    def _facing(self):
        if self.direction is not None:
            return self.direction
        obj = getattr(self, "_obj", None)
        if obj is not None and obj.has("rotate"):
            # No explicit direction: look wherever the object is turned.
            return Vec2.fromAngle(obj.comp("rotate").angle)
        return None

    # ---- the three tests ---------------------------------------------------

    def isWithinFieldOfView(self, obj, direction=None, fieldOfView=None):
        """Is obj inside the cone? Ignores range and walls."""
        import math
        from ..geometry import get_world_pos

        facing = _as_direction(direction) if direction is not None else self._facing()
        view = self.fieldOfView if fieldOfView is None else fieldOfView
        if facing is None or view is None or view >= 360:
            return True

        me = get_world_pos(self._obj)
        to = get_world_pos(obj) - me
        if to.len() == 0:
            return True
        # The angle between two directions, the short way round — a guard
        # facing 350 degrees looking at something at 10 degrees is 20 apart,
        # not 340, and getting that wrong makes a cone that works except
        # when it straddles zero.
        gap = abs(_wrap180(to.angle() - facing.angle()))
        return gap <= view / 2.0

    def hasLineOfSight(self, obj):
        """Is there nothing solid between us?"""
        from ..geometry import get_world_pos
        from ..raycast import raycast

        me = get_world_pos(self._obj)
        to = get_world_pos(obj) - me
        if to.len() == 0:
            return True

        exclude = list(self.raycastExclude or ())
        # Ignoring itself is not optional: the ray starts inside the
        # sentry's own area(), so without this every sentry with a collision
        # box discovers that the first thing in its line of sight is itself,
        # and can never see anything.
        hit = raycast(me, to, exclude=exclude or None, ignore=[self._obj])
        if hit is None:
            # Nothing at all in the way — including the target, if it has no
            # area(). Seeing something that cannot be hit by a ray is the
            # right answer: the wall is what blocks sight, not the player.
            return True
        return hit.obj is obj or hit.distance >= to.len()

    def _visible(self, obj):
        from ..geometry import get_world_pos
        if obj is self._obj or not obj.exists() or not obj.has("pos"):
            return False
        if self.range is not None:
            if get_world_pos(self._obj).dist(get_world_pos(obj)) > self.range:
                return False
        if not self.isWithinFieldOfView(obj):
            return False
        if self.lineOfSight and not self.hasLineOfSight(obj):
            return False
        return True

    # ---- who to look at ----------------------------------------------------

    def _candidates(self):
        from ..engine import current_engine
        items = self.candidates
        if callable(items):
            items = items()
        out = []
        for item in items:
            if isinstance(item, str):
                out.extend(current_engine().get(item))
            elif isinstance(item, GameObj):
                out.append(item)
        return out

    # ---- the loop ----------------------------------------------------------

    def add(self, obj):
        self._obj = obj

    def update(self, obj):
        from ..engine import current_engine

        interval = 1.0 / self.checkFrequency
        self._since += current_engine().dt()
        if self._since < interval:
            return
        # Subtract the interval rather than zeroing, so the leftover carries
        # into the next one. Zeroing loses it, and the loss compounds: at
        # sixty frames a second, six frames of 1/60 come to 0.09999999999,
        # just under a tenth, so every check waits a seventh frame and
        # `checkFrequency=10` quietly runs at eight and a half.
        self._since -= interval
        if self._since > interval:
            # A long frame — a stalled tab, a slow machine — is one check,
            # not a queue of them to catch up on.
            self._since = 0.0

        was = bool(self.spotted)
        self.spotted = [o for o in self._candidates() if self._visible(o)]
        if self.spotted and not was:
            for fn in list(self._handlers):
                fn(self.spotted)

    def onObjectsSpotted(self, fn=None):
        """Run something when it starts seeing what it is looking for."""
        from ..callutil import register_or_decorate

        def register(f):
            self._handlers.append(f)
            return f

        return register_or_decorate(fn, register)


def _as_direction(value):
    """A direction as a Vec2, from a Vec2, a tuple, or an angle in degrees."""
    if isinstance(value, Vec2):
        return value.unit()
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return vec2(*value).unit()
    if isinstance(value, (int, float)):
        return Vec2.fromAngle(value)
    raise TypeError(
        "sentry(direction=%r) — a direction is a vec2 or an angle in "
        "degrees.\n"
        "    direction=vec2(1, 0)   # looking right\n"
        "    direction=90           # looking down" % (value,))


def _wrap180(degrees):
    """The same angle, expressed between -180 and 180."""
    return (degrees + 180.0) % 360.0 - 180.0


def sentry(candidates, direction=None, fieldOfView=None, range=None,
           lineOfSight=False, raycastExclude=None, checkFrequency=10):
    return SentryComp(candidates, direction=direction, fieldOfView=fieldOfView,
                      range=range, lineOfSight=lineOfSight,
                      raycastExclude=raycastExclude,
                      checkFrequency=checkFrequency)
