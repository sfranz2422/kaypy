"""say() and ask() — a panel over a paused game.

    say("You found the key!")
    ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)

Both pause the game, put a panel over it, take the answer, and start the game
again. While a panel is up it owns the keyboard and the mouse, so the game
underneath cannot be played by accident through it.

WHY THE CONTENT IS STRUCTURED AND NOT HTML

This is the one design decision the rest of the file follows from. A panel is
described as text, choices and links — never as markup — because kaypy runs
in two places that share nothing:

    python game.py      a pygame window. There is no DOM. None.
    a web page          a canvas, and a whole browser around it.

Structured content can be rendered by both: as real HTML over the canvas in a
browser, where the text is selectable and a link is a real <a>; and drawn with
pygame on a desktop, where a link opens the system browser instead. An
HTML-shaped API would be lovely in one of those places and impossible in the
other, and "the same file runs both places" is the whole of what kaypy is for.

The cost is real and worth stating: you cannot put arbitrary markup in a
panel. Text, a link, and a question is what there is.

WHY IT CALLS YOU BACK INSTEAD OF RETURNING AN ANSWER

    answer = ask("2 + 2?")        # NOT how this works

In a browser, Python runs on the same thread as everything else the page
does. Waiting there for a click would stop the page — including the click
being waited for — so the tab would hang, not pause. On a desktop the same
line would work fine, which is the worst kind of difference between the two:
one that only shows up in front of a class.

So the answer arrives in a function, which is the shape the rest of kaypy
already uses for anything that happens later:

    @ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
    def checked(correct):
        if correct:
            door.destroy()

WHAT THE FUNCTION IS GIVEN

    say(...)                    nothing
    ask(..., answer=...)        True or False — was it right?
    ask(...) with no answer=    what they picked or typed, as a string

Which of the last two you get is decided by whether you passed `answer=`,
and nothing else. A function that takes no arguments is fine in every case.
"""
from __future__ import annotations

import sys
import webbrowser

import pygame

# The panel currently up, or None, and the ones waiting behind it.
#
# ONE AT A TIME, BUT NONE THROWN AWAY
#
# Only one panel is ever on screen: two at once would have to decide which
# owns the keyboard, and there is no answer to that a beginner would enjoy
# discovering. So a second panel opened while one is up waits its turn.
#
# It used to be closed instead, on the assumption that a panel goes away
# because somebody answered it. That holds when you call ask() from inside a
# handler, and it is false for the most obvious way to write a quiz:
#
#     @ask("What is your name?")
#     def greeted(reply): ...
#
#     @ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
#     def checked(correct): ...
#
# Both decorators run as the file is read, microseconds apart and long before
# anyone can answer anything. The first panel was created and immediately
# discarded by the second, so only the second question was ever asked and
# `greeted` never ran — with nothing printed and nothing raised to say so.
_current = None
_queue = []


def _engine():
    from .engine import current_engine
    return current_engine()


