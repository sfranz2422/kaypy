from kaplay import *

kaplay(width=800, height=600, background=[0, 0, 0])

loadSound("bell", "sounds/ding.wav")
loadSound("bgMusic", "sounds/background.wav")

# Start the music paused, so it doesn't play until we say so.
music = play("bgMusic", loop=True, paused=True, volume=0.5)

bell_button = add([
    rect(200, 60, radius=8),
    pos(100, 100),
    area(),
    color(80, 120, 220),
])
# Added to the BUTTON, not to the screen — so (16, 18) is measured from the
# button's own corner, and the text travels with it if the button moves.
bell_button.add([
    text("Ring the bell", size=20),
    pos(16, 18),
])
bell_button.onClick(lambda: play("bell"))

music_button = add([
    rect(200, 60, radius=8),
    pos(100, 200),
    area(),
    color(220, 120, 80),
])
music_button.add([text("Play music", size=20), pos(30, 18)])


def toggle_music():
    music.paused = not music.paused


music_button.onClick(toggle_music)
