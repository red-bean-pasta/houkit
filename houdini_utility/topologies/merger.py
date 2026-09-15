from typing import Sequence, Any

from hou import Point

from ..attributings.transferer import collect_prim_attribs
from .basic import fill_faces


def merge_points(
        pairs: Sequence[tuple[Point, Point]] | tuple[Point, Point],
) -> None:
    if _is_single_data(pairs):
        pairs = (pairs,)
    if not pairs:
        return

    target_map = {
        src: dst
        for dst, src in pairs
        if src != dst
    }
    if not target_map:
        return

    geo = pairs[0][0].geometry()
    to_delete_pts = set(target_map.keys())
    affected_prims = list({prim for pt in to_delete_pts for prim in pt.prims()})
    attr_data = collect_prim_attribs(affected_prims)

    if not affected_prims:
        geo.deletePoints(list(to_delete_pts))
        return

    new_face_points: list[list[Point]] = []
    valid_attr_data: list[tuple[dict[str, Any], list[str]]] = []
    for prim, attrs in zip(affected_prims, attr_data):
        new_pts: list[Point] = []

        for pt in prim.points():
            pt = target_map.get(pt, pt)
            if not new_pts or pt != new_pts[-1]:
                new_pts.append(pt)

        # First and last vertices are adjacent in a closed polygon.
        if len(new_pts) > 1 and new_pts[0] == new_pts[-1]:
            new_pts.pop()

        if len(new_pts) >= 3:
            new_face_points.append(new_pts)
            valid_attr_data.append(attrs)

    geo.deletePrims(affected_prims, keep_points=True)
    if new_face_points:
        fill_faces(new_face_points, valid_attr_data)
    geo.deletePoints(list(to_delete_pts))


def _is_single_data(
    x: Sequence[tuple[Point, Point]] | tuple[Point, Point]
) -> bool:
    return (
        isinstance(x, tuple)
        and len(x) == 2
        and isinstance(x[0], Point)
        and isinstance(x[1], Point)
    )