class Panel:
    """What is on screen, and what to do with the answer.

    Deliberately dumb: it holds the content and the state, and knows nothing
    about how it is drawn. The two renderers (this file's _DesktopView and
    webpanel.py's DOM one) read it and do the rest.
    """

    def __init__(self, text, choices=None, answer=None, link=None,
                 button="OK", placeholder=None, then=None, asks=False):
        self.text = str(text)
        self.choices = list(choices) if choices else None
        self.answer = answer
        self.link = link                 # (label, url) or None
        self.button = button
        self.placeholder = placeholder or ""
        self.then = then

        #: Is this a question? Set by ask(), false for say().
        #
        # WHY THIS IS RECORDED RATHER THAN WORKED OUT
        #
        # Both renderers used to decide what a panel looks like from the only
        # thing they could see — whether it had choices:
        #
        #     if p.choices:  ...buttons...
        #     else:          ...a text box...
        #
        # A say() has no choices, exactly like a short-answer ask(), so it got
        # the short-answer layout: a real text field, which the player could
        # type into, and whose contents finish() then threw away, because a
        # say() handler is called with nothing. On the desktop the hint under
        # it even read "Type your answer, then press Enter." On a message.
        #
        # Two renderers guessing the same thing from the same missing fact is
        # not a rendering bug twice, it is one missing field. So the panel
        # says what it is, and nobody has to infer it.
        self.asks = asks

        self.typed = ""                  # short-answer box
        self.hover = -1                  # which choice the mouse is over
        self.done = False

    # ---- what the answer means ------------------------------------------

    def _is_correct(self, chosen_index, chosen_text):
        """Was that right? None when the panel never claimed to have a right
        answer, which is different from being wrong."""
        if self.answer is None:
            return None
        if self.choices is not None:
            if isinstance(self.answer, int):
                return chosen_index == self.answer
            # A string answer against choices: match the text, so a teacher
            # can write answer="for" instead of counting from zero.
            return _same(chosen_text, self.answer)
        if isinstance(self.answer, (list, tuple, set)):
            return any(_same(chosen_text, a) for a in self.answer)
        return _same(chosen_text, self.answer)

    def finish(self, chosen_index=None, chosen_text=None):
        """Close the panel and hand the answer to the callback."""
        if self.done:
            return
        self.done = True
        close()

        if self.then is None:
            return

        # A say() has nothing to hand over. That used to be inferred from
        # three negatives — no choices, no answer, nothing typed — which was
        # the same guess the renderers were making, in a third place.
        if not self.asks:
            _call(self.then, None)
            return

        correct = self._is_correct(chosen_index, chosen_text)
        value = chosen_text if correct is None else correct
        _call(self.then, value)


def _same(a, b):
    """Two short answers that mean the same thing.

    Case and outside spaces are ignored, because "Paris", "paris " and
    " Paris" are the same answer from a fourteen-year-old and marking one of
    them wrong teaches nothing about the subject.
    """
    return str(a).strip().lower() == str(b).strip().lower()


def _call(fn, value):
    """Call the callback with the answer, or with nothing if it takes none.

    A handler that ignores the answer is common and reasonable — `say()` has
    none to give, and plenty of ask() handlers only care that the panel
    closed. Requiring an unused parameter would be noise.
    """
    if value is None:
        try:
            return fn()
        except TypeError:
            return fn(None)
    try:
        return fn(value)
    except TypeError:
        return fn()


# ------------------------------------------------------------ the API

def say(text, link=None, button="OK", then=None):
    """Pause the game and show a message.

        say("You found the key!")
        say("I built this in 2023.", link=("See the repo", "https://..."))

    `link` is a (label, url) pair. In a browser it is a real link; on a
    desktop it opens your browser.
    """
    def straight(fn):
        _show(Panel(text, link=link, button=button, then=fn, asks=False))
        return fn

    if then is not None:
        return straight(then)
    if callable(text):
        raise TypeError("say() needs some words: say(\"Well done!\")")

    # The panel goes up now, because `say("Saved!")` on its own is a
    # statement and has to show something. If a decorator follows, it gives
    # this panel its handler rather than opening a second one.
    #
    # It used to open a second one. That was invisible while a new panel
    # closed whatever was already up — the duplicate replaced the original
    # and looked like one panel. With panels queueing instead, `@say("Hi")`
    # showed "Hi" twice, and the bug had been there all along.
    shown = Panel(text, link=link, button=button, then=None, asks=False)
    _show(shown)

    def attach(fn):
        shown.then = fn
        return fn

    return attach


def ask(question, choices=None, answer=None, placeholder=None, then=None):
    """Pause the game and ask something.

        @ask("Which keyword starts a loop?", ["if", "for", "def"], answer=1)
        def checked(correct):
            ...

        @ask("What is your name?")
        def greeted(reply):
            ...

    With `choices`, it is multiple choice; without, it is a box to type in.
    With `answer`, your function is told True or False; without, it is given
    what was picked or typed.
    """
    def register(fn):
        _show(Panel(question, choices=choices, answer=answer,
                    placeholder=placeholder, then=fn, asks=True))
        return fn

    if then is not None:
        return register(then)
    return register


def isShowing():
    """Is a panel up right now?"""
    return _current is not None


def close():
    """Take the panel away and start the game again.

    Rarely called by hand — answering does it — but a panel that cannot be
    closed from code is one a game can get stuck behind.
    """
    global _current
    if _current is None:
        return
    _current = None
    view = _views.pop("view", None)
    if view is not None:
        view.destroy()

    # The next one, if anybody is waiting. The game stays paused between
    # them: resuming for a frame and pausing again would flash the game
    # behind the panels, which reads as a bug.
    if _queue:
        _present(_queue.pop(0))
        return

    eng = _safe_engine()
    if eng is not None:
        eng.resume()


