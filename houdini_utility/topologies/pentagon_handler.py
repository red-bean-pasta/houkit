from typing import Sequence

from hou import Point, Vector3

from .basic import add_point
from .basic import fill_face
from .helper import is_same_geo, point_distance_to_line, interpolate_point, order_prim_points


def fill_pentagon(
    points: Sequence[Point],
    midpoint_edge: tuple[Point, Point],
    reverse_order: bool = False,
) -> tuple[Point, Point]:
    ordered = order_prim_points(points, midpoint_edge, 5)
    p0, p1, p2, p3, p4 = ordered

    assert is_same_geo(ordered)
    geo = p0.geometry()

    midpoint = add_point(
        geo,
        (p0.position() + p1.position()) * 0.5,
    )

    float_pos = _get_float_position(ordered)
    floatpoint = add_point(geo, float_pos)

    fill_face([p1, midpoint, floatpoint, p2], reverse_order)
    fill_face([midpoint, p0, p4, floatpoint], reverse_order)
    fill_face([floatpoint, p4, p3, p2], reverse_order)

    return midpoint, floatpoint


def fill_pentagon_with_buffer(
    points: Sequence[Point],
    buffer_edge: tuple[Point, Point],
    buffer_ratio: float,
    midpoint_edge: tuple[Point, Point],
    reverse_order: bool = False,
) -> tuple[Point, Point, Point, Point]:
    assert 0.0 <= buffer_ratio < 1.0, f"buffer_ratio must be in [0.0, 1.0), got {buffer_ratio}"
    assert set(midpoint_edge) != set(buffer_edge), f"midpoint_edge {midpoint_edge} cannot be buffer_edge {buffer_edge}"

    p_start, p_end, p_next, p_mid, p_prev = order_prim_points(points, buffer_edge, 5)

    if buffer_ratio == 0.0:
        midpoint, floatpoint = fill_pentagon(points, midpoint_edge, reverse_order)
        return midpoint, floatpoint, buffer_edge[0], buffer_edge[1]

    geo = p_start.geometry()

    b_start = add_point(
        geo,
        interpolate_point(p_start, p_prev, buffer_ratio)
    )
    b_end = add_point(
        geo,
        interpolate_point(p_end, p_next, buffer_ratio)
    )
    fill_face([p_start, b_start, b_end, p_end], reverse_order)

    pentagon_points = [b_start, b_end, p_next, p_mid, p_prev]
    pentagon_midedge = _update_buffered_midedge(midpoint_edge, (p_start, p_end), (b_start, b_end))
    midpoint, floatpoint = fill_pentagon(pentagon_points, pentagon_midedge, reverse_order)

    if buffer_edge[0] == p_start:
        return midpoint, floatpoint, b_start, b_end
    else:
        return midpoint, floatpoint, b_end, b_start


def _get_float_position(ordered_points: list[Point]) -> Vector3:
    p0, p1, p2, p3, p4 = ordered_points
    edge = (p0, p1)

    dist_p2 = point_distance_to_line(p2, edge)
    dist_p4 = point_distance_to_line(p4, edge)
    if dist_p2 <= dist_p4:
        m_base = (p0.position() + p4.position()) / 2.0
        f_pos = (p2.position() + m_base) / 2.0
    else:
        m_base = (p1.position() + p2.position()) / 2.0
        f_pos = (p4.position() + m_base) / 2.0

    return f_pos


def _update_buffered_midedge(
    mid_edge: tuple[Point, Point],
    buff_edge: tuple[Point, Point],
    buffer_points: tuple[Point, Point],
) -> tuple[Point, Point]:
    result = mid_edge
    for i in range(2):
        result = tuple(
            buffer_points[i]
            if p == buff_edge[i] else
            p
            for p in result
        )
    return result
