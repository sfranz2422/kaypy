# Changelog

## 0.10.0

**A d-pad on the screen, for playing with a thumb.**

```python
kaypy(width=800, height=600, joystick=True)
```

That is the whole change to a game. The overlay pretends to be the keyboard:
the pad holds the arrow keys and the two buttons send `space` and `z`, so
every game already written — every lesson in the guide, the starter, whatever
a class wrote last week — is playable on a phone without a line of it
changing. Pass a list to choose what the buttons send:
`joystick=["space", "x"]`.

- Every way a game can ask about a key agrees: `onKeyDown`, `isKeyDown`,
  `onKeyPress` and `onKeyRelease` all see a thumb exactly as they see a
  finger on the keyboard.
- **Fingers are tracked one by one.** A platformer needs run and jump at the
  same time, and with a single pointer, pressing jump releases right — so
  the games this exists for would have been the ones it broke.
- Diagonals hold two directions at once, and the middle of the pad holds
  nothing, so a resting thumb is not "left".
- The mouse counts as a finger, so it can be tried on a laptop. A control
  scheme that can only be tested by picking up a phone is one that goes
  untested.
- A panel lets go of everything, or the player answers a question and comes
  back to a character that has been walking into a wall.

It is drawn on the canvas rather than built out of HTML — unlike a panel,
there is nothing to select, read aloud or zoom, and drawing it means the same
code works in a browser and in a window on a desktop.

## 0.9.0

**Pause a game, and ask the player something.**

```python
@player.onCollide("door")
def at_the_door(d):
    @ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
    def checked(correct):
        if correct:
            d.destroy()
```

- `pause()`, `resume()`, `isPaused()`. Timers, gravity, collisions and every
  `onUpdate` stop; the frame is still drawn, so the game sits there behind
  whatever is over it. Key handlers keep running — a pause menu has to hear
  the key that un-pauses it — and that is safe because `dt()` is zero, so a
  held arrow key fires its handler and moves the player nowhere. `time()`
  stops too, so a `wave()` or a tween resumes where it stopped instead of
  jumping forward.
- `say()` and `ask()`. Multiple choice, answered by clicking or by pressing
  the number beside it; or a box to type in. `answer=` gets your function
  True or False; without it, your function is given what was picked or typed.
  Marking ignores capitals and stray spaces.
- `isShowing()` and `close()`.
- A panel owns the input while it is up, so a click meant for an answer does
  not also fire an `onClick` in the game behind it. That is keyed to the
  panel and not to being paused, so a hand-rolled `pause()` menu still works.

**The content is text, choices and links — never HTML.** In a browser the
panel is real elements over the canvas, so the text can be selected, a link
is a real link, and the box is a real input with a phone keyboard and paste.
On a desktop kaypy draws it and a link opens the system browser. An
HTML-shaped API would have been lovely in one of those places and impossible
in the other, and `python game.py` and the web build running the same file is
the whole point of kaypy.

**They call you back rather than returning an answer.** In a browser Python
runs on the page's own thread, so waiting for a click would stop the page —
including the click being waited for. The tab would hang, not pause. On a
desktop the same line would work, which is the worst kind of difference: one
that only appears in front of a class.

Fixed while building it: typing into a panel's box did nothing on the web.
SDL, under Emscripten, puts key listeners on `document` and calls
`preventDefault()` on them so game keys do not scroll the page, and it never
removes them. A cancelled `keydown` still fires — which is why the number-key
shortcut worked — but inserting a character into an `<input>` is the default
action, and that is what was being cancelled. The panel now takes keys at
`window` in the capture phase, which runs before `document`, and stops them
propagating so SDL never sees them.

## 0.8.0

**`kaplay()` is gone.** 0.7.0 kept it as an alias for anyone who had already
written it. Nobody had — the engine has not been in front of a class yet —
and keeping it meant both exporters carrying two names for one function for
ever. `kaypy(width=, height=, background=)` is the only way to start a game.

If you have a file from 0.7.0 or earlier that says `kaplay(...)`, change that
one line. Nothing else moves.

- `webbuild.INIT_NAMES` stays, with one name in it, and so does the test that
  compares it against what the package exports. The failure it guards is
  silent: an unrecognised init call falls back to 800×600 and the build
  reports success, so the wrong canvas only turns up on itch.io. Removing the
  alias tripped that guard in PyIDE's export test, which is what it is for.

