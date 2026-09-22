from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")

SPEED = 320

player = add([
    sprite("bean"),
    pos(center()),
    area(),
])

onKeyDown("left", lambda: player.move(-SPEED, 0))
onKeyDown("right", lambda: player.move(SPEED, 0))
onKeyDown("up", lambda: player.move(0, -SPEED))
onKeyDown("down", lambda: player.move(0, SPEED))

onClick(lambda: player.moveTo(mousePos()))

add([
    text("Arrow keys to move, click to teleport", size=20),
    pos(12, 12),
])
