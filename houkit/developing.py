from pathlib import Path
from typing import Callable

from .developings import reloader, saver


def save(
    path: Path,
    build: Callable[[], None],
    rebuild: bool = True
) -> None:
    """Execute a build callable and save to a Houdini .hip file, creating a backup in case the build fails."""
    saver.save(path, build, rebuild)


def reload_modules() -> None:
    reloader.reload_modules()
