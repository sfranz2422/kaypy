"""debug.inspect = True draws every collision box on screen (or press F1
while the game is running)."""


class _Debug:
    def __init__(self):
        self.inspect = False


debug = _Debug()
