#!/usr/bin/env python3
"""Build the patched FYG8 R4W1-B direct-PID1-init witness kernel host-only."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import struct
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_kernel_build as base  # noqa: E402
import s22plus_fyg8_r4w1b_patch_check as patch_check  # noqa: E402


SCHEMA = "s22plus_fyg8_r4w1b_build_v1"
TARGET = base.TARGET
STOCK_IMAGE_SIZE = 41_490_944
FIXED_KERNEL_SLOT_CAPACITY = 41_492_480
ABSOLUTE_RAMDISK_START = 41_496_576
R4W1B_MARKER_FAMILY = b"[[S22R4W1B|"
HISTORICAL_R4W1_MARKER_FAMILY = b"[[S22R4W1|"
BUILD_SH_PATH = Path("kernel_platform/build/build.sh")
BUILD_SH_SHA256 = "4b633f5ff11920307e193019248d69e2243ba20b4b55483a6bd419910a383690"
KMI_PATH_ORIGINAL = (
    "              --set-str UNUSED_KSYMS_WHITELIST "
    "${OUT_DIR}/abi_symbollist.raw\n"
)
KMI_PATH_REPRODUCIBLE = (
    "              --set-str UNUSED_KSYMS_WHITELIST "
    "../../out/msm-waipio-waipio-gki/gki_kernel/common/abi_symbollist.raw\n"
)
KERNEL_MAKEFILE_PATH = Path("kernel_platform/common/Makefile")
KERNEL_MAKEFILE_SHA256 = (
    "9dcb6faf9709e8bc5a0d52c08611e36b14788e04e0488c88178015142e9c0c0f"
)
KERNEL_DEBUG_PATH_ORIGINAL = (
    "# change __FILE__ to the relative path from the srctree\n"
    "KBUILD_CPPFLAGS += $(call cc-option,-fmacro-prefix-map=$(srctree)/=)\n"
)
KERNEL_DEBUG_PATH_REPRODUCIBLE = (
    KERNEL_DEBUG_PATH_ORIGINAL
    + "KBUILD_AFLAGS += -fdebug-prefix-map=$(abs_objtree)=/kernel-out\n"
    + "KBUILD_CFLAGS += -fdebug-prefix-map=$(abs_objtree)=/kernel-out\n"
)
VDSO_DEBUG_CONTROLS = (
    {
        "path": Path("kernel_platform/common/arch/arm64/kernel/vdso/Makefile"),
        "sha256": "ffea25de09036567a55f0618f37c7ec71d05bed2fda57080c7018e5a67957d5a",
        "original": "ccflags-y += -DDISABLE_BRANCH_PROFILING -DBUILD_VDSO\n",
        "reproducible": (
            "ccflags-y += -DDISABLE_BRANCH_PROFILING -DBUILD_VDSO\n"
            "ccflags-y += -fdebug-prefix-map=$(abs_srctree)=/kernel-src\n"
            "ccflags-y += -fdebug-prefix-map=$(abs_objtree)=/kernel-out\n"
            "asflags-y += -fdebug-prefix-map=$(abs_srctree)=/kernel-src\n"
            "asflags-y += -fdebug-prefix-map=$(abs_objtree)=/kernel-out\n"
        ),
    },
    {
        "path": Path("kernel_platform/common/arch/arm64/kernel/vdso32/Makefile"),
        "sha256": "a0f4a9ea0f57b075d5835d0d4755e2d70eaab1c90d49105da557ff1892986393",
        "original": "VDSO_CAFLAGS += -DDISABLE_BRANCH_PROFILING\n",
        "reproducible": (
            "VDSO_CAFLAGS += -DDISABLE_BRANCH_PROFILING\n"
            "VDSO_CAFLAGS += -fdebug-prefix-map=$(abs_srctree)=/kernel-src\n"
            "VDSO_CAFLAGS += -fdebug-prefix-map=$(abs_objtree)=/kernel-out\n"
        ),
    },
)
DEFAULT_RESULT_DIR = Path(
    "workspace/private/outputs/s22plus_fyg8_r4w1b_build/build"
)
HOST_PACKAGING_OUTPUTS = (
    "boot.img",
    "dtbo.img",
    "super.img",
    "vendor_boot.img",
    "vendor_dlkm.img",
)
PRIVATE_NAMESPACE_MARKER = "S22PLUS_R4W1B_PRIVATE_REPO_V1"
INITIAL_USER_NAMESPACE_MAP = "0 0 4294967295"
SAMSUNG_SOURCE_COMPATIBILITY_ROOT = "/home/dpi/qb5_8814/workspace/P4_1716/android"
PRIVATE_NAMESPACE_BOOTSTRAP = r"""
import ctypes
import json
import os
import sys

payload = json.loads(sys.argv[1])
libc = ctypes.CDLL(None, use_errno=True)
MS_BIND = 4096
MS_REC = 16384
MS_PRIVATE = 1 << 18
PR_SET_DUMPABLE = 4
PR_CAPBSET_DROP = 24
PR_SET_NO_NEW_PRIVS = 38

def mount(source, target, filesystem, flags, data=None):
    encoded = lambda value: value.encode() if value is not None else None
    if libc.mount(encoded(source), encoded(target), encoded(filesystem), flags, encoded(data)) != 0:
        raise OSError(ctypes.get_errno(), f"mount failed: {source!r} -> {target!r}")

mount(None, "/", None, MS_REC | MS_PRIVATE)
private_root = payload["private_root"]
mount("tmpfs", private_root, "tmpfs", 0, "mode=0700,size=16m")
repo_mount = os.path.join(private_root, "repo")
os.mkdir(repo_mount, 0o700)
source_stat = os.fstat(payload["repo_fd"])
if (source_stat.st_dev, source_stat.st_ino) != (
    payload["repo_device"], payload["repo_inode"]
):
    raise RuntimeError("inherited repository FD identity mismatch")
repo_source = os.readlink(f"/proc/self/fd/{payload['repo_fd']}")
mount(repo_source, repo_mount, None, MS_BIND)
mounted_stat = os.stat(repo_mount)
if (source_stat.st_dev, source_stat.st_ino) != (mounted_stat.st_dev, mounted_stat.st_ino):
    raise RuntimeError("private repository bind identity mismatch")
recorded_root = payload["recorded_root"]
if not os.path.isabs(recorded_root) or recorded_root == "/":
    raise RuntimeError("invalid recorded repository root")
recorded_stat = os.stat(recorded_root)
if (source_stat.st_dev, source_stat.st_ino) != (
    recorded_stat.st_dev, recorded_stat.st_ino
):
    raise RuntimeError("recorded repository identity mismatch")
