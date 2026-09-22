# kaypy

[![PyPI](https://img.shields.io/pypi/v/kaypy.svg)](https://pypi.org/project/kaypy/)
[![Python versions](https://img.shields.io/pypi/pyversions/kaypy.svg)](https://pypi.org/project/kaypy/)
[![License: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](https://github.com/sfranz2422/kaypy/blob/main/LICENSE)

**A real-Python game engine with [KAPLAY](https://kaplayjs.com)'s API — runs on your
machine, exports to the browser.**

Every name is KAPLAY's own name, in KAPLAY's own order, with KAPLAY's own
arguments: `add`, `sprite`, `onKeyDown`, `loadSpriteAtlas`, `isGrounded`. So
KAPLAY's documentation and every KAPLAY example on the internet still tells you
what to write — you just write it in Python.

Nothing is transpiled and nothing runs through a JavaScript bridge. It's
[pygame-ce](https://pyga.me) underneath, all the way down. The same file runs as
a desktop window with `python game.py`, or as a web page with `kaypy web
game.py`.

## Get running

```bash
pip install kaypy
kaypy new mygame
cd mygame
python game.py
```

Four commands and you have a game on screen — `kaypy new` writes a working
`game.py` along with the sprites to build on, so there is nothing to hunt for
and no paths to fix. Arrow keys to move, space to jump. Then open `game.py` and
start changing it.

It also fetches the three lesson sounds, which are 2.6 MB and live outside the
package so that every install doesn't pay for audio one lesson plays. If that
fetch fails — no internet, a school network that blocks GitHub — you get a
sentence saying so and a game that still runs, because the starter game plays
no sound. `kaypy sounds mygame` picks them up whenever you like.

Put the same file on the web with:

```bash
kaypy web game.py
```

which builds it into **one HTML file**. Double-click that file and the game
plays — no server, nothing installed, nothing unzipped. Upload the same single
file to itch.io, email it, or drop it on a school share.

**New here?** [`GUIDE.md`](https://github.com/sfranz2422/kaypy/blob/main/GUIDE.md) is a thirteen-lesson course that starts from
nothing and ends with a state-machine enemy AI — the Learn Kaplay lessons,
written for Python.

```python
from kaypy import *

kaplay(width=800, height=600, background=[141, 183, 255])

loadSprite("bean", "images/bean.png")

add([
    sprite("bean"),
    pos(120, 80),
    area(),
])
```

That's a complete, running game. Save it, run `python game.py`, and a window
opens. **There is no `run()` call** — exactly like the browser version, the
loop is already going the moment `kaplay()` executes.

---

## Quick overview

**Game objects are made of components.** You don't subclass anything; you hand
`add()` a list of parts, and the object is whatever those parts make it.

```python
player = add([
    sprite("bean"),
    pos(100, 200),
    area(),           # a collision box — without this, nothing can hit it
    body(),           # gravity, jumping, isGrounded()
    anchor("bot"),    # pos() now means "where its feet are"
    "player",         # a plain string is a tag
])
```

Each component adds its own methods to the object. `body()` is what gives you
`.jump()` and `.isGrounded()`; ask for them without it and you get a plain
`AttributeError` telling you so.

**Input is callbacks — put the event above the function it runs.**

```python
SPEED = 320

@onKeyDown("left")                       # every frame while held
def go_left():
    player.move(-SPEED, 0)


@onKeyPress("space")                     # once, when the key goes down
def jump():
    if player.isGrounded():
        player.jump(1000)
```

Every event also takes a function directly, which is shorter when the handler
is one short line and nothing else:

```python
onKeyDown("right", lambda: player.move(SPEED, 0))
```

Both forms do exactly the same thing, so use whichever reads better. The
decorator is the one to reach for first, because a lambda can only hold a
*single expression* and the workarounds get ugly fast: as a lambda, the jump
above has to be written
`lambda: player.jump(1000) if player.isGrounded() else None` — where the
`else None` does nothing at all and is only there to satisfy Python — and a
handler that assigns something has to reach for
`lambda: setattr(player, "pos", spawn)`, because a lambda cannot contain `=`.
As a decorator both are just ordinary indented code. Named handlers also show
up in error messages as `jump` rather than `<lambda>`.

**Collisions are events, addressed by tag.**

```python
@player.onCollide("danger")
def died(spike):
    player.pos = level.tile2Pos(2, 5)
    go("gameover")


player.onCollide("coin", lambda coin: coin.destroy())
```

Only objects with `area()` collide at all. An object with `area()` *and*
`body()` is solid; one with `area()` alone is a trigger you pass straight
through — that's how a coin can be picked up while a wall stops you.

**Turning, and going the way you point.** `rotate()` gives an object an
`angle`; `Vec2.fromAngle()` turns that angle back into a direction, which is
what "thrust forward" means once a thing can face anywhere.

```python
ship = add([sprite("ship"), pos(center()), anchor("center"), rotate(0)])
ship.vel = vec2(0, 0)


@onKeyDown("left")
def turn_left():
    ship.rotateBy(-200 * dt())


@onKeyDown("right")
def turn_right():
    ship.rotateBy(200 * dt())


@onKeyDown("up")
def thrust():
    ship.vel = ship.vel + Vec2.fromAngle(ship.angle) * 320 * dt()
```

That last one is the case the decorator exists for: `thrust` *assigns*, and a
lambda cannot contain `=`, so as a one-liner it would have to be
`lambda: setattr(ship, "vel", ...)`.

Rotation is about the anchor, so `anchor("center")` spins on the spot and the
default top-left corner swings around it. The **collision box does not turn**
— it stays the upright rectangle, which is what Kaplay does and what keeps a
spinning asteroid's hitbox from growing and shrinking as it goes round.

`examples/asteroids.py` is the whole thing: turning, thrust, momentum,
screen-wrap and splitting rocks.

**The mouse does more than click.** `onClick` tells you *that* someone
clicked. For aiming, dragging or holding, you need to know which button and
whether it is down right now.

```python
@onMousePress("left")
def shoot():
    heading = (mousePos() - player.pos).unit()
    add([sprite("bullet"), pos(player.pos), move(heading, 500), lifespan(2)])

@onUpdate
def charge():
    if isMouseDown("left"):          # held, not just pressed
        power = min(power + dt(), 1)
```

**Drawing that is not a game object.** A health bar, an aim line, a grid — a
mark on the screen for one frame, not a thing in the world. Those go in
`onDraw`, and the draw functions only work there.

```python
@onDraw
def hud():
    # fixed=True ignores the camera, which is what a HUD wants
    drawRect(pos=vec2(20, 20), width=200, height=16, color=rgb(60, 0, 0),
             fixed=True)
    drawRect(pos=vec2(20, 20), width=20 * player.hp, height=16,
             color=rgb(220, 40, 40), fixed=True)
    drawLine(p1=player.pos, p2=mousePos(), width=2, color=rgb(255, 255, 0))
```

**Hit points, and something to do when they run out.**

```python
enemy = add([sprite("ogre"), pos(300, 200), area(), health(3), "enemy"])

@enemy.onDeath
def slain():
    addKaboom(enemy.pos)
    enemy.destroy()
```

`enemy.hp = 3` does the same until the third place that takes a point off,
because now three lines have to remember to check for zero — and the one that
forgets is the enemy that cannot be killed. `hurt()` is one place, and death is
one event that fires exactly once however many things land in the same frame.

**A high score that is still there tomorrow.**

```python
best = getData("best_score", 0)

@player.onCollide("spike")
def died():
    if score > best:
        setData("best_score", score)
    go("gameover", score)
```

On your machine that is a `kaypy-data.json` file beside the game, which you
can open and read — and delete, to start over. In a browser it is the page's
own storage. If saving is not possible at all, the game says so once and
carries on without it.

**Gravity needs a world to fall in.**

```python
setGravity(2400)

add([                     # the floor
    rect(width(), 40),
    pos(0, 560),
    area(),
    body(isStatic=True),  # solid, and nothing can push it
])
```

**Moving something smoothly is a tween.** You say where it starts, where it
ends, how long it takes, and what to do with each value along the way.

```python
box = add([rect(60, 60), pos(100, 300), opacity(1)])


def move_box(x):
    box.pos.x = x


tween(100, 600, 0.5, move_box, easings.easeOutBounce)
tween(1.0, 0.0, 1.0, lambda a: setattr(box, "opacity", a)).then(
    lambda: box.destroy())
```

Numbers, `vec2` positions and colour tuples all tween. The fifth argument is
the **easing** — the shape of the motion — and without one everything travels
at a flat, robotic pace. There are thirty-one, named `easeIn`, `easeOut` and
`easeInOut` for each of Sine, Quad, Cubic, Quart, Quint, Expo, Circ, Back,
Elastic and Bounce, plus `easings.linear` for none at all. Any function from
0–1 to 0–1 works too.

Unlike the events, `tween` is not a decorator: the function it takes is a
setter that receives every value along the way, not a handler that runs once.

**Whole levels are drawn as pictures made of characters.**

```python
level = addLevel([
    "  $    $  ",
    "          ",
    "@   ^^    ",
    "==========",
], {
    "tileWidth": 64,
    "tileHeight": 64,
    "tiles": {
        "=": lambda: [sprite("grass"), area(), body(isStatic=True)],
        "$": lambda: [sprite("coin"), area(), "coin"],
        "^": lambda: [sprite("spike"), area(), "danger"],
        "@": lambda: [sprite("bean"), area(), body(), anchor("bot"), "player"],
    },
})

player = level.get("player")[0]
```

Those lambdas are not event handlers — each one is a recipe that gets called
every time that character appears, to build a fresh list of components. A
lambda returning a list is exactly the right shape for that, so they stay
lambdas.

**Scenes are named screens you jump between.**

```python
@scene("game")
def build_game():
    build_the_level()


@scene("gameover")
def show_gameover(score):
    show_score(score)


go("game")                 # start here
# ...later, from anywhere:
go("gameover", player_score)
```

---

## Installing

```bash
pip install kaypy
```

Python 3.10 or newer, and `pygame-ce` is the only dependency. There is nothing
else to install for the web export — it used to need `pygbag` and an `ffmpeg`
to convert sounds, and needs neither now.

`pip install kaypy` gives you two things: the `kaypy` package to import, and a
`kaypy` command with three subcommands.

| Command | What it does |
|---------|--------------|
| `kaypy new mygame` | Make a folder with a working game and the lesson sprites |
| `kaypy sounds mygame` | Fetch the lesson sounds into a folder that hasn't got them |
| `kaypy web game.py` | Build that game into one playable HTML file |

**Working from a clone instead?** `pip install -e .` from the project root, and
use `python webbuild.py game.py` wherever this README says `kaypy web game.py` —
they run the same code.

---

## Putting a game on the web

```bash
kaypy web game.py          # or: python webbuild.py game.py, from a clone
```

One command, one file:

```
Built game.py as one file:
    web_build/game.html
    412 KB, including 3 assets
```

Double-click it and it plays. It reads your script to find the images and
sounds it loads and carries those, and only those, inside the file — along
with the engine and your program. There is nothing beside it to keep together,
nothing to zip, and no server to start.

To publish on itch.io: upload that one file, set **Kind of project** to
*HTML*, and tick *This file will be played in the browser*. Their own
instructions cover it — *"For simple projects that are self contained in a
single `.html` file, you directly upload the file without zipping it."*

**Your program goes in unchanged.** kaypy opens sprites as ordinary files, and
the page gives it a filesystem to open them from, so `loadSprite("bean",
"images/bean.png")` means the same thing in a built game as it does on your
desktop. Open the built file in a text editor and your own code is in there,
as you wrote it.

**The one thing it fetches** is Python itself — Pyodide and pygame-ce, from a
CDN, on the first run. So a built game wants an internet connection the first
time it is opened and takes a few seconds to start; the browser caches both
afterwards. Embedding them would make every game tens of megabytes.

| Flag | Effect |
|------|--------|
| `--serve` | also start a local server, for testing on a phone or another machine |
| `--port 9000` | which port `--serve` uses (default 8000) |
| `--title "..."` | the browser tab's title (default: the script's name) |
| `--out FILE` | write somewhere other than `web_build/<name>.html` |
| `--assets a b` | copy these too, for paths your script builds at runtime |

Building needs no internet at all — it is your own machine, your own files,
and the engine already installed. Only *playing* a built game fetches
anything, and only Python itself, once.

Your game file doesn't change between the two targets — no `if` on the
platform, no separate build of your code. The same `game.py` that opens a window
with `python game.py` is the one that becomes the web page.

---

## API

### Starting up

| Call | What it does |
|------|--------------|
| `kaplay(width, height, background)` | Starts the engine. Must come first. |
| `setGravity(n)` | Pixels per second squared. `0` (the default) means no gravity. |
| `setBackground(r, g, b)` | Change the background colour later. |

### Loading

| Call | What it does |
|------|--------------|
| `loadSprite(name, path)` | One image. |
| `loadSprite(name, [path, path, ...], anims={...})` | One image per frame. |
| `loadSprite(name, path, sliceX=8, anims={...})` | One strip cut into frames. |
| `loadSpriteAtlas(path, {name: {x, y, width, height, sliceX, anims}})` | Cut many named sprites out of one sheet. |
| `loadSound(name, path)` | A `.wav` or `.ogg`. |

An `anims` entry looks like `{"run": {"from": 0, "to": 8, "speed": 12, "loop": True}}`.

### Making things

| Call | What it does |
|------|--------------|
| `add([comp, comp, ...])` | Build a game object. Returns it. |
| `get(tag)` | Every live object carrying that tag. |
| `addLevel(layout, config)` | Build a whole map from a list of strings. |
| `addKaboom(pos, scale=1)` | The explosion, for when something should feel good. |
| `obj.add([...])` | A child object, positioned relative to its parent. |

### Components

| Component | What it gives the object |
|-----------|--------------------------|
| `pos(x, y)` | A position, plus `.move(dx, dy)` and `.moveTo(target, speed)`. |
| `sprite(name, anim=None, frame=None)` | An image. Adds `.play(anim)`, `.curAnim()`, `.flipX`, `.flipY`. |
| `rect(w, h, radius=0)` | A drawn rectangle. |
| `circle(radius)` | A drawn circle. |
| `text(str, size=22, width=None)` | Drawn text. |
| `area()` | A collision box. Required on **both** objects for any collision. Adds `.isHovering()`. |
| `body(isStatic=False, mass=1, jumpForce=800)` | Physics. Adds `.jump(force)`, `.isGrounded()`, `.onGround(fn)`, `.vel`. |
| `anchor(name)` | What `pos()` points at: `"topleft"` (default), `"top"`, `"center"`, `"bot"`, `"botright"`, … |
| `rotate(degrees)` | Turn it, clockwise, about its anchor. Adds `.angle`, `.rotateBy(n)`, `.rotateTo(n)`. |
| `scale(x, y=None)` | Resize. Affects the collision box too. |
| `color(r, g, b)` | Tint. |
| `opacity(n)` | `0.0`–`1.0`. |
| `outline(width, color)` | An outline on shapes. |
| `z(n)` | Draw order; higher draws on top. |
| `fixed()` | Ignore the camera — for HUD and UI. |
| `move(direction, speed)` | Drift in a direction forever. |
| `offscreen(destroy=False, distance=64)` | Notice (or clean up) objects that leave the view. |
| `tile(isObstacle=False)` | Mark a level tile. |
| `health(hp, maxHP=None)`                      | Hit points. Adds `.hp`, `.hurt(n)`, `.heal(n)`, `.onDeath(fn)`, `.isAlive()`.               |
| `lifespan(seconds, fade=0)`                   | Destroy itself after a while. `fade` needs an `opacity()`.                                  |
| `state(start, states)` | A state machine. Adds `.enterState(n)`, `.onStateEnter(n, fn)`, `.onStateUpdate(n, fn)`. |
| `"any string"` | A tag. Objects are found and collided-with by tag. |

### Events

| Call | When it fires |
|------|---------------|
| `onUpdate(fn)` | Every frame. |
| `onUpdate(tag, fn)` | Every frame, once per object with that tag. |
| `onKeyDown(key, fn)` | Every frame the key is held. |
| `onKeyPress(key, fn)` | Once, when the key goes down. |
| `onKeyRelease(key, fn)` | Once, when it comes back up. |
| `onClick(fn)` | Any left click. `obj.onClick(fn)` for clicks on that object. |
| `onMousePress(button, fn)` | Once, when a mouse button goes down. |
| `onMouseRelease(button, fn)` | Once, when it comes back up. |
| `onMouseDown(button, fn)` | Every frame it is held. |
| `onMouseMove(fn)` | Whenever the mouse moves. |
| `onDraw(fn)` | Draw straight to the screen, after the objects. |
| `obj.onCollide(tag, fn)` | Once, when a touch begins. |
| `onCollide(tagA, tagB, fn)` | Once, when anything tagged A touches anything tagged B. |
| `obj.onCollideUpdate(tag, fn)` | Every frame the two stay touching. |
| `obj.onCollideEnd(tag, fn)` | Once, when they come apart. |
| `wait(seconds, fn)` | Once, later. |
| `loop(seconds, fn)` | Over and over, forever. |

Key names are `"left"`, `"right"`, `"up"`, `"down"`, `"space"`, `"enter"`,
`"escape"`, `"tab"`, `"shift"`, `"ctrl"`, `"alt"`, `"backspace"`, plus `"a"`–`"z"`
and `"0"`–`"9"`.

**Every event above takes a function, or sits above one as a decorator** —
including `wait`, `loop`, `scene`, `obj.onGround` and the `state()` handlers:

```python
onKeyPress("space", jump)     # hand it a function
@onKeyPress("space")          # or put it above one
def jump(): ...

@onUpdate                     # no argument, so no parentheses
def every_frame(): ...

@onUpdate("enemy")            # once per object with that tag
def chase(enemy): ...

@loop(1.0)
def spawn_one(): ...

@scene("game")
def build_game(): ...
```

### Values and helpers

| Call | Gives you |
|------|-----------|
| `width()`, `height()`, `center()` | The size of the screen, and its middle. |
| `dt()` | Seconds since the last frame. |
| `vec2(x, y)` | A vector. Supports `+`, `-`, `*`, `.len()`, `.unit()`, `.dist()`. |
| `Vec2.fromAngle(degrees)` | A unit vector pointing that way — which direction a rotated object faces. |
| `rand(a, b)`, `randi(a, b)`, `choose(seq)`, `chance(p)` | Randomness. |
| `time()` | Seconds since `kaplay()` — the game's clock, so it pauses when the game does. |
| `lerp(a, b, t)`, `clamp(v, lo, hi)`, `wave(lo, hi, t)` | Blend, bound, swing. |
| `rgb(r, g, b)` | A colour. Takes `rgb(255, 128, 0)`, `rgb("#ff8800")` or `rgb(200)` for a grey. |
| `destroy(obj)`, `destroyAll(tag)` | Remove one, or every object with a tag. |
| `isKeyDown(key)` | Ask instead of being told — the polling form of `onKeyDown`. |
| `deg2rad(d)`, `rad2deg(r)` | Angles. |
| `mousePos()`, `toWorld(pos)` | Where the mouse is, on screen and in the world. |
| `isMouseDown(button)`, `isMousePressed(button)`, `isMouseReleased(button)` | Ask about a mouse button instead of being told. `"left"` if you leave it out. |
| `isMouseMoved()`, `mouseDeltaPos()` | Did the mouse move this frame, and how far. |
| `drawRect`, `drawCircle`, `drawLine`, `drawLines`, `drawText`, `drawSprite` | Draw for one frame, inside `onDraw`. `fixed=True` for a HUD that ignores the camera. |
| `setData(key, value)`, `getData(key, default)` | Remember something between runs — a high score. A file beside the game; localStorage on the web. |
| `setCamPos(pos)`, `setCamScale(n)`, `shake(n)` | The camera. |
| `play(name, loop=False, volume=1.0)` | Play a sound. Returns a handle with settable `.paused` and `.volume`. |
| `tween(start, end, seconds, setter, ease)` | Change a value smoothly. Returns a handle with `.then()`, `.cancel()`, `.finish()`, `.paused`. |
| `easings.easeOutBounce` | One of thirty-one curves — the shape of a tween's motion. |
| `scene(name, fn)`, `go(name, *args)` | Define and switch screens. |
| `debug.inspect = True` | Draw every collision box. **F1** toggles it while running. |

### Object methods

Every object has `.destroy()`, `.exists()`, `.is_(tag)`, `.pos`, and `.tags`,
plus whatever its components added.

---

## Examples

All 13 lessons of [the guide](https://github.com/sfranz2422/kaypy/blob/main/GUIDE.md)
live in `examples/` **in this repository** — they aren't part of the pip
package, so clone the repo if you want to run them as they're written:

| # | Lesson | Shows |
|---|--------|-------|
| 1 | `lesson1_adding_object.py` | `kaplay()`, `loadSprite`, `add` |
| 2 | `lesson2_player_movement.py` | `onKeyDown`, `.move()` |
| 3 | `lesson3_collision.py` | `area()` vs `body()`, `onCollide` |
| 5 | `lesson5_gravity.py` | `setGravity`, `isStatic`, jumping |
| 6 | `lesson6_sprite_animation.py` | frame lists, `sliceX` strips, `anims` |
| 7 | `lesson7_scenes.py` | `scene` / `go`, passing data between screens |
| 8 | `lesson8_audio_buttons.py` | `loadSound`, `play()`, clickable objects, children |
| 9 | `lesson9_timer_loop.py` | `wait`, `loop` |
| 10 | `lesson10_levels.py` | `addLevel`, tile maps |
| 11 | `lesson11_camera.py` | `setCamPos`, `fixed()` HUD |
| 12 | `lesson12_sprite_atlas.py` | `loadSpriteAtlas` |
| 13 | `lesson13_state_ai.py` | `state()` machines for enemy AI |
| — | `asteroids.py` | `rotate()`, `Vec2.fromAngle()`, momentum, screen-wrap |

```bash
git clone https://github.com/sfranz2422/kaypy
cd kaypy/examples
python lesson10_levels.py
```

If you installed from pip instead, `kaypy new mygame` gives you every asset
those lessons use — sprites from the package, sounds fetched on the spot — so
you can follow the guide by typing its code into your own `game.py`.

---

## Troubleshooting

**The sprite is invisible but the game runs.** Almost always a bad path.
`loadSprite` raises on a missing file, so check the name you drew with matches
the name you loaded.

**Nothing collides.** Both objects need `area()`. That's the single most common
cause.

**It falls through the floor.** The floor needs `area()` *and*
`body(isStatic=True)`. With only `area()` it's a trigger, not a wall.

**Every frame is half one pose and half the next.** `sliceX` doesn't match the
number of frames in the strip.

**The animation is stuck on frame 0.** `.play()` restarts from the first frame,
so calling it every frame inside `onKeyDown` never lets it advance. Only call
it when the animation should actually change.

**`AttributeError: 'GameObj' object has no attribute 'jump'.`** That object
doesn't have `body()`.

Press **F1** while a game is running to draw every collision box.

---

## Assets

`examples/images/`, `examples/dungeon/`, `examples/dungeon.png` and
`examples/sounds/` hold real sprites and sounds vendored from the KAPLAY
project (MIT) and 0x72's DungeonTileset II (CC0). See `examples/CREDITS.md` for
the full licence text and attribution. Only the files the lessons actually use
are included, not the full packs.

`examples/gen_assets.py` fills in placeholder shapes for any sprite that isn't
there yet, and never overwrites a real file.

---

## How it works, and what's rough

[`DEVELOPING.md`](https://github.com/sfranz2422/kaypy/blob/main/DEVELOPING.md) has the architecture, the test suite, the
known limitations, and the war stories — including the three real physics bugs
and the pygbag incompatibilities that the web export had to work around before
it stopped using pygbag.

## Credits

**kaypy is an independent project.** It is not affiliated with, endorsed by, or
produced by the KAPLAY team. It follows KAPLAY's published API on purpose, so
that KAPLAY's documentation and examples tell you what to write — but it is a
separate implementation in Python, and bugs in it are mine, not theirs.

KAPLAY's API design, and its documentation, which this follows deliberately and
closely. Built on [pygame-ce](https://pyga.me); the web export runs on
[Pyodide](https://pyodide.org). It was built on
[pygbag](https://github.com/pygame-web/pygbag) first, which is what made a
browser build possible at all while this was finding its feet.

The bundled sprites and sounds come from KAPLAY (MIT) and 0x72's
DungeonTileset II (CC0). Full terms travel with the files, in
`examples/CREDITS.md`.
