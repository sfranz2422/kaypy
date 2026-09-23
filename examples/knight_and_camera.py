"""A sword that goes where the knight goes — what child objects are for

    python3 knight_and_camera.py

Arrows to move, space to swing, 1/2/3 to change the camera. The sword, the
shield and the name tag are all children of the knight: nothing in the
movement code mentions any of them, and they follow anyway.

    knight = add([sprite("bean"), pos(200, 300), area()])
    sword  = knight.add([rect(8, 34), pos(26, -4), color(220, 220, 235)])

A child's `pos()` is measured from its parent, not from the screen. The
sword sits at +26, -4 *from the knight* and stays there through walking,
turning and being teleported, because there is nothing to keep in step —
it is one position, expressed once. Destroy the knight and the sword goes
with it.

That is the difference between this and follow(): a follower is a separate
object being kept in agreement every frame, which is what you want when the
two things meet later in the game. A child is part of the thing.

THE CAMERA KEYS

    1   setCamScale(1)              normal
    2   setCamScale(2)              zoomed in, both ways
    3   setCamScale(vec2(2, 0.6))   wide and squashed

The third is the one worth pressing. The scale is a vec2, so the two axes
can differ — a letterboxed cutscene, a squash as something lands, or a
deliberately wrong aspect ratio for a dream sequence. Everything obeys it
together: sprites, the children, the drawn cone of the swing, and the debug
boxes under F1.
"""
import math

from kaypy import *

kaypy(width=800, height=600, background=[26, 30, 42])

loadSprite("bean", "images/bean.png")

add([rect(2000, 40), pos(-600, 470), area(), body(isStatic=True),
     color(60, 70, 90)])
setGravity(1800)

knight = add([sprite("bean"), pos(200, 300), area(), body(), "knight"])

# Everything below hangs off the knight. None of it is mentioned again in
# the movement code.
sword = knight.add([rect(8, 34), pos(26, -4), color(220, 220, 235),
                    anchor("bot"), rotate(0)])
knight.add([rect(6, 24), pos(-10, 4), color(150, 110, 60)])          # shield
knight.add([text("Sir Bean", size=14), pos(-4, -22), color(200, 210, 230)])

add([text("arrows move · space swings · 1 2 3 camera", size=18),
     pos(12, 12), color(140, 150, 170), fixed()])

swing = [0.0]


@onKeyDown("left")
def go_left():
    knight.move(-240, 0)


@onKeyDown("right")
def go_right():
    knight.move(240, 0)


@onKeyPress("space")
def jump_or_swing():
    swing[0] = 0.35
    if knight.isGrounded():
        knight.jump(700)


@onUpdate
def animate_sword():
    if swing[0] > 0:
        swing[0] = max(0.0, swing[0] - dt())
        # A swing is just the child's own angle. The knight knows nothing.
        sword.angle = -110 * math.sin((0.35 - swing[0]) / 0.35 * math.pi)
    else:
        sword.angle = 0


@onUpdate
def chase():
    setCamPos(vec2(knight.pos.x, 300))


@onKeyPress("1")
def normal():
    setCamScale(1)


@onKeyPress("2")
def close():
    setCamScale(2)


@onKeyPress("3")
def letterbox():
    setCamScale(vec2(2, 0.6))
