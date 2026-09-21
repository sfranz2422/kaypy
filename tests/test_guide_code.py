"""Standalone sanity script: every complete program printed in GUIDE.md runs.

The guide is the thing students type from, so a sample that doesn't run is
worse than no sample. This pulls every fenced ```python block out of
GUIDE.md, keeps the ones that are whole programs (they start with
`from kaplay import *`), and actually executes each one against the real
engine, headless, for a few frames.

It exists because of Lesson 10: its player fell through the floor for a
long time while the script still exited 0. "It runs" is a floor, not a
ceiling — but a guide whose code doesn't even run has no floor at all.

Run it from anywhere:

    python tests/test_guide_code.py
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDE = REPO_ROOT / "GUIDE.md"
EXAMPLES = REPO_ROOT / "examples"

BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def complete_programs(markdown: str):
    """Whole programs only — fragments are illustrations, not runnable."""
    for i, block in enumerate(BLOCK_RE.findall(markdown), start=1):
        if block.lstrip().startswith("from kaplay import *"):
            yield i, block


def first_line_of(block: str) -> str:
    for line in block.splitlines():
        line = line.strip()
        if line and not line.startswith(("from ", "#")):
            return line
    return "?"


def main():
    if not GUIDE.is_file():
        raise SystemExit(f"no guide at {GUIDE}")

    env = dict(os.environ)
    env.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYTHONPATH=str(REPO_ROOT),
        KAYPY_TEST_MAX_FRAMES="30",
    )

    programs = list(complete_programs(GUIDE.read_text()))
    if not programs:
        raise SystemExit("found no complete programs in GUIDE.md — did the format change?")

    failures = []
    for index, block in programs:
        # Run from examples/, which is where the guide tells the reader to be,
        # so "images/bean.png" resolves exactly as it will for them.
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", dir=EXAMPLES, delete=False
        ) as fh:
            fh.write(block)
            path = Path(fh.name)
        try:
            result = subprocess.run(
                [sys.executable, path.name],
                cwd=EXAMPLES, env=env, capture_output=True, text=True, timeout=60,
            )
        finally:
            path.unlink(missing_ok=True)

        label = f"block {index:>2} ({first_line_of(block)[:48]})"
        if result.returncode == 0:
            print(f"  ok   {label}")
        else:
            tail = (result.stderr.strip().splitlines() or ["(no stderr)"])[-1]
            print(f"  FAIL {label}\n       {tail}")
            failures.append((index, result.stderr.strip()))

    print()
    if failures:
        print(f"{len(failures)} of {len(programs)} guide programs failed:\n")
        for index, err in failures:
            print(f"--- block {index} ---\n{err}\n")
        raise SystemExit(1)

    print(f"ALL {len(programs)} GUIDE PROGRAMS RAN")


if __name__ == "__main__":
    main()
