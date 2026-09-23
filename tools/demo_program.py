from kaypy import *

kaypy(width=360, height=300, background=[141, 183, 255])
loadSprite("bean", "images/bean.png")
setGravity(1600)

player = add([sprite("bean"), pos(60, 40), area(), body()])

add([rect(width(), 36), pos(0, height() - 36),
     area(), body(isStatic=True), color(90, 150, 70)])


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(620)
