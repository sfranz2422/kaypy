"""The `kaypy` command.

    kaypy new mygame      make a folder with a working game and its assets
    kaypy web game.py     build that game as a web page and serve it

Both exist because a pip install has no repo to stand in. `kaypy new` is
what gets a student from `pip install kaypy` to something moving on
screen without hunting for sprite files, and `kaypy web` is the same
build tool the checkout calls `webbuild.py`.
"""
from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

STARTER = Path(__file__).resolve().parent / "starter"

# ---------------------------------------------------------------- sounds
# The three lesson sounds are 2.6 MB, and they used to sit inside the wheel.
# That made every `pip install kaypy` anywhere in the world 1.36 MB, of which
# 92 KB was the engine and the rest was mostly one background.wav — paid for
# by everybody, used by the one lesson that plays audio.
#
# So they are fetched when a game folder is made, and the install stays small.
# Everything a game needs to *run* still ships in the package: the starter
# game, every sprite, the dungeon atlas. The starter game plays no sound at
# all, so a failed fetch costs a student nothing until Lesson 8, and
# `kaypy sounds` picks them up later.
SOUNDS = ("background.wav", "ding.wav", "screech.wav")
SOUND_URL = ("https://raw.githubusercontent.com/sfranz2422/kaypy/"
             "{ref}/examples/sounds/{name}")
SOUND_TIMEOUT = 30


def _sound_refs():
    """Which refs to fetch from, most specific first.

    Pinning to the release tag means an old kaypy keeps fetching the assets it
    was published with, rather than whatever main happens to hold. Both `v0.2.0`
    and `0.2.0` are tried because the tag is whatever the GitHub release is
    called, and the publish workflow accepts either — it compares
    `${GITHUB_REF_NAME#v}` against pyproject's version, so the `v` is optional
    there and would be easy to leave off here by accident.

    `main` is last, and is what actually answers today for a version whose tag
    does not exist. A miss costs one 404 and nothing else.
    """
    try:
        from importlib.metadata import version
        v = version("kaypy")
        return ["v" + v, v, "main"]
    except Exception:
        return ["main"]


def fetch_sounds(dest: Path, quiet: bool = False):
    """Download the lesson sounds into dest/sounds/. Never raises.

    Returns (fetched, missing) so the caller can say something useful. A
    student on a school network that blocks GitHub gets a clear sentence and a
    game that still runs, not a traceback.
    """
    import urllib.error
    import urllib.request

    out = dest / "sounds"
    out.mkdir(parents=True, exist_ok=True)
    fetched, missing = [], []

    for name in SOUNDS:
        target = out / name
        if target.is_file() and target.stat().st_size > 0:
            fetched.append(name)
            continue
        for ref in _sound_refs():
            try:
                url = SOUND_URL.format(ref=ref, name=name)
                with urllib.request.urlopen(url, timeout=SOUND_TIMEOUT) as r:
                    data = r.read()
                if not data:
                    continue
                # Write beside, then move: a half-written wav that looks like a
                # real file is worse than no file, because the next run skips it.
                tmp = target.with_suffix(target.suffix + ".part")
                tmp.write_bytes(data)
                tmp.replace(target)
                fetched.append(name)
                break
            except (urllib.error.URLError, OSError, ValueError):
                continue
        else:
            missing.append(name)

    if not quiet:
        if fetched and not missing:
            print("Fetched %d sounds (%.1f MB)."
                  % (len(fetched),
                     sum((out / n).stat().st_size for n in fetched) / 1e6))
        elif missing:
            print("Could not fetch %s — no internet, or GitHub is blocked here."
                  % ", ".join(missing))
            print("The game still runs; it plays no sound. When you reach the "
                  "audio lesson, run:  kaypy sounds " + dest.name)
    return fetched, missing


def cmd_new(args) -> int:
    dest = Path(args.name).resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"{dest} already exists and isn't empty — pick another name, "
              f"or delete it first.")
        return 1
    if not STARTER.is_dir():
        print("this kaypy install has no starter files in it, which shouldn't "
              "happen — reinstall, or copy a game from the project's examples/.")
        return 1

    shutil.copytree(
        STARTER, dest, dirs_exist_ok=True,
        # `sounds` is listed for the benefit of a working copy, not a pip
        # install: the wheel has no such directory, but a clone from before
        # the sounds moved out still does, and copying 2.6 MB of it would
        # quietly undo the point of fetching them.
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "sounds"),
    )

    here = Path.cwd()
    try:
        shown = dest.relative_to(here)
    except ValueError:
        shown = dest

    print(f"Created {shown}/ — a game, and the sprites to build on.\n")
    fetch_sounds(dest)
    print("\nTry it:\n")
    print(f"    cd {shown}")
    print("    python game.py\n")
    print("Arrow keys to move, space to jump. Then open game.py and change it.")
    print(f"To put it on the web instead:  kaypy web game.py")
    return 0


def cmd_sounds(args) -> int:
    """Fetch the lesson sounds into a game folder that hasn't got them.

    Its own command because the fetch during `kaypy new` can fail for reasons
    that have nothing to do with the student — a school network, a flaky
    morning — and the answer to that should be one short command, not a
    reinstall.
    """
    dest = Path(args.folder).resolve()
    if not dest.is_dir():
        print(f"No folder at {dest} — make one first with:  kaypy new "
              f"{Path(args.folder).name}")
        return 1
    _, missing = fetch_sounds(dest)
    return 1 if missing else 0


def cmd_web(args) -> int:
    from . import webbuild
    # webbuild parses its own arguments, so hand it the ones meant for it.
    sys.argv = ["kaypy web"] + args.rest
    webbuild.main()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="kaypy",
        description="kaypy — a real-Python game engine with Kaplay's API.",
    )
    sub = parser.add_subparsers(dest="command")

    p_new = sub.add_parser("new", help="create a new game folder, ready to run")
    p_new.add_argument("name", help="folder to create, e.g. mygame")
    p_new.set_defaults(func=cmd_new)

    p_sounds = sub.add_parser(
        "sounds", help="fetch the lesson sounds into an existing game folder")
    p_sounds.add_argument("folder", nargs="?", default=".",
                          help="the game folder (default: this one)")
    p_sounds.set_defaults(func=cmd_sounds)

    p_web = sub.add_parser(
        "web", help="build a game as a web page and serve it",
        add_help=False,
    )
    p_web.add_argument("rest", nargs=argparse.REMAINDER,
                       help="the game file, plus any webbuild options")
    p_web.set_defaults(func=cmd_web)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
