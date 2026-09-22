from kaypy import *

kaypy(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")


def spawn():
    b = add([
        sprite("bean"),
        pos(rand(0, width()), rand(0, height())),
        area(),
    ])
    wait(3, lambda: b.destroy())


loop(0.5, spawn)
