#!/usr/bin/env python3
"""Run the fail-closed R4W1-B static compatibility audit host-only."""

from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import s22plus_fyg8_kernel_r2_audit as r2  # noqa: E402
import s22plus_fyg8_r4w1b_elf_audit as elf_audit  # noqa: E402
import s22plus_fyg8_r4w1b_build as r4w1b_build  # noqa: E402
import s22plus_fyg8_r4w1b_patch_check as patch_check  # noqa: E402


SCHEMA = "s22plus_fyg8_r4w1b_static_audit_v1"
TARGET = r2.TARGET
VERDICT = "PASS_R4W1B_STATIC_COMPATIBILITY"
WITNESS_CONFIG = "CONFIG_S22PLUS_FYG8_RETAINED_WITNESS"
BUILD_PASS_FIELD = "r4w1b_build_pass"
PATCH_CONTRACT_FIELD = "r4w1b_patch_contract"
STATIC_PASS_FIELD = "r4w1b_static_pass"
BLOCKED_VERDICT = "BLOCKED_R4W1B_STATIC_COMPATIBILITY"
AUDIT_LABEL = "R4W1-B"
MARKER_FAMILY = r4w1b_build.R4W1B_MARKER_FAMILY
HISTORICAL_MARKER_FAMILY = r4w1b_build.HISTORICAL_R4W1_MARKER_FAMILY
DEFAULT_BASELINE_SYMVERS = Path(
    "workspace/private/outputs/s22plus_fyg8_r4w1/"
    "remote-g-artifacts-final/vmlinux.symvers"
)
DEFAULT_BASELINE_ABI = DEFAULT_BASELINE_SYMVERS.with_name("abi.xml")
BASELINE_SYMVERS_SHA256 = (
    "fd75413401617a427ddf6c264d0ae4f5452b46cde02b4575b9af09f19601ca19"
)
BASELINE_ABI_SHA256 = (
    "3660c592e1884ab323816c09a3abd197744c8b2f78aed890b02c3e69dbc1c55c"
)
PINNED_BASELINE_INPUTS = {
    "baseline_symvers": (BASELINE_SYMVERS_SHA256, 439_646),
    "baseline_abi": (BASELINE_ABI_SHA256, 12_787_205),
    "stock_baseline": (
        "3041f6a50c5ac77631c747dc3d21e5fd0ad68a520ffc9a2052b1c0b5976db092",
        3_257,
    ),
    "stock_config": (
        "99352a4f8db49814330c9d2c28038fafbbd1dadbe1fef3082c6d7e2614c2dbf1",
        185_351,
    ),
    "requirements_0": (
        "9be63bf9d2086d0823cc2b87cc2412b34f3d44394444c0cb693a5b1edf5a6e86",
        1_429_332,
    ),
    "requirements_1": (
        "870d7cf4d077c7bb98bfe42d5ef24b5765136a7166c4850b6031168ce78dd00e",
        272_145,
    ),
    "module_map": (
        "f18e692511f4f37387f916be9266bd6c744eac650fad3455d8fef139257dfc33",
        3_682,
    ),
    "corpus_layout": (
        "89d97fd7215ca1e830a983de61779baa13d4ecba3573bc2778ba98c5c26bca3e",
        18_610,
    ),
}
FIPS_SOURCE_INPUTS = {
    "fips_crypto_integrity": (
        Path("kernel_platform/common/scripts/crypto/fips_crypto_integrity.py"),
        "0203f283f11032800c633a9fee74cce7c2f1b1b9e67a71d32db03db1f86c27a3",
        3_024,
    ),
    "fips_integrity_routine": (
        Path("kernel_platform/common/scripts/crypto/IntegrityRoutine.py"),
        "c13576b054e913cd1318ffb15511922e36b79adcceaa57b4a20cce5181d72c36",
        23_189,
    ),
    "fips_utils": (
        Path("kernel_platform/common/scripts/crypto/Utils.py"),
        "00c8c9cc0415754b952b911ea82aca395f7afbe8315cf0e8ff8f91f6ec3a845d",
        3_541,
    ),
    "fips_elf": (
        Path("kernel_platform/common/scripts/crypto/ELF.py"),
        "a80c592192da19c0b6aeb06c4f0938802094de11add312bf63d1a09423dc325a",
        29_650,
    ),
    "link_vmlinux": (
        Path("kernel_platform/common/scripts/link-vmlinux.sh"),
        "91b2fed51d66d3d607539578448b0b3aab0fb7cfba693212d24189ce6b1c111e",
        11_889,
    ),
    "fips140_out": (
        Path("kernel_platform/common/crypto/fips140_out.c"),
        "00a2f5ed0e0f777fe6efd6ca56c0ec7aabd5e907aa7f95546cb95a525a057f34",
        266,
    ),
}
FIPS_RUNTIME_SCRIPT_NAMES = (
    "fips_crypto_integrity",
    "fips_integrity_routine",
    "fips_utils",
    "fips_elf",
)
FIPS_CRYPTO_OBJECTS = (
    "fips140_integrity.o", "fips140_post.o", "fips140_test.o",
    "fips140_test_tv.o", "ghash-generic.o", "api.o", "cipher.o",
    "compress.o", "memneq.o", "proc.o", "algapi.o", "scatterwalk.o",
    "aead.o", "skcipher.o", "seqiv.o", "echainiv.o", "ahash.o",
    "shash.o", "algboss.o", "testmgr.o", "hmac.o", "sha1_generic.o",
    "sha256_generic.o", "sha512_generic.o", "ecb.o", "cbc.o", "ctr.o",
    "gcm.o", "aes_generic.o", "authenc.o", "authencesn.o", "rng.o",
    "drbg.o", "jitterentropy.o", "jitterentropy-kcapi.o",
    "../lib/crypto/aes.o", "../lib/crypto/sha256.o",
)
FIPS_ARM64_CRYPTO_OBJECTS = (
    "aes-ce-core.o", "aes-ce-glue.o", "aes-ce.o", "aes-glue-ce.o",
    "sha256-core.o", "sha256-glue.o", "sha2-ce-core.o",
    "sha2-ce-glue.o", "sha1-ce-glue.o", "sha1-ce-core.o",
)
ARM64_IMAGE_HEADER = bytes.fromhex(
    "4d5a0091ff7f891400000000000000000000a502000000000a000000000000000000000000000000d011950200000000000000000000000041524d6440000000"
)
ARM64_IMAGE_HEADER_SHA256 = (
    "8ff5cbe619baa8ce3e447baa1d8da13769bdd75eb4363b7e348e4a611450e442"
)
ARM64_IMAGE_HEADER_STRUCT = struct.Struct("<IIQQQQQQII")
CRITICAL_SECURITY_CONFIGS = (
    "CONFIG_UH",
    "CONFIG_RKP",
    "CONFIG_KDP",
    "CONFIG_SECURITY_DEFEX",
    "CONFIG_FIVE",
    "CONFIG_PROCA",
    "CONFIG_CRYPTO_FIPS",
    "CONFIG_CRYPTO_FIPS140",
)
DEFAULT_OUT = Path(
    "workspace/private/outputs/s22plus_fyg8_r4w1b_static_audit/result.json"
)


class AuditError(ValueError):
    pass


def file_identity(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "realpath": None,
        "exists": False,
        "symlink": False,
        "indirect": False,
        "regular": False,
        "size": None,
        "sha256": None,
        "device": None,
        "inode": None,
        "mode": None,
        "stable_during_read": False,
    }
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    absolute = Path(os.path.abspath(path))
    try:
        path_metadata = path.lstat()
        result["exists"] = True
        result["symlink"] = stat.S_ISLNK(path_metadata.st_mode)
        result["indirect"] = (
            result["symlink"] or absolute.parent.resolve() != absolute.parent
        )
    except OSError:
        result["indirect"] = absolute.parent.resolve() != absolute.parent
        return result
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return result
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            return result
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        stable = (
            before.st_dev == after.st_dev
            and before.st_ino == after.st_ino
            and before.st_size == after.st_size
            and before.st_mtime_ns == after.st_mtime_ns
            and before.st_ctime_ns == after.st_ctime_ns
        )
        result.update(
            {
                "realpath": str(path.resolve(strict=True)),
                "indirect": path.resolve(strict=True) != absolute,
                "regular": stat.S_ISREG(before.st_mode),
                "size": before.st_size,
                "sha256": digest.hexdigest(),
                "device": before.st_dev,
                "inode": before.st_ino,
                "mode": stat.S_IMODE(before.st_mode),
                "stable_during_read": stable,
            }
        )
        return result
    finally:
        os.close(descriptor)


