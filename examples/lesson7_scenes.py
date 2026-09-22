from kaypy import *

kaypy(width=800, height=600)
setBackground(0, 0, 0)

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("coin", "images/coin.png")
loadSprite("portal", "images/portal.png")
loadSound("ding", "sounds/ding.wav")
loadSound("danger", "sounds/screech.wav")

SPEED = 320


def game():
    score = 0
    coin_mult = 1.0

    player = add([sprite("bean"), pos(center()), area(), "player"])

    onKeyDown("left", lambda: player.move(-SPEED, 0))
    onKeyDown("right", lambda: player.move(SPEED, 0))
    onKeyDown("up", lambda: player.move(0, -SPEED))
    onKeyDown("down", lambda: player.move(0, SPEED))

    for i in range(20):
        add([
            sprite("coin"),
            pos(rand(20, width() - 20), rand(20, height() - 20)),
            area(),
            "coin",
        ])

    score_label = add([text("0", size=28), pos(12, 12)])

    def got_coin(c):
        nonlocal score, coin_mult
        c.destroy()
        score += 1
        coin_mult += 0.05
        score_label.text = str(score)
        play("ding")

    player.onCollide("coin", got_coin)

    for i in range(5):
        add([
            sprite("ghosty"),
            pos(rand(0, width()), rand(0, height())),
            area(),
            "enemy",
        ])

    onUpdate("enemy", lambda g: g.moveTo(player.pos, 70 * coin_mult))

    def caught(e):
        play("danger")
        go("lose", score)

    player.onCollide("enemy", caught)

    add([
        sprite("portal"),
        pos(rand(20, width() - 20), rand(20, height() - 20)),
        area(),
        "portal",
    ])

    player.onCollide("portal", lambda p: go("win", score))


def lose(score):
    add([text("You lost", size=48), pos(center()), anchor("center")])
    add([text("Score: " + str(score), size=28),
         pos(center().x, center().y + 60), anchor("center")])
    onKeyPress("space", lambda: go("game"))


def win(score):
    add([text("You win!", size=48), pos(center()), anchor("center")])
    add([text("Score: " + str(score), size=28),
         pos(center().x, center().y + 60), anchor("center")])
    onKeyPress("space", lambda: go("game"))


scene("game", game)
scene("lose", lose)
scene("win", win)

go("game")
