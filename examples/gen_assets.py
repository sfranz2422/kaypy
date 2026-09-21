"""Fallback placeholder art, only for whatever the real asset pack (see
CREDITS.md) doesn't cover — this never overwrites a real file, so it's
safe to re-run after vendoring real assets. Not part of the kaplay
package itself, just a fixture generator for these examples."""
import os
import pygame

pygame.init()

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(HERE, "images")
SOUNDS = os.path.join(HERE, "sounds")
os.makedirs(IMAGES, exist_ok=True)
os.makedirs(SOUNDS, exist_ok=True)


def save(surf, name):
    path = os.path.join(IMAGES, name)
    if os.path.exists(path):
        print(f"skipping {name} — a real asset is already there")
        return
    pygame.image.save(surf, path)


def circle_sprite(name, radius, color, size=None):
    size = size or radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (size // 2, size // 2), radius)
    save(surf, name)


def square_sprite(name, size, color):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill(color)
    save(surf, name)


def triangle_sprite(name, size, color):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.polygon(surf, color, [(size // 2, 0), (0, size), (size, size)])
    save(surf, name)


circle_sprite("bean.png", 22, (70, 130, 255), size=48)
circle_sprite("ghosty.png", 20, (240, 240, 240), size=48)
circle_sprite("coin.png", 14, (255, 210, 40), size=32)
circle_sprite("portal.png", 20, (170, 70, 220), size=48)
square_sprite("steel.png", 48, (150, 150, 160))
square_sprite("grass.png", 64, (90, 170, 90))
triangle_sprite("spike.png", 48, (220, 40, 40))

# a 9-frame "dino" walk cycle: 9 images, each a rectangle with a moving leg mark
for i in range(9):
    surf = pygame.Surface((16, 26), pygame.SRCALPHA)
    surf.fill((90, 74, 58))
    leg_x = 2 + (i % 4) * 3
    pygame.draw.rect(surf, (60, 50, 40), (leg_x, 20, 4, 6))
    save(surf, f"dino_{i}.png")

print("Done —", IMAGES)
