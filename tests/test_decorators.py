"""Standalone sanity script: every event can be written either way.

Kaplay's own form — hand the event a function — is what every Kaplay doc
page and example translates into directly, so it has to keep working
exactly as it did. The decorator form is an addition for Python's sake:
a lambda can only hold a single expression, and the workarounds for that
are the kind of thing you don't want in front of someone learning
(`lambda: p.jump() if p.isGrounded() else None` has an `else None` that
does nothing; `lambda: setattr(p, "pos", v)` reaches for setattr only
because a lambda can't assign).

So each event is checked twice here: once called with a function, once
used as a decorator, with the same assertion either way. Plus the thing
that would make the decorator form quietly useless — the decorated name
has to stay bound to the function, not to None or to a wrapper.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "1"

from kaypy import (  # noqa: E402
    kaypy, add, pos, rect, area, body, state, setGravity,
    onUpdate, onKeyDown, onKeyPress, onKeyRelease, onClick, wait, loop, scene,
)
from kaypy.engine import current_engine  # noqa: E402

kaypy(width=400, height=300, background=[0, 0, 0])
engine = current_engine()


def counts():
    ev, tm = engine.events, engine.timers
    return (
        len(ev.update_handlers), len(ev.key_down_handlers),
        len(ev.key_press_handlers), len(ev.key_release_handlers),
        len(ev.click_handlers),
    )


# --- 1. the callback form still registers exactly what it always did ---
before = counts()
onUpdate(lambda: None)
onUpdate("enemy", lambda o: None)
onKeyDown("left", lambda: None)
onKeyPress("space", lambda: None)
onKeyRelease("space", lambda: None)
onClick(lambda: None)
after_callbacks = counts()
assert [a - b for a, b in zip(after_callbacks, before)] == [2, 1, 1, 1, 1], \
    f"callback form registered {after_callbacks} from {before}"
print("confirmed: the callback form registers what it always did")


# --- 2. the decorator form registers the same things -------------------
@onUpdate
def _every_frame():
    pass


@onUpdate("enemy")
def _every_enemy(o):
    pass


@onKeyDown("left")
def _walk():
    pass


@onKeyPress("space")
def _jump():
    pass


@onKeyRelease("space")
def _stop():
    pass


@onClick
def _clicked():
    pass


after_decorators = counts()
assert [a - b for a, b in zip(after_decorators, after_callbacks)] == [2, 1, 1, 1, 1], \
    f"decorator form registered {after_decorators} from {after_callbacks}"
print("confirmed: the decorator form registers the same things")


# --- 3. the decorated name is still the function -----------------------
for fn, name in [(_every_frame, "_every_frame"), (_walk, "_walk"), (_jump, "_jump"),
                 (_clicked, "_clicked"), (_every_enemy, "_every_enemy")]:
    assert callable(fn), f"{name} is not callable after decoration — got {fn!r}"
    assert fn.__name__ == name, f"{name} lost its name, became {fn.__name__!r}"
print("confirmed: decorated handlers stay callable, and keep their own name")


# --- 4. per-object events, both ways -----------------------------------
setGravity(100)
player = add([pos(0, 0), rect(10, 10), area(), body(), "player"])
coin = add([pos(0, 0), rect(10, 10), area(), "coin"])

hits = []
player.onCollide("coin", lambda c: hits.append("callback"))


@player.onCollide("coin")
def _grab(c):
    hits.append("decorator")


@player.onGround
def _landed():
    hits.append("ground")


engine.collision.step(engine._objs)
assert "callback" in hits and "decorator" in hits, \
    f"both onCollide forms should have fired, got {hits}"
print("confirmed: object events fire identically whichever way they're written")


# --- 5. state machine handlers, both ways ------------------------------
seen = []
enemy = add([pos(0, 0), rect(10, 10), state("idle", ["idle", "attack"])])
enemy.onStateEnter("attack", lambda: seen.append("callback"))


@enemy.onStateEnter("attack")
def _on_attack():
    seen.append("decorator")


enemy.enterState("attack")
assert seen == ["callback", "decorator"], f"state handlers: got {seen}"
print("confirmed: state handlers fire in order, whichever way they're written")


# --- 6. timers and scenes ----------------------------------------------
fired = []
wait(0.01, lambda: fired.append("wait-callback"))


@wait(0.01)
def _later():
    fired.append("wait-decorator")


@loop(0.01)
def _repeatedly():
    fired.append("loop-decorator")


engine.timers.update(0.02)
assert set(fired) == {"wait-callback", "wait-decorator", "loop-decorator"}, \
    f"timers: got {fired}"

scene("a", lambda: None)


@scene("b")
def _build_b():
    pass


assert "a" in engine._scenes and "b" in engine._scenes, "both scene forms should register"
print("confirmed: wait/loop/scene work both ways")

print("ALL DECORATOR CHECKS PASSED")
