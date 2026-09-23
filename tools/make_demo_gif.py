#!/usr/bin/env python3
"""Build docs/demo.gif — the code on the left, what it does on the right.

    python3 tools/make_demo_gif.py

WHY THIS IS GENERATED RATHER THAN SCREEN-RECORDED

A screen recording of a browser carries a mouse pointer, a scrollbar, a tab
strip and whatever the window manager felt like drawing that day, and it has
to be re-made by hand every time the program in it changes. This renders the
frames instead: the game half is real kaypy, stepped by hand and captured
off the surface it actually drew, and the code half is the same source file
run through the same syntax highlighter the website uses. Re-run it and you
get the same GIF, which means it can be regenerated when the API moves
rather than slowly becoming a picture of an old version.

WHAT IT SHOWS

The program types itself in, then runs. Thirteen lines and a character that
falls, lands and jumps — which is the actual claim the project makes, made
in about five seconds without asking anybody to read anything.
"""
from __future__ import annotations

import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame                                                     # noqa: E402
from PIL import Image                                             # noqa: E402
from PIL import ImageDraw, ImageFont                              # noqa: E402
from pygments import lex                                          # noqa: E402
from pygments.lexers import PythonLexer                           # noqa: E402
from pygments.token import Token                                  # noqa: E402

OUT = ROOT / "docs" / "demo.gif"

# The program on screen. Kept to what fits without scrolling, and it is a
# real file: tools/demo_program.py runs it, so this cannot drift into
# something that no longer works.
SOURCE = (ROOT / "tools" / "demo_program.py").read_text().rstrip("\n")

W, H = 980, 420
GAME_W, GAME_H = 360, 300
PAD = 26
CODE_W = W - GAME_W - PAD * 3

BG = (22, 27, 36)
PANEL = (21, 27, 36)
EDGE = (54, 66, 79)
DIM = (169, 182, 196)

# The website's own dark palette, so the GIF and the docs agree.
COLORS = {
    Token.Keyword: (217, 139, 209),
    Token.Name.Builtin: (111, 197, 197),
    Token.Name.Function: (74, 134, 212),
    Token.Name.Decorator: (232, 167, 96),
    Token.String: (143, 217, 94),
    Token.Number: (232, 167, 96),
    Token.Comment: (134, 148, 163),
    Token.Operator: (169, 182, 196),
    Token.Punctuation: (169, 182, 196),
}
INK = (238, 243, 248)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def ink_for(tok):
    while tok is not None:
        if tok in COLORS:
            return COLORS[tok]
        tok = tok.parent
    return INK


def coloured_lines(source):
    """[[(text, colour), ...], ...] — one list per line."""
    lines, current = [], []
    for tok, text in lex(source, PythonLexer()):
        colour = ink_for(tok)
        while "\n" in text:
            head, text = text.split("\n", 1)
            if head:
                current.append((head, colour))
            lines.append(current)
            current = []
        if text:
            current.append((text, colour))
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------ the game
def game_frames(count):
    """Run the program on screen, and photograph what it draws.

    It RUNS the file rather than rebuilding it here. The first version of
    this function set the scene up itself, and immediately drifted: it added
    two platforms and walked the bean along them, neither of which appeared
    in the code beside it. A demo whose code does not produce the picture
    next to it is a lie told at four hundred frames a second, and it would
    have drifted again the moment either half was edited.

    So the only thing added from outside is the spacebar, which is exactly
    what a person would be doing.
    """
    import runpy
    import kaypy.engine as ke

    os.chdir(ROOT / "examples")
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
        ke._engine = None

    scope = runpy.run_path(str(ROOT / "tools" / "demo_program.py"),
                           run_name="__main__")
    eng = ke._engine
    player = scope["player"]

    shots = []
    for n in range(count):
        # Press space every so often, once the bean has landed. A real
        # KEYDOWN through the real event path, so the @onKeyPress handler in
        # the program is what does the jumping.
        if n > 22 and n % 22 == 0:
            eng.events.process_pygame_events(
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE,
                                    mod=0, unicode=" ", scancode=44)],
                eng._objs)

        eng._dt = 1 / 60
        eng.events.run_update_handlers(eng._objs)
        for obj in list(eng._objs):
            if obj.exists():
                for comp in list(obj._comps.values()):
                    comp.update(obj)
        steps = eng.physics.substeps_for(eng._objs, eng._dt)
        for _ in range(steps):
            eng.physics.step(eng._objs, eng._dt / steps)
            eng.collision.step(eng._objs)
        for obj in list(eng._objs):
            if obj.exists():
                for comp in list(obj._comps.values()):
                    if comp.wants_late:
                        comp.late_update(obj)

        eng.screen.fill(eng._background)
        eng.render.draw(eng._objs, eng.screen, eng.camera, False,
                        eng.events.draw_handlers)
        raw = pygame.image.tobytes(eng.screen, "RGB")
        shots.append(Image.frombytes("RGB", (GAME_W, GAME_H), raw))

    if not any(s.tobytes() != shots[0].tobytes() for s in shots[1:]):
        sys.exit("Nothing moved in %d frames — the GIF would be a still "
                 "picture of a game engine, which is worse than none." % count)
    return shots


