# V1233 mdm_helper Post-WAIT_FOR_REQ Branch Snapshot Build

- date: `2026-05-31`
- result: `PASS`
- decision: `v1233-post-wait-req-branch-snapshot-build-pass`
- helper: `a90_android_execns_probe v257`
- sha256: `66c3bc5a9cc0daa9a9a04fe7b98ebe2d7aa974798ed131adf82e5b314b2753e5`
- verifier: `scripts/revalidation/native_wifi_mdm_helper_post_wait_req_branch_snapshot_support_v1233.py`
- evidence: `tmp/wifi/v1233-execns-helper-v257-build/manifest.json`

## Purpose

V1232 proved that `mdm_helper` leaves `ESOC_WAIT_FOR_REQ` at sample `4`, but
`/vendor/bin/ks`, `/dev/mhi_0305_01.01.00_pipe_10`, and MHI fds remain absent
through the bounded post-transition window. V1233 prepares a source/build-only
helper update to inspect the immediate post-return branch more tightly without
using ptrace or changing the live action contract.

## Helper Changes

- Bumped `stage3/linux_init/helpers/a90_android_execns_probe.c` to `v257`.
- Added `--pm-observer-mdm-helper-post-wait-req-branch-snapshot`.
- The new flag requires `--pm-observer-mdm-helper-post-wait-req-ks-observer`.
- Added bounded `post_wait_branch.*` snapshots around the wait-return boundary.
- Captures per-thread `wchan`, `/proc/<tid>/syscall`, selected syscall names,
  args, path strings for path-taking syscalls, and `/dev/esoc-0`/MHI fd counts.
- Adds an initial pre-sample window, post-transition samples, and a 20-sample
  10ms transition burst.

## Safety Contract

V1233 is source/build-only. It does not execute device commands, deploy helpers,
write tracefs, issue eSoC ioctls, start PM/CNSS/`mdm_helper` actors, start Wi-Fi
HAL, scan/connect, use credentials, run DHCP/routes, external ping, reboot, flash,
or write boot/partition artifacts.

The generated live observer keeps these explicit helper-side markers:

```text
post_wait_branch.esoc_notify_attempted=0
post_wait_branch.boot_done_attempted=0
post_wait_branch.wifi_hal_start_executed=0
post_wait_branch.scan_connect_linkup=0
post_wait_branch.credentials=0
post_wait_branch.dhcp_routing=0
post_wait_branch.external_ping=0
```

## Validation

| Check | Result |
|---|---|
| `python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_post_wait_req_branch_snapshot_support_v1233.py` | pass |
| `python3 scripts/revalidation/native_wifi_mdm_helper_post_wait_req_branch_snapshot_support_v1233.py run` | pass |
| static aarch64 helper | pass |
| no dynamic section / no interpreter | pass |
| required source strings | pass |
| required binary strings | pass |
| stage3 binary SHA matches built output | pass |

The build produced `stage3/linux_init/helpers/a90_android_execns_probe_v257`:

```text
ELF 64-bit LSB executable, ARM aarch64, statically linked
sha256=66c3bc5a9cc0daa9a9a04fe7b98ebe2d7aa974798ed131adf82e5b314b2753e5
size=1253872
```

Existing compiler warnings remain in older PM observer snapshot paths and were
not introduced by the V1233 branch snapshot path.

## Next Gate

V1234 should deploy helper `v257` only. V1235 should run the bounded live branch
snapshot with the same lower-path constraints: no Wi-Fi HAL, no scan/connect, no
credentials, no DHCP/routes, no external ping, no `ESOC_NOTIFY`, and no
`ESOC_BOOT_DONE`.
