from kaypy import *

kaplay(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
loadSprite("grass", "images/grass.png")
loadSprite("steel", "images/steel.png")
loadSprite("coin", "images/coin.png")
loadSprite("spike", "images/spike.png")

SPEED = 320
setGravity(2400)

layout = [
    "                          ",
    "                          ",
    "     $$                  ",
    "     =====      $$       ",
    "                =====    ",
    " @      ^^            $  ",
    "========================",
]

level = addLevel(layout, {
    "tileWidth": 64,
    "tileHeight": 64,
    "pos": vec2(0, 0),
    "tiles": {
        "=": lambda: [sprite("grass"), area(), body(isStatic=True)],
        "$": lambda: [sprite("coin"), area(), "coin"],
        "^": lambda: [sprite("spike"), area(), "danger"],
        "@": lambda: [sprite("bean"), area(), body(), anchor("bot"), "player"],
    },
})

player = level.get("player")[0]

onKeyDown("left", lambda: player.move(-SPEED, 0))
onKeyDown("right", lambda: player.move(SPEED, 0))
onKeyPress("space", lambda: player.jump(1000) if player.isGrounded() else None)

player.onCollide("danger", lambda d: setattr(player, "pos", level.tile2Pos(2, 5)))
player.onCollide("coin", lambda c: c.destroy())
