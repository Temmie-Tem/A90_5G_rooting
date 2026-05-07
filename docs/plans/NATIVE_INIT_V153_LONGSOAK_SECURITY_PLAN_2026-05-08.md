# Native Init v153 Longsoak Security Hardening Plan

Date: `2026-05-08`
Target: `A90 Linux init 0.9.53 (v153)` / `0.9.53 v153 LONGSOAK SECURITY`
Baseline: `A90 Linux init 0.9.52 (v152)`

## Summary

v153 should pause kernel-inventory feature work and first close the new longsoak
security findings from `docs/security/codex-security-findings-2026-05-07T20-00-44.982Z.csv`.

Scope:

- F034: `native_long_soak.py` trusts device-provided longsoak paths and runs unbounded `cat`.
- F035: `/bin/a90_longsoak` follows symlinks when appending root-owned JSONL logs.
- F036: `a90_longsoak_get_status()` treats display sentinel `-` as a real file path.
- F037: `native_long_soak_bundle.py` writes host evidence bundles without private file handling.

Policy:

- Keep longsoak as a monitoring feature.
- Do not broaden USB/NCM/tcpctl exposure.
- Do not introduce destructive filesystem operations.
- Prefer bounded, module-owned exports over host-side generic `cat`.

## Relationship

These are one issue family, not three unrelated bugs.

Root cause:

```text
longsoak runtime path contract
  -> PID1 stores recorder path in global state
  -> helper writes to that path as root
  -> status/tail scans that path
  -> host tooling asks for the path and cats it back
```

The missing boundary checks appear at three different trust transitions:

| finding | trust transition | current problem | fix direction |
|---|---|---|---|
| F035 | PID1 path -> root helper write | helper uses `fopen(path, "a")` and `chmod(path, 0600)`, following symlinks | no-follow `open`, `fstat` regular file, `fdopen`, `fchmod` |
| F036 | display sentinel -> status scanner | sentinel `-` is passed to `open()` as a path | keep unset path empty internally or reject `-`/relative paths before scan |
| F034 | device path -> host export | host trusts printed path and invokes unbounded `cat` | device-side `longsoak export` with path validation and size/line caps |
| F037 | host evidence -> local filesystem | bundle uses default-permission `mkdir`, `copy2`, and `write_text` | private bundle dir, no-follow/private writes, explicit copy |

The common patch target is to make `a90_longsoak` own recorder path validation,
bounded reads, and export semantics.

## Key Changes

### 1. Version and artifacts

- Copy v152 to `init_v153.c` and `v153/*.inc.c`.
- Bump `stage3/linux_init/a90_config.h` to:
  - `INIT_VERSION "0.9.53"`
  - `INIT_BUILD "v153"`
  - changelog marker `0.9.53 v153 LONGSOAK SECURITY`
- Produce `stage3/boot_linux_v153.img`.

### 2. Implementation sequence

Implement in this order so each stage has a small, testable boundary:

1. Commit the imported finding docs and this plan separately from code.
2. Patch host bundle private writes first because it does not require a boot image.
3. Patch longsoak helper safe output open and locally build/run the helper against symlink PoC paths.
4. Patch `a90_longsoak.c` path validation and add bounded `longsoak export`.
5. Patch `native_long_soak.py` to consume `longsoak export` instead of `cat <device_path>`.
6. Add local rescan assertions for F034-F037.
7. Bump v153 source/ramdisk/boot image.
8. Flash and run real-device longsoak/report/bundle regression.
9. Mark F034-F037 as `mitigated-v153`, write report, update task queue/latest verified, commit.

### 3. Host bundle private output

Patch `scripts/revalidation/native_long_soak_bundle.py` before changing device code:

- Add `ensure_private_dir(path)`:
  - `mkdir(parents=True, mode=0o700, exist_ok=True)`
  - `chmod(0o700)`
  - reject if path exists and is not a directory.
- Add `write_private_text(path, text)`:
  - reject destination symlink with `lstat()`;
  - open with `os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_CLOEXEC`;
  - add `os.O_NOFOLLOW` when available;
  - write via `os.fdopen()`;
  - final `chmod(0o600)`.
- Add `copy_private_regular_file(source, dest)`:
  - source must be an existing regular file;
  - destination must not be a symlink;
  - read bytes from source and write destination with `0600`;
  - preserve no metadata that would weaken permissions.
- Replace:
  - `bundle_dir.mkdir(...)` with `ensure_private_dir(bundle_dir)`;
  - `shutil.copy2(...)` with `copy_private_regular_file(...)`;
  - every `Path.write_text(...)` under bundle output with `write_private_text(...)`.

Local validation:

```bash
python3 -m py_compile scripts/revalidation/native_long_soak_bundle.py
umask 022
python3 scripts/revalidation/native_long_soak_bundle.py --timeout 1 --bundle-dir tmp/soak/private-bundle-smoke || true
stat -c '%a %n' tmp/soak/private-bundle-smoke tmp/soak/private-bundle-smoke/README.md tmp/soak/private-bundle-smoke/manifest.json
```

Expected:

