from typing import Tuple


Colour = Tuple[int, int, int]
Palette = Tuple[Colour, ...]


palette1: Palette = (
    (255,   0,   0),
    (  0, 255,   0),
    (  0,   0, 255),
    (255, 255,   0),
)

palette2: Palette = (
    (214, 126, 195),
    ( 24, 185, 196),
    (128,  65, 196),
    (128, 196,  65),
)


PALLETE: Palette = palette2
