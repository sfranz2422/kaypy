"""Kaplay's own timers (wait/loop) — tied to the frame loop, so they
pause and resume with the game, unlike Python's own time functions."""
from .callutil import call_flexible


class _Timer:
    def __init__(self, delay, fn, repeat):
        self.delay = delay
        self.fn = fn
        self.repeat = repeat
        self.elapsed = 0.0
        self.dead = False

    def cancel(self):
        self.dead = True


def _lerp(a, b, t):
    """Blend two values. Numbers, Vec2s and colour tuples all tween.

    A tween is almost always moving one of those three, and requiring a
    student to know which is which would be a worse lesson than the tween.
    """
    from .vec2 import Vec2

    if isinstance(a, Vec2) or isinstance(b, Vec2):
        return Vec2(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)
    if isinstance(a, (tuple, list)):
        return type(a)(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


class Tween:
    """What `tween()` hands back: a handle on something still happening.

    `.then(fn)` runs something after it, `.cancel()` stops it where it is,
    `.finish()` jumps it to the end, and `.paused` holds it. All four are
    Kaplay's own names, so its documentation applies.
    """

    def __init__(self, start, end, duration, setter, ease):
        self.start = start
        self.end = end
        self.duration = float(duration)
        self.setter = setter
        self.ease = ease
        self.elapsed = 0.0
        self.paused = False
        self.dead = False
        self._ends = []

    def onEnd(self, fn):
        self._ends.append(fn)
        return self

    #: Kaplay spells this `then`, and it chains.
    then = onEnd

    def cancel(self):
        """Stop it where it is. Nothing further is set and onEnd never runs."""
        self.dead = True

    def finish(self):
        """Jump straight to the end value, and run the onEnd handlers."""
        if self.dead:
            return
        self.dead = True
        self.setter(self.end)
        self._fire()

    def _fire(self):
        for fn in self._ends:
            call_flexible(fn)

    def update(self, dt):
        if self.dead or self.paused:
            return
        self.elapsed += dt
        # A zero-length tween is an instant set, not a division by zero.
        progress = 1.0 if self.duration <= 0 else min(self.elapsed / self.duration, 1.0)
        self.setter(_lerp(self.start, self.end, self.ease(progress)))
        if progress >= 1.0:
            self.dead = True
            # Land exactly on the end value. An eased curve can return
            # 0.9999999 at t=1, and a sprite that stops one pixel short of
            # where it was told to go is a bug nobody can see but everybody
            # can feel.
            self.setter(self.end)
            self._fire()


class TimerManager:
    def __init__(self):
        self._timers = []
        self._tweens = []

    def wait(self, seconds, fn):
        t = _Timer(seconds, fn, repeat=False)
        self._timers.append(t)
        return t

    def loop(self, seconds, fn):
        t = _Timer(seconds, fn, repeat=True)
        self._timers.append(t)
        return t

    def tween(self, start, end, duration, setter, ease=None):
        from .easings import easings as _easings

        t = Tween(start, end, duration, setter, ease or _easings.linear)
        self._tweens.append(t)
        return t

    def update(self, dt):
        for t in list(self._timers):
            if t.dead:
                continue
            t.elapsed += dt
            if t.elapsed >= t.delay:
                t.elapsed -= t.delay
                if t.repeat:
                    call_flexible(t.fn)
                else:
                    t.dead = True
                    call_flexible(t.fn)
        self._timers = [t for t in self._timers if not t.dead]

        for t in list(self._tweens):
            t.update(dt)
        self._tweens = [t for t in self._tweens if not t.dead]

    def clear(self):
        self._timers.clear()
        self._tweens.clear()


def wait(seconds, fn):
    from .engine import current_engine
    return current_engine().timers.wait(seconds, fn)


def loop(seconds, fn):
    from .engine import current_engine
    return current_engine().timers.loop(seconds, fn)