compatibility_work_tree = payload.get("compatibility_work_tree")
if compatibility_work_tree:
    mount("tmpfs", "/home", "tmpfs", 0, "mode=0755,size=16m")
    if os.path.commonpath((recorded_root, "/home")) == "/home":
        os.makedirs(os.path.dirname(recorded_root), mode=0o700, exist_ok=True)
        os.mkdir(recorded_root, 0o700)
mount(repo_mount, recorded_root, None, MS_BIND)
shadowed_stat = os.stat(recorded_root)
if (source_stat.st_dev, source_stat.st_ino) != (
    shadowed_stat.st_dev, shadowed_stat.st_ino
):
    raise RuntimeError("recorded repository shadow bind identity mismatch")
if compatibility_work_tree:
    compatibility_source = os.path.join(repo_mount, compatibility_work_tree)
    compatibility_source_stat = os.stat(compatibility_source)
    if not os.path.isdir(compatibility_source):
        raise RuntimeError("compatibility work tree is not a directory")
    compatibility_root = payload["compatibility_root"]
    os.makedirs(os.path.dirname(compatibility_root), mode=0o700, exist_ok=True)
    os.mkdir(compatibility_root, 0o700)
    mount(compatibility_source, compatibility_root, None, MS_BIND)
    compatibility_stat = os.stat(compatibility_root)
    if (compatibility_source_stat.st_dev, compatibility_source_stat.st_ino) != (
        compatibility_stat.st_dev, compatibility_stat.st_ino
    ):
        raise RuntimeError("Samsung source compatibility bind identity mismatch")

if libc.prctl(PR_SET_DUMPABLE, 0, 0, 0, 0) != 0:
    raise OSError(ctypes.get_errno(), "PR_SET_DUMPABLE failed")
for capability in range(64):
    libc.prctl(PR_CAPBSET_DROP, capability, 0, 0, 0)
if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
    raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS failed")

class CapHeader(ctypes.Structure):
    _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]

class CapData(ctypes.Structure):
    _fields_ = [
        ("effective", ctypes.c_uint32),
        ("permitted", ctypes.c_uint32),
        ("inheritable", ctypes.c_uint32),
    ]

header = CapHeader(0x20080522, 0)
data = (CapData * 2)()
if libc.capset(ctypes.byref(header), ctypes.byref(data)) != 0:
    raise OSError(ctypes.get_errno(), "capset failed")

