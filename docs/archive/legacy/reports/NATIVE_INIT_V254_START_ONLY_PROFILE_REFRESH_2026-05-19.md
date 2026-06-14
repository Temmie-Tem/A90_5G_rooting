# Native Init V254 CNSS Start-Only Profile Refresh Report

## Summary

- Status: PASS
- Decision: `start-only-profile-refresh-pass`
- Scope: host tooling profile refresh only
- Device build: `A90 Linux init 0.9.59 (v159)`
- Helper: `a90_android_execns_probe v9`
- Helper SHA-256: `80e8afb1b77fdba23dfbc71d6a8e17e5a2a095ed1de728474fd2855923c351a1`
- Daemon start: not executed

## Change

- Updated `scripts/revalidation/wifi_cnss_start_only_runner.py` start-only profile:
  - `--null-device-mode dev-null-selinux`
  - `--data-wifi-mode private-empty`
- Added dry-run metadata for the private runtime materialization profile.
- Preserved the existing approval gate:
  - `--allow-cnss-start-only` is appended only for `run` with all explicit approval flags.
  - default `run` without approval remains fail-closed.

## Static Validation

- `python3 -m py_compile scripts/revalidation/wifi_cnss_start_only_runner.py`: PASS
- `git diff --check`: PASS
- `rg` confirmed the runner and plan include:
  - `dev-null-selinux`
  - `--data-wifi-mode`
  - `private-empty`
  - `runtime_materialization`

## Safe Runner Validation

Output directories:

- `tmp/wifi/v254-start-only-profile-plan/`
- `tmp/wifi/v254-start-only-profile-preflight/`
- `tmp/wifi/v254-start-only-profile-dryrun/`
- `tmp/wifi/v254-start-only-profile-run-blocked/`

Results:

| mode | decision | pass | daemon_start_executed |
| --- | --- | --- | --- |
| `plan` | `dry-run-ready` | `True` | `False` |
| `preflight` | `preflight-ready` | `True` | `False` |
| `dry-run` | `preflight-ready` | `True` | `False` |
| default `run` without approval | `start-only-blocked` | `False` | `False` |

Dry-run plan runtime materialization:

```text
null_device_mode=dev-null-selinux
data_wifi_mode=private-empty
data_wifi_path=/data/vendor/wifi
data_wifi_sockets_path=/data/vendor/wifi/sockets
private_namespace_only=True
```

## Helper No-Allow Validation

Command profile:

```text
run /cache/bin/a90_android_execns_probe --system-root /mnt/system/system --vendor-block /dev/block/sda29 --vendor-fstype ext4 --mode cnss-start-only --null-device-mode dev-null-selinux --vndk-apex-alias-mode v30-to-current --linkerconfig-mode copy-real --linkerconfig-source /cache/bin/a90_real_ld.config.txt --apex-libraries-source /cache/bin/a90_real_apex.libraries.config.txt --data-wifi-mode private-empty --timeout-sec 10
```

Important evidence:

```text
null_device_mode=dev-null-selinux
data_wifi_mode=private-empty
context.selinux_null.exists=1
context.selinux_null.rdev=1:3
context.data_vendor_wifi.exists=1
context.data_vendor_wifi.uid=1000
context.data_vendor_wifi.gid=1010
context.data_vendor_wifi.mode=770
context.data_vendor_wifi_sockets.exists=1
context.data_vendor_wifi_sockets.uid=1000
context.data_vendor_wifi_sockets.gid=1010
context.data_vendor_wifi_sockets.mode=770
cnss_start.allowed=0
cnss_start.exec_attempted=0
cnss_start.child_started=0
cnss_start.postflight_safe=1
cnss_start.result=start-only-blocked
cnss_start.reason=missing-allow-cnss-start-only
```

Post-check:

```text
cmdv1 run /cache/bin/toybox pidof cnss-daemon
rc=1
```

## Interpretation

- V254 closes the runner-profile drift between the latest no-start probes and the future start-only review path.
- The candidate profile now includes both known private runtime shims:
  - SELinux null device compatibility shim.
  - Private `/data/vendor/wifi/sockets` runtime tree.
- The runner still does not start `cnss-daemon` without explicit operator approval and dangerous flags.
- The real Android `/data/vendor/wifi` path is not created or modified by this validation.

## Next

- Either perform a first bounded live start-only operator approval review, or
- Run one more no-start checklist review that freezes the live profile and rollback procedure.

Live Wi-Fi daemon execution remains blocked until explicitly approved.
