import math
from typing import Callable, Sequence

import hou
from hou import Point, Vector3, Quaternion

from .geomaths import elliptical_interpolator


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


def get_line_face_intersection(
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


def get_point_on_ellipse_2d(
    origin: Vector3,
    vertical_end: Vector3,
    side_end: Vector3,
    rad_from_y: float = math.pi / 4,
) -> Vector3:
    """Evaluate a point on a planar ellipse arc parameterized by its semi-axes vectors."""
    return elliptical_interpolator.get_point_on_ellipse_2d(origin, vertical_end, side_end, rad_from_y)


def interpolate_conic(
    p0: Vector3 | Point,
    p1: Vector3 | Point,
    p2: Vector3 | Point,
    normal0: Vector3,
    normal1: Vector3,
) -> Callable[[float], tuple[tuple[Vector3, Vector3], ...]]:
    """
    Construct a planar conic passing through p0, p1, p2 with normals normal0 at p0 and normal1 at p1.

    The method projects the 3D problem into a 2D local orthonormal coordinate plane:
      - along_axis: direction from p0 to p1
      - across_axis: in-plane normal orthogonal to along_axis
    It sets up an algebraic conic equation:
      A * x² + B * x * y + C * y² + D * x + E * y = 0
    where (x, y) = (along, across) with p0 at (0, 0).
    The remaining 4 constraints (passage through p1, p2, and normal directions at p0, p1)
    form a 4x5 linear system solved via SVD for the 1D null space.

    :param p0: First point on conic (origin of the local 2D coordinate system).
    :param p1: Second point on conic.
    :param p2: Intermediate third point on conic.
    :param normal0: Inward normal vector at p0.
    :param normal1: Inward normal vector at p1.
    :return: A function that accepts a signed distance along the p0->p1 axis,
             and returns 0, 1, or 2 point and normal pairs in 3D space on the conic.
    """
    return elliptical_interpolator.interpolate_conic(p0, p1, p2, normal0, normal1)


def interpolate_elliptical(
    p0: Vector3 | Point,
    p1: Vector3 | Point,
    p2: Vector3 | Point,
    normal0: Vector3,
    normal2: Vector3,
) -> Callable[[float], tuple[Vector3, Vector3]]:
    """
    Construct a smooth elliptical 3D bulge passing through p0, p1, p2 with normals normal0 at p0 and normal2 at p2.

    The middle point p1 is explicitly treated as the apex/tip of the bulge relative to the baseline from p0 to p2.
    The curve is composed of two quintic polynomial segments (p0 -> p1 and p1 -> p2) joined at p1 with C² continuity.
    Tangent magnitudes and apex curvature are chosen by minimizing jerk energy.

    :param p0: Start point of the curve (t = 0.0).
    :param p1: Apex/peak point of the curve (bulge tip).
    :param p2: End point of the curve (t = 1.0).
    :param normal0: Inward normal vector at p0.
    :param normal2: Inward normal vector at p2.
    :return: A function that accepts a normalized parameter t in [0, 1]
            representing progress along the p0->p2 baseline chord axis (where 0.0 is p0 and 1.0 is p2),
            and returns the (position, in-plane inward normal) pair as hou.Vector3.
    """
    return elliptical_interpolator.interpolate_elliptical(p0, p1, p2, normal0, normal2)