**Fixed: `KAYPY_TEST_MAX_FRAMES=0` meant *unlimited*, not zero frames.**
`int(os.environ.get(..., "0")) or None` — `int("0")` is falsy, so `or None`
replaced it, and a second guard read `if max_frames` the same way. Setting it
to 0 to hold a game still produced a loop that never returned, at interpreter
exit, with no output and no traceback. Unset still means no limit, because a
real game runs until it is closed. `tests/test_max_frames.py` pins down all
three cases.

## 0.7.0

**The engine starts with `kaypy()`.** The first line of every game said
`kaplay(...)`, directly under `from kaypy import *` — two names for one
project, on two adjacent lines, in the file every beginner opens first.

- `kaypy(width=, height=, background=)` is the documented name.
- `kaplay(...)` is an alias and keeps working. Nothing written before this
  needs changing: same function, same arguments, same behaviour.
- Both exporters read the window size off that call by name, so both were
  taught the new one. A game built with `kaypy web`, or downloaded from
  PyIDE, opens at the size it asks for either way — that failure mode was
  silent (it fell back to 800×600 and reported success), so it is now
  covered by a test in each project that compares the two lists of names
  rather than trusting them to be kept in step.

## 0.6.0

**The mouse does more than click.** `onClick` answered "somebody clicked" and
nothing else — not which button, not whether one is being held, not that the
mouse moved. Aiming at the cursor, dragging a piece, hold-to-charge and
drawing all needed one of those and had no way to ask.

- `onMousePress`, `onMouseRelease`, `onMouseDown`, `onMouseMove`
- `isMouseDown`, `isMousePressed`, `isMouseReleased`, `isMouseMoved`,
  `mouseDeltaPos`
- Buttons are named — `"left"`, `"right"`, `"middle"` — as in KAPLAY, and
  default to the left one. pygame numbers them 1, 2, 3 with middle in the
  middle, which is not the order anyone guesses.
- `onClick` is unchanged and still means the left button.

**`onDraw`, and drawing that is not a game object.** A health bar, an aim
line, a grid, a radius — marks on the screen for one frame, not things in the
world. Making each one a game object works and teaches the wrong lesson about
what a game object is for.

- `drawRect`, `drawCircle`, `drawLine`, `drawLines`, `drawText`, `drawSprite`
- They draw in world space by default and move with the camera; `fixed=True`
  for a HUD, the same distinction `fixed()` makes for objects.
- Called outside `onDraw` they **raise** and say what to write instead. A
  drawing that silently never appears is close to undebuggable for a beginner.

**`health()` and `lifespan()`.**

- `health(hp)` adds `.hp`, `.hurt()`, `.heal()`, `.onHurt()`, `.onHeal()`,
  `.onDeath()` and `.isAlive()`. `onDeath` fires **exactly once**, however many
  things land in the same frame — a death handler that runs twice drops two
  coins and scores twice, and looks like generosity until someone notices.
  It does not destroy the object, so it can play an animation first.
- `lifespan(seconds, fade=0)` destroys the object when its time is up, fading
  out first if asked. Replaces `wait(2, lambda: b.destroy())`, and belongs to
  the bullet rather than to a timer somewhere else holding it alive.

**`setData()` and `getData()` — a high score that is still there tomorrow.**
A `kaypy-data.json` file beside the game on a desktop, deliberately plain so a
student can open it and delete it; the page's localStorage on the web.

- A save that cannot be written returns False, says so once, and lets the game
  carry on. A locked-down school account is not a reason to crash.
- It never pretends: `getData()` after a failed `setData()` returns what is
  really stored.
- A corrupt file is ignored rather than fatal, and repairs itself on the next
  save.
- Only things that can be written down — numbers, text, True/False, None,
  lists and dicts of those. Saving a game object is refused, by name, with
  what to do instead.

## 0.5.0

**`from kaypy import *`.** The package was called `kaplay` — the name of the
JavaScript library whose API it follows — which put a project that says it is
not affiliated with KAPLAY in the position of telling every student to type
that project's name on line one.

`kaplay(width=800)` is unchanged: that is KAPLAY's own function name, and
keeping it is what makes their documentation translate line for line. Only the
module moved.

There is no compatibility alias, deliberately. `from kaplay import *` now
fails — and in a browser IDE that still recognises the old spelling, it fails
with a sentence naming the one line to change.

## 0.4.0

