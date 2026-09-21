#!/usr/bin/env python3
"""Turn a kaypy game into a web page, in one command.

    python webbuild.py examples/lesson10_levels.py

The implementation lives in the package itself, as kaplay/webbuild.py, so
that it also ships with `pip install kaypy` — where the same tool is
spelled `kaypy web game.py`. This file just calls it, so working from a
checkout needs no install.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kaplay.webbuild import main  # noqa: E402

if __name__ == "__main__":
    main()
