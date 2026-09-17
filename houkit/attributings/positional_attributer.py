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
