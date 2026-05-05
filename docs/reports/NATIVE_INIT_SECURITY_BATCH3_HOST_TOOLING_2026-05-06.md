# A90 Native Init Security Batch 3 Host Tooling

Date: 2026-05-06
Device baseline: `A90 Linux init 0.9.24 (v124)`
Scope: host tooling only; no native init version bump.

## Summary

Security Batch 3 hardens the host-side tooling trust boundary around the native
init control path. The changes reduce accidental or malicious execution from an
untrusted host CWD, prevent unsafe cmdv1 replay and framed-result spoofing,
require explicit host NIC selection before sudo NCM setup, pin serial bridge
identity across re-enumeration, quote ADB remote shell paths, and remove shared
predictable temporary-file usage.

## Changes

- `a90ctl.py`
  - Retries only read-only observation commands by default.
  - Requires `--retry-unsafe` for non-observation command retry.
  - Reads through the real cmdv1 trailer prompt and parses the last `A90P1 END`.
  - Correlates `BEGIN`/`END` by `seq` and `cmd` where both markers are present.
- `native_soak_validate.py`
  - Resolves `a90ctl.py` from `__file__` and runs subprocesses with `cwd=REPO_ROOT`.
  - Updates default expected version to the current v124 baseline.
- `ncm_host_setup.py` and `netservice_reconnect_soak.py`
  - Require `--interface <ifname>` for sudo host NIC configuration by default.
  - Provide `--allow-auto-interface` only for explicit operator opt-in to MAC-based auto selection.
  - Validate interface names and reject nonexistent or unsafe names.
- `serial_tcp_bridge.py`
  - Pins the first resolved serial realpath by default.
  - Supports `--expect-realpath` for strict device identity.
  - Refuses ambiguous `--device=auto` matches unless explicitly allowed.
- `native_init_flash.py`
  - Quotes and validates remote ADB shell paths used in `sha256sum` and `dd` commands.
  - Logs host command lines with `shlex.join()`.
- `build_static_busybox.sh`
  - Uses `mktemp` and a cleanup trap for dynamic-section validation output.
- `capture_baseline.sh`
  - Validates device-discovered `by_name` path before using it in `su -c` commands.

## Finding Coverage

| finding | result |
|---|---|
| F008 | Mitigated: soak validator uses absolute repo-resolved `a90ctl.py` and `cwd=REPO_ROOT`. |
| F015 | Mitigated: unsafe cmdv1 commands are not retried by default; retry requires either a safe command name or explicit `--retry-unsafe`. |
| F016 | Mitigated: host parser waits past injected END-like output and accepts the real trailer correlated with prompt/sequence. |
| F017 | Mitigated: reconnect soak refuses sudo NIC setup from device-reported MAC unless `--interface` or explicit auto opt-in is provided. |
| F018 | Mitigated: NCM host setup refuses sudo NIC setup from device-reported MAC unless `--interface` or explicit auto opt-in is provided. |
| F019 | Mitigated: serial bridge pins resolved serial identity and rejects ambiguous auto matches by default. |
| F020 | Mitigated: remote image and boot block arguments are absolute-path checked and shell-quoted before `adb shell`. |
| F022 | Mitigated: BusyBox validation uses a private `mktemp` file instead of predictable `/tmp/a90_busybox_dynamic_check.txt`. |
| F031 | Mitigated: `by_name` must be a safe `/dev/block/.../by-name` path before later root shell use. |

## Validation

### Static

- `python3 -m py_compile` for host control scripts — PASS.
- `bash -n scripts/revalidation/build_static_busybox.sh scripts/revalidation/capture_baseline.sh` — PASS.
- `git diff --check` — PASS.
- CLI help smoke for `a90ctl.py`, `ncm_host_setup.py`, `netservice_reconnect_soak.py`, `serial_tcp_bridge.py` — PASS.

### Live Bridge Checks

- `python3 scripts/revalidation/a90ctl.py --json version` — PASS, returns v124 with `rc=0 status=ok`.
- `python3 scripts/revalidation/native_init_flash.py --verify-only --expect-version "A90 Linux init 0.9.24 (v124)" --verify-protocol auto` — PASS.
- `python3 scripts/revalidation/netservice_reconnect_soak.py status` — PASS with netservice disabled and ACM-only usbnet status.
- `python3 scripts/revalidation/ncm_host_setup.py status` — PASS with ACM-only status and no host sudo operation.

### Targeted Regression Checks

- cmdv1 spoof regression — PASS. A child command printed a forged `A90P1 END seq=999 ... status=ok`; `a90ctl.py` returned the real trailer `seq=31 cmd=run rc=0 status=ok`.
- Host NIC fail-closed unit check — PASS. Both `ncm_host_setup.select_host_interface()` and `netservice_reconnect_soak.select_host_interface()` refuse MAC-based sudo target selection unless `--interface` or `--allow-auto-interface` is supplied.

## Notes

- Batch 3 is host-tooling only. The latest verified device image remains `A90 Linux init 0.9.24 (v124)`.
- Full NCM start/stop soak was not repeated in this batch because the changed default intentionally requires explicit host interface selection before sudo configuration.
- Operators should now pass `--interface <enx...>` for normal NCM host setup, or `--allow-auto-interface` only in trusted single-device lab conditions.