environment = os.environ.copy()
environment.update(
    {
        "S22PLUS_R4W1B_PRIVATE_NAMESPACE": payload["marker"],
        "S22PLUS_R4W1B_PRIVATE_REPO": repo_mount,
        "S22PLUS_R4W1B_RECORDED_REPO": payload["recorded_root"],
        "S22PLUS_R4W1B_REPO_DEVICE": str(source_stat.st_dev),
        "S22PLUS_R4W1B_REPO_INODE": str(source_stat.st_ino),
        "S22PLUS_R4W1B_COMPATIBILITY_WORK_TREE": compatibility_work_tree or "",
        "S22PLUS_R4W1B_COMPATIBILITY_ROOT": payload.get("compatibility_root", ""),
    }
)
script = os.path.join(repo_mount, payload["script_relative"])
os.chdir(repo_mount)
os.execve(sys.executable, [sys.executable, script, *payload["arguments"]], environment)
"""


class BuildError(ValueError):
    pass


def _status_fields() -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key] = value.strip()
    return fields


def inspect_outer_namespace() -> dict[str, Any]:
    status = _status_fields()
    uid_map = " ".join(
        Path("/proc/self/uid_map").read_text(encoding="ascii").split()
    )
    cap_eff = int(status.get("CapEff", "0"), 16)
    result = {
        "uid": os.getuid(),
        "effective_uid": os.geteuid(),
        "uid_map": uid_map,
        "cap_eff": cap_eff,
        "cap_sys_admin": bool(cap_eff & (1 << 21)),
    }
    result["verified"] = (
        result["uid"] != 0
        and result["effective_uid"] != 0
        and result["uid_map"] == INITIAL_USER_NAMESPACE_MAP
        and not result["cap_sys_admin"]
    )
    return result


def inspect_private_namespace(repo_root: Path) -> dict[str, Any]:
    status = _status_fields()
    uid_map = " ".join(
        Path("/proc/self/uid_map").read_text(encoding="ascii").split()
    )
    repo_stat = repo_root.stat()
    expected_device = os.environ.get("S22PLUS_R4W1B_REPO_DEVICE")
    expected_inode = os.environ.get("S22PLUS_R4W1B_REPO_INODE")
    recorded_repo = os.environ.get("S22PLUS_R4W1B_RECORDED_REPO")
    recorded_stat = Path(recorded_repo).stat() if recorded_repo else None
    compatibility_relative = os.environ.get(
        "S22PLUS_R4W1B_COMPATIBILITY_WORK_TREE"
    )
    compatibility_root = os.environ.get("S22PLUS_R4W1B_COMPATIBILITY_ROOT")
    compatibility_source = (
        repo_root / compatibility_relative if compatibility_relative else None
    )
    compatibility_source_stat = (
        compatibility_source.stat() if compatibility_source is not None else None
    )
    compatibility_stat = (
        Path(compatibility_root).stat() if compatibility_root else None
    )
    mountpoints = {
        line.split(" - ", 1)[0].split()[4]
        for line in Path("/proc/self/mountinfo").read_text(encoding="ascii").splitlines()
        if " - " in line and len(line.split(" - ", 1)[0].split()) >= 5
    }
    result = {
        "marker": os.environ.get("S22PLUS_R4W1B_PRIVATE_NAMESPACE"),
        "private_repo": os.environ.get("S22PLUS_R4W1B_PRIVATE_REPO"),
        "recorded_repo": recorded_repo,
        "recorded_repo_shadow_mounted": recorded_repo in mountpoints,
        "compatibility_work_tree": compatibility_relative,
        "compatibility_root": compatibility_root,
        "compatibility_root_mounted": (
            compatibility_root in mountpoints if compatibility_root else None
        ),
        "uid_map": uid_map,
        "cap_eff": int(status.get("CapEff", "0"), 16),
        "cap_prm": int(status.get("CapPrm", "0"), 16),
        "cap_bnd": int(status.get("CapBnd", "0"), 16),
        "no_new_privs": status.get("NoNewPrivs"),
        "repo_device": repo_stat.st_dev,
        "repo_inode": repo_stat.st_ino,
    }
    result["verified"] = (
        result["marker"] == PRIVATE_NAMESPACE_MARKER
        and result["private_repo"] == str(repo_root)
        and bool(result["recorded_repo"])
        and result["recorded_repo_shadow_mounted"]
        and result["uid_map"] != INITIAL_USER_NAMESPACE_MAP
        and result["cap_eff"] == 0
        and result["cap_prm"] == 0
        and result["cap_bnd"] == 0
        and result["no_new_privs"] == "1"
        and expected_device == str(result["repo_device"])
        and expected_inode == str(result["repo_inode"])
        and recorded_stat is not None
        and recorded_stat.st_dev == result["repo_device"]
        and recorded_stat.st_ino == result["repo_inode"]
        and (
            not compatibility_relative
            or (
                compatibility_root == SAMSUNG_SOURCE_COMPATIBILITY_ROOT
                and result["compatibility_root_mounted"]
                and compatibility_source_stat is not None
                and compatibility_stat is not None
                and compatibility_source_stat.st_dev == compatibility_stat.st_dev
                and compatibility_source_stat.st_ino == compatibility_stat.st_ino
            )
        )
    )
    result["private_repo"] = "<private-tmpfs-repository-bind>"
    return result


def reexec_in_private_repo_namespace(
    repo_root: Path,
    *,
    script: Path,
    arguments: list[str],
    compatibility_work_tree: Path | None = None,
) -> int | None:
    if os.environ.get("S22PLUS_R4W1B_PRIVATE_NAMESPACE"):
        return None
    outer = inspect_outer_namespace()
    if not outer["verified"]:
        raise BuildError("R4W1-B requires a normal unprivileged host namespace")
    relative_script = script.resolve().relative_to(repo_root.resolve())
    compatibility_relative: str | None = None
    if compatibility_work_tree is not None:
        if compatibility_work_tree.is_absolute() or ".." in compatibility_work_tree.parts:
            raise BuildError("compatibility work tree must be a safe relative path")
        compatibility_relative = str(compatibility_work_tree)
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    repo_descriptor = os.open(repo_root, flags)
    try:
        repo_stat = os.fstat(repo_descriptor)
        with tempfile.TemporaryDirectory(prefix="s22-r4w1b-private-") as private_root:
            payload = {
                "marker": PRIVATE_NAMESPACE_MARKER,
                "private_root": private_root,
                "repo_fd": repo_descriptor,
                "repo_device": repo_stat.st_dev,
                "repo_inode": repo_stat.st_ino,
                "recorded_root": str(repo_root.resolve()),
                "compatibility_work_tree": compatibility_relative,
                "compatibility_root": SAMSUNG_SOURCE_COMPATIBILITY_ROOT,
                "script_relative": str(relative_script),
                "arguments": arguments,
            }
            completed = subprocess.run(
                [
                    "/usr/bin/unshare",
                    "-Urnm",
                    "--fork",
                    "--kill-child",
                    sys.executable,
                    "-I",
                    "-B",
                    "-c",
                    PRIVATE_NAMESPACE_BOOTSTRAP,
                    json.dumps(payload, sort_keys=True),
                ],
                pass_fds=(repo_descriptor,),
                check=False,
            )
            return completed.returncode
    finally:
        os.close(repo_descriptor)


def inspect_kmi_path_control(work_tree: Path) -> dict[str, Any]:
    path = work_tree / BUILD_SH_PATH
    if path.is_symlink() or not path.is_file():
        return {"path": str(path), "verified": False, "reason": "missing-or-indirect"}
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        return {"path": str(path), "verified": False, "reason": "not-utf8"}
    metadata = path.stat()
    replaced = text.replace(KMI_PATH_ORIGINAL, KMI_PATH_REPRODUCIBLE, 1).encode()
    result = {
        "path": str(path),
        "original_sha256": base.sha256_file(path),
        "expected_original_sha256": BUILD_SH_SHA256,
        "patched_sha256": __import__("hashlib").sha256(replaced).hexdigest(),
        "original_mode": stat.S_IMODE(metadata.st_mode),
        "original_atime_ns": metadata.st_atime_ns,
        "original_mtime_ns": metadata.st_mtime_ns,
        "match_count": text.count(KMI_PATH_ORIGINAL),
        "reproducible_path": KMI_PATH_REPRODUCIBLE.strip(),
        "parent_writable": os.access(path.parent, os.W_OK),
    }
    result["verified"] = (
        result["original_sha256"] == BUILD_SH_SHA256
        and result["match_count"] == 1
        and replaced != original
        and result["parent_writable"]
    )
    return result


@contextmanager
def apply_kmi_path_control(
    work_tree: Path, control: dict[str, Any]
) -> Iterator[dict[str, Any]]:
    if not control.get("verified"):
        raise BuildError("KMI path reproducibility control is not verified")
    path = work_tree / BUILD_SH_PATH
    original = path.read_bytes()
    if base.sha256_file(path) != control["original_sha256"]:
        raise BuildError("build.sh changed after KMI path preflight")
    patched = original.decode("utf-8").replace(
        KMI_PATH_ORIGINAL, KMI_PATH_REPRODUCIBLE, 1
    ).encode("utf-8")
    base.atomic_replace_bytes(path, patched, mode=control["original_mode"])
    runtime = dict(control)
    runtime.update({"applied": True, "restored": False})
    try:
        yield runtime
    finally:
        current_sha = base.sha256_file(path) if path.is_file() else None
        base.atomic_replace_bytes(path, original, mode=control["original_mode"])
        os.utime(
            path,
            ns=(control["original_atime_ns"], control["original_mtime_ns"]),
            follow_symlinks=False,
        )
        runtime["patched_content_unchanged"] = current_sha == control["patched_sha256"]
        runtime["restored_sha256"] = base.sha256_file(path)
        runtime["restored_mode"] = stat.S_IMODE(path.stat().st_mode)
        runtime["restored"] = (
            runtime["restored_sha256"] == control["original_sha256"]
            and runtime["restored_mode"] == control["original_mode"]
        )
        if not runtime["patched_content_unchanged"] or not runtime["restored"]:
            raise BuildError("KMI path control was not cleanly restored")


def inspect_vdso_debug_control(work_tree: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for spec in VDSO_DEBUG_CONTROLS:
        path = work_tree / spec["path"]
        if path.is_symlink() or not path.is_file():
            rows.append(
                {"path": str(path), "verified": False, "reason": "missing-or-indirect"}
            )
            continue
        original = path.read_bytes()
        try:
            text = original.decode("utf-8")
        except UnicodeDecodeError:
            rows.append({"path": str(path), "verified": False, "reason": "not-utf8"})
            continue
        metadata = path.stat()
        patched = text.replace(spec["original"], spec["reproducible"], 1).encode(
            "utf-8"
        )
        row = {
            "path": str(path),
            "relative_path": str(spec["path"]),
            "original_sha256": base.sha256_file(path),
            "expected_original_sha256": spec["sha256"],
            "patched_sha256": __import__("hashlib").sha256(patched).hexdigest(),
            "original_mode": stat.S_IMODE(metadata.st_mode),
            "original_atime_ns": metadata.st_atime_ns,
            "original_mtime_ns": metadata.st_mtime_ns,
            "match_count": text.count(spec["original"]),
            "source_map": "/kernel-src",
            "object_map": "/kernel-out",
            "parent_writable": os.access(path.parent, os.W_OK),
        }
        row["verified"] = (
            row["original_sha256"] == spec["sha256"]
            and row["match_count"] == 1
            and patched != original
            and row["parent_writable"]
        )
        rows.append(row)
    return {
        "files": rows,
        "expected_file_count": len(VDSO_DEBUG_CONTROLS),
        "verified": (
            len(rows) == len(VDSO_DEBUG_CONTROLS)
            and all(row.get("verified") for row in rows)
        ),
    }


def inspect_kernel_debug_control(work_tree: Path) -> dict[str, Any]:
    path = work_tree / KERNEL_MAKEFILE_PATH
    if path.is_symlink() or not path.is_file():
        return {"path": str(path), "verified": False, "reason": "missing-or-indirect"}
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        return {"path": str(path), "verified": False, "reason": "not-utf8"}
    metadata = path.stat()
    patched = text.replace(
        KERNEL_DEBUG_PATH_ORIGINAL, KERNEL_DEBUG_PATH_REPRODUCIBLE, 1
    ).encode("utf-8")
    result = {
        "path": str(path),
        "original_sha256": base.sha256_file(path),
        "expected_original_sha256": KERNEL_MAKEFILE_SHA256,
        "patched_sha256": __import__("hashlib").sha256(patched).hexdigest(),
        "original_mode": stat.S_IMODE(metadata.st_mode),
        "original_atime_ns": metadata.st_atime_ns,
        "original_mtime_ns": metadata.st_mtime_ns,
        "match_count": text.count(KERNEL_DEBUG_PATH_ORIGINAL),
        "object_map": "/kernel-out",
        "parent_writable": os.access(path.parent, os.W_OK),
    }
    result["verified"] = (
        result["original_sha256"] == KERNEL_MAKEFILE_SHA256
        and result["match_count"] == 1
        and patched != original
        and result["parent_writable"]
    )
    return result


@contextmanager
def apply_kernel_debug_control(
    work_tree: Path, control: dict[str, Any]
) -> Iterator[dict[str, Any]]:
    if not control.get("verified"):
        raise BuildError("kernel debug-path reproducibility control is not verified")
    path = work_tree / KERNEL_MAKEFILE_PATH
    original = path.read_bytes()
    if base.sha256_file(path) != control["original_sha256"]:
        raise BuildError("kernel Makefile changed after debug-path preflight")
    patched = original.decode("utf-8").replace(
        KERNEL_DEBUG_PATH_ORIGINAL, KERNEL_DEBUG_PATH_REPRODUCIBLE, 1
    ).encode("utf-8")
    base.atomic_replace_bytes(path, patched, mode=control["original_mode"])
    runtime = dict(control)
    runtime.update({"applied": True, "restored": False})
    try:
        yield runtime
    finally:
        current_sha = base.sha256_file(path) if path.is_file() else None
        base.atomic_replace_bytes(path, original, mode=control["original_mode"])
        os.utime(
            path,
            ns=(control["original_atime_ns"], control["original_mtime_ns"]),
            follow_symlinks=False,
        )
        runtime["patched_content_unchanged"] = current_sha == control["patched_sha256"]
        runtime["restored_sha256"] = base.sha256_file(path)
        runtime["restored_mode"] = stat.S_IMODE(path.stat().st_mode)
        runtime["restored"] = (
            runtime["restored_sha256"] == control["original_sha256"]
            and runtime["restored_mode"] == control["original_mode"]
        )
        if not runtime["patched_content_unchanged"] or not runtime["restored"]:
            raise BuildError("kernel debug-path control was not cleanly restored")


@contextmanager
def apply_vdso_debug_control(
    work_tree: Path, control: dict[str, Any]
) -> Iterator[dict[str, Any]]:
    if not control.get("verified"):
        raise BuildError("VDSO debug-path reproducibility control is not verified")
    originals: dict[Path, bytes] = {}
    patched_hashes: dict[Path, str] = {}
    rows_by_relative = {
        row["relative_path"]: row for row in control.get("files", [])
    }
    runtime = dict(control)
    runtime["files"] = [dict(row) for row in control["files"]]
    runtime.update({"applied": False, "restored": False})
    written: list[Path] = []
    try:
        for spec in VDSO_DEBUG_CONTROLS:
            path = work_tree / spec["path"]
            row = rows_by_relative[str(spec["path"])]
            original = path.read_bytes()
            if base.sha256_file(path) != row["original_sha256"]:
                raise BuildError(f"VDSO Makefile changed after preflight: {path}")
            patched = original.decode("utf-8").replace(
                spec["original"], spec["reproducible"], 1
            ).encode("utf-8")
            originals[path] = original
            patched_hashes[path] = row["patched_sha256"]
            base.atomic_replace_bytes(path, patched, mode=row["original_mode"])
            written.append(path)
        runtime["applied"] = True
        yield runtime
    finally:
        runtime_rows = {row["relative_path"]: row for row in runtime["files"]}
        for path in reversed(written):
            relative = str(path.relative_to(work_tree))
            row = runtime_rows[relative]
            current_sha = base.sha256_file(path) if path.is_file() else None
            base.atomic_replace_bytes(path, originals[path], mode=row["original_mode"])
            os.utime(
                path,
                ns=(row["original_atime_ns"], row["original_mtime_ns"]),
                follow_symlinks=False,
            )
            row["patched_content_unchanged"] = current_sha == patched_hashes[path]
            row["restored_sha256"] = base.sha256_file(path)
            row["restored_mode"] = stat.S_IMODE(path.stat().st_mode)
            row["restored"] = (
                row["restored_sha256"] == row["original_sha256"]
                and row["restored_mode"] == row["original_mode"]
            )
        runtime["patched_content_unchanged"] = (
            len(written) == len(VDSO_DEBUG_CONTROLS)
            and all(row.get("patched_content_unchanged") for row in runtime["files"])
        )
        runtime["restored"] = (
            len(written) == len(VDSO_DEBUG_CONTROLS)
            and all(row.get("restored") for row in runtime["files"])
        )
        if written and (
            not runtime["patched_content_unchanged"] or not runtime["restored"]
        ):
            raise BuildError("VDSO debug-path control was not cleanly restored")


def witness_output_gate(work_tree: Path) -> dict[str, Any]:
    dist = work_tree / "out/msm-waipio-waipio-gki/gki_kernel/dist"
    image = dist / "Image"
    vmlinux = dist / "vmlinux"
    config = work_tree / "out/msm-waipio-waipio-gki/gki_kernel/common/.config"
    missing = [str(path) for path in (image, vmlinux, config) if not path.is_file()]
    if missing:
        return {"missing": missing, "verified": False}
    marker = patch_check.MARKER.encode("ascii")
    image_data = image.read_bytes()
    vmlinux_data = vmlinux.read_bytes()
    config_text = config.read_text(encoding="utf-8")
    aligned_image_size = (len(image_data) + 4095) & ~4095
    result = {
        "image_size": len(image_data),
        "aligned_image_size": aligned_image_size,
        "stock_image_size": STOCK_IMAGE_SIZE,
        "exact_stock_image_size": len(image_data) == STOCK_IMAGE_SIZE,
        "fixed_kernel_slot_capacity": FIXED_KERNEL_SLOT_CAPACITY,
        "absolute_ramdisk_start": ABSOLUTE_RAMDISK_START,
        "pre_ramdisk_slack_remaining": FIXED_KERNEL_SLOT_CAPACITY - len(image_data),
        "fits_fixed_ramdisk_layout": len(image_data) <= FIXED_KERNEL_SLOT_CAPACITY,
        "preserves_fixed_ramdisk_start": (
            aligned_image_size == FIXED_KERNEL_SLOT_CAPACITY
        ),
        "image_marker_count": image_data.count(marker),
        "vmlinux_marker_count": vmlinux_data.count(marker),
        "image_family_count": image_data.count(R4W1B_MARKER_FAMILY),
        "vmlinux_family_count": vmlinux_data.count(R4W1B_MARKER_FAMILY),
        "image_historical_family_count": image_data.count(
            HISTORICAL_R4W1_MARKER_FAMILY
        ),
        "vmlinux_historical_family_count": vmlinux_data.count(
            HISTORICAL_R4W1_MARKER_FAMILY
        ),
        "config_enable_count": config_text.splitlines().count(
            "CONFIG_S22PLUS_FYG8_RETAINED_WITNESS=y"
        ),
        "fips_enable_count": config_text.splitlines().count(
            "CONFIG_CRYPTO_FIPS=y"
        ),
        "missing": [],
    }
    result["verified"] = (
        result["exact_stock_image_size"]
        and result["fits_fixed_ramdisk_layout"]
        and result["preserves_fixed_ramdisk_start"]
        and result["image_marker_count"] == 1
        and result["vmlinux_marker_count"] == 1
        and result["image_family_count"] == 1
        and result["vmlinux_family_count"] == 1
        and result["image_historical_family_count"] == 0
        and result["vmlinux_historical_family_count"] == 0
        and result["config_enable_count"] == 1
        and result["fips_enable_count"] == 1
    )
    return result


def collect_host_packaging_outputs(work_tree: Path) -> dict[str, Any]:
    dist = work_tree / "out/msm-waipio-waipio-gki/dist"
    rows = []
    for name in HOST_PACKAGING_OUTPUTS:
        path = dist / name
        if path.is_file() and not path.is_symlink():
            rows.append(
                {
                    "name": name,
                    "path": str(path),
                    "size": path.stat().st_size,
                    "sha256": base.sha256_file(path),
                }
            )
    present = {row["name"] for row in rows}
    return {
        "dist": str(dist),
        "expected": list(HOST_PACKAGING_OUTPUTS),
        "outputs": rows,
        "missing": sorted(set(HOST_PACKAGING_OUTPUTS) - present),
        "generated": bool(rows),
        "complete": present == set(HOST_PACKAGING_OUTPUTS),
        "promoted_as_live_candidate": False,
        "flash_authorized": False,
    }


def create_exclusive_result_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir()
    except FileExistsError as exc:
        raise BuildError(f"result directory already exists: {path}") from exc


def inspect_clean_output_precondition(work_tree: Path) -> dict[str, Any]:
    output = work_tree / "out"
    work_stat = work_tree.stat()
    result = {
        "path": str(output),
        "exists": output.exists() or output.is_symlink(),
        "work_tree_realpath": str(work_tree.resolve()),
        "work_tree_device": work_stat.st_dev,
        "work_tree_inode": work_stat.st_ino,
    }
    result["verified"] = not result["exists"]
    return result


def rebase_recorded_paths(
    value: Any,
    *,
    observed_root: Path,
    recorded_root: Path,
    embedded: bool = False,
) -> Any:
    observed = str(observed_root)
    recorded = str(recorded_root)
    if isinstance(value, str):
        if embedded:
            return value.replace(observed, recorded)
        if value == observed:
            return recorded
        if value.startswith(observed + os.sep):
            return recorded + value[len(observed) :]
        return value
    if isinstance(value, list):
        return [
            rebase_recorded_paths(
                item,
                observed_root=observed_root,
                recorded_root=recorded_root,
                embedded=embedded,
            )
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: rebase_recorded_paths(
                item,
                observed_root=observed_root,
                recorded_root=recorded_root,
                embedded=embedded,
            )
            for key, item in value.items()
        }
    return value


def collect_bound_symvers(work_tree: Path) -> list[dict[str, Any]]:
    out_root = work_tree / "out"
    if not out_root.is_dir():
        return []
    paths = {
        str(path.relative_to(out_root)): path
        for pattern in ("Module.symvers", "vmlinux.symvers")
        for path in out_root.rglob(pattern)
        if path.is_file() and not path.is_symlink()
    }
    return [
        {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": base.sha256_file(path),
        }
        for _, path in sorted(paths.items())
    ]


@contextmanager
def create_exclusive_output_root(
    work_tree: Path, *, expected_work_tree: dict[str, Any] | None = None
) -> Iterator[dict[str, Any]]:
    output = work_tree / "out"
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    work_tree_descriptor = os.open(work_tree, flags)
    work_tree_opened = os.fstat(work_tree_descriptor)
    preflight_work_tree_identity_match = (
        expected_work_tree is None
        or (
            work_tree_opened.st_dev == expected_work_tree.get("work_tree_device")
            and work_tree_opened.st_ino == expected_work_tree.get("work_tree_inode")
        )
    )
    if not preflight_work_tree_identity_match:
        os.close(work_tree_descriptor)
        raise BuildError("work tree changed between preflight and FD bind")
    try:
        os.mkdir("out", mode=0o755, dir_fd=work_tree_descriptor)
    except FileExistsError as exc:
        os.close(work_tree_descriptor)
        raise BuildError(f"output tree appeared after preflight: {output}") from exc
    descriptor = os.open("out", flags, dir_fd=work_tree_descriptor)
    opened = os.fstat(descriptor)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.inotify_init1.argtypes = [ctypes.c_int]
    libc.inotify_init1.restype = ctypes.c_int
    inotify_fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    if inotify_fd < 0:
        os.close(descriptor)
        os.close(work_tree_descriptor)
        raise BuildError(f"inotify_init1 failed: errno={ctypes.get_errno()}")
    inotify_add_watch = libc.inotify_add_watch
    inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    inotify_add_watch.restype = ctypes.c_int
    targets_by_parent: dict[Path, set[str]] = {work_tree: {output.name}}
    descendant = work_tree
    while descendant != descendant.parent:
        targets_by_parent.setdefault(descendant.parent, set()).add(descendant.name)
        descendant = descendant.parent
    namespace_watches: dict[int, dict[str, Any]] = {}
    namespace_mask = (
        0x00000100
        | 0x00000200
        | 0x00000040
        | 0x00000080
        | 0x00000400
        | 0x00000800
    )
    for parent, names in targets_by_parent.items():
        watch = inotify_add_watch(
            inotify_fd, os.fsencode(parent), namespace_mask
        )
        if watch < 0:
            error = ctypes.get_errno()
            os.close(inotify_fd)
            os.close(descriptor)
            os.close(work_tree_descriptor)
            raise BuildError(
                f"inotify_add_watch failed for {parent}: errno={error}"
            )
        namespace_watches[watch] = {"parent": str(parent), "names": names}
    output_watch = inotify_add_watch(
        inotify_fd, os.fsencode(output), 0x00000400 | 0x00000800
    )
    if output_watch < 0:
        error = ctypes.get_errno()
        os.close(inotify_fd)
        os.close(descriptor)
        os.close(work_tree_descriptor)
        raise BuildError(f"inotify_add_watch failed: errno={error}")
    runtime: dict[str, Any] = {
        "path": str(output),
        "created_exclusively": True,
        "device": opened.st_dev,
        "inode": opened.st_ino,
        "work_tree_device": work_tree_opened.st_dev,
        "work_tree_inode": work_tree_opened.st_ino,
        "work_tree_access": "held-fd-via-parent-procfs",
        "_work_tree_fd_path": f"/proc/{os.getpid()}/fd/{work_tree_descriptor}",
        "preflight_work_tree_identity_match": preflight_work_tree_identity_match,
        "namespace_watch_count": len(namespace_watches) + 1,
        "empty_at_creation": not os.listdir(descriptor),
        "same_inode_after_build": False,
        "same_work_tree_inode_after_build": False,
        "namespace_events": [],
        "namespace_unchanged": False,
        "verified": False,
    }
    try:
        if not runtime["empty_at_creation"]:
            raise BuildError(f"exclusive output root was not empty: {output}")
        yield runtime
    finally:
        try:
            event_header = struct.Struct("iIII")
            events: list[dict[str, Any]] = []
            while True:
                try:
                    data = os.read(inotify_fd, 64 * 1024)
                except BlockingIOError:
                    break
                if not data:
                    break
                offset = 0
                while offset + event_header.size <= len(data):
                    watch, mask, cookie, name_size = event_header.unpack_from(data, offset)
                    offset += event_header.size
                    raw_name = data[offset : offset + name_size]
                    offset += name_size
                    event_name = os.fsdecode(raw_name.split(b"\0", 1)[0])
                    namespace_row = namespace_watches.get(watch)
                    if (
                        mask & 0x00004000
                        or watch == output_watch
                        or (
                            namespace_row is not None
                            and (
                                mask & (0x00000400 | 0x00000800)
                                or event_name in namespace_row["names"]
                            )
                        )
                    ):
                        events.append(
                            {
                                "watch": watch,
                                "mask": mask,
                                "cookie": cookie,
                                "name": event_name,
                                "parent": (
                                    namespace_row["parent"]
                                    if namespace_row is not None
                                    else str(output)
                                ),
                            }
                        )
            runtime["namespace_events"] = events
            runtime["namespace_unchanged"] = not events
            path_stat = output.stat(follow_symlinks=False)
            fd_stat = os.fstat(descriptor)
            work_tree_path_stat = work_tree.stat(follow_symlinks=False)
            work_tree_fd_stat = os.fstat(work_tree_descriptor)
            runtime["same_inode_after_build"] = (
                stat.S_ISDIR(path_stat.st_mode)
                and path_stat.st_dev == opened.st_dev == fd_stat.st_dev
                and path_stat.st_ino == opened.st_ino == fd_stat.st_ino
            )
            runtime["same_work_tree_inode_after_build"] = (
                stat.S_ISDIR(work_tree_path_stat.st_mode)
                and work_tree_path_stat.st_dev
                == work_tree_opened.st_dev
                == work_tree_fd_stat.st_dev
                and work_tree_path_stat.st_ino
                == work_tree_opened.st_ino
                == work_tree_fd_stat.st_ino
            )
            runtime["verified"] = (
                runtime["created_exclusively"]
                and runtime["empty_at_creation"]
                and runtime["preflight_work_tree_identity_match"]
                and runtime["same_inode_after_build"]
                and runtime["same_work_tree_inode_after_build"]
                and runtime["namespace_unchanged"]
            )
        finally:
            os.close(inotify_fd)
            os.close(descriptor)
            os.close(work_tree_descriptor)


@contextmanager
def apply_checked_patch(
    work_tree: Path, patch: Path
) -> Iterator[dict[str, Any]]:
    patch_flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        patch_flags |= os.O_NOFOLLOW
    patch_descriptor = os.open(patch, patch_flags)
    try:
        patch_before = os.fstat(patch_descriptor)
        if not stat.S_ISREG(patch_before.st_mode):
            raise BuildError("R4W1-B source patch is not a regular file")
        patch_bytes = bytearray()
        while chunk := os.read(patch_descriptor, 1024 * 1024):
            patch_bytes.extend(chunk)
        patch_after = os.fstat(patch_descriptor)
    finally:
        os.close(patch_descriptor)
    patch_stable = (
        patch_before.st_dev == patch_after.st_dev
        and patch_before.st_ino == patch_after.st_ino
        and patch_before.st_size == patch_after.st_size
        and patch_before.st_mtime_ns == patch_after.st_mtime_ns
        and patch_before.st_ctime_ns == patch_after.st_ctime_ns
    )
    patch_sha256 = hashlib.sha256(patch_bytes).hexdigest()
    if not patch_stable or patch_sha256 != patch_check.PATCH_SHA256:
        raise BuildError("R4W1-B source patch bytes are not the exact stable pin")
    before: dict[str, dict[str, Any]] = {}
    originals: dict[str, bytes] = {}
    for relative, expected in patch_check.BASE_FILES.items():
        path = work_tree / relative
        actual = base.sha256_file(path)
        if actual != expected:
            raise BuildError(f"pre-apply SHA mismatch for {relative}: {actual}")
        metadata = path.stat()
        mode = stat.S_IMODE(metadata.st_mode)
        originals[relative] = path.read_bytes()
        before[relative] = {
            "sha256": actual,
            "mode": mode,
            "atime_ns": metadata.st_atime_ns,
            "mtime_ns": metadata.st_mtime_ns,
        }
    runtime: dict[str, Any] = {
        "patch_sha256": patch_sha256,
        "patch_bytes_stable": patch_stable,
        "patch_delivery": "verified-bytes-via-stdin",
        "before": before,
        "after": {},
        "applied": False,
        "restored": False,
        "patched_content_unchanged": False,
        "verified": False,
    }
    try:
        for relative, row in before.items():
            os.chmod(work_tree / relative, row["mode"] | stat.S_IWUSR)
        completed = subprocess.run(
            ["patch", "--batch", "--forward", "-p1"],
            cwd=work_tree,
            input=bytes(patch_bytes).decode("utf-8"),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        runtime["stdout"] = completed.stdout
        if completed.returncode != 0:
            raise BuildError(f"patch apply failed: {completed.stdout[-3000:]}")
        after: dict[str, dict[str, Any]] = {}
        for relative, expected in patch_check.PATCHED_FILES.items():
            path = work_tree / relative
            actual = base.sha256_file(path)
            if actual != expected:
                raise BuildError(f"post-apply SHA mismatch for {relative}: {actual}")
            after[relative] = {
                "sha256": actual,
                "mode": stat.S_IMODE(path.stat().st_mode),
            }
        runtime.update({"after": after, "applied": True})
        yield runtime
    finally:
        unchanged = True
        restored = True
        restore_rows: dict[str, dict[str, Any]] = {}
        for relative, original in originals.items():
            path = work_tree / relative
            expected_patched = patch_check.PATCHED_FILES.get(relative)
            current_sha = base.sha256_file(path) if path.is_file() else None
            if runtime["applied"] and current_sha != expected_patched:
                unchanged = False
            row = before[relative]
            base.atomic_replace_bytes(path, original, mode=row["mode"])
            os.utime(
                path,
                ns=(row["atime_ns"], row["mtime_ns"]),
                follow_symlinks=False,
            )
            restored_sha = base.sha256_file(path)
            restored_mode = stat.S_IMODE(path.stat().st_mode)
            row_restored = (
                restored_sha == row["sha256"] and restored_mode == row["mode"]
            )
            restored = restored and row_restored
            restore_rows[relative] = {
                "sha256": restored_sha,
                "mode": restored_mode,
                "restored": row_restored,
            }
        runtime["patched_content_unchanged"] = runtime["applied"] and unchanged
        runtime["restored_files"] = restore_rows
        runtime["restored"] = restored
        runtime["verified"] = (
            runtime["applied"]
            and runtime["patched_content_unchanged"]
            and runtime["restored"]
        )
        if runtime["applied"] and not runtime["verified"]:
            raise BuildError("R4W1-B source patch was not cleanly restored")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "build"), default="preflight")
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    parser.add_argument("--work-tree", type=Path, default=base.DEFAULT_WORK_TREE)
    parser.add_argument("--clang-repo", type=Path, default=base.DEFAULT_CLANG_REPO)
    parser.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIR)
    parser.add_argument("--base-archive", type=Path, default=base.DEFAULT_BASE_ARCHIVE)
    parser.add_argument("--delta-archive", type=Path, default=base.DEFAULT_DELTA_ARCHIVE)
    parser.add_argument("--overlay-audit", type=Path, default=base.DEFAULT_OVERLAY_AUDIT)
    parser.add_argument("--stock-baseline", type=Path, default=base.DEFAULT_STOCK_BASELINE)
    parser.add_argument("--patch", type=Path, default=patch_check.DEFAULT_PATCH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.jobs < 1 or args.jobs > 64:
        raise BuildError("--jobs must be between 1 and 64")
    root = base.repo_root()
    path_arguments = (
        args.work_tree,
        args.clang_repo,
        args.result_dir,
        args.base_archive,
        args.delta_archive,
        args.overlay_audit,
        args.stock_baseline,
        args.patch,
    )
    if any(path.is_absolute() for path in path_arguments):
        raise BuildError("R4W1-B isolated execution requires repo-relative paths")
    reexecuted = reexec_in_private_repo_namespace(
        root,
        script=Path(__file__),
        arguments=sys.argv[1:],
        compatibility_work_tree=args.work_tree,
    )
    if reexecuted is not None:
        return reexecuted
    private_namespace = inspect_private_namespace(root)
    if not private_namespace["verified"]:
        raise BuildError("R4W1-B private repository namespace is not verified")
    recorded_root = Path(private_namespace["recorded_repo"])
    work_tree = base.resolve(root, args.work_tree)
    clang_repo = base.resolve(root, args.clang_repo)
    result_dir = base.resolve(root, args.result_dir)
    source_patch = base.resolve(root, args.patch)
    create_exclusive_result_dir(result_dir)
    clean_output = inspect_clean_output_precondition(work_tree)
    if not clean_output["verified"]:
        raise BuildError(f"clean build requires absent output tree: {clean_output['path']}")

    host_tools = base.prepare_host_tool_overrides(work_tree)
    source_overlay = base.run_overlay_audit(
        root,
        work_tree,
        result_dir,
        base.resolve(root, args.base_archive),
        base.resolve(root, args.delta_archive),
        base.resolve(root, args.overlay_audit),
    )
    timestamp = base.inspect_timestamp_control(work_tree)
    kmi_path_control = inspect_kmi_path_control(work_tree)
    kernel_debug_control = inspect_kernel_debug_control(work_tree)
    vdso_debug_control = inspect_vdso_debug_control(work_tree)
    stock = base.inspect_stock_baseline(base.resolve(root, args.stock_baseline))
    r4_contract = patch_check.run_check(work_tree, source_patch)
    preflight = base.preflight(
        root,
        work_tree,
        clang_repo,
        lto="full",
        jobs=args.jobs,
        source_overlay=source_overlay,
        host_tool_overrides=host_tools,
        timestamp_control=timestamp,
        stock_baseline=stock,
    )
    preflight["build_allowed"] = (
        preflight["build_allowed"]
        and clean_output["verified"]
        and kmi_path_control["verified"]
        and kernel_debug_control["verified"]
        and vdso_debug_control["verified"]
    )
    preflight["provenance"]["kmi_path_control"] = kmi_path_control
    preflight["provenance"]["kernel_debug_control"] = kernel_debug_control
    preflight["provenance"]["vdso_debug_control"] = vdso_debug_control
    preflight["provenance"]["clean_output_precondition"] = clean_output
    preflight["provenance"]["private_namespace"] = private_namespace
    result: dict[str, Any] = {
        **preflight,
        "schema": SCHEMA,
        "base_schema": preflight["schema"],
        "r4w1b_patch_contract": r4_contract,
        "mode": args.mode,
        "result_directory": {
            "path": str(result_dir),
            "created_exclusively": True,
        },
        "stock_equivalent_claim": False,
        "safety": {
            "host_only": True,
            "device_contact": False,
            "boot_image_packaging": False,
            "flash": False,
            "partition_write": False,
            "live_authorized": False,
        },
    }
    base.write_json(
        result_dir / "preflight.json",
        rebase_recorded_paths(
            result,
            observed_root=root,
            recorded_root=recorded_root,
            embedded=True,
        ),
    )
    if args.mode == "preflight":
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if preflight["build_allowed"] else 2
    if not preflight["build_allowed"]:
        raise BuildError("build refused: clean-source preflight did not pass")

    with create_exclusive_output_root(
        work_tree, expected_work_tree=clean_output
    ) as output_root_runtime:
        bound_work_tree = Path(output_root_runtime["_work_tree_fd_path"])
        with apply_checked_patch(bound_work_tree, source_patch) as source_delta:
            incremental = base.prepare_incremental_dist_refresh(bound_work_tree)
            if incremental.get("removed"):
                raise BuildError("clean build unexpectedly removed incremental outputs")
            incremental["clean_output_tree"] = output_root_runtime["empty_at_creation"]
            environment = base.build_environment(
                work_tree, lto="full", jobs=args.jobs, clang_repo=clang_repo
            )
            environment = {
                key: value.replace(str(work_tree), str(bound_work_tree))
                for key, value in environment.items()
            }
            command = ["./kernel_platform/build/android/prepare_vendor.sh", "sec", "gki"]
            time_file = result_dir / "time.txt"
            with apply_kmi_path_control(
                bound_work_tree, kmi_path_control
            ) as kmi_path_runtime:
                with apply_kernel_debug_control(
                    bound_work_tree, kernel_debug_control
                ) as kernel_debug_runtime:
                    with apply_vdso_debug_control(
                        bound_work_tree, vdso_debug_control
                    ) as vdso_debug_runtime:
                        with base.apply_timestamp_control(
                            bound_work_tree, timestamp
                        ) as timestamp_runtime:
                            with (result_dir / "stdout.log").open(
                                "w", encoding="utf-8"
                            ) as stdout_log, (result_dir / "stderr.log").open(
                                "w", encoding="utf-8"
                            ) as stderr_log:
                                completed = subprocess.run(
                                    [
                                        "/usr/bin/time",
                                        "-v",
                                        "-o",
                                        str(time_file),
                                        *command,
                                    ],
                                    cwd=bound_work_tree,
                                    env=environment,
                                    text=True,
                                    stdout=stdout_log,
                                    stderr=stderr_log,
                                    check=False,
                                )
            providers = (
                base.run_provider_module_closure(
                    bound_work_tree, environment, result_dir, jobs=args.jobs
                )
                if completed.returncode == 0
                else {"providers": [], "verified": False, "skipped": True}
            )
        outputs = rebase_recorded_paths(
            base.collect_outputs(bound_work_tree),
            observed_root=bound_work_tree,
            recorded_root=work_tree,
        )
        output_gate = base.output_gate(outputs)
        modules = rebase_recorded_paths(
            base.collect_generated_modules(bound_work_tree),
            observed_root=bound_work_tree,
            recorded_root=work_tree,
        )
        module_gate = {
            "generated_module_count": len(modules),
            "verified": bool(modules),
        }
        banner_gate = rebase_recorded_paths(
            base.kernel_banner_gate(
                bound_work_tree, expected_banner=stock["expected_banner"]
            ),
            observed_root=bound_work_tree,
            recorded_root=work_tree,
        )
        witness_gate = rebase_recorded_paths(
            witness_output_gate(bound_work_tree),
            observed_root=bound_work_tree,
            recorded_root=work_tree,
        )
        host_packaging = rebase_recorded_paths(
            collect_host_packaging_outputs(bound_work_tree),
            observed_root=bound_work_tree,
            recorded_root=work_tree,
        )
        symvers_files = rebase_recorded_paths(
            collect_bound_symvers(bound_work_tree),
            observed_root=bound_work_tree,
            recorded_root=work_tree,
        )
    output_root_runtime.pop("_work_tree_fd_path", None)
    base.write_json(
        result_dir / "source-delta.json",
        rebase_recorded_paths(
            source_delta,
            observed_root=root,
            recorded_root=recorded_root,
            embedded=True,
        ),
    )
    effective = completed.returncode
    gates = (
        (source_delta.get("verified", False), 8),
        (
            clean_output["verified"]
            and output_root_runtime.get("verified") is True
            and not incremental.get("removed")
            and incremental.get("clean_output_tree") is True,
            9,
        ),
        (providers.get("verified", False), 5),
        (output_gate["verified"], 3),
        (module_gate["verified"], 4),
        (banner_gate["verified"], 6),
        (witness_gate["verified"], 7),
    )
    if effective == 0:
        for passed, code in gates:
            if not passed:
                effective = code
                break
    result.update(
        {
            "mode": "build",
            "build_command": command,
            "build_command_returncode": completed.returncode,
            "returncode": effective,
            "source_delta": source_delta,
            "clean_output_precondition": clean_output,
            "exclusive_output_root": output_root_runtime,
            "outputs": outputs,
            "output_gate": output_gate,
            "generated_modules": modules,
            "module_gate": module_gate,
            "kernel_banner_gate": banner_gate,
            "witness_output_gate": witness_gate,
            "host_packaging_outputs": host_packaging,
            "timestamp_control_runtime": timestamp_runtime,
            "kmi_path_control_runtime": kmi_path_runtime,
            "kernel_debug_control_runtime": kernel_debug_runtime,
            "vdso_debug_control_runtime": vdso_debug_runtime,
            "provider_module_closure": providers,
            "symvers_files": symvers_files,
            "incremental_dist_refresh": incremental,
            "r4w1b_build_pass": effective == 0,
            "interpretation": (
                "host build only; generated packaging side outputs are not promoted "
                "as live candidates; R4 static KMI audit, reproducibility, artifact "
                "review, and a fresh live exception remain required"
            ),
        }
    )
    result["safety"].update(
        {
            "boot_image_packaging": host_packaging["generated"],
            "packaging_outputs_promoted": False,
            "flash": False,
            "partition_write": False,
            "live_authorized": False,
        }
    )
    base.write_json(
        result_dir / "result.json",
        rebase_recorded_paths(
            result,
            observed_root=root,
            recorded_root=recorded_root,
            embedded=True,
        ),
    )
    print(
        json.dumps(
            {
                "result": "pass" if effective == 0 else "fail",
                "returncode": effective,
                "result_dir": base.display_path(root, result_dir),
                "image_size": witness_gate.get("image_size"),
                "slot_slack": witness_gate.get("pre_ramdisk_slack_remaining"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return effective


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, patch_check.CheckError, base.BuildError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
