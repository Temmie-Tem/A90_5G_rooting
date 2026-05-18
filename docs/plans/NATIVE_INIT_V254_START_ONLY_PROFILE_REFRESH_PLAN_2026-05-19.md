# Native Init V254 CNSS Start-Only Profile Refresh Plan

## Summary

- V254 is a host-tooling refresh, not a boot image change.
- Goal: update the guarded CNSS start-only runner profile to use the latest no-start namespace primitives proven by V249 and V253.
- The runner must keep live daemon execution approval-gated.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing is allowed in this step.

## Baseline

- Latest native device build remains `A90 Linux init 0.9.59 (v159)`.
- Latest helper is `a90_android_execns_probe v9`.
- Helper SHA-256: `80e8afb1b77fdba23dfbc71d6a8e17e5a2a095ed1de728474fd2855923c351a1`.
- V249 proved `--null-device-mode dev-null-selinux` can be materialized inside the private namespace without executing CNSS.
- V253 proved `--data-wifi-mode private-empty` can materialize private `/data/vendor/wifi/sockets` as `system:wifi` mode `0770`, while real `/data/vendor/wifi` remains absent.

## Key Changes

- Update `scripts/revalidation/wifi_cnss_start_only_runner.py` default helper argv:
  - `--null-device-mode dev-null-selinux`
  - `--data-wifi-mode private-empty`
- Keep existing namespace support:
  - `--vndk-apex-alias-mode v30-to-current`
  - `--linkerconfig-mode copy-real`
  - real linkerconfig source files under `/cache/bin`.
- Extend dry-run plan metadata so reviewers can see the exact private runtime materialization profile.
- Remove duplicate `helper_result` key in start observation construction.
- Preserve live-run guardrails:
  - `run` may append `--allow-cnss-start-only` only when all explicit approval flags are present.
  - default `run` without approval must remain fail-closed.

## Validation

- Static checks:
  - `python3 -m py_compile scripts/revalidation/wifi_cnss_start_only_runner.py`
  - `git diff --check`
- Safe host/device checks only:
  - `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v254-start-only-profile-plan plan`
  - `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v254-start-only-profile-preflight preflight`
  - `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v254-start-only-profile-dryrun dry-run`
  - `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v254-start-only-profile-run-blocked run`
  - `python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon`
- Expected results:
  - plan/preflight/dry-run produce no daemon execution.
  - default run is blocked without approval and `exec_attempted=0`.
  - helper argv includes `dev-null-selinux` and `private-empty`.
  - `pidof cnss-daemon` remains rc=1 after validation.

## Acceptance

- Decision: `start-only-profile-refresh-pass`.
- No daemon is started.
- No persistent Android filesystem mutation is performed.
- Runner plan reflects the latest private namespace closure work before any future live start-only approval review.

## Assumptions

- V254 does not change `init_v159` or create a new boot image.
- First bounded live start-only still requires explicit operator approval.
- `cnss_diag`, ICNSS bind/unbind, rfkill unblock, WLAN link-up, scan/connect, and firmware mutation remain blocked.
