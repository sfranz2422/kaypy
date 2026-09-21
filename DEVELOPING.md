# Developer notes

How kaypy is put together, what's been verified and how, where it's still
thin, and the bugs that were expensive enough to be worth writing down.

For how to *use* the engine, see [README.md](README.md).

---

## Architecture

- **`kaplay/gameobj.py`** — `GameObj` merges each component's attributes onto
  itself via `__getattr__`/`__setattr__` delegation, the same way KAPLAY's JS
  does `Object.assign`. Calling `.jump()` on an object without `body()` raises
  exactly the `AttributeError` the guide's troubleshooting section describes.
- **`kaplay/comps/`** — one file per component family. Components are data
  holders with optional `add`/`update`/`destroy` hooks; nothing draws itself.
- **`kaplay/geometry.py`** — the one place that turns `pos()` + `anchor()` +
  `scale()` + parent offsets into a world-space rect. Both collision
  (`area.py`) and rendering (`render.py`) call into it, so "does this touch
  that" and "where does this draw" can never disagree.
- **`kaplay/physics.py`** — gravity and integration, then AABB overlap and
  resolution. Physical pushback only happens between two objects that **both**
  have `body()`; a coin or enemy with only `area()` is a pass-through trigger,
  per Lesson 3. Collision rects are `pygame.FRect` (float precision) rather
  than `pygame.Rect` — a resting object's sub-pixel gravity drift would
  otherwise round away and make `isGrounded()` flicker.
- **`kaplay/engine.py`** — the `Engine` singleton: window, clock, asset/event/
  timer managers, camera, and the frame loop. The loop is `asyncio`-shaped so
  the same body drives both the native run and the pygbag web build.
- **`kaplay/render.py`** — draws sprite/rect/circle/text in `z()` order,
  through the camera unless `fixed()`.

### How the loop starts

There is no `run()` call anywhere in the KAPLAY guide, so there is none here
either. Natively, `kaplay()` registers the frame loop with `atexit`, so it
starts the instant your script's top level finishes. `run()` is still exposed
for tooling that wants to be explicit, and is a harmless no-op the second time.

The web build can't use that trick (see *pygbag incompatibilities* below), so
`webbuild.py` generates a `main.py` that imports your script as a module —
which runs its whole top level exactly once, same as atexit firing after it —
and then awaits `run_async()` directly. Your game script is byte-for-byte the
same on both targets.

---

## Tests

Standalone scripts, run directly, using plain `assert`. They set
`SDL_VIDEODRIVER=dummy` themselves so they run headless.

```bash
python tests/test_core.py               # collision edge-triggering, child objects, scenes, state()
python tests/test_physics.py            # gravity, grounding, mass-based pushing
python tests/test_tile_floor_landing.py # landing on a tiled floor, at uneven frame rates
python tests/test_web_platform_guard.py # kaplay() never touches pygbag's broken atexit
python tests/test_lazy_key_map.py       # pygame.K_* is never read before pygame.init()
python tests/test_decorators.py         # every event works as a callback AND as a decorator
python tests/test_guide_code.py         # every program printed in GUIDE.md actually runs
```

`test_web_platform_guard`, `test_lazy_key_map` and `test_tile_floor_landing`
all exist because of bugs that only ever showed up in a browser.

`KAYPY_TEST_MAX_FRAMES=n` makes any game script run `n` frames and exit, which
is how the lessons get smoke-tested. `KAYPY_SCREENSHOT_AT=n` plus
`KAYPY_SCREENSHOT_PATH=out.png` dumps a frame to disk, which is how they get
checked by eye.

**No pytest wiring yet** — worth converting once the API settles.

> A caution learned the hard way: "the lesson script exits 0" is not the same
> as "the lesson works." Lesson 10's player fell through the floor for a long
> time while the script exited 0 every single run. Render a frame and look at
> it.

`test_guide_code.py` applies the weaker half of that lesson to GUIDE.md: it pulls
every complete program out of the guide and runs it, so a sample can't rot into
something that doesn't start. Knowing it is *correct* still means rendering it
and looking.

---

## Physics: three real bugs

All three were found by watching Lesson 10 actually run, not by reading code.
`tests/test_tile_floor_landing.py` pins down all three.

