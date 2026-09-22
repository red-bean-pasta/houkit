import inspect
from typing import Callable

import hou
from hou import SopNode, OpNode

from .sopifier import sopify
from ..developings.reloader import reload_modules


def add_reloadable_subnet(
        parent: OpNode,
        name: str,
) -> SopNode:
    subnet = parent.createNode("subnet", name)
    add_reload_button(subnet)
    return subnet


def add_reload_button(parent: OpNode, reload_fn: Callable = reload_modules) -> SopNode:
    node = sopify(parent, None, reload_fn)

    templates = node.parmTemplateGroup()
    templates.append(
        hou.ButtonParmTemplate(
            "reload",
            "Reload",
            script_callback=build_reload_callback(reload_fn),
            script_callback_language=hou.scriptLanguage.Python,
        )
    )
    node.setParmTemplateGroup(templates)

    return node

def build_reload_callback(fn: Callable) -> str:
    module_path, function_path = get_callable_path(fn)
    return inspect.cleandoc(f"""
        import hou
        import importlib

        module = importlib.import_module({module_path!r})

        callback = module
        for name in {function_path!r}.split("."):
            callback = getattr(callback, name)

        callback()

        node = hou.pwd()
        subnet = node.parent()

        if subnet:
            try:
                for child in subnet.allSubChildren():
                    child.cook(force=True)

                subnet.cook(force=True)
            except Exception as e:
                node.addError(str(e))
                raise
    """)

def get_callable_path(fn: Callable) -> tuple[str, str]:
    module = inspect.getmodule(fn)
    if module is None:
        raise ValueError(f"Cannot determine module for {fn!r}")
    return module.__name__, fn.__qualname__
