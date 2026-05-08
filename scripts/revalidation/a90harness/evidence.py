"""Private evidence output helpers for A90 host-side validation."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any


PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


def nofollow_flag() -> int:
    return getattr(os, "O_NOFOLLOW", 0)


def cloexec_flag() -> int:
    return getattr(os, "O_CLOEXEC", 0)


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, mode=PRIVATE_DIR_MODE, exist_ok=True)
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f"refusing non-directory output path: {path}")
    path.chmod(PRIVATE_DIR_MODE)


def write_private_bytes(path: Path, data: bytes) -> None:
    ensure_private_dir(path.parent)
    try:
        info = path.lstat()
    except FileNotFoundError:
        pass
    else:
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"refusing symlink destination: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | cloexec_flag() | nofollow_flag()
    fd = os.open(path, flags, PRIVATE_FILE_MODE)
    try:
        with os.fdopen(fd, "wb") as file_obj:
            fd = -1
            file_obj.write(data)
    finally:
        if fd >= 0:
            os.close(fd)
    path.chmod(PRIVATE_FILE_MODE)


def write_private_text(path: Path, text: str) -> None:
    write_private_bytes(path, text.encode("utf-8"))


def write_private_json(path: Path, payload: dict[str, Any]) -> None:
    write_private_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


class EvidenceStore:
    """Run-scoped private evidence directory."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        ensure_private_dir(run_dir.parent)
        ensure_private_dir(run_dir)

    def path(self, *parts: str) -> Path:
        return self.run_dir.joinpath(*parts)

    def mkdir(self, *parts: str) -> Path:
        path = self.path(*parts)
        ensure_private_dir(path)
        return path

    def write_text(self, relative_path: str, text: str) -> Path:
        path = self.path(relative_path)
        write_private_text(path, text)
        return path

    def write_json(self, relative_path: str, payload: dict[str, Any]) -> Path:
        path = self.path(relative_path)
        write_private_json(path, payload)
        return path

