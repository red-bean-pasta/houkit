from typing import Sequence

from hou import Prim, Point

from ..attributings.transferer import collect_prim_attribs, copy_point_attribs
from .basic import fill_faces
from .helper import is_same_geo


def split_point(
    prims: Prim | Sequence[Prim],
    point: Point,
) -> tuple[Point, list[Prim]]:
    """Split ``point`` from the selected primitives.

    The selected primitives are rebuilt with a new point at the same position.
    Point and primitive attributes, including group membership, are preserved.
    """
    if isinstance(prims, Prim):
        prims = (prims,)

    assert prims, "Expected at least one primitive"
    assert all(point in prim.points() for prim in prims)

    assert is_same_geo(prims)
    geo = prims[0].geometry()
    prim_attrs = collect_prim_attribs(prims)

    split = geo.createPoint()
    split.setPosition(point.position())
    copy_point_attribs(point, split)

    split_points = [
        [split if pt == point else pt for pt in prim.points()]
        for prim in prims
    ]

    geo.deletePrims(list(prims), keep_points=True)
    return split, fill_faces(split_points, prim_attrs)
