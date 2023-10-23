from enum import Enum, auto
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

class Crossing(Enum):
    WARP = 0
    WEFT = auto()

Colour = Tuple[int, int, int]

palette1 = (
    (255,   0,   0),
    (  0, 255,   0),
    (  0,   0, 255),
)

palette2 = (
    (214, 126, 195),
    ( 24, 185, 196),
    (128,  65, 196),
)

PALLETE = palette2

COLOURS: dict[Thread, Colour] = {
    Thread.RED: PALLETE[0],
    Thread.GRN: PALLETE[1],
    Thread.BLU: PALLETE[2],
}

Cell = Tuple[Thread, Thread, Thread, Thread]
Grid = List[List[Cell]]

def start_threads() -> Generator[Literal[Thread.RED, Thread.GRN], Any, None]:
    yield Thread.GRN
    while True:
        yield Thread.RED

def next_crossing(up: Thread, left: Thread, cross: Crossing) -> Tuple[Thread, Thread, Thread, Thread]:
    if up == left:
        return (up, left, up, left)
    new = ({Thread.RED, Thread.GRN, Thread.BLU} - {up, left}).pop()
    if cross == Crossing.WARP:
        return (up, left, new, left)
    else:
        return (up, left, up, new)

def print_grid(grid: Grid):
    for row in grid:
        for cell in row:
            #if all(x == Thread.RED for x in cell):
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
    if cross == Crossing.WARP:
        draw.rectangle( ((ctr[0], start[1]), (ctr[0]+1, ctr[1]-2)), fill=COLOURS[cell[0]])
        draw.rectangle( ((ctr[0], ctr[1]+3), (ctr[0]+1, end[1])), fill=COLOURS[cell[2]])
        draw.rectangle( ((start[0], ctr[1]), (end[0], ctr[1]+1)), fill=COLOURS[cell[1]])
    else:
        draw.rectangle( ((start[0], ctr[1]), (ctr[0]-2, ctr[1]+1)), fill=COLOURS[cell[1]])
        draw.rectangle( ((ctr[0]+3, ctr[1]), (end[0], ctr[1]+1)), fill=COLOURS[cell[3]])
        draw.rectangle( ((ctr[0], start[1]), (ctr[0]+1, end[1])), fill=COLOURS[cell[0]])


def render_grid(size: int, grid: Grid):
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
                (x, y),
                # bkg=((0,0,0),(255,255,255))[(x+y)%2]
            )
    im.save('sierpinski_capet.png')

def main(rank: int):
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
    render_grid(size, grid)

if __name__ == '__main__':
    main(5)
