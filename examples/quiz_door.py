from kaypy import *

kaypy(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
setGravity(2400)

add([rect(width(), 48), pos(0, height() - 48), area(), body(isStatic=True),
     color(90, 150, 70)])

player = add([sprite("bean"), pos(80, 100), area(), body(), anchor("bot")])
door = add([rect(40, 90), pos(650, height() - 138), area(), color(140, 90, 40),
            "door"])

score = 0
label = add([text("Score: 0", size=26), pos(12, 12), fixed()])


@onKeyDown("left")
def left():
    player.move(-320, 0)


@onKeyDown("right")
def right():
    player.move(320, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)


@player.onCollide("door")
def at_the_door(d):
    @ask("Which keyword starts a loop in Python?", ["if", "for", "def"], answer=1)
    def checked(correct):
        global score
        if correct:
            score += 1
            label.text = "Score: %d" % score
            d.destroy()
            say("The door swings open.")
        else:
            say("Not that one. Have another go.")


@onKeyPress("escape")
def toggle_pause():
    resume() if isPaused() else pause()
