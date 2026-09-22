from typing import Callable

import hou
from hou import SopNode, OpNode

from .nodes import sopifier

# noinspection PyUnusedImports
from .nodes.reloader import (
    add_reloadable_subnet,
    add_reload_button,
)
# noinspection PyUnusedImports
from .nodes.normal_recalculator import (
    add_outside_recalculation as add_recalculate_normal,
)
# noinspection PyUnusedImports
from .nodes.sops import (
    add_merge,
    add_fuse,
    add_mirror,
    add_output,
)


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
    parent: OpNode,
    input_node: OpNode | None,
    function: Callable[[], None] | Callable[[SopNode], None]
) -> SopNode:
    """Generate a Python SOP node invoking a given module-level python function."""
    return sopifier.sopify(parent, input_node, function)

