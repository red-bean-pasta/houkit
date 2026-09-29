from typing import Sequence, Iterator

from hou import Node, ParmTuple, OpNode, ParmTemplate, FolderSetParmTemplate

from ..formatter import snake_case


UNPROMOTABLE: tuple[type[ParmTemplate]] = (
    FolderSetParmTemplate,
)


def promote_children_parms(
    parent: OpNode,
    type_names: str | Sequence[str] | None,
    node_names: str | Sequence[str] | None = None,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    deepest_first: bool = True,
) -> list[OpNode]:
    """

    :param parent:
    :param type_names: None for every node type
    :param node_names: None for all the node names
    :param depth: None for search recursively
    :param skip_parameters:
    :param dest_group: Parameter folder label, or an empty string for the parent root.
    :param deepest_first: If True, deeper node is promoted first
    :return:
    """
    children = _find_children(parent, depth, type_names, node_names, deepest_first)
    for child in children:
        promote_parms_from(
            parent,
            child,
            skip_parameters,
            dest_group,
        )
    return children


def promote_parms_from(
    parent: OpNode,
    child: OpNode,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
) -> None:
    """Expose spare parameters from child node onto parent node and link them via expressions."""
    if not isinstance(skip_parameters, tuple):
        skip_parameters = (skip_parameters,)
    parameters = list(
        parameter for parameter in child.parmTuples()
        if parameter[0].isSpare()
        and parameter.name() not in skip_parameters
        and not isinstance(parameter.parmTemplate(), UNPROMOTABLE)
    )

    if len(parameters) < 1:
        return

    template_group = parent.parmTemplateGroup()
    for source in parameters:
        name = _format_child_parm_default(parent, child, source.name())
        param = source.parmTemplate().clone()
        param.setName(name)
        if dest_group:
            template_group.appendToFolder(dest_group, param)
        else:
            template_group.append(param)
    parent.setParmTemplateGroup(template_group)

    for source in parameters:
        name = _format_child_parm_default(parent, child, source.name())
        target = parent.parmTuple(name)
        target.set(source.eval())
        for source_parm, target_parm in zip(source, target):
            source_parm.set(target_parm)


def _format_child_parm_default(parent: OpNode, child: OpNode, parm_name: str) -> str:
    parts = _get_relative_path_components(parent, child)
    prefix = snake_case("_".join(parts))
    return f"{prefix}_{parm_name}" if prefix else str(parm_name)


def _get_relative_path_components(
    parent: Node,
    child: Node,
) -> list[str]:
    path = parent.relativePathTo(child)
    parts = [] if path == "." else path.split("/")
    assert ".." not in parts
    return parts


def _find_children(
    parent: Node,
    depth: int | None,
    type_names: str | Sequence[str] | None = None,
    node_names: str | Sequence[str] | None = None,
    deepest_first: bool = True,
) -> list[OpNode]:
    if depth == 0:
        return []

    if depth is None:
        children = list(
            _get_qualified_children(parent.allSubChildren(), type_names, node_names)
        )
        if deepest_first:
            children.sort(key=lambda n: len(n.path().split("/")), reverse=True)
        return children

    assert depth > 0, "depth must be non-negative or None"

    direct_children = list(
        _get_qualified_children(parent.children(), type_names, node_names)
    )
    if depth == 1:
        return direct_children

    descendants = list(
        descendant
        for child in parent.children()
        for descendant in _find_children(
            child,
            depth - 1,
            type_names,
            node_names,
            deepest_first,
        )
    )
    if deepest_first:
        return descendants + direct_children
    return direct_children + descendants


def _get_qualified_children(
    children: Sequence[Node],
    type_names: str | Sequence[str] | None,
    node_names: str | Sequence[str] | None,
) -> Iterator[OpNode]:
    if isinstance(type_names, str):
        type_names = [type_names]
    if isinstance(node_names, str):
        node_names = [node_names]

    for c in children:
        if not isinstance(c, OpNode):
            continue
        if type_names and c.type().name() not in type_names:
            continue
        if node_names and c.name() not in node_names:
            continue
        yield c
