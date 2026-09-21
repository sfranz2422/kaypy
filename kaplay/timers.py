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


class TimerManager:
    def __init__(self):
        self._timers = []

    def wait(self, seconds, fn):
        t = _Timer(seconds, fn, repeat=False)
        self._timers.append(t)
        return t

    def loop(self, seconds, fn):
        t = _Timer(seconds, fn, repeat=True)
        self._timers.append(t)
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

    def clear(self):
        self._timers.clear()


def wait(seconds, fn):
    from .engine import current_engine
    return current_engine().timers.wait(seconds, fn)


def loop(seconds, fn):
    from .engine import current_engine
    return current_engine().timers.loop(seconds, fn)
