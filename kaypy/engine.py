"""The engine singleton. kaypy(...) creates it and starts the game the
moment the rest of the script finishes running — there is no run() call
anywhere in the Kaplay guide.

On native CPython, atexit gets us this for free: kaypy() registers the
frame loop and it fires once your script's top level finishes.

In a browser (sys.platform == "emscripten") that trick is no use, and
kaypy() skips atexit entirely there. Two reasons, either one sufficient.

The plain one: a browser tab's Python interpreter does not exit, so an
atexit handler is a frame loop that never starts.

The historical one, kept because it explains why the check is a hard skip
rather than a try/except: this used to run under pygbag, which replaced
the stdlib atexit module with its own (support/cross/aio/atexit.py in
0.9.3) whose register() closed over an undefined `arg` instead of `args`
— so merely *calling* atexit.register() there raised NameError before
the game had drawn a frame. tests/test_web_platform_guard.py still holds
that line down.

Whatever starts the game on the web calls run_async() explicitly
instead. That is kaypy/webrun.py, which is what the page built by
`kaypy web` calls, and what a browser IDE embedding kaypy calls too."""
from __future__ import annotations
import asyncio
import sys
import random as _random

import pygame

from .vec2 import Vec2
from .gameobj import GameObj
from .assets import AssetManager
from .events import EventManager
from .timers import TimerManager
from .camera import Camera
from .physics import PhysicsSystem, CollisionSystem
from .render import RenderSystem
from .debugmod import debug

_engine: "Engine | None" = None


def current_engine() -> "Engine":
    if _engine is None:
        raise RuntimeError("kaypy(...) must run before anything else in a Kaplay script")
    return _engine


class SoundHandle:
    def __init__(self, sound, loop=False, paused=False, volume=1.0):
        self._channel = None
        self._volume = volume
        self._paused = paused
        if sound is not None:
            self._channel = sound.play(loops=-1 if loop else 0)
            if self._channel:
                self._channel.set_volume(volume)
                if paused:
                    self._channel.pause()

    @property
    def paused(self):
        return self._paused

    @paused.setter
    def paused(self, value):
        self._paused = value
        if self._channel:
            if value:
                self._channel.pause()
            else:
                self._channel.unpause()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        if self._channel:
            self._channel.set_volume(value)


