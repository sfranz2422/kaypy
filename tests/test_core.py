"""Standalone sanity script (see test_physics.py) covering: collision
edge-triggering, child objects following their parent, scene teardown,
and the state() component's transitions."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("KAYPY_TEST_MAX_FRAMES", "5")  # this script never calls run() itself;
# it finishes and lets the atexit-triggered loop run for a few frames, so
# it's exercising the same "script just ends" path every lesson relies on.

from kaypy import *  # noqa: E402
from kaypy.engine import current_engine  # noqa: E402

kaplay(width=400, height=400, background=[0, 0, 0])

# ---- child objects follow their parent -----------------------------------
parent = add([pos(50, 50), rect(10, 10)])
child = parent.add([pos(5, 5), rect(4, 4)])
from kaypy.geometry import get_world_pos  # noqa: E402
wp = get_world_pos(child)
assert (wp.x, wp.y) == (55, 55), f"child should be at parent+offset, got {wp}"
parent.pos.x = 100
wp2 = get_world_pos(child)
assert wp2.x == 105, f"child should move with its parent, got {wp2}"
print("child-object relative positioning ok")

# ---- collision fires onCollide once, onCollideUpdate while touching -----
counts = {"enter": 0, "update": 0, "end": 0}
a = add([pos(0, 0), rect(20, 20), area()])
b = add([pos(5, 5), rect(20, 20), area(), "thing"])
a.onCollide("thing", lambda o: counts.__setitem__("enter", counts["enter"] + 1))
a.onCollideUpdate("thing", lambda o: counts.__setitem__("update", counts["update"] + 1))
a.onCollideEnd("thing", lambda o: counts.__setitem__("end", counts["end"] + 1))

for _ in range(5):
    current_engine().collision.step(current_engine()._objs)
assert counts["enter"] == 1, f"onCollide should fire once (edge-triggered), got {counts['enter']}"
assert counts["update"] == 4, f"onCollideUpdate should fire on every later touching frame, got {counts['update']}"

b.pos.x = 1000  # move apart
current_engine().collision.step(current_engine()._objs)
assert counts["end"] == 1, f"onCollideEnd should fire once when contact breaks, got {counts['end']}"
print("collision edge-triggering ok:", counts)

# ---- scene teardown: go() throws away objects/events/timers -------------
def scene_a():
    add([pos(0, 0), rect(5, 5)])
    onUpdate(lambda: None)
    wait(999, lambda: None)


def scene_b():
    pass


scene("a", scene_a)
scene("b", scene_b)
go("a")
assert len(current_engine()._objs) >= 1
assert len(current_engine().events.update_handlers) >= 1
assert len(current_engine().timers._timers) >= 1
go("b")
assert current_engine()._objs == [], "go() should clear objects from the old scene"
assert current_engine().events.update_handlers == [], "go() should clear old event handlers"
assert current_engine().timers._timers == [], "go() should clear old timers"
print("scene teardown ok")

# ---- state machine transitions -------------------------------------------
log = []
e = add([pos(0, 0), rect(4, 4), state("idle", ["idle", "active"])])
e.onStateEnter("idle", lambda: log.append("enter-idle"))
e.onStateEnter("active", lambda: log.append("enter-active"))
e.onStateUpdate("active", lambda: log.append("update-active"))

e.comp("state").update(e)  # first frame fires the starting state's onStateEnter
assert log == ["enter-idle"], log
e.enterState("active")
e.comp("state").update(e)
e.comp("state").update(e)
assert log == ["enter-idle", "enter-active", "update-active", "update-active"], log
print("state machine ok:", log)

print("ALL CORE CHECKS PASSED")
