from __future__ import annotations

import shutil
from pathlib import Path

FOLDER_NAME = "Shortlisted"


def _unique(dest: Path) -> Path:
    """Return ``dest`` or the first free ``name (1).pdf`` style alternative."""
    if not dest.exists():
        return dest
    index = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({index}){dest.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def shortlist(files: list[Path], base_folder: Path, move: bool = False) -> Path:
    """Copy (or move) ``files`` into ``base_folder/Shortlisted``.

    The target folder is created only if it is missing and is reused otherwise.
    Name collisions receive a numeric suffix so nothing is overwritten.
    Returns the target folder path.
    """
    target = base_folder / FOLDER_NAME
    target.mkdir(parents=True, exist_ok=True)

    for source in files:
        if not source.is_file():
            continue
        destination = _unique(target / source.name)
        if move:
            shutil.move(str(source), str(destination))
        else:
            shutil.copy2(str(source), str(destination))

    return target
