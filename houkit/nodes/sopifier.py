import inspect
from typing import Callable

from hou import SopNode, OpNode


def sopify(
    parent: OpNode,
    input_node: SopNode | None,
    function: Callable[[], None] | Callable[[SopNode], None]
) -> SopNode:
    assert "<locals>" not in function.__qualname__, "Python SOP functions must be module-level functions"

    module = function.__module__
    qualname = function.__qualname__
    has_arg = len(inspect.signature(function).parameters) >= 1

    node = parent.createNode("python", function.__name__.strip("_"))
    if input_node is not None:
        node.setInput(0, input_node)

    call_code = f"f(hou.pwd())" if has_arg else "f()"
    node.parm("python").set(
        f"import {module}\n"
        f"f = {module}.{qualname}\n"
        f"{call_code}\n"
    )
    return node