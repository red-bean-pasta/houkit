"""
Utility functions for attribute-based identification, naming, and indexing of geometry elements (points, prims).
"""
from typing import Any

import hou
from hou import Geometry

# noinspection PyUnusedImports
from .attributings.operator import (
    add_attrib,
    deduplicate_point_attribs,
    modify_point_attribs,
    remove_attribs,
    set_point_attrib,
    set_points_attrib,
)
# noinspection PyUnusedImports
from .attributings.positional_attributer import (
    set_point_attribs_by_position,
)
# noinspection PyUnusedImports
from .attributings.querier import (
    points_by_attrib,
    points_from_geo,
    points_start_with,
    positions_from_geo,
    latest_points_by_attrib,
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
