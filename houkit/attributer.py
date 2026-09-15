"""
Utility functions for attribute-based identification, naming, and indexing of geometry elements (points, prims).
"""
from typing import Sequence, Callable, Any

import hou
from hou import Geometry, Point, Prim

from .attributings import transferer
from .attributings import querier, operator


def add_point_attrib(geo: Geometry, name: str, default: Any) -> hou.Attrib:
    return add_attrib(geo, hou.attribType.Point, name, default)

def add_prim_attrib(geo: Geometry, name: str, default: Any) -> hou.Attrib:
    return add_attrib(geo, hou.attribType.Prim, name, default)

def add_global_attrib(geo: Geometry, name: str, default: Any) -> hou.Attrib:
    return add_attrib(geo, hou.attribType.Global, name, default)

def add_attrib(
    geo: hou.Geometry,
    cls: hou.attribType,
    name: str,
    default: Any,
    skip_existing: bool = True,
) -> hou.Attrib:
    return operator.add_attrib(geo, cls, name, default, skip_existing)


def set_point_attrib(
    point: Point,
    attribute: str,
    value: str,
) -> None:
    operator.set_point_attrib(point, attribute, value)

def set_points_attrib(
    points: Sequence[Point],
    attribute: str,
    values: str | Sequence[str],
) -> None:
    operator.set_points_attrib(points, attribute, values)


def remove_attribs(
    geo: Geometry,
    point_attributes: str | tuple[str, ...] | None = None,
    prim_attributes: str | tuple[str, ...] | None = None,
    global_attributes: str | tuple[str, ...] | None = None,
) -> None:
    operator.remove_attribs(geo, point_attributes, prim_attributes, global_attributes)


def points_by_attrib(
    source: Geometry | Prim | Sequence[Prim],
    attribute: str,
    skip_blank: bool = False,
) -> dict[str, set[Point]]:
    return querier.points_by_attrib(source, attribute, skip_blank)


def points_start_with(
    geo: Geometry,
    attribute: str,
    prefixes: str | tuple[str, ...],
) -> list[Point]:
    return querier.points_start_with(geo, attribute, prefixes)


def unique_points_by_attrib(
    source: Geometry | Prim | Sequence[Prim],
    attribute: str,
) -> dict[str, Point]:
    return querier.unique_points_by_attrib(source, attribute)


def unique_points_start_with(
    geo: Geometry,
    attribute: str,
    prefixes: str | tuple[str, ...],
) -> dict[str, dict[str, Point]]:
    return querier.unique_points_start_with(geo, attribute, prefixes)


def scan_indexed_attrib_range(
    geo: Geometry,
    attribute: str,
    prefix: str,
) -> tuple[int, int] | None:
    return querier.scan_indexed_attrib_range(geo, attribute, prefix)


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
    operator.deduplicate_point_attribs(geo, attribute, prefix, add_affix, keep_first)


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
    operator.modify_point_attribs(geo, attribute, filtrate, rename)


def copy_point_attribs(
    src: Point,
    dst: Point
) -> None:
    transferer.copy_point_attribs(src, dst)

def collect_prim_attribs(
    prims: Sequence[Prim],
) -> list[tuple[dict[str, Any], list[str]]]:
    return transferer.collect_prim_attribs(prims)

def apply_prim_attribs(
    prims: Sequence[Prim],
    data: Sequence[tuple[dict[str, Any], list[str]]] | tuple[dict[str, Any], list[str]],
) -> None:
    transferer.apply_prim_attribs(prims, data)