**1. Push direction was read off `pos()`, which is anchor-dependent.**
`_resolve` decided which object was on top by comparing the two objects' raw
`pos` values. But `pos` means different things to different objects: a plain
tile's `pos.y` is its *top edge*, while `anchor("bot")` — what a platformer
character wants, so it can be placed by its feet — makes `pos.y` the *bottom
edge*. A bean standing on a tile therefore had the larger `pos.y` of the two,
so the engine concluded the tile was above the bean and pushed the bean
**downward**, deeper in, every frame, until it was through the floor and
falling forever. Any object combining `anchor("bot")` with `body()` hit this,
on every platform, at every frame rate. Now read off the collision rects, which
`get_world_rect()` has already folded the anchor into.

**2. The resolution axis came from whichever overlap was smaller.**
That's the usual shortcut and it fails on the case a platformer hits
constantly: a floor built of separate tiles. A player landing on the seam
between two tiles overlaps each by only half its width; sink deeper than that
in a single frame and both tiles push *sideways*, in opposite directions, so
they cancel and nothing holds the player up. Now the axis comes from where the
two were before the step — if they already lined up horizontally and have only
now begun overlapping vertically, it's a landing, however deep it got.

**3. Fast bodies tunneled through walls.**
Movement and collision now run in as many substeps as needed to keep any body
under `MAX_STEP_PX` (16px) of travel per step, up to `MAX_SUBSTEPS` (4).
Normal frames need exactly one substep, so this costs nothing until something
is genuinely moving fast. Frame times aren't ours to control — a backgrounded
tab, a slow machine, a breakpoint — so the fix has to be in how far one step
may move things.

Still not stress-tested: simultaneous multi-body stacking.

---

## Events: two forms, one registration path

Every event accepts a function, or acts as a decorator over one. Both go
through `callutil.register_or_decorate(fn, register)`: given a function it
registers immediately, given `None` it hands back a decorator that registers
and then returns the function unchanged — so the decorated name stays bound to
the function rather than to `None` or a wrapper.

The callback form is Kaplay's and is not going anywhere; it's what makes
Kaplay's docs translate line for line. The decorator form exists because
Python's lambdas hold a single *expression*, and the workarounds teach things
you would not choose to teach:

```python
# what the lesson had to write
onKeyPress("space", lambda: player.jump(1000) if player.isGrounded() else None)
player.onCollide("danger", lambda d: setattr(player, "pos", level.tile2Pos(2, 5)))
```

The `else None` is inert — it exists only because a conditional expression
demands an else. `setattr` appears only because a lambda cannot assign. Neither
is game logic.

Adding it cost one helper and an `fn=None` default on each event. Bare
decorators (`@onUpdate`, `@player.onGround`) already worked before any of this,
because the registration functions returned `fn`.

`tests/test_decorators.py` checks each event twice, once per form, asserting
the same registration and the same firing — plus that decorated handlers stay
callable and keep their `__name__`.

**Naming stays camelCase.** `onKeyPress`, not `on_key_press`. snake_case would
be more idiomatic Python in isolation, but the entire premise of this project
is that Kaplay's documentation and examples apply as written; two spellings for
every event would cost that and hand students two names for one idea. The
decorator gain doesn't require giving it up.

---

## Web export (pygbag)

`webbuild.py` assembles a folder, converts audio, runs pygbag, and serves the
result. Four separate incompatibilities had to be fixed before a page would run
at all. Each one is cheap to re-break, so they're documented here with the
evidence that found them.

### 1. pygbag's `atexit` replacement is broken

pygbag replaces the stdlib `atexit` module outright
(`pygbag/support/cross/aio/atexit.py`), and that replacement has a genuine bug:
its `register()` closes over an undefined `arg` instead of `args`, so calling
it raises `NameError` immediately. kaypy's atexit-based "no `run()` call" trick
would have crashed instantly under pygbag.

Fixed by detecting `sys.platform == "emscripten"` (the real marker pygbag and
CPython both use) and skipping atexit registration there entirely. The web
build's generated `main.py` calls `run_async()` explicitly instead. Pinned by
`tests/test_web_platform_guard.py`, which recreates pygbag's actual broken
module and confirms `kaplay()` never touches it once that platform is detected.

### 2. pygame was a stub, because nothing declared it

pygbag's in-browser bootstrap only links in the *real*, compiled pygame WASM
extension when it finds a PEP 723 dependency block naming `pygame.base` in the
entry script it runs:

