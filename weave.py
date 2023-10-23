from enum import Enum, auto
from functools import cache
from sys import stderr
from typing import Any, Generator, List, Literal, Tuple
try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = False

CELL_STRIDE = 5

class Thread(Enum):
    RED = 0
    GRN = auto()
    BLU = auto()
    YEL = auto()

class Crossing(Enum):
    WARP = 0
    WEFT = auto()

Colour = Tuple[int, int, int]

palette1 = (
    (255,   0,   0),
    (  0, 255,   0),
    (  0,   0, 255),
    (255, 255,   0),
)

palette2 = (
    (214, 126, 195),
    ( 24, 185, 196),
    (128,  65, 196),
    (128, 196,  65),
)

PALLETE = palette2

COLOURS: dict[Thread, Colour] = {
    Thread.RED: PALLETE[0],
    Thread.GRN: PALLETE[1],
    Thread.BLU: PALLETE[2],
    Thread.YEL: PALLETE[3],
}

Cell = Tuple[Thread, Thread, Thread, Thread]
Grid = List[List[Cell]]

def start_threads() -> Generator[Literal[Thread.RED, Thread.GRN], Any, None]:
    yield Thread.GRN
    while True:
        yield Thread.RED

@cache
def next_crossing_knot(up: Thread, left: Thread, cross: Crossing) -> Tuple[Thread, Thread, Thread, Thread]:
    """Knot 3-colour: No change if both threads the same colour else thee under thread is changed to the third colour if"""
    if up == left:
        return (up, left, up, left)
    new = ({Thread.RED, Thread.GRN, Thread.BLU} - {up, left}).pop()
    if cross is Crossing.WARP:
        return (up, left, new, left)
    else:
        return (up, left, up, new)

@cache
def next_crossing_xor(up: Thread, left: Thread, cross: Crossing) -> Tuple[Thread, Thread, Thread, Thread]:
    """2-colour: Under thread is flipped if over is green"""
    if cross is Crossing.WARP:
        if left is Thread.RED:
            return (up, left, up, left)
        down = ({Thread.RED, Thread.GRN} - {up}).pop()
        return (up, left, down, left)
    else:
        if up is Thread.RED:
            return (up, left, up, left)
        right = ({Thread.RED, Thread.GRN} - {left}).pop()
        return (up, left, up, right)

@cache
def next_crossing_mod3(up: Thread, left: Thread, cross: Crossing) -> Tuple[Thread, Thread, Thread, Thread]:
    """3-colour: Sum the enumeration of the top and left and mod 3 it, under thread is changed to this colour

    This rotates the colour of the under thread by the enum value of the over thread. The mod 3 means we lose
    information so the rule does not work in th opposite direction. However. It still produces the sierpinski
    pattern and the padding threads are more distinctive.
    """
    out = Thread((up.value + left.value) % 3)
    if cross is Crossing.WARP:
        return (up, left, out, left)
    else:
        return (up, left, up, out)

@cache
def next_crossing_sub_mod3(up: Thread, left: Thread, cross: Crossing) -> Tuple[Thread, Thread, Thread, Thread]:
    """3-colour: Sub the enumeration of the under from the over and mod 3 it, under thread is changed to this colour
    """
    if cross is Crossing.WARP:
        out = Thread((left.value - up.value) % 3)
        return (up, left, out, left)
    else:
        out = Thread((up.value - left.value) % 3)
        return (up, left, up, out)

RULES = {
    'knot': next_crossing_knot,
    'xor': next_crossing_xor,
    'mod3': next_crossing_mod3,
    'smod3': next_crossing_sub_mod3,
}

def print_grid(grid: Grid):
    for row in grid:
        for cell in row:
            if Thread.RED == cell[0] == cell[2] or Thread.RED == cell[1] == cell[3]:
                print(' ', end='')
            else:
                print('+', end='')
        print('')

def render_cell(draw: ImageDraw, cell: Cell, coords: Tuple[int,int], bkg: Colour=(0,0,0)):
    cross = (Crossing.WARP, Crossing.WEFT)[sum(coords)%2]
    start = tuple(val * CELL_STRIDE for val in coords)
    end = tuple(val + CELL_STRIDE for val in start)
    draw.rectangle( (start, end), fill=bkg)
    ctr = tuple((s+e)//2 for s, e in zip(start, end))
    if cross is Crossing.WARP:
        draw.rectangle( ((ctr[0], start[1]), (ctr[0]+1, ctr[1]-2)), fill=COLOURS[cell[0]])
        draw.rectangle( ((ctr[0], ctr[1]+3), (ctr[0]+1, end[1])), fill=COLOURS[cell[2]])
        draw.rectangle( ((start[0], ctr[1]), (end[0], ctr[1]+1)), fill=COLOURS[cell[1]])
    else:
        draw.rectangle( ((start[0], ctr[1]), (ctr[0]-2, ctr[1]+1)), fill=COLOURS[cell[1]])
        draw.rectangle( ((ctr[0]+3, ctr[1]), (end[0], ctr[1]+1)), fill=COLOURS[cell[3]])
        draw.rectangle( ((ctr[0], start[1]), (ctr[0]+1, end[1])), fill=COLOURS[cell[0]])


def render_grid(size: int, grid: Grid, filename: str='sierpinski_carpet.png'):
    if not Image:
        print("Dependency 'pillow' is not installed", file=stderr)
        return
    im_size = size*CELL_STRIDE
    im = Image.new(mode="RGB", size=(im_size, im_size))
    im_draw = ImageDraw.Draw(im)
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            render_cell(
                im_draw,
                cell,
                (x, y)
            )
    im.save(filename)

def main(rank: int, rule: str='knot', filename: str='sierpinski_carpet.png'):

    next_crossing = RULES[rule]

    size = 3**rank + 1
    start_ys = start_threads()
    start_xs = start_threads()

    grid: Grid = [[(Thread.RED, Thread.RED, Thread.RED, Thread.RED) for _ in range(size)] for _ in range(size)]

    for y in range(size):
        for x in range(size):
            up = next(start_xs) if y == 0 else grid[y-1][x][2]
            left = next(start_ys) if x == 0 else grid[y][x-1][3]
            cross = (Crossing.WARP, Crossing.WEFT)[(x+y)%2]
            grid[y][x] = next_crossing(up, left, cross)

    # print_grid(grid)
    render_grid(size, grid, filename=filename)

if __name__ == '__main__':
    main(5, rule='knot', filename='rank_5_knot.png')
    main(5, rule='xor', filename='rank_5_xor.png')
    main(5, rule='mod3', filename='rank_5_mod3.png')
    main(5, rule='smod3', filename='rank_5_smod3.png')
