"""Sprite / sound loading: loadSprite, loadSpriteAtlas, loadSound.

Kaplay's own troubleshooting note applies here too: "the sprite is
invisible but the game runs" almost always means a bad path, and
"every frame is half one pose and half the next" means sliceX doesn't
match the sheet. We raise clear errors for the first and let the second
happen silently (cutting a rectangle of nothing without complaint),
exactly as Kaplay's own guide describes.
"""
from __future__ import annotations
import os
import sys
import pygame


class SpriteAsset:
    def __init__(self, frames, anims=None, frame_size=None):
        self.frames = frames  # list[pygame.Surface]
        self.anims = anims or {}  # name -> {"from","to","speed","loop"} or int
        self.frame_size = frame_size or (frames[0].get_width(), frames[0].get_height())


def _load_image(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"loadSprite/loadSpriteAtlas: no such file {path!r} — "
            f"check the path (the two sprite packs live in separate "
            f"folders; a dungeon sprite is not under images/)"
        )
    return pygame.image.load(path).convert_alpha()


def _slice_surface(surface, slice_x, slice_y):
    w = surface.get_width() // slice_x
    h = surface.get_height() // slice_y
    frames = []
    for row in range(slice_y):
        for col in range(slice_x):
            rect = pygame.Rect(col * w, row * h, w, h)
            frame = pygame.Surface((w, h), pygame.SRCALPHA)
            frame.blit(surface, (0, 0), rect)
            frames.append(frame)
    return frames, (w, h)


def _normalize_anims(anims):
    out = {}
    for name, spec in (anims or {}).items():
        if isinstance(spec, int):
            out[name] = {"from": spec, "to": spec, "speed": 1, "loop": False}
        else:
            out[name] = {
                "from": spec.get("from", 0),
                "to": spec.get("to", 0),
                "speed": spec.get("speed", 10),
                "loop": spec.get("loop", False),
            }
    return out


class AssetManager:
    def __init__(self):
        self.sprites: dict[str, SpriteAsset] = {}
        self.sounds: dict[str, "pygame.mixer.Sound"] = {}
        self._atlas_cache: dict[str, "pygame.Surface"] = {}

    def loadSprite(self, name, path, sliceX=1, sliceY=1, anims=None):
        if isinstance(path, (list, tuple)):
            frames = [_load_image(p) for p in path]
            frame_size = (frames[0].get_width(), frames[0].get_height())
        else:
            surface = _load_image(path)
            if sliceX > 1 or sliceY > 1:
                frames, frame_size = _slice_surface(surface, sliceX, sliceY)
            else:
                frames = [surface]
                frame_size = (surface.get_width(), surface.get_height())
        self.sprites[name] = SpriteAsset(frames, _normalize_anims(anims), frame_size)
        return self.sprites[name]

    def loadSpriteAtlas(self, path, atlas):
        if path not in self._atlas_cache:
            self._atlas_cache[path] = _load_image(path)
        sheet = self._atlas_cache[path]
        for name, spec in atlas.items():
            x, y = spec["x"], spec["y"]
            w, h = spec["width"], spec["height"]
            region = pygame.Surface((w, h), pygame.SRCALPHA)
            region.blit(sheet, (0, 0), pygame.Rect(x, y, w, h))
            slice_x = spec.get("sliceX", 1)
            slice_y = spec.get("sliceY", 1)
            if slice_x > 1 or slice_y > 1:
                frames, frame_size = _slice_surface(region, slice_x, slice_y)
            else:
                frames = [region]
                frame_size = (w, h)
            self.sprites[name] = SpriteAsset(
                frames, _normalize_anims(spec.get("anims")), frame_size
            )
        return self.sprites

    def loadSound(self, name, path):
        if sys.platform == "emscripten":
            # If a sibling .ogg is sitting next to the .wav, prefer it in the
            # browser, so a script never needs an if-web branch just to pick a
            # file extension.
            #
            # Plain uncompressed PCM .wav — which is what every sound in the
            # lessons is, and what most tools write by default — plays fine in
            # the browser, so this is no longer something a game has to do.
            # It used to be: the old pygbag build step rejected .wav outright,
            # so `kaypy web` converted every one to .ogg with ffmpeg first.
            # That is gone, along with the ffmpeg dependency. What remains is
            # a preference, for the compressed formats that genuinely are
            # chancy in a WASM SDL2-mixer (ADPCM, µ-law, mp3): put an .ogg
            # beside the .wav and the browser quietly gets the better one.
            ogg_path = os.path.splitext(path)[0] + ".ogg"
            if os.path.isfile(ogg_path):
                path = ogg_path
        if not os.path.isfile(path):
            raise FileNotFoundError(f"loadSound: no such file {path!r}")
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error:
            self.sounds[name] = None  # audio device unavailable (headless/CI)
        return self.sounds[name]

    def get_sprite(self, name) -> SpriteAsset:
        if name not in self.sprites:
            raise KeyError(
                f"no sprite called {name!r} — loadSprite(\"{name}\", ...) "
                f"must run before it is used"
            )
        return self.sprites[name]
