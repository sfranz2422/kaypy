# Bundled assets

Everything beside this file came from somewhere else. Both sources permit
redistribution, and the full terms are reproduced below so they travel with
the files rather than living on a website that may move.

| what | where from | licence |
|---|---|---|
| `images/` — 16 sprites | KAPLAY (formerly Kaboom.js) | MIT |
| `dungeon/elf_m.png` | 0x72's DungeonTileset II | CC0 1.0 |
| `dungeon.png` — the atlas | 0x72's DungeonTileset II | CC0 1.0 |
| `sounds/` — 3 effects | Kaboom.js, now KAPLAY's asset library | CC0 1.0 |

Only the files kaypy's own lessons and starter game actually use are here, not
the complete packs.

---

## Sprites — KAPLAY, MIT

The sprites in `images/` come from the KAPLAY game library (formerly
Kaboom.js), which is distributed under the MIT License. MIT permits use,
copying and redistribution provided the licence notice travels with the work,
which is why the full notice is reproduced here.

`dino_0` through `dino_8` are the nine frames of the original `dino.png` walk
cycle, split so each frame can be used on its own.

Project: https://github.com/kaplayjs/kaplay

```
MIT License

Copyright (c) 2025 KAPLAY Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Dungeon sprites — 0x72, CC0

`dungeon/` and `dungeon.png` are **DungeonTileset II by 0x72**, released under
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — the
author has put it in the public domain, so attribution is not required. It is
recorded here anyway, because knowing where an asset came from is worth more
than the licence asks.

Source: https://0x72.itch.io/dungeontileset-ii (version 1.7)

`elf_m.png` is one character's frames gathered into a single horizontal strip:
eight frames wide, with an `idle` animation over frames 0–3 and a `run` over
4–7.

```python
loadSprite("elf_m", "dungeon/elf_m.png", sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})
add([sprite("elf_m", anim="idle"), pos(100, 100)])
```

### dungeon.png — the same artwork, uncut

`dungeon.png` is the sprite atlas that ships with KAPLAY's examples: one
512×512 image holding the whole tileset, which `loadSpriteAtlas` cuts up by
pixel coordinates. Same CC0 artwork, kept because it is what Lesson 12
teaches — where sprites come from, and how a rectangle of an image becomes a
named sprite.

Two of the five region coordinates KAPLAY publishes are **wrong for this
image**, and neither mistake raises an error:

| region | published | correct | what the published value gives you |
|---|---|---|---|
| `ogre` | `y: 320` | `y: 336` | 16px too high — half an ogre and a strip of floor |
| `chest` | `y: 304` | `y: 400` | empty space, so the sprite loads with nothing in it |

`examples/lesson12_sprite_atlas.py` uses the corrected values.

## Sounds — Kaboom.js / KAPLAY crew, CC0

The sound effects came from **Kaboom.js**, the project KAPLAY grew out of, and
were part of its original download. KAPLAY now publishes the same asset library
as [`kaplayjs/crew`](https://github.com/kaplayjs/crew), released under
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — a
public-domain dedication, so no attribution is required. Recorded here for the
same reason as the dungeon pack.

Source: https://github.com/kaplayjs/crew (CC0-1.0)

Either route permits redistribution, which is the part that matters: the
Kaboom-era files travelled under that project's MIT licence, and the same
assets are now dedicated to the public domain outright.

Uncompressed PCM `.wav` is the safe format — it is what these are, and what
plays everywhere without conversion.

---

## kaypy itself

kaypy's own code is MIT, © Stephen Franz — see `LICENSE` at the root of the
repository. It is an independent project and is not affiliated with, endorsed
by, or produced by the KAPLAY team; it follows KAPLAY's published API so that
KAPLAY's documentation applies to what you write.
