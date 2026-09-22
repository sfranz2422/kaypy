"""Standalone sanity script: a body must land on a floor made of separate
tiles even when a slow frame buries it deep into them in one step.

This is a regression test for a real bug, found by running a real web
build in a real browser (it never reproduced natively, which is the
whole point of it existing):

Lesson 10's floor is a row of individual 64x64 tiles, and the player
straddles the seam between two of them — overlapping each by only 32px
horizontally. The old resolver pushed objects apart along whichever axis
overlapped least. At a steady 60fps the player only ever sank ~10px into
the floor per frame, so the vertical overlap was always the smaller one
and it got pushed up, correctly. But browser frames are less even than
desktop ones: dt hit the engine's 50ms ceiling on alternating frames,
which let the player sink ~45px in a single step — deeper than its 32px
horizontal overlap with either tile. Both tiles then pushed it sideways
instead of up, in opposite directions, so the two pushes cancelled and
nothing held it up. It sank through the floor and fell forever.

So the two things that matter here, both checked below:
  1. deep penetration still resolves as a landing (the resolver decides
     the axis from where the two came from, not from which overlap is
     smaller), and
  2. a single frame can't move a body so far that it skips the floor
     entirely without ever overlapping it (substepping).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["KAYPY_TEST_MAX_FRAMES"] = "1"

from kaypy import (  # noqa: E402
    kaplay, add, pos, rect, area, body, anchor, setGravity,
)
from kaypy.engine import current_engine  # noqa: E402

TILE = 64
FLOOR_TOP = 384


def build_scene():
    """Lesson 10's shape exactly: a tiled floor, and a player standing on
    the seam between two tiles, one tile's height above it."""
    engine = current_engine()
    engine._objs.clear()
    for col in range(6):
        add([pos(col * TILE, FLOOR_TOP), rect(TILE, TILE), area(), body(isStatic=True)])
    # 64x54 is the real bean sprite's size; anchor("bot") is what the
    # lesson uses, so pos is the player's feet.
    player = add([pos(TILE, FLOOR_TOP - TILE), rect(64, 54), area(), body(), anchor("bot")])
    return player


def run_frames(dts):
    """Drive exactly what Engine._main_loop drives, one frame per dt."""
    engine = current_engine()
    for dt in dts:
        substeps = engine.physics.substeps_for(engine._objs, dt)
        sub_dt = dt / substeps
        for _ in range(substeps):
            engine.physics.step(engine._objs, sub_dt)
            engine.collision.step(engine._objs)


kaplay(width=800, height=600, background=[0, 0, 0])
setGravity(2400)

# --- 1. the exact failure: every frame at the engine's 50ms dt ceiling ---
player = build_scene()
run_frames([0.05] * 40)
bottom = player.comp("area").get_rect().bottom
assert bottom <= FLOOR_TOP + 1, (
    f"player sank through a tiled floor at dt=0.05 — its feet are at "
    f"{bottom}, the floor's surface is at {FLOOR_TOP}"
)
assert player.comp("body").isGrounded(), "player should be grounded resting on the floor"
print(f"confirmed: lands on a tile seam at a steady dt=0.05 (feet at y={bottom})")

# --- 2. the real browser trace: dt alternating between cap and 60fps ----
player = build_scene()
run_frames([0.05, 0.016] * 30)
bottom = player.comp("area").get_rect().bottom
assert bottom <= FLOOR_TOP + 1, (
    f"player sank through with alternating 50ms/16ms frames — feet at {bottom}"
)
print(f"confirmed: lands with alternating 50ms/16ms frames (feet at y={bottom})")

# --- 3. steady 60fps must still behave exactly as it always did --------
player = build_scene()
run_frames([1 / 60] * 80)
bottom = player.comp("area").get_rect().bottom
assert abs(bottom - FLOOR_TOP) <= 1, f"native 60fps landing regressed — feet at {bottom}"
print(f"confirmed: unchanged at a steady 60fps (feet at y={bottom})")

# --- 4. arriving fast enough to clear the whole floor in one frame -----
# Falling the height of the screen reaches ~1700px/s; at the 50ms ceiling
# that is 85px of travel in one step, more than the floor is thick.
player = build_scene()
player.comp("body").vel.y = 1700
run_frames([0.05] * 20)
bottom = player.comp("area").get_rect().bottom
assert bottom <= FLOOR_TOP + 1, (
    f"player tunneled clean through the floor at 1700px/s — feet at {bottom}"
)
print(f"confirmed: 1700px/s impact doesn't tunnel through a 64px floor (feet at y={bottom})")

print("ALL TILE-FLOOR LANDING CHECKS PASSED")
