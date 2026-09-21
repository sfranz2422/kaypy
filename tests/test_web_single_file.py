"""`kaypy web` builds one file, and the game inside it runs.

    python3 tests/test_web_single_file.py

A built game is the one thing kaypy produces that nobody watches fail. It is
built, uploaded or emailed, and opened on someone else's machine with no
console open and nobody to ask. Every way it can go wrong is quiet: an engine
written one directory too deep is an ImportError no one reads; a sprite
written beside the program instead of under its working directory is a blank
page.

So this does not only look at the file. It takes it apart and runs what is
inside it, on real pygame-ce, against real sprite and sound files.

WHAT IS FAITHFUL HERE, AND WHAT IS NOT

Faithful: the page comes from the real builder, and the engine, the assets and
the program are read back out of it rather than re-derived. The two calls the
page makes are the two calls made here. Where the files go is read out of the
page's own source, not decided here — a replay that supplies the answer it is
checking is not a replay.

Not faithful, deliberately:

  * The page writes to /lib and /project. This relocates both into a
    temporary directory, because a test should not need to write to the root
    of the filesystem. That the page uses those paths is checked as text.
  * SDL is on its dummy driver, so nothing here can tell you the game is
    visible. Only a browser can.
  * Pyodide and pygame-ce are fetched by the page at run time. This uses the
    pygame-ce already installed, which is the same library, and never touches
    the network.
"""
import asyncio
import base64
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaplay import webbuild                                     # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def done(code=None):
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(code if code is not None else (1 if bad else 0))


# A program that uses a sprite, a sound, a key, a collision and a timer, so
# that "it ran" means several different things went right rather than one.
GAME = '''from kaplay import *

kaplay(width=320, height=240, background=[24, 24, 40])
loadSprite("bean", "images/bean.png")
loadSound("ding", "sounds/ding.wav")

player = add([sprite("bean"), pos(40, 40), area(), "player"])
coin = add([sprite("bean"), pos(44, 44), area(), "coin"])

seen = []


@onKeyDown("right")
def go_right():
    player.move(120, 0)


@player.onCollide("coin")
def got(c):
    seen.append("coin")
    c.destroy()


@wait(0.2)
def later():
    seen.append("timer")


onUpdate(lambda: seen.append("frame"))
'''

# ------------------------------------------------------------- build one
work = pathlib.Path(tempfile.mkdtemp())
game_dir = work / "mygame"
(game_dir / "images").mkdir(parents=True)
(game_dir / "sounds").mkdir(parents=True)
(game_dir / "game.py").write_text(GAME)

# Real files: a 2x2 PNG and a tenth of a second of silence, made here so the
# test needs no fixtures on disk.
import struct                                                   # noqa: E402
import wave                                                     # noqa: E402
import zlib                                                     # noqa: E402


def tiny_png(path, w=8, h=8):
    raw = b"".join(b"\x00" + bytes([200, 80, 80, 255] * w) for _ in range(h))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b""))


def tiny_wav(path):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(22050)
        f.writeframes(b"\x00\x00" * 2205)


tiny_png(game_dir / "images" / "bean.png")
tiny_wav(game_dir / "sounds" / "ding.wav")

out = work / "game.html"
page, used = webbuild.build_page(game_dir / "game.py", [], "Test Game",
                                 webbuild.read_size(game_dir / "game.py"))
out.write_text(page)

check("it builds one file", out.is_file(), "%.0f KB" % (len(page) / 1024))
check("it is a whole HTML document",
      page.startswith("<!doctype html>") and page.rstrip().endswith("</html>"))
check("the title carries through", "<title>Test Game</title>" in page)
check("the canvas starts at the size the script asks for",
      'width="320" height="240"' in page, "read off kaplay(width=, height=)")
check("it carries exactly the assets the script names",
      sorted(used) == ["images/bean.png", "sounds/ding.wav"], " ".join(sorted(used)))

