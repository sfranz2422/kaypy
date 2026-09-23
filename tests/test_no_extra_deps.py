"""kaypy installs one thing, and nothing here may need a second.

    python3 tests/test_no_extra_deps.py

`pip install kaypy` brings pygame-ce and stops. That is a promise the
project makes on its front page and in `dependencies`, and it is the whole
reason a student on a school laptop can get a game running in four commands.

It is also a promise nothing enforces at the moment somebody breaks it,
because the machine that breaks it is always a machine where the extra thing
happens to be installed already. That is exactly how it went wrong:
`tests/test_cam_scale.py` read pixels back with `pygame.surfarray`, which
needs numpy. It passed here. It failed in CI — a clean environment with
precisely what the package asks for — after the code was written, reviewed,
and about to be pushed.

So this walks every Python file the project ships or tests with, and fails
on an import of anything that is neither the standard library, nor pygame,
nor kaypy itself.

THE SECOND HALF, WHICH AN IMPORT SCAN MISSES

`pygame.surfarray` is not an import. It is an attribute of a module that IS
allowed, and it raises only when touched, only without numpy. `pygame.sndarray`
is the same. Both are checked for by name, because the honest version of this
test has to catch the thing that actually happened.
"""
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-54s %s" % ("ok" if ok else "FAIL", label, detail))


def done():
    bad = results.count(False)
    print("\n%s (%d checks, %d failed)"
          % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
    sys.exit(1 if bad else 0)


#: Everything a file here is allowed to import on top of the standard
#: library. Adding to this list is adding to what a student must install, so
#: it is meant to be hard to do by accident.
#:
#: `js` and `pyodide` are not installed by anybody: they are what Pyodide
#: puts in place inside a browser, and the files that reach for them do so
#: behind a check for sys.platform == "emscripten" or a try/except. There is
#: nothing to add to `dependencies` for either, and nothing a desktop install
#: needs — which is the point of the distinction this file is drawing.
ALLOWED = {"pygame", "kaypy", "js", "pyodide"}

#: Parts of pygame that quietly require numpy. Allowed nowhere.
NEEDS_NUMPY = ("surfarray", "sndarray")

FOLDERS = ["kaypy", "tests", "examples"]


def python_files():
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*.py")):
            if "__pycache__" in path.parts or "build" in path.parts:
                continue
            yield path


files = list(python_files())
check("there are files to check", len(files) > 30, "%d files" % len(files))

# ------------------------------------------------------- what is declared
toml = (ROOT / "pyproject.toml").read_text()
block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", toml, re.S | re.M)
# Comments first: the note above the pin quotes a section title, and a
# regex looking for quoted things finds the words in it.
lines = [ln.split("#", 1)[0] for ln in (block.group(1) if block else "").splitlines()]
declared = re.findall(r'"([A-Za-z0-9_.-]+)', "\n".join(lines))
check("pyproject declares exactly one dependency", declared == ["pygame-ce"],
      ", ".join(declared) or "none found")

# ---------------------------------------------------------- what is used
stdlib = set(sys.stdlib_module_names)
local = {p.stem for p in files}

offenders = []
for path in files:
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:                                      # noqa: BLE001
        offenders.append((path, "does not parse: %s" % e))
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:                     # a relative import, ours
                continue
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        for name in names:
            if not name or name in stdlib or name in ALLOWED or name in local:
                continue
            offenders.append((path, "imports %r" % name))

check("nothing imports outside the standard library, pygame and kaypy",
      not offenders,
      "; ".join("%s %s" % (p.relative_to(ROOT), why)
                for p, why in offenders[:3]))

# --------------------------------------------- the parts of pygame that do
# Through the syntax tree, not a text search. Written as a grep, this check
# fails on the paragraph at the top of this file that explains what it is
# for — and the obvious fix, skipping this file, would then miss a real use
# in it. An attribute access is what matters, and the tree knows the
# difference between one of those and the same word in a docstring.
numpy_users = []
for path in files:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute)
                and node.attr in NEEDS_NUMPY
                and isinstance(node.value, ast.Name)
                and node.value.id == "pygame"):
            numpy_users.append((path, node.attr))

check("and nothing reaches for a part of pygame that needs numpy",
      not numpy_users,
      "; ".join("%s uses pygame.%s" % (p.relative_to(ROOT), part)
                for p, part in numpy_users[:3]))

# ------------------------------------------------- the check has teeth
#
# An import scan that silently found nothing to scan would pass forever.
# These two are known to be present, so finding them proves the walk works.
sample = "\n".join(p.read_text() for p in files)
check("  (the scan really is reading the files)",
      "import pygame" in sample and "from kaypy import" in sample)

done()
