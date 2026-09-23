"""Drawing straight to the screen, without making a game object for it.

    @onDraw
    def health_bar():
        drawRect(pos=vec2(20, 20), width=200, height=16, color=rgb(60, 0, 0),
                 fixed=True)
        drawRect(pos=vec2(20, 20), width=2 * player.hp, height=16,
                 color=rgb(220, 40, 40), fixed=True)

WHY THIS EXISTS

Everything else in kaypy is a game object: it has a position, it persists, it
collides, it is destroyed. That is the right shape for a player, a coin, a
platform — and the wrong shape for a health bar, an aim line from the player
to the cursor, a grid behind a puzzle, or a circle showing an explosion's
radius. Those are not *things in the world*; they are marks on the screen for
one frame.

Without this, a student builds them out of game objects anyway — creating and
destroying a rectangle every frame, or making one and hunting for every place
its width has to be updated. Both work. Both teach the wrong lesson about what
a game object is for.

WHEN THEY CAN BE CALLED

Only from inside an `onDraw` handler, because only then is there a frame being
drawn. Called anywhere else they raise and say so, rather than silently doing
nothing — a drawing that never appears is among the least debuggable things a
beginner can write.

WORLD SPACE OR SCREEN SPACE

By default these draw in *world* space: they move with the camera, exactly
like game objects do, so a marker drawn at an enemy's position stays on the
enemy. Pass `fixed=True` for screen space, which is what you want for a HUD —
the same distinction `fixed()` makes for game objects.
"""
from __future__ import annotations

import pygame

from .vec2 import Vec2

#: Set by RenderSystem for the length of the draw phase, cleared after. A
#: tuple of (surface, camera), or None when no frame is being drawn.
_target = None


def _begin(screen, camera):
    global _target
    _target = (screen, camera)


def _end():
    global _target
    _target = None


def _surface(who):
    if _target is None:
        raise RuntimeError(
            f"{who}() can only be called while a frame is being drawn — put it "
            f"inside an onDraw handler:\n"
            f"    @onDraw\n"
            f"    def hud():\n"
            f"        {who}(...)"
        )
    return _target


def _place(pos, fixed, camera):
    """A world (or screen) position, as pixels on the surface.

    The zoom that comes back is a Vec2, because the camera can be scaled a
    different amount on each axis. Sizes with a width and a height use both
    of them; see `_thickness` for the things that cannot."""
    point = pos if isinstance(pos, Vec2) else Vec2(pos[0], pos[1])
    if fixed:
        return point, Vec2(1.0, 1.0)
    return camera.world_to_screen(point), camera.scale


def _thickness(zoom):
    """One number, for things that only have one.

    A line's width, a corner radius, the size of a letter: none of these can
    be two different numbers, however the camera is stretched, because
    nothing in pygame can draw a line that is thicker across than along. The
    smaller of the two axes is the safe answer — the larger makes an outline
    swell out past the shape it is supposed to be edging."""
    return min(zoom.x, zoom.y)


def _colour(color, opacity):
    from .helpers import rgb

    r, g, b = rgb(color) if color is not None else (255, 255, 255)
    if opacity >= 1:
        return (int(r), int(g), int(b))
    return (int(r), int(g), int(b), max(0, int(255 * opacity)))


def _put(screen, surf, at, anchor):
    """Blit so that `at` lands on the named anchor point of the surface.

    Through AnchorComp's own resolver rather than a second table of names, so
    `anchor="botright"` means here exactly what it means on a game object —
    including raising the same error for a name that does not exist.
    """
    from .comps.transform import AnchorComp

    a = AnchorComp(anchor).anchor
    ox = (a.x + 1) / 2 * surf.get_width()
    oy = (a.y + 1) / 2 * surf.get_height()
    screen.blit(surf, (at.x - ox, at.y - oy))


# --------------------------------------------------------------- shapes

def drawRect(pos=None, width=0, height=0, color=None, opacity=1.0,
             anchor="topleft", radius=0, outline=0, fixed=False):
    """A rectangle. `radius` rounds the corners; `outline` draws only the edge."""
    screen, camera = _surface("drawRect")
    at, zoom = _place(pos or Vec2(0, 0), fixed, camera)
    w, h = max(1, int(width * zoom.x)), max(1, int(height * zoom.y))
    thick = _thickness(zoom)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, _colour(color, opacity), pygame.Rect(0, 0, w, h),
                     width=int(outline * thick),
                     border_radius=int(radius * thick))
    _put(screen, surf, at, anchor)


