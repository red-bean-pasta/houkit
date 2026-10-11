from typing import Sequence

import hou
from hou import Vector3, Quaternion, Point

# noinspection PyUnusedImports
from .geomaths.elliptical_interpolator import (
    get_point_on_ellipse_2d,
    interpolate_conic,
    interpolate_elliptical,
)


def is_zero_approx(a: float, tol: float = 1e-5) -> bool:
    return abs(a) <= tol

def is_equal_approx(a: float, b: float, tol: float = 1e-5) -> bool:
    return abs(a - b) <= tol


def rotation_to(a: Vector3, b: Vector3) -> Quaternion:
    q = Quaternion()
    q.setToVectors(a, b)
    return q

def rotate_positions(
    origin: Vector3,
    positions: Sequence[Vector3],
    axis: Vector3,
    degrees: float,
) -> tuple[Vector3, ...]:
    rot = hou.hmath.buildRotateAboutAxis(
        axis,
        degrees,
    )
    return tuple(
        (p - origin) * rot + origin
        for p in positions
    )


def line_intersect_face(
    line: tuple[Vector3, Vector3],
    face: tuple[Vector3, Vector3, Vector3],
    eps: float=1e-5
) -> Vector3 | None:
    a, b = line
    p0, p1, p2 = face

    d = b - a
    e1 = p1 - p0
    e2 = p2 - p0
    n = e1.cross(e2)
    denom = n.dot(d)
    # Line is parallel to plane
    if abs(denom) < eps:
        return None

    t = n.dot(p0 - a) / denom
    hit = a + d * t
    return hit


def point_distance_to_line(
    point: Vector3,
    line: tuple[Vector3, Vector3]
) -> float:
    p0, p1 = line

    v_line = p1 - p0
    len_line = v_line.length()
    assert len_line > 1e-6, "Expected nonzero mid_edge length"

    v = point - p0
    return v.cross(v_line).length() / len_line


def line_intersect_line(
    first_line: tuple[Vector3, Vector3],
    second_line: tuple[Vector3, Vector3],
) -> Vector3:
    first_start, first_end = first_line
    second_start, second_end = second_line
    first_direction = first_end - first_start
    second_direction = second_end - second_start
    normal = first_direction.cross(second_direction)
    denominator = normal.dot(normal)

    assert first_direction.length() > 1e-6, "Expected a nonzero first line"
    assert second_direction.length() > 1e-6, "Expected a nonzero second line"
    assert denominator > 1e-12, "Expected nonparallel lines"

    normal = normal.normalized()
    projected_second_start = second_start - normal * (second_start - first_start).dot(normal)
    offset = projected_second_start - first_start
    normal_length = denominator ** 0.5
    first_ratio = offset.cross(second_direction).dot(normal) / normal_length

    return first_start + first_direction * first_ratio


def direction_and_distance(
    source: Vector3 | Point,
    target: Vector3 | Point,
) -> tuple[Vector3, float]:
    ps = source.position() if isinstance(source, Point) else source
    pt = target.position() if isinstance(target, Point) else target
    diff = pt - ps
    distance = ps.distanceTo(pt)
    assert distance > 1e-6, "Expected distinct source and target positions"
    return diff.normalized(), distance


def project_point_on_line(
    point: Vector3 | Point,
    line: tuple[Vector3 | Point, Vector3 | Point],
) -> Vector3:
    p = point.position() if isinstance(point, Point) else point
    start = line[0].position() if isinstance(line[0], Point) else line[0]
    end = line[1].position() if isinstance(line[1], Point) else line[1]
    direction = end - start
    length_squared = direction.dot(direction)
    assert length_squared > 1e-12, "Expected a line with non-zero length"
    offset = p - start
    return start + direction * (offset.dot(direction) / length_squared)

project_point_on_edge = project_point_on_line


def reflect_point_across_line(
    point: Vector3 | Point,
    line: tuple[Vector3 | Point, Vector3 | Point],
) -> Vector3:
    projection = project_point_on_line(point, line)
    p = point.position() if isinstance(point, Point) else point
    return projection * 2.0 - p

reflect_point_across_edge = reflect_point_across_line

