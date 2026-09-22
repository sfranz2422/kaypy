#!/usr/bin/env python3
"""Turn a kaypy game into a web page, in one command.

    kaypy web game.py          (or: python webbuild.py game.py, in a checkout)

The result is **one HTML file**. Double-click it and the game plays: no
server, nothing installed, nothing unzipped. Upload that single file to
itch.io, email it, put it on a school share — it is the whole game.

    kaypy web game.py
    -> web_build/game.html   (420 KB, say)

WHAT IS INSIDE IT

The engine, the program, and every picture and sound the script names, all
inlined. The script is read rather than run to work out which assets it uses,
so nothing is carried that the game never loads.

Pyodide brings a Python interpreter and an in-memory filesystem, so the page
writes the engine and the assets into that filesystem as real files before the
program starts. `import kaypy` is then an ordinary import and
`pygame.image.load("images/bean.png")` opens an ordinary file — which is why
the program goes in byte for byte, with no paths rewritten. The page itself is
kaypy/web_page.html; it is worth reading if you want the details.

THE ONE THING IT FETCHES

Pyodide and pygame-ce, from a CDN, on first run. So the first load of a built
game wants an internet connection and takes a few seconds while Python starts;
the browser caches both afterwards. pygame-ce cannot be embedded even in
principle — it is a compiled C extension and has to be the interpreter's own
build of it.

WHAT THIS REPLACED

Until now this ran pygbag, which produces a *folder*: an index.html that
fetches a .apk archive at run time, plus a tarball and a favicon. That works
when a web server is serving it, and not at all when someone double-clicks the
index.html, because a file:// page is not allowed to read the file next to it.
So a student who built a game could not open their own game without first
starting a web server.

Three dependencies went with it: pygbag itself, ffmpeg (pygbag's build step
rejects .wav outright, so every sound had to be converted to .ogg first), and
a build-time download of a WASM runtime from pygame-web.github.io.

Useful flags, none of them usually needed:

    --serve         also start a local server and print a URL, for testing
                    across a network or in a browser that dislikes file://
    --port 9000     which port to serve on (default: 8000)
    --assets a b    carry these too, for files the script doesn't name
                    outright (a path built at runtime, say)
    --out FILE      write somewhere other than web_build/<name>.html
    --title "..."   the browser tab's title (default: the script's name)
"""
from __future__ import annotations
import argparse
import ast
import base64
import json
import re
import socket
import subprocess
import sys
from pathlib import Path

# Where the engine itself lives. Under `pip install kaypy` this is inside
# site-packages, not a repo checkout, which is why it is resolved from this
# module rather than from a project directory.
PKG_DIR = Path(__file__).resolve().parent
PAGE_TEMPLATE = PKG_DIR / "web_page.html"

PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v314.0.6/full/"

# What counts as an asset worth carrying when it shows up as a string in the
# game script.
ASSET_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",
    ".wav", ".ogg", ".mp3", ".flac",
    ".ttf", ".otf", ".json",
}

# Files inside the package that the browser has no use for. `starter/` is what
# `kaypy new` hands a desktop user and would otherwise add megabytes of sprites
# to every build, whether or not the game loads any of them.
SKIP_DIRS = {"starter", "__pycache__"}


def default_out_file(stem: str) -> Path:
    return Path.cwd() / "web_build" / (stem + ".html")


# ---------------------------------------------------------------- assets

def find_assets(game_script: Path) -> list[str]:
    """Every asset the script names, as the script spells it.

    Reads the file rather than running it, and picks up any string literal
    that looks like an asset path — which covers loadSprite's single path, its
    list-of-frames form, loadSpriteAtlas's sheet and loadSound, without this
    needing to know about any of them. Paths are kept exactly as written
    ("images/bean.png", not an absolute path), because that spelling is what
    the script passes to loadSprite at run time, and the copy has to land
    where the script will look for it.
    """
    try:
        tree = ast.parse(game_script.read_text(), filename=str(game_script))
    except SyntaxError as exc:
        raise SystemExit(f"{game_script} doesn't parse as Python: {exc}")

    base = game_script.parent
    found: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        spelled = node.value
        if Path(spelled).suffix.lower() not in ASSET_SUFFIXES:
            continue
        if spelled in found:
            continue
        if not (base / spelled).is_file():
            continue
        if ".." in Path(spelled).parts or Path(spelled).is_absolute():
            print(f"note: skipping {spelled} — only paths inside the script's own "
                  f"folder can be carried; pass it with --assets if you need it")
            continue
        found.append(spelled)
    return found


# ------------------------------------------------------------- the engine

def engine_files() -> dict[str, str]:
    """The kaypy package, as {path inside the package: source}.

    Text, not bytes: every file in it is Python. The page writes each one
    into Pyodide's filesystem so that a traceback through the engine names
    kaypy/engine.py and a line number that exists, rather than pointing at
    some string that was exec'd.
    """
    files: dict[str, str] = {}
    for path in sorted(PKG_DIR.rglob("*.py")):
        rel = path.relative_to(PKG_DIR)
        if set(rel.parts) & SKIP_DIRS:
            continue
        files[str(rel).replace("\\", "/")] = path.read_text()
    return files


# ------------------------------------------------------------- the page

def _js(value) -> str:
    """A JavaScript literal that cannot end the <script> block it sits in.

    The HTML parser stops a script block at the first `</script`, wherever it
    appears — inside a string literal, inside a comment, anywhere. It does not
    know it is reading JavaScript. `<\\/` is identical to `</` in JavaScript
    and invisible to the parser, so escaping it costs nothing and removes a
    whole class of failure: a game whose engine silently spills onto the page
    as visible text.
    """
    return json.dumps(value).replace("</", "<\\/")


