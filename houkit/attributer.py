"""
Utility functions for attribute-based identification, naming, and indexing of geometry elements (points, prims).
"""
from typing import Sequence, Callable, Any, Iterator, Mapping

import hou
from hou import Geometry, Point, Prim

from .attributings import transferer, positional_attributer
from .attributings import querier, operator
from .topologies.sorter import Axis


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


def set_point_attrib_by_position(
    points: Sequence[Point],
    attrib_name: str,
    name_prefix: str,
    axis_order: tuple[Axis, Axis, Axis],
    axis_ascending: tuple[bool, bool, bool] = (True, True, True),
    start_index: int = 0,
    special_labels: Mapping[int, str] | None = None,
    reuse_index_after_special: bool = True,
) -> None:
    """Set an indexed string attribute on points ordered by position.

    :param points: Points to label. The input sequence is not reordered.
    :param attrib_name: Name of the point attribute to set.
    :param name_prefix: Prefix for generated attribute values.
    :param axis_order: Axes to compare, from highest to lowest priority.
    :param axis_ascending: Sort direction for each axis in ``axis_order``. ``True`` placing smaller coordinates first.
    :param start_index: Numeric suffix assigned to the first sorted point.
    :param special_labels: Replacement labels keyed by their generated index.
    :param reuse_index_after_special: Whether special labels leave the next regular numeric suffix unchanged.
    """
    positional_attributer.set_point_attrib_by_position(points, attrib_name, name_prefix, axis_order, axis_ascending, start_index, special_labels, reuse_index_after_special)


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


def latest_points_by_attrib(
    geo: Geometry,
    attribute: str,
    *values: str,
    assert_existing: bool = True,
) -> Iterator[Point]:
    """

    :param geo:
    :param attribute:
    :param values:
    :param assert_existing: If False, missing point will return None
    :return:
    """
    return querier.latest_points_by_attrib(geo, attribute, *values, assert_existing=assert_existing)


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
