"""The URL `kaypy web` prints must say 127.0.0.1, not localhost.

    python3 tests/test_web_serve_host.py

This looks like a cosmetic test. It is not.

pygbag's in-browser bootstrap contains this, in
pygbag/support/cross/aio/pep0723.py:

    elif platform.window.location.href.startswith("http://localhost:8"):
        rewritecdn = "http://localhost:8000/cdn/"

A page served from localhost on a port starting with 8 is therefore assumed to
have a local mirror of pygbag's package CDN, and every wheel it needs is
fetched from *your* dev server instead of pygame-web.github.io. kaypy has no
such mirror, so the one wheel that matters 404s:

    GET /cdn/cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl -> 404

and the game sits at "Loading, please wait ..." for ever — after the whole
CPython interpreter, the terminal, the service worker and the game archive have
all loaded from the real CDN without complaint. Nothing in the build is wrong.
The page asked the wrong host for one file.

`http://127.0.0.1:8000/` does not match that prefix. Verified against one
unchanged build loaded both ways in a real browser: on localhost it 404s and
stops; on 127.0.0.1 the game runs.

So if someone ever tidies that hostname back to `localhost` because it reads
better, the web export breaks, silently, in a way whose symptom points
nowhere near this line. Hence a test.
"""
import io
import contextlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kaplay import webbuild                                   # noqa: E402

results = []


def check(label, ok, detail=""):
    results.append(bool(ok))
    print("  %-4s %-52s %s" % ("ok" if ok else "FAIL", label, detail))


# serve() blocks on a real server, so it is stopped at the subprocess call —
# everything this test cares about has already been printed by then.
class Stop(Exception):
    pass


def refuse_to_run(*_args, **_kwargs):
    raise Stop


webbuild.subprocess.run = refuse_to_run

out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        webbuild.serve(ROOT, 8000)
except Stop:
    pass
printed = out.getvalue()

check("it prints a URL to open", "http://" in printed)
check("the URL is 127.0.0.1, not localhost",
      "http://127.0.0.1:" in printed and "http://localhost:" not in printed,
      [l.strip() for l in printed.split("\n") if "http://" in l][:1])
check("and it says why, so nobody 'fixes' it back",
      "localhost" in printed.lower(),
      "the warning mentions localhost")

# The docstring is where the reason lives; losing it loses the reason.
doc = webbuild.serve.__doc__ or ""
check("serve() explains the pygbag rewrite",
      "pep0723" in doc and "rewritecdn" in doc)
check("and names the file that 404s", "pygame_ce" in doc and "404" in doc)

# A missing build directory must say so rather than start a server on nothing.
out = io.StringIO()
with contextlib.redirect_stdout(out):
    webbuild.serve(ROOT / "no-such-build", 8000)
check("nothing to serve is reported, not served",
      "nothing to serve" in out.getvalue())

bad = results.count(False)
print("\n%s (%d checks, %d failed)"
      % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