**`kaypy web` builds one file.** It used to build a folder — an `index.html`
that fetched a `.apk` archive at run time, plus a tarball and a favicon, by way
of pygbag. That works behind a web server and not at all when you double-click
the `index.html`, because a `file://` page may not read the file next to it. So
you could build your own game and not open it.

```bash
kaypy web game.py
# -> web_build/game.html    412 KB, including 3 assets
```

Double-click it and it plays. Upload that one file to itch.io — no zip, no
folder to keep together.

- **Your program is carried byte for byte.** The page writes the engine and
  the assets into Pyodide's in-memory filesystem before running anything, so
  `loadSprite("bean", "images/bean.png")` opens a real file at the path you
  wrote. Nothing is rewritten to point at inlined data. Open a built game in a
  text editor and your own code is in there as you typed it.
- **Two dependencies went away**, and with them the separate install step the
  web export used to need. `pip install kaypy` is now the whole thing: no
  pygbag, and no ffmpeg. The ffmpeg was there only because pygbag's build step
  rejects `.wav` files outright, so every sound had to be converted to `.ogg`
  first. Plain PCM `.wav` — which is what the lesson sounds are, and what most
  tools write — plays in the browser as it is.
- **Nothing is downloaded at build time.** pygbag fetched a WASM runtime from
  pygame-web.github.io to build with. Building now needs no network at all;
  only *playing* a built game does, once, for Python itself.
- **New: `kaypy/webrun.py`**, the two halves of a run — `run(source)` for the
  program's top level and `await drive()` for the frame loop — plus traceback
  trimming that drops asyncio, the standard library and the engine's own frames
  so the first thing a student reads is their own line. It is a real module
  rather than a string inside the page, so it is tested, and so a browser IDE
  embedding kaypy runs a game the same way the built page does.
