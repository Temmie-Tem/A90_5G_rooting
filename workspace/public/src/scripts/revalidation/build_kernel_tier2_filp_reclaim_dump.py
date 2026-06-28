#!/usr/bin/env python3
"""Tier-2 KASAN-lite variant: dump the reset_file `struct file` object at the
proc_integrity_reset_file use site (RECON, observation-only).

Difference vs build_kernel_tier2_kasan_lite_reclaim_dump.py: instead of dumping the
`task_integrity` object, this hook loads `reset_file = task->integrity->reset_file`
and dumps the first words of that `struct file` (offsets 0x00..0x38) so the operator
can observe whether a freed reset_file slot (general filp cache) gets reclaimed.

It NEVER dereferences f_path.dentry / f_op and NEVER calls d_path (no
function-pointer call). A `cbz` NULL-check skips the dump if reset_file is NULL.
Same ROPP-correct direct-bl-printk method as the base builder; x17 preserved; the
only control-flow instructions are direct `bl printk` (x3) and one forward `cbz`
(direct conditional branch, not JOPP-gated). RECON only.

struct file layout (4.14, verified from include/linux/fs.h):
  0x00 f_u.fu_llist/rcu (freelist next when freed)   0x08 f_u rcu func
  0x10 f_path.mnt   0x18 f_path.dentry   0x20 f_inode   0x28 f_op
  0x30 f_lock+f_write_hint   0x38 f_count (refcount)
"""
from __future__ import annotations

import json
import os

from _workspace_bootstrap import add_legacy_revalidation_path, repo_root

REPO_ROOT = repo_root()
add_legacy_revalidation_path(REPO_ROOT)

from a90harness.evidence import (  # noqa: E402
    workspace_private_build_path,
    workspace_private_input_path,
    write_private_bytes,
    write_private_json,
)

import build_kernel_tier2_stage_c_direct_bl_printk as stage_c  # noqa: E402
import build_kernel_tier2_kasan_lite_reclaim_dump as kasan  # noqa: E402

CYCLE = "TIER2_FILP_RECLAIM_DUMP"
DECISION = "tier2-filp-reclaim-dump-source-build-pass"
BASE_BOOT_SHA256 = stage_c.BASE_BOOT_SHA256
BASE_BOOT = stage_c.BASE_BOOT
OUT_BOOT = workspace_private_input_path(
    "boot_images",
    "boot_linux_tier2_filp_reclaim_dump.img",
    legacy_fallback=False,
)
OUT_DIR = workspace_private_build_path("boot_images", "tier2-filp-reclaim-dump")

RESET_FILE_OFF = kasan.TASK_INTEGRITY_RESET_FILE_OFF  # 0x58 in task_integrity
TASK_INTEGRITY_OFF = kasan.PROC_RESET_TASK_INTEGRITY_OFF  # 0xb40 in task_struct
FILE_DUMP_LINES = (0x00, 0x20)  # each line dumps 4 qwords: off, +8, +0x10, +0x18

FORMAT = b"A90KF%d %llx %llx %llx %llx %llx\n\x00"


def encode_str_x_imm(rt: int, rn: int, imm: int) -> int:
    if imm % 8:
        raise RuntimeError(f"unaligned 64-bit STR offset: {imm}")
    imm12 = imm // 8
    if not 0 <= imm12 < (1 << 12):
        raise RuntimeError(f"64-bit STR offset out of range: {imm}")
    return 0xF9000000 | (imm12 << 10) | (rn << 5) | rt


def encode_cbz_x(rt: int, word_delta: int) -> int:
    # CBZ <Xt>, label ; imm19 = (target - pc) / 4 (here pc = this word)
    if not -(1 << 18) <= word_delta < (1 << 18):
        raise RuntimeError(f"CBZ branch out of range: {word_delta}")
    return 0xB4000000 | ((word_delta & 0x7FFFF) << 5) | rt


