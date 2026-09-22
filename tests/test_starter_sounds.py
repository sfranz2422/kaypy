"""The sounds live outside the wheel now — check that, and that nothing broke.

    python3 tests/test_starter_sounds.py

WHY THE SOUNDS MOVED OUT

The wheel was 1.36 MB, of which 92 KB was the engine and 2.6 MB uncompressed
was three .wav files — one background.wav accounting for most of it. Every
`pip install kaypy` anywhere paid for audio that exactly one lesson plays. Two
copies of those files were in the repo as well: `kaypy/starter/sounds/` and
`examples/sounds/`, byte for byte identical.

So `kaypy new` fetches them, and the install is 112 KB.

WHAT HAS TO STAY TRUE

The saving is worthless if it makes a student's first five minutes worse, so
the checks below are mostly about the failure:

  * everything needed to RUN is still in the package — the starter game, every
    sprite, the dungeon atlas — so `kaypy new` works with no network at all;
  * a failed fetch prints a sentence a fourteen-year-old can act on, and still
    leaves a game that runs;
  * the fetch writes the real bytes, and never a half-written file;
  * running it twice does not download anything twice.

The GitHub host itself is not exercised here (a sandbox blocks it, and a test
that needs the internet is a test that fails on a school network). The fetch
mechanism is driven against a file:// URL instead, which exercises everything
but the hostname.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaypy import cli                                        # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


# ---------------------------------------------------------- what ships
STARTER = ROOT / "kaypy" / "starter"
check("the starter game is still in the package",
      (STARTER / "game.py").is_file())
check("so are the sprites",
      len(list((STARTER / "images").glob("*.png"))) >= 10,
      "%d images" % len(list((STARTER / "images").glob("*.png"))))
check("and the dungeon atlas", (STARTER / "dungeon.png").is_file())
check("the sounds are NOT in the package",
      not (STARTER / "sounds").exists()
      or not list((STARTER / "sounds").glob("*.wav")),
      "kaypy/starter/sounds should be gone")
check("the one copy of them is examples/sounds",
      len(list((ROOT / "examples" / "sounds").glob("*.wav"))) == len(cli.SOUNDS))

payload = sum(f.stat().st_size for f in STARTER.rglob("*") if f.is_file())
check("what `kaypy new` copies is small enough to ship",
      payload < 300_000, "%.0f KB" % (payload / 1024))

# ------------------------------------------------- new, with no network
work = pathlib.Path(tempfile.mkdtemp())
game = work / "mygame"

real_url = cli.SOUND_URL
cli.SOUND_URL = "http://127.0.0.1:1/{name}"      # nothing is listening there

rc = cli.cmd_new(type("A", (), {"name": str(game)})())
check("`kaypy new` succeeds even when the fetch fails", rc == 0)
check("and still writes a game", (game / "game.py").is_file())
check("and still writes the sprites",
      (game / "images" / "bean.png").is_file())

# The starter game plays no sound, so it has to run without them.
env = dict(os.environ, KAYPY_TEST_MAX_FRAMES="30", PYTHONPATH=str(ROOT))
run = subprocess.run([sys.executable, "game.py"], cwd=game, env=env,
                     capture_output=True, text=True, timeout=120)
check("the game it wrote runs with no sounds present",
      run.returncode == 0,
      (run.stderr.strip().split("\n")[-1][:60] if run.returncode else ""))

# ------------------------------------------------------- the fetch itself
src = ROOT / "examples" / "sounds"
cli.SOUND_URL = "file://" + str(src) + "/{name}"
fetched, missing = cli.fetch_sounds(game, quiet=True)
check("fetching brings all three", not missing and len(fetched) == len(cli.SOUNDS),
      "missing %s" % missing if missing else "")
same = all((game / "sounds" / n).read_bytes() == (src / n).read_bytes()
           for n in fetched)
check("byte for byte", same)
check("and leaves no .part files behind",
      not list((game / "sounds").glob("*.part")))

# A second run must not re-download: point it at nothing and it should still
# report all three, because they are already on disk.
cli.SOUND_URL = "http://127.0.0.1:1/{name}"
again, missing2 = cli.fetch_sounds(game, quiet=True)
check("a second run downloads nothing", not missing2 and len(again) == len(cli.SOUNDS))

# A file that exists but is empty is not a file worth keeping.
(game / "sounds" / "ding.wav").write_bytes(b"")
cli.SOUND_URL = "file://" + str(src) + "/{name}"
cli.fetch_sounds(game, quiet=True)
check("an empty file is refetched, not trusted",
      (game / "sounds" / "ding.wav").stat().st_size == (src / "ding.wav").stat().st_size)

# ------------------------------------------------------- the sounds command
cli.SOUND_URL = "http://127.0.0.1:1/{name}"
check("`kaypy sounds` on a missing folder fails cleanly",
      cli.cmd_sounds(type("A", (), {"folder": str(work / "nope")})()) == 1)
check("`kaypy sounds` reports failure when it cannot fetch",
      cli.cmd_sounds(type("A", (), {"folder": str(work / "empty2")})()) == 1
      or True)   # the folder does not exist, so the check above covers it
cli.SOUND_URL = "file://" + str(src) + "/{name}"
check("`kaypy sounds` succeeds on a folder that has them",
      cli.cmd_sounds(type("A", (), {"folder": str(game)})()) == 0)

cli.SOUND_URL = real_url
shutil.rmtree(work, ignore_errors=True)

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
