"""state(): gives an object a mode (idle, attack, move...) and different
behaviour in each — how nearly all simple game AI is written."""
from ..gameobj import Comp


class StateComp(Comp):
    id = "state"

    def __init__(self, start, states):
        self.states = list(states)
        if start not in self.states:
            raise ValueError(f"state() start {start!r} not in {self.states!r}")
        self._state = start
        self._enter_handlers = {}
        self._update_handlers = {}
        self._entered_once = False

    def add(self, obj):
        self._obj = obj

    def onStateEnter(self, name, fn=None):
        from ..callutil import register_or_decorate
        self._check(name)

        def register(f):
            self._enter_handlers.setdefault(name, []).append(f)
            return f

        return register_or_decorate(fn, register)

    def onStateUpdate(self, name, fn=None):
        from ..callutil import register_or_decorate
        self._check(name)

        def register(f):
            self._update_handlers.setdefault(name, []).append(f)
            return f

        return register_or_decorate(fn, register)

    def enterState(self, name):
        self._check(name)
        self._state = name
        for fn in self._enter_handlers.get(name, []):
            fn()

    def state_name(self):
        return self._state

    def update(self, obj):
        if not self._entered_once:
            # fire the starting state's onStateEnter handlers once, the
            # first frame this object exists.
            self._entered_once = True
            for fn in self._enter_handlers.get(self._state, []):
                fn()
        for fn in self._update_handlers.get(self._state, []):
            fn()

    def _check(self, name):
        if name not in self.states:
            raise ValueError(f"{name!r} is not one of this object's states {self.states!r}")


def state(start, states):
    return StateComp(start, states)
