from typing import Sequence, Iterator, Any

from hou import Geometry, Point, Prim, Vector3, Polygon, Face, Attrib

from .topologies import basic, extruder, helper, merger, sorter
from .topologies import loop_cutter
from .topologies import pentagon_handler, face_offseter
from .topologies import splitter
from .topologies.helper import Edge
from .topologies.sorter import Axis


def points_to_positions(points: Sequence[Point]) -> Iterator[Vector3]:
    return basic.points_to_positions(points)


def add_point(
    geo: Geometry,
    position: Vector3,
    attributes: dict[str | Attrib, Any] | tuple[str | Attrib, Any] | None = None,
) -> Point:
    return basic.add_point(geo, position, attributes)


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
    return sorter.sort_points_by_position(points, axis_order, axis_ascending, tolerance)


def is_neighbor(p1: Point, p2: Point) -> bool:
    return helper.is_neighbor(p1, p2)


def check_neighbors(target: Point, samples: Sequence[Point]) -> list[Point]:
    return helper.check_neighbors(target, samples)


def get_first_neighbor(target: Point, samples: Sequence[Point]) -> Point | None:
    return helper.get_first_neighbor(target, samples)


def get_prims_normal(prims: Prim | Face | Sequence[Prim]) -> Vector3:
    return helper.get_prims_normal(prims)


def get_prim_normal(prim: Prim | Face) -> Vector3:
    return helper.get_prim_normal(prim)


def unique_prim_points(prims: Sequence[Prim]) -> list[Point]:
    return helper.unique_prim_points(prims)


def get_edge_prim_count(prims: Sequence[Prim]) -> dict[Edge, int]:
    return helper.get_edge_prim_count(prims)


def get_prim_centroid(prims: Prim | Sequence[Prim]) -> Vector3:
    return helper.get_prim_centroid(prims)


def find_prim(
    *points: Point
) -> Prim:
    """Return the first primitive containing ``reference_point`` and all required points."""
    reference, *rest = points
    return next(find_prims(reference, *rest))

def find_prims(
    *points: Point
) -> Iterator[Prim]:
    """Return the primitives containing ``reference_point`` and all required points."""
    reference, *rest = points
    return helper.find_prims(reference, *rest)


def interpolate_point(
    p0: Point,
    p1: Point,
    ratio: float,
) -> Vector3:
    return helper.interpolate_point(p0, p1, ratio)


def point_distance_to_line(
    point: Point,
    line: Edge | tuple[Point, Point],
) -> float:
    return helper.point_distance_to_line(point, line)


def get_line_intersection(
    first_line: tuple[Point, Point],
    second_line: tuple[Point, Point],
) -> Vector3:
    """Return the projected intersection of two 3D lines on first line."""
    return helper.get_line_intersection(first_line, second_line)


def order_prim_points(
    points: Sequence[Point],
    edge: tuple[Point, Point],
    assert_count: int | None = None,
) -> list[Point]:
    return helper.order_prim_points(points, edge, assert_count)


def offset_point(
    point: Point,
    offset: Vector3,
) -> None:
    basic.offset_point(point, offset)


def fill_face(
    points: Sequence[Point],
    reverse: bool = False,
) -> Polygon:
    return basic.fill_face(points, reverse)


def fill_faces(
    points: list[list[Point]],
    attributes: Sequence[tuple[dict[str, Any], list[str]]] | tuple[dict[str, Any], list[str]] = (),
) -> list[Prim]:
    return basic.fill_faces(points, attributes)


def fill_face_by_attrib(
    geo: Geometry,
    attribute: str,
    values: Sequence[str],
    reverse_order: bool = False,
) -> Polygon:
    return basic.fill_face_by_attrib(geo, attribute, values, reverse_order)


def traverse_faces_between_edges(
    edge_start: tuple[Point, Point],
    edge_end: tuple[Point, Point],
    side_point: Point | None = None,
    limit: int = 100,
) -> list[Prim]:
    """

    :param edge_start:
    :param edge_end:
    :param side_point: Optional point to disambiguate the traverse direction. This point must be share a quad with edge_start.
    :param limit: Maximum count of returned faces
    :return:
    """
    return helper.traverse_faces_between_edges(edge_start, edge_end, side_point, limit)


def extrude(
    prims: Prim | Sequence[Prim],
    dist: float,
    normal: Vector3 | None = None,
    delete_original: bool = True,
) -> dict[Prim, list[Prim]]:
    """

    :param prims:
    :param dist:
    :param normal: Offset vector. If None, the averaged unit normal of prims will be used
    :param delete_original: If true, the source prims will be deleted
    :return: The duplicated faces followed by faces connecting their boundary to the source
    """
    return extruder.extrude(prims, dist, normal, delete_original)


def inset(
    prims: list[Prim],
    scalar: float,
    use_ratio: bool = True,
    follow_existing_edge: bool = True,
) -> dict[tuple[Prim, ...], list[Prim]]:
    """
    Perform an inset operation on a collection of polygon primitives.
    - Groups primitives into connected components and insets each component independently.
    - Offsets boundary vertices inward by distance or ratio and generates border quad faces (trapezoids).
    - If scalar is negative, delegates to outset.
    - Preserves primitive attributes and primitive group memberships across divided primitives.
    - Preserves point attributes and group memberships on newly generated inset points.

    :param prims:
    :param scalar:
    :param use_ratio: If True, scalar is interpreted as a ratio; otherwise as absolute distance.
    :param follow_existing_edge:
    :return: List of inner inset primitives.
    """
    return face_offseter.inset(prims, scalar, use_ratio, follow_existing_edge)


