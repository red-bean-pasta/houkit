from typing import Sequence

import hou
from hou import SopNode, OpNode, Vector2, Vector3

from .parameterizings.promoter import (
    PromoteFormatter,
    promote_children_parms,
    promote_parms_from,
)
from .parameterizings.querier import T, Parameters
from .parameterizings import operator, querier


def add_folder(
    node: OpNode,
    name: str,
    label: str = "",
    folder_type: hou.folderType = hou.folderType.Tabs,
    **kwargs,
) -> None:
    operator.add_folder(node, name, label, folder_type, **kwargs)


def add_heading(
    node: OpNode,
    text: str,
    name: str = "",
    label: str = "",
    folder_label: str = "",
    **kwargs,
) -> None:
    operator.add_heading(node, text, name, label, folder_label, **kwargs)


def add_float_parm(
    node: OpNode,
    name: str,
    size: int = 1,
    default: float | tuple[float, ...] = (0.0,),
    min_max: tuple[float | None, float | None] = (None, None),
    naming_scheme: hou.parmNamingScheme = hou.parmNamingScheme.XYZW,
    label: str = "",
    folder_label: str = "",
    **kwargs,
) -> None:
    operator.add_float_parm(
        node,
        name,
        size,
        default,
        min_max,
        naming_scheme,
        label,
        folder_label,
        **kwargs,
    )


def get_parms(
    node: OpNode,
    exclude_internal: bool = True,
    use_tuple: bool = True,
) -> Parameters:
    """Read all evaluated parameters on a node into a dot-accessible Parameters dictionary."""
    return querier.get_parms(node, exclude_internal, use_tuple)


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

def get_parm(node: OpNode, name: str, cls: type[T]) -> T:
    return querier.get_parm(node, name, cls)


def promote_subnets(
    parent: SopNode,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
) -> list[SopNode]:
    return promote_children_parms(
        parent,
        "subnet",
        None,
        depth,
        skip_parameters,
        dest_group,
        formatter,
    )

def promote_controls(
    parent: SopNode,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    control_node_name: str | Sequence[str] = ("CONTROLS", "CONTROL"),
    formatter: PromoteFormatter | None = None,
) -> list[SopNode]:
    return promote_children_parms(
        parent,
        None,
        control_node_name,
        depth,
        skip_parameters,
        dest_group,
        formatter,
    )

def promote_parms_from_child(
    parent: SopNode,
    child: SopNode,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
) -> None:
    promote_parms_from(parent, child, skip_parameters, dest_group, formatter)

def promote_parms_from_children(
    parent: SopNode,
    children: Sequence[SopNode],
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
) -> None:
    for c in children:
        promote_parms_from_child(parent, c, skip_parameters, dest_group, formatter)
