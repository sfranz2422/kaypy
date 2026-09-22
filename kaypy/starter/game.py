"""A starter kaypy game. Run it with:

    python game.py

and press the arrow keys. Then start changing things — that is the whole
point of it being this short.

GUIDE.md in the kaypy project walks through thirteen lessons that build
on this one.
"""
from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
loadSprite("grass", "images/grass.png")
loadSprite("coin", "images/coin.png")

SPEED = 320
setGravity(2400)

# The ground. area() gives it a collision box; body(isStatic=True) makes
# that box solid and immovable, so the player can stand on it.
add([
    rect(width(), 48),
    pos(0, height() - 48),
    area(),
    body(isStatic=True),
    color(90, 150, 70),
])

player = add([
    sprite("bean"),
    pos(120, 100),
    area(),
    body(),
    anchor("bot"),        # pos() now means "where its feet are"
])

# A coin to collect. area() with no body() is a trigger you pass through,
# rather than something you bump into.
add([
    sprite("coin"),
    pos(600, height() - 100),
    area(),
    "coin",
])

score = 0
score_label = add([text("0", size=28), pos(12, 12), fixed()])


@onKeyDown("left")
def move_left():
    player.move(-SPEED, 0)


@onKeyDown("right")
def move_right():
    player.move(SPEED, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)


@player.onCollide("coin")
def collect(coin):
    global score
    coin.destroy()
    score += 1
    score_label.text = str(score)


add([
    text("Arrows to move, space to jump", size=20),
    pos(12, 50),
    fixed(),
])
