from functools import cache
from sys import stderr
from typing import Any, Sequence
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

from palette import Colour, Palette
from palette import PALETTE
from rules import Crossing
from rules import RuleFunc
from rules import RULES
from thread import THREAD_GENS
from thread import Thread

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = False

CELL_STRIDE = 5


Cell = Tuple[Thread, Thread, Thread, Thread]
Grid = List[List[Cell]]


@cache
def get_tile_image(cell: Cell, cross: Crossing, bkg: Colour=(0,0,0), palette: Palette=PALETTE) -> Image:
    im = Image.new(mode="RGB", size=(CELL_STRIDE, CELL_STRIDE))
    draw = ImageDraw.Draw(im)
    sta_x = sta_y = 0
    end_x = end_y = CELL_STRIDE
    ctr_x = ctr_y = CELL_STRIDE//2
    draw.rectangle( ((sta_x, sta_y), (end_x, end_y)), fill=bkg)
    print(cell)
    if cross is Crossing.WARP:
        draw.rectangle( ((ctr_x,   sta_y),   (ctr_x+1, ctr_y-2)), fill=palette[cell[0].value])
        draw.rectangle( ((ctr_x,   ctr_y+3), (ctr_x+1, end_y)),   fill=palette[cell[2].value])
        draw.rectangle( ((sta_x,   ctr_y),   (end_x,   ctr_y+1)), fill=palette[cell[1].value])
    else:
        draw.rectangle( ((sta_x,   ctr_y),   (ctr_x-2, ctr_y+1)), fill=palette[cell[1].value])
        draw.rectangle( ((ctr_x+3, ctr_y),   (end_x,   ctr_y+1)), fill=palette[cell[3].value])
        draw.rectangle( ((ctr_x,   sta_y),   (ctr_x+1, end_y)),   fill=palette[cell[0].value])
    return im


def render_cell(im: Image, cell: Cell, coords: Tuple[int,int], bkg: Colour=(0,0,0), palette: Palette=PALETTE):
    cross = (Crossing.WARP, Crossing.WEFT)[sum(coords)%2]
    start = tuple(val * CELL_STRIDE for val in coords)
    tile_im = get_tile_image(cell, cross, bkg, palette)
    im.paste(tile_im, start)


def render_grid(size: int, grid: Grid, palette: Palette=PALETTE, filename: str='sierpinski_carpet.png'):
    if not Image:
        print("Dependency 'pillow' is not installed", file=stderr)
        return
    im_size = size*CELL_STRIDE
    im = Image.new(mode="RGB", size=(im_size, im_size))
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            render_cell(
                im,
                cell,
                (x, y),
                palette=palette
            )
    im.save(filename)


def make_grid(h: int, w: int, fill: Any) -> Grid:
    return [[fill for _ in range(w)] for _ in range(h)]


@cache
def weave2(thread_seqs: Tuple[Sequence[Cell],Sequence[Cell]], cross: Crossing, rule: RuleFunc) -> Grid:
    start_ys, start_xs = thread_seqs
    y_len, x_len = len(start_ys), len(start_xs)
    if y_len == x_len == 0:
        return []
    if y_len == x_len == 1:
        return [[rule(start_ys[0][3], start_xs[0][2], cross)]]
    y_split, x_split = y_len // 2, x_len // 2
    r = Thread.RED
    ul = weave2(
        (
            tuple((r,r,r,t[3]) for t in start_ys[:y_split]),
            tuple((r,r,t[2],r) for t in start_xs[:x_split]),
        ),
        cross,
        rule
    )
    ur = weave2(
        (
            tuple((r,r,r,t[3]) for t in tuple(row[-1] for row in ul if len(row) > 0)),
            tuple((r,r,t[2],r) for t in start_xs[x_split:]),
        ),
        Crossing((cross.value + x_split) % 2),
        rule
    )
    bl = weave2(
        (
            tuple((r,r,r,t[3]) for t in start_ys[y_split:]),
            tuple((r,r,t[2],r) for t in tuple((ul[-1] if len(ul) > 0 else []))),
        ),
        Crossing((cross.value + y_split) % 2),
        rule
    )
    br = weave2(
        (
            tuple((r,r,r,t[3]) for t in tuple(row[-1] for row in bl if len(row) > 0)),
            tuple((r,r,t[2],r) for t in tuple((ul[-1] if len(ur) > 0 else []))),
        ),
        Crossing((cross.value + y_split + x_split) % 2),
        rule
    )
    quads = (
        (ul, ur),
        (bl, br),
    )
    return [
        [
            quads[y//y_split][x//x_split][y%y_split][x%x_split]
            for x
            in range(x_len)
        ]
        for y
        in range(y_len)
    ]



def weave(grid: Grid, thread_gens: Tuple[Iterator[Thread], Iterator[Thread]], rule: RuleFunc) -> Grid:
    start_ys, start_xs = thread_gens
    for y, row in enumerate(grid):
        for x, _ in enumerate(row):
            up = next(start_xs) if y == 0 else grid[y-1][x][2]
            left = next(start_ys) if x == 0 else grid[y][x-1][3]
            cross = (Crossing.WARP, Crossing.WEFT)[(x+y)%2]
            grid[y][x] = rule(up, left, cross)
    return grid


def main(
    rank:           int,
    rule:           str=                                                    'knot',
    start_threads:  Tuple[str,str]=                                         ('g-r..', 'g-r..'),
    thread_gens:    Optional[Tuple[Iterator[Thread], Iterator[Thread]]]=    None,
    filename:       str=                                                    'sierpinski_carpet.png'
):

    next_crossing, _ = RULES[rule]
    size = 3**rank + 1

    if thread_gens is None:
        thread_gens = tuple(THREAD_GENS[s]() for s in start_threads)

    grid = make_grid(size, size, (Thread.RED, Thread.RED, Thread.RED, Thread.RED))

    # grid = weave(grid, thread_gens, next_crossing)
    
    r = Thread.RED
    grid = weave2(
        (
            tuple((r,r,r,next(thread_gens[0])) for _ in range(size)),
            tuple((r,r,next(thread_gens[1]),r) for _ in range(size))
        ),
        Crossing(0),
        next_crossing
    )

    render_grid(size, grid, filename=filename)


if __name__ == '__main__':
    main(5, rule='knot', filename='rank_5_knot.png')
    main(5, rule='xor', filename='rank_5_xor.png')
    main(5, rule='mod3', filename='rank_5_mod3.png')
    main(5, rule='smod3', filename='rank_5_smod3.png')
    main(5, rule='knot', start_threads=('b-g-r', 'r-g-b'), filename='rank_5_knot_bgr_rgb.png')
