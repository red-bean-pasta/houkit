from enum import Enum
from typing import Sequence

from hou import Point


class Axis(Enum):
    X = 0
    Y = 1
    Z = 2


def sort_points_by_position(
    points: Sequence[Point],
    axis_order: tuple[Axis, Axis, Axis],
    axis_ascending: tuple[bool, bool, bool] = (True, True, True),
) -> list[Point]:
    return sorted(
        points,
        key=lambda point: _position_sort_key(point, axis_order, axis_ascending),
    )

def _position_sort_key(
    point: Point,
    axis_order: tuple[Axis, Axis, Axis],
    axis_ascending: tuple[bool, bool, bool],
) -> tuple[float, float, float]:
    position = point.position()
    return tuple(
        coordinate if ascending else -coordinate
        for axis, ascending in zip(axis_order, axis_ascending)
        for coordinate in (position[axis.value],)
    )
