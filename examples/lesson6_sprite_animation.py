from kaplay import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("dino", [
    "images/dino_0.png", "images/dino_1.png", "images/dino_2.png",
    "images/dino_3.png", "images/dino_4.png", "images/dino_5.png",
    "images/dino_6.png", "images/dino_7.png", "images/dino_8.png",
], anims={
    "idle": {"from": 0, "to": 0, "loop": True},
    "run": {"from": 0, "to": 8, "speed": 12, "loop": True},
})

SPEED = 300
setGravity(1600)

player = add([
    sprite("dino"),
    pos(center()),
    anchor("center"),
    area(),
    body(),
    scale(3),
    "player",
])

player.play("idle")

add([
    rect(width(), 48),
    pos(0, height() - 48),
    area(),
    body(isStatic=True),
    color(90, 74, 58),
])


def run_left():
    player.move(-SPEED, 0)
    player.flipX = True
    if player.isGrounded() and player.curAnim() != "run":
        player.play("run")


def run_right():
    player.move(SPEED, 0)
    player.flipX = False
    if player.isGrounded() and player.curAnim() != "run":
        player.play("run")


onKeyDown("left", run_left)
onKeyDown("right", run_right)
onKeyRelease("left", lambda: player.play("idle"))
onKeyRelease("right", lambda: player.play("idle"))

onKeyPress("space", lambda: player.jump(700) if player.isGrounded() else None)


# --- Lesson 6's shorter way: a spritesheet ----------------------------
# The real dungeon elf_m.png (vendored by kaplay's own tooling — see
# examples/CREDITS.md) is one 8-frame strip: idle over 0-3, run over 4-7.
loadSprite("elf_m", "dungeon/elf_m.png", sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})
elf = add([sprite("elf_m", anim="idle"), pos(200, 200), scale(3)])
