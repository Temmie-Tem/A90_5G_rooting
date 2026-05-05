# A90 Native Init Security Batch 5 Legacy Tooling

Date: 2026-05-06
Scope: host/rootfs legacy tooling; no native init image bump.
Latest verified device image remains: `A90 Linux init 0.9.25 (v125)`.

## Summary

Batch 5 mitigates the remaining high-impact legacy/host-tooling findings: default
root SSH credentials in archived rootfs automation and unsafe archive extraction
in GKI boot image certification tooling. These changes do not alter the native
PID1 runtime or boot image.

## Changes

- Changed archived rootfs creation to keep `PermitRootLogin prohibit-password`, set `PasswordAuthentication no`, and lock the root password instead of setting `root:root`.
- Removed user-facing default-password guidance from archived rootfs output and boot logs.
- Kept archived boot-time `sshd` startup behavior, but connection guidance now states key-based auth instead of a static password.
- Replaced unfiltered `shutil.unpack_archive()` in `certify_bootimg.py` with safe tar/zip extraction that rejects absolute paths, traversal, links, and non-regular archive members.
- Added regular-file checks before `certify_bootimg()` reads/writes boot image paths, preventing archive-provided symlink `boot*.img` overwrite primitives.

## Finding Coverage

| finding | result |
|---|---|
| F006 | Mitigated: archived automation no longer sets or advertises a hardcoded root password; password SSH auth is disabled. |
| F007 | Mitigated: boot image archive extraction rejects traversal/link/special entries and boot image processing refuses symlink/non-regular paths. |

## Validation

- `rg` over `scripts/archive/legacy` for `root:root`, `password: root`, `PermitRootLogin yes`, `PasswordAuthentication yes`, and old default-password Korean guidance — PASS, no matches.
- `bash -n` for modified legacy shell scripts and headless boot wrapper — PASS.
- `python3 -m py_compile mkbootimg/gki/certify_bootimg.py` — PASS.
- Direct safe extraction checks for malicious tar traversal and tar symlink entries — PASS, both rejected.
- Direct safe extraction checks for malicious zip traversal and zip symlink entries — PASS, both rejected.
- `git diff --check` — PASS.

## Notes

- F006 lives in archived legacy automation, not the current native init runtime. The fix keeps the archive safer if reused.
- F007 is active host tooling. The fix is fail-closed for unsafe archive members and intentionally rejects links/special files rather than trying to sanitize them.
