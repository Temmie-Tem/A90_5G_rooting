# F038. Weak fs exerciser path guard can delete outside test dir

## Metadata

| field | value |
|---|---|
| finding_id | `5a5ce4100f888191b552a392a8fce1e0` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/5a5ce4100f888191b552a392a8fce1e0 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-08T18:19:20.715142Z` |
| committed_at | `2026-05-09 02:04:35 +0900` |
| commit_hash | `6f254fbe78888d7197a0bb29a4d5cd597379b12a` |
| relevant_paths | `docs/plans/NATIVE_INIT_V167_FS_EXERCISER_PLAN_2026-05-09.md` <br> `scripts/revalidation/fs_exerciser_mini.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

The v167 fs exerciser is intended to confine all writes and cleanup to `/mnt/sdext/a90/test-fsx/<run-id>`, but the new validation only checks `path.startswith("/mnt/sdext/a90/test-fsx")` and simple `..` substrings. This accepts paths like `/mnt/sdext/a90/test-fsx-other` that are not under the intended directory, and it does not require `--run-id` to be a single safe path component. Values such as `--run-id .` are accepted, causing `args.run_root` to refer to the test root itself rather than a run-owned subdirectory. The script then sends root commands to the device and performs `rm -rf args.run_root` during cleanup. In an automation or shared-lab scenario where an attacker can influence CLI parameters, or where an accepted `test-fsx*` path is a symlink to another on-device directory, this can redirect root writes and destructive cleanup outside the promised test-owned directory. This primarily threatens device filesystem integrity/availability rather than remote code execution.

## Local Initial Assessment

- Valid class: host-side validator uses weak prefix checks before issuing root-side filesystem operations.
- Related to F041: both need strict safe component and POSIX path boundary validation before command construction.
- Treat as a mixed-soak blocker because cleanup uses `rm -rf` on the computed run root.

## Local Remediation

- Planned Batch A fix.
- Require `--run-id` to be one safe path component, not `.`, `..`, or a path.
- Normalize device paths and require exact root or `root + "/"` boundary, not string prefix.
- Ensure cleanup target is a run-owned child under `/mnt/sdext/a90/test-fsx`, never the test root itself.

## Codex Cloud Detail

Weak fs exerciser path guard can delete outside test dir
Link: https://chatgpt.com/codex/cloud/security/findings/5a5ce4100f888191b552a392a8fce1e0?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 6f254fb
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:19:20
Assignee: Unassigned
Signals: Security

# Summary
Introduced: the newly added `scripts/revalidation/fs_exerciser_mini.py` implements an insufficient device path guard and then uses the guarded path in root-level create/write/rename/unlink and cleanup operations.
The v167 fs exerciser is intended to confine all writes and cleanup to `/mnt/sdext/a90/test-fsx/<run-id>`, but the new validation only checks `path.startswith("/mnt/sdext/a90/test-fsx")` and simple `..` substrings. This accepts paths like `/mnt/sdext/a90/test-fsx-other` that are not under the intended directory, and it does not require `--run-id` to be a single safe path component. Values such as `--run-id .` are accepted, causing `args.run_root` to refer to the test root itself rather than a run-owned subdirectory. The script then sends root commands to the device and performs `rm -rf args.run_root` during cleanup. In an automation or shared-lab scenario where an attacker can influence CLI parameters, or where an accepted `test-fsx*` path is a symlink to another on-device directory, this can redirect root writes and destructive cleanup outside the promised test-owned directory. This primarily threatens device filesystem integrity/availability rather than remote code execution.

# Evidence
docs/plans/NATIVE_INIT_V167_FS_EXERCISER_PLAN_2026-05-09.md (L44 to 50)
  Note: The plan states the security guardrails: device paths must remain under the fsx test directory and cleanup must remove only the run-owned directory.
```
## Guardrails

- device path must stay under `/mnt/sdext/a90/test-fsx`.
- no raw block access.
- no Android/EFS/modem/bootloader/key/security path writes.
- cleanup removes only the run-owned directory.
- host evidence files use private directory/file permissions and reject symlink destinations.
```

scripts/revalidation/fs_exerciser_mini.py (L113 to 125)
  Note: The path guard is only a lexical prefix check and simple `..` substring check; it accepts sibling prefixes such as `test-fsx-other` and does not normalize or verify real device paths.
```
def validate_test_root(path: str) -> None:
    if not path.startswith("/mnt/sdext/a90/test-fsx"):
        raise RuntimeError(f"refusing test root outside /mnt/sdext/a90/test-fsx*: {path}")
    if "//" in path or "/../" in path or path.endswith("/.."):
        raise RuntimeError(f"unsafe test root: {path}")


def validate_device_path(path: str, root: str) -> None:
    root = root.rstrip("/")
    if path != root and not path.startswith(root + "/"):
        raise RuntimeError(f"refusing path outside test root: {path}")
    if "/../" in path or path.endswith("/.."):
        raise RuntimeError(f"unsafe device path: {path}")
```

scripts/revalidation/fs_exerciser_mini.py (L241 to 247)
  Note: `args.run_root` is built directly from user-controlled `--test-root` and `--run-id`; special run IDs like `.` are not rejected before the path is accepted.
```
def main() -> int:
    args = parse_args()
    validate_test_root(args.test_root)
    args.run_root = posixpath.join(args.test_root, args.run_id)
    validate_device_path(args.run_root, args.test_root)
    out_dir = Path(args.out_dir) / args.run_id
    ensure_private_dir(out_dir)
```

scripts/revalidation/fs_exerciser_mini.py (L331 to 343)
  Note: Cleanup executes root-level `rm -rf` against `args.run_root`, so any path-guard bypass or unsafe run ID becomes a destructive device operation.
```
    if not args.keep_device_files:
        ok, cleanup_text, cleanup_rc, cleanup_status = run_cmd(
            args,
            ["run", args.toybox, "rm", "-rf", args.run_root],
            retry_unsafe=True,
            allow_error=True,
        )
        cleanup_ok = ok
        records.append(record(args.ops + len(final_verify) + 1, "cleanup", args.run_root, None, None, ok, f"rm rc={cleanup_rc} status={cleanup_status}\n{cleanup_text}"))
        ok, stat_text, stat_rc, stat_status = run_cmd(args, ["stat", args.run_root], allow_error=True)
        removed = not ok
        cleanup_ok = cleanup_ok and removed
        records.append(record(args.ops + len(final_verify) + 2, "cleanup-verify", args.run_root, None, None, removed, f"stat rc={stat_rc} status={stat_status}\n{stat_text}"))
```