def outset(
    prims: list[Prim],
    scalar: float,
    use_ratio: bool = False,
    follow_existing_edge: bool = True,
) -> dict[tuple[Prim, ...], list[Prim]]:
    """Perform an outset operation on a collection of polygon primitives.
    - Groups primitives into connected components and outsets each component independently.
    - Offsets boundary vertices outward by distance or ratio and generates border quad faces around the exterior.
    - If scalar is negative, delegates to inset.
    - Preserves primitive attributes and primitive group memberships on newly created border primitives.
    - Preserves point attributes and group memberships on newly generated outset points.

    :param prims: List of polygon primitives to outset.
    :param scalar: Offset ratio or world distance. Negative values trigger inset.
    :param use_ratio: If True, scalar is interpreted as a ratio; otherwise as absolute distance.
    :param follow_existing_edge:
    :return: List of newly generated outer border quad primitives.
    """
    return face_offseter.outset(prims, scalar, use_ratio, follow_existing_edge)


def partition_connected_prims(
    prims: list[Prim],
) -> list[tuple[Prim]]:
    return face_offseter.partition_connected_prims(prims)


def loop_cut(
    prim: Prim,
    start_point: Point,
    end_point: Point,
    scalar: float,
    use_ratio: bool = True,
    scope: list[Prim] | None = None,
) -> dict[tuple[Point, Point], tuple[Prim, Prim]]:
    """Perform a loop cut across adjacent quads starting from a specified edge of a quad primitive.

    - Places points interpolated between the start side and end side of each quad's cut edge.
    - Propagates across quad topology in both directions from the starting edge until reaching an open boundary, non-quad geometry, out-of-scope primitive, or looping back.
    - Deletes affected primitives and refills faces (end-side faces first, followed by start-side faces).
    - Preserves all primitive attributes and primitive group memberships across divided primitives.

    :param prim: The initial quad primitive.
    :param start_point: Starting point of the initial edge to cut.
    :param end_point: Ending point of the initial edge to cut.
    :param scalar: Ratio (in [0, 1]) or distance from start_point along the edge.
    :param use_ratio: If True, scalar is interpreted as a ratio; otherwise as a distance.
    :param scope: Optional list of primitives to restrict propagation to.
    :return: Tuple of (added_points, start_side_prims).
    """
    return loop_cutter.loop_cut(prim, start_point, end_point, scalar, use_ratio, scope)


def fill_pentagon(
    points: Sequence[Point],
    midpoint_edge: tuple[Point, Point],
    reverse_order: bool = False,
) -> tuple[Point, Point]:
    """
    Subdivide a pentagon into 3 quads by placing a midpoint on one edge and an internal floating point.

    :param points: 5 cyclic points of the pentagon.
    :param midpoint_edge: Tuple of 2 adjacent points defining the edge to split.
    :param reverse_order:
    :return: Tuple of (midpoint on specified midpoint_edge, interior float point).
    """
    return pentagon_handler.fill_pentagon(points, midpoint_edge, reverse_order)


def fill_pentagon_with_buffer(
    points: Sequence[Point],
    buffer_edge: tuple[Point, Point],
    buffer_ratio: float,
    midpoint_edge: tuple[Point, Point],
    reverse_order: bool = False,
) -> tuple[Point, Point, Point, Point]:
    """Subdivide a pentagon with a buffer quad adjacent to buffer_edge, then subdivide the remainder into 3 quads.

    :param points: 5 cyclic points of the pentagon.
    :param buffer_edge: Tuple of 2 adjacent points defining the edge to buffer.
    :param buffer_ratio: Ratio along the connected edges from buffer_edge (in [0, 1)).
    :param midpoint_edge: Tuple of 2 adjacent points defining the edge to split in the pentagon.
    :param reverse_order:
    :return: Tuple of (midpoint, interior float point, buffer_point_a, buffer_point_b).
    """
    return pentagon_handler.fill_pentagon_with_buffer(points, buffer_edge, buffer_ratio, midpoint_edge, reverse_order)


def merge_points(
    pairs: Sequence[tuple[Point, Point]] | tuple[Point, Point],
) -> None:
    """
    Merge multiple (target_point, source_point) pairs simultaneously.
    - For each pair (target, source), replaces all occurrences of `source` in attached primitives with `target`.
    - Deletes `source` points.
    - Reconstructs affected primitives preserving primitive attributes and primitive group memberships.
    """
    merger.merge_points(pairs)


def split_point(
    prims: Prim | Sequence[Prim],
    point: Point,
) -> tuple[Point, list[Prim]]:
    """Split ``point`` from the selected primitives.

    The selected primitives are rebuilt with a new point at the same position.
    Point and primitive attributes, including group membership, are preserved.
    """
    return splitter.split_point(prims, point)


def is_same_geo(sequence: Sequence[Any]) -> bool:
    return helper.is_same_geo(sequence)
