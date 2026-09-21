# Changelog

## Unreleased

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

**Assigning over a component's method is now refused.** `rock.size = 3` used
to overwrite `circle()`'s `size()` method and kill the game later, in the
collision system, with `'int' object is not callable` — nowhere near the line
responsible. It now raises immediately, names the method, and suggests picking
another name. Found by writing asteroids.py and losing a while to it.

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