# ------------------------------------------------ read the values back out
def declared(name):
    """A `var NAME = ...;` the page declares, read by line.

    By line, because a regex across the document runs straight past the end of
    the object — the engine's own source contains "};" inside strings.
    """
    prefix = "var %s = " % name
    for line in page.splitlines():
        if line.startswith(prefix) and line.endswith(";"):
            try:
                return json.loads(line[len(prefix):-1])
            except json.JSONDecodeError as exc:
                raise AssertionError("var %s is not valid JSON: %s" % (name, exc))
    raise AssertionError("the page declares no %s on one line" % name)


try:
    engine = declared("ENGINE")
    assets = declared("ASSETS")
    program = declared("PROGRAM")
    parsed = True
except AssertionError as exc:
    parsed = False
    check("the page's values parse", False, str(exc)[:80])
if not parsed:
    done(1)

check("the page's values parse", True)
check("the engine is the whole package", len(engine) > 20, "%d files" % len(engine))
check("including the runner the page calls", "webrun.py" in engine)
check("and not the starter assets", not any(f.startswith("starter/") for f in engine),
      "those are for `kaypy new`, not the browser")

# The program is not rewritten. That is the whole reason the paths in it can
# stay as the student wrote them.
check("the program is carried byte for byte", program == GAME)
check("so it still names its sprite by path", '"images/bean.png"' in program)

check("the assets are carried as bytes", sorted(assets) == sorted(used))
check("a PNG decodes back to a PNG",
      base64.b64decode(assets["images/bean.png"])[1:4] == b"PNG")
check("a WAV decodes back to a WAV",
      base64.b64decode(assets["sounds/ding.wav"])[:4] == b"RIFF")

# ------------------------------------- the self-referential replacement bug
# The engine carries webbuild.py, whose own source contains the literal text
# "__ASSETS__". Filling the template one slot at a time put the engine in
# first and then replaced that mention too, corrupting a Python string inside
# a JSON string. The page still looked plausible; the JSON no longer parsed.
check("the engine's own source survived being embedded",
      "__ASSETS__" in engine.get("webbuild.py", ""),
      "the slot names in webbuild.py are still the slot names")
# Every line except the one carrying the engine — the engine's own source
# legitimately contains the slot names, and it is embedded JSON-escaped, so it
# cannot be stripped out by matching the raw text.
elsewhere = "\n".join(l for l in page.splitlines()
                      if not l.startswith("var ENGINE = "))
leftover = re.findall(r"__(?:TITLE|WIDTH|HEIGHT|PYODIDE|ENGINE|ASSETS|PROGRAM)__",
                      elsewhere)
check("and no slot was left unfilled", not leftover, ", ".join(leftover))

# ----------------------------------------------------- nothing left to fetch
external = re.findall(r'src="(https?:[^"]+)"', page)
check("the only thing fetched is Pyodide",
      len(external) == 1 and "pyodide" in external[0], ", ".join(external) or "none")
check("and it is fetched over HTTPS", all(u.startswith("https://") for u in external))
check("no asset is left as a URL to fetch",
      not re.search(r'src="(?!https?:)[^"]*\.(png|wav|ogg)"', page))

# --------------------------------------------- nothing shows below the game
# A published game is the game. Anything drawn under the canvas appears inside
# the iframe on itch.io and everywhere else that hosts one HTML file — and the
# first thing it showed was not even the game's doing: `import pygame` greets
# stdout with its version every time, so every export opened with a grey box
# under it reading "pygame-ce 2.5.8 (SDL ...)".
check("the page has no output pane under the canvas",
      'id="log"' not in page and "logEl" not in page)
check("print() goes to the developer console instead",
      "console.log(s)" in page and "setStdout" in page)
check("nothing else is drawn below the canvas",
      page.count("<pre id=") == 1, "only the error pane")

