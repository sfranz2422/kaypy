"""Running a kaypy game inside a web page.

This is what a built web page calls. It is a real module in the package,
rather than a few lines of Python living inside an HTML template, for three
reasons: it can be tested (tests/test_webrun.py), a traceback through it names
a file that exists, and the page that a browser IDE builds and the page that
`kaypy web` builds can call exactly the same code instead of each carrying
their own slightly different copy.

THE TWO HALVES

A game runs in two steps, and keeping them apart is the whole design:

    run(source)      the program's top level, once, top to bottom
    await drive()    the frame loop, until the game ends

`run` is what `python game.py` does before atexit fires: kaplay() builds the
engine, everything after it registers handlers, and then it returns — with the
game built and not yet moving. `drive` sets it going.

They are separate so that a mistake in the setup is reported as a mistake in
the setup, with the student's own traceback, instead of arriving tangled up in
whatever the frame loop happened to be doing sixty times a second.

WHY THE TRACEBACK IS TRIMMED

An error in a game reaches Python with this module, asyncio and the engine
stacked above the one line the student wrote. Printed whole, the line that
matters is somewhere in the middle of twenty, and the first thing a beginner
reads is a frame inside `kaypy/engine.py` — which reliably produces "I think
the engine is broken" rather than "I think I made a mistake". So frames
belonging to Python itself, to asyncio and to kaypy are dropped, and what is
left is the student's own program.

The engine's frames are kept when there are no others, because an error raised
inside the engine with nothing of the student's on the stack is a kaypy bug
and hiding it would be dishonest.
"""
from __future__ import annotations

import builtins
import linecache
import os
import sys
import traceback
import types

#: The name a game's own code is compiled under, and what a traceback calls it.
MAIN = "main.py"


def _own_frame(frame_summary, package_dir):
    """Is this frame the student's own code?"""
    name = frame_summary.filename
    if name == MAIN:
        return True
    # Anything inside the engine, the standard library or asyncio is ours.
    if name.startswith(package_dir):
        return False
    return not (name.startswith("<") or os.sep + "asyncio" + os.sep in name
                or name.startswith(sys.prefix))


def format_error(err):
    """A traceback with the machinery taken out of it.

    Returns the text to print. The exception's own line — `NameError: name
    'plyer' is not defined` — is always the last line, because that is the one
    a student can act on and it should be where they stop reading.
    """
    package_dir = os.path.dirname(os.path.abspath(__file__))
    frames = traceback.extract_tb(err.__traceback__)
    mine = [f for f in frames if _own_frame(f, package_dir)]

    # Nothing of theirs on the stack means this is the engine's fault, and
    # saying so plainly beats printing an empty traceback.
    shown = mine or frames
    out = ["Traceback:"] if mine else [
        "Traceback (this one looks like a bug in kaypy itself):"]
    for f in shown:
        where = ("line %d" % f.lineno if f.filename == MAIN
                 else "%s, line %d" % (os.path.basename(f.filename), f.lineno))
        out.append("  %s, in %s" % (where, f.name))
        if f.line:
            out.append("    " + f.line.strip())
    out.append("%s: %s" % (type(err).__name__, err))
    return "\n".join(out)


def run(source, filename=MAIN):
    """Run a game's top level. Returns "ok" or "error".

    The program gets a real module to live in rather than a bare dict,
    because the handlers it registers go on referring to its globals long
    after this function has returned — a lambda in onKeyDown() is still
    looking things up in there on the four hundredth frame. A dict that went
    out of scope would take them with it.
    """
    try:
        code = compile(source, filename, "exec")
    except SyntaxError as err:
        line = err.lineno or 0
        text = (err.text or "").rstrip()
        message = "SyntaxError on line %d: %s" % (line, err.msg)
        if text:
            message += "\n    " + text.strip()
        print(message, file=sys.stderr)
        return "error"

    # So a traceback can quote the line it is pointing at. The source is not
    # on any disk the browser can see, so linecache has to be told.
    linecache.cache[filename] = (len(source), None, source.splitlines(True), filename)

    module = types.ModuleType("__main__")
    module.__dict__["__builtins__"] = builtins
    module.__file__ = filename
    sys.modules["__main__"] = module

    try:
        exec(code, module.__dict__)
        return "ok"
    except SystemExit:
        return "ok"
    except BaseException as err:                   # noqa: BLE001
        print(format_error(err), file=sys.stderr)
        return "error"


async def drive():
    """Run the frame loop until the game ends. Returns "ok" or "error".

    Awaited, so it does not return until the game is actually over. The page
    can therefore tell the difference between a game that is playing and one
    that has finished, which is what lets it put a "play again" button up
    rather than leaving a dead canvas.
    """
    from . import engine as _engine

    game = _engine._engine
    if game is None:
        print("No game started. A kaypy program needs kaplay() before anything "
              "else — see the guide, or `kaypy new` for a starter.",
              file=sys.stderr)
        return "error"

    try:
        await game.run_async()
        return "ok"
    except BaseException as err:                   # noqa: BLE001
        # An error inside a handler surfaces here, long after the line that
        # registered it. Report it once and stop, rather than sixty identical
        # tracebacks a second.
        game._running = False
        print(format_error(err), file=sys.stderr)
        return "error"
