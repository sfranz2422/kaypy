"""Not pytest-wired yet (see README) — a standalone sanity script:
run it directly and it exits 0 only if gravity, grounding and collision
resolution behave the way Lesson 5 / Lesson 3 describe."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from kaplay import *  # noqa: E402

kaplay(width=800, height=600, background=[0, 0, 0])
setGravity(1600)

player = add([
    rect(32, 32),
    pos(400, 100),
    area(),
    body(),
])

ground = add([
    rect(800, 48),
    pos(0, 552),
    area(),
    body(isStatic=True),
])

box = add([
    rect(32, 32),
    pos(200, 300),
    area(),
    body(mass=100),
])

pusher = add([
    rect(32, 32),
    pos(120, 300),
    area(),
    body(mass=1),
])

jumped = {"done": False}


def after_settled():
    assert player.isGrounded(), f"expected player grounded, pos={player.pos}"
    start_y = player.pos.y
    player.jump(800)
    jumped["done"] = True


wait(1.0, after_settled)


def push_check():
    # pusher should have nudged the much heavier box only slightly
    assert pusher.pos.x > 120, "pusher should have moved toward the box"
    assert box.pos.x >= 200, "heavy box should not have been pushed backwards"
    print("push resolution ok: pusher.x=%.2f box.x=%.2f" % (pusher.pos.x, box.pos.x))


def move_pusher():
    pusher.move(200, 0)


onUpdate(move_pusher)
wait(1.5, push_check)

os.environ["KAYPY_TEST_MAX_FRAMES"] = "150"
run()

assert player.pos.y < 552, "player should have stopped ON TOP of the ground, not inside it"
assert abs(player.pos.y - (552 - 32)) < 2, f"player should rest at y={552-32}, got {player.pos.y}"
assert jumped["done"], "the wait() timer for jumping never fired"
print("physics sanity checks passed. player.pos=", player.pos)
