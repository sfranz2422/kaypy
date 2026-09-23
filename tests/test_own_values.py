"""A dict in the component list: your own values, on the object.

    python3 tests/test_own_values.py

    add([sprite("bean"), pos(10, 10), {"hits": 0, "dir": 1}])

KAPLAY allows a plain object among the components and merges its keys onto
the game object. This is the same thing in Python.

THE FAILURE THIS GUARDS AGAINST

A key a component already owns. `{"pos": vec2(0, 0)}` next to `pos(10, 10)`
reads like it sets the position; what it actually does is put a plain value
in the object's own `__dict__`, where Python finds it *before* `__getattr__`
ever runs — so the component is still attached, still being updated by the
physics system, and completely unreachable. The object is then half a game
object, and it dies somewhere else entirely.

Which makes ORDER the interesting case: written after `pos()` the clash is
obvious, and written before it there are no components to compare against
yet. So dicts are applied last however they were written, and both orders
are checked below.
"""
import os
import pathlib
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "0"

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kaypy.engine as ke                                        # noqa: E402
from kaypy import (kaypy, add, pos, rect, area, body, health,     # noqa: E402
                   vec2, get)

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


def reset():
    if ke._engine is not None:
        ke._engine._started = True
        ke._engine._running = False
        ke._engine = None


def message(fn):
    try:
        fn()
    except Exception as e:                                        # noqa: BLE001
        return "%s: %s" % (type(e).__name__, e)
    return ""


# ------------------------------------------------------------ it works
reset()
kaypy(width=800, height=600)

p = add([rect(20, 20), pos(10, 10), area(), {"isEnemy": True, "hits": 0}])
check("a dict in the list becomes attributes",
      p.isEnemy is True and p.hits == 0, "isEnemy=%r hits=%r"
      % (p.isEnemy, p.hits))

p.hits += 1
check("  and they are ordinary values you can change", p.hits == 1)

check("  while the components still work",
      p.pos == vec2(10, 10) and p.has("area"), "%s" % (p.pos,))

# Several dicts, and one holding something that is not a number.
q = add([rect(10, 10), pos(0, 0), {"dir": -1}, {"loot": ["coin", "key"]}])
check("more than one dict is fine", q.dir == -1 and q.loot == ["coin", "key"],
      "dir=%r loot=%r" % (q.dir, q.loot))

# Two objects must not share a dict's values.
a = add([rect(10, 10), pos(0, 0), {"hits": 0}])
b = add([rect(10, 10), pos(0, 0), {"hits": 0}])
a.hits = 7
check("two objects get their own copies", b.hits == 0, "b.hits=%r" % b.hits)

# It is not a tag, and a tag is not an attribute. Worth pinning down,
# because "isEnemy" is exactly the case where somebody expects both.
r = add([rect(10, 10), pos(0, 0), {"isEnemy": True}, "enemy"])
check("a dict value is not a tag", not r.is_("isEnemy"))
check("  and the tag is still a tag", r.is_("enemy") and len(get("enemy")) == 1)

# ----------------------------------------------------- clashes, both orders
reset()
kaypy(width=800, height=600)

m = message(lambda: add([rect(20, 20), pos(10, 10), {"pos": vec2(0, 0)}]))
check("a key a component owns is refused", "already gives" in m and "pos" in m,
      m.split("\n")[0][:60])

# The same clash written the other way round. Nothing has been attached yet
# when the dict is read, so this is the one that needs dicts applied last.
m = message(lambda: add([{"pos": vec2(0, 0)}, rect(20, 20), pos(10, 10)]))
check("  and refused with the dict written FIRST",
      "already gives" in m and "pos" in m, m.split("\n")[0][:60])

m = message(lambda: add([rect(10, 10), pos(0, 0), body(), {"jump": 3}]))
check("a component's METHOD is refused too", "already gives" in m,
      m.split("\n")[0][:60])

m = message(lambda: add([rect(10, 10), pos(0, 0), health(3), {"hp": 99}]))
check("  including one from a component added in the same list",
      "already gives" in m, m.split("\n")[0][:60])

# And the clash check must not be so keen that it blocks ordinary names.
ok = add([rect(10, 10), pos(0, 0), area(), body(),
          {"hits": 0, "dir": 1, "cooldown": 0.0, "name": "Bob"}])
check("names no component uses are allowed through",
      ok.hits == 0 and ok.name == "Bob", "%r" % ok.name)

# ------------------------------------------------------------ bad names
reset()
kaypy(width=800, height=600)

m = message(lambda: add([rect(10, 10), pos(0, 0), {"my flag": True}]))
check("a key that is not a valid name is refused",
      "cannot be a name" in m, m.split("\n")[0][:60])

m = message(lambda: add([rect(10, 10), pos(0, 0), {"class": 1}]))
check("  and so is a Python keyword", "cannot be a name" in m,
      m.split("\n")[0][:60])

m = message(lambda: add([rect(10, 10), pos(0, 0), {3: "three"}]))
check("  and so is a key that is not a string", "cannot be a name" in m,
      m.split("\n")[0][:60])

m = message(lambda: add([rect(10, 10), pos(0, 0), {"_id": 99}]))
check("an underscore name is refused as the engine's own",
      "engine's own" in m, m.split("\n")[0][:60])

# Nothing above may have half-built an object before raising.
check("a refused dict leaves nothing behind", len(ke._engine._objs) == 0,
      "%d objects" % len(ke._engine._objs))

# ------------------------------------------------- the old error still helps
m = message(lambda: add([rect(10, 10), 42]))
check("something that is not a component still says what is allowed",
      "components" in m and "dict" in m, m.split("\n")[0][:60])

reset()
done()
