from typing import Sequence

from hou import OpNode, Vector2, Vector3

# noinspection PyUnusedImports
from .parameterizings.operator import (
    add_folder,
    add_heading,
    add_float_parm,
)
# noinspection PyUnusedImports
from .parameterizings.promoter import (
    PromoteFormatter,
    promote_children_parms,
    promote_parms_from as promote_parms_from_child,
)
# noinspection PyUnusedImports
from .parameterizings.querier import (
    Parameters,
    get_parm,
    get_parms,
)


def get_float_parm(node: OpNode, name: str) -> float:
    return get_parm(node, name, float)

def get_vector2_parm(node: OpNode, name: str) -> Vector2:
    return Vector2(
        get_parm(node, name, tuple[float, float])
    )

def get_vector3_parm(node: OpNode, name: str) -> Vector3:
    return Vector3(
        get_parm(node, name, tuple[float, float, float])
    )

def promote_subnets(
    parent: OpNode,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
    deepest_first: bool = True,
) -> list[OpNode]:
    return promote_children_parms(
        parent,
        "subnet",
        None,
        depth,
        skip_parameters,
        dest_group,
        formatter,
        deepest_first
    )

def promote_controls(
    parent: OpNode,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    control_node_name: str | Sequence[str] = ("CONTROLS", "CONTROL"),
    formatter: PromoteFormatter | None = None,
    deepest_first: bool = True,
) -> list[OpNode]:
    return promote_children_parms(
        parent,
        None,
        control_node_name,
        depth,
        skip_parameters,
        dest_group,
        formatter,
        deepest_first,
    )

def promote_parms_from_children(
    parent: OpNode,
    children: Sequence[OpNode],
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
) -> None:
    for c in children:
        promote_parms_from_child(parent, c, skip_parameters, dest_group, formatter)
