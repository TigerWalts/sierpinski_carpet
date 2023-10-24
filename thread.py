from enum import Enum
from enum import auto
from itertools import cycle
from typing import Callable
from typing import Generator
from typing import Iterator
from typing import Sequence


class Thread(Enum):
    RED = 0
    GRN = auto()
    BLU = auto()
    YEL = auto()


ThreadIteratorFactory = Callable[[], Iterator[Thread]]


def cycle_threads(threads: Sequence[Thread], offset: int=0) -> Callable[[], Iterator[Thread]]:
    """Returns a function that returns an itertools.cycle over a sequence of Threads"""
    if len(threads) == 0:
        raise ValueError("sequence given to cycle_threads is empty")
    def func():
        gen = cycle(threads)
        for _ in range(offset):
            next(gen)
        return gen
    return func


def green_then_all_red_threads() -> Generator[Thread, None, None]:
    yield Thread.GRN
    while True:
        yield Thread.RED


RGB = Thread.RED, Thread.GRN, Thread.BLU
BGR = tuple(reversed(RGB))
RGBY = Thread.RED, Thread.GRN, Thread.BLU, Thread.YEL
YBGR = tuple(reversed(RGBY))


THREAD_GENS: dict[str, ThreadIteratorFactory] = {
    'g-r..': green_then_all_red_threads,
    'r-g-b': cycle_threads(RGB),
    'g-b-r': cycle_threads(RGB, offset=1),
    'b-r-g': cycle_threads(RGB, offset=2),
    'b-g-r': cycle_threads(BGR),
    'g-r-b': cycle_threads(BGR, offset=1),
    'r-b-g': cycle_threads(BGR, offset=2),
}