def check_pinned_identity(
    path: Path, expected_sha256: str, expected_size: int
) -> dict[str, Any]:
    result = file_identity(path)
    result.update(
        {
            "expected_sha256": expected_sha256,
            "expected_size": expected_size,
        }
    )
    result["verified"] = (
        result["regular"]
        and result["stable_during_read"]
        and not result["indirect"]
        and result["sha256"] == expected_sha256
        and result["size"] == expected_size
    )
    return result


def _fd_matches_file_identity(opened: os.stat_result, expected: dict[str, Any]) -> bool:
    return (
        expected.get("regular") is True
        and stat.S_ISREG(opened.st_mode)
        and opened.st_dev == expected.get("device")
        and opened.st_ino == expected.get("inode")
        and opened.st_size == expected.get("size")
        and stat.S_IMODE(opened.st_mode) == expected.get("mode")
    )


def _fd_stability_tuple(opened: os.stat_result, *, mutable_content: bool) -> tuple[int, ...]:
    common = (
        opened.st_dev,
        opened.st_ino,
        opened.st_mode,
        opened.st_size,
    )
    if mutable_content:
        return common
    return common + (opened.st_mtime_ns, opened.st_ctime_ns)


@contextmanager
def bind_fips_execution_snapshot(
    snapshot: Path,
    *,
    script_name: str,
    python_path: Path,
    snapshot_identities: dict[str, dict[str, Any]],
    python_identity: dict[str, Any],
) -> Iterator[tuple[dict[str, str], dict[str, Any]]]:
    """Bind every FIPS execution input to FDs owned by this audit process."""

    directory_flags = os.O_RDONLY | os.O_DIRECTORY
    file_flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
        file_flags |= os.O_NOFOLLOW
    descriptors: dict[str, int] = {}
    opened_stats: dict[str, os.stat_result] = {}
    mutable_names = {"vmlinux"}

    def open_directory(
        name: str, path: Path | str, *, dir_fd: int | None = None
    ) -> int:
        lexical = (
            os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
            if dir_fd is not None
            else os.stat(path, follow_symlinks=False)
        )
        descriptor = os.open(path, directory_flags, dir_fd=dir_fd)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or opened.st_dev != lexical.st_dev
            or opened.st_ino != lexical.st_ino
        ):
            os.close(descriptor)
            raise AuditError(f"FIPS snapshot directory changed before FD bind: {name}")
        descriptors[name] = descriptor
        opened_stats[name] = opened
        return descriptor

    def open_file(
        name: str,
        path: Path | str,
        expected: dict[str, Any],
        *,
        dir_fd: int | None = None,
        writable: bool = False,
    ) -> int:
        flags = file_flags | (os.O_RDWR if writable else 0)
        if writable:
            flags &= ~os.O_RDONLY
        descriptor = os.open(path, flags, dir_fd=dir_fd)
        opened = os.fstat(descriptor)
        if not _fd_matches_file_identity(opened, expected):
            os.close(descriptor)
            raise AuditError(f"FIPS snapshot file changed before FD bind: {name}")
        descriptors[name] = descriptor
        opened_stats[name] = opened
        return descriptor

    runtime: dict[str, Any] = {
        "access": "held-fds-via-parent-procfs",
        "opened_verified": False,
        "procfs_paths_verified": False,
        "stable": False,
    }
    try:
        root_fd = open_directory("snapshot_root", snapshot)
        scripts_fd = open_directory("scripts", "scripts", dir_fd=root_fd)
        objects_fd = open_directory("objects", "objects", dir_fd=root_fd)
        tools_fd = open_directory("tools", "bin", dir_fd=root_fd)
        libraries_fd = open_directory("libraries", "lib64", dir_fd=root_fd)
        crypto_fd = open_directory("crypto_objects", "crypto", dir_fd=objects_fd)
        arm64_crypto_fd = open_directory(
            "arm64_crypto_objects", "arch/arm64/crypto", dir_fd=objects_fd
        )
        open_file(
            "script",
            script_name,
            snapshot_identities["script_fips_crypto_integrity"],
            dir_fd=scripts_fd,
        )
        open_file(
            "vmlinux",
            "vmlinux",
            snapshot_identities["vmlinux"],
            dir_fd=root_fd,
            writable=True,
        )
        open_file(
            "llvm_readelf",
            "llvm-readelf",
            snapshot_identities["tool_llvm-readelf"],
            dir_fd=tools_fd,
        )
        open_file(
            "llvm_nm",
            "llvm-nm",
            snapshot_identities["tool_llvm-nm"],
            dir_fd=tools_fd,
        )
        open_file(
            "libcxx",
            "libc++.so.1",
            snapshot_identities["tool_libcxx"],
            dir_fd=libraries_fd,
        )
        open_file("python", python_path, python_identity)

        proc_root = f"/proc/{os.getpid()}/fd"
        bound_paths = {
            name: f"{proc_root}/{descriptor}"
            for name, descriptor in descriptors.items()
        }
        # The Samsung generator normalizes crypto/../lib/crypto lexically.
        # Keep that traversal below the held objects-root FD.
        bound_paths["crypto_objects"] = f"{bound_paths['objects']}/crypto"
        bound_paths["arm64_crypto_objects"] = (
            f"{bound_paths['objects']}/arch/arm64/crypto"
        )
        runtime["opened_verified"] = True
        runtime["bound_input_count"] = len(bound_paths)
        runtime["procfs_paths_verified"] = all(
            os.stat(bound_paths[name]).st_dev == opened_stats[name].st_dev
            and os.stat(bound_paths[name]).st_ino == opened_stats[name].st_ino
            for name in bound_paths
        )
        if not runtime["procfs_paths_verified"]:
            raise AuditError("FIPS parent-procfs FD binding is not exact")
        yield bound_paths, runtime
    finally:
        runtime["stable"] = bool(descriptors) and all(
            _fd_stability_tuple(
                os.fstat(descriptor), mutable_content=name in mutable_names
            )
            == _fd_stability_tuple(
                opened_stats[name], mutable_content=name in mutable_names
            )
            for name, descriptor in descriptors.items()
        )
        for descriptor in reversed(tuple(descriptors.values())):
            os.close(descriptor)


@contextmanager
def watch_immutable_paths(paths: list[Path]) -> Iterator[dict[str, Any]]:
    if not paths:
        raise AuditError("immutable-path watch requires at least one path")
    expanded_paths = set(paths)
    for path in paths:
        ancestor = path.parent
        while ancestor != ancestor.parent:
            expanded_paths.add(ancestor)
            ancestor = ancestor.parent
    targets_by_parent: dict[Path, set[str]] = {}
    for path in expanded_paths:
        targets_by_parent.setdefault(path.parent, set()).add(path.name)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.inotify_init1.argtypes = [ctypes.c_int]
    libc.inotify_init1.restype = ctypes.c_int
    descriptor = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    if descriptor < 0:
        raise AuditError(f"inotify_init1 failed: errno={ctypes.get_errno()}")
    add_watch = libc.inotify_add_watch
    add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    add_watch.restype = ctypes.c_int
    mask = (
        0x00000002
        | 0x00000004
        | 0x00000008
        | 0x00000040
        | 0x00000080
        | 0x00000100
        | 0x00000200
        | 0x00000400
        | 0x00000800
    )
    watched: dict[int, dict[str, Any]] = {}
    try:
        for parent, names in targets_by_parent.items():
            watch = add_watch(descriptor, os.fsencode(parent), mask)
            if watch < 0:
                raise AuditError(
                    f"inotify_add_watch failed for {parent}: errno={ctypes.get_errno()}"
                )
            watched[watch] = {"parent": str(parent), "names": names}
        runtime: dict[str, Any] = {
            "watched_path_count": len(paths),
            "watched_path_and_ancestor_count": len(expanded_paths),
            "watched_directory_count": len(watched),
            "events": [],
            "verified": False,
        }
        yield runtime
    finally:
        try:
            event_header = struct.Struct("iIII")
            events: list[dict[str, Any]] = []
            while True:
                try:
                    data = os.read(descriptor, 64 * 1024)
                except BlockingIOError:
                    break
                if not data:
                    break
                offset = 0
                while offset + event_header.size <= len(data):
                    watch, event_mask, cookie, name_size = event_header.unpack_from(
                        data, offset
                    )
                    offset += event_header.size
                    raw_name = data[offset : offset + name_size]
                    offset += name_size
                    event_name = os.fsdecode(raw_name.split(b"\0", 1)[0])
                    row = watched.get(watch)
                    if (
                        event_mask & (0x00004000 | 0x00000400 | 0x00000800)
                        or row is None
                        or event_name in row["names"]
                    ):
                        events.append(
                            {
                                "watch": watch,
                                "mask": event_mask,
                                "cookie": cookie,
                                "name": event_name,
                                "parent": row["parent"] if row else None,
                            }
                        )
            if "runtime" in locals():
                runtime["events"] = events
                runtime["verified"] = not events
        finally:
            os.close(descriptor)