def build_filp_dump_injection(
    entry_off: int, next_magic_off: int, printk_entry_off: int
) -> tuple[bytes, int]:
    room = next_magic_off - entry_off
    code_words: list[int] = [
        stage_c.U32_EOR_PROLOGUE,            # 0 eor x16,x30,x17
        0xA9BE43FD,                          # 1 stp x29,x16,[sp,#-32]!
        0xF9000BF3,                          # 2 str x19,[sp,#16]
        encode_str_x_imm(20, 31, 24),        # 3 str x20,[sp,#24]
        0x910003FD,                          # 4 mov x29,sp
        kasan.encode_ldr_x_imm(19, 3, TASK_INTEGRITY_OFF),   # 5 x19 = task->integrity
        kasan.encode_ldr_x_imm(20, 19, RESET_FILE_OFF),      # 6 x20 = reset_file
        0,                                   # 7 cbz x20, skip  (patched below)
    ]

    adr_placeholders: list[int] = []
    bl_placeholders: list[int] = []
    for line_index, offset in enumerate(FILE_DUMP_LINES):
        adr_placeholders.append(len(code_words))
        bl_placeholders.append(len(code_words) + 5)
        code_words.extend([
            0,                               # ADR x0, format (patched)
            kasan.encode_mov_w_imm(1, line_index),
            kasan.encode_mov_x(2, 20),       # x2 = reset_file ptr
            kasan.encode_ldp_x(3, 4, 20, offset),
            kasan.encode_ldp_x(5, 6, 20, offset + 0x10),
            0,                               # BL printk (patched)
        ])

    skip_index = len(code_words)             # mov w0,wzr label
    # patch the cbz at word 7 to branch to skip_index
    code_words[7] = encode_cbz_x(20, skip_index - 7)

    code_words.extend([
        0x2A1F03E0,                          # skip: mov w0, wzr
        0xF9400BF3,                          # ldr x19,[sp,#16]
        kasan.encode_ldr_x_imm(20, 31, 24),  # ldr x20,[sp,#24]
        0xA8C243FD,                          # ldp x29,x16,[sp],#32
        stage_c.U32_EOR_EPILOGUE,            # eor x30,x16,x17
        stage_c.U32_RET,                     # ret
    ])

    code_len = len(code_words) * 4
    format_off = entry_off + code_len
    format_vaddr = stage_c.kernel_vaddr(format_off)
    entry_vaddr = stage_c.kernel_vaddr(entry_off)
    for word_index in adr_placeholders:
        site_vaddr = entry_vaddr + word_index * 4
        code_words[word_index] = stage_c.encode_adr_x0(site_vaddr, format_vaddr)
    for word_index in bl_placeholders:
        site_vaddr = entry_vaddr + word_index * 4
        code_words[word_index] = stage_c.encode_bl(site_vaddr, stage_c.kernel_vaddr(printk_entry_off))

    payload = b"".join(stage_c.put_u32(word) for word in code_words) + FORMAT
    while len(payload) % 4:
        payload += b"\x00"
    if len(payload) > room:
        raise RuntimeError(f"injection payload too large: {len(payload)} > {room}")
    payload += stage_c.put_u32(stage_c.U32_NOP) * ((room - len(payload)) // 4)
    return payload, format_off


def build_candidate() -> dict[str, object]:
    base_sha = stage_c.sha256_file(BASE_BOOT)
    if base_sha != BASE_BOOT_SHA256:
        raise RuntimeError(f"unexpected v2321 SHA256: {base_sha}")
    original = BASE_BOOT.read_bytes()
    patched = bytearray(original)
    layout = stage_c.parse_boot_layout(original)
    kernel = bytes(original[layout.kernel_off : layout.kernel_off + layout.kernel_size])
    if kernel[:16] != b"UNCOMPRESSED_IMG":
        raise RuntimeError("kernel wrapper is not UNCOMPRESSED_IMG")

    proc_magic_off, proc_entry_off, proc_next_magic_off = kasan.find_proc_integrity_reset_file(kernel)
    printk_magic_off, printk_entry_off, printk_va_helper_off, printk_emit_core_off = (
        stage_c.locate_printk_variadic_wrapper(kernel)
    )
    payload, format_off = build_filp_dump_injection(proc_entry_off, proc_next_magic_off, printk_entry_off)

    patch_abs_off = layout.kernel_off + proc_entry_off
    patched[patch_abs_off : patch_abs_off + len(payload)] = payload
    boot_id = stage_c.recompute_boot_id(patched, layout)
    diff_offsets = stage_c.changed_offsets(original, bytes(patched))
    allowed_kernel = set(range(patch_abs_off, patch_abs_off + len(payload)))
    allowed_id = set(range(stage_c.BOOT_ID_OFFSET, stage_c.BOOT_ID_OFFSET + stage_c.BOOT_ID_SIZE))
    unexpected = [off for off in diff_offsets if off not in allowed_kernel and off not in allowed_id]
    if unexpected:
        raise RuntimeError(f"unexpected patched offsets outside kernel/id contract: {unexpected[:8]}")

    write_private_bytes(OUT_BOOT, bytes(patched))
    os.chmod(OUT_BOOT, 0o600)
    out_sha = stage_c.sha256_file(OUT_BOOT)
    manifest = {
        "cycle": CYCLE,
        "decision": DECISION,
        "base_boot": str(BASE_BOOT.relative_to(REPO_ROOT)),
        "base_sha256": base_sha,
        "out_boot": str(OUT_BOOT.relative_to(REPO_ROOT)),
        "out_sha256": out_sha,
        "out_mode": oct(OUT_BOOT.stat().st_mode & 0o777),
        "boot_id": boot_id[:20].hex(),
        "diff_byte_count": len(diff_offsets),
        "diff_ranges": [[hex(start), hex(stop)] for start, stop in stage_c.contiguous_ranges(diff_offsets)],
        "proc_reset_entry_vaddr": hex(stage_c.kernel_vaddr(proc_entry_off)),
        "proc_reset_patch_room": proc_next_magic_off - proc_entry_off,
        "proc_reset_patch_len": len(payload),
        "reset_file_off_in_task_integrity": hex(RESET_FILE_OFF),
        "struct_file_layout": {
            "f_u": "0x0", "f_path.mnt": "0x10", "f_path.dentry": "0x18",
            "f_inode": "0x20", "f_op": "0x28", "f_lock+f_write_hint": "0x30",
            "f_count": "0x38",
        },
        "dump_lines": [hex(x) for x in FILE_DUMP_LINES],
        "format": FORMAT.decode("ascii").replace("\n", "\\n").replace("\x00", "\\0"),
        "format_vaddr": hex(stage_c.kernel_vaddr(format_off)),
        "printk_entry_vaddr": hex(stage_c.kernel_vaddr(printk_entry_off)),
        "control_flow": {
            "new_direct_bl": True,
            "bl_target": "plain-printk-variadic-wrapper-signature",
            "new_cbz": "forward direct conditional branch (NULL check), not JOPP-gated",
            "no_blr": True,
            "no_d_path_call": True,
            "no_dentry_or_fop_deref": True,
            "preserves_x17": True,
            "max_args_per_printk_call": 6,
            "stack_varargs": False,
        },
    }
    write_private_json(OUT_DIR / "manifest.json", manifest)
    return manifest


def main() -> int:
    manifest = build_candidate()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
