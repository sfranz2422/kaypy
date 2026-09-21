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
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    here = Path.cwd()
    try:
        shown = dest.relative_to(here)
    except ValueError:
        shown = dest

    print(f"Created {shown}/ — a game, and the sprites and sounds to build on.\n")
    print("Try it:\n")
    print(f"    cd {shown}")
    print("    python game.py\n")
    print("Arrow keys to move, space to jump. Then open game.py and change it.")
    print(f"To put it on the web instead:  kaypy web game.py")
    return 0


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
