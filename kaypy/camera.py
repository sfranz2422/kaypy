from .vec2 import Vec2


class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pos = Vec2(width / 2, height / 2)
        self.scale = 1.0
        self.shake_amount = 0.0
        self._frame_shake_offset = Vec2(0, 0)

    def setPos(self, pos):
        self.pos = Vec2(pos.x, pos.y)

    def setScale(self, n):
        self.scale = n

    def shake(self, amount=8):
        self.shake_amount = amount

    def begin_frame(self):
        """Called once per frame by the render system: decays shake and
        freezes this frame's random offset so every object drawn this
        frame shakes together."""
        if self.shake_amount <= 0:
            self._frame_shake_offset = Vec2(0, 0)
            return
        import random
        a = self.shake_amount
        self._frame_shake_offset = Vec2(random.uniform(-a, a), random.uniform(-a, a))
        self.shake_amount *= 0.9
        if self.shake_amount < 0.2:
            self.shake_amount = 0

    def world_to_screen(self, world_pos: Vec2) -> Vec2:
        center = Vec2(self.width / 2, self.height / 2)
        return (world_pos - self.pos) * self.scale + center + self._frame_shake_offset

    def screen_to_world(self, screen_pos) -> Vec2:
        if not isinstance(screen_pos, Vec2):
            screen_pos = Vec2(screen_pos[0], screen_pos[1])
        center = Vec2(self.width / 2, self.height / 2)
        return (screen_pos - center) / self.scale + self.pos
