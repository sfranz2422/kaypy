"""KAYPY_TEST_MAX_FRAMES means what it says."""
import os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
PROG = '''
import sys
sys.path.insert(0, %r)
import atexit
frames = []
atexit.register(lambda: print("FRAMES", len(frames)))   # registered FIRST, so it runs LAST
from kaypy import *
kaypy(width=64, height=64)
onUpdate(lambda: frames.append(1))
'''
def run(value, timeout=15):
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    if value is None:
        env.pop("KAYPY_TEST_MAX_FRAMES", None)
    else:
        env["KAYPY_TEST_MAX_FRAMES"] = value
    try:
        p = subprocess.run([sys.executable, "-c", PROG % str(ROOT)],
                           capture_output=True, text=True, env=env, timeout=timeout)
        for line in p.stdout.splitlines():
            if line.startswith("FRAMES"):
                return int(line.split()[1])
        return None
    except subprocess.TimeoutExpired:
        return "ran forever"

results = []
def check(label, ok, detail=""):
    results.append(ok); print("  %-4s %-44s %s" % ("ok" if ok else "FAIL", label, detail))

n = run("0")
check('"0" runs zero frames', n == 0, "ran %s" % n)
n = run("3")
check('"3" runs three', n == 3, "ran %s" % n)
n = run(None, timeout=6)
check("unset means no limit (a real game keeps running)", n == "ran forever", str(n))

bad = results.count(False)
print("\n%s (%d checks, %d failed)" % ("SOME FAILED" if bad else "ALL PASSED", len(results), bad))
sys.exit(1 if bad else 0)
