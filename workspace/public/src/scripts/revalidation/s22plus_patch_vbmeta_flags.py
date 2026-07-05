#!/usr/bin/env python3
"""Patch top-level AVB vbmeta flags for the S22+ FYG8 vbmeta experiment."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


AVB_MAGIC = b"AVB0"
AVB_HEADER_SIZE = 256
AVB_FLAGS_OFFSET = 120
AVB_FLAGS_HASHTREE_DISABLED = 1
AVB_FLAGS_VERIFICATION_DISABLED = 2
AVB_FLAGS_DISABLED_BOTH = AVB_FLAGS_HASHTREE_DISABLED | AVB_FLAGS_VERIFICATION_DISABLED


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_vbmeta_flags(
    src: Path,
    dst: Path,
    flags: int,
    expect_src_sha256: str | None,
    expect_old_flags: int | None,
) -> dict[str, object]:
    src_bytes = src.read_bytes()
    src_sha256 = hashlib.sha256(src_bytes).hexdigest()
    if expect_src_sha256 is not None and src_sha256.lower() != expect_src_sha256.lower():
        raise ValueError(
            f"{src} SHA256 mismatch: got {src_sha256}, expected {expect_src_sha256}"
        )

    data = bytearray(src_bytes)
    if len(data) < AVB_HEADER_SIZE:
        raise ValueError(f"{src} is too small for an AVB vbmeta header")
    if data[:4] != AVB_MAGIC:
        raise ValueError(f"{src} does not start with AVB0")

    old_flags = struct.unpack_from("!I", data, AVB_FLAGS_OFFSET)[0]
    if expect_old_flags is not None and old_flags != expect_old_flags:
        raise ValueError(f"{src} flags mismatch: got {old_flags}, expected {expect_old_flags}")

    struct.pack_into("!I", data, AVB_FLAGS_OFFSET, flags)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)

    changed_offsets = [i for i, (a, b) in enumerate(zip(src_bytes, data)) if a != b]
    dst_sha256 = sha256_file(dst)
    return {
        "src": str(src),
        "dst": str(dst),
        "size": len(data),
        "old_flags": old_flags,
        "new_flags": flags,
        "changed_offsets": changed_offsets,
        "src_sha256": src_sha256,
        "dst_sha256": dst_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, type=Path)
    parser.add_argument("--dst", required=True, type=Path)
    parser.add_argument("--flags", type=lambda x: int(x, 0), default=AVB_FLAGS_DISABLED_BOTH)
    parser.add_argument("--expect-src-sha256")
    parser.add_argument("--expect-old-flags", type=lambda x: int(x, 0))
    args = parser.parse_args()

    result = patch_vbmeta_flags(
        args.src,
        args.dst,
        args.flags,
        args.expect_src_sha256,
        args.expect_old_flags,
    )
    for key, value in result.items():
        if isinstance(value, list):
            value = ",".join(str(v) for v in value)
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