def build_page(game_script: Path, extra_assets: list[Path], title: str | None,
               size: tuple[int, int] = (800, 600)) -> tuple[str, list[str]]:
    """The whole game, as one HTML document."""
    if not PAGE_TEMPLATE.is_file():
        raise SystemExit(
            f"the page template is missing from the installed package "
            f"({PAGE_TEMPLATE}). A broken install — try `pip install "
            f"--force-reinstall kaypy`."
        )

    used = find_assets(game_script)
    assets: dict[str, str] = {}
    for spelled in used:
        assets[spelled] = base64.b64encode(
            (game_script.parent / spelled).read_bytes()).decode("ascii")

    for src in extra_assets:
        if not src.exists():
            print(f"warning: --assets path {src} does not exist, skipping")
            continue
        for path in ([src] if src.is_file() else sorted(p for p in src.rglob("*") if p.is_file())):
            rel = path.name if src.is_file() else str(
                Path(src.name) / path.relative_to(src)).replace("\\", "/")
            assets[rel] = base64.b64encode(path.read_bytes()).decode("ascii")
            if rel not in used:
                used.append(rel)

    slots = {
        "__TITLE__": (title or game_script.stem).replace("&", "&amp;")
                                                .replace("<", "&lt;")
                                                .replace(">", "&gt;"),
        "__WIDTH__": str(size[0]),
        "__HEIGHT__": str(size[1]),
        "__PYODIDE__": PYODIDE_CDN,
        "__ENGINE__": _js(engine_files()),
        "__ASSETS__": _js(assets),
        "__PROGRAM__": _js(game_script.read_text()),
    }

    page = PAGE_TEMPLATE.read_text()
    missing = [name for name in slots if name not in page]
    if missing:
        raise SystemExit("the page template has no %s slot — "
                         "kaypy/web_page.html and this file disagree."
                         % ", ".join(missing))

    # ONE pass, not one replace() per slot.
    #
    # The engine carries this very file, and this very file contains the
    # literal text "__ASSETS__" a few lines up. Filling the slots one at a
    # time put the engine in first and then went looking for "__ASSETS__"
    # again — finding the mention inside webbuild.py's own source and
    # replacing it with the game's assets, halfway through a Python string
    # inside a JSON string. The page still looked plausible and the JSON no
    # longer parsed.
    #
    # A single pass cannot do that: what goes in is never looked at again.
    return re.sub("|".join(slots), lambda m: slots[m.group(0)], page), used


def read_size(game_script: Path) -> tuple[int, int]:
    """The width and height the script asks kaplay() for.

    Only so the canvas starts at the right size instead of resizing visibly on
    the first frame. Read off the syntax tree, never run; anything it cannot
    work out (a variable, a computed value) falls back to kaypy's own default,
    which is what the engine would use anyway.
    """
    width, height = 800, 600
    try:
        tree = ast.parse(game_script.read_text())
    except SyntaxError:
        return width, height
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "kaplay"):
            for kw in node.keywords:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
                    if kw.arg == "width":
                        width = kw.value.value
                    elif kw.arg == "height":
                        height = kw.value.value
    return width, height


# ---------------------------------------------------------------- serve

def pick_port(preferred: int) -> int:
    for port in range(preferred, preferred + 10):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit(f"ports {preferred}-{preferred + 9} are all busy — pass --port")


def serve(page: Path, preferred_port: int):
    """Serve the built file, for the cases where opening it directly won't do.

    Opening the file is the normal way — it is one document and it fetches
    nothing but Python. A server is still worth having for two cases: trying
    the game on a phone or another machine on the same network, and browsers
    or extensions configured to treat file:// pages harshly.
    """
    port = pick_port(preferred_port)
    print("\n" + "=" * 62)
    print(f"  Your game is running at:  http://127.0.0.1:{port}/{page.name}")
    print("=" * 62)
    print("\nPress Ctrl-C here when you're done.\n")
    try:
        subprocess.run(
            [sys.executable, "-m", "http.server", str(port),
             "--directory", str(page.parent)],
            check=False,
        )
    except KeyboardInterrupt:
        pass
    print(f"\nServer stopped. Your game is still at:\n    {page}")


# ----------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("game_script", type=Path, help="the kaypy game .py file to put on the web")
    ap.add_argument("--out", type=Path, default=None,
                    help="output file [default: web_build/<game script name>.html]")
    ap.add_argument("--title", default=None, help="the browser tab's title")
    ap.add_argument("--assets", nargs="*", type=Path, default=[],
                    help="extra files/folders to carry, for assets the script doesn't spell out")
    ap.add_argument("--serve", action="store_true",
                    help="also start a local server and print a URL")
    ap.add_argument("--port", type=int, default=8000,
                    help="port for --serve [default: 8000]")
    args = ap.parse_args(argv)

    game_script = args.game_script.resolve()
    if not game_script.is_file():
        raise SystemExit(f"no such game script: {game_script}")

    out = (args.out or default_out_file(game_script.stem)).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    page, used = build_page(game_script, [p.resolve() for p in args.assets],
                            args.title, read_size(game_script))
    out.write_text(page)

    print(f"Built {game_script.name} as one file:\n    {out}")
    print(f"    {len(page) / 1024:.0f} KB, including {len(used)} asset"
          f"{'' if len(used) == 1 else 's'}")
    if used:
        print(f"    carried: {', '.join(used)}")
    else:
        print("    no asset files named in the script — if it does load some, "
              "pass --assets")

    if args.serve:
        serve(out, args.port)
        return 0

    print("\nDouble-click it to play. The first run needs the internet, for")
    print("Python itself; after that the browser has it cached.")
    print("To publish: upload that one file to itch.io as an HTML project.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