# An error still shows on the page. A blank canvas that explains nothing is
# worse than a red box that does, and the box is hidden until it has something
# to say.
check("an error still has somewhere to appear", 'id="error"' in page)
check("and that somewhere starts hidden",
      re.search(r"#error\s*\{[^}]*display:\s*none", page) is not None)
check("errors accumulate rather than replacing each other",
      "errorEl.textContent +=" in page)

closers = page.count("</script>")
check("exactly two script blocks are closed", closers == 2, "%d closers" % closers)
inline_start = page.index("<script>") + len("<script>")
check("nothing inlined can end a block early",
      "</script" not in page[inline_start:page.index("</script>", inline_start)])

# --------------------------------------------- unpack it, as the page does
# Where things go is read out of the page, not decided here.
asset_dir = re.search(r'writeFile\(py, PROJECT \+ "/" \+ path', page)
engine_dir = re.search(r'writeFile\(py, LIB \+ "/kaplay/" \+ rel', page)
lib_path = re.search(r'var LIB = "([^"]+)"', page)
project_path = re.search(r'var PROJECT = "([^"]+)"', page)
check("the page says where the engine goes", engine_dir and lib_path,
      lib_path.group(1) if lib_path else "")
check("and where the assets go", asset_dir and project_path,
      project_path.group(1) if project_path else "")
if not (asset_dir and engine_dir and lib_path and project_path):
    done(1)

root = work / "root"
lib = root / lib_path.group(1).strip("/")
project = root / project_path.group(1).strip("/")
for rel, text in engine.items():
    target = lib / "kaplay" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
for path, b64 in assets.items():
    target = project / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(base64.b64decode(b64))

check("the engine unpacks into an importable package",
      (lib / "kaplay" / "__init__.py").is_file())
check("the assets land where the program will look",
      (project / "images/bean.png").is_file() and (project / "sounds/ding.wav").is_file())

# ---------------------------------------------------------- and run it
# From the unpacked copy, not from this checkout: the point is that what the
# page carries is enough on its own.
for name in [m for m in sys.modules if m == "kaplay" or m.startswith("kaplay.")]:
    del sys.modules[name]
sys.path.insert(0, str(lib))
os.chdir(project)
os.environ["KAYPY_TEST_MAX_FRAMES"] = "30"

from kaplay import webrun as unpacked_webrun                    # noqa: E402
import kaplay.engine as unpacked_engine                         # noqa: E402

check("the engine imported is the one out of the page",
      pathlib.Path(unpacked_webrun.__file__).is_relative_to(lib),
      pathlib.Path(unpacked_webrun.__file__).parent.name)

status = unpacked_webrun.run(program)
check("the program's top level runs", status == "ok", "status %r" % status)
if status == "ok":
    loop = asyncio.run(unpacked_webrun.drive())
    check("the frame loop runs and ends", loop == "ok", "status %r" % loop)

    seen = getattr(sys.modules.get("__main__"), "seen", None)
    check("the game's update handler ran", seen and "frame" in seen,
          "%d frames" % (seen.count("frame") if seen else 0))
    check("its collision fired, so the sprite really loaded",
          seen and "coin" in seen)

if unpacked_engine._engine is not None:
    unpacked_engine._engine._started = True
    unpacked_engine._engine._running = False
    unpacked_engine._engine = None

# ----------------------------------- an asset the page did not carry
# Must fail by name rather than leaving a blank page.
missing = program.replace("images/bean.png", "images/not_carried.png")
import io                                                       # noqa: E402
err = io.StringIO()
real, sys.stderr = sys.stderr, err
try:
    bad = unpacked_webrun.run(missing)
finally:
    sys.stderr = real
check("a sprite that was not carried fails loudly, by name",
      bad == "error" and "not_carried.png" in err.getvalue(),
      err.getvalue().strip().splitlines()[-1][:58] if err.getvalue() else "silent")

os.chdir(ROOT)
shutil.rmtree(work, ignore_errors=True)
done()
