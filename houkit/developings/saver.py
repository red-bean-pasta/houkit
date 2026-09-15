import shutil
import textwrap
from pathlib import Path
from typing import Callable

import hou


def save(
    path: Path,
    build: Callable[[], None],
    rebuild: bool = True,
) -> None:
    assert path.is_absolute(), "Require absolute path"

    if path.exists() and not rebuild:
        print(f"{path}: File exists. Exiting...")
        return

    backup_path = _backup(path)

    try:
        _initialize_hip(path)
        build()
        hou.hipFile.save()  # type: ignore
    except Exception:
        _restore_backup(path, backup_path)
        raise
    else:
        _remove_backup(backup_path)
        print(f"Saved {path}")


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None

    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    return backup_path


def _restore_backup(path: Path, backup_path: Path | None) -> None:
    if backup_path is None or not backup_path.exists():
        return
    shutil.copy2(backup_path, path)
    backup_path.unlink()


def _remove_backup(backup_path: Path | None) -> None:
    if backup_path is not None:
        backup_path.unlink(missing_ok=True)


def _initialize_hip(path: Path) -> None:
    path.unlink(missing_ok=True)
    hou.hipFile.save(str(path))  # type: ignore

    hou.setSessionModuleSource(
        textwrap.dedent("""
            from pathlib import Path
            import sys
            import hou

            hip_dir = str(Path(hou.hipFile.path()).resolve().parent)
            if hip_dir not in sys.path:
                sys.path.insert(0, hip_dir)
        """)
    )