"""setData() and getData(): something that is still there next time.

    best = getData("best_score", 0)

    if score > best:
        setData("best_score", score)

A high score that survives closing the game is the difference between a
project a student shows someone once and a project they play again. It is
also the first time most of them meet the idea that a program can have
memory beyond its own run, which is worth a lesson on its own.

WHERE IT ACTUALLY GOES

On a desktop, a file called `kaypy-data.json` next to the game script. A plain
JSON file, deliberately: a student can open it, read it, and see their own
score in it — and delete it when they want to start over. A hidden file in an
application-support directory would be tidier and would teach nothing.

In a browser, the page's localStorage, keyed by the game's name. That is the
same place KAPLAY puts it.

WHEN IT CANNOT WRITE

It gives up quietly and says so once. A read-only folder, a browser with
storage disabled, a private window — none of those are a reason for a game to
crash, and a student who cannot save a high score still has a game. What it
never does is pretend: getData() after a failed setData() returns what was
really stored, not what someone hoped was.
"""
from __future__ import annotations

import json
import os
import sys

FILENAME = "kaypy-data.json"

_cache = None        # the loaded dict, or None before the first read
_complained = False  # so a failure is reported once, not every frame


def _web():
    return sys.platform == "emscripten"


def _storage_key():
    """What a browser files this game's data under.

    The script's own name, so two games served from one origin — which is
    exactly what a school's editor does — do not overwrite each other's
    scores.
    """
    main = sys.modules.get("__main__")
    name = os.path.basename(getattr(main, "__file__", "") or "game")
    return "kaypy:" + (os.path.splitext(name)[0] or "game")


def _path():
    """The file beside the game script, on a desktop."""
    main = sys.modules.get("__main__")
    where = getattr(main, "__file__", None)
    folder = os.path.dirname(os.path.abspath(where)) if where else os.getcwd()
    return os.path.join(folder, FILENAME)


def _warn(what, err):
    global _complained
    if _complained:
        return
    _complained = True
    print(f"note: could not {what} ({type(err).__name__}: {err}). "
          f"The game carries on; scores just will not be remembered.")


def _load():
    global _cache
    if _cache is not None:
        return _cache

    _cache = {}
    try:
        if _web():
            import js

            raw = js.localStorage.getItem(_storage_key())
            if raw:
                _cache = json.loads(str(raw))
        elif os.path.isfile(_path()):
            with open(_path()) as f:
                _cache = json.load(f)
    except Exception as err:                               # noqa: BLE001
        # Includes a corrupt file. Starting from empty beats refusing to run:
        # the worst case is a lost high score, and the best case is a game
        # that stops being broken as soon as it saves again.
        _warn("read your saved data", err)
        _cache = {}

    if not isinstance(_cache, dict):
        _cache = {}
    return _cache


def _save():
    try:
        if _web():
            import js

            js.localStorage.setItem(_storage_key(), json.dumps(_cache))
        else:
            with open(_path(), "w") as f:
                json.dump(_cache, f, indent=1)
                f.write("\n")
        return True
    except Exception as err:                               # noqa: BLE001
        _warn("save your data", err)
        return False


def setData(key, value):
    """Remember something under a name. Returns True if it was written."""
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        raise TypeError(
            f"setData({key!r}, ...) can only save numbers, text, True/False, "
            f"None, and lists or dicts of those — not {type(value).__name__}. "
            f"A game object cannot be saved; save what you need from it."
        ) from None

    _load()[str(key)] = value
    return _save()


def getData(key, default=None):
    """What was remembered under that name, or `default` if nothing was."""
    return _load().get(str(key), default)


def _reset_for_tests():
    """Forget the cache, so a test can point at a different folder."""
    global _cache, _complained
    _cache = None
    _complained = False