_views = {}


def _safe_engine():
    try:
        return _engine()
    except Exception:                                          # noqa: BLE001
        return None


def _show(panel):
    """Put a panel up, or get in line behind the one that is."""
    if _current is not None:
        _queue.append(panel)
        return
    _present(panel)


def _present(panel):
    global _current
    eng = _engine()
    _current = panel
    eng.pause()
    _views["view"] = _make_view(panel)


def _make_view(panel):
    """The renderer for wherever this is running."""
    if sys.platform == "emscripten":
        from . import webpanel
        return webpanel.DomView(panel)
    return _DesktopView(panel)


# ------------------------------------------------------- the desktop view

PAD = 18
LINE = 26
CHOICE_H = 34


class _DesktopView:
    """The panel, drawn with pygame.

    Plain rectangles and text on purpose: this has to look deliberate at
    800x600 on a projector, and anything fancier is another thing to go wrong
    in front of a class.
    """

    def __init__(self, panel):
        self.panel = panel
        self.rects = []          # (pygame.Rect, index) for the choices
        self.link_rect = None
        self.button_rect = None

    def destroy(self):
        self.rects = []

    # ---- input ----------------------------------------------------------

    def handle(self, events):
        p = self.panel
        for e in events:
            if e.type == pygame.KEYDOWN:
                self._key(e)
            elif e.type == pygame.MOUSEMOTION:
                p.hover = self._choice_at(e.pos)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._click(e.pos)

    def _key(self, e):
        p = self.panel
        if p.choices:
            # 1, 2, 3... as well as clicking. A keyboard answer is faster for
            # a whole class and works on a machine with no mouse.
            if pygame.K_1 <= e.key <= pygame.K_9:
                i = e.key - pygame.K_1
                if i < len(p.choices):
                    p.finish(i, p.choices[i])
            return
        # A say() has no box, so there is nothing to type into. Enter still
        # closes it — that is the button.
        if not p.asks:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                p.finish(None, None)
            return
        # A short answer: type into it.
        if e.key == pygame.K_RETURN:
            p.finish(None, p.typed)
        elif e.key == pygame.K_BACKSPACE:
            p.typed = p.typed[:-1]
        elif e.unicode and e.unicode.isprintable():
            p.typed += e.unicode

    def _click(self, point):
        p = self.panel
        if self.link_rect and self.link_rect.collidepoint(point):
            _open_link(p.link[1])
            return
        i = self._choice_at(point)
        if i >= 0:
            p.finish(i, p.choices[i])
            return
        if self.button_rect and self.button_rect.collidepoint(point):
            p.finish(None, p.typed if p.asks and p.choices is None else None)

    def _choice_at(self, point):
        for rect, i in self.rects:
            if rect.collidepoint(point):
                return i
        return -1

    # ---- drawing --------------------------------------------------------

    def draw(self, screen, engine):
        p = self.panel
        sw, sh = screen.get_size()
        font = engine._get_font(24)
        small = engine._get_font(20)

        lines = _wrap(p.text, font, int(sw * 0.7) - PAD * 2)
        body_h = len(lines) * LINE
        rows = len(p.choices) if p.choices else 1
        box_w = int(sw * 0.7)
        box_h = PAD * 3 + body_h + rows * CHOICE_H + (LINE if p.link else 0)
        box = pygame.Rect((sw - box_w) // 2, (sh - box_h) // 2, box_w, box_h)

        # Dim the game rather than hide it: the point of pausing instead of
        # changing scene is that the player can still see where they were.
        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        screen.blit(veil, (0, 0))

        pygame.draw.rect(screen, (250, 250, 252), box, border_radius=10)
        pygame.draw.rect(screen, (60, 70, 90), box, width=2, border_radius=10)

        y = box.top + PAD
        for line in lines:
            screen.blit(font.render(line, True, (20, 24, 34)), (box.left + PAD, y))
            y += LINE

        self.rects = []
        self.link_rect = None
        self.button_rect = None

        if p.choices:
            for i, choice in enumerate(p.choices):
                r = pygame.Rect(box.left + PAD, y, box_w - PAD * 2, CHOICE_H - 6)
                over = (p.hover == i)
                pygame.draw.rect(screen, (225, 238, 225) if over else (240, 242, 246),
                                 r, border_radius=6)
                pygame.draw.rect(screen, (80, 150, 60) if over else (200, 206, 214),
                                 r, width=2, border_radius=6)
                label = "%d.  %s" % (i + 1, choice)
                screen.blit(small.render(label, True, (20, 24, 34)),
                            (r.left + 10, r.top + 6))
                self.rects.append((r, i))
                y += CHOICE_H
        elif p.asks:
            # A short answer: a box to type in.
            r = pygame.Rect(box.left + PAD, y, box_w - PAD * 2, CHOICE_H - 6)
            pygame.draw.rect(screen, (255, 255, 255), r, border_radius=6)
            pygame.draw.rect(screen, (120, 140, 170), r, width=2, border_radius=6)
            shown = p.typed or p.placeholder
            colour = (20, 24, 34) if p.typed else (150, 158, 170)
            screen.blit(small.render(shown + ("|" if p.typed else ""), True, colour),
                        (r.left + 10, r.top + 6))
            self.button_rect = r
            y += CHOICE_H
        else:
            # A message: one button, and nothing to fill in.
            label = p.button or "OK"
            text_w = small.size(label)[0]
            r = pygame.Rect(box.left + PAD, y, text_w + 36, CHOICE_H - 6)
            pygame.draw.rect(screen, (80, 150, 60), r, border_radius=6)
            screen.blit(small.render(label, True, (255, 255, 255)),
                        (r.left + 18, r.top + 6))
            self.button_rect = r
            y += CHOICE_H

        if p.link:
            label, _url = p.link
            surf = small.render(label, True, (40, 90, 200))
            pos = (box.left + PAD, y)
            screen.blit(surf, pos)
            self.link_rect = pygame.Rect(pos, surf.get_size())
            pygame.draw.line(screen, (40, 90, 200),
                             (pos[0], pos[1] + surf.get_height()),
                             (pos[0] + surf.get_width(), pos[1] + surf.get_height()))
            y += LINE

        if p.choices:
            hint = "Click an answer, or press its number."
        elif p.asks:
            hint = "Type your answer, then press Enter."
        else:
            hint = "Press Enter, or click %s." % (p.button or "OK")
        screen.blit(small.render(hint, True, (110, 118, 132)),
                    (box.left + PAD, box.bottom - LINE))


def _open_link(url):
    """Open a link from a panel.

    On a desktop this hands the URL to the system browser. On the web the DOM
    view uses a real <a> and never reaches here.
    """
    try:
        webbrowser.open(url)
    except Exception:                                          # noqa: BLE001
        # A machine with no browser configured, or a locked-down account.
        # Not worth ending a game over.
        print("Could not open %s" % url, file=sys.stderr)


def _wrap(text, font, width):
    """Break text into lines that fit, on spaces."""
    out = []
    for para in str(text).split("\n"):
        words, line = para.split(), ""
        for word in words:
            trial = (line + " " + word).strip()
            if font.size(trial)[0] <= width or not line:
                line = trial
            else:
                out.append(line)
                line = word
        out.append(line)
    return out or [""]


# ------------------------------------------------- what the engine calls

def handle_events(events):
    """Give the panel the input. True if it took it."""
    view = _views.get("view")
    if _current is None or view is None:
        return False
    view.handle(events)
    return True


def draw(screen, engine):
    """Draw the panel over everything else, if there is one."""
    view = _views.get("view")
    if _current is None or view is None:
        return
    if hasattr(view, "draw"):
        view.draw(screen, engine)


def reset():
    """Forget any panel. Called when a new engine starts, so a panel cannot
    outlive the game that opened it — which is exactly what happens in a
    browser IDE, where the page stays and the game is run again.

    The queue goes with it. A question still waiting from the last run is not
    a question about this one."""
    global _current
    view = _views.pop("view", None)
    if view is not None:
        try:
            view.destroy()
        except Exception:                                      # noqa: BLE001
            pass
    _current = None
    _queue.clear()
