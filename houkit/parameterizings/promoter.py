from typing import Sequence, Iterator

from hou import (
    Node,
    ParmTuple,
    OpNode,
    ParmTemplate,
    ParmTemplateGroup,
    FolderSetParmTemplate,
    FolderParmTemplate,
    folderType,
)

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
    :return: List of child nodes whose parameters were promoted.
    """
    children = _find_children(parent, depth, type_names, node_names, deepest_first)
    promoted = []
    for child in children:
        if promote_parms_from(parent, child, skip_parameters, dest_group):
            promoted.append(child)
    return promoted


def promote_parms_from(
    parent: OpNode,
    child: OpNode,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
) -> bool:
    """Expose spare parameters from child node onto parent node and link them via expressions."""
    parameters = _get_promotable_parameters(child, skip_parameters)
    if not parameters:
        return False

    template_group = parent.parmTemplateGroup()
    folder_path = _ensure_folder_path(template_group, parent, child, dest_group, skip_parameters)
    for source in parameters:
        name = _format_child_parm_default(parent, child, source.name())
        param = source.parmTemplate().clone()
        param.setName(name)
        if folder_path:
            template_group.appendToFolder(folder_path, param)
        else:
            template_group.append(param)
    parent.setParmTemplateGroup(template_group)

    for source in parameters:
        name = _format_child_parm_default(parent, child, source.name())
        target = parent.parmTuple(name)
        target.set(source.eval())
        for source_parm, target_parm in zip(source, target):
            source_parm.set(target_parm)
    return True


def _ensure_folder_path(
    ptg: ParmTemplateGroup,
    parent: Node,
    child: Node,
    dest_group: str = "",
    skip_parameters: str | tuple[str, ...] = (),
) -> tuple[str, ...]:
    assert not dest_group or ptg.findFolder(dest_group) is not None, f"Cannot find destination group {dest_group}"

    parts = _get_relative_path_components(parent, child)
    current_label_path = [dest_group] if dest_group else []

    for i in range(len(parts)):
        sub_path = parts[:i + 1]
        if i < len(parts) - 1:
            ancestor = parent.node("/".join(sub_path))
            if not isinstance(ancestor, OpNode) or not _get_promotable_parameters(ancestor, skip_parameters):
                continue

        folder_label = parts[i]
        folder_name = "_".join(sub_path) + "_folder"
        target_path = tuple(current_label_path + [folder_label])
        if ptg.findFolder(target_path) is None:
            new_folder = FolderParmTemplate(
                folder_name,
                folder_label,
                folder_type=folderType.Collapsible,
            )
            if current_label_path:
                ptg.appendToFolder(tuple(current_label_path), new_folder)
            else:
                ptg.append(new_folder)
        current_label_path.append(folder_label)

    return tuple(current_label_path)


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


def _get_promotable_parameters(
    node: OpNode,
    skip_parameters: str | tuple[str, ...] = (),
) -> list[ParmTuple]:
    if not isinstance(skip_parameters, tuple):
        skip_parameters = (skip_parameters,)
    return [
        parameter for parameter in node.parmTuples()
        if parameter[0].isSpare()
        and parameter.name() not in skip_parameters
        and not isinstance(parameter.parmTemplate(), UNPROMOTABLE)
    ]
