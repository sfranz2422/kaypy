from kaypy import *

kaypy(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")

bean = add([
    sprite("bean"),
    pos(80, 40),
    area(),
    color(0, 0, 255),
])
