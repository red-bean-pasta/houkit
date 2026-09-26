from collections import defaultdict
from typing import Sequence, Callable, Any

import hou
from hou import Geometry, Point

from .querier import points_start_with


def add_attrib(
    geo: Geometry,
    cls: hou.attribType,
    name: str,
    default: Any,
    skip_existing: bool = True,
) -> hou.Attrib:
    find_attrib = {
        hou.attribType.Point: geo.findPointAttrib,
        hou.attribType.Prim: geo.findPrimAttrib,
        hou.attribType.Vertex: geo.findVertexAttrib,
        hou.attribType.Global: geo.findGlobalAttrib,
    }[cls]
    found = find_attrib(name)
    if skip_existing and found:
        return found
    return geo.addAttrib(cls, name, default)


def set_point_attrib(
    point: Point,
    attribute: str | hou.Attrib,
    value: str,
) -> None:
    point.setAttribValue(attribute, value)

def set_points_attrib(
    points: Sequence[Point],
    attribute: str,
    values: str | Sequence[str],
) -> None:
    if isinstance(values, str) or not isinstance(values, Sequence):
        values = [values] * len(points)
    assert len(points) == len(values), "Expected matching point and value array sizes"
    for p_point, p_id in zip(points, values):
        set_point_attrib(p_point, attribute, p_id)


def remove_attribs(
    geo: Geometry,
    point_attributes: str | tuple[str, ...] | None = None,
    prim_attributes: str | tuple[str, ...] | None = None,
    global_attributes: str | tuple[str, ...] | None = None,
) -> None:
    for attribs, finder in zip(
        (point_attributes, prim_attributes, global_attributes),
        (geo.findPointAttrib, geo.findPrimAttrib, geo.findGlobalAttrib),
    ):
        if not attribs:
            continue
        if isinstance(attribs, str):
            attribs = (attribs,)
        for name in attribs:
            attrib = finder(name)
            if attrib is not None:
                attrib.destroy()


def modify_point_attribs(
    geo: Geometry,
    attribute: str,
    filtrate: Callable[[Point], bool],
    rename: Callable[[str], str | None],
) -> None:
    """Conditionally rename point attribute values matching a filter.

    :param geo: The Houdini geometry.
    :param attribute: The point attribute name.
    :param filtrate: Predicate to decide if point should be considered.
    :param rename: Transformation function returning new name or None to skip renaming.
    """
    for point in geo.points():
        if not filtrate(point):
            continue
        value = point.stringAttribValue(attribute)
        if not value:
            continue
        new_id = rename(value)
        if new_id is None:
            continue
        point.setAttribValue(attribute, new_id)


def deduplicate_point_attribs(
    geo: Geometry,
    attribute: str,
    prefix: str | tuple[str, ...] | None,
    add_affix: bool = False,
    keep_first: bool = True,
) -> None:
    """
    Deduplicate string attributes on points by either clearing duplicates or affixing sequential indices.

    :param geo: The Houdini geometry.
    :param attribute: The point attribute name.
    :param prefix: Optional prefix to filter points.
    :param add_affix: If true, affixes like "_1", "_2" will be added; otherwise duplicates after the first are cleared.
    :param keep_first: If true, first encountered point will keep the attribute, else the last;
    """
    points = points_start_with(geo, attribute, prefix) if prefix else geo.points()
    grouped: defaultdict[str, list[Point]] = defaultdict(list)
    for p in points:
        v = p.stringAttribValue(attribute)
        grouped[v].append(p)
    for value, duplicates in grouped.items():
        if len(duplicates) <= 1:
            continue
        if add_affix:
            for i, point in enumerate(duplicates):
                set_point_attrib(point, attribute, f"{value}_{i+1}")
        else:
            for point in (duplicates[1:] if keep_first else duplicates[:-1]):
                point.setAttribValue(attribute, "")
