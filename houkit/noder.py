from typing import Callable

import hou
from hou import SopNode, OpNode

from .nodes import sops, normal_recalculator
from .nodes import reloader
from .nodes import sopifier


def get_parent(node: hou.Node) -> OpNode:
    parent = node.parent()
    assert isinstance(parent, OpNode), "Expect SOP to be inside a valid network"
    return parent

def get_control(node: hou.Node, name: str = "CONTROLS") -> OpNode:
    target = node if node.isSubNetwork() else get_parent(node)
    control = target.node(name)
    assert control is not None, f"Expected CONTROL node under {target}"
    return control


def sopify(
    parent: SopNode,
    input_node: SopNode | None,
    function: Callable[[], None] | Callable[[SopNode], None]
) -> SopNode:
    """Generate a Python SOP node invoking a given module-level python function."""
    return sopifier.sopify(parent, input_node, function)


def add_reloadable_subnet(
    parent: hou.OpNode,
    name: str,
) -> SopNode:
    return reloader.add_reloadable_subnet(parent, name)

def add_reload_button(parent: SopNode) -> SopNode:
    return reloader.add_reload_button(parent)


def add_recalculate_normal(
    parent: SopNode,
    name: str,
    p_input: SopNode,
    reverse: bool = False,
) -> SopNode:
    return normal_recalculator.add_outside_recalculation(parent, name, p_input, reverse)


def add_merge(
    parent: SopNode,
    name: str,
    *inputs: SopNode,
) -> SopNode:
    return sops.add_merge(parent, name, *inputs)

def add_fuse(
    parent: SopNode,
    name: str,
    p_input: SopNode,
) -> SopNode:
    return sops.add_fuse(parent, name, p_input)

def add_mirror(
    parent: SopNode,
    name: str,
    p_input: SopNode,
    axis: hou.Vector3 | tuple[float, float, float],
    keep_original: bool,
    consolidate_unshared: bool,
    *args,
) -> SopNode:
    return sops.add_mirror(parent, name, p_input, axis, keep_original, consolidate_unshared, *args)

def add_output(
    parent: SopNode,
    name: str,
    p_input: SopNode,
) -> SopNode:
    return sops.add_output(parent, name, p_input)



