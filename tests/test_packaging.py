"""Standalone sanity script: what `pip install kaypy` gives someone works.

A checkout has things an install does not — examples/, webbuild.py, the
whole repo — so it is easy to ship a package that is broken in ways the
repo never shows. This checks the three that actually bit:

  1. The starter assets bundled in the package haven't drifted from the
     ones the lessons use.
  2. `kaypy new` produces a folder whose game runs, with every asset it
     asks for present.
  3. The web builder finds the engine through the package, not through a
     repo path that only exists in a checkout.
"""
import filecmp
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

STARTER = REPO_ROOT / "kaplay" / "starter"
EXAMPLES = REPO_ROOT / "examples"

# The sounds are deliberately not here: they are 2.6 MB against the engine's
# 92 KB, only one lesson plays audio, and every `pip install kaypy` was paying
# for them. `kaypy new` fetches them instead — tests/test_starter_sounds.py
# covers that, including what happens when the fetch fails.
ASSET_DIRS = ["images", "dungeon"]


# --- 1. the bundled copy matches the lessons' copy ----------------------
mismatched, missing = [], []
for sub in ASSET_DIRS:
    for src in sorted((EXAMPLES / sub).glob("*")):
        if not src.is_file():
            continue
        twin = STARTER / sub / src.name
        if not twin.is_file():
            missing.append(f"{sub}/{src.name}")
        elif not filecmp.cmp(src, twin, shallow=False):
            mismatched.append(f"{sub}/{src.name}")

for name in ["dungeon.png", "CREDITS.md"]:
    if not (STARTER / name).is_file():
        missing.append(name)
    elif not filecmp.cmp(EXAMPLES / name, STARTER / name, shallow=False):
        mismatched.append(name)

assert not missing, (
    f"bundled in kaplay/starter/ but missing: {missing} — `kaypy new` would "
    f"produce a game whose assets aren't all there"
)
assert not mismatched, (
    f"kaplay/starter/ has drifted from examples/: {mismatched} — the copy "
    f"students get is no longer the copy the lessons were checked against"
)

# The sounds are not bundled, so the thing that can drift is the LIST of them
# in the CLI: fetching a name that examples/sounds hasn't got would fail at a
# student's machine and nowhere else.
from kaplay import cli                                        # noqa: E402

on_disk = {p.name for p in (EXAMPLES / "sounds").glob("*.wav")}
assert set(cli.SOUNDS) == on_disk, (
    f"kaypy new fetches {sorted(cli.SOUNDS)} but examples/sounds holds "
    f"{sorted(on_disk)} — one of the two has moved on without the other"
)
assert not (STARTER / "sounds").exists(), (
    "kaplay/starter/sounds is back — that is 2.6 MB inside every wheel again"
)
print(f"confirmed: kaplay/starter assets match examples/ ({len(ASSET_DIRS)} folders + atlas)")


# --- 2. `kaypy new` makes something that runs ---------------------------
from kaplay import cli  # noqa: E402

env = dict(os.environ)
env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
           PYTHONPATH=str(REPO_ROOT), KAYPY_TEST_MAX_FRAMES="20")

with tempfile.TemporaryDirectory() as tmp:
    project = Path(tmp) / "mygame"
    rc = cli.main(["new", str(project)])
    assert rc == 0, "kaypy new returned a failure"
    assert (project / "game.py").is_file(), "kaypy new made no game.py"

    result = subprocess.run(
        [sys.executable, "game.py"],
        cwd=project, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"the scaffolded game doesn't run:\n{result.stderr.strip()[-800:]}"
    )
    print("confirmed: `kaypy new` produces a game that runs")

    # Refusing to overwrite someone's work matters more than convenience.
    assert cli.main(["new", str(project)]) == 1, \
        "kaypy new should refuse a folder that already has files in it"
    print("confirmed: `kaypy new` refuses to overwrite a non-empty folder")


# --- 3. the web builder resolves the engine through the package ---------
from kaplay import webbuild  # noqa: E402

assert (webbuild.KAPLAY_PKG / "engine.py").is_file(), (
    f"webbuild looks for the engine in {webbuild.KAPLAY_PKG}, which has no "
    f"engine.py — an install would copy the wrong thing, or nothing"
)
assert webbuild.KAPLAY_PKG.name == "kaplay", \
    f"expected the package directory, got {webbuild.KAPLAY_PKG}"

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "build"
    webbuild.assemble(STARTER / "game.py", [], out)
    assert (out / "kaplay" / "engine.py").is_file(), "engine missing from the build"
    assert (out / "main.py").is_file(), "generated main.py missing from the build"
    leaked = list((out / "kaplay").rglob("starter"))
    assert not leaked, (
        f"the starter assets were copied into the web build ({leaked}) — that's "
        f"megabytes of sprites in every export, most of them unused"
    )
    print("confirmed: web builds use the installed engine, without the starter assets")

print("ALL PACKAGING CHECKS PASSED")
