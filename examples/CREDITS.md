# Bundled assets

## Sprites

The sprites in `images/` come from the KAPLAY game library (formerly Kaboom.js),
which is distributed under the MIT License. MIT permits use, copying and
redistribution provided the license notice travels with the work, which is why
the full notice is reproduced below.

`dino_0` through `dino_8` are the nine frames of the original `dino.png` walk
cycle, sliced apart by `tools/build_assets.py` so each frame can be used as its
own Actor image. `dino` is frame 0.

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

## Dungeon sprites

`dungeon/` is **DungeonTileset II by 0x72**, released under
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) — the
author has put it in the public domain, so attribution is not required. It is
recorded here anyway, because knowing where an asset came from is worth more
than the licence requires.

Source: https://0x72.itch.io/dungeontileset-ii (version 1.7)

The pack ships 370 separate PNGs, four to an animation. `tools/vendor_dungeon.py`
gathers them into 142 sprites: each character becomes one horizontal strip
carrying all of its animations end to end, and each still tile is copied across
untouched. So `elf_m_idle_anim_f0..3` and `elf_m_run_anim_f0..3` become one
`elf_m.png`, eight frames wide, with an `idle` animation over frames 0–3 and a
`run` over 4–7 — which is what the Sprites panel inserts:

```python
loadSprite("elf_m", "dungeon/elf_m.png",
            sliceX=8, anims={
    "idle": {"from": 0, "to": 3, "speed": 8, "loop": True},
    "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
})
add([sprite("elf_m", anim="idle"), pos(100, 100)])
```

Two names, `coin` and `bomb`, exist in both packs. Kaplay keeps one sprite per
name, so the dungeon versions are called `dungeon_coin` and `dungeon_bomb`.

To rebuild from the original download:

```
python tools/vendor_dungeon.py --frames "path/to/0x72_DungeonTilesetII_v1.7/frames"
node tools/test_dungeon.mjs
```

### dungeon.png — the same artwork, uncut

`dungeon.png` at the top of `assets/` is the sprite atlas that ships with
KAPLAY's examples: one 512×512 image holding the whole tileset, which
`loadSpriteAtlas` cuts up by pixel coordinates. Same CC0 artwork; it sits at
the root of `assets/` rather than in a folder so that
`loadSpriteAtlas("dungeon.png", ...)` — the path in KAPLAY's example and on the
course site — works exactly as written.

It is kept alongside the cut-up pack because it is what Lesson 12 teaches:
where sprites come from, and how a rectangle of an image becomes a named
sprite. The five named regions are in `manifest.json`, and two of them are
**not** the values KAPLAY publishes:

| region | published | here | why |
|---|---|---|---|
| `ogre` | `y: 320` | `y: 336` | 320 is 16px above the ogres — half an ogre and a strip of floor |
| `chest` | `y: 304` | `y: 400` | 304 is empty space — the sprite loads with nothing in it |

Neither mistake raises an error. `tools/vendor_atlas.py` checks every region is
in bounds, divides evenly and has pixels in every frame, and `--proof` writes a
picture of all five for a human to look at:

```
python tools/vendor_atlas.py --file "path/to/dungeon.png" --proof /tmp/proof.png
```

## Sounds

`sounds/` holds 23 effects. Sounds must be `.wav` — the browser's SDL_mixer has
no Vorbis decoder, so `.ogg` files fail at playback. To add more, drop `.wav`
files in a folder and re-run:

```
python tools/build_assets.py --sounds "path/to/sounds"
```

They appear in the editor's Sprites panel, which inserts
`loadSound("ding", "sounds/ding.wav")` and `play("ding")`.

Record the license of whatever you add here, the same way the sprites are
recorded above.

---

**Note on this copy:** kaypy's `examples/` only vendors the handful of
sprites and sounds the 13 lesson scripts actually use (`bean`, `ghosty`,
`coin`, `portal`, `steel`, `grass`, `spike`, the `dino_0..8` walk cycle,
`dungeon/elf_m.png`, and the full `dungeon.png` atlas), plus three `.wav`
effects (`ding`, `background`, `screech`) — not the complete packs
described above. `examples/lesson12_sprite_atlas.py` cuts its `wall`,
`floor`, `hero`, `ogre` and `chest` regions straight out of `dungeon.png`
using the corrected coordinates from the table above (verified by cropping
each region during development and checking it wasn't blank — `ogre` and
`chest` land on empty/half-cropped pixels at the coordinates KAPLAY
publishes). Everything above is kept verbatim as the upstream attribution
and license text; both licenses (MIT for the Kaplay pack, CC0 for
DungeonTileset II) travel with this copy regardless of which subset of
files is actually present.
