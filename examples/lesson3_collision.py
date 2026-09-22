from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("steel", "images/steel.png")

SPEED = 320

player = add([
    sprite("bean"),
    pos(center()),
    area(),
    body(),
    "player",
])

for i in range(3):
    add([
        sprite("ghosty"),
        pos(rand(0, width()), rand(0, height())),
        area(),
        "enemy",
    ])

add([
    sprite("steel"),
    pos(600, 300),
    area(),
    body(isStatic=True),
])

add([
    sprite("steel"),
    pos(200, 400),
    area(),
    body(mass=100),
])

onKeyDown("left", lambda: player.move(-SPEED, 0))
onKeyDown("right", lambda: player.move(SPEED, 0))
onKeyDown("up", lambda: player.move(0, -SPEED))
onKeyDown("down", lambda: player.move(0, SPEED))

player.onCollide("enemy", lambda e: e.destroy())

debug.inspect = True
