"""Asteroids — what rotate() is for.

    python3 asteroids.py

Left and right turn the ship, up thrusts in the direction it is facing,
space fires. Rocks drift, split when hit, and wrap around the screen.

Not one of the thirteen lessons: it is the game the lessons build towards,
and the one that cannot be written at all without a ship that turns. Three
things here appear nowhere in the lessons and are the whole point of it:

    rotate(angle)            the ship turns
    Vec2.fromAngle(angle)    which way "forward" is, once it has turned
    a velocity of its own     momentum, so letting go of thrust coasts
"""
from kaypy import *

kaypy(width=800, height=600, background=[8, 8, 20])

TURN = 200          # degrees per second
THRUST = 320        # pixels per second per second
MAX_SPEED = 420
BULLET_SPEED = 560

score = 0

ship = add([
    rect(26, 18),
    pos(center()),
    anchor("center"),
    color(200, 230, 255),
    rotate(0),
    area(),
    "ship",
])
ship.vel = vec2(0, 0)

label = add([text("0", size=22), pos(12, 10), fixed()])


def wrap(obj):
    """Off one edge, on at the other — the rule that makes it Asteroids."""
    p = obj.pos
    if p.x < 0:
        obj.pos = vec2(width(), p.y)
    elif p.x > width():
        obj.pos = vec2(0, p.y)
    p = obj.pos
    if p.y < 0:
        obj.pos = vec2(p.x, height())
    elif p.y > height():
        obj.pos = vec2(p.x, 0)


def spawn_rock(at=None, chunks=3):
    r = add([
        circle(chunks * 11),
        pos(at or vec2(rand(0, width()), rand(0, 60))),
        anchor("center"),
        color(150, 140, 130),
        outline(2, (90, 85, 80)),
        area(),
        rotate(rand(0, 360)),
        "rock",
    ])
    r.vel = Vec2.fromAngle(rand(0, 360)) * rand(40, 110)
    r.spin = rand(-90, 90)
    r.chunks = chunks   # 3, 2, 1 — splits down to nothing
    return r


for _ in range(4):
    spawn_rock()


@onKeyDown("left")
def turn_left():
    ship.rotateBy(-TURN * dt())


@onKeyDown("right")
def turn_right():
    ship.rotateBy(TURN * dt())


@onKeyDown("up")
def thrust():
    ship.vel = ship.vel + Vec2.fromAngle(ship.angle) * THRUST * dt()
    if ship.vel.len() > MAX_SPEED:
        ship.vel = ship.vel.unit() * MAX_SPEED


@onKeyPress("space")
def fire():
    b = add([
        circle(3),
        pos(ship.pos),
        anchor("center"),
        color(255, 240, 160),
        area(),
        "bullet",
    ])
    b.vel = Vec2.fromAngle(ship.angle) * BULLET_SPEED
    wait(1.2, lambda: b.destroy() if b.exists() else None)


@onUpdate
def fly():
    ship.pos = ship.pos + ship.vel * dt()
    wrap(ship)
    for r in get("rock"):
        r.pos = r.pos + r.vel * dt()
        r.rotateBy(r.spin * dt())
        wrap(r)
    for b in get("bullet"):
        b.pos = b.pos + b.vel * dt()
        wrap(b)


@onUpdate
def shooting():
    global score
    for b in get("bullet"):
        for r in get("rock"):
            if not (b.exists() and r.exists()):
                continue
            if b.pos.dist(r.pos) < r.chunks * 11:
                b.destroy()
                r.destroy()
                score += 10 * r.chunks
                label.text = str(score)
                shake(6)
                if r.chunks > 1:
                    for _ in range(2):
                        spawn_rock(r.pos, r.chunks - 1)
                break
