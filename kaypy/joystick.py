"""An on-screen d-pad and buttons, for playing with a thumb.

    kaypy(width=800, height=600, joystick=True)

That is the whole change. The overlay pretends to be the keyboard: touching
the d-pad is exactly as if `left` were held, and the buttons are `space` and
`z`. Every game already written — every lesson in the guide — becomes
playable on a phone without a line of it changing.

WHY IT PRETENDS TO BE KEYS RATHER THAN HAVING ITS OWN API

Because an API nobody has called yet is an API no existing game supports. A
`joystickDir()` would be more honest about what this is, and would mean every
game needed rewriting before a student could play it on the bus. Firing the
same handlers the keyboard fires means the thirteen lessons, the starter, and
whatever a class wrote last week all work on touch immediately.

The cost is that a game cannot tell a thumb from a keyboard. That seems a
small price, and mostly a feature.

WHY IT IS DRAWN ON THE CANVAS AND NOT BUILT OUT OF HTML

Unlike a panel — which is words to read, a link to follow and a box to type
in, all things a browser does far better than a canvas — a d-pad is a picture
you put your thumb on. There is nothing to select, nothing to read aloud,
nothing to zoom. Drawing it means it works identically in a browser and in a
window on a desktop, from one piece of code, and it sits inside the game's
own coordinates so it scales with the canvas for free.

MULTI-TOUCH, AND WHY IT IS NOT OPTIONAL

A platformer needs run and jump at the same time. Tracked by mouse position
alone there is one pointer, so holding right and pressing jump would release
right — which makes exactly the games this is for unplayable. So fingers are
tracked individually by their own ids, and the mouse is treated as one more
finger so the thing can still be tried on a laptop.
"""
from __future__ import annotations

import pygame

from .events import resolve_key

#: What the two action buttons send when nothing else is asked for. `space`
#: because that is what every lesson in the guide jumps with; `z` because it
#: is reachable on a keyboard too, so a game built for touch is still
#: playable on a laptop without remapping anything.
DEFAULT_BUTTONS = ("space", "z")

#: The mouse, as a finger. Real finger ids come from SDL and are arbitrary
#: integers, so this is a value they will not collide with.
MOUSE_FINGER = "mouse"


