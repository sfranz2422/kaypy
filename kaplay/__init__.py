"""from kaplay import * — every name here is Kaplay's own name, in
Kaplay's own order, with Kaplay's own arguments. The Kaplay documentation
and every Kaplay example on the internet applies to what you write here;
only the language underneath (real, native Python, via pygame-ce) is new.
"""
from .vec2 import vec2, Vec2
from .engine import Engine, current_engine, rand, randi, choose
from .debugmod import debug
from .easings import easings
from .helpers import (time, destroy, destroyAll, isKeyDown, rgb, lerp,
                      clamp, chance, wave, deg2rad, rad2deg)
from .level import addLevel, Level
from .kaboom import addKaboom

# ---- components ---------------------------------------------------------
from .comps.pos import pos
from .comps.sprite import sprite
from .comps.shapes import rect, circle, text
from .comps.area import area
from .comps.body import body
from .comps.transform import (anchor, scale, rotate, color, opacity, outline,
                              z, fixed)
from .comps.state import state
from .comps.move import move, offscreen, tile
from .callutil import register_or_decorate

__all__ = [
    "kaplay",
    "loadSprite", "loadSpriteAtlas", "loadSound",
    "setGravity", "setBackground",
    "add", "get", "addLevel", "addKaboom",
    "pos", "sprite", "rect", "circle", "text", "area", "body",
    "anchor", "scale", "rotate", "color", "opacity", "outline", "z", "fixed",
    "move", "offscreen", "tile", "state",
    "onUpdate", "onKeyDown", "onKeyPress", "onKeyRelease", "onClick",
    "wait", "loop", "tween", "easings", "onCollide",
    "scene", "go",
    "width", "height", "center", "dt", "vec2", "Vec2",
    "rand", "randi", "choose", "chance", "lerp", "clamp", "wave",
    "time", "destroy", "destroyAll", "isKeyDown", "rgb",
    "deg2rad", "rad2deg",
    "mousePos", "toWorld",
    "setCamPos", "setCamScale", "shake",
    "play",
    "debug",
    "run",
]


def kaplay(width=800, height=600, background=(0, 0, 0)):
    """Starts the engine. It has to come first, before anything else."""
    return Engine(width=width, height=height, background=background)


# ---- loading -------------------------------------------------------------

def loadSprite(name, path, sliceX=1, sliceY=1, anims=None):
    return current_engine().assets.loadSprite(name, path, sliceX=sliceX, sliceY=sliceY, anims=anims)


def loadSpriteAtlas(path, atlas):
    return current_engine().assets.loadSpriteAtlas(path, atlas)


def loadSound(name, path):
    return current_engine().assets.loadSound(name, path)


def setGravity(n):
    current_engine().setGravity(n)


def setBackground(r, g, b):
    current_engine().setBackground(r, g, b)


# ---- making things --------------------------------------------------------

def add(comp_list):
    return current_engine().add(comp_list)


def get(tag):
    return current_engine().get(tag)


# ---- events ----------------------------------------------------------------

def onUpdate(*args):
    """onUpdate(fn) / onUpdate(tag, fn), or as a decorator:

        @onUpdate                 # every frame
        @onUpdate("enemy")        # every frame, once per tagged object
    """
    if len(args) == 2:
        tag, fn = args
        return register_or_decorate(fn, lambda f: current_engine().events.on_update(tag, f))
    if len(args) == 1 and callable(args[0]):
        return current_engine().events.on_update(args[0])
    if len(args) == 1:
        tag = args[0]
        return register_or_decorate(None, lambda f: current_engine().events.on_update(tag, f))
    raise TypeError("onUpdate() takes a function, or a tag and a function")


def onKeyDown(key, fn=None):
    return register_or_decorate(fn, lambda f: current_engine().events.on_key_down(key, f))


def onKeyPress(key, fn=None):
    return register_or_decorate(fn, lambda f: current_engine().events.on_key_press(key, f))


def onKeyRelease(key, fn=None):
    return register_or_decorate(fn, lambda f: current_engine().events.on_key_release(key, f))


def onClick(fn=None):
    return register_or_decorate(fn, lambda f: current_engine().events.on_click(f))


def wait(seconds, fn=None):
    return register_or_decorate(fn, lambda f: current_engine().timers.wait(seconds, f))


def loop(seconds, fn=None):
    return register_or_decorate(fn, lambda f: current_engine().timers.loop(seconds, f))


def onCollide(tag_a, tag_b, fn=None):
    """Every time anything tagged `tag_a` touches anything tagged `tag_b`.

        onCollide("bullet", "enemy", lambda b, e: (b.destroy(), e.destroy()))

        @onCollide("player", "spike")
        def hurt(player, spike):
            go("gameover")

    The object-free form of `obj.onCollide(tag, fn)`, for when the pair
    matters and neither object is one you are holding — bullets and enemies
    that both appear and vanish while the game runs. The handler is given
    both objects, in the order the tags were named.

    Registered against objects as they appear, so it covers ones created
    later, which is the whole reason to prefer it over wiring each bullet up
    as it is made.
    """
    from .callutil import register_or_decorate

    def register(f):
        current_engine().events.on_collide_tags(tag_a, tag_b, f)
        return f

    return register_or_decorate(fn, register)


def tween(start, end, duration, setter, ease=None):
    """Change a value smoothly over time.

        tween(100, 600, 0.5, lambda x: setattr(box.pos, "x", x))
        tween(1.0, 0.0, 1.0, fade).then(lambda: print("gone"))
        tween(box.pos, target, 0.8, move_box, easings.easeOutBounce)

    Works on numbers, on vec2 positions and on colour tuples. The fifth
    argument is the shape of the motion — see `easings`; without one it moves
    at a flat rate, which is the one motion that looks like nothing.

    Not a decorator, unlike the events: the function it takes is a setter that
    receives each value along the way, not a handler that runs once.
    """
    return current_engine().timers.tween(start, end, duration, setter, ease)


# ---- scenes -----------------------------------------------------------------

def scene(name, fn=None):
    """scene(name, fn), or as a decorator:

        @scene("game")
        def build_game(): ...
    """
    def register(f):
        current_engine().scene(name, f)
        return f
    return register_or_decorate(fn, register)


def go(name, *args):
    current_engine().go(name, *args)


# ---- useful values ------------------------------------------------------

def width():
    return current_engine().width()


def height():
    return current_engine().height()


def center():
    return current_engine().center()


def dt():
    return current_engine().dt()


def mousePos():
    return current_engine().mousePos()


def toWorld(pos_):
    return current_engine().toWorld(pos_)


def setCamPos(pos_):
    current_engine().setCamPos(pos_)


def setCamScale(n):
    current_engine().setCamScale(n)


def shake(n=8):
    current_engine().shake(n)


def play(name, loop=False, paused=False, volume=1.0):
    from .engine import SoundHandle
    engine = current_engine()
    if name not in engine.assets.sounds:
        raise KeyError(f"no sound called {name!r} — loadSound(\"{name}\", ...) first")
    return SoundHandle(engine.assets.sounds[name], loop=loop, paused=paused, volume=volume)


def run():
    """Not part of the Kaplay API — the loop starts on its own once your
    script finishes. Exposed only so 'kaypy run game.py'-style tooling
    (or a script that wants to be explicit) has something to call."""
    current_engine().run()
