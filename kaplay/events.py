"""Input handling: onKeyDown (held, every frame) / onKeyPress (once per
press) / onKeyRelease (once per release), onClick (anywhere), and the
plain per-frame onUpdate / tagged onUpdate("tag", action)."""
import pygame
from .callutil import call_flexible

_LETTERS = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"

# Built lazily, on first use, rather than at module import time: native
# pygame-ce's pygame.K_LEFT etc. are plain constants, available the moment
# you `import pygame`, before pygame.init() ever runs — but pygbag's WASM
# build of pygame apparently doesn't populate them until after init(), and
# `import kaplay` reaches this module (via engine.py's `from .events import
# EventManager`) well before a script's own kaplay() call gets to run
# pygame.init(). Building the map eagerly here crashed every web export
# with `AttributeError: module 'pygame' has no attribute 'K_LEFT'` before a
# single line of the game script ran. resolve_key()/key_name() are only
# ever called from on_key_down/on_key_press/on_key_release (registered
# after kaplay() runs) or from the frame loop (which only starts after
# kaplay() runs), so building on first call is always safe.
_KEY_MAP = None
_REVERSE_KEY_MAP = None


def _ensure_key_maps():
    global _KEY_MAP, _REVERSE_KEY_MAP
    if _KEY_MAP is not None:
        return
    _KEY_MAP = {
        "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
        "up": pygame.K_UP, "down": pygame.K_DOWN,
        "space": pygame.K_SPACE, "enter": pygame.K_RETURN, "return": pygame.K_RETURN,
        "escape": pygame.K_ESCAPE, "tab": pygame.K_TAB,
        "shift": pygame.K_LSHIFT, "ctrl": pygame.K_LCTRL, "control": pygame.K_LCTRL,
        "alt": pygame.K_LALT, "backspace": pygame.K_BACKSPACE,
    }
    for _c in _LETTERS:
        _KEY_MAP[_c] = getattr(pygame, f"K_{_c}")
    for _d in _DIGITS:
        _KEY_MAP[_d] = getattr(pygame, f"K_{_d}")
    _REVERSE_KEY_MAP = {code: name for name, code in _KEY_MAP.items()}


def resolve_key(name: str) -> int:
    _ensure_key_maps()
    key = name.lower()
    if key not in _KEY_MAP:
        raise KeyError(f"unknown key name {name!r}")
    return _KEY_MAP[key]


def key_name(code: int) -> str:
    _ensure_key_maps()
    return _REVERSE_KEY_MAP.get(code, str(code))


class EventManager:
    def __init__(self):
        self.key_down_handlers = []
        # (tag_a, tag_b, fn) — the object-free onCollide, fired by
        # CollisionSystem when a NEW touch begins between two tags.
        self.collide_tag_handlers = []
        self.key_press_handlers = []
        self.key_release_handlers = []
        self.click_handlers = []
        self.update_handlers = []  # (tag_or_None, fn)

    def clear(self):
        self.key_down_handlers.clear()
        self.collide_tag_handlers.clear()
        self.key_press_handlers.clear()
        self.key_release_handlers.clear()
        self.click_handlers.clear()
        self.update_handlers.clear()

    def on_collide_tags(self, tag_a, tag_b, fn):
        self.collide_tag_handlers.append((tag_a, tag_b, fn))
        return fn

    def fire_tag_collision(self, a, b):
        """A new touch between a and b — tell anyone watching for the pair.

        Checked both ways round, so onCollide("bullet", "enemy") fires
        whichever of the two the collision system happened to look at first.
        The handler always gets them in the order the tags were named.
        """
        for tag_a, tag_b, fn in list(self.collide_tag_handlers):
            if a.is_(tag_a) and b.is_(tag_b):
                call_flexible(fn, a, b)
            elif b.is_(tag_a) and a.is_(tag_b):
                call_flexible(fn, b, a)

    def on_key_down(self, key, fn):
        self.key_down_handlers.append((resolve_key(key), fn))
        return fn

    def on_key_press(self, key, fn):
        self.key_press_handlers.append((resolve_key(key), fn))
        return fn

    def on_key_release(self, key, fn):
        self.key_release_handlers.append((resolve_key(key), fn))
        return fn

    def on_click(self, fn):
        self.click_handlers.append(fn)
        return fn

    def on_update(self, *args):
        if len(args) == 1:
            self.update_handlers.append((None, args[0]))
            return args[0]
        tag, fn = args
        self.update_handlers.append((tag, fn))
        return fn

    def process_pygame_events(self, pg_events, objs):
        for e in pg_events:
            if e.type == pygame.KEYDOWN:
                for code, fn in self.key_press_handlers:
                    if code == e.key:
                        call_flexible(fn, key_name(code))
            elif e.type == pygame.KEYUP:
                for code, fn in self.key_release_handlers:
                    if code == e.key:
                        call_flexible(fn, key_name(code))
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for fn in self.click_handlers:
                    call_flexible(fn)
                for obj in objs:
                    if (obj.exists() and obj.has("area")
                            and "click" in obj._event_handlers
                            and obj.comp("area").isHovering()):
                        obj._fire("click")

        pressed = pygame.key.get_pressed()
        for code, fn in self.key_down_handlers:
            if pressed[code]:
                call_flexible(fn, key_name(code))

    def run_update_handlers(self, objs):
        for tag, fn in self.update_handlers:
            if tag is None:
                call_flexible(fn)
            else:
                for obj in objs:
                    if obj.exists() and obj.is_(tag):
                        call_flexible(fn, obj)
