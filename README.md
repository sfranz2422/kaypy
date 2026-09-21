# kaypy

[![PyPI](https://img.shields.io/pypi/v/kaypy.svg)](https://pypi.org/project/kaypy/)
[![Python versions](https://img.shields.io/pypi/pyversions/kaypy.svg)](https://pypi.org/project/kaypy/)
[![License: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

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
pip install "kaypy[web]"
kaypy web game.py
```

which builds it to WebAssembly and serves it at a URL you can open. The finished
folder is a plain static site — upload it to itch.io, GitHub Pages or anywhere
else.

**New here?** [`GUIDE.md`](https://github.com/sfranz2422/kaypy/blob/main/GUIDE.md) is a thirteen-lesson course that starts from
nothing and ends with a state-machine enemy AI — the Learn Kaplay lessons,
written for Python.

```python
from kaplay import *

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

**Input is callbacks — write them whichever way reads better.**

```python
SPEED = 320

onKeyDown("left",  lambda: player.move(-SPEED, 0))   # every frame while held
onKeyDown("right", lambda: player.move(SPEED, 0))
```

A lambda is fine for one short line. The moment a handler needs more than
that, put the event above a normal function instead — same event, same
result:

```python
@onKeyPress("space")
def jump():
    if player.isGrounded():
        player.jump(1000)
```

Every event works both ways. The decorator form is worth knowing because a
lambda can only hold a *single expression*, and the workarounds for that get
ugly fast: as a lambda, the jump above has to be written
`lambda: player.jump(1000) if player.isGrounded() else None` — where the
`else None` does nothing at all and is only there to satisfy Python — and a
handler that assigns something has to reach for
`lambda: setattr(player, "pos", spawn)` because a lambda can't contain `=`.
As a decorator both are just ordinary indented code. Named handlers also show
up in error messages as `jump` rather than `<lambda>`.

**Collisions are events, addressed by tag.**

```python
player.onCollide("coin", lambda coin: coin.destroy())

@player.onCollide("danger")
def died(spike):
    player.pos = level.tile2Pos(2, 5)
    go("gameover")
```

Only objects with `area()` collide at all. An object with `area()` *and*
`body()` is solid; one with `area()` alone is a trigger you pass straight
through — that's how a coin can be picked up while a wall stops you.

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

**Scenes are named screens you jump between.**

```python
scene("game", lambda: build_the_level())
scene("gameover", lambda score: show_score(score))

go("game")                 # start here
# ...later, from anywhere:
go("gameover", player_score)
```

---

## Installing

```bash
pip install kaypy            # the engine
pip install "kaypy[web]"     # ...and the web exporter
```

Python 3.10 or newer. `pygame-ce` is the only runtime dependency; the `[web]`
extra adds `pygbag` and a bundled `ffmpeg` used to convert sounds for the
browser. The quotes matter on the second one — zsh reads a bare `[web]` as a
glob pattern and will tell you there are no matches.

`pip install kaypy` gives you two things: the `kaplay` package to import, and a
`kaypy` command with two subcommands.

| Command | What it does |
|---------|--------------|
| `kaypy new mygame` | Make a folder with a working game and the lesson sprites |
| `kaypy sounds mygame` | Fetch the lesson sounds into a folder that hasn't got them |
| `kaypy web game.py` | Build that game for the browser and serve it |

**Working from a clone instead?** `pip install -e .` from the project root, and
use `python webbuild.py game.py` wherever this README says `kaypy web game.py` —
they run the same code.

---

## Putting a game on the web

```bash
kaypy web game.py          # or: python webbuild.py game.py, from a clone
```

One command. It reads your script to find the images and sounds it loads,
packages them with the engine into WebAssembly, then serves the result and
prints a URL to open. Ctrl-C stops the server; the finished site stays in
`web_build/<name>/build/web/` and can be uploaded as-is to itch.io or any
static host.

**Open the URL it prints, exactly as printed — `127.0.0.1`, not `localhost`.**
They are the same server, but pygbag treats a page served from
`http://localhost:8…` as having a local mirror of its package CDN, and fetches
the pygame WebAssembly wheel from your machine instead of from
pygame-web.github.io. There is no such mirror, so that one file 404s and the
game sits at "Loading, please wait ..." for ever — after everything else,
including the whole Python interpreter, has loaded perfectly. Nothing is wrong
with the build. `kaplay/webbuild.py`'s `serve()` has the details.

| Flag | Effect |
|------|--------|
| `--no-serve` | build, but don't start the local server |
| `--no-build` | only assemble the folder |
| `--port 9000` | serve on a different port (default 8000) |
| `--assets a b` | copy these too, for paths your script builds at runtime |
| `--out DIR` | write somewhere other than `web_build/<script name>` |

The first web build downloads a WebAssembly Python runtime, so it needs
ordinary internet access. After that it's local.

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
| `scale(x, y=None)` | Resize. Affects the collision box too. |
| `color(r, g, b)` | Tint. |
| `opacity(n)` | `0.0`–`1.0`. |
| `outline(width, color)` | An outline on shapes. |
| `z(n)` | Draw order; higher draws on top. |
| `fixed()` | Ignore the camera — for HUD and UI. |
| `move(direction, speed)` | Drift in a direction forever. |
| `offscreen(destroy=False, distance=64)` | Notice (or clean up) objects that leave the view. |
| `tile(isObstacle=False)` | Mark a level tile. |
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
| `onClick(fn)` | Any click. `obj.onClick(fn)` for clicks on that object. |
| `obj.onCollide(tag, fn)` | Once, when a touch begins. |
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
| `vec2(x, y)` | A vector. Supports `+`, `-`, `*`, `.len()`, `.unit()`. |
| `rand(a, b)`, `randi(a, b)`, `choose(seq)` | Randomness. |
| `mousePos()`, `toWorld(pos)` | Where the mouse is, on screen and in the world. |
| `setCamPos(pos)`, `setCamScale(n)`, `shake(n)` | The camera. |
| `play(name, loop=False, volume=1.0)` | Play a sound. Returns a handle with settable `.paused` and `.volume`. |
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
and the four pygbag incompatibilities that had to be fixed to make the web
export work at all.

## Credits

KAPLAY's API design, and its documentation, which this follows deliberately and
closely. Built on [pygame-ce](https://pyga.me); the web export rides on
[pygbag](https://github.com/pygame-web/pygbag).