def check_arm64_image_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as source:
        header = source.read(ARM64_IMAGE_HEADER_STRUCT.size)
    fields = (
        ARM64_IMAGE_HEADER_STRUCT.unpack(header)
        if len(header) == ARM64_IMAGE_HEADER_STRUCT.size
        else None
    )
    result = {
        "header_size": len(header),
        "header_hex": header.hex(),
        "header_sha256": hashlib.sha256(header).hexdigest(),
        "expected_header_sha256": ARM64_IMAGE_HEADER_SHA256,
        "code0": fields[0] if fields else None,
        "code1": fields[1] if fields else None,
        "text_offset": fields[2] if fields else None,
        "image_size_field": fields[3] if fields else None,
        "flags": fields[4] if fields else None,
        "magic": fields[8] if fields else None,
        "reserved5": fields[9] if fields else None,
    }
    result["verified"] = (
        header == ARM64_IMAGE_HEADER
        and result["header_sha256"] == ARM64_IMAGE_HEADER_SHA256
        and result["magic"] == 0x644D5241
    )
    return result


def extract_fips_fields(path: Path) -> dict[str, Any]:
    names = {
        "builtime_crypto_hmac",
        "integrity_crypto_addrs",
        "crypto_buildtime_address",
    }
    with elf_audit.Elf64(path) as elf:
        symbols = elf.symbols(names)
        return {
            name: {
                "size": len(data := elf.symbol_bytes(symbols[name])),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name in sorted(names)
        }


def collect_fips_runtime_inputs(
    work_tree: Path, *, effective_path: str
) -> dict[str, Path]:
    if not effective_path:
        raise AuditError("missing pinned effective PATH for FIPS oracle")
    objtree = work_tree / "out/msm-waipio-waipio-gki/gki_kernel/common"
    generator = work_tree / FIPS_SOURCE_INPUTS["fips_crypto_integrity"][0]
    generator_pin = FIPS_SOURCE_INPUTS["fips_crypto_integrity"]
    if not check_pinned_identity(generator, generator_pin[1], generator_pin[2])["verified"]:
        raise AuditError("FIPS generator source is not the exact direct pin")
    parsed = ast.parse(generator.read_text(encoding="utf-8"), filename=str(generator))
    declared: dict[str, tuple[str, ...]] = {}
    for node in parsed.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in {
            "list_obj_files_skc",
            "list_obj_files_skc_ce",
        }:
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise AuditError(f"invalid FIPS object declaration: {target.id}")
        declared[target.id] = tuple(value)
    if declared != {
        "list_obj_files_skc": FIPS_CRYPTO_OBJECTS,
        "list_obj_files_skc_ce": FIPS_ARM64_CRYPTO_OBJECTS,
    }:
        raise AuditError("pinned FIPS object inventory differs from generator source")
    paths: dict[str, Path] = {
        f"fips_runtime_script_{name}": work_tree / FIPS_SOURCE_INPUTS[name][0]
        for name in FIPS_RUNTIME_SCRIPT_NAMES
    }
    for index, relative in enumerate(FIPS_CRYPTO_OBJECTS):
        paths[f"fips_crypto_object_{index:02d}"] = Path(
            os.path.normpath(objtree / "crypto" / relative)
        )
    for index, relative in enumerate(FIPS_ARM64_CRYPTO_OBJECTS):
        paths[f"fips_arm64_crypto_object_{index:02d}"] = Path(
            os.path.normpath(objtree / "arch/arm64/crypto" / relative)
        )
    for name in ("llvm-readelf", "llvm-nm"):
        alias = shutil.which(name, path=effective_path)
        if alias is None:
            raise AuditError(f"pinned effective PATH has no {name}")
        paths[f"fips_tool_{name}"] = Path(alias).resolve(strict=True)
    toolchain_root = paths["fips_tool_llvm-readelf"].parent.parent
    paths["fips_tool_libcxx"] = (toolchain_root / "lib64/libc++.so.1").resolve(
        strict=True
    )
    paths["fips_python_executable"] = Path(sys.executable).resolve(strict=True)
    return paths


def regenerate_fips_oracle(
    work_tree: Path,
    vmlinux: Path,
    *,
    effective_path: str,
    runtime_inputs: dict[str, Path] | None = None,
) -> dict[str, Any]:
    namespace = r4w1b_build.inspect_private_namespace(r2.repo_root())
    if not namespace["verified"]:
        return {
            "verified": False,
            "reason": "FIPS regeneration requires the private repository namespace",
            "private_namespace": namespace,
        }
    objtree = work_tree / "out/msm-waipio-waipio-gki/gki_kernel/common"
    runtime_inputs = runtime_inputs or collect_fips_runtime_inputs(
        work_tree, effective_path=effective_path
    )
    source_inputs = {"vmlinux": vmlinux, **runtime_inputs}
    source_before = {name: file_identity(path) for name, path in source_inputs.items()}
    source_inputs_valid = all(
        (
            (row["regular"] and row["stable_during_read"] and not row["indirect"])
            if "_object_" not in input_name
            else (row["regular"] and row["stable_during_read"] and not row["indirect"])
            or (not row["exists"] and not row["indirect"])
        )
        for input_name, row in source_before.items()
    )
    if not source_inputs_valid:
        return {
            "verified": False,
            "reason": "missing-unstable-or-indirect-generator-input",
            "source_inputs_before": source_before,
        }
    original_sha256 = r2.sha256_file(vmlinux)
    original_fields = extract_fips_fields(vmlinux)
    with tempfile.TemporaryDirectory(prefix="s22-r4w1b-fips-") as name:
        snapshot = Path(name)
        scripts = snapshot / "scripts"
        objects = snapshot / "objects"
        tools = snapshot / "bin"
        libraries = snapshot / "lib64"
        scripts.mkdir()
        objects.mkdir()
        tools.mkdir()
        libraries.mkdir()
        for source_name in FIPS_RUNTIME_SCRIPT_NAMES:
            source = runtime_inputs[f"fips_runtime_script_{source_name}"]
            shutil.copy2(source, scripts / source.name)
        for key, source in runtime_inputs.items():
            if not key.startswith("fips_") or "_object_" not in key:
                continue
            if not source_before[key]["regular"]:
                continue
            relative = source.relative_to(objtree)
            destination = objects / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        for tool_name in ("llvm-readelf", "llvm-nm"):
            target = runtime_inputs[f"fips_tool_{tool_name}"]
            shutil.copy2(target, tools / tool_name)
        shutil.copy2(runtime_inputs["fips_tool_libcxx"], libraries / "libc++.so.1")
        regenerated = snapshot / "vmlinux"
        shutil.copyfile(vmlinux, regenerated)
        snapshot_paths = {
            "vmlinux": regenerated,
            **{
                f"script_{source_name}": scripts
                / runtime_inputs[f"fips_runtime_script_{source_name}"].name
                for source_name in FIPS_RUNTIME_SCRIPT_NAMES
            },
            **{
                key: objects / source.relative_to(objtree)
                for key, source in runtime_inputs.items()
                if key.startswith("fips_") and "_object_" in key
                and source_before[key]["regular"]
            },
            "tool_llvm-readelf": tools / "llvm-readelf",
            "tool_llvm-nm": tools / "llvm-nm",
            "tool_libcxx": libraries / "libc++.so.1",
        }
        snapshot_identities = {
            snapshot_name: file_identity(path)
            for snapshot_name, path in snapshot_paths.items()
        }
        snapshot_verified = all(
            row["regular"] and row["stable_during_read"] and not row["indirect"]
            for row in snapshot_identities.values()
        )
        absent_snapshot_paths = {
            key: objects / source.relative_to(objtree)
            for key, source in runtime_inputs.items()
            if key.startswith("fips_")
            and "_object_" in key
            and not source_before[key]["regular"]
        }
        for path in absent_snapshot_paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_absence_verified = all(
            not path.exists() and not path.is_symlink()
            for path in absent_snapshot_paths.values()
        )
        snapshot_source_map = {
            "vmlinux": "vmlinux",
            **{
                f"fips_runtime_script_{source_name}": f"script_{source_name}"
                for source_name in FIPS_RUNTIME_SCRIPT_NAMES
            },
            **{
                key: key
                for key in runtime_inputs
                if key.startswith("fips_") and "_object_" in key
                and source_before[key]["regular"]
            },
            "fips_tool_llvm-readelf": "tool_llvm-readelf",
            "fips_tool_llvm-nm": "tool_llvm-nm",
            "fips_tool_libcxx": "tool_libcxx",
        }
        snapshot_source_bindings = {
            source_name: {
                "snapshot_name": snapshot_name,
                "source_sha256": source_before[source_name]["sha256"],
                "snapshot_sha256": snapshot_identities[snapshot_name]["sha256"],
                "source_size": source_before[source_name]["size"],
                "snapshot_size": snapshot_identities[snapshot_name]["size"],
                "verified": (
                    source_before[source_name]["sha256"]
                    == snapshot_identities[snapshot_name]["sha256"]
                    and source_before[source_name]["size"]
                    == snapshot_identities[snapshot_name]["size"]
                ),
            }
            for source_name, snapshot_name in snapshot_source_map.items()
        }
        snapshot_source_bindings_verified = all(
            row["verified"] for row in snapshot_source_bindings.values()
        )
        script = scripts / runtime_inputs["fips_runtime_script_fips_crypto_integrity"].name
        crypto_objects = objects / "crypto"
        arm64_crypto_objects = objects / "arch/arm64/crypto"
        immutable_paths = [
            path for name, path in snapshot_paths.items() if name != "vmlinux"
        ] + list(absent_snapshot_paths.values()) + [
            scripts,
            objects,
            tools,
            libraries,
        ]
        with bind_fips_execution_snapshot(
            snapshot,
            script_name=script.name,
            python_path=runtime_inputs["fips_python_executable"],
            snapshot_identities=snapshot_identities,
            python_identity=source_before["fips_python_executable"],
        ) as (bound_paths, snapshot_fd_runtime):
            environment = {
                "PATH": bound_paths["tools"],
                "LD_LIBRARY_PATH": bound_paths["libraries"],
                "PYTHONPATH": bound_paths["scripts"],
                "LC_ALL": "C",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            with watch_immutable_paths(immutable_paths) as snapshot_mutation_watch:
                snapshot_armed = {
                    snapshot_name: file_identity(path)
                    for snapshot_name, path in snapshot_paths.items()
                }
                snapshot_armed_exact = snapshot_armed == snapshot_identities
                if not snapshot_armed_exact:
                    raise AuditError("FIPS snapshot changed before execution")
                completed = subprocess.run(
                    [
                        bound_paths["python"],
                        bound_paths["script"],
                        bound_paths["vmlinux"],
                        bound_paths["crypto_objects"],
                        bound_paths["arm64_crypto_objects"],
                    ],
                    cwd=bound_paths["scripts"],
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300,
                    check=False,
                )
                regenerated_sha256 = r2.sha256_file(Path(bound_paths["vmlinux"]))
                regenerated_fields = extract_fips_fields(Path(bound_paths["vmlinux"]))
                snapshot_after = {
                    snapshot_name: file_identity(path)
                    for snapshot_name, path in snapshot_paths.items()
                }
                snapshot_stable = snapshot_after == snapshot_identities
                snapshot_absence_stable = snapshot_absence_verified and all(
                    not path.exists() and not path.is_symlink()
                    for path in absent_snapshot_paths.values()
                )
    source_after = {name: file_identity(path) for name, path in source_inputs.items()}
    source_inputs_stable = source_after == source_before
    result = {
        "command": [
            "<held-python-fd>",
            str(script),
            "<exclusive-vmlinux-copy>",
            str(crypto_objects),
            str(arm64_crypto_objects),
        ],
        "returncode": completed.returncode,
        "stdout_size": len(completed.stdout.encode("utf-8")),
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_size": len(completed.stderr.encode("utf-8")),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
        "stderr_tail": completed.stderr[-4000:],
        "stderr_has_fatal_marker": any(
            marker in completed.stderr
            for marker in ("Traceback (most recent call last)", "ERROR:", "Error:")
        ),
        "completion_count": completed.stdout.count(
            "FIPS integrity procedure has been finished for crypto"
        ),
        "original_vmlinux_sha256": original_sha256,
        "regenerated_vmlinux_sha256": regenerated_sha256,
        "whole_vmlinux_unchanged": regenerated_sha256 == original_sha256,
        "original_fields": original_fields,
        "regenerated_fields": regenerated_fields,
        "fields_unchanged": original_fields == regenerated_fields,
        "selected_parser_count": completed.stdout.count(
            "Used parsers is:  llvm-readelf llvm-nm"
        ),
        "source_inputs_before": source_before,
        "source_inputs_after": source_after,
        "source_inputs_stable": source_inputs_stable,
        "source_inputs_valid": source_inputs_valid,
        "snapshot_inputs": snapshot_identities,
        "snapshot_verified": snapshot_verified,
        "snapshot_stable": snapshot_stable,
        "snapshot_source_bindings": snapshot_source_bindings,
        "snapshot_source_bindings_verified": snapshot_source_bindings_verified,
        "snapshot_armed": snapshot_armed,
        "snapshot_armed_exact": snapshot_armed_exact,
        "snapshot_mutation_watch": snapshot_mutation_watch,
        "snapshot_absent_inputs": {
            key: str(path) for key, path in absent_snapshot_paths.items()
        },
        "snapshot_absence_stable": snapshot_absence_stable,
        "snapshot_fd_access": snapshot_fd_runtime["access"],
        "snapshot_fds_bound": (
            snapshot_fd_runtime["opened_verified"]
            and snapshot_fd_runtime["procfs_paths_verified"]
        ),
        "snapshot_fds_stable": snapshot_fd_runtime["stable"],
        "private_namespace": namespace,
    }
    result["verified"] = (
        result["returncode"] == 0
        and result["completion_count"] == 1
        and not result["stderr_has_fatal_marker"]
        and result["whole_vmlinux_unchanged"]
        and result["fields_unchanged"]
        and result["selected_parser_count"] == 1
        and result["source_inputs_stable"]
        and result["source_inputs_valid"]
        and result["snapshot_verified"]
        and result["snapshot_stable"]
        and result["snapshot_source_bindings_verified"]
        and result["snapshot_armed_exact"]
        and result["snapshot_mutation_watch"]["verified"]
        and result["snapshot_absence_stable"]
        and result["snapshot_fd_access"] == "held-fds-via-parent-procfs"
        and result["snapshot_fds_bound"]
        and result["snapshot_fds_stable"]
        and result["private_namespace"]["verified"]
    )
    return result


def compare_r4w1b_configs(stock_path: Path, generated_path: Path) -> dict[str, Any]:
    stock = r2.parse_config(stock_path)
    generated = r2.parse_config(generated_path)
    deltas = [
        {
            "key": key,
            "stock": stock.get(key, "<missing>"),
            "generated": generated.get(key, "<missing>"),
        }
        for key in sorted(set(stock) | set(generated))
        if stock.get(key) != generated.get(key)
    ]
    allowed = {r2.PATH_ONLY_CONFIG, WITNESS_CONFIG}
    unexpected = [delta for delta in deltas if delta["key"] not in allowed]
    witness = [delta for delta in deltas if delta["key"] == WITNESS_CONFIG]
    witness_exact = (
        len(witness) == 1
        and witness[0]["stock"] in ("<missing>", "n")
        and witness[0]["generated"] == "y"
    )
    path_deltas = [delta for delta in deltas if delta["key"] == r2.PATH_ONLY_CONFIG]
    path_only_valid = len(path_deltas) <= 1 and all(
        delta["stock"].startswith('"')
        and delta["stock"].endswith('"')
        and delta["generated"].startswith('"')
        and delta["generated"].endswith('"')
        for delta in path_deltas
    )
    full_lto = (
        generated.get("CONFIG_LTO_CLANG_FULL") == "y"
        and generated.get("CONFIG_LTO_CLANG_THIN") == "n"
    )
    security = {
        key: {
            "stock": stock.get(key, "<missing>"),
            "generated": generated.get(key, "<missing>"),
        }
        for key in CRITICAL_SECURITY_CONFIGS
    }
    security_preserved = all(
        row["stock"] == "y" and row["generated"] == "y"
        for row in security.values()
    )
    return {
        "stock_sha256": r2.sha256_file(stock_path),
        "generated_sha256": r2.sha256_file(generated_path),
        "delta_count": len(deltas),
        "deltas": deltas,
        "unexpected_deltas": unexpected,
        "witness_exact": witness_exact,
        "path_only_valid": path_only_valid,
        "full_lto": full_lto,
        "critical_security": security,
        "critical_security_preserved": security_preserved,
        "verified": (
            not unexpected
            and witness_exact
            and path_only_valid
            and full_lto
            and security_preserved
        ),
    }


def compare_full_symvers(baseline: Path, candidate: Path) -> dict[str, Any]:
    baseline_map, baseline_conflicts = r2.parse_symvers([baseline])
    candidate_map, candidate_conflicts = r2.parse_symvers([candidate])
    missing = sorted(set(baseline_map) - set(candidate_map))
    added = sorted(set(candidate_map) - set(baseline_map))
    mismatched = [
        {
            "symbol": symbol,
            "baseline": baseline_map[symbol],
            "candidate": candidate_map[symbol],
        }
        for symbol in sorted(set(baseline_map) & set(candidate_map))
        if baseline_map[symbol] != candidate_map[symbol]
    ]
    baseline_sha256 = r2.sha256_file(baseline)
    candidate_sha256 = r2.sha256_file(candidate)
    baseline_size = baseline.stat().st_size
    candidate_size = candidate.stat().st_size
    return {
        "baseline_sha256": baseline_sha256,
        "candidate_sha256": candidate_sha256,
        "baseline_size": baseline_size,
        "candidate_size": candidate_size,
        "byte_identical": (
            baseline_sha256 == candidate_sha256
            and baseline_size == candidate_size
        ),
        "baseline_symbols": len(baseline_map),
        "candidate_symbols": len(candidate_map),
        "baseline_conflicts": baseline_conflicts,
        "candidate_conflicts": candidate_conflicts,
        "missing_count": len(missing),
        "missing_sample": missing[:50],
        "added_count": len(added),
        "added_sample": added[:50],
        "mismatched_count": len(mismatched),
        "mismatched_sample": mismatched[:50],
        "verified": (
            not baseline_conflicts
            and not candidate_conflicts
            and not missing
            and not added
            and not mismatched
            and baseline_sha256 == candidate_sha256
            and baseline_size == candidate_size
        ),
    }


def compare_abi_definition(baseline: Path, candidate: Path) -> dict[str, Any]:
    baseline_sha256 = r2.sha256_file(baseline)
    candidate_sha256 = r2.sha256_file(candidate)
    return {
        "baseline_path": str(baseline),
        "candidate_path": str(candidate),
        "baseline_sha256": baseline_sha256,
        "candidate_sha256": candidate_sha256,
        "baseline_size": baseline.stat().st_size,
        "candidate_size": candidate.stat().st_size,
        "verified": (
            baseline_sha256 == candidate_sha256
            and baseline.stat().st_size == candidate.stat().st_size
        ),
    }


def check_sec_log_buf_module(config_path: Path, module_path: Path) -> dict[str, Any]:
    config = r2.parse_config(config_path)
    module_regular = module_path.is_file() and not module_path.is_symlink()
    result = {
        "config_path": str(config_path),
        "config_value": config.get("CONFIG_SEC_LOG_BUF", "<missing>"),
        "module_path": str(module_path),
        "module_regular": module_regular,
        "module_sha256": r2.sha256_file(module_path) if module_regular else None,
    }
    result["verified"] = result["config_value"] == "m" and module_regular
    return result


def count_file_occurrences(path: Path, needle: bytes) -> int:
    if not needle:
        raise AuditError("empty byte pattern is not countable")
    count = 0
    overlap = len(needle) - 1
    tail = b""
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            data = tail + chunk
            count += data.count(needle)
            tail = data[-overlap:] if overlap else b""
    return count


def check_image_load_derivation(image: Path, vmlinux: Path) -> dict[str, Any]:
    image_data = image.read_bytes()
    expected = bytearray(len(image_data))
    occupied = bytearray(len(image_data))
    segment_rows: list[dict[str, Any]] = []
    with elf_audit.Elf64(vmlinux) as elf:
        load_base = elf.load_base()
        for row in elf.load_segment_manifest():
            offset = int(row["image_offset"])
            size = int(row["file_size"])
            bounded = 0 <= offset <= len(image_data) - size
            overlap = bounded and any(occupied[offset : offset + size])
            if bounded and not overlap:
                source_offset = int(row["file_offset"])
                projected = elf.data[source_offset : source_offset + size]
                expected[offset : offset + size] = projected
                occupied[offset : offset + size] = b"\x01" * size
            else:
                projected = b""
            segment_rows.append(
                {
                    **row,
                    "bounded": bounded,
                    "overlap": overlap,
                    "projected_sha256": (
                        hashlib.sha256(projected).hexdigest() if bounded and not overlap else None
                    ),
                    "verified": (
                        bounded
                        and not overlap
                        and hashlib.sha256(projected).hexdigest() == row["sha256"]
                    ),
                }
            )
    expected_bytes = bytes(expected)
    expected_sha256 = hashlib.sha256(expected_bytes).hexdigest()
    image_sha256 = hashlib.sha256(image_data).hexdigest()
    first_mismatch = next(
        (
            index
            for index, (actual, wanted) in enumerate(zip(image_data, expected_bytes))
            if actual != wanted
        ),
        None,
    )
    result = {
        "load_base": load_base,
        "image_size": len(image_data),
        "segment_count": len(segment_rows),
        "covered_bytes": sum(occupied),
        "derived_start": min(
            (int(row["image_offset"]) for row in segment_rows), default=None
        ),
        "derived_extent": max(
            (
                int(row["image_offset"]) + int(row["file_size"])
                for row in segment_rows
            ),
            default=None,
        ),
        "segments": segment_rows,
        "expected_image_sha256": expected_sha256,
        "image_sha256": image_sha256,
        "first_mismatch_offset": first_mismatch,
        "whole_image_exact": image_data == expected_bytes,
    }
    result["verified"] = (
        bool(segment_rows)
        and all(row["verified"] for row in segment_rows)
        and result["derived_start"] == 0
        and result["derived_extent"] == len(image_data)
        and result["whole_image_exact"]
    )
    return result


def check_system_map(path: Path, symbols: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected = {
        name: int(row["value"])
        for name, row in symbols.items()
        if name
        in {
            "kernel_init",
            "run_init_process",
            "strcmp",
            "memcpy",
            "memstart_addr",
            "ramdisk_execute_command",
        }
    }
    found: dict[str, list[int]] = {name: [] for name in expected}
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] in found:
            try:
                found[fields[2]].append(int(fields[0], 16))
            except ValueError as exc:
                raise AuditError(f"invalid System.map address: {line}") from exc
    details = {
        name: {
            "vmlinux_address": address,
            "system_map_addresses": found[name],
            "verified": found[name] == [address],
        }
        for name, address in expected.items()
    }
    return {
        "path": str(path),
        "sha256": r2.sha256_file(path),
        "symbols": details,
        "verified": len(details) == 6 and all(
            row["verified"] for row in details.values()
        ),
    }


def check_final_binary_contract(
    *,
    image: Path,
    vmlinux: Path,
    system_map: Path,
    generated_config: Path,
    build_stdout: Path,
) -> dict[str, Any]:
    marker = patch_check.MARKER.encode("ascii")
    elf = elf_audit.inspect_final_vmlinux(vmlinux, marker)
    image_data = image.read_bytes()
    hmac = bytes.fromhex(elf["fips"]["hmac_hex"])
    image_hmac_count = count_file_occurrences(image, hmac)
    image_marker_count = count_file_occurrences(image, marker)
    image_family_count = count_file_occurrences(
        image, MARKER_FAMILY
    )
    historical_image_count = count_file_occurrences(
        image, HISTORICAL_MARKER_FAMILY
    )
    historical_vmlinux_count = count_file_occurrences(
        vmlinux, HISTORICAL_MARKER_FAMILY
    )
    config = r2.parse_config(generated_config)
    stdout = build_stdout.read_text(encoding="utf-8", errors="strict")
    fips_log = {
        "generate_count": stdout.count(
            "FIPS : Generating hmac of crypto and updating vmlinux"
        ),
        "complete_count": stdout.count(
            "FIPS integrity procedure has been finished for crypto"
        ),
    }
    fips_log["verified"] = (
        fips_log["generate_count"] == 1 and fips_log["complete_count"] == 1
    )
    system_map_gate = check_system_map(system_map, elf["symbols"])
    projection_specs = {
        "builtime_crypto_hmac": (
            elf["fips"]["hmac_size"],
            elf["fips"]["hmac_sha256"],
        ),
        "integrity_crypto_addrs": (
            elf["fips"]["address_table_size"],
            elf["fips"]["address_table_sha256"],
        ),
        "crypto_buildtime_address": (
            elf["fips"]["build_address_size"],
            elf["fips"]["build_address_sha256"],
        ),
    }
    image_projection: dict[str, dict[str, Any]] = {}
    for name, (size, expected_sha256) in projection_specs.items():
        offset = elf["fips"]["image_offsets"][name]
        bounded = isinstance(offset, int) and 0 <= offset <= len(image_data) - size
        projected = image_data[offset : offset + size] if bounded else b""
        actual_sha256 = hashlib.sha256(projected).hexdigest() if bounded else None
        image_projection[name] = {
            "offset": offset,
            "size": size,
            "bounded": bounded,
            "expected_vmlinux_sha256": expected_sha256,
            "image_sha256": actual_sha256,
            "verified": bounded and actual_sha256 == expected_sha256,
        }
    image_projection_verified = all(
        row["verified"] for row in image_projection.values()
    )
    image_header = check_arm64_image_header(image)
    image_load_derivation = check_image_load_derivation(image, vmlinux)
    result = {
        "elf": elf,
        "system_map": system_map_gate,
        "image_hmac_count": image_hmac_count,
        "image_marker_count": image_marker_count,
        "image_family_count": image_family_count,
        "historical_image_family_count": historical_image_count,
        "historical_vmlinux_family_count": historical_vmlinux_count,
        "fips_config": config.get("CONFIG_CRYPTO_FIPS", "<missing>"),
        "fips140_config": config.get("CONFIG_CRYPTO_FIPS140", "<missing>"),
        "fips_log": fips_log,
        "fips_image_projection": {
            "symbols": image_projection,
            "verified": image_projection_verified,
        },
        "arm64_image_header": image_header,
        "image_load_derivation": image_load_derivation,
    }
    result["verified"] = (
        elf["verified"]
        and system_map_gate["verified"]
        and image_hmac_count == 1
        and image_marker_count == 1
        and image_family_count == 1
        and historical_image_count == 0
        and historical_vmlinux_count == 0
        and result["fips_config"] == "y"
        and result["fips140_config"] == "y"
        and fips_log["verified"]
        and image_projection_verified
        and image_header["verified"]
        and image_load_derivation["verified"]
    )
    return result


def audit_build_result(
    path: Path,
    *,
    recorded_root: Path | None = None,
    observed_root: Path | None = None,
    expected_work_tree: Path | None = None,
    expected_artifacts: dict[str, Path] | None = None,
) -> dict[str, Any]:
    build = r2.load_json(path)
    timestamp = build.get("timestamp_control_runtime", {})
    kmi_path = build.get("kmi_path_control_runtime", {})
    kernel_debug = build.get("kernel_debug_control_runtime", {})
    vdso_debug = build.get("vdso_debug_control_runtime", {})
    patch_contract = build.get(PATCH_CONTRACT_FIELD, {})
    source_delta = build.get("source_delta", {})
    clean_output = build.get("clean_output_precondition", {})
    output_root = build.get("exclusive_output_root", {})
    incremental = build.get("incremental_dist_refresh", {})
    result_directory = build.get("result_directory", {})
    effective_tools = build.get("provenance", {}).get("effective_tools", {})
    private_namespace = build.get("provenance", {}).get("private_namespace", {})
    recorded_work_tree = build.get("work_tree")

    def recorded_equivalent(observed: Path) -> Path:
        if recorded_root is None or observed_root is None:
            return observed
        try:
            relative = observed.resolve().relative_to(observed_root.resolve())
        except ValueError:
            return observed
        return recorded_root / relative

    if isinstance(recorded_work_tree, str):
        recorded_path = Path(recorded_work_tree)
        if not recorded_path.is_absolute() and recorded_root is not None:
            recorded_path = recorded_root / recorded_path
        recorded_path = recorded_path.resolve()
    else:
        recorded_path = None
    work_tree_bound = expected_work_tree is None or (
        recorded_path == recorded_equivalent(expected_work_tree).resolve()
    )
    output_rows = {
        row.get("name"): row
        for row in build.get("outputs", [])
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    artifact_bindings: dict[str, dict[str, Any]] = {}
    if expected_artifacts is not None:
        for name, artifact_path in expected_artifacts.items():
            row = output_rows.get(name, {})
            expected_recorded_path = recorded_equivalent(artifact_path)
            artifact_bindings[name] = {
                "path_match": (
                    isinstance(row.get("path"), str)
                    and Path(row["path"]).resolve()
                    == expected_recorded_path.resolve()
                ),
                "sha256_match": (
                    artifact_path.is_file()
                    and not artifact_path.is_symlink()
                    and row.get("sha256") == r2.sha256_file(artifact_path)
                ),
                "size_match": (
                    artifact_path.is_file()
                    and row.get("size") == artifact_path.stat().st_size
                ),
            }
            artifact_bindings[name]["verified"] = all(
                artifact_bindings[name].values()
            )
    artifacts_bound = expected_artifacts is None or (
        set(artifact_bindings) == set(expected_artifacts)
        and all(item["verified"] for item in artifact_bindings.values())
    )
    gate = {
        "path": str(path),
        "sha256": r2.sha256_file(path),
        "schema": build.get("schema"),
        "lto_mode": build.get("lto_mode"),
        "returncode": build.get("returncode"),
        BUILD_PASS_FIELD: build.get(BUILD_PASS_FIELD),
        "source_overlay_verified": build.get("provenance", {})
        .get("source_overlay", {})
        .get("verified"),
        "patch_contract_verdict": patch_contract.get("verdict"),
        "patch_sha256": source_delta.get("patch_sha256"),
        "source_delta_verified": source_delta.get("verified"),
        "source_delta_restored": (
            source_delta.get("applied") is True
            and source_delta.get("patched_content_unchanged") is True
            and source_delta.get("restored") is True
            and source_delta.get("verified") is True
        ),
        "clean_output_verified": (
            clean_output.get("verified") is True
            and clean_output.get("exists") is False
            and output_root.get("created_exclusively") is True
            and output_root.get("empty_at_creation") is True
            and output_root.get("same_inode_after_build") is True
            and output_root.get("same_work_tree_inode_after_build") is True
            and output_root.get("namespace_unchanged") is True
            and output_root.get("namespace_events") == []
            and output_root.get("verified") is True
            and incremental.get("clean_output_tree") is True
            and incremental.get("removed") == []
        ),
        "exclusive_result_directory_verified": (
            result_directory.get("created_exclusively") is True
            and isinstance(result_directory.get("path"), str)
            and Path(result_directory["path"]).resolve()
            == recorded_equivalent(path.parent).resolve()
        ),
        "private_namespace_verified": (
            private_namespace.get("verified") is True
            and private_namespace.get("marker")
            == r4w1b_build.PRIVATE_NAMESPACE_MARKER
            and private_namespace.get("cap_eff") == 0
            and private_namespace.get("cap_prm") == 0
            and private_namespace.get("cap_bnd") == 0
            and private_namespace.get("no_new_privs") == "1"
        ),
        "effective_tools_verified": (
            effective_tools.get("verified") is True
            and effective_tools.get("expected_count")
            == len(r4w1b_build.base.EFFECTIVE_TOOL_NAMES)
            and len(effective_tools.get("tools", []))
            == len(r4w1b_build.base.EFFECTIVE_TOOL_NAMES)
            and all(row.get("verified") is True for row in effective_tools.get("tools", []))
        ),
        "recorded_work_tree": recorded_work_tree,
        "work_tree_bound": work_tree_bound,
        "artifact_bindings": artifact_bindings,
        "artifacts_bound": artifacts_bound,
        "output_gate_verified": build.get("output_gate", {}).get("verified"),
        "module_gate_verified": build.get("module_gate", {}).get("verified"),
        "kernel_banner_gate_verified": build.get("kernel_banner_gate", {}).get(
            "verified"
        ),
        "witness_output_gate_verified": build.get("witness_output_gate", {}).get(
            "verified"
        ),
        "timestamp_control_verified": (
            timestamp.get("applied") is True
            and timestamp.get("restored") is True
            and timestamp.get("patched_content_unchanged") is True
            and timestamp.get("restored_sha256") == timestamp.get("original_sha256")
        ),
        "kmi_path_control_verified": (
            kmi_path.get("applied") is True
            and kmi_path.get("restored") is True
            and kmi_path.get("patched_content_unchanged") is True
            and kmi_path.get("restored_sha256") == kmi_path.get("original_sha256")
            and kmi_path.get("original_sha256") == r4w1b_build.BUILD_SH_SHA256
        ),
        "kernel_debug_control_verified": (
            kernel_debug.get("applied") is True
            and kernel_debug.get("restored") is True
            and kernel_debug.get("patched_content_unchanged") is True
            and kernel_debug.get("restored_sha256")
            == kernel_debug.get("original_sha256")
            and kernel_debug.get("original_sha256")
            == r4w1b_build.KERNEL_MAKEFILE_SHA256
            and kernel_debug.get("object_map") == "/kernel-out"
        ),
        "vdso_debug_control_verified": (
            vdso_debug.get("applied") is True
            and vdso_debug.get("restored") is True
            and vdso_debug.get("patched_content_unchanged") is True
            and vdso_debug.get("verified") is True
            and len(vdso_debug.get("files", []))
            == len(r4w1b_build.VDSO_DEBUG_CONTROLS)
            and all(
                row.get("restored") is True
                and row.get("patched_content_unchanged") is True
                and row.get("original_sha256") == spec["sha256"]
                and row.get("source_map") == "/kernel-src"
                and row.get("object_map") == "/kernel-out"
                for row, spec in zip(
                    vdso_debug.get("files", []), r4w1b_build.VDSO_DEBUG_CONTROLS
                )
            )
        ),
    }
    gate["verified"] = (
        gate["schema"] == r4w1b_build.SCHEMA
        and gate["lto_mode"] == "full"
        and gate["returncode"] == 0
        and gate[BUILD_PASS_FIELD] is True
        and gate["source_overlay_verified"] is True
        and gate["patch_contract_verdict"] == patch_check.VERDICT
        and gate["patch_sha256"] == patch_check.PATCH_SHA256
        and gate["source_delta_verified"] is True
        and gate["source_delta_restored"] is True
        and gate["clean_output_verified"] is True
        and gate["exclusive_result_directory_verified"] is True
        and gate["effective_tools_verified"] is True
        and gate["work_tree_bound"] is True
        and gate["artifacts_bound"] is True
        and gate["output_gate_verified"] is True
        and gate["module_gate_verified"] is True
        and gate["kernel_banner_gate_verified"] is True
        and gate["witness_output_gate_verified"] is True
        and gate["timestamp_control_verified"] is True
        and gate["kmi_path_control_verified"] is True
        and gate["kernel_debug_control_verified"] is True
        and gate["vdso_debug_control_verified"] is True
        and gate["private_namespace_verified"] is True
    )
    return gate


def run_audit(
    root: Path,
    *,
    recorded_root: Path | None = None,
    work_tree: Path,
    build_result: Path,
    baseline_symvers: Path,
    baseline_abi: Path,
    symvers_paths: list[Path] | None,
    stock_baseline: Path,
    stock_config: Path,
    requirements: list[Path],
    module_map: Path,
    corpus_layout: Path,
) -> dict[str, Any]:
    dist = work_tree / "out/msm-waipio-waipio-gki/gki_kernel/dist"
    image = dist / "Image"
    vmlinux = dist / "vmlinux"
    system_map = dist / "System.map"
    generated_config = work_tree / (
        "out/msm-waipio-waipio-gki/gki_kernel/common/.config"
    )
    candidate_symvers = dist / "vmlinux.symvers"
    candidate_abi = dist / "abi.xml"
    vendor_config = work_tree / "out/msm-waipio-waipio-gki/msm-kernel/.config"
    sec_log_buf_module = work_tree / (
        "out/msm-waipio-waipio-gki/dist/sec_log_buf.ko"
    )
    fips_sources = {
        name: work_tree / relative
        for name, (relative, _, _) in FIPS_SOURCE_INPUTS.items()
    }
    build_stdout = build_result.parent / "stdout.log"
    build_data = r2.load_json(build_result)
    effective_path = build_data.get("provenance", {}).get("effective_path", "")
    fips_runtime_inputs = collect_fips_runtime_inputs(
        work_tree, effective_path=effective_path
    )
    if symvers_paths is None:
        symvers_items = build_data.get("symvers_files", [])
        symvers_paths = [Path(item["path"]) for item in symvers_items]
        if not symvers_paths:
            raise AuditError("build result contains no symvers files")
        for item, path in zip(symvers_items, symvers_paths):
            if not path.is_file() or r2.sha256_file(path) != item.get("sha256"):
                raise AuditError(f"build-result symvers identity mismatch: {path}")
    required = [
        image,
        vmlinux,
        system_map,
        generated_config,
        candidate_symvers,
        candidate_abi,
        vendor_config,
        sec_log_buf_module,
        build_result,
        build_stdout,
        baseline_symvers,
        baseline_abi,
        stock_baseline,
        stock_config,
        module_map,
        corpus_layout,
        *fips_sources.values(),
        *symvers_paths,
        *requirements,
    ]
    missing = [
        str(path)
        for path in required
        if not path.is_file() or path.is_symlink()
    ]
    if missing:
        raise AuditError(f"required inputs missing or indirect: {missing}")
    if len(requirements) != 2 or requirements[0].resolve() == requirements[1].resolve():
        raise AuditError("exactly two distinct pinned requirement inputs are required")

    pinned_paths = {
        "baseline_symvers": baseline_symvers,
        "baseline_abi": baseline_abi,
        "stock_baseline": stock_baseline,
        "stock_config": stock_config,
        "requirements_0": requirements[0],
        "requirements_1": requirements[1],
        "module_map": module_map,
        "corpus_layout": corpus_layout,
    }
    pinned_inputs = {
        name: check_pinned_identity(path, *PINNED_BASELINE_INPUTS[name])
        for name, path in pinned_paths.items()
    }
    fips_source_gate = {
        name: check_pinned_identity(
            fips_sources[name], expected_sha256, expected_size
        )
        for name, (_, expected_sha256, expected_size) in FIPS_SOURCE_INPUTS.items()
    }
    pinned_inputs_verified = all(
        row["verified"] for row in (*pinned_inputs.values(), *fips_source_gate.values())
    )

    manifest_paths = {
        "build_result": build_result,
        "build_stdout": build_stdout,
        "image": image,
        "vmlinux": vmlinux,
        "system_map": system_map,
        "generated_config": generated_config,
        "candidate_symvers": candidate_symvers,
        "candidate_abi": candidate_abi,
        "vendor_config": vendor_config,
        "sec_log_buf_module": sec_log_buf_module,
        **pinned_paths,
        **fips_sources,
        **fips_runtime_inputs,
        **{f"provider_symvers_{index}": path for index, path in enumerate(symvers_paths)},
    }
    input_manifest = {
        name: file_identity(path) for name, path in manifest_paths.items()
    }
    input_manifest_verified = all(
        (
            row["regular"] and row["stable_during_read"] and not row["indirect"]
            if "_object_" not in name
            else (row["regular"] and row["stable_during_read"] and not row["indirect"])
            or (not row["exists"] and not row["indirect"])
        )
        for name, row in input_manifest.items()
    )

    stock = r2.load_json(stock_baseline)
    module_manifest = r2.load_json(module_map)
    corpus = r2.load_json(corpus_layout)
    if any(item.get("target") != TARGET for item in (stock, module_manifest, corpus)):
        raise AuditError("target mismatch in pinned baseline")
    expected_banner = stock.get("linux_banner")
    if not isinstance(expected_banner, str) or not expected_banner:
        raise AuditError("stock baseline has no Linux banner")

    build_gate = audit_build_result(
        build_result,
        recorded_root=recorded_root or root,
        observed_root=root,
        expected_work_tree=work_tree,
        expected_artifacts={
            "Image": image,
            ".config": generated_config,
            "vmlinux.symvers": candidate_symvers,
            "abi.xml": candidate_abi,
            "vmlinux": vmlinux,
            "System.map": system_map,
        },
    )
    image_gate = r2.image_metadata(image, expected_banner=expected_banner)
    config_gate = compare_r4w1b_configs(stock_config, generated_config)
    consumer_crc = r2.compare_symbol_requirements(requirements, symvers_paths)
    full_symvers = compare_full_symvers(baseline_symvers, candidate_symvers)
    abi_definition = compare_abi_definition(baseline_abi, candidate_abi)
    baseline_identity = {
        "symvers_sha256": r2.sha256_file(baseline_symvers),
        "expected_symvers_sha256": BASELINE_SYMVERS_SHA256,
        "abi_sha256": r2.sha256_file(baseline_abi),
        "expected_abi_sha256": BASELINE_ABI_SHA256,
    }
    baseline_identity["verified"] = (
        baseline_identity["symvers_sha256"] == BASELINE_SYMVERS_SHA256
        and baseline_identity["abi_sha256"] == BASELINE_ABI_SHA256
    )
    sec_log_buf_gate = check_sec_log_buf_module(vendor_config, sec_log_buf_module)
    partition_capacity = r2.boot_capacity(stock, image_gate["file_bytes"])
    fixed_layout = {
        "capacity": r4w1b_build.FIXED_KERNEL_SLOT_CAPACITY,
        "image_bytes": image_gate["file_bytes"],
        "aligned_image_bytes": r2.aligned(image_gate["file_bytes"]),
        "remaining": r4w1b_build.FIXED_KERNEL_SLOT_CAPACITY - image_gate["file_bytes"],
        "absolute_ramdisk_start": r4w1b_build.ABSOLUTE_RAMDISK_START,
        "verified": (
            image_gate["file_bytes"] == r4w1b_build.STOCK_IMAGE_SIZE
            and r2.aligned(image_gate["file_bytes"])
            == r4w1b_build.FIXED_KERNEL_SLOT_CAPACITY
            and 4096 + r4w1b_build.FIXED_KERNEL_SLOT_CAPACITY
            == r4w1b_build.ABSOLUTE_RAMDISK_START
        ),
    }
    corpus_gate = {
        "vendor_ramdisk_modules": module_manifest.get("inputs", {}).get(
            "module_count"
        ),
        "layout_sha256": r2.sha256_file(corpus_layout),
        "complete_modules": corpus.get("complete_module_count"),
    }
    corpus_gate["verified"] = (
        corpus_gate["vendor_ramdisk_modules"] == r2.EXPECTED_VENDOR_RAMDISK_MODULES
        and corpus_gate["layout_sha256"] == r2.EXPECTED_CORPUS_LAYOUT_SHA256
        and corpus.get("schema") == "s22plus_fyg8_super_module_layout_v1"
        and corpus.get("complete_on_disk_module_corpus") is True
        and corpus_gate["complete_modules"] == 491
    )
    marker = patch_check.MARKER.encode("ascii")
    marker_gate = {
        "image_count": count_file_occurrences(image, marker),
        "image_family_count": count_file_occurrences(
            image, MARKER_FAMILY
        ),
        "image_historical_family_count": count_file_occurrences(
            image, HISTORICAL_MARKER_FAMILY
        ),
        "vmlinux_count": count_file_occurrences(vmlinux, marker),
        "vmlinux_family_count": count_file_occurrences(
            vmlinux, MARKER_FAMILY
        ),
        "vmlinux_historical_family_count": count_file_occurrences(
            vmlinux, HISTORICAL_MARKER_FAMILY
        ),
        "marker_id": patch_check.MARKER_ID,
    }
    marker_gate["verified"] = (
        marker_gate["image_count"] == 1
        and marker_gate["image_family_count"] == 1
        and marker_gate["image_historical_family_count"] == 0
        and marker_gate["vmlinux_count"] == 1
        and marker_gate["vmlinux_family_count"] == 1
        and marker_gate["vmlinux_historical_family_count"] == 0
    )
    final_binary = check_final_binary_contract(
        image=image,
        vmlinux=vmlinux,
        system_map=system_map,
        generated_config=generated_config,
        build_stdout=build_stdout,
    )
    fips_regeneration = regenerate_fips_oracle(
        work_tree,
        vmlinux,
        effective_path=effective_path,
        runtime_inputs=fips_runtime_inputs,
    )
    input_manifest_post = {
        name: file_identity(path) for name, path in manifest_paths.items()
    }
    input_manifest_stable = input_manifest_post == input_manifest

    gates = {
        "build": build_gate,
        "image": image_gate,
        "config": config_gate,
        "consumer_crc": consumer_crc,
        "baseline_identity": baseline_identity,
        "full_symvers": full_symvers,
        "abi_definition": abi_definition,
        "sec_log_buf_single_writer": sec_log_buf_gate,
        "partition_capacity": partition_capacity,
        "fixed_layout": fixed_layout,
        "module_corpus": corpus_gate,
        "marker": marker_gate,
        "final_binary": final_binary,
        "fips_regeneration": fips_regeneration,
        "pinned_inputs": {
            "baseline": pinned_inputs,
            "fips_sources": fips_source_gate,
            "verified": pinned_inputs_verified,
        },
        "input_manifest": {
            "files": input_manifest,
            "post_files": input_manifest_post,
            "stable": input_manifest_stable,
            "verified": input_manifest_verified and input_manifest_stable,
        },
    }
    blockers: list[str] = []
    if not build_gate["verified"]:
        blockers.append(f"{AUDIT_LABEL} Full-LTO build provenance gate failed")
    if not image_gate["exact_banner_match"]:
        blockers.append("Linux banner differs from exact FYG8 baseline")
    if not config_gate["verified"]:
        blockers.append(f"config delta is not the exact {AUDIT_LABEL} contract")
    if not consumer_crc["provider_crc_closed"]:
        blockers.append("stock module-consumer CRC closure failed")
    if not consumer_crc["expected_baseline_shape"]:
        blockers.append("module-consumer requirement baseline shape changed")
    if not baseline_identity["verified"]:
        blockers.append("pinned R4W1 KMI/ABI baseline identity changed")
    if not full_symvers["verified"]:
        blockers.append("complete exported symbol/CRC mapping changed")
    if not abi_definition["verified"]:
        blockers.append("generated GKI ABI definition differs from baseline")
    if not sec_log_buf_gate["verified"]:
        blockers.append("sec_log_buf is not a loadable module for witness timing")
    if not partition_capacity["fits"]:
        blockers.append("Image exceeds boot partition capacity")
    if not fixed_layout["verified"]:
        blockers.append(f"Image does not match exact {AUDIT_LABEL} kernel geometry")
    if not corpus_gate["verified"]:
        blockers.append("pinned module corpus contract failed")
    if not marker_gate["verified"]:
        blockers.append(f"Image/vmlinux {AUDIT_LABEL} marker-family contract failed")
    if not final_binary["verified"]:
        blockers.append("final vmlinux control-flow/FIPS/System.map contract failed")
    if not fips_regeneration["verified"]:
        blockers.append("pinned FIPS generator did not reproduce the final vmlinux")
    if not pinned_inputs_verified:
        blockers.append("one or more baseline/FIPS source inputs are not exact pins")
    if not input_manifest_verified:
        blockers.append("one or more static-audit inputs are missing, unstable, or indirect")
    if not input_manifest_stable:
        blockers.append("one or more static-audit inputs changed during the transaction")
    return {
        "schema": SCHEMA,
        "target": TARGET,
        "verdict": VERDICT if not blockers else BLOCKED_VERDICT,
        "gates": gates,
        "symvers_paths": [r2.display_path(root, path) for path in symvers_paths],
        "blockers": blockers,
        STATIC_PASS_FIELD: not blockers,
        "safety": {
            "host_only": True,
            "device_contact": False,
            "image_packaging": False,
            "flash": False,
            "live_authorized": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-tree", type=Path, required=True)
    parser.add_argument("--build-result", type=Path, required=True)
    parser.add_argument("--baseline-symvers", type=Path, default=DEFAULT_BASELINE_SYMVERS)
    parser.add_argument("--baseline-abi", type=Path, default=DEFAULT_BASELINE_ABI)
    parser.add_argument("--symvers", type=Path, action="append")
    parser.add_argument("--stock-baseline", type=Path, default=r2.DEFAULT_STOCK_BASELINE)
    parser.add_argument("--stock-config", type=Path, default=r2.DEFAULT_STOCK_CONFIG)
    parser.add_argument("--requirements", type=Path, action="append")
    parser.add_argument("--module-map", type=Path, default=r2.DEFAULT_MODULE_MAP)
    parser.add_argument("--corpus-layout", type=Path, default=r2.DEFAULT_CORPUS_LAYOUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = r2.repo_root()
    requirements = args.requirements or [
        r2.DEFAULT_REQUIREMENTS,
        r2.DEFAULT_EXTRA_REQUIREMENTS,
    ]
    path_arguments = [
        args.work_tree,
        args.build_result,
        args.baseline_symvers,
        args.baseline_abi,
        args.stock_baseline,
        args.stock_config,
        args.module_map,
        args.corpus_layout,
        args.out,
        *(args.symvers or []),
        *requirements,
    ]
    if any(path.is_absolute() for path in path_arguments):
        raise AuditError("R4W1-B isolated audit requires repo-relative paths")
    reexecuted = r4w1b_build.reexec_in_private_repo_namespace(
        root,
        script=Path(__file__),
        arguments=sys.argv[1:],
        compatibility_work_tree=args.work_tree,
    )
    if reexecuted is not None:
        return reexecuted
    private_namespace = r4w1b_build.inspect_private_namespace(root)
    if not private_namespace["verified"]:
        raise AuditError("R4W1-B private repository namespace is not verified")
    recorded_root = Path(private_namespace["recorded_repo"])
    result = run_audit(
        root,
        recorded_root=recorded_root,
        work_tree=r2.resolve(root, args.work_tree),
        build_result=r2.resolve(root, args.build_result),
        baseline_symvers=r2.resolve(root, args.baseline_symvers),
        baseline_abi=r2.resolve(root, args.baseline_abi),
        symvers_paths=(
            [r2.resolve(root, path) for path in args.symvers]
            if args.symvers
            else None
        ),
        stock_baseline=r2.resolve(root, args.stock_baseline),
        stock_config=r2.resolve(root, args.stock_config),
        requirements=[r2.resolve(root, path) for path in requirements],
        module_map=r2.resolve(root, args.module_map),
        corpus_layout=r2.resolve(root, args.corpus_layout),
    )
    result["private_namespace"] = private_namespace
    out = r2.resolve(root, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    recorded_result = r4w1b_build.rebase_recorded_paths(
        result,
        observed_root=root,
        recorded_root=recorded_root,
        embedded=True,
    )
    out.write_text(
        json.dumps(recorded_result, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(
        json.dumps(
            {
                "result": "pass" if result[STATIC_PASS_FIELD] else "blocked",
                "out": r2.display_path(root, out),
                "blocker_count": len(result["blockers"]),
                "fixed_layout_remaining": result["gates"]["fixed_layout"][
                    "remaining"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result[STATIC_PASS_FIELD] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        AuditError,
        r2.AuditError,
        r4w1b_build.BuildError,
        OSError,
        KeyError,
    ) as exc:
        raise SystemExit(str(exc)) from exc
