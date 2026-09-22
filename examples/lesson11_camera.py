from kaypy import *

kaplay(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
loadSprite("grass", "images/grass.png")
loadSprite("coin", "images/coin.png")

SPEED = 320
setGravity(2400)

layout = [
    "                                          ",
    "     $      $      $      $               ",
    "     ====   ====   ====   =====           ",
    "                                          ",
    " @                                    $   ",
    "===========================================",
]

level = addLevel(layout, {
    "tileWidth": 64,
    "tileHeight": 64,
    "tiles": {
        "=": lambda: [sprite("grass"), area(), body(isStatic=True)],
        "$": lambda: [sprite("coin"), area(), "coin"],
        "@": lambda: [sprite("bean"), area(), body(), anchor("bot"), "player"],
    },
})

player = level.get("player")[0]

score = 0
score_label = add([text("0", size=28), pos(12, 12), fixed()])


def keep_camera_on_player():
    setCamPos(player.pos)


onUpdate(keep_camera_on_player)


def got_coin(c):
    global score
    c.destroy()
    score += 1
    score_label.text = str(score)
    setCamScale(1 + score * 0.02)


player.onCollide("coin", got_coin)

onKeyDown("left", lambda: player.move(-SPEED, 0))
onKeyDown("right", lambda: player.move(SPEED, 0))
onKeyPress("space", lambda: player.jump(1000) if player.isGrounded() else None)

onClick(lambda: print("clicked world position:", toWorld(mousePos())))
