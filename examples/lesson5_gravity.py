from kaypy import *

kaypy(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")

setGravity(1600)

player = add([
    sprite("bean"),
    pos(center()),
    area(),
    body(),
])

add([
    rect(width(), 48),
    pos(0, height() - 48),
    outline(4),
    area(),
    body(isStatic=True),
    color(127, 200, 255),
])


def jump():
    if player.isGrounded():
        player.jump(800)


onKeyPress("space", jump)

player.onGround(lambda: print("landed"))

add([
    text("Press space to jump", size=24, width=320),
    pos(12, 12),
    color(255, 255, 255),
])