- directory mode `700`;
- output files mode `600`;
- no destination symlink is followed.

### 4. Safe longsoak helper output open

Patch `stage3/linux_init/helpers/a90_longsoak.c`:

- Add `open_output_file(path)` helper:
  - `open(path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC | O_NOFOLLOW, 0600)`;
  - `fstat(fd, &st)`;
  - require `S_ISREG(st.st_mode)`;
  - `fchmod(fd, 0600)`;
  - return fd or negative error.
- Replace `fopen(path, "a")` and `chmod(path, 0600)` with:
  - `fd = open_output_file(path)`;
  - `file = fdopen(fd, "a")`;
  - close fd on error.
- Keep append semantics and JSONL format unchanged.

Local validation:

```bash
gcc -O2 -Wall -Wextra -o /tmp/a90_longsoak_host stage3/linux_init/helpers/a90_longsoak.c
tmpdir=$(mktemp -d)
mkdir -p "$tmpdir/logs"
echo victim > "$tmpdir/victim"
ln -s ../victim "$tmpdir/logs/longsoak-test.jsonl"
timeout 2 /tmp/a90_longsoak_host "$tmpdir/logs/longsoak-test.jsonl" 1 test; test $? -ne 0
test "$(cat "$tmpdir/victim")" = victim
```

Expected:

- symlink target is not appended/chmodded;
- normal regular-file path still records JSONL.

### 5. Device longsoak path validation and export

Patch `stage3/linux_init/a90_longsoak.c`:

- Add a single internal validator used by scan/tail/export:
  - no empty path;
  - no `-` sentinel;
  - absolute path only;
  - prefix under current runtime log dir or fallback log dir;
  - basename starts with `longsoak-` and ends with `.jsonl`.
- Add `longsoak_open_log_readonly()`:
  - `open(..., O_RDONLY | O_CLOEXEC | O_NOFOLLOW)`;
  - `fstat()` regular-file validation.
- Route `longsoak_scan_file()` and `a90_longsoak_tail()` through the safe opener.
- Add `a90_longsoak_export(max_lines, max_bytes)`:
  - bounded read;
  - default line/byte caps;
  - hard maximum caps;
  - print JSONL records only;
  - print final `longsoak: export path=... lines=... bytes=... truncated=...`.
- Extend `a90_longsoak_cmd()` usage:
  - `longsoak [status [verbose]|start [interval]|stop|path|tail [lines]|export [max_lines] [max_bytes]]`.

Real-device validation:

```bash
python3 scripts/revalidation/a90ctl.py longsoak status verbose
python3 scripts/revalidation/a90ctl.py longsoak start 2
sleep 6
python3 scripts/revalidation/a90ctl.py longsoak export 1000 1048576
python3 scripts/revalidation/a90ctl.py longsoak stop
```

Expected:

- pre-start status does not open `-`;
- export is bounded and parseable;
- no unbounded generic `cat` is needed.

### 6. Host longsoak exporter

Patch `scripts/revalidation/native_long_soak.py`:

- Keep `longsoak path` as metadata only.
- Remove `record_command(..., ["cat", device_path])`.
- Add CLI options:
  - `--device-export-max-lines` default `200000`;
  - `--device-export-max-bytes` default `16777216`.
- Export with:
  - `["longsoak", "export", str(max_lines), str(max_bytes)]`.
- Extract JSONL records from export output.
- Parse the `longsoak: export ... truncated=...` summary and include it in `summary_json`.
- Treat missing export summary as failure.

Acceptance for F034:

- `rg -n '\\[\"cat\", device_path\\]|cat <device_path>' scripts/revalidation/native_long_soak.py` returns no active code hit.
- Host exporter cannot be redirected to arbitrary device paths by forged `longsoak path`.

### 7. Local rescan assertions

Patch `scripts/revalidation/local_security_rescan.py`:

- Add F034 check:
  - no active `["cat", device_path]` in `native_long_soak.py`;
  - `longsoak export` is used.
- Add F035 check:
  - helper has `O_NOFOLLOW`, `fstat`, `S_ISREG`, `fchmod`, `fdopen`.
- Add F036 check:
  - longsoak scan/open rejects `"-"` and non-absolute paths.
- Add F037 check:
  - bundle script has private writer helpers;
  - no active `shutil.copy2`;
  - no active bundle `Path.write_text`;
  - `chmod(0o700)` and `chmod(0o600)` present.

### 8. Version/report/docs

After real-device validation:

- Update F034-F037 finding status to `mitigated-v153`.
- Add `docs/reports/NATIVE_INIT_V153_LONGSOAK_SECURITY_2026-05-08.md`.
- Add `docs/security/SECURITY_FRESH_SCAN_V153_2026-05-08.md`.
- Update `README.md` and `docs/plans/NATIVE_INIT_TASK_QUEUE_2026-04-25.md` latest verified from v152 to v153.

### 9. Safe longsoak path handling

Add internal path helpers in `stage3/linux_init/a90_longsoak.c`:

- `longsoak_has_recorder_path()`
- `longsoak_path_is_display_sentinel()`
- `longsoak_path_is_absolute()`
- `longsoak_path_has_expected_shape()`
- `longsoak_open_log_readonly()`

