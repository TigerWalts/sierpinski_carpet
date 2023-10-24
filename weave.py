from sys import stderr
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

from palette import Colour
from palette import PALLETE
from rules import Crossing
from rules import RULES
from thread import THREAD_GENS
from thread import Thread

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = False

CELL_STRIDE = 5

COLOURS: dict[Thread, Colour] = {
    Thread.RED: PALLETE[0],
    Thread.GRN: PALLETE[1],
    Thread.BLU: PALLETE[2],
    Thread.YEL: PALLETE[3],
}

Cell = Tuple[Thread, Thread, Thread, Thread]
Grid = List[List[Cell]]


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


def main(
    rank:           int,
    rule:           str=                                                    'knot',
    start_threads:  Tuple[str,str]=                                         ('g-r..', 'g-r..'),
    thread_gens:    Optional[Tuple[Iterator[Thread], Iterator[Thread]]]=    None,
    filename:       str=                                                    'sierpinski_carpet.png'
):

    next_crossing = RULES[rule]
    size = 3**rank + 1

    if thread_gens is None:
        start_ys, start_xs = tuple(THREAD_GENS[s]() for s in start_threads)
    else:
        start_ys, start_xs = thread_gens

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
    main(5, rule='knot', start_threads=('b-g-r', 'r-g-b'), filename='rank_5_knot_bgr_rgb.png')
