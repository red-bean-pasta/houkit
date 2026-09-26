from dataclasses import dataclass
from typing import Callable, Any, Sequence, Iterator, Self

from hou import Node, ParmTuple, LabelParmTemplate, labelParmType, OpNode

from .operator import add_heading
from ..formatter import snake_case, title_case


@dataclass
class ParmContext:
    data: Any
    parameter: ParmTuple
    destination: OpNode
    source: OpNode
    heading_factory: Callable[[OpNode, OpNode], str]

    @property
    def heading(self) -> str:
        return self.heading_factory(self.destination, self.source)


@dataclass
class PromoteFormatter:
    heading_factory: Callable[[OpNode, OpNode], str] = None
    child_parm_factory: Callable[[ParmContext], str] = None
    child_heading_factory: Callable[[ParmContext], str] = None

    @classmethod
    def default(cls) -> Self:
        f = cls()
        f.normalize()
        return f

    def normalize(self) -> None:
        if not self.heading_factory:
            self.heading_factory = _format_heading_default
        if not self.child_parm_factory:
            self.child_parm_factory = _format_child_parm_default
        if not self.child_heading_factory:
            self.child_heading_factory = _format_child_heading_default


def promote_children_parms(
    parent: OpNode,
    type_names: str | Sequence[str] | None,
    node_names: str | Sequence[str] | None = None,
    depth: int | None = 1,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
    deepest_first: bool = True,
) -> list[OpNode]:
    """

    :param parent:
    :param type_names: None for every node type
    :param node_names: None for all the node names
    :param depth: None for search recursively
    :param skip_parameters:
    :param dest_group: Parameter folder label, or an empty string for the parent root.
    :param formatter:
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
            formatter
        )
    return children


def promote_parms_from(
    parent: OpNode,
    child: OpNode,
    skip_parameters: str | tuple[str, ...] = (),
    dest_group: str = "",
    formatter: PromoteFormatter | None = None,
) -> None:
    """Expose spare parameters from child node onto parent node and link them via expressions."""
    if not formatter:
        formatter = PromoteFormatter.default()
    formatter.normalize()
    if not isinstance(skip_parameters, tuple):
        skip_parameters = (skip_parameters,)
    info = ParmContext(
        data=None,
        parameter=None,
        source=child,
        destination=parent,
        heading_factory=formatter.heading_factory,
    )
    parameters = list(
        parameter for parameter in child.parmTuples()
        if parameter[0].isSpare() and parameter.name() not in skip_parameters
    )

    if len(parameters) < 1:
        return

    heading = formatter.heading_factory(parent, child)
    add_heading(
        parent,
        heading,
        name=snake_case(heading.replace(" > ", "_")),
        folder_label=dest_group,
    )

    template_group = parent.parmTemplateGroup()
    for source in parameters:
        name = _get_new_parm_name(source, info, formatter.child_parm_factory)
        param = source.parmTemplate().clone()
        param.setName(name)
        if dest_group:
            template_group.appendToFolder(dest_group, param)
        else:
            template_group.append(param)
    parent.setParmTemplateGroup(template_group)

    for source in parameters:
        name = _get_new_parm_name(source, info, formatter.child_parm_factory)
        target = parent.parmTuple(name)
        template = source.parmTemplate()
        if isinstance(template, LabelParmTemplate) and template.labelParmType() == labelParmType.Heading:
            text = _get_new_heading(source, info, formatter.child_heading_factory)
            target[0].set(text)
        else:
            target.set(source.eval())
            for source_parm, target_parm in zip(source, target):
                source_parm.set(target_parm)

def _format_heading_default(parent: OpNode, child: OpNode) -> str:
    parts = _get_relative_path_components(parent, child)
    return " > ".join(title_case(part) for part in parts)

def _format_child_parm_default(parameter: ParmContext) -> str:
    prefix = snake_case(parameter.heading.replace(" > ", "_"))
    return f"{prefix}_{parameter.data}" if prefix else str(parameter.data)

def _format_child_heading_default(parameter: ParmContext) -> str:
    return parameter.heading + " > " + parameter.data

def _get_new_parm_name(
    parameter: ParmTuple,
    info: ParmContext,
    parameter_factory: Callable[[ParmContext], str]
) -> str:
    info.data = parameter.name()
    info.parameter = parameter
    return parameter_factory(info)

def _get_new_heading(
    parameter: ParmTuple,
    info: ParmContext,
    heading_factory: Callable[[ParmContext], str]
) -> str:
    text = parameter[0].evalAsString()
    info.data = text
    info.parameter = parameter
    return heading_factory(info)

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
        return list(
            _get_qualified_children(parent.allSubChildren(), type_names, node_names)
        )
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
