"""A pet that trails you and a health bar that never does — what follow() is for

    python3 pet_and_healthbar.py

Arrows to move, space to jump, F to hurt the enemy. The ghost chases you and
falls behind when you run; the red bar over the enemy is welded to it and
never falls behind at all.

Both of those are one component. The difference between them is the word
`speed`:

    follow(target)              be exactly where it is
    follow(target, speed=180)   move toward it at 180 pixels a second

The bar is the interesting half. It is pinned to an object that gravity
moves, that collision shoves out of the floor, and that a keypress teleports
— and it stays put through all three, because follow() runs after the engine
has finished deciding where everything actually ended up, rather than before
like every other component. Without that it would sit correctly while the
enemy stands still and slide off it the moment the enemy moved, which looks
like a drawing bug and is not one.
"""
from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
setGravity(1600)

add([rect(width(), 48), pos(0, height() - 48), area(),
     body(isStatic=True), color(90, 150, 70)])

player = add([sprite("bean"), pos(120, 300), area(), body()])

# Locked on: no speed, so it is simply where the player is, plus an offset.
add([text("you", size=18), pos(0, 0), color(30, 40, 60),
     follow(player, offset=vec2(4, -28))])

# Chasing: with a speed, it heads for the player and arrives when it arrives.
add([sprite("ghosty"), pos(600, 200), follow(player, speed=180)])

enemy = add([sprite("ghosty"), pos(560, 400), area(), body(), health(5)])

# A health bar over something gravity is pulling down and the floor is
# pushing back up. This is the case that shows whether follow() runs early
# or late.
BAR = 48
backing = add([rect(BAR, 6), pos(0, 0), color(40, 20, 20),
               follow(enemy, offset=vec2(0, -14))])
bar = add([rect(BAR, 6), pos(0, 0), color(220, 60, 60),
           follow(enemy, offset=vec2(0, -14))])


@onKeyDown("left")
def go_left():
    player.move(-320, 0)


@onKeyDown("right")
def go_right():
    player.move(320, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(760)


@onKeyPress("f")
def hurt():
    if enemy.exists():
        enemy.hurt(1)
        bar.width = BAR * max(0, enemy.hp) / 5


@enemy.onDeath
def gone():
    # A follower whose target is destroyed stops where it stands and goes on
    # existing — which is right for a pet and wrong for a health bar, so the
    # bars are destroyed here, next to the thing they belonged to.
    enemy.destroy()
    backing.destroy()
    bar.destroy()


add([text("arrows move · space jumps · F hurts the ghost", size=20),
     pos(12, 12), color(20, 30, 50), fixed()])
