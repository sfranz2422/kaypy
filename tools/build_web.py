#!/usr/bin/env python3
"""Moved. This tool now lives at the repo root, as webbuild.py, and takes
one argument:

    python webbuild.py examples/lesson10_levels.py

It works out the assets from the game script itself, builds, and serves
the result — no --assets list and no separate pygbag command to remember.

This file stays behind so existing commands and notes keep working; it
just forwards everything to webbuild.py.
"""
import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

print("note: tools/build_web.py has moved to webbuild.py at the repo root.")
print(f"      running it for you: python webbuild.py {' '.join(sys.argv[1:])}\n")

sys.argv[0] = str(REPO_ROOT / "webbuild.py")
runpy.run_path(str(REPO_ROOT / "webbuild.py"), run_name="__main__")