class Engine:
    def __init__(self, width=800, height=600, background=(0, 0, 0)):
        global _engine
        _engine = self

        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass  # no audio device (e.g. headless/CI) — sounds become silent no-ops

        self._width = width
        self._height = height
        self._background = tuple(background)
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("kaypy")
        self.clock = pygame.time.Clock()

        self.assets = AssetManager()
        self.events = EventManager()
        self.timers = TimerManager()
        self.camera = Camera(width, height)
        self.physics = PhysicsSystem()
        self.collision = CollisionSystem()
        self.render = RenderSystem()

        self._objs: list[GameObj] = []
        self._scenes: dict[str, callable] = {}
        self._current_scene = None
        self._dt = 0.0
        # Game time, not wall time: it advances with the frames, so it stops
        # when the game does. A sine wave driven by wall time jumps when a
        # paused game resumes.
        self._elapsed = 0.0
        self._running = True
        self._started = False
        self._font_cache = {}
        self.is_web = sys.platform == "emscripten"

        if not self.is_web:
            # Native only — see the module docstring for why this is
            # unsafe under pygbag's own atexit replacement.
            import atexit
            atexit.register(self._atexit_run)

    # ---- values ------------------------------------------------------------

    def width(self):
        return self._width

    def height(self):
        return self._height

    def center(self) -> Vec2:
        return Vec2(self._width / 2, self._height / 2)

    def dt(self):
        return self._dt

    def elapsed(self):
        return self._elapsed

    def mousePos(self) -> Vec2:
        x, y = pygame.mouse.get_pos()
        return Vec2(x, y)

    def toWorld(self, screen_pos) -> Vec2:
        return self.camera.screen_to_world(screen_pos)

    def setGravity(self, n):
        self.physics.gravity = n

    def setBackground(self, r, g, b):
        self._background = (r, g, b)

    def setCamPos(self, pos):
        self.camera.setPos(pos)

    def setCamScale(self, n):
        self.camera.setScale(n)

    def shake(self, n=8):
        self.camera.shake(n)

    def _get_font(self, size):
        f = self._font_cache.get(size)
        if f is None:
            f = pygame.font.SysFont(None, size)
            self._font_cache[size] = f
        return f

    # ---- object tree ---------------------------------------------------------

    def add(self, comp_list) -> GameObj:
        obj = GameObj(comp_list)
        obj._engine = self
        self._register(obj)
        return obj

    def _register(self, obj: GameObj):
        self._objs.append(obj)

    def _unregister(self, obj: GameObj):
        try:
            self._objs.remove(obj)
        except ValueError:
            pass

    def get(self, tag: str):
        return [o for o in self._objs if o.exists() and o.is_(tag)]

    # ---- scenes ----------------------------------------------------------

    def scene(self, name, fn):
        self._scenes[name] = fn

    def go(self, name, *args):
        if name not in self._scenes:
            raise KeyError(
                f"no scene called {name!r} — register it with scene({name!r}, fn) first"
            )
        self._clear_scene()
        self._current_scene = name
        self._scenes[name](*args)

    def _clear_scene(self):
        for obj in list(self._objs):
            obj.destroy()
        self._objs.clear()
        self.events.clear()
        self.timers.clear()
        self.camera = Camera(self._width, self._height)

    # ---- main loop ---------------------------------------------------------

    def _atexit_run(self):
        if self._started:
            return
        self.run()

    def run(self):
        """Starts the frame loop by driving it with a fresh asyncio.run().
        On native, kaypy scripts never need to call this themselves — it
        fires automatically once the script body finishes (see the atexit
        registration in __init__) — but it's safe (and a no-op the second
        time) to call explicitly too. Not for use under pygbag: the web
        build's generated main.py wrapper awaits run_async() directly
        instead, inside the asyncio.run() IT owns (see tools/build_web.py)."""
        if self._started:
            return
        try:
            asyncio.run(self.run_async())
        finally:
            pygame.quit()

    async def run_async(self):
        """The coroutine form of run() — awaits the frame loop directly,
        without starting its own asyncio.run(). This is what the pygbag
        web build's main.py wrapper calls, since pygbag needs to own the
        outermost asyncio.run() itself."""
        if self._started:
            return
        self._started = True
        await self._main_loop()

    async def _main_loop(self):
        import os
        # Unset means no limit — a real game runs until it is closed.
        #
        # Read this way, rather than `int(os.environ.get(..., "0")) or None`,
        # because that made "0" mean UNLIMITED: int("0") is falsy, so `or
        # None` replaced it. A test that set it to 0 meaning "do not run a
        # single frame" got a loop that never returned, at interpreter exit,
        # with no output and nothing to attach a traceback to. Every other
        # caller passes a positive number and never noticed.
        raw = os.environ.get("KAYPY_TEST_MAX_FRAMES")
        max_frames = int(raw) if raw not in (None, "") else None
        frame_count = 0
        # The limit below is checked after a frame has been drawn, so a bare
        # `while` would still run one. Zero has to mean zero: a test that
        # wants the loop not to run at all is usually one holding a game
        # object still to look at it.
        if max_frames == 0:
            self._running = False
            return
        while self._running:
            pg_events = pygame.event.get()
            for e in pg_events:
                if e.type == pygame.QUIT:
                    self._running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F1:
                    debug.inspect = not debug.inspect
            if not self._running:
                break

            # Native: tick(60) sleeps to pace the loop at 60fps. Web: the
            # browser already paces us (each `await asyncio.sleep(0)`
            # below lands on the next animation frame), and tick(60)'s
            # sleep can't yield to the browser, so it just burns the main
            # thread and makes frame times *less* even — measured in a
            # real build, dt alternated between 16ms and the 50ms cap
            # below. So on web just measure, don't pace.
            elapsed = self.clock.tick() if self.is_web else self.clock.tick(60)
            self._dt = min(elapsed / 1000.0, 0.05)
            self._elapsed += self._dt

            self.events.process_pygame_events(pg_events, self._objs)
            self.events.run_update_handlers(self._objs)

            for obj in list(self._objs):
                if not obj.exists():
                    continue
                for comp in list(obj._comps.values()):
                    comp.update(obj)
                if "update" in obj._event_handlers:
                    obj._fire("update")

            self.timers.update(self._dt)
            # Movement and collision run together, in as many substeps as
            # it takes to keep anything from jumping clean over a wall it
            # should have hit (see PhysicsSystem.substeps_for). Normal
            # frames need exactly one, so this costs nothing until
            # something is genuinely moving fast.
            substeps = self.physics.substeps_for(self._objs, self._dt)
            sub_dt = self._dt / substeps
            for _ in range(substeps):
                self.physics.step(self._objs, sub_dt)
                self.collision.step(self._objs)

            self.screen.fill(self._background)
            self.render.draw(self._objs, self.screen, self.camera, debug.inspect,
                             self.events.draw_handlers)
            pygame.display.flip()

            frame_count += 1
            shot_at = os.environ.get("KAYPY_SCREENSHOT_AT")
            shot_path = os.environ.get("KAYPY_SCREENSHOT_PATH")
            if shot_at and shot_path and frame_count == int(shot_at):
                pygame.image.save(self.screen, shot_path)
            # `is not None`, not a truthiness test: max_frames == 0 means run
            # no frames, and `if max_frames` reads that as no limit — the same
            # confusion between "zero" and "unset" that the parsing above had.
            if max_frames is not None and frame_count >= max_frames:
                self._running = False

            await asyncio.sleep(0)


def rand(a=1.0, b=None):
    if b is None:
        return _random.uniform(0, a)
    return _random.uniform(a, b)


def randi(a=1, b=None):
    if b is None:
        return _random.randint(0, a)
    return _random.randint(a, b)


def choose(seq):
    return _random.choice(seq)
