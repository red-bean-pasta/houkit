from typing import Sequence, Any

from hou import Prim, Point

from ..topologies.helper import is_same_geo


def copy_point_attribs(
    src: Point,
    dst: Point
) -> None:
    assert is_same_geo([src, dst])
    geo = src.geometry()
    for attr in geo.pointAttribs():
        if attr.name() != "P":
            dst.setAttribValue(attr.name(), src.attribValue(attr))
    for grp in geo.pointGroups():
        if grp.contains(src):
            grp.add(dst)


def collect_prim_attribs(
    prims: Sequence[Prim],
) -> list[tuple[dict[str, Any], list[str]]]:
    if not prims:
        return []
    assert is_same_geo(prims)
    geo = prims[0].geometry()
    prim_attribs = geo.primAttribs()
    prim_groups = geo.primGroups()
    return [
        (
            {attr.name(): p.attribValue(attr) for attr in prim_attribs},
            [g.name() for g in prim_groups if g.contains(p)],
        ) for p in prims
    ]

def apply_prim_attribs(
    prims: Sequence[Prim],
    data: Sequence[tuple[dict[str, Any], list[str]]] | tuple[dict[str, Any], list[str]],
) -> None:
    if _is_single_data(data):
        data = [data] * len(prims)

    assert len(prims) == len(data)

    for (attr_dict, group_list), prim in zip(data, prims):
        for attr_name, attr_val in attr_dict.items():
            prim.setAttribValue(attr_name, attr_val)
        for g_name in group_list:
            geo = prim.geometry()
            group = geo.findPrimGroup(g_name)
            if group is not None:
                group.add(prim)


def _is_single_data(
    x: Sequence[tuple[dict[str, Any], list[str]]] | tuple[dict[str, Any], list[str]]
) -> bool:
    return (
        isinstance(x, tuple)
        and len(x) == 2
        and isinstance(x[0], dict)
        and isinstance(x[1], list)
    )