```python
# /// script
# dependencies = [
#     "pygame.base",
# ]
# ///
```

Without it, `import pygame` still silently succeeds, but you get a stub with
the constants (`pygame.K_LEFT` and friends) and **none of the real functions**.

Ordinary pygbag games never hit this, because they write `import pygame` at the
top of their own `main.py`. A kaypy game never writes it at all — `kaplay` does
that internally, several imports removed from anything pygbag's scanner reads —
so that block could only ever come from the generated `main.py`, and now does.

Symptom: the page loaded, the click did nothing, and the crash was
`AttributeError: module 'pygame' has no attribute 'init'` at the exact line
`Engine.__init__` calls `pygame.init()` — with pygbag's own boot log printing
`"# 696: no pep 723 block found"` immediately before it.

### 3. `pygame.K_*` read at import time

`kaplay/events.py` used to build its key-name lookup table at module level.
Native pygame-ce doesn't care — those constants exist the moment you
`import pygame`, before `pygame.init()`. Under pygbag's WASM pygame they don't
exist until after `init()`, and `import kaplay` reaches `events.py` (via
`engine.py`'s `from .events import EventManager`) well before a script's own
`kaplay()` call runs `pygame.init()`. Every web export died with
`AttributeError: module 'pygame' has no attribute 'K_LEFT'` before a single
line of the game ran.

The table is now built lazily on first use — `onKeyDown`/`onKeyPress`/
`onKeyRelease` or the frame loop, all of which only happen after `kaplay()`.
Pinned by `tests/test_lazy_key_map.py`.

### 4. A reboot loop on the very first click

pygbag's default (`--can_close 0`) registers a `beforeunload` handler that
calls `confirm("Are you sure you want to navigate away from this page ?")`.
Modern Chrome and Safari flatly refuse to run a synchronous `confirm()` during
`beforeunload` — and rather than the site just failing to prompt, that sends
pygbag's runtime into a loop: fetch the game archive, wait for the click it
demands to unlock audio, hit the blocked `confirm()`, reboot from scratch,
forever, before the first frame ever runs. From outside it looks exactly like
"I clicked, saw a border, then nothing."

`webbuild.py` always passes `--can_close 1`, which skips the handler. Confirmed
against a real built site by driving a browser through the click and watching
the console log the fetch → focus → blocked-confirm → reboot cycle fire
repeatedly with the flag unset, then stop once it was set.

**This is why `webbuild.py` must be the thing that runs pygbag.** The flags
above only get added when it's the one invoking it. Running
`python -m pygbag --build <dir>` yourself afterwards skips them and puts you
straight back on the broken defaults.

### Audio: `.wav` → `.ogg`

Browsers' WASM audio can't reliably decode most `.wav` files, and pygbag's
build step refuses to package one at all ("has a common unsupported format. Use
OGG format instead."). `webbuild.py` converts every `.wav` it copies into a
same-named `.ogg`, and `AssetManager.loadSound` prefers that sibling `.ogg`
automatically whenever it detects the browser platform — so the game script
still just says `loadSound("ding", "sounds/ding.wav")` with no if-web branch.

The conversion uses `ffmpeg` if it's on PATH, otherwise the `imageio-ffmpeg`
package (pulled in by `pip install -e ".[web]"`), whose wheel bundles an actual
static ffmpeg binary per platform — so no Homebrew or system package manager is
ever required. Only if neither is available does it fall back to
`--disable-sound-format-error` and warn.

> A `soundfile`-only pure-Python fallback was tried first and rejected: its
> bundled libsndfile OGG/Vorbis encoder **segfaulted silently** on a real
> 22.05kHz mono `.wav`, writing a valid-looking but completely empty `.ogg`.
> Every conversion now runs in a subprocess so an encoder crash can't take the
> build down with it.

### Frame pacing on the web

Natively, `clock.tick(60)` sleeps to pace the loop. In the browser that sleep
can't yield, so it just burns the main thread and makes frame times *less*
even — measured in a real build, `dt` alternated between 16ms and the engine's
50ms ceiling. On web the loop now only measures, and lets the browser's
animation frame do the pacing.

### Debugging a running web build

Worth knowing, because it turns a rebuild-and-squint loop into a live one:

- pygbag prints Python tracebacks to its **own in-page terminal**, not the
  browser console. `read_page` on the accessibility tree shows them; the
  devtools console will not.
- `window.python.PyRun_SimpleString("...")` runs arbitrary Python **inside the
  live game**. That's how the falling-bean bug was diagnosed: reset the player,
  record its rect each frame from an injected `onUpdate`, and read the numbers
  back out. The physics fix was verified the same way — monkeypatched into the
  running build and confirmed landing before anything was rebuilt.

---

## Why pygame-ce is pinned, not vendored

It's pinned to an exact version (`pygame-ce==2.5.8`), not vendored:

- **It's a compiled C extension**, shipped as separate binary wheels per OS and
  CPU. There's no single file to vendor — one wheel's contents only work on the
  platform it was built for, and shipping all of them is what PyPI already does
  for you, at its hosting cost rather than this repo's.
- **Vendoring the source** means bundling SDL2's source and a build toolchain,
  and compiling on every machine it installs to. That trades "pip might break
  someday" for "the install needs a C compiler and SDL2 headers today" — a
  bigger, earlier cost for a smaller, later risk.
- **A pin already buys the thing vendoring was for.** `pygame-ce==2.5.8`
  resolves to the same wheel every time, forever; PyPI doesn't let a published
  version change underneath you. Bumping it is a deliberate one-line change you
  test against, not something that happens to you.

If the real worry is installing with no internet at all, that's a different and
solvable problem (a local wheel cache, or an offline `pip download` bundle) and
worth deciding on separately.

Note that the web build runs a *different* pygame — pygbag supplies
`pygame-ce 2.5.7` compiled for WASM, and you don't get to choose it. Anything
that depends on 2.5.8-specific behaviour will diverge in the browser.

---

## Why the sounds are fetched, not shipped

The wheel was 1.36 MB. Of that, 92 KB was the engine and 2.6 MB uncompressed
was three `.wav` files, mostly one `background.wav`. Every `pip install kaypy`
anywhere paid for audio that exactly one lesson plays. They were also in the
repo twice — `kaplay/starter/sounds/` and `examples/sounds/`, byte for byte
identical.

So `examples/sounds/` is now the one copy, `kaypy new` fetches from it over
raw.githubusercontent.com, and the wheel is **112 KB**.

What had to stay true, and is checked in `tests/test_starter_sounds.py`:

- everything needed to *run* still ships — the starter game, every sprite, the
  dungeon atlas — so `kaypy new` works with no network at all;
- the starter game plays no sound, so a failed fetch costs a student nothing
  until Lesson 8;
- a failed fetch prints a sentence they can act on and still leaves a game that
  runs, rather than a traceback;
- files are written to `.part` and moved into place, because a half-written wav
  that looks like a real file is worse than no file — the next run would skip
  it;
- a second run downloads nothing.

Two packaging traps worth knowing, both found by building the wheel and looking
inside it rather than by reading the config:

- **Narrowing `package-data` is not enough.** `include-package-data` is on by
  default, so anything `MANIFEST.in` sweeps up lands in the wheel regardless.
  The wheel came out at 1366 KB with the sounds still in it. What actually
  works is `exclude-package-data`, plus a `prune` in `MANIFEST.in`.
- **A clone is not an install.** `kaypy new` copies `starter/` wholesale, so a
  working copy that still has a stale `starter/sounds/` would go on shipping it
  to students. `cmd_new` ignores that name explicitly.

The fetch is pinned to the release tag (`v0.1.1`) and falls back to `main`,
which is what it uses today because there are no tags yet. Tagging releases
makes an old install keep fetching the assets it was published with.

---

## Known limitations

- **No tile-based pathfinding.** `tile(isObstacle=True)` is stored (Lesson 12)
  but nothing reads it to route around obstacles the way KAPLAY's own
  pathfinding helpers do.
- **Multi-body stacking** is untested — see *Physics* above.
- **No pytest suite** — `tests/` are standalone scripts.
- **Audio on a headless machine** degrades to silent no-ops rather than
  crashing (`pygame.mixer.init()` and `loadSound()` are both wrapped), which is
  useful for CI. On a real desktop, `examples/lesson8_audio_buttons.py` plays
  real sound.
- **The native build step for the web** has only ever been exercised up to the
  network wall in this project's sandbox, which blocks pygbag's CDN
  (`pygame-web.github.io`). Folder assembly and file gathering are verified
  there; the actual WASM packaging is verified on a normal machine. The browser
  side has been driven end-to-end against a real local server.
