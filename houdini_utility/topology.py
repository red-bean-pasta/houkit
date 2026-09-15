from typing import Sequence, Iterator, Any

from hou import Point, Prim, Vector3, Polygon, Face

from .topologies import basic, extruder, helper, merger
from .topologies import loop_cutter
from .topologies import pentagon_handler, face_offseter


def points_to_positions(points: Sequence[Point]) -> Iterator[Vector3]:
    return basic.points_to_positions(points)


def get_prims_normal(prims: Prim | Face | Sequence[Prim]) -> Vector3:
    return helper.get_prims_normal(prims)


def get_prim_centroid(prims: Prim | Sequence[Prim]) -> Vector3:
    return helper.get_prim_centroid(prims)


def find_prim(
    *points: Point
) -> Prim:
    """Return the first primitive containing ``reference_point`` and all required points."""
    reference, *rest = points
    return helper.find_prim(reference, *rest)


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


def is_same_geo(sequence: Sequence[Any]) -> bool:
    return helper.is_same_geo(sequence)