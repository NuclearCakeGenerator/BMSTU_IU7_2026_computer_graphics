from dataclasses import dataclass


WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 920
LEFT_PANEL_WIDTH = 360
CANVAS_WIDTH = 920
CANVAS_HEIGHT = 860

BACKGROUND_COLOR = "#101317"
DEFAULT_CLIPPER_COLOR = "#31C48D"
DEFAULT_SEGMENT_COLOR = "#E5E7EB"
DEFAULT_RESULT_COLOR = "#F59E0B"


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Segment:
    start: Point
    end: Point


@dataclass(frozen=True)
class Rect:
    left: float
    top: float
    right: float
    bottom: float


def normalize_rect(first: Point, second: Point) -> Rect:
    left = min(first.x, second.x)
    right = max(first.x, second.x)
    top = min(first.y, second.y)
    bottom = max(first.y, second.y)
    return Rect(left=left, top=top, right=right, bottom=bottom)