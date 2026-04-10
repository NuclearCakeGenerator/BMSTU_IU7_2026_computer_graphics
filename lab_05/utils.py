from dataclasses import dataclass
from enum import Enum, auto


WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 900
LEFT_PANEL_WIDTH = 320
CANVAS_WIDTH = 920
CANVAS_HEIGHT = 860


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class InteractionMode(Enum):
    EDITING = auto()
    STEP_FILL = auto()


class FillStep(Enum):
    BUILD_EDGE_LIST = auto()
    FIND_SCANLINE_RANGE = auto()
    COLLECT_INTERSECTIONS = auto()
    TOGGLE_FLAG = auto()
    PAINT_INTERVALS = auto()
    NEXT_SCANLINE = auto()


FILL_STEP_MESSAGES = {
    FillStep.BUILD_EDGE_LIST: (
        "Шаг 1: сформировать список ребер по всем замкнутым контурам."
    ),
    FillStep.FIND_SCANLINE_RANGE: (
        "Шаг 2: найти диапазон строк сканирования (min_y..max_y)."
    ),
    FillStep.COLLECT_INTERSECTIONS: (
        "Шаг 3: для текущей строки найти пересечения с активными ребрами."
    ),
    FillStep.TOGGLE_FLAG: (
        "Шаг 4: отсортировать X пересечений и переключать флаг inside/outside."
    ),
    FillStep.PAINT_INTERVALS: "Шаг 5: закрасить интервалы, где флаг inside = True.",
    FillStep.NEXT_SCANLINE: "Шаг 6: перейти к следующей строке и повторить.",
}
