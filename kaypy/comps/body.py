"""body(): makes an object respond to physics. isStatic=True makes it a
wall — solid, and never moved by anything. mass=n makes it heavy but
still pushable. Gives .jump(), .isGrounded(), .onGround()."""
from ..gameobj import Comp
from ..vec2 import Vec2


class BodyComp(Comp):
    id = "body"

    def __init__(self, isStatic=False, mass=1, jumpForce=800):
        self.isStatic = isStatic
        self.mass = mass
        self.jumpForce = jumpForce
        self.vel = Vec2(0, 0)
        self._grounded = False
        self._pending_grounded = False
        self._ground_handlers = []

    def add(self, obj):
        self._obj = obj

    def jump(self, force=None):
        if force is None:
            force = self.jumpForce
        self.vel.y = -force
        self._grounded = False

    def isGrounded(self) -> bool:
        return self._grounded

    def onGround(self, fn=None):
        from ..callutil import register_or_decorate

        def register(f):
            self._ground_handlers.append(f)
            return f

        return register_or_decorate(fn, register)

    def _apply_grounded(self, value: bool):
        was = self._grounded
        self._grounded = value
        if value and not was:
            for fn in self._ground_handlers:
                fn()


def body(isStatic=False, mass=1, jumpForce=800):
    return BodyComp(isStatic=isStatic, mass=mass, jumpForce=jumpForce)
