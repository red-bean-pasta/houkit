from typing import Mapping, Sequence

from hou import Point

from houkit.topologies.sorter import Axis, sort_points_by_position


def set_point_attribs_by_position(
    points: Sequence[Point],
    attrib_name: str,
    name_prefix: str,
    axis_order: tuple[Axis, Axis, Axis],
    axis_ascending: tuple[bool, bool, bool] = (True, True, True),
    start_index: int = 0,
    special_labels: Mapping[int, str] | None = None,
    reuse_index_after_special: bool = True,
    tolerance: float = 1e-5,
) -> None:
    """Set an indexed string attribute on points ordered by position.

    :param points: Points to label. The input sequence is not reordered.
    :param attrib_name: Name of the point attribute to set.
    :param name_prefix: Prefix for generated attribute values.
    :param axis_order: Axes to compare, from highest to lowest priority.
    :param axis_ascending: Sort direction for each axis in ``axis_order``. ``True`` placing smaller coordinates first.
    :param start_index: Numeric suffix assigned to the first sorted point.
    :param special_labels: Replacement labels keyed by their generated index.
    :param reuse_index_after_special: Whether special labels leave the next regular numeric suffix unchanged.
    :param tolerance:
    """
    sorted_points = sort_points_by_position(points, axis_order, axis_ascending, tolerance)

    next_numeric_index = start_index
    for global_index, point in enumerate(sorted_points, start=start_index):
        if special_labels is not None and global_index in special_labels:
            point.setAttribValue(attrib_name, special_labels[global_index])
            if not reuse_index_after_special:
                next_numeric_index += 1
            continue
        point.setAttribValue(attrib_name, f"{name_prefix}{next_numeric_index}")
        next_numeric_index += 1