Rules:

- Empty path means no recorder path.
- `-` is display-only and must never be passed to `open()`.
- Relative paths are invalid.
- Recorder path must be under the active runtime log directory or fallback log directory.
- Recorder filename must follow `longsoak-*.jsonl`.
- Reads must use `open(..., O_RDONLY | O_CLOEXEC | O_NOFOLLOW)` and `fstat()` regular-file validation.

### 10. Safe helper write

Patch `stage3/linux_init/helpers/a90_longsoak.c`:

- Replace `fopen(path, "a")` with:
  - `open(path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC | O_NOFOLLOW, 0600)`
  - `fstat(fd, ...)`
  - reject non-regular files
  - `fchmod(fd, 0600)`
  - `fdopen(fd, "a")`
- Keep helper argv contract unchanged: `/bin/a90_longsoak <path> <interval_sec> <session>`.

### 11. Bounded device-side export

Add a `longsoak export [max_lines] [max_bytes]` subcommand in `a90_longsoak.c`.

Behavior:

- Uses the same validated recorder path as status/tail.
- Defaults should cover normal 8h/24h runs without unbounded output.
- Hard caps prevent serial/host exhaustion.
- Output only JSONL records plus a final export summary line:

```text
longsoak: export path=... lines=N bytes=N truncated=no
```

If truncated, return success but print `truncated=yes` so host reports can flag
partial evidence without hanging.

### 12. Host exporter hardening

Patch `scripts/revalidation/native_long_soak.py`:

- Stop sending `cat <device_path>` from parsed device output.
- Use `longsoak export <max_lines> <max_bytes>` instead.
- Keep `longsoak path` only as metadata, not as a host-selected read target.
- Add host-side sanity checks:
  - exported records must be JSON objects;
  - output must contain a `longsoak: export` summary;
  - truncated export should be recorded in summary JSON.

### 13. Regression checks

Update `scripts/revalidation/local_security_rescan.py` with checks for:

- F034: `native_long_soak.py` does not issue `["cat", device_path]`.
- F035: helper uses `O_NOFOLLOW`, `fstat`, regular-file check, and `fchmod`.
- F036: `longsoak_scan_file()` rejects empty, `-`, and non-absolute paths.
- F037: `native_long_soak_bundle.py` does not use `Path.write_text()` or `shutil.copy2()` for bundle outputs and forces `0700`/`0600` output modes.

Update finding files after implementation:

- F034 status -> `mitigated-v153`
- F035 status -> `mitigated-v153`
- F036 status -> `mitigated-v153`
- F037 status -> `mitigated-v153`

### 14. Private host bundle output

Patch `scripts/revalidation/native_long_soak_bundle.py`:

- Add host-side helpers equivalent to the private output pattern in `diag_collect.py`.
- Force the bundle directory to mode `0700`.
- Write command transcript files, `manifest.json`, and `README.md` with private mode `0600`.
- Avoid destination symlink following with `os.open()` and `O_NOFOLLOW` where available.
- Replace `shutil.copy2()` with explicit source read and private destination write.
- Reject source directories and destination symlinks.

## Validation

Static:

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_long_soak.py \
  scripts/revalidation/native_long_soak_report.py \
  scripts/revalidation/native_long_soak_bundle.py \
  scripts/revalidation/local_security_rescan.py
```

Build:

```bash
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra \
  -o stage3/linux_init/helpers/a90_longsoak \
  stage3/linux_init/helpers/a90_longsoak.c
```

Then build `init_v153` with the same module list as v152 and include the updated helper in the v153 ramdisk.

Real-device:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v153.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.53 (v153)" \
  --verify-protocol auto
```

Regression:

```bash
python3 scripts/revalidation/a90ctl.py longsoak status verbose
python3 scripts/revalidation/a90ctl.py longsoak start 2
python3 scripts/revalidation/a90ctl.py longsoak export 1000 1048576
python3 scripts/revalidation/a90ctl.py longsoak stop
python3 scripts/revalidation/native_long_soak.py --duration-sec 10 --device-interval 2 --start-device
python3 scripts/revalidation/native_long_soak_report.py
python3 scripts/revalidation/native_long_soak_bundle.py
python3 scripts/revalidation/local_security_rescan.py --out docs/security/SECURITY_FRESH_SCAN_V153_2026-05-08.md
```

Acceptance:

- `longsoak status` before recorder start does not try to open `-`.
- Symlinked recorder target is rejected by helper and does not receive root writes.
- Host longsoak export no longer sends generic `cat <device_path>`.
- Longsoak bundle output directory is `0700`; bundle files are `0600` and do not follow destination symlinks.
- 10-second longsoak/report/bundle still PASS.
- Local security rescan reports F034/F035/F036/F037 mitigations.

## Follow-up

After v153 is verified, return to the previously selected candidate:

- v154: Kernel Capability Inventory, covering `/proc/config.gz`, pstore, tracefs, watchdog, cgroup, thermal, power_supply, and USB gadget state.
