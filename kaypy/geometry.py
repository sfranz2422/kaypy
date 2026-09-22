"""Shared geometry helpers used by both collision (area()) and rendering,
so 'does this touch that' and 'where does this draw' never disagree."""
import pygame
from .vec2 import Vec2


def get_size(obj):
    if obj.has("sprite"):
        base = obj.comp("sprite").size()
    elif obj.has("rect"):
        base = obj.comp("rect").size()
    elif obj.has("circle"):
        base = obj.comp("circle").size()
    elif obj.has("text"):
        base = obj.comp("text").size()
    else:
        base = (0, 0)
    if obj.has("scale"):
        sc = obj.comp("scale").scale
        base = (base[0] * sc.x, base[1] * sc.y)
    return base


def get_world_pos(obj) -> Vec2:
    """Position in world space, folding in parent offsets (children are
    positioned relative to their parent, and move when it moves)."""
    p = obj.comp("pos").pos if obj.has("pos") else Vec2(0, 0)
    if obj.parent is not None:
        return p + get_world_pos(obj.parent)
    return p


def get_topleft(obj) -> Vec2:
    p = get_world_pos(obj)
    w, h = get_size(obj)
    if obj.has("anchor"):
        a = obj.comp("anchor").anchor
    else:
        # "Without it, pos() means the top-left corner."
        a = Vec2(-1, -1)
    offset_x = (a.x + 1) / 2 * w
    offset_y = (a.y + 1) / 2 * h
    return Vec2(p.x - offset_x, p.y - offset_y)


def get_world_rect(obj) -> "pygame.FRect":
    """Float-precision rect, used for collision. AABB resolution snaps
    resting objects to sub-pixel contact, and pygame.Rect truncates to
    ints — enough to make a resting object's ground contact flicker in
    and out of existence one pixel at a time. FRect avoids that."""
    tl = get_topleft(obj)
    w, h = get_size(obj)
    return pygame.FRect(tl.x, tl.y, max(w, 0), max(h, 0))
