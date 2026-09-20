"""
Utility functions for attribute-based identification, naming, and indexing of geometry elements (points, prims).
"""
from typing import Sequence, Callable, Any, Iterator, Mapping

import hou
from hou import Geometry, Point, Vector3

from .topologies.sorter import Axis
from .attributings import positional_attributer
from .attributings import querier, operator
# noinspection PyUnusedImports
from .attributings.operator import (
    add_attrib,
    remove_attribs,
    set_point_attrib,
    set_points_attrib,
)
# noinspection PyUnusedImports
from .attributings.querier import (
    points_by_attrib,
    points_start_with,
    unique_points_by_attrib,
    unique_points_start_with,
    scan_indexed_attrib_range,
)
# noinspection PyUnusedImports
from .attributings.transferer import (
    copy_point_attribs,
    collect_prim_attribs,
    apply_prim_attribs,
)


def add_point_attrib(geo: Geometry, name: str, default: Any) -> hou.Attrib:
    return add_attrib(geo, hou.attribType.Point, name, default)

def add_prim_attrib(geo: Geometry, name: str, default: Any) -> hou.Attrib:
    return add_attrib(geo, hou.attribType.Prim, name, default)

def add_global_attrib(geo: Geometry, name: str, default: Any) -> hou.Attrib:
    return add_attrib(geo, hou.attribType.Global, name, default)


def set_point_attribs_by_position(
    points: Sequence[Point],
    attrib_name: str,
    name_prefix: str,
    axis_order: tuple[Axis, Axis, Axis],
    axis_ascending: tuple[bool, bool, bool] = (True, True, True),
    start_index: int = 0,
    special_labels: Mapping[int, str] | None = None,
    reuse_index_after_special: bool = True,
    tolerance: float = 1e-5,
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
    :param tolerance:
    """
    positional_attributer.set_point_attribs_by_position(points, attrib_name, name_prefix, axis_order, axis_ascending, start_index, special_labels, reuse_index_after_special, tolerance)


def points_from_geo(
    geo: Geometry,
    attribute: str,
    *values: str
) -> Iterator[Point]:
    """Return the geometry points identified by ``point_ids`` in the same order."""
    return querier.points_from_geo(geo, attribute, *values)

def positions_from_geo(
    geo: Geometry,
    attribute: str,
    *values: str
) -> Iterator[Vector3]:
    """Return the geometry points' positions identified by ``point_ids`` in the same order."""
    return querier.positions_from_geo(geo, attribute, *values)


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
