import pygame
from ..gameobj import Comp


class SpriteComp(Comp):
    id = "sprite"

    def __init__(self, name, anim=None, frame=None):
        self.spriteName = name
        self.flipX = False
        self.flipY = False
        self._asset = None
        self._frame_override = frame
        self._cur_anim = None
        self._anim_spec = None
        self._anim_frame_idx = 0
        self._anim_timer = 0.0
        self._anim_done = False
        self._pending_initial_anim = anim
        self._frame_cache = {}

    def add(self, obj):
        from ..engine import current_engine
        self._asset = current_engine().assets.get_sprite(self.spriteName)
        if self._frame_override is None:
            self._anim_frame_idx = 0
        if self._pending_initial_anim:
            self.play(self._pending_initial_anim)

    def play(self, name):
        """Restarts the animation from its first frame — calling it every
        frame while a key is held gives a character stuck on frame 0."""
        spec = self._asset.anims.get(name)
        if spec is None:
            raise KeyError(
                f"sprite {self.spriteName!r} has no animation called {name!r}"
            )
        self._cur_anim = name
        self._anim_spec = spec
        self._anim_frame_idx = spec["from"]
        self._anim_timer = 0.0
        self._anim_done = False

    def curAnim(self):
        return self._cur_anim

    def update(self, obj):
        if self._cur_anim is None or self._anim_done:
            return
        from ..engine import current_engine
        dt = current_engine().dt()
        spec = self._anim_spec
        speed = spec.get("speed") or 10
        step = 1.0 / speed
        self._anim_timer += dt
        while self._anim_timer >= step:
            self._anim_timer -= step
            if self._anim_frame_idx >= spec["to"]:
                if spec.get("loop"):
                    self._anim_frame_idx = spec["from"]
                else:
                    self._anim_done = True
                    break
            else:
                self._anim_frame_idx += 1

    def current_surface(self):
        idx = self._frame_override if self._frame_override is not None else self._anim_frame_idx
        frames = self._asset.frames
        idx = max(0, min(idx, len(frames) - 1))
        key = (idx, self.flipX, self.flipY)
        cached = self._frame_cache.get(key)
        if cached is not None:
            return cached
        surf = frames[idx]
        if self.flipX or self.flipY:
            surf = pygame.transform.flip(surf, self.flipX, self.flipY)
        self._frame_cache[key] = surf
        return surf

    def size(self):
        return self._asset.frame_size


def sprite(name, anim=None, frame=None):
    return SpriteComp(name, anim=anim, frame=frame)
