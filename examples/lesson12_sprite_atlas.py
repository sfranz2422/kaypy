from kaypy import *

kaplay(width=800, height=600, background=[20, 20, 28])

# dungeon.png is the real CC0 DungeonTileset II atlas (see CREDITS.md) —
# one 512x512 image holding the whole tileset. loadSpriteAtlas cuts named
# rectangles out of it by pixel coordinates.
#
# Two of these differ from what KAPLAY's own docs publish (ogre's y and
# chest's y) — the published values land 16px off, either half onto the
# floor tiles above or on an empty stretch of the sheet. CREDITS.md has
# the full story; these are the corrected values, verified below by
# cropping each region and checking it isn't blank.
loadSpriteAtlas("dungeon.png", {
    "wall": {"x": 16, "y": 16, "width": 16, "height": 16},
    "floor": {"x": 16, "y": 64, "width": 48, "height": 48, "sliceX": 3, "sliceY": 3},
    "hero": {
        "x": 128, "y": 196, "width": 144, "height": 28, "sliceX": 9,
        "anims": {
            "idle": {"from": 0, "to": 3, "speed": 3, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
            "hit": 8,
        },
    },
    "ogre": {
        "x": 16, "y": 336, "width": 256, "height": 32, "sliceX": 8,
        "anims": {
            "idle": {"from": 0, "to": 3, "speed": 3, "loop": True},
            "run": {"from": 4, "to": 7, "speed": 10, "loop": True},
        },
    },
    "chest": {
        "x": 304, "y": 400, "width": 48, "height": 16, "sliceX": 3,
        "anims": {
            "open": {"from": 0, "to": 2, "speed": 20, "loop": False},
            "close": {"from": 2, "to": 0, "speed": 20, "loop": False},
        },
    },
})

SPEED = 200

map_layout = [
    "##########",
    "#        #",
    "#   $    #",
    "#        #",
    "#  @    ^#",
    "#        #",
    "##########",
]
# The floor, drawn first. A space means floor here, so we don't have to
# type a character for every square.
floor_layout = [" " * len(row) for row in map_layout]

addLevel(floor_layout, {
    "tileWidth": 16,
    "tileHeight": 16,
    "tiles": {
        " ": lambda: [sprite("floor", frame=randi(0, 8))],
    },
})

# Then everything that stands on it.
level = addLevel(map_layout, {
    "tileWidth": 16,
    "tileHeight": 16,
    "tiles": {
        "#": lambda: [sprite("wall"), area(), body(isStatic=True), tile(isObstacle=True)],
        "$": lambda: [sprite("chest"), area(), tile(), "chest"],
        "^": lambda: [sprite("ogre", anim="idle"), area(), tile(), "ogre"],
        "@": lambda: [sprite("hero", anim="idle"), anchor("bot"), area(), scale(1), "player"],
    },
})

player = level.get("player")[0]


def move_left():
    player.move(-SPEED, 0)
    if player.curAnim() != "run":
        player.play("run")
    player.flipX = True


def move_right():
    player.move(SPEED, 0)
    if player.curAnim() != "run":
        player.play("run")
    player.flipX = False


onKeyDown("left", move_left)
onKeyDown("right", move_right)
onKeyRelease("left", lambda: player.play("idle"))
onKeyRelease("right", lambda: player.play("idle"))

# Exercise from the guide: make the chests play their open animation when
# space is pressed.
onKeyPress("space", lambda: [c.play("open") for c in level.get("chest")])
