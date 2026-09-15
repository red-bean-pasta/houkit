from hou import Geometry, PointGroup, EdgeGroup, PrimGroup

from .groupings.operator import add_group, GroupType


def add_point_group(geo: Geometry, name: str, skip_existing: bool = True) -> PointGroup:
    return add_group(geo, GroupType.Point, name, skip_existing)

def add_edge_group(geo: Geometry, name: str, skip_existing: bool = True) -> EdgeGroup:
    return add_group(geo, GroupType.Edge, name, skip_existing)

def add_prim_group(geo: Geometry, name: str, skip_existing: bool = True) -> PrimGroup:
    return add_group(geo, GroupType.Prim, name, skip_existing)