# ------------------------------------------------------------ the frame
def compose(lines_shown, chars_shown, game_img, font, small, bold):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((PAD, 18), "game.py", font=bold, fill=DIM)

    code_box = (PAD, 46, PAD + CODE_W, H - 22)
    d.rounded_rectangle(code_box, 10, fill=PANEL, outline=EDGE)

    y = 62
    for i, line in enumerate(LINES):
        if i > lines_shown:
            break
        x = PAD + 16
        budget = chars_shown if i == lines_shown else None
        for text, colour in line:
            if budget is not None:
                if budget <= 0:
                    break
                text = text[:budget]
                budget -= len(text)
            d.text((x, y), text, font=font, fill=colour)
            x += d.textlength(text, font=font)
        if i == lines_shown and budget is not None and budget > 0:
            d.rectangle((x, y + 2, x + 8, y + 16), fill=(143, 217, 94))
        y += 19

    gx = PAD * 2 + CODE_W
    gy = (H - GAME_H) // 2 + 6
    d.rounded_rectangle((gx - 6, gy - 6, gx + GAME_W + 6, gy + GAME_H + 6),
                        10, fill=PANEL, outline=EDGE)
    if game_img is None:
        d.text((gx + GAME_W // 2 - 52, gy + GAME_H // 2 - 8),
               "press Run", font=small, fill=DIM)
    else:
        img.paste(game_img, (gx, gy))
    d.text((gx - 6, 18), "what it does", font=bold, fill=DIM)
    return img


font = ImageFont.truetype(FONT_PATH, 14)
small = ImageFont.truetype(FONT_PATH, 14)
bold = ImageFont.truetype(FONT_BOLD, 13)
LINES = coloured_lines(SOURCE)

# Both of these are measured rather than judged by eye. The first version
# of this file had two lines running off the right-hand edge of the panel,
# which is invisible in the source and obvious in the picture.
if len(LINES) > 18:
    sys.exit("demo_program.py is %d lines; more than 18 will not fit in the "
             "code panel without scrolling." % len(LINES))

_probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
_room = CODE_W - 32
for _n, _line in enumerate(SOURCE.splitlines(), 1):
    _wide = _probe.textlength(_line, font=font)
    if _wide > _room:
        sys.exit("line %d of demo_program.py is %.0fpx wide and the code "
                 "panel is %dpx.\n    %s\n  Shorten the line, or widen the "
                 "frame." % (_n, _wide, _room, _line))

frames = []

# 1. It types itself in, four characters at a time.
for i, line in enumerate(LINES):
    width_of = sum(len(t) for t, _ in line)
    if width_of == 0:
        frames.append(compose(i, 0, None, font, small, bold))
        continue
    for taken in range(0, width_of + 1, 7):
        frames.append(compose(i, taken, None, font, small, bold))

# 2. A beat with the whole program on screen.
frames += [compose(len(LINES), 10 ** 6, None, font, small, bold)] * 8

# 3. And it runs.
shots = game_frames(118)
for shot in shots:
    frames.append(compose(len(LINES), 10 ** 6, shot, font, small, bold))

OUT.parent.mkdir(parents=True, exist_ok=True)
first, rest = frames[0], frames[1:]
first.save(OUT, save_all=True, append_images=rest, optimize=True,
           duration=50, loop=0)

size = OUT.stat().st_size
print("docs/demo.gif — %d frames, %dx%d, %.1f MB"
      % (len(frames), W, H, size / 1e6))
print("  %d typing, 8 holding, %d playing" % (len(frames) - 8 - len(shots),
                                              len(shots)))
if size > 8e6:
    print("\n  That is large for a README. Drop the frame count or the size.")
