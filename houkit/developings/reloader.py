import importlib
import sys
from pathlib import Path

import hou


def reload_modules() -> None:
    importlib.invalidate_caches()
    hip_dir = Path(hou.hipFile.path()).resolve().parent  # type: ignore

    for name, module in _hip_modules_to_reload(hip_dir):
        # Earlier reloads may have replaced this entry.
        if sys.modules.get(name) is not module:
            continue
            
        # Earlier reloads may also have changed its spec.
        spec = getattr(module, "__spec__", None)
        if spec is None or spec.name != name:
            continue

        importlib.reload(module)


def _hip_modules_to_reload(hip_dir: Path):
    modules = []
    seen = set()

    for name, module in list(sys.modules.items()):
        if module is None or id(module) in seen:
            continue
        if not _is_hip_module(module, hip_dir):
            continue
        if not _is_reloadable(name, module):
            continue
        seen.add(id(module))
        modules.append((name, module))

    return sorted(
        modules,
        key=lambda item: item[0].count("."),
        reverse=True,
    )


def _is_hip_module(module, hip_dir: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if module_file and _path_is_under(module_file, hip_dir):
        return True

    module_path = getattr(module, "__path__", None)
    if module_path:
        return any(_path_is_under(path, hip_dir) for path in module_path)

    return False


def _is_reloadable(name: str, module) -> bool:
    spec = getattr(module, "__spec__", None)
    if spec is None or spec.name != name:
        return False

    parent_name = name.rpartition(".")[0]
    if not parent_name:
        return True

    parent = sys.modules.get(parent_name)
    return parent is not None and hasattr(parent, "__path__")


def _path_is_under(path: str | Path, root: Path) -> bool:
    path = Path(path)
    if not path.is_absolute():
        return False

    try:
        resolved = path.resolve(strict=True)
        return path.is_relative_to(root) or resolved.is_relative_to(root)
    except (OSError, RuntimeError):
        return False
