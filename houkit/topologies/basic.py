from typing import Sequence, Any, Iterator

from hou import Point, Vector3, Prim, Polygon, Geometry

from ..attributings.operator import set_point_attrib
from ..attributings.querier import unique_points_by_attrib
from ..attributings.transferer import apply_prim_attribs
from .helper import is_same_geo


def points_to_positions(points: Sequence[Point]) -> Iterator[Vector3]:
    return (p.position() for p in points)


def add_point(
    geo: Geometry,
    position: Vector3,
    attributes: dict[str, Any] | tuple[str, Any] | None = None,
) -> Point:
    p: Point = geo.createPoint()
    p.setPosition(position)
    if attributes:
        if isinstance(attributes, tuple):
            assert len(attributes) == 2
            attributes = {attributes[0]: attributes[1]}
        for k, v in attributes.items():
            set_point_attrib(p, k, v)
    return p


def offset_point(
    point: Point,
    offset: Vector3,
) -> None:
    point.setPosition(point.position() + offset)


def fill_face(
    points: Sequence[Point],
    reverse_order: bool = False,
) -> Polygon:
    assert points

    assert is_same_geo(points)
    geo = points[0].geometry()

    clone = list(points)
    if reverse_order:
        clone.reverse()

    polygon = geo.createPolygon()
    for point in clone:
        polygon.addVertex(point)
    return polygon

def fill_faces(
    points: list[list[Point]],
    attributes: Sequence[tuple[dict[str, Any], list[str]]] | tuple[dict[str, Any], list[str]] = ()
) -> list[Prim]:
    prims: list[Prim] = []
    for pts in points:
        prims.append(fill_face(pts))
    if attributes:
        apply_prim_attribs(prims, attributes)
    return prims

def fill_face_by_attrib(
    geo: Geometry,
    attribute: str,
    values: Sequence[str],
    reverse_order: bool = False,
) -> Polygon:
    all_points = unique_points_by_attrib(geo, attribute)
    face_points: list[Point] = []
    for v in values:
        p = all_points.get(v)
        assert p is not None, f"Expected point with id {v}"
        face_points.append(p)
    return fill_face(face_points, reverse_order)


def remove_unused_points(
    geo: Geometry,
) -> None:
    unused = [p for p in geo.points() if not p.prims()]
    if unused:
        geo.deletePoints(unused)