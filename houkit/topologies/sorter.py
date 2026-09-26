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
    tolerance: float = 1e-5,
) -> list[Point]:
    """

    :param points:
    :param axis_order: Axes to compare, from highest to lowest priority.
    :param axis_ascending: Sort direction for each axis in ``axis_order``. ``True`` placing smaller coordinates first.
    :param tolerance:
    """
    return sorted(
        points,
        key=lambda point: _position_sort_key(point, axis_order, axis_ascending, tolerance),
    )

def _position_sort_key(
    point: Point,
    axis_order: tuple[Axis, Axis, Axis],
    axis_ascending: tuple[bool, bool, bool],
    tolerance: float = 1e-5,
) -> tuple[int, int, int]:
    position = point.position()
    return tuple(
        round(position[axis.value] / tolerance) * (1 if ascending else -1)
        for axis, ascending in zip(axis_order, axis_ascending)
    )
