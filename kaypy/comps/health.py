"""health(): hit points, and something to do when they run out.

    enemy = add([sprite("ogre"), pos(300, 200), area(), health(3), "enemy"])

    @enemy.onDeath
    def died():
        addKaboom(enemy.pos)
        enemy.destroy()

WHY IT IS A COMPONENT AND NOT JUST A NUMBER

`enemy.hp = 3` works, and for one enemy it is simpler. It stops working at
the third place that takes a point off, because now three separate lines have
to remember to check whether it reached zero — and the one that forgets is the
enemy that survives at -2 hit points and cannot be killed.

`hurt()` is one place. Death is one event. That is the whole argument.
"""
from ..gameobj import Comp


class HealthComp(Comp):
    id = "health"

    def __init__(self, hp, maxHP=None):
        if hp is None:
            raise TypeError("health() needs a number of hit points, e.g. health(3)")
        self.hp = hp
        self.maxHP = maxHP if maxHP is not None else hp
        self._hurt_handlers = []
        self._heal_handlers = []
        self._death_handlers = []

    def add(self, obj):
        self._obj = obj

    # ---- changing it --------------------------------------------------

    def setHP(self, value):
        """Set hit points directly. Fires onDeath if this takes it to zero."""
        was = self.hp
        self.hp = min(value, self.maxHP)
        if self.hp <= 0 < was:
            self._fire(self._death_handlers)

    def hurt(self, amount=1):
        """Take damage. Fires onHurt, and onDeath if it reaches zero."""
        if amount < 0:
            raise ValueError(
                f"hurt({amount}) — to add hit points use heal({-amount})")
        was = self.hp
        self.hp = self.hp - amount
        self._fire(self._hurt_handlers, amount)
        # Strictly "crossed zero this time", so a second hit on something
        # already dead does not hold a second funeral for it.
        if self.hp <= 0 < was:
            self._fire(self._death_handlers)

    def heal(self, amount=1):
        """Get hit points back, never above maxHP. Fires onHeal."""
        if amount < 0:
            raise ValueError(
                f"heal({amount}) — to take hit points away use hurt({-amount})")
        before = self.hp
        self.hp = min(self.hp + amount, self.maxHP)
        gained = self.hp - before
        if gained:
            self._fire(self._heal_handlers, gained)

    def isAlive(self):
        return self.hp > 0

    # ---- being told about it ------------------------------------------

    def onHurt(self, fn=None):
        return self._register(self._hurt_handlers, fn)

    def onHeal(self, fn=None):
        return self._register(self._heal_handlers, fn)

    def onDeath(self, fn=None):
        """When hit points reach zero. It does NOT destroy the object — an
        enemy may want to play a death animation, drop a coin, or respawn."""
        return self._register(self._death_handlers, fn)

    def _register(self, where, fn):
        from ..callutil import register_or_decorate

        def register(f):
            where.append(f)
            return f

        return register_or_decorate(fn, register)

    def _fire(self, handlers, *args):
        from ..callutil import call_flexible

        for fn in list(handlers):
            call_flexible(fn, *args)


def health(hp, maxHP=None):
    return HealthComp(hp, maxHP)
