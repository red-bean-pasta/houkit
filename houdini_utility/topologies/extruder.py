from typing import Sequence, Any

from hou import Prim, Vector3, Point

from .basic import fill_face
from .helper import get_prims_normal, get_edge_prim_count, Edge
from .helper import is_same_geo, unique_prim_points
from ..attributings.transferer import collect_prim_attribs, copy_point_attribs, apply_prim_attribs


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
    prims = _normalize_prims(prims)
    if normal is None:
        normal = get_prims_normal(prims)

    geo = prims[0].geometry()
    edge_counts = get_edge_prim_count(prims)
    source_attrs = collect_prim_attribs(prims)
    source_loops = [list(prim.points()) for prim in prims]

    point_map = _extrude_points(prims, normal, dist)

    if delete_original:
        geo.deletePrims(list(prims), keep_points=True)

    return _extrude_faces(source_loops, source_attrs, edge_counts, point_map)


def _normalize_prims(prims: Prim | Sequence[Prim]) -> list[Prim]:
    result = [prims] if not isinstance(prims, Sequence) else list(prims)
    assert result, "Expected at least one primitive"
    assert is_same_geo(result), "Expected primitives from one geometry"
    return result


def _extrude_points(
    prims: Sequence[Prim],
    normal: Vector3,
    dist: float,
) -> dict[Point, Point]:
    geo = prims[0].geometry()
    result: dict[Point, Point] = {}
    for point in unique_prim_points(prims):
        extruded = geo.createPoint()
        extruded.setPosition(point.position() + normal * dist)
        copy_point_attribs(point, extruded)
        result[point] = extruded
    return result

def _extrude_faces(
        points: list[list[Point]],
        attributes: list[tuple[dict[str, Any], list[str]]],
        edge_counts: dict[Edge, int],
        extruded_points: dict[Point, Point],
) -> dict[Prim, list[Prim]]:
    geo = points[0][0].geometry()
    created_faces: dict[Prim, list[Prim]] = {}
    created_attrs: dict[Prim, tuple[dict[str, Any], list[str]]] = {}
    for source_points, source_attr in zip(points, attributes):
        extruded_face = fill_face([extruded_points[point] for point in source_points])

        created_faces[extruded_face] = []
        created_attrs[extruded_face] = source_attr

        for index, start in enumerate(source_points):
            end = source_points[(index + 1) % len(source_points)]
            edge = Edge.from_points(start, end, reorder=True)
            if edge_counts[edge] != 1:
                continue
            side_face = fill_face(
                [start, end, extruded_points[end], extruded_points[start]],
            )
            created_faces[extruded_face].append(side_face)

    for d, s in created_faces.items():
        apply_prim_attribs([d] + s, created_attrs[d])
    return created_faces
