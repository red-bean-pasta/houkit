from pathlib import Path
from typing import Callable

from .developings import saver

# noinspection PyUnusedImports
from .developings.reloader import (
    reload_modules,
)


def save(
    path: Path,
    build: Callable[[], None],
    rebuild: bool = True
) -> None:
    """Execute a build callable and save to a Houdini .hip file, creating a backup in case the build fails."""
    saver.save(path, build, rebuild)
