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
    parmNamingScheme,
    hscript,
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

_SCHEME_SUFFIXES = {
    parmNamingScheme.XYZW: ("x", "y", "z", "w"),
    parmNamingScheme.RGBA: ("r", "g", "b", "a"),
    parmNamingScheme.UVW: ("u", "v", "w"),
    parmNamingScheme.XYWH: ("x", "y", "w", "h"),
    parmNamingScheme.StartEnd: ("start", "end"),
    parmNamingScheme.MinMax: ("min", "max"),
    parmNamingScheme.MaxMin: ("max", "min"),
    parmNamingScheme.BeginEnd: ("begin", "end"),
}


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

    promoter = _ChildPromoter(parent, child, skip_parameters)
    grouped_parms = promoter.collect_templates()
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

    promoter.link_parms()
    promoter.link_multiparms()
    return True


class _ChildPromoter:
    """Encapsulates promotion of spare parameters from a child node onto a parent node."""

    def __init__(
        self,
        parent: OpNode,
        child: OpNode,
        skip_parameters: tuple[str, ...] = (),
    ):
        self.parent = parent
        self.child = child
        self.skip_parameters = skip_parameters
        self.prefix = snake_case("_".join(_get_relative_path_components(parent, child)))
        self.parm_tuples: list[ParmTuple] = []
        self.multiparm_pairs: list[tuple[str, str]] = []

    def collect_templates(self) -> list[ParmTemplate]:
        promoted = []
        for entry in self.child.parmTemplateGroup().entries():
            formatted = self._format_template(entry)
            if formatted is not None:
                promoted.append(formatted)
        return promoted

    def link_parms(self) -> None:
        for source in self.parm_tuples:
            target_name = self.format_parm_name(source.name())
            target = self.parent.parmTuple(target_name)
            target.set(source.eval())
            for source_parm, target_parm in zip(source, target):
                source_parm.set(target_parm)

    def link_multiparms(self) -> None:
        if not self.multiparm_pairs:
            return
        rel_dir = self.child.relativePathTo(self.parent)
        pairs_str = " ".join(
            f'"{child_pat}" "{rel_dir}/{parent_pat}"'
            for child_pat, parent_pat in self.multiparm_pairs
        )
        cmd = f'opmultiparm "{self.child.path()}" {pairs_str}'
        out, err = hscript(cmd)
        assert not err, f"opmultiparm failed on {self.child.path()}: {err}"

    def format_parm_name(self, parm_name: str) -> str:
        return f"{self.prefix}_{parm_name}" if self.prefix else str(parm_name)

    def _format_template(self, tmpl: ParmTemplate) -> ParmTemplate | None:
        if isinstance(tmpl, FolderParmTemplate):
            if tmpl.folderType() in MULTIPARM_FOLDER_TYPES:
                return self._format_multiparm(tmpl)
            return self._format_folder(tmpl)

        if tmpl.name() in self.skip_parameters:
            return None
        pt = self.child.parmTuple(tmpl.name())
        if pt is None or not pt[0].isSpare() or isinstance(pt.parmTemplate(), UNPROMOTABLE):
            return None

        param = tmpl.clone()
        param.setName(self.format_parm_name(param.name()))
        self.parm_tuples.append(pt)
        return param

    def _format_multiparm(self, tmpl: FolderParmTemplate) -> FolderParmTemplate | None:
        if tmpl.name() in self.skip_parameters:
            return None
        pt = self.child.parmTuple(tmpl.name())
        if pt is None or not pt[0].isSpare():
            return None

        cloned = tmpl.clone()
        cloned.setName(self.format_parm_name(cloned.name()))
        cloned.setParmTemplates(tuple(
            self._format_multiparm_sub(sub) for sub in tmpl.parmTemplates()
        ))

        self.parm_tuples.append(pt)
        count = int(pt[0].eval())
        for i in range(1, count + 1):
            for sub in _get_multiparm_leaves(tmpl.parmTemplates()):
                inst_pt = self.child.parmTuple(sub.name().replace("#", str(i)))
                if inst_pt is not None:
                    self.parm_tuples.append(inst_pt)
        return cloned

    def _format_multiparm_sub(self, sub: ParmTemplate) -> ParmTemplate:
        cloned = sub.clone()
        cloned.setName(self.format_parm_name(cloned.name()))
        if isinstance(sub, FolderParmTemplate) and sub.folderType() not in MULTIPARM_FOLDER_TYPES:
            cloned.setParmTemplates(tuple(
                self._format_multiparm_sub(nested) for nested in sub.parmTemplates()
            ))
        else:
            for suffix in _get_template_suffixes(sub):
                self.multiparm_pairs.append((
                    f"{sub.name()}{suffix}",
                    f"{cloned.name()}{suffix}",
                ))
        return cloned

    def _format_folder(self, tmpl: FolderParmTemplate) -> FolderParmTemplate | None:
        subs = []
        for sub in tmpl.parmTemplates():
            res = self._format_template(sub)
            if res is not None:
                subs.append(res)
        if not subs:
            return None
        folder = tmpl.clone()
        folder.setName(self.format_parm_name(folder.name()))
        folder.setParmTemplates(tuple(subs))
        return folder


def _get_multiparm_leaves(templates: Sequence[ParmTemplate]) -> list[ParmTemplate]:
    leaves = []
    for tmpl in templates:
        if isinstance(tmpl, FolderParmTemplate) and tmpl.folderType() not in MULTIPARM_FOLDER_TYPES:
            leaves.extend(_get_multiparm_leaves(tmpl.parmTemplates()))
        else:
            leaves.append(tmpl)
    return leaves


def _get_template_suffixes(tmpl: ParmTemplate) -> tuple[str, ...]:
    num_components = getattr(tmpl, "numComponents", lambda: 1)()
    if num_components <= 1:
        return ("",)
    scheme = getattr(tmpl, "namingScheme", lambda: None)()
    if scheme in _SCHEME_SUFFIXES and num_components <= len(_SCHEME_SUFFIXES[scheme]):
        return _SCHEME_SUFFIXES[scheme][:num_components]
    return tuple(str(i) for i in range(1, num_components + 1))


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
