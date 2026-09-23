"""Sneak past a guard who cannot see through walls — what sentry() is for

    python3 stealth_guard.py

Arrows to move. The guard sweeps a torch left and right; get into the cone
and it spots you. Hide behind a crate and it does not, because the cone is
light and the crate is solid.

The whole of the seeing is one component:

    sentry("player", fieldOfView=70, range=300, lineOfSight=True)

`fieldOfView` is the width of the cone in degrees. `range` is how far the
torch reaches — not KAPLAY's, added because "how close can I get" is the
question a stealth game is made of. `lineOfSight` casts a ray at you and
lets the crates stop it.

There is no `direction` here on purpose: without one, the sentry looks
wherever `rotate()` has the guard turned, so sweeping the torch is a matter
of changing `guard.angle` and the cone follows.

The cone you can see is drawn by hand in onDraw, out of the same three
numbers the component was given. Drawing it is worth the twenty lines: a
vision cone you cannot see is a rule the player has to infer by dying.
"""
import math

from kaypy import *

kaypy(width=800, height=600, background=[18, 20, 30])

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")

FOV = 70
RANGE = 300

player = add([sprite("bean"), pos(80, 500), area(), "player"])

# Crates. Solid, so they stop the guard's ray — and tagged, so the ray can
# be told about them.
for x, y in [(300, 180), (300, 260), (300, 340), (560, 420), (560, 500)]:
    add([rect(56, 56), pos(x, y), area(), color(90, 74, 58), outline(2),
         "crate"])

guard = add([
    sprite("ghosty"), pos(400, 120), area(), rotate(90),
    sentry("player", fieldOfView=FOV, range=RANGE, lineOfSight=True),
    "guard",
])

caught = add([text("", size=28), pos(12, 12), color(255, 120, 120), fixed()])
add([text("arrows to move · hide behind the crates", size=18),
     pos(12, 560), color(150, 160, 180), fixed()])


@onKeyDown("left")
def go_left():
    player.move(-220, 0)


@onKeyDown("right")
def go_right():
    player.move(220, 0)


@onKeyDown("up")
def go_up():
    player.move(0, -220)


@onKeyDown("down")
def go_down():
    player.move(0, 220)


# The torch sweeps between 50 and 130 degrees — down and to either side.
@onUpdate
def sweep():
    guard.angle = 90 + 40 * math.sin(time() * 0.8)


@guard.onObjectsSpotted
def spotted(objects):
    caught.text = "Spotted!"
    shake(8)


@onUpdate
def forget():
    # .spotted is the current answer, for the frames between edges.
    if not guard.spotted and caught.text:
        caught.text = ""


@onDraw
def draw_cone():
    """The cone, drawn from the same numbers the sentry was given.

    Its far edge is cut short wherever a crate is in the way, which is the
    same question the component asks — so what you see and what the guard
    sees cannot disagree.
    """
    seeing = bool(guard.spotted)
    edge = (255, 210, 120) if not seeing else (255, 120, 120)

    points = [guard.pos]
    steps = 24
    for i in range(steps + 1):
        angle = guard.angle - FOV / 2 + FOV * i / steps
        along = Vec2.fromAngle(angle)
        hit = raycast(guard.pos, along, exclude=["player"], ignore=[guard],
                      max_distance=RANGE)
        reach = hit.distance if hit else RANGE
        points.append(guard.pos + along * reach)

    drawLines(points=points, width=2, color=edge, opacity=0.55, close=True)
