from kaplay import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("coin", "images/coin.png")

SPEED = 320

player = add([
    sprite("bean"),
    pos(100, 300),
    area(),
    anchor("center"),
    "player",
])

enemy = add([
    sprite("ghosty"),
    pos(600, 300),
    area(),
    anchor("center"),
    state("move", ["idle", "attack", "move"]),
])

enemy.onStateEnter("idle", lambda: wait(0.5, lambda: enemy.enterState("attack")))


def start_attack():
    if player.exists():
        direction = player.pos.sub(enemy.pos).unit()
        add([
            sprite("coin"),
            pos(enemy.pos),
            anchor("center"),
            area(),
            move(direction, 400),
            offscreen(destroy=True),
            "bullet",
        ])
    wait(1, lambda: enemy.enterState("move"))


enemy.onStateEnter("attack", start_attack)
enemy.onStateEnter("move", lambda: wait(2, lambda: enemy.enterState("idle")))
enemy.onStateUpdate("move", lambda: enemy.moveTo(player.pos, 120))


def hit(b):
    b.destroy()
    addKaboom(player.pos)
    player.destroy()


player.onCollide("bullet", hit)

onKeyDown("left", lambda: player.move(-SPEED, 0))
onKeyDown("right", lambda: player.move(SPEED, 0))
onKeyDown("up", lambda: player.move(0, -SPEED))
onKeyDown("down", lambda: player.move(0, SPEED))