class Joystick:
    """The overlay: where it is, what is held, and how to draw it."""

    def __init__(self, width, height, buttons=None):
        self.screen_w = width
        self.screen_h = height

        if buttons is None:
            buttons = DEFAULT_BUTTONS
        elif isinstance(buttons, str):
            buttons = (buttons,)
        self.button_keys = tuple(buttons)

        # Sized off the screen so it is thumb-sized on a phone and not
        # comical on a projector. Clamped because a very small canvas would
        # otherwise end up with a d-pad bigger than the game.
        base = max(48, min(120, int(min(width, height) * 0.22)))
        self.pad_r = base
        self.btn_r = int(base * 0.42)
        margin = int(base * 0.45)

        self.pad_centre = (margin + self.pad_r, height - margin - self.pad_r)

        # The action buttons, bottom right, offset from each other so a thumb
        # can reach both without covering either.
        bx = width - margin - self.btn_r
        by = height - margin - self.btn_r
        self.buttons = []
        for i, key in enumerate(self.button_keys):
            cx = bx - i * int(self.btn_r * 2.4)
            cy = by - (0 if i % 2 == 0 else int(self.btn_r * 1.1))
            self.buttons.append({"key": key, "centre": (cx, cy),
                                 "label": key[:1].upper()})

        # finger id -> the set of key codes that finger is holding.
        self._fingers = {}
        # Key codes held by any finger, as of this frame.
        self.held = set()

    # ---- what is under a point ------------------------------------------

    def _dirs_at(self, x, y):
        """Which directions a point on the d-pad means.

        A ring, split into eight. Diagonals hold two keys at once, because a
        thumb between up and right means up and right — anything else makes a
        platformer feel broken in a way players cannot describe.
        """
        cx, cy = self.pad_centre
        dx, dy = x - cx, y - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > self.pad_r * 1.15:
            return set()
        # A dead zone in the middle, so resting a thumb there is not "left".
        if dist < self.pad_r * 0.28:
            return set()

        out = set()
        if abs(dx) > self.pad_r * 0.22:
            out.add("right" if dx > 0 else "left")
        if abs(dy) > self.pad_r * 0.22:
            out.add("down" if dy > 0 else "up")
        return out

    def _button_at(self, x, y):
        for b in self.buttons:
            cx, cy = b["centre"]
            if (x - cx) ** 2 + (y - cy) ** 2 <= (self.btn_r * 1.2) ** 2:
                return b["key"]
        return None

    def _keys_at(self, x, y):
        keys = set(self._dirs_at(x, y))
        b = self._button_at(x, y)
        if b:
            keys.add(b)
        return keys

    # ---- input ------------------------------------------------------------

    def handle(self, events, post):
        """Take the frame's events. `post` is called with (key_code, down)
        for each change, so the engine can fire onKeyPress / onKeyRelease."""
        for e in events:
            kind = e.type
            if kind == pygame.FINGERDOWN:
                self._set(e.finger_id, self._at_normalised(e), post)
            elif kind == pygame.FINGERMOTION:
                self._set(e.finger_id, self._at_normalised(e), post)
            elif kind == pygame.FINGERUP:
                self._set(e.finger_id, set(), post)
            elif kind == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._set(MOUSE_FINGER, self._keys_at(*e.pos), post)
            elif kind == pygame.MOUSEMOTION and e.buttons and e.buttons[0]:
                self._set(MOUSE_FINGER, self._keys_at(*e.pos), post)
            elif kind == pygame.MOUSEBUTTONUP and e.button == 1:
                self._set(MOUSE_FINGER, set(), post)

    def _at_normalised(self, e):
        """Finger events carry 0..1 across the window, not pixels."""
        return self._keys_at(e.x * self.screen_w, e.y * self.screen_h)

    def _set(self, finger, key_names, post):
        codes = set()
        for name in key_names:
            try:
                codes.add(resolve_key(name))
            except Exception:                                  # noqa: BLE001
                pass

        was = self._fingers.get(finger, set())
        if codes:
            self._fingers[finger] = codes
        else:
            self._fingers.pop(finger, None)

        after = set()
        for held in self._fingers.values():
            after |= held

        # Only the edges are announced. A key held across two frames must not
        # fire onKeyPress twice — that is the difference between a jump and a
        # double jump nobody asked for.
        for code in after - self.held:
            post(code, True)
        for code in self.held - after:
            post(code, False)
        self.held = after

    def release_all(self, post):
        """Let go of everything. Used when the overlay goes away, so a key
        cannot be left stuck down with nothing holding it."""
        self._fingers.clear()
        for code in list(self.held):
            post(code, False)
        self.held = set()

    # ---- drawing ----------------------------------------------------------

    def draw(self, screen, engine):
        w, h = screen.get_size()
        if (w, h) != (self.screen_w, self.screen_h):
            # The canvas can be resized under us in a browser.
            self.__init__(w, h, self.button_keys)

        layer = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = self.pad_centre

        pygame.draw.circle(layer, (255, 255, 255, 40), (cx, cy), self.pad_r)
        pygame.draw.circle(layer, (255, 255, 255, 90), (cx, cy), self.pad_r, 3)

        # The four directions, lit when held, so a player can see what the
        # game thinks their thumb is doing.
        arm = int(self.pad_r * 0.62)
        for name, dx, dy in (("left", -1, 0), ("right", 1, 0),
                             ("up", 0, -1), ("down", 0, 1)):
            try:
                lit = resolve_key(name) in self.held
            except Exception:                                  # noqa: BLE001
                lit = False
            colour = (120, 220, 120, 210) if lit else (255, 255, 255, 110)
            tip = (cx + dx * arm, cy + dy * arm)
            side = int(self.pad_r * 0.20)
            a = (cx + dx * side - dy * side, cy + dy * side - dx * side)
            b = (cx + dx * side + dy * side, cy + dy * side + dx * side)
            pygame.draw.polygon(layer, colour, [tip, a, b])

        font = engine._get_font(int(self.btn_r * 1.1))
        for btn in self.buttons:
            bx, by = btn["centre"]
            try:
                lit = resolve_key(btn["key"]) in self.held
            except Exception:                                  # noqa: BLE001
                lit = False
            pygame.draw.circle(layer, (120, 220, 120, 190) if lit
                               else (255, 255, 255, 55), (bx, by), self.btn_r)
            pygame.draw.circle(layer, (255, 255, 255, 120), (bx, by),
                               self.btn_r, 3)
            label = font.render(btn["label"], True, (20, 24, 34) if lit
                                else (255, 255, 255))
            layer.blit(label, (bx - label.get_width() // 2,
                               by - label.get_height() // 2))

        screen.blit(layer, (0, 0))
