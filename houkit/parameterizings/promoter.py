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


UNPROMOTABLE: tuple[type[ParmTemplate], ...] = (
    FolderSetParmTemplate,
)

MULTIPARM_FOLDER_TYPES = (
    folderType.MultiparmBlock,
    folderType.ScrollingMultiparmBlock,
    folderType.TabbedMultiparmBlock,
)


def promote_children_parms(
    parent: OpNode,
    type_names: str | Sequence[str] | None,
    node_names: str | Sequence[str] | None = None,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    deepest_first: bool = True,
    create_child_folder: bool = True,
) -> list[OpNode]:
    """

    :param parent:
    :param type_names: None for every node type
    :param node_names: None for all the node names
    :param depth: None for search recursively
    :param skip_parameters:
    :param dest_group: Parameter folder label, or an empty string for the parent root.
    :param deepest_first: If True, deeper node is promoted first
    :param create_child_folder: If True, creates a folder for the child node.
    :return: List of child nodes whose parameters were promoted.
    """
    children = _find_children(parent, depth, type_names, node_names, deepest_first)
    promoted = []
    for child in children:
        if promote_parms_from(parent, child, skip_parameters, dest_group, create_child_folder):
            promoted.append(child)
    return promoted


def promote_parms_from(
    parent: OpNode,
    child: OpNode,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    create_child_folder: bool = True,
) -> bool:
    """Expose spare parameters from child node onto parent node and link them via expressions."""
    if not isinstance(skip_parameters, tuple):
        skip_parameters = (skip_parameters,)

    grouped_parms, parm_tuples = _get_grouped_parms(parent, child, skip_parameters)
    if not grouped_parms:
        return False

    template_group = parent.parmTemplateGroup()
    folder_path = _ensure_folder_path(
        template_group,
        parent,
        child,
        dest_group,
        skip_parameters,
        create_child_folder,
    )
    for parm in grouped_parms:
        if folder_path:
            template_group.appendToFolder(folder_path, parm)
        else:
            template_group.append(parm)
    parent.setParmTemplateGroup(template_group)

    for source in parm_tuples:
        name = _format_child_parm_default(parent, child, source.name())
        target = parent.parmTuple(name)
        target.set(source.eval())
        for source_parm, target_parm in zip(source, target):
            source_parm.set(target_parm)
    return True


def _get_grouped_parms(
    parent: OpNode,
    child: OpNode,
    skip_parameters: tuple[str, ...] = (),
) -> tuple[list[ParmTemplate], list[ParmTuple]]:
    grouped_parms = []
    parm_tuples = []
    for entry in child.parmTemplateGroup().entries():
        processed = _format_child_template(parent, child, entry, skip_parameters, parm_tuples)
        if processed is not None:
            grouped_parms.append(processed)
    return grouped_parms, parm_tuples


def _format_child_template(
    parent: OpNode,
    child: OpNode,
    tmpl: ParmTemplate,
    skip_parameters: tuple[str, ...],
    parm_tuples: list[ParmTuple],
) -> ParmTemplate | None:
    if isinstance(tmpl, FolderParmTemplate):
        if tmpl.folderType() in MULTIPARM_FOLDER_TYPES:
            return _format_child_multiparm(parent, child, tmpl, skip_parameters, parm_tuples)
        return _format_child_folder(parent, child, tmpl, skip_parameters, parm_tuples)

    if tmpl.name() in skip_parameters:
        return None
    pt = child.parmTuple(tmpl.name())
    if pt is None or not pt[0].isSpare() or isinstance(pt.parmTemplate(), UNPROMOTABLE):
        return None

    param = tmpl.clone()
    param.setName(_format_child_parm_default(parent, child, param.name()))
    parm_tuples.append(pt)
    return param


def _format_child_multiparm(
    parent: OpNode,
    child: OpNode,
    tmpl: FolderParmTemplate,
    skip_parameters: tuple[str, ...],
    parm_tuples: list[ParmTuple],
) -> FolderParmTemplate | None:
    if tmpl.name() in skip_parameters:
        return None
    pt = child.parmTuple(tmpl.name())
    if pt is None or not pt[0].isSpare():
        return None

    cloned = tmpl.clone()
    cloned.setName(_format_child_parm_default(parent, child, cloned.name()))
    sub_templates = []
    for sub in tmpl.parmTemplates():
        sub_cloned = sub.clone()
        sub_cloned.setName(_format_child_parm_default(parent, child, sub_cloned.name()))
        sub_templates.append(sub_cloned)
    cloned.setParmTemplates(tuple(sub_templates))

    parm_tuples.append(pt)
    count = int(pt[0].eval())
    for i in range(1, count + 1):
        for sub in tmpl.parmTemplates():
            inst_name = sub.name().replace("#", str(i))
            inst_pt = child.parmTuple(inst_name)
            if inst_pt is not None:
                parm_tuples.append(inst_pt)
    return cloned


def _format_child_folder(
    parent: OpNode,
    child: OpNode,
    tmpl: FolderParmTemplate,
    skip_parameters: tuple[str, ...],
    parm_tuples: list[ParmTuple],
) -> FolderParmTemplate | None:
    subs = []
    for sub in tmpl.parmTemplates():
        res = _format_child_template(parent, child, sub, skip_parameters, parm_tuples)
        if res is not None:
            subs.append(res)
    if not subs:
        return None
    folder = tmpl.clone()
    folder.setName(_format_child_parm_default(parent, child, folder.name()))
    folder.setParmTemplates(tuple(subs))
    return folder


def _ensure_folder_path(
    ptg: ParmTemplateGroup,
    parent: Node,
    child: Node,
    dest_group: str = "",
    skip_parameters: tuple[str, ...] = (),
    create_child_folder: bool = True,
) -> tuple[str, ...]:
    assert not dest_group or ptg.findFolder(dest_group) is not None, f"Cannot find destination group {dest_group}"

    parts = _get_relative_path_components(parent, child)
    current_label_path = [dest_group] if dest_group else []

    count = len(parts) if create_child_folder else len(parts) - 1
    for i in range(count):
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
    skip_parameters: tuple[str, ...] = (),
) -> list[ParmTuple]:
    return [
        parameter for parameter in node.parmTuples()
        if parameter[0].isSpare()
        and parameter.name() not in skip_parameters
        and not isinstance(parameter.parmTemplate(), UNPROMOTABLE)
    ]