def drawCircle(pos=None, radius=0, color=None, opacity=1.0, outline=0,
               fixed=False):
    """A circle, centred on `pos`."""
    screen, camera = _surface("drawCircle")
    at, zoom = _place(pos or Vec2(0, 0), fixed, camera)
    # A circle in a world stretched twice as wide is an ellipse, the same
    # way a square in it is an oblong. Drawing it as a circle of some
    # average radius would leave it the one shape on screen that did not
    # agree with the camera.
    rx = max(1, int(radius * zoom.x))
    ry = max(1, int(radius * zoom.y))

    surf = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
    box = pygame.Rect(0, 0, rx * 2, ry * 2)
    edge = int(outline * _thickness(zoom))
    if rx == ry:
        pygame.draw.circle(surf, _colour(color, opacity), (rx, ry), rx,
                           width=edge)
    else:
        pygame.draw.ellipse(surf, _colour(color, opacity), box, width=edge)
    screen.blit(surf, (at.x - rx, at.y - ry))


def drawLine(p1=None, p2=None, width=1, color=None, opacity=1.0, fixed=False):
    """A line from one point to another."""
    screen, camera = _surface("drawLine")
    a, zoom = _place(p1 or Vec2(0, 0), fixed, camera)
    b, _ = _place(p2 or Vec2(0, 0), fixed, camera)
    thickness = max(1, int(width * _thickness(zoom)))

    if opacity >= 1:
        pygame.draw.line(screen, _colour(color, 1.0),
                         (a.x, a.y), (b.x, b.y), thickness)
        return
    # A translucent line needs its own surface; pygame.draw ignores alpha on
    # the display surface.
    surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    pygame.draw.line(surf, _colour(color, opacity),
                     (a.x, a.y), (b.x, b.y), thickness)
    screen.blit(surf, (0, 0))


def drawLines(points=None, width=1, color=None, opacity=1.0, close=False,
              fixed=False):
    """A run of connected lines. `close` joins the last point back to the first."""
    pts = list(points or [])
    if len(pts) < 2:
        return
    pairs = list(zip(pts, pts[1:]))
    if close:
        pairs.append((pts[-1], pts[0]))
    for a, b in pairs:
        drawLine(p1=a, p2=b, width=width, color=color, opacity=opacity,
                 fixed=fixed)


# ----------------------------------------------------------------- text

def drawText(text="", pos=None, size=22, color=None, opacity=1.0,
             anchor="topleft", fixed=False):
    """Some words. Same font as the text() component."""
    from .engine import current_engine

    screen, camera = _surface("drawText")
    at, zoom = _place(pos or Vec2(0, 0), fixed, camera)

    font = current_engine()._get_font(max(1, int(size * _thickness(zoom))))
    surf = font.render(str(text), True, _colour(color, 1.0)[:3])
    if opacity < 1:
        surf = surf.copy()
        surf.set_alpha(max(0, int(255 * opacity)))
    _put(screen, surf, at, anchor)


# --------------------------------------------------------------- sprites

def drawSprite(sprite="", pos=None, frame=0, width=None, height=None,
               opacity=1.0, anchor="topleft", angle=0, fixed=False):
    """One frame of a loaded sprite, without making an object for it."""
    from .engine import current_engine

    screen, camera = _surface("drawSprite")
    at, zoom = _place(pos or Vec2(0, 0), fixed, camera)

    asset = current_engine().assets.get_sprite(sprite)
    index = max(0, min(int(frame), len(asset.frames) - 1))
    surf = asset.frames[index]

    w = (width if width is not None else surf.get_width()) * zoom.x
    h = (height if height is not None else surf.get_height()) * zoom.y
    if (int(w), int(h)) != surf.get_size():
        surf = pygame.transform.scale(surf, (max(1, int(w)), max(1, int(h))))
    if angle:
        surf = pygame.transform.rotate(surf, -angle)
    if opacity < 1:
        surf = surf.copy()
        surf.set_alpha(max(0, int(255 * opacity)))
    _put(screen, surf, at, anchor)
