from dataclasses import dataclass
from math import hypot


WINDOW_WIDTH = 1460
WINDOW_HEIGHT = 940
LEFT_PANEL_WIDTH = 430
CANVAS_WIDTH = 960
CANVAS_HEIGHT = 880

BACKGROUND_COLOR = "#101317"
DEFAULT_CLIPPER_COLOR = "#31C48D"
DEFAULT_SEGMENT_COLOR = "#E5E7EB"
DEFAULT_RESULT_COLOR = "#F59E0B"

EPS = 1e-9


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Segment:
    start: Point
    end: Point


def vec_add(a: Point, b: Point) -> Point:
    return Point(a.x + b.x, a.y + b.y)


def vec_sub(a: Point, b: Point) -> Point:
    return Point(a.x - b.x, a.y - b.y)


def vec_mul(a: Point, k: float) -> Point:
    return Point(a.x * k, a.y * k)


def dot(a: Point, b: Point) -> float:
    return a.x * b.x + a.y * b.y


def cross(a: Point, b: Point) -> float:
    return a.x * b.y - a.y * b.x


def length(v: Point) -> float:
    return hypot(v.x, v.y)
