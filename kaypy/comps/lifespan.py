"""lifespan(): destroy this after a few seconds.

    add([sprite("bullet"), pos(player.pos), move(0, -400), lifespan(2)])

Bullets, explosions, damage numbers, footprints. Anything that appears, does
its job, and should stop existing without anyone having to remember it.

`wait(2, lambda: b.destroy())` does the same thing and is what this replaces.
The difference is where it lives: the lifespan belongs to the bullet, next to
its sprite and its speed, rather than in a timer somewhere else that refers
back to it. When the bullet is destroyed early — it hit something — the
lifespan goes with it, while a stray wait() would still be holding the object
alive until it fired into nothing.

    lifespan(1, fade=0.5)

fades the last half-second out instead of vanishing mid-air, which is most of
what makes an explosion look finished rather than interrupted. Fading needs an
opacity() on the object; without one the object simply disappears at the end,
and says so once rather than every frame.
"""
from ..gameobj import Comp


class LifespanComp(Comp):
    id = "lifespan"

    def __init__(self, seconds, fade=0):
        if seconds is None or seconds < 0:
            raise ValueError(
                f"lifespan({seconds!r}) — give it a number of seconds, e.g. lifespan(2)")
        if fade < 0:
            raise ValueError(f"lifespan(fade={fade!r}) cannot be negative")
        self.seconds = seconds
        self.fade = min(fade, seconds)
        self._left = seconds
        self._warned = False

    def add(self, obj):
        self._obj = obj

    def update(self, obj):
        from ..engine import current_engine

        self._left -= current_engine().dt()

        if self._left <= 0:
            obj.destroy()
            return

        if self.fade and self._left < self.fade:
            if obj.has("opacity"):
                obj.comp("opacity").opacity = max(0.0, self._left / self.fade)
            elif not self._warned:
                # Once, not sixty times a second — and it keeps running,
                # because a bullet that vanishes abruptly is still a bullet
                # that went away, which is what was asked for.
                self._warned = True
                print("note: lifespan(fade=...) needs an opacity() component "
                      "to fade — add opacity(1) to this object, or drop the "
                      "fade argument.")


def lifespan(seconds, fade=0):
    return LifespanComp(seconds, fade)
