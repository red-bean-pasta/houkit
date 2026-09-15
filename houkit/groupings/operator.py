from enum import Enum

from hou import Geometry


class GroupType(Enum):
    Point = 0,
    Edge = 1,
    Prim = 2,

type_finder_creator_map = {
    GroupType.Point: (Geometry.findPointGroup, Geometry.createPointGroup),
    GroupType.Edge: (Geometry.findEdgeGroup, Geometry.createEdgeGroup),
    GroupType.Prim: (Geometry.findPrimGroup, Geometry.createPrimGroup)
}


def add_group(
    geo: Geometry,
    group_type: GroupType,
    name: str,
    skip_existing: bool = True
):
    find, create = type_finder_creator_map[group_type]
    group = find(geo, name)
    if not skip_existing or group is None:
        group = create(geo, name)
    return group