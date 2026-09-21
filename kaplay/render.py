"""Draws every live object each frame: sprite, rect, circle or text,
in z-order, through the camera unless the object has fixed()."""
import pygame
from .geometry import get_world_pos, get_size


class RenderSystem:
    def draw(self, objs, screen, camera, debug_inspect=False):
        camera.begin_frame()
        visible = [o for o in objs if o.exists() and _is_drawable(o)]
        visible.sort(key=lambda o: o.comp("z").z if o.has("z") else 0)

        for obj in visible:
            self._draw_one(obj, screen, camera)

        if debug_inspect:
            for obj in objs:
                if obj.exists() and obj.has("area"):
                    self._draw_debug_box(obj, screen, camera)

    def _draw_one(self, obj, screen, camera):
        world_pos = get_world_pos(obj)
        w, h = get_size(obj)

        if obj.has("anchor"):
            a = obj.comp("anchor").anchor
        else:
            a = pygame_default_anchor()
        offset_x = (a.x + 1) / 2 * w
        offset_y = (a.y + 1) / 2 * h

        surf = self._build_surface(obj, w, h)
        if surf is None:
            return

        if obj.has("opacity"):
            op = obj.comp("opacity").opacity
            surf = surf.copy()
            surf.set_alpha(max(0, min(255, int(op * 255))))

        if obj.has("fixed"):
            screen.blit(surf, (world_pos.x - offset_x, world_pos.y - offset_y))
        else:
            # Camera zoom scales both the surface and the anchor offset,
            # so the anchor point stays put on screen as you zoom.
            if camera.scale != 1:
                nw = max(int(surf.get_width() * camera.scale), 1)
                nh = max(int(surf.get_height() * camera.scale), 1)
                surf = pygame.transform.scale(surf, (nw, nh))
            anchor_screen = camera.world_to_screen(world_pos)
            screen_offset_x = offset_x * camera.scale
            screen_offset_y = offset_y * camera.scale
            screen.blit(
                surf, (anchor_screen.x - screen_offset_x, anchor_screen.y - screen_offset_y)
            )

    def _build_surface(self, obj, w, h):
        if obj.has("sprite"):
            surf = obj.comp("sprite").current_surface()
        elif obj.has("rect"):
            rc = obj.comp("rect")
            col = obj.comp("color").color if obj.has("color") else (255, 255, 255)
            surf = pygame.Surface((max(int(w), 1), max(int(h), 1)), pygame.SRCALPHA)
            pygame.draw.rect(
                surf, col, surf.get_rect(), border_radius=int(rc.radius)
            )
        elif obj.has("circle"):
            col = obj.comp("color").color if obj.has("color") else (255, 255, 255)
            r = obj.comp("circle").radius
            surf = pygame.Surface((max(int(w), 1), max(int(h), 1)), pygame.SRCALPHA)
            pygame.draw.circle(surf, col, (int(r), int(r)), int(r))
        elif obj.has("text"):
            col = obj.comp("color").color if obj.has("color") else (255, 255, 255)
            surf = obj.comp("text").render_surface(col)
        else:
            return None

        if obj.has("scale"):
            sc = obj.comp("scale").scale
            nw = max(int(surf.get_width() * sc.x), 1)
            nh = max(int(surf.get_height() * sc.y), 1)
            surf = pygame.transform.scale(surf, (nw, nh))

        if obj.has("outline") and (obj.has("rect") or obj.has("circle")):
            surf = surf.copy()
            out = obj.comp("outline")
            if obj.has("circle"):
                r = min(surf.get_width(), surf.get_height()) // 2
                pygame.draw.circle(
                    surf, out.outlineColor, (surf.get_width() // 2, surf.get_height() // 2),
                    r, width=out.outlineWidth
                )
            else:
                pygame.draw.rect(surf, out.outlineColor, surf.get_rect(), width=out.outlineWidth)

        return surf

    def _draw_debug_box(self, obj, screen, camera):
        rect = obj.comp("area").get_rect()
        if obj.has("fixed"):
            pygame.draw.rect(screen, (0, 255, 0), rect, width=1)
        else:
            from .vec2 import Vec2
            tl_world = Vec2(rect.x, rect.y)
            tl = camera.world_to_screen(tl_world)
            w = rect.width * camera.scale
            h = rect.height * camera.scale
            pygame.draw.rect(
                screen, (0, 255, 0), pygame.Rect(tl.x, tl.y, w, h), width=1
            )


def _is_drawable(obj):
    return obj.has("sprite") or obj.has("rect") or obj.has("circle") or obj.has("text")


def pygame_default_anchor():
    from .vec2 import Vec2
    return Vec2(-1, -1)
