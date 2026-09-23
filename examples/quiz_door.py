"""A door that asks a question — what ask(), say() and pause() are for.

    python3 quiz_door.py

Arrows to move, space to jump, escape to pause. Walk into the door and the
game stops and asks you something; get it right and the door opens.

Not one of the thirteen lessons: it is the smallest complete example of the
one thing a teacher asks for that a game engine usually cannot do. Three
names here appear nowhere in the lessons:

    ask(question, choices, answer=n)   stop and ask, then run a callback
    say(text)                          stop and show a line of text
    pause() / resume() / isPaused()    freeze the game where it stands

The question is a callback rather than a return value because a browser
cannot block: nothing can wait for an answer without stopping the frame that
would draw the question. So `ask` puts the panel up and hands you the answer
when there is one, and the game is paused in between.
"""
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
