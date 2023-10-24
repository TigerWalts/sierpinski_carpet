from enum import Enum
from enum import auto
from functools import cache
from typing import Tuple

from thread import Thread


class Crossing(Enum):
    WARP = 0
    WEFT = auto()


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
