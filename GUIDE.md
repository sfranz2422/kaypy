# Learn Kaplay — in Python

Thirteen lessons, the same thirteen as the Learn Kaplay site, written for
**kaypy**.

Every name below — `add`, `sprite`, `onKeyDown`, `loadSpriteAtlas` — is Kaplay's
own name, in Kaplay's own order, with Kaplay's own arguments. Which means the
Kaplay documentation, and every Kaplay example on the internet, still applies to
what you write here.

The difference from Kaplay itself is underneath: this is real Python, drawing
through [pygame-ce](https://pyga.me). Nothing is transpiled and there is no
JavaScript involved. The same file you run on your machine is the one that
becomes a web page.

> kaypy is an independent project, not affiliated with or endorsed by the
> KAPLAY team. It follows their API on purpose — that is what lets their
> documentation answer your questions — but it is a separate implementation.

---

## Getting started

Every game in this guide is an ordinary Python file that begins:

```python
from kaypy import *
```

That line brings in every Kaplay name. Everything else follows from it.

There are two ways to run what you write, and **the lessons themselves are
identical in both** — same code, same results. Use whichever you're set up for.

### In PyIDE

Press **+ Game**. You get a project that already starts with the import line
above — which is also how the editor knows this is a game rather than an
ordinary program, and what makes the picture appear instead of the console.

Press **Run** to play, and **click the picture once** so the keys reach the
game. Press **Stop** when you want the keyboard back for typing.

### On your own machine

Install once, then make yourself a game to work in:

```bash
pip install kaypy
kaypy new mygame
cd mygame
```

That folder has a small working game in `game.py`, and all the sprites and
sounds these lessons use. Run it:

```bash
python game.py
```

A window opens and the game is already running. Close it to stop.

To turn the same file into a web page instead:

```bash
kaypy web game.py
```

That gives you one HTML file. Double-click it and the game plays — no server,
nothing to install. It is also the file you upload to itch.io if you want to
put the game somewhere other people can play it.

**There is no `run()` call anywhere in this guide**, either way. The loop starts
on its own once your file has finished being read.

### Where the pictures and sounds live

Paths look the same wherever you run:

```python
loadSprite("bean", "images/bean.png")       # the Kaplay pack — cartoon sprites
loadSprite("elf_m", "dungeon/elf_m.png")    # the dungeon pack — pixel art
loadSound("ding", "sounds/ding.wav")        # sounds
```

In PyIDE, the **Sprites** button opens every sprite and sound there is; click one
and it inserts the lines you need, so you never type a path by hand. The search
box covers both packs at once, and a ▶ in the corner of a cell means that sprite
animates.

On your own machine, `kaypy new` put those same three folders next to your
`game.py`, so the paths line up already. (Working from a checkout of the
project instead? They're in `examples/`, so run the lessons from in there.)

Either way, **the two sprite packs are separate folders**, and that matters: a
dungeon sprite is not in `images/`. There is also `dungeon.png`, the dungeon
artwork as one uncut image — that is a sprite atlas, and Lesson 12 is about
cutting one up yourself.

---

## Reading JavaScript Kaplay as Python

You will find Kaplay examples written in JavaScript everywhere, including on the
Learn Kaplay site. Here is the whole translation.

| JavaScript | Python |
|---|---|
| `kaplay({ width: 800 })` | `kaplay(width=800)` |
| `body({ jumpForce: 800 })` | `body(jumpForce=800)` |
| `const SPEED = 300;` | `SPEED = 300` |
| `function jump() { ... }` | `def jump(): ...` |
| `if (a && !b) { ... }` | `if a and not b: ...` |
| `true` / `false` / `null` | `True` / `False` / `None` |
| `// a comment` | `# a comment` |
| `{ ... }` blocks | indentation |
| `;` at the end of a line | nothing |

Two rules worth stating plainly:

**Options in curly braces become keyword arguments.** Anywhere the JavaScript
shows `{ speed: 10, loop: true }`, you write `speed=10, loop=True`.

**Callbacks can ignore arguments they don't want.** Kaplay hands `onKeyDown` the
key that was pressed, but a handler that takes nothing works anyway, exactly as
`() => ...` does in JavaScript. If you do want the key, give your function a
parameter and you will get it.

### Event handlers

This is the one place where the Python is shaped differently from the
JavaScript, and it is an improvement. JavaScript writes an event like this:

```javascript
onKeyPress("space", () => {
    if (player.isGrounded()) player.jump(800)
})
```

In Python you put the event **above** the function it should run:

```python
@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(800)
```

The `@` line reads as a label: *when space is pressed, run this*. The function
underneath is an ordinary function — as many lines as you like, `if` statements,
variables, anything.

Every event in this guide works that way. You can also hand an event a function
directly, which is what the JavaScript translates to literally:

```python
onKeyPress("space", jump)
```

Both do exactly the same thing. Use whichever is clearer. Where you see Kaplay's
JavaScript use a one-line arrow function, Python's equivalent is a `lambda`:

```javascript
onKeyDown("left", () => player.move(-300, 0))   // JavaScript
```
```python
onKeyDown("left", lambda: player.move(-300, 0))  # Python, same thing
```

You never have to write one. This guide uses the `@` form throughout, because
a `lambda` can only hold a single expression — the moment a handler needs an
`if`, or to change a variable, a `lambda` can't do it and you need a real
function anyway.

---

## 1 — Adding a game object

In Kaplay everything you put on the screen — players, bullets, rocks, clouds,
text — is a **game object**. You build one out of **components**, and each
component gives it one ability.

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")

bean = add([
    sprite("bean"),
    pos(80, 40),
    area(),
    color(0, 0, 255),
])
```

Run it — **Run** in PyIDE, or `python game.py` on your machine. Bean is on
the screen.

**What each part does.**

`kaplay(...)` starts the engine. It has to come first, before anything else.

`loadSprite("bean", "images/bean.png")` makes a picture available under the name
`bean`. Loading and using are two separate steps, and forgetting the load is the
commonest reason a sprite doesn't appear.

`add([...])` builds a game object out of a list of components:

- `sprite("bean")` — draw it using the picture called `bean`
- `pos(80, 40)` — put it at x=80, y=40
- `area()` — give it a collision box, so it can bump into things
- `color(0, 0, 255)` — tint it blue

There are many more components. You will meet most of them in the lessons below.

> **Challenge**
>
> 1. Use a different sprite. Click **Sprites** to see them all, or look in
>    `examples/images/`.
> 2. Play with the position, colour and scale. Try adding `scale(1.5)`, and try
>    `pos(width() / 2, height() / 2)` — `width()` and `height()` give you the
>    size of the game window, so that puts the object dead centre.

---

## 2 — Player movement

Input handling and moving things about.

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")

SPEED = 320                          # pixels per second

player = add([
    sprite("bean"),
    pos(center()),
    area(),
])


@onKeyDown("left")
def move_left():
    player.move(-SPEED, 0)


@onKeyDown("right")
def move_right():
    player.move(SPEED, 0)


@onKeyDown("up")
def move_up():
    player.move(0, -SPEED)


@onKeyDown("down")
def move_down():
    player.move(0, SPEED)


@onClick
def teleport():
    player.moveTo(mousePos())


add([
    text("Arrow keys to move, click to teleport", size=20),
    pos(12, 12),
])
```

**What each part does.**

`center()` gives you the middle of the screen — it is shorthand for
`vec2(width() / 2, height() / 2)`.

`@onKeyDown(key)` above a function registers an event that runs **every frame
while the key is held down**. This pattern — name an event, give it a function
to run — is the shape of nearly everything in Kaplay. Learn it once here.

`@onClick` has no argument to give it, so it needs no brackets. Everything else
in this guide does.

`.move()` comes from the `pos()` component. **A component gives an object
abilities, and the object only has the abilities its components gave it.** No
`pos()`, no `.move()`. This is worth stopping on, because it explains a whole
category of confusing error later.

`.move()` is measured in **pixels per second**, not pixels per frame. Kaplay
multiplies by the frame time for you, so your game runs at the same speed on a
fast computer and a slow one.

`.moveTo()` also comes from `pos()`, and puts the object somewhere rather than
nudging it.

`text()` is a component just like `sprite()`, but it draws words instead of a
picture.

---

## 3 — Collision handling

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("steel", "images/steel.png")

SPEED = 320

player = add([
    sprite("bean"),
    pos(center()),
    area(),
    body(),
    "player",
])

# Three enemies, made with an ordinary Python for loop.
for i in range(3):
    add([
        sprite("ghosty"),
        pos(rand(0, width()), rand(0, height())),
        area(),
        "enemy",
    ])

# A wall that nothing can push. isStatic means it never moves.
add([
    sprite("steel"),
    pos(600, 300),
    area(),
    body(isStatic=True),
])

# Heavy, but not immovable — you can shove it, slowly.
add([
    sprite("steel"),
    pos(200, 400),
    area(),
    body(mass=100),
])


@onKeyDown("left")
def move_left():
    player.move(-SPEED, 0)


@onKeyDown("right")
def move_right():
    player.move(SPEED, 0)


@onKeyDown("up")
def move_up():
    player.move(0, -SPEED)


@onKeyDown("down")
def move_down():
    player.move(0, SPEED)


@player.onCollide("enemy")
def hit_enemy(enemy):
    enemy.destroy()
```

**What each part does.**

`area()` is what makes collision possible. **Both** objects need it — an object
without `area()` is invisible to collision, and this is the single most common
reason a collision "doesn't work".

`body()` makes an object respond to physics. `body(isStatic=True)` makes it a
wall: solid, and never moved by anything. `body(mass=100)` makes it heavy but
still pushable.

`"player"` and `"enemy"` in the component list are **tags**. A tag is just a
label you can look objects up by later.

`@obj.onCollide(tag)` comes from `area()`. It runs when this object touches an
object carrying that tag, and the thing it touched is handed to your function —
that's the `enemy` parameter above. There are two relatives:

- `@obj.onCollideUpdate(tag)` runs every frame while they are touching
- `@obj.onCollideEnd(tag)` runs once when they stop touching

Also from `area()`: `@obj.onClick` runs when the object itself is clicked, and
`.isHovering()` returns `True` while the mouse is over it.

**A debugging tool worth knowing now.** Add this line and every collision box is
drawn on screen:

```python
debug.inspect = True
```

You can also press **F1** while the game is running. When a collision isn't
firing, look at the boxes before you look at the code — usually they simply
aren't touching.

### About `dt()`

`dt()` is the time since the last frame. You use it as a multiplier when you
move something by hand:

```python
@onUpdate
def drift():
    rock.move(0, 50 * dt())
```

`.move()` already does this for you, which is why the movement code above has no
`dt()` in it. Reach for `dt()` when you are changing a number yourself — a
timer, a fade, a score that climbs over time.

---

## 4 — Review assignment

No new material. Build this from memory, checking back only when stuck.

1. Initialize Kaplay.
2. Put a sprite on the screen that responds to collisions. (Which component
   makes collision possible?)
3. Put a rectangle on the screen. Think — you want a `rect()` component. What
   arguments would it take?

*Hint for 3:* a rectangle needs a width and a height, and like everything else it
needs a `pos()` to say where it goes.

---

## 5 — Gravity

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")

setGravity(1600)                             # pixels per second, per second

player = add([
    sprite("bean"),
    pos(center()),
    area(),
    body(),
])

# A platform to land on.
add([
    rect(width(), 48),
    pos(0, height() - 48),
    outline(4),
    area(),
    body(isStatic=True),
    color(127, 200, 255),
])


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(800)


@player.onGround
def landed():
    print("landed")


add([
    text("Press space to jump", size=24, width=320),
    pos(12, 12),
    color(255, 255, 255),
])
```

**What each part does.**

`setGravity(1600)` switches gravity on for the whole game. Nothing falls until
you call it.

`body()` is what makes an object respond to gravity. And `body()` is what gives
you these:

- `.isGrounded()` — `True` when standing on something
- `.jump(force)` — launch upward
- `@obj.onGround` — an event that runs each time it lands

Again: no `body()`, none of these exist. If you get an error saying an object has
no `jump`, you forgot `body()`.

The `if player.isGrounded()` check is what stops infinite mid-air jumping. Take
it out and see.

**`onKeyPress` runs once per press; `onKeyDown` runs every frame while held.**
Jumping wants `onKeyPress`.

The platform is a `rect()` with `body(isStatic=True)` — solid and immovable.
`outline(4)` draws a border round it.

`text()` takes options like everything else: `size=24` sets the height,
`width=320` wraps the words at that many pixels.

> **Exercise**
>
> Add left and right movement from Lesson 2, so you can jump and run.

---

## 6 — Sprite animation

An animation is several pictures shown in turn. The Kaplay pack has a nine-frame
dino walk cycle — `dino_0` through `dino_8` — so you can build one from the
frames you already have:

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

# One sprite made out of nine pictures. The frames are numbered 0 to 8 in the
# order you list them.
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


@onKeyDown("left")
def run_left():
    player.move(-SPEED, 0)
    player.flipX = True
    if player.isGrounded() and player.curAnim() != "run":
        player.play("run")


@onKeyDown("right")
def run_right():
    player.move(SPEED, 0)
    player.flipX = False
    if player.isGrounded() and player.curAnim() != "run":
        player.play("run")


@onKeyRelease("left")
def stop_left():
    player.play("idle")


@onKeyRelease("right")
def stop_right():
    player.play("idle")


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(700)
```

**What each part does.**

`anims=` names ranges of frames. `"run": {"from": 0, "to": 8, "speed": 12}`
means "frames 0 through 8, twelve frames per second, forever". `speed` is frames
per second; `loop` decides whether it repeats.

`.play(name)` comes from `sprite()` and starts one of those animations.

**`.play()` restarts the animation from its first frame.** So calling it every
frame while a key is held gives you a character stuck on frame 0, twitching.
That is what `player.curAnim() != "run"` is for — only start the run animation if
it isn't already running. This catches everyone once.

Notice how much the `@` form is earning here. `run_left` changes a variable,
checks two conditions and calls a method — none of which fits in a `lambda`.

`anchor("center")` says which point of the picture `pos()` refers to. Without it,
`pos()` means the top-left corner.

**It takes a name, not a position.** `anchor(center())` looks reasonable — the
line above it is `pos(center())` — but it is the one mistake in this guide that
costs a whole lesson. `center()` is a place on the screen; an anchor is an offset
between −1 and 1. The number is accepted either way and your sprite is drawn
thousands of pixels off screen, with no error and nothing on the canvas.

```python
anchor("center")        # right — a name
anchor(center())        # wrong — a screen position
anchor(vec2(0, 1))      # also right — bottom edge, an offset in -1..1
```

`player.flipX = True` mirrors the sprite so it faces the other way. Notice this
is a plain assignment, not a method call.

`scale(3)` draws it three times the size — the dino frames are only 16×26 pixels.

**The shorter way: a spritesheet.** A spritesheet is many frames in one image
file, and Kaplay slices it for you. The dungeon pack is built this way — every
one of its characters is a single strip holding all of their animations end to
end:

```python
loadSprite("elf_m", "dungeon/elf_m.png",
           sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})

player = add([sprite("elf_m", anim="idle"), pos(200, 200), scale(3)])
```

`sliceX` is how many frames across, `sliceY` how many down. `anims` names the
runs of frames: `elf_m` is eight frames, the first four an idle and the next four
a run.

You don't have to type any of that. In PyIDE, click the elf in the **Sprites**
panel and it appears, filled in — then change it. Turn `speed` up and the elf
runs faster. Set `"loop": False` on the run and it stops after one lap.

`anim="idle"` starts an animation the moment the object is added, and
`.play("run")` switches it later — exactly as in the dino version above.

> **Exercise**
>
> The player walks off the edge of the screen. Add an `@onUpdate` that keeps them
> on it. *Hint:* compare `player.pos.x` against `0` and `width()`.

---

## 7 — Scenes

A scene is one part of your game: a menu, the game itself, a game-over screen.
Each one is a function, and `go()` switches between them.

```python
from kaypy import *

kaplay(width=800, height=600)
setBackground(0, 0, 0)

loadSprite("bean", "images/bean.png")
loadSprite("ghosty", "images/ghosty.png")
loadSprite("coin", "images/coin.png")
loadSprite("portal", "images/portal.png")
loadSound("ding", "sounds/ding.wav")
loadSound("danger", "sounds/screech.wav")

SPEED = 320


@scene("game")
def game():
    score = 0
    coin_mult = 1.0

    player = add([sprite("bean"), pos(center()), area(), "player"])

    @onKeyDown("left")
    def move_left():
        player.move(-SPEED, 0)

    @onKeyDown("right")
    def move_right():
        player.move(SPEED, 0)

    @onKeyDown("up")
    def move_up():
        player.move(0, -SPEED)

    @onKeyDown("down")
    def move_down():
        player.move(0, SPEED)

    for i in range(20):
        add([
            sprite("coin"),
            pos(rand(20, width() - 20), rand(20, height() - 20)),
            area(),
            "coin",
        ])

    score_label = add([text("0", size=28), pos(12, 12)])

    @player.onCollide("coin")
    def got_coin(c):
        nonlocal score, coin_mult
        c.destroy()
        score += 1
        coin_mult += 0.05
        score_label.text = str(score)
        play("ding")

    for i in range(5):
        add([
            sprite("ghosty"),
            pos(rand(0, width()), rand(0, height())),
            area(),
            "enemy",
        ])

    # Every frame, every ghost drifts toward the player — and speeds up as the
    # player collects coins.
    @onUpdate("enemy")
    def chase(ghost):
        ghost.moveTo(player.pos, 70 * coin_mult)

    @player.onCollide("enemy")
    def caught(e):
        play("danger")
        go("lose", score)

    add([
        sprite("portal"),
        pos(rand(20, width() - 20), rand(20, height() - 20)),
        area(),
        "portal",
    ])

    @player.onCollide("portal")
    def escaped(p):
        go("win", score)


@scene("lose")
def lose(score):
    add([text("You lost", size=48), pos(center()), anchor("center")])
    add([text("Score: " + str(score), size=28),
         pos(center().x, center().y + 60), anchor("center")])

    @onKeyPress("space")
    def restart():
        go("game")


@scene("win")
def win(score):
    add([text("You win!", size=48), pos(center()), anchor("center")])
    add([text("Score: " + str(score), size=28),
         pos(center().x, center().y + 60), anchor("center")])

    @onKeyPress("space")
    def restart():
        go("game")


go("game")            # nothing happens until you start a scene
```

**What each part does.**

`@scene("name")` above a function registers a scene. `go("name")` switches to it,
and everything from the previous scene is thrown away — objects, events, all of
it. That is the point: you never have to clean up by hand.

`go("lose", score)` passes a value through, and the scene function receives it as
a parameter: `def lose(score):`.

**Nothing runs until `go()` is called.** That last line is the one everybody
forgets.

Notice that the events live *inside* the scene functions. They have to: they
refer to `player`, which doesn't exist until the scene runs. A decorator runs at
the moment Python reaches it, so an `@onKeyDown` indented inside `game()` is
registered when `game()` is called, not before.

`setBackground(0, 0, 0)` sets the background outside the `kaplay()` call — handy
when you want to change it later.

`@onUpdate("enemy")` runs the function every frame for every object tagged
`enemy`. The object is handed to your function.

`.moveTo(target, speed)` moves toward a point at a given speed, rather than
jumping straight there.

**About `nonlocal`.** `score` belongs to the `game` function, and `got_coin` is a
function inside it. Python needs `nonlocal score` to say "change the outer one,
don't make a new one". Leave it out and the score stays at zero forever,
silently. This is the one Python-specific gotcha in the whole guide.

---

## 8 — Audio and buttons

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSound("bell", "sounds/ding.wav")
loadSound("bgMusic", "sounds/background.wav")

# Start the music paused, so it doesn't play until we say so.
music = play("bgMusic", loop=True, paused=True, volume=0.5)

bell_button = add([
    rect(200, 60, radius=8),
    pos(100, 100),
    area(),
    color(80, 120, 220),
])

# Added to the BUTTON, not to the screen — so (16, 18) is measured from the
# button's own corner, and the text travels with it if the button moves.
bell_button.add([
    text("Ring the bell", size=20),
    pos(16, 18),
])


@bell_button.onClick
def ring():
    play("bell")


music_button = add([
    rect(200, 60, radius=8),
    pos(100, 200),
    area(),
    color(220, 120, 80),
])

music_button.add([text("Play music", size=20), pos(30, 18)])


@music_button.onClick
def toggle_music():
    music.paused = not music.paused
```

**What each part does.**

`loadSound(name, path)` works just like `loadSprite`.

`play(name)` plays a sound once. `play(name, loop=True, paused=True)` hands you
back a **handle** you can control — `music.paused = False` starts it,
`music.volume = 0.2` turns it down.

The bell needs no handle, because we never want to control it — we just want it
to go off.

**Child objects.** `bell_button.add([...])` adds the text to the button rather
than to the screen. Positions of a child are relative to its parent, and a child
moves when its parent moves.

Think about where else that's useful: a player carrying a sword, a health bar
floating above an enemy's head, a label on a moving platform. Make it a child and
you never have to keep the two positions in step by hand.

`@obj.onClick` on an object needs `area()` on that object — the click has to land
somewhere.

---

## 9 — Timer and loop

Kaplay has its own timers. Use them instead of Python's, because Kaplay's are
tied to the frame loop and stay in step with the game.

```python
from kaypy import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSprite("bean", "images/bean.png")


# Every half second, for as long as the game runs.
@loop(0.5)
def spawn():
    b = add([
        sprite("bean"),
        pos(rand(0, width()), rand(0, height())),
        area(),
    ])

    # ...and three seconds after it appears, it goes away again.
    @wait(3)
    def remove_it():
        b.destroy()
```

**What each part does.**

`@loop(seconds)` runs the function over and over, that many seconds apart.

`@wait(seconds)` runs the function once, after a delay.

Both are measured in seconds and both are managed by Kaplay, so they pause and
resume with the game and never drift out of step with what's on screen.

Notice the `@wait(3)` nested inside `spawn`. Each bean that appears schedules its
own removal, and `b` inside `remove_it` means *that* bean — the one this run of
`spawn` just made.

You will use `wait()` constantly: a delay before a respawn, a pause before the
game-over screen appears, a gap between waves of enemies.

---

## 10 — Levels

Drawing a map by hand gets old fast. `addLevel()` lets you draw it as a picture
made of characters.

```python
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
    "                          ",
    "      $$                  ",
    "    =====        $$       ",
    "                =====     ",
    " @         ^^          $  ",
    "==========================",
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


@onKeyDown("left")
def move_left():
    player.move(-SPEED, 0)


@onKeyDown("right")
def move_right():
    player.move(SPEED, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)


# Touch a spike and you go back to the start.
@player.onCollide("danger")
def hit_spike(spike):
    player.pos = level.tile2Pos(1, 6)


@player.onCollide("coin")
def collect(coin):
    coin.destroy()
```

**What each part does.**

The `layout` is a list of strings. Each character becomes one tile, and the
`tiles` dictionary says what each character means. A space means nothing at all.

Each entry in `tiles` is **a function returning a component list** — that is why
every one of them is `lambda: [...]`. It has to be a function because Kaplay
calls it once per tile; a plain list would give every tile the same single
object. (`lambda: [...]` is just a one-line function that returns the list. It is
not an event handler, which is why it isn't written with `@`.)

`tileWidth` and `tileHeight` are the size of one tile in pixels. Match them to
your sprites — the bundled `grass` and `steel` are 64×64.

`level.get("player")[0]` finds the object you tagged `player` inside the level,
so you can control it. `get` returns a list, hence the `[0]`.

`level.tile2Pos(col, row)` converts a tile position into real pixels. The `@`
above is at column 1, row 6.

Notice `player.pos = ...` in `hit_spike`. That is an ordinary assignment, and it
is only possible because the handler is a real function — you cannot assign
inside a `lambda`.

Design your map on paper first, or with an ASCII map editor. Keep all the rows
the same length.

> **Exercises**
>
> 1. Send the player to a game-over scene when they fall off the bottom.
>    *Hint:* `@onUpdate` and check `player.pos.y > height()`.
> 2. Add a score that goes up when a coin is collected.

---

## 11 — Camera

When the level is bigger than the window, the camera follows the player.

```python
from kaypy import *

kaplay(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")
loadSprite("grass", "images/grass.png")
loadSprite("coin", "images/coin.png")

SPEED = 320
setGravity(2400)

layout = [
    "                                             ",
    "                                             ",
    "       $      $        $        $            ",
    "    ====    =====    =====    ======         ",
    "                                             ",
    " @                                        $  ",
    "=============================================",
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

# A score that does NOT scroll with the world.
score_label = add([
    text("0", size=28),
    pos(12, 12),
    fixed(),
])


@onUpdate
def keep_camera_on_player():
    setCamPos(player.pos)


@player.onCollide("coin")
def got_coin(c):
    global score
    c.destroy()
    score += 1
    score_label.text = str(score)
    setCamScale(1 + score * 0.02)      # zoom in a little with every coin


@onKeyDown("left")
def move_left():
    player.move(-SPEED, 0)


@onKeyDown("right")
def move_right():
    player.move(SPEED, 0)


@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)


# Where did I actually click, in the world?
@onClick
def report_click():
    print("clicked world position:", toWorld(mousePos()))
```

**What each part does.**

`setCamPos(position)` points the camera somewhere. Calling it from `@onUpdate`
every frame is what makes it follow.

`setCamScale(n)` zooms. Bigger than 1 zooms in.

`fixed()` is the component that makes an object ignore the camera. Score labels,
health bars, buttons — anything that should stay stuck to the screen rather than
to the world — needs `fixed()`. Leave it off the score and it slides away as you
walk.

`toWorld(mousePos())` converts a position on the screen into a position in the
world. Once the camera has moved, those are different things, and mixing them up
is a genuinely confusing bug. `mousePos()` is where the mouse is on screen;
`toWorld(...)` is what it's pointing at in the game.

`global score` here does the same job `nonlocal` did in Lesson 7 — `score` lives
at the top level of the file, so `global` is the right word for it.

---

## 12 — Sprite atlas

An atlas is one image holding many different sprites, each at a known position.
You load it once and name the pieces. `dungeon.png` is one — it is in the
**Sprites** panel under *Sprite atlas*, and in `examples/` on disk. Clicking it
in PyIDE inserts all of this:

```python
loadSpriteAtlas("dungeon.png", {
    "wall": {"x": 16, "y": 16, "width": 16, "height": 16},
    "floor": {"x": 16, "y": 64, "width": 48, "height": 48, "sliceX": 3, "sliceY": 3},
    "hero": {
        "x": 128, "y": 196, "width": 144, "height": 28, "sliceX": 9,
        "anims": {
            "idle": {"from": 0, "to": 3, "speed": 3, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
            "hit": 8,
        },
    },
    "ogre": {
        "x": 16, "y": 336, "width": 256, "height": 32, "sliceX": 8,
        "anims": {
            "idle": {"from": 0, "to": 3, "speed": 3, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
        },
    },
    "chest": {
        "x": 304, "y": 400, "width": 48, "height": 16, "sliceX": 3,
        "anims": {
            "open": {"from": 0, "to": 2, "speed": 20, "loop": False},
            "close": {"from": 2, "to": 0, "speed": 20, "loop": False},
        },
    },
})
```

> **The published coordinates for this image are wrong, and nothing will tell
> you.** The version you find online has `ogre` at `y: 320` and `chest` at
> `y: 304`. Both are wrong for this image: `y: 320` is 16 pixels above the
> ogres, so you get the top half of an ogre and a strip of floor, and `y: 304`
> is empty space, so the chest loads with nothing in it. Neither one is an
> error — Kaplay will cut out a rectangle of nothing without complaint. Which
> is the whole lesson: **the numbers are not checked for you**, so when a sprite
> comes out wrong or missing, suspect the rectangle first.

**What each part does.**

Each entry says where its sprite sits in the big image: `x` and `y` are how far
in from the left and down from the top, `width` and `height` how big the whole
strip is.

`sliceX` and `sliceY` cut that strip into frames — `"sliceX": 9` means nine
frames side by side.

`anims` names ranges of those frames, exactly as in Lesson 6. An animation can
also be a single number (`"hit": 8` means "frame 8").

Animations are optional. `floor` and `wall` above have none — they are just
pictures.

**Atlas or ready-made?** The dungeon pack — the **Sprites** panel, or
`examples/dungeon/` on disk — is this same artwork, already cut up and named.
Reaching for one of those is faster and you cannot get a rectangle wrong. Use the
atlas when the artwork you want is in one image somebody else laid out, which is
most artwork you will find online.

Building a level from an atlas is the same `addLevel()` as Lesson 10, run twice:
once for the floor, then once for the walls and objects on top, so things sit
above the floor rather than under it.

```python
# The floor, drawn first. A space means floor here, so we don't have to type
# a character for every square.
addLevel(floor_layout, {
    "tileWidth": 16,
    "tileHeight": 16,
    "tiles": {
        " ": lambda: [sprite("floor", frame=randi(0, 8))],
    },
})

# Then everything that stands on it.
addLevel(map_layout, {
    "tileWidth": 16,
    "tileHeight": 16,
    "tiles": {
        "#": lambda: [sprite("wall"), area(), body(isStatic=True), tile(isObstacle=True)],
        "$": lambda: [sprite("chest"), area(), tile()],
    },
})
```

`frame=randi(0, 8)` picks a random floor tile, so the floor is different every
time the game loads.

`tile()` marks an object as occupying a square on a grid.

> **Exercise**
>
> Make the chests play their open animation when space is pressed.

---

## 13 — Using state to handle AI

A state machine gives an object a **mode** — idle, attack, move — and different
behaviour in each. It is how nearly all simple game AI is written.

```python
from kaypy import *

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
    # Start in "move", and these are the only three modes it can be in.
    state("move", ["idle", "attack", "move"]),
])


# --- what each state means -------------------------------------------------

# Idle: stand still for half a second, then attack.
@enemy.onStateEnter("idle")
def start_idle():

    @wait(0.5)
    def then_attack():
        enemy.enterState("attack")


@enemy.onStateEnter("attack")
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

    @wait(1)
    def then_move():
        enemy.enterState("move")


# Move: chase for two seconds, then go idle.
@enemy.onStateEnter("move")
def start_move():

    @wait(2)
    def then_idle():
        enemy.enterState("idle")


# This runs every frame, but ONLY while the state is "move".
@enemy.onStateUpdate("move")
def chase():
    enemy.moveTo(player.pos, 120)


# --- getting hit -----------------------------------------------------------

@player.onCollide("bullet")
def shot(bullet):
    bullet.destroy()
    addKaboom(player.pos)
    player.destroy()


@onKeyDown("left")
def move_left():
    player.move(-SPEED, 0)


@onKeyDown("right")
def move_right():
    player.move(SPEED, 0)


@onKeyDown("up")
def move_up():
    player.move(0, -SPEED)


@onKeyDown("down")
def move_down():
    player.move(0, SPEED)
```

**What each part does.**

`state(starting, [all_possible])` gives the object a mode. It starts in the first
one, and can only ever be in one of the listed modes.

`@obj.onStateEnter(name)` runs once, the moment the object enters that state.
`@obj.onStateUpdate(name)` runs every frame while it is in that state — think of
it as an `onUpdate` that only applies to one mode.

`.enterState(name)` switches modes. Notice that every state ends by scheduling a
switch to another one with `@wait(...)`, which is what makes the cycle turn:
move → idle → attack → move.

Compare `shot` above with what it would have to be as a single expression. Three
separate things happen — destroy the bullet, draw the explosion, destroy the
player — and a `lambda` can only hold one.

`player.exists()` checks the player hasn't already been destroyed. Without it,
the enemy would try to aim at something that isn't there.

`player.pos.sub(enemy.pos).unit()` is the direction from the enemy to the player:
subtract the positions to get the difference, then `.unit()` shrinks it to length
1 so it is a pure direction.

`move(direction, speed)` is a component that makes an object drift in a straight
line forever. `offscreen(destroy=True)` cleans it up once it leaves the screen —
without that, every bullet ever fired is still in memory.

`addKaboom(position)` plays Kaplay's explosion animation.

> **If you have seen the JavaScript version of this lesson**
>
> It used `async` and `await` inside `onStateEnter`, which needed explaining and
> apologising for. Python has no equivalent here, so instead each state schedules
> the next one with `@wait(seconds)`. Same behaviour, one less concept.

---

## Quick reference

Everything used in this guide.

### Starting up

| | |
|---|---|
| `kaplay(width=, height=, background=)` | start the engine, always first |
| `loadSprite(name, path)` | make a picture available |
| `loadSprite(name, [paths], anims={})` | build frames from several pictures |
| `loadSprite(name, path, sliceX=, anims={})` | cut a spritesheet into frames |
| `loadSpriteAtlas(path, {...})` | name many sprites inside one image |
| `loadSound(name, path)` | make a sound available |
| `setGravity(n)` / `setBackground(r, g, b)` | world settings |

### Making things

| | |
|---|---|
| `add([components])` | build a game object |
| `obj.add([components])` | build a child of that object |
| `obj.destroy()` | remove it |
| `get("tag")` | every object with that tag |
| `addLevel(layout, config)` | build a map out of characters |
| `addKaboom(pos)` | the explosion animation |

### Components

| | |
|---|---|
| `sprite(name)` | draw a picture — gives `.play()`, `.flipX`, `.curAnim()` |
| `text(str, size=, width=)` | draw words — gives `.text` |
| `rect(w, h, radius=)` / `circle(r)` | draw a shape |
| `pos(x, y)` | position — gives `.move()`, `.moveTo()`, `.pos` |
| `area()` | collision box — gives `.onCollide()`, `.onClick()`, `.isHovering()` |
| `body(isStatic=, mass=, jumpForce=)` | physics — gives `.jump()`, `.isGrounded()`, `.onGround()` |
| `state(start, [all])` | modes — gives `.onStateEnter()`, `.onStateUpdate()`, `.enterState()` |
| `anchor("center")` | which point `pos()` refers to |
| `scale(n)`, `color(r,g,b)`, `opacity(n)`, `outline(n)`, `z(n)` | appearance |
| `fixed()` | ignore the camera |
| `move(dir, speed)` | drift in a straight line |
| `offscreen(destroy=True)` | clean up when it leaves the screen |
| `tile(isObstacle=)` | occupies a square on a grid |
| `"a string"` | a tag |

### Events

Each one goes above a function, as `@onKeyDown("left")`. The ones with nothing to
configure — `@onUpdate`, `@onClick`, `@obj.onGround` — take no brackets.

| | |
|---|---|
| `@onUpdate` | every frame |
| `@onUpdate("tag")` | every frame, for each tagged object |
| `@onKeyDown` / `@onKeyPress` / `@onKeyRelease` `(key)` | held / pressed once / let go |
| `@onClick` | mouse clicked anywhere |
| `@obj.onClick` | that object clicked (needs `area()`) |
| `@obj.onCollide("tag")` | touched something tagged |
| `@obj.onCollideUpdate` / `@obj.onCollideEnd` | while touching / when it stops |
| `@obj.onGround` | landed on something (needs `body()`) |
| `@wait(seconds)` | once, after a delay |
| `@loop(seconds)` | over and over |

Every one of these also takes a function directly — `onKeyDown("left", walk)` —
which is what Kaplay's JavaScript examples translate to.

### Scenes

| | |
|---|---|
| `@scene("name")` | define one |
| `go("name", value)` | switch to it, optionally passing something |

### Useful values

| | |
|---|---|
| `width()`, `height()`, `center()` | the size and middle of the window |
| `dt()` | seconds since the last frame |
| `vec2(x, y)` | a position — has `.x`, `.y`, `.sub()`, `.unit()` |
| `rand(a, b)`, `randi(a, b)`, `choose(list)` | randomness |
| `mousePos()`, `toWorld(pos)` | on screen / in the world |
| `setCamPos(pos)`, `setCamScale(n)`, `shake(n)` | the camera |
| `play(name, loop=, paused=, volume=)` | play a sound |
| `debug.inspect = True` | show every collision box (or press **F1**) |

---

## When something doesn't work

**"has no attribute 'jump'"** — the object is missing the component that provides
it. `.jump()` and `.isGrounded()` come from `body()`; `.move()` from `pos()`;
`.onCollide()` from `area()`.

**A collision never fires** — one of the two objects has no `area()`. Turn on
`debug.inspect = True` and look at the boxes.

**Nothing appears at all** — you called `scene()` but never `go()`, or you loaded
a sprite but never added it.

**The sprite is invisible but the game runs** — check the path. It should look
like `"images/bean.png"` or `"dungeon/elf_m.png"`. In PyIDE it must be a file the
Sprites panel lists; on your own machine you need to be running from the folder
those live in. Either way the two packs are separate folders, and a dungeon
sprite is not in `images/`.

**Every frame is half one pose and half the next** — `sliceX` doesn't match the
spritesheet.

**The animation is stuck on one frame** — you are calling `.play()` every frame.
Guard it with `if obj.curAnim() != "run"`.

**The score never changes** — a function inside another function needs
`nonlocal score`, or `global score` if the score lives at the top level of the
file.

**An event does nothing, and you wrote it with `@`** — check whether it needed
brackets. `@onKeyDown("space")` has something to configure, so it takes them;
`@onUpdate` has nothing, so it doesn't. Writing `@onUpdate()` or `@onKeyDown`
without its key won't do what you meant.

**The keys do nothing** — click the picture once. In PyIDE, and in a web build,
the game only gets the keyboard once the canvas has focus. (A desktop window
takes focus by itself.)
