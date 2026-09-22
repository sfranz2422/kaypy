"""Drawable shape/text components: rect(), circle(), text().
These hold data only — the RenderSystem does the actual drawing so
z-ordering, camera transform, anchor and scale stay in one place."""
from ..gameobj import Comp


class RectComp(Comp):
    id = "rect"

    def __init__(self, width, height, radius=0):
        self.width = width
        self.height = height
        self.radius = radius

    def size(self):
        return (self.width, self.height)


def rect(width, height, radius=0):
    return RectComp(width, height, radius)


class CircleComp(Comp):
    id = "circle"

    def __init__(self, radius):
        self.radius = radius

    def size(self):
        d = self.radius * 2
        return (d, d)


def circle(radius):
    return CircleComp(radius)


class TextComp(Comp):
    id = "text"

    def __init__(self, text_str="", size=22, width=None):
        self.text = text_str
        self.textSize = size
        self.width = width
        self._font_cache_key = None
        self._surf_cache = None
        self._surf_cache_key = None

    def render_surface(self, color=(255, 255, 255)):
        from ..engine import current_engine
        import pygame
        font = current_engine()._get_font(self.textSize)
        key = (self.text, self.textSize, self.width, color)
        if self._surf_cache_key == key:
            return self._surf_cache
        if self.width:
            surf = _wrap_text(font, self.text, self.width, color)
        else:
            surf = font.render(self.text, True, color)
        self._surf_cache_key = key
        self._surf_cache = surf
        return surf

    def size(self):
        return self.render_surface().get_size()


def _wrap_text(font, text_str, max_width, color):
    import pygame
    words = text_str.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if font.size(trial)[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    if not lines:
        lines = [""]
    line_surfs = [font.render(line, True, color) for line in lines]
    total_h = sum(s.get_height() for s in line_surfs)
    total_w = max((s.get_width() for s in line_surfs), default=0)
    out = pygame.Surface((max(total_w, 1), max(total_h, 1)), pygame.SRCALPHA)
    y = 0
    for s in line_surfs:
        out.blit(s, (0, y))
        y += s.get_height()
    return out


def text(text_str="", size=22, width=None):
    return TextComp(text_str, size=size, width=width)
