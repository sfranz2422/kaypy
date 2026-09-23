"""follow(obj): keep this object where another one is.

    bar = add([rect(40, 6), pos(0, 0), color(220, 60, 60),
               follow(enemy, offset=vec2(-4, -30))])

A health bar over an enemy, a name over a player, an arrow pointing at the
thing you are meant to go to next. The follower is placed on the target every
frame, so it does not matter how the target moved — walked, jumped, fell,
got shoved by a collision, or was picked up and put somewhere by one line of
code. It is simply there.

    pet = add([sprite("ghosty"), pos(0, 0), follow(player, speed=180)])

With `speed`, it chases instead: it moves toward the target at that many
pixels per second and arrives when it arrives. That is the difference between
a health bar and a pet, and it is one keyword.

WHY THIS RUNS AFTER PHYSICS AND ALMOST NOTHING ELSE DOES

A component's update() runs before the physics step, which is right for
nearly everything: you decide what an object is trying to do, and then the
engine works out where everything actually ended up.

A follower is the exception, because its whole job is to agree with where
another object ended up. Reading the target's position before physics reads
last frame's. Standing still that is invisible; on a player halfway through a
jump at 800 px/s it is thirteen pixels, so the health bar sits correct while
the player walks and slides off them the moment they jump. That is a bug
which looks like a rendering problem, appears only sometimes, and is very
hard to see in a position readout.

So follow() sets `wants_late`, and the engine gives it a second pass after
collision has finished. Nothing else in kaypy needs one, and a game with no
followers never makes the pass at all.

WHAT HAPPENS WHEN THE TARGET IS DESTROYED

The follower stops where it is, and goes on existing. It does not vanish and
it does not fall back to the origin — either of which would be a mysterious
thing to watch happen. If a health bar should die with its enemy, destroy it
where the enemy is destroyed:

    @enemy.onCollide("bullet")
    def hit(bullet):
        enemy.destroy()
        bar.destroy()

which says what it means in the one place it is true.
"""
from ..gameobj import Comp, GameObj
from ..vec2 import vec2, Vec2


class FollowComp(Comp):
    id = "follow"
    wants_late = True

    def __init__(self, obj, offset=None, speed=None):
        if not isinstance(obj, GameObj):
            raise TypeError(
                "follow(%r) — follow() takes a game object to follow, the one "
                "add() gave back.\n"
                "    player = add([sprite(\"bean\"), pos(100, 100)])\n"
                "    add([sprite(\"ghosty\"), pos(0, 0), follow(player)])"
                % (obj,))
        if not obj.has("pos"):
            raise ValueError(
                "follow() was given an object with no pos() — there is "
                "nowhere to follow it to. Add pos() to it.")
        if speed is not None and speed <= 0:
            raise ValueError(
                "follow(speed=%r) — speed is how fast to chase, in pixels per "
                "second, so it must be above zero. Leave it out to stick to "
                "the target exactly." % (speed,))

        self.obj = obj
        self.speed = speed
        if offset is None:
            self.offset = vec2(0, 0)
        elif isinstance(offset, Vec2):
            self.offset = Vec2(offset.x, offset.y)
        else:
            self.offset = vec2(*offset)

    def add(self, obj):
        self._obj = obj
        if not obj.has("pos"):
            raise ValueError(
                "follow() needs a pos() on the object doing the following — "
                "that is what it moves. Add pos() alongside it.")

    def late_update(self, obj):
        target = self.obj
        if target is None or not target.exists():
            # Stop where it is. See the note at the top of this file.
            return

        from ..geometry import get_world_pos

        want = get_world_pos(target) + self.offset
        # pos() is relative to a parent, if the follower has one, so a
        # world-space target has to come back into the parent's frame or the
        # follower lands at double the parent's offset.
        if obj.parent is not None:
            want = want - get_world_pos(obj.parent)

        place = obj.comp("pos")
        if self.speed is None:
            place.pos = Vec2(want.x, want.y)
        else:
            place.moveTo(want, self.speed)


def follow(obj, offset=None, speed=None):
    return FollowComp(obj, offset=offset, speed=speed)
