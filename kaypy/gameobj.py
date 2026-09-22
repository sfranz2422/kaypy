"""GameObj: the entity, built out of a list of components (and tags).

Kaplay literally merges each component's properties onto the object
(Object.assign). We fake that with attribute delegation in __getattr__,
which is also what produces the "has no attribute" error the guide's
troubleshooting section describes when a component is missing.
"""
from __future__ import annotations

_next_id = 0


def _new_id():
    global _next_id
    _next_id += 1
    return _next_id


class Comp:
    """Base class for all components. Subclasses set `id` and may
    implement add/update/draw hooks, plus any methods/attributes that
    should appear directly on the owning GameObj.
    """
    id: str = ""

    def add(self, obj: "GameObj"):
        """Called once, when the component is attached to obj."""

    def update(self, obj: "GameObj"):
        """Called every frame, if the engine has one running."""

    def draw(self, obj: "GameObj", ctx):
        """Called every frame during rendering."""

    def destroy(self, obj: "GameObj"):
        """Called once, when obj is destroyed."""


class GameObj:
    def __init__(self, comp_list=None):
        self._id = _new_id()
        self._comps: dict[str, Comp] = {}
        self.tags: set[str] = set()
        self.children: list["GameObj"] = []
        self.parent: "GameObj | None" = None
        self._destroyed = False
        self._engine = None  # set by Engine.add / obj.add
        self._event_handlers: dict[str, list] = {}
        if comp_list:
            self.use_all(comp_list)

    # ---- component wiring -------------------------------------------------

    def use(self, comp):
        """Attach a single component or tag string."""
        if isinstance(comp, str):
            self.tags.add(comp)
            return
        if not isinstance(comp, Comp):
            raise TypeError(
                f"add([...]) expects components or tag strings, got {comp!r}"
            )
        self._comps[comp.id] = comp
        comp.add(self)

    def use_all(self, comp_list):
        for c in comp_list:
            self.use(c)

    def has(self, comp_id: str) -> bool:
        return comp_id in self._comps

    def comp(self, comp_id: str):
        return self._comps.get(comp_id)

    # ---- KAPLAY-style attribute delegation ---------------------------------

    def __getattr__(self, name):
        # __getattr__ only fires when normal attribute lookup fails,
        # so this never shadows things set in __init__/__dict__.
        comps = self.__dict__.get("_comps", {})
        for c in comps.values():
            if hasattr(c, name):
                return getattr(c, name)
        raise AttributeError(
            f"GameObj has no attribute '{name}' — "
            f"did you forget a component that provides it?"
        )

    def __setattr__(self, name, value):
        # Allow plain-assignment mutation of component fields, e.g.
        # player.flipX = True (Lesson 6). Only redirect if the name is
        # not one of GameObj's own declared fields and a component owns it.
        if name.startswith("_") or name in (
            "tags", "children", "parent",
        ):
            object.__setattr__(self, name, value)
            return
        comps = self.__dict__.get("_comps")
        if comps:
            for c in comps.values():
                if hasattr(c, name):
                    # Refuse to replace a component's METHOD with a value.
                    # `rock.size = 3` looks like storing a number on your own
                    # object; it actually overwrites circle()'s size() method,
                    # and the game then dies somewhere else entirely with
                    # "'int' object is not callable" — in the collision system,
                    # nowhere near the line that did it. Found by writing
                    # examples/asteroids.py and losing a while to exactly that.
                    if callable(getattr(c, name)) and not callable(value):
                        raise AttributeError(
                            f"'{name}' is a method that {type(c).__name__} "
                            f"gives this object, so assigning to it would "
                            f"break the component. Pick another name for your "
                            f"own value — rock.{name}_value, or something "
                            f"that says what it is."
                        )
                    setattr(c, name, value)
                    return
        object.__setattr__(self, name, value)

    # ---- tree ---------------------------------------------------------------

    def add(self, comp_list):
        """Add a child object. Children are positioned/drawn relative to
        their parent and moved along with it (Lesson 8)."""
        child = GameObj(comp_list)
        child.parent = self
        child._engine = self._engine
        self.children.append(child)
        if self._engine:
            self._engine._register(child)
        return child

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        for c in list(self._comps.values()):
            c.destroy(self)
        for child in list(self.children):
            child.destroy()
        if self.parent:
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
        if self._engine:
            self._engine._unregister(self)

    def exists(self) -> bool:
        return not self._destroyed

    def is_(self, tag: str) -> bool:
        return tag in self.tags

    # ---- events (mirrors the free onX functions, but scoped to this obj) --

    def _on(self, event, tag_or_fn, fn=None):
        if fn is None:
            handler = tag_or_fn
            tag = None
        else:
            tag = tag_or_fn
            handler = fn
        self._event_handlers.setdefault(event, []).append((tag, handler))
        return handler

    # Each of these takes a function, or is used as a decorator over one:
    #     player.onCollide("coin", pick_up)
    #     @player.onCollide("coin")
    #     def pick_up(coin): ...
    # See callutil.register_or_decorate for why both forms exist.

    def onUpdate(self, fn=None):
        from .callutil import register_or_decorate
        return register_or_decorate(fn, lambda f: self._on("update", f))

    def onClick(self, fn=None):
        if not self.has("area"):
            raise RuntimeError("onClick() needs area() on this object")
        from .callutil import register_or_decorate
        return register_or_decorate(fn, lambda f: self._on("click", f))

    def onCollide(self, tag, fn=None):
        if not self.has("area"):
            raise RuntimeError("onCollide() needs area() on this object")
        from .callutil import register_or_decorate
        return register_or_decorate(fn, lambda f: self._on("collide", tag, f))

    def onCollideUpdate(self, tag, fn=None):
        if not self.has("area"):
            raise RuntimeError("onCollideUpdate() needs area() on this object")
        from .callutil import register_or_decorate
        return register_or_decorate(fn, lambda f: self._on("collideUpdate", tag, f))

    def onCollideEnd(self, tag, fn=None):
        if not self.has("area"):
            raise RuntimeError("onCollideEnd() needs area() on this object")
        from .callutil import register_or_decorate
        return register_or_decorate(fn, lambda f: self._on("collideEnd", tag, f))

    def _fire(self, event, tag=None, *args):
        from .callutil import call_flexible
        for h_tag, handler in list(self._event_handlers.get(event, [])):
            if h_tag is None or h_tag == tag:
                call_flexible(handler, *args)
