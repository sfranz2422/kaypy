"""kaypy() must not touch atexit in a browser.

    python3 tests/test_web_platform_guard.py

The rule outlives the reason it was written for. On the web, something else
calls run_async() explicitly — kaypy/webrun.py — and an atexit handler in a
tab whose interpreter never exits is a frame loop that never starts. So
kaypy() checks the platform and skips atexit there, and this proves the check
is really in the code path rather than in a comment about it.

It proves it the harshest way available: under an atexit module where merely
*calling* register() raises. That module is not hypothetical, and the rest of
this docstring is why it is worth keeping now that kaypy no longer builds
through pygbag at all. A test that says "we don't call this" is weak; a test
that says "we don't call this, and here is a version of it that would explode
if we did" is not.

---

Originally: proves kaypy survives pygbag's real (buggy) atexit replacement.

pygbag 0.9.3 ships its own atexit module (support/cross/aio/atexit.py)
that replaces sys.modules["atexit"] wholesale, and whose register()
references an undefined `arg` instead of `args` — calling
atexit.register(...) under it raises NameError immediately.

Import order matters here: in a real pygbag run, that swap (and all of
pygbag's own startup, which uses asyncio/logging plenty) has already
happened by the time YOUR game script's kaypy() call runs — so the
question that actually matters is narrower than "does anything, ever,
call atexit.register after the swap" (stdlib's own `logging` module does
that on its own first import, before kaypy is even involved, and that's
pygbag's problem to have solved for its own runtime to work at all —
plenty of other pygbag games ship fine, so it evidently has). The
question that's actually kaypy's to answer is: once everything is
already imported and the swap has already happened, does kaypy() itself
ever touch atexit? This imports kaypy normally FIRST (so stdlib's own
atexit usage happens against the real atexit, matching real execution
order), then swaps in pygbag's broken module and sets
sys.platform = "emscripten" before calling kaypy(), the way a real
pygbag boot precedes your game script.
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Import kaypy (and therefore asyncio, logging, etc.) FIRST, against the
# real atexit — matching real pygbag execution order, where all of that
# bootstrapping is long done before your game script's kaypy() call runs.
from kaypy import kaypy, add, pos, rect  # noqa: E402
from kaypy.engine import current_engine  # noqa: E402

# --- NOW recreate pygbag's actual buggy atexit shim verbatim ---------------
fake_atexit = types.ModuleType("atexit")


def _register(func, *args, **kwargs):
    # this is pygbag's real bug: `arg` (undefined) instead of `args`
    _register.plan.append((func, arg, kwargs))  # noqa: F821 (deliberately broken, matches upstream)


_register.calls = 0
_orig_register = _register


def _counting_register(func, *args, **kwargs):
    _register.calls += 1
    return _orig_register(func, *args, **kwargs)


_register.plan = []
fake_atexit.register = _counting_register
sys.modules["atexit"] = fake_atexit

real_platform = sys.platform
sys.platform = "emscripten"

try:
    kaypy(width=200, height=200, background=[0, 0, 0])
    assert current_engine().is_web is True, "Engine should detect the emscripten platform"
    add([pos(0, 0), rect(10, 10)])
    assert _register.calls == 0, (
        f"kaypy() called atexit.register() {_register.calls} time(s) under "
        f"sys.platform=='emscripten' — that would crash for real under pygbag"
    )
    print("confirmed: kaypy() never calls atexit.register() once sys.platform is 'emscripten'")
finally:
    sys.platform = real_platform

print("ALL WEB-PLATFORM GUARD CHECKS PASSED")
