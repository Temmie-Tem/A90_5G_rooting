# Native Init v153 Longsoak Security Report

Date: `2026-05-08`
Version: `A90 Linux init 0.9.53 (v153)` / `0.9.53 v153 LONGSOAK SECURITY`
Baseline: `A90 Linux init 0.9.52 (v152)`

## Summary

- Mitigated F034-F037 longsoak export/helper/status/bundle findings.
- Replaced host-side `cat <device_path>` export with bounded device-owned `longsoak export [max_lines] [max_bytes]`.
- Hardened `/bin/a90_longsoak` root log output with no-follow open, regular-file validation, and fd-based chmod.
- Hardened host long-soak bundle output with private `0700` directories, `0600` files, regular source checks, and symlink destination rejection.
- Kept longsoak recorder/report/bundle behavior compatible for normal operator workflows.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v153` | `3032ede7949c3feb614361f7f9331f9f85d001eb60b9a1ea6ee8268198532252` |
| `stage3/linux_init/helpers/a90_longsoak` | `cb1d992c4da7cf0a15d8012ca0964ac63291d128b322f0e00a23718445d8bf43` |
| `stage3/ramdisk_v153.cpio` | `4142cbf52b9fcc5da53023f5495d48f5a4b03eca9794aeb550d31f7ff8a2de93` |
| `stage3/boot_linux_v153.img` | `659e2206bef6deee7ca64f6a7cac2fb5d9b53bb196fecfa4820595643a00836c` |

## Validation

- Static ARM64 build for `init_v153` and updated `a90_longsoak` helper — PASS.
- Boot image marker checks for `A90 Linux init 0.9.53 (v153)`, `A90v153`, and `0.9.53 v153 LONGSOAK SECURITY` — PASS.
- `git diff --check` and host Python `py_compile` — PASS.
- Real-device flash with `native_init_flash.py` and cmdv1 version/status verify — PASS.
- Longsoak no-recorder `status verbose` does not scan `-` and reports path `-` safely — PASS.
- Manual `hide -> longsoak start 2 -> longsoak export 1000 1048576 -> longsoak stop` — PASS.
- `native_long_soak.py --duration-sec 10 --device-interval 2 --start-device` — `PASS samples=9 failures=0`.
- `native_long_soak_report.py` — `PASS host_events=9 device_samples=6`.
- `native_disconnect_classify.py` — classification `serial-ok-ncm-down-or-inactive`, version checks PASS.
- `native_long_soak_bundle.py` — `PASS bundle=tmp/soak/native-long-soak-v153-bundle missing=0 failed_commands=0`.
- `native_integrated_validate.py` — `PASS commands=25`.
- `native_soak_validate.py --expect-version "A90 Linux init 0.9.53 (v153)" --cycles 3` — `PASS cycles=3 commands=14`.
- Local targeted security rescan — PASS=21/WARN=1/FAIL=0.

## Security Regression Checks

- Helper symlink PoC: symlinked `longsoak-test.jsonl` was rejected with `Too many levels of symbolic links`; victim content stayed unchanged — PASS.
- Helper regular-file path: output file mode `0600`, JSONL start/sample records written normally — PASS.
- Bundle private mode: bundle directory `0700`, `README.md`, `manifest.json`, and command transcript files `0600` — PASS.
- Bundle destination symlink PoC: pre-created `cmd-version.txt` symlink was rejected and target content stayed unchanged — PASS.
- Host export guard: `native_long_soak.py` no longer issues `cat <device_path>`; it records path as metadata and uses bounded `longsoak export` — PASS.

## Finding Status

- F034 `Unvalidated device path triggers unbounded host cat` — `mitigated-v153`.
- F035 `Longsoak helper follows symlinks when writing root logs` — `mitigated-v153`.
- F036 `Longsoak status treats '-' sentinel as a file path` — `mitigated-v153`.
- F037 `Long-soak bundle writes evidence without private file handling` — `mitigated-v153`.

## Notes

- `longsoak export` is still routed through the shell command policy, so host automation sends `hide` before export when the menu is visible.
- The remaining local security warning is the accepted trusted-lab USB ACM/local serial root-control boundary.
- NCM was inactive during the disconnect classifier run, so `ncm_ping` failed as expected for the `serial-ok-ncm-down-or-inactive` classification.
