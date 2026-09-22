"""Input handling: onKeyDown (held, every frame) / onKeyPress (once per
press) / onKeyRelease (once per release), onClick (anywhere), and the
plain per-frame onUpdate / tagged onUpdate("tag", action)."""
import pygame
from .callutil import call_flexible

_LETTERS = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"

# Built lazily, on first use, rather than at module import time.
#
# Native pygame-ce's pygame.K_LEFT and friends are plain constants, there the
# moment you `import pygame` and before pygame.init() ever runs. A WASM build
# of pygame need not be: one of them (pygbag 0.9.3's) did not populate them
# until after init(). `import kaypy` reaches this module — via engine.py's
# `from .events import EventManager` — long before a script's own kaplay()
# call gets as far as pygame.init(), so building the map eagerly here crashed
# every web export with `AttributeError: module 'pygame' has no attribute
# 'K_LEFT'` before a single line of the game script ran.
#
# kaypy no longer builds through pygbag, and the browser build it uses now
# does define them early. The laziness stays anyway: it costs nothing, it
# makes the module's import order its own business rather than a property of
# whichever WASM pygame is underneath, and tests/test_lazy_key_map.py holds
# it. resolve_key()/key_name() are only ever called from
# on_key_down/on_key_press/on_key_release (registered after kaplay() runs) or
# from the frame loop (which only starts after kaplay() runs), so building on
# first call is always safe.
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


# pygame numbers mouse buttons 1, 2, 3 with MIDDLE in the middle, which is not
# the order anyone guesses. Names are what a student writes and what KAPLAY's
# documentation says, so names are what this takes.
_BUTTONS = {"left": 1, "middle": 2, "right": 3}
_BUTTON_NAMES = {code: name for name, code in _BUTTONS.items()}


def resolve_button(name) -> int:
    """A mouse button name to pygame's number. Defaults to the left one."""
    if name is None:
        return _BUTTONS["left"]
    key = str(name).lower()
    if key not in _BUTTONS:
        raise KeyError(
            f"unknown mouse button {name!r} — use 'left', 'right' or 'middle'")
    return _BUTTONS[key]


def button_name(code: int) -> str:
    return _BUTTON_NAMES.get(code, str(code))


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

        self.mouse_down_handlers = []      # (button, fn)
        self.mouse_press_handlers = []     # (button, fn)
        self.mouse_release_handlers = []   # (button, fn)
        self.mouse_move_handlers = []
        self.draw_handlers = []

        # Edge state, rebuilt every frame in process_pygame_events. A press
        # and a release both last exactly one frame, which is what makes
        # isMousePressed() answerable at all — "is it down" is a question SDL
        # can answer any time, "did it just go down" is not.
        self._pressed_now = set()
        self._released_now = set()
        self._moved_now = False
        self._delta = (0, 0)

    def clear(self):
        self.key_down_handlers.clear()
        self.collide_tag_handlers.clear()
        self.key_press_handlers.clear()
        self.key_release_handlers.clear()
        self.click_handlers.clear()
        self.update_handlers.clear()
        self.mouse_down_handlers.clear()
        self.mouse_press_handlers.clear()
        self.mouse_release_handlers.clear()
        self.mouse_move_handlers.clear()
        self.draw_handlers.clear()

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

    # ---- mouse ---------------------------------------------------------
    #
    # onClick() was the whole mouse API for a long time, and it is enough for
    # "click the button" and nothing else. Aiming at the cursor, dragging a
    # piece, holding to charge, drawing a line — every one of those needs to
    # know which button is down *now*, or that the mouse moved, and had no way
    # to ask.
    #
    # Button names, not numbers, to match KAPLAY: `"left"`, `"right"`,
    # `"middle"`. pygame numbers them 1, 2, 3 with middle in the middle, which
    # is a detail nobody should have to remember.

    def on_mouse_down(self, button, fn):
        self.mouse_down_handlers.append((resolve_button(button), fn))
        return fn

    def on_mouse_press(self, button, fn):
        self.mouse_press_handlers.append((resolve_button(button), fn))
        return fn

    def on_mouse_release(self, button, fn):
        self.mouse_release_handlers.append((resolve_button(button), fn))
        return fn

    def on_mouse_move(self, fn):
        self.mouse_move_handlers.append(fn)
        return fn

    def on_update(self, *args):
        if len(args) == 1:
            self.update_handlers.append((None, args[0]))
            return args[0]
        tag, fn = args
        self.update_handlers.append((tag, fn))
        return fn

    def process_pygame_events(self, pg_events, objs):
        # A press and a release are true for exactly one frame. Clearing them
        # here, before this frame's events are read, is what makes that so —
        # forget it and isMousePressed() stays true until the next click,
        # which looks like a game that fires twice.
        self._pressed_now.clear()
        self._released_now.clear()
        self._moved_now = False
        self._delta = (0, 0)

        for e in pg_events:
            if e.type == pygame.KEYDOWN:
                for code, fn in self.key_press_handlers:
                    if code == e.key:
                        call_flexible(fn, key_name(code))
            elif e.type == pygame.KEYUP:
                for code, fn in self.key_release_handlers:
                    if code == e.key:
                        call_flexible(fn, key_name(code))
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self._pressed_now.add(e.button)
                for button, fn in self.mouse_press_handlers:
                    if button == e.button:
                        call_flexible(fn, button_name(e.button))
                # onClick and obj.onClick are the left button only, which is
                # what they have always meant and what KAPLAY means by them.
                if e.button == _BUTTONS["left"]:
                    for fn in self.click_handlers:
                        call_flexible(fn)
                    for obj in objs:
                        if (obj.exists() and obj.has("area")
                                and "click" in obj._event_handlers
                                and obj.comp("area").isHovering()):
                            obj._fire("click")
            elif e.type == pygame.MOUSEBUTTONUP:
                self._released_now.add(e.button)
                for button, fn in self.mouse_release_handlers:
                    if button == e.button:
                        call_flexible(fn, button_name(e.button))
            elif e.type == pygame.MOUSEMOTION:
                self._moved_now = True
                # Accumulated, not overwritten: SDL can deliver several
                # motion events in one frame, and a handler that saw only the
                # last one would under-report a fast drag.
                self._delta = (self._delta[0] + e.rel[0],
                               self._delta[1] + e.rel[1])
                for fn in self.mouse_move_handlers:
                    call_flexible(fn)

        pressed = pygame.key.get_pressed()
        for code, fn in self.key_down_handlers:
            if pressed[code]:
                call_flexible(fn, key_name(code))

        if self.mouse_down_handlers:
            held = pygame.mouse.get_pressed(num_buttons=3)
            for button, fn in self.mouse_down_handlers:
                if held[button - 1]:
                    call_flexible(fn, button_name(button))

    # ---- what a game can ask about the mouse right now -----------------

    def is_mouse_down(self, button=None):
        try:
            return bool(pygame.mouse.get_pressed(num_buttons=3)
                        [resolve_button(button) - 1])
        except (pygame.error, IndexError):
            return False

    def is_mouse_pressed(self, button=None):
        return resolve_button(button) in self._pressed_now

    def is_mouse_released(self, button=None):
        return resolve_button(button) in self._released_now

    def is_mouse_moved(self):
        return self._moved_now

    def mouse_delta(self):
        return self._delta

    def run_update_handlers(self, objs):
        for tag, fn in self.update_handlers:
            if tag is None:
                call_flexible(fn)
            else:
                for obj in objs:
                    if obj.exists() and obj.is_(tag):
                        call_flexible(fn, obj)