- **Nothing is drawn below the game.** `print()` output goes to the browser's
  developer console rather than onto the page, so a published game is the game.
  The first thing the old pane showed was not even the game's doing: `import
  pygame` greets stdout with its version every time, so every export opened
  with a grey box under it reading "pygame-ce 2.5.8 (SDL 2.32.10, ...)". An
  error still shows on the page, because a blank canvas that explains nothing
  is worse than a red box that does.
- **New: `kaypy/web_page.html`**, the page itself. Shipped as package data,
  which means an editor that vendors kaypy can build exactly the same page
  rather than keeping its own copy in step by hand.
- `--serve` is now opt-in rather than automatic, since a built file opens on
  its own. `--no-build` and `--no-serve` are gone with pygbag; `--title` and
  `--out` are new.

**Fixed: filling the page one slot at a time corrupted it.** The engine the
page carries includes `webbuild.py`, whose own source contains the literal text
`__ASSETS__` — it is the module that defines the slots. Substituting them in
sequence put the engine in first and then replaced that mention too, halfway
through a Python string inside a JSON string. The page still looked plausible
and the JSON no longer parsed. Substitution is a single pass now, so what goes
in is never looked at again.

## 0.3.0

**`rotate()` — things can turn.** Asteroids was not writable before this;
there was no rotate component and no `.angle` on an object.

- `rotate(degrees)` turns an object clockwise about its **anchor**, so
  `anchor("center")` spins on the spot. Adds `.angle`, `.rotateBy(n)`,
  `.rotateTo(n)`.
- The **collision box does not turn** with it, deliberately, as in Kaplay. A
  hitbox that rotated would grow and shrink twice a revolution, so a spinning
  asteroid would catch the player at some angles and not others.
- `Vec2.fromAngle(degrees)` — the partner to it. An object at `angle` faces
  `Vec2.fromAngle(obj.angle)`, which is how a ship thrusts the way it points
  without trigonometry in the middle of a lesson.
- `examples/asteroids.py`: turning, thrust, momentum, screen-wrap, splitting
  rocks.

**`tween()` and thirty-one easing curves.** Change a value smoothly over
time — `tween(start, end, seconds, setter, ease)` — on numbers, `vec2`
positions or colour tuples. Returns a handle with `.then()`, `.cancel()`,
`.finish()` and `.paused`, all Kaplay's own names.

- `easings.easeOutBounce` and the rest, named `easeIn`/`easeOut`/`easeInOut`
  for each of Sine, Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic and
  Bounce, plus `easings.linear`. Any function from 0–1 to 0–1 works too.
- A tween lands **exactly** on its end value. An eased curve can return
  0.9999999 at t=1, and a sprite that stops one pixel short of where it was
  told to go is a bug nobody can see and everybody can feel.
- A misspelled curve says which names exist rather than raising a bare
  AttributeError about a module.

**The small Kaplay names.** `time()`, `destroy()`, `destroyAll()`,
`isKeyDown()`, `rgb()`, `lerp()`, `clamp()`, `chance()`, `wave()`,
`deg2rad()`, `rad2deg()`, and the object-free `onCollide(tagA, tagB, fn)`.

None matters on its own; together they are the difference between a Kaplay
example found online running as written and dying on its third line with a
NameError. "KAPLAY's documentation still tells you what to write" is only true
while the names in it exist.

- `time()` is the **game's** clock, not the wall's, so it stops when the game
  does — a sine wave driven by wall time jumps when a paused game resumes.
- `onCollide(tagA, tagB, fn)` hands the handler both objects **in the order
  the tags were named**, whichever order the collision system happened to meet
  them in. Otherwise a student's `bullet.destroy()` destroys the enemy.
- `rgb()` takes three numbers, a hex string long or short, or one number for a
  grey — and says what is missing rather than inventing a third channel.

**Assigning over a component's method is now refused.** `rock.size = 3` used
to overwrite `circle()`'s `size()` method and kill the game later, in the
collision system, with `'int' object is not callable` — nowhere near the line
responsible. It now raises immediately, names the method, and suggests picking
another name. Found by writing asteroids.py and losing a while to it.

**The README leads with decorators now.** Input, collisions and scenes all
showed the lambda first; they show the decorator first and the lambda after,
as the shorter option for a one-line handler. The `addLevel` tile factories
stay lambdas and now say why — they are recipes that get called to build a
component list, not event handlers.

**`tests/test_readme_code.py`** — every Python block in the README is executed
against the real engine, fragments included, on a preamble that supplies the
names they lean on. Nothing checked the README before: `test_guide_code.py`
covers GUIDE.md and only its whole programs, and the README is almost all
fragments and is the first thing anyone reads.

`tests/test_tween.py`: 27 checks, driving frames by hand so a "half a second"
tween takes no real time and the samples are exact. Every one asks what
*arrived* — the values the setter got, whether it landed exactly, whether
`.then()` really ran — because a tween that silently does nothing raises
nothing at all. That is not hypothetical: the same feature in the old
JavaScript bridge looked perfectly healthy while `.cancel()` cancelled
nothing.

`tests/test_rotate.py`: 32 checks. The direction and the pivot are measured
rather than reasoned about — a marker pixel is drawn and the test asks where
it landed — because both conventions are easy to get backwards and neither
mistake raises anything.

## 0.2.0

**The install is 92% smaller: 1366 KB → 113 KB.**

The wheel carried 2.6 MB of lesson audio, mostly one `background.wav`, against
92 KB of actual engine. Every `pip install kaypy` anywhere paid for sound that
one lesson plays. The same three files were also in the repo twice, byte for
byte identical.

- `examples/sounds/` is now the single copy, and `kaypy new` fetches from it.
- Everything needed to **run** still ships in the package — the starter game,
  every sprite, the dungeon atlas — so `kaypy new` works with no network.
- The starter game plays no sound, so a failed fetch costs nothing until the
  audio lesson. You get a sentence saying what happened and a game that runs,
  not a traceback.
- **New:** `kaypy sounds [folder]` fetches them later, for a school network
  that blocks GitHub or a build that ran offline.

**Fixed: the web export stopped at "Loading, please wait ..."**

`kaypy web` now prints `http://127.0.0.1:<port>` rather than
`http://localhost:<port>`. That is not cosmetic. pygbag's bootstrap treats a
page served from `http://localhost:8…` as having a local mirror of its package
CDN, so it fetches the pygame WebAssembly wheel from your own dev server:

```
GET /cdn/cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl -> 404
```

There is no mirror, so boot never finishes — after the whole interpreter and
every other file has loaded from the real CDN without complaint. `127.0.0.1`
does not match that prefix. Verified by loading one unchanged build both ways
in a real browser.

If you have an existing build, it works as-is — just open it at `127.0.0.1`.

**Tests:** `test_starter_sounds.py` (18 checks, mostly about the failure path)
and `test_web_serve_host.py` (6 checks, so nobody tidies that hostname back).

## 0.1.1

First published release.
