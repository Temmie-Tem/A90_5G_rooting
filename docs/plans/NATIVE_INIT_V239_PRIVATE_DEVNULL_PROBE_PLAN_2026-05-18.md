# Native Init v239 Private Devnull Probe Plan

## Summary

- v239 continues from v238 without changing the PID1 boot image.
- Goal: test whether materializing a minimal `/dev/null` inside the private
  Android execution namespace clears bionic linker early abort `0xa1`.
- Scope is helper/host probe tooling only: `linker64 --list` remains the only
  executed Android-side operation inside the temporary namespace.
- Wi-Fi daemon start, scan/connect, rfkill writes, credentials, DHCP, routing,
  and persistent Android partition writes remain blocked.

## Rationale

v238 mapped the crash to `__libc_init_AT_SECURE` stdio nullification.  The
selected caller first opens `/dev/null`, then falls back to
`/sys/fs/selinux/null`, and passes abort code `0xa1` when that setup fails.
Therefore the smallest safe closure test is to provide `/dev/null` inside the
private chroot root and rerun the same linker list matrix.

## Implementation

- Update `stage3/linux_init/helpers/a90_android_execns_probe.c` to v6.
- Add helper option:
  - `--null-device-mode none` keeps v236 behavior.
  - `--null-device-mode dev-null` creates `<root>/dev/null` as char device
    `1:3`, mode `0666`.
  - `--null-device-mode dev-null-selinux` also creates
    `<root>/sys/fs/selinux/null` as char device `1:3`, mode `0666` for fallback
    testing if needed.
- Add pre-exec context reporting for `/dev/null` and `/sys/fs/selinux/null`.
- Extend `scripts/revalidation/wifi_linker_crash_capture_probe.py` with
  `--null-device-mode` and `fault_addr` reporting.
- Treat v239 as PASS when no selected matrix entry still crashes at fault
  address `0xa1`.

## Test Plan

```bash
python3 -m py_compile scripts/revalidation/wifi_linker_crash_capture_probe.py
scripts/revalidation/build_android_execns_probe_helper.sh
python3 scripts/revalidation/wifi_linker_crash_capture_probe.py \
  --out-dir tmp/wifi/v239-plan-smoke \
  --null-device-mode dev-null \
  plan
```

Device validation:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_android_execns_probe \
  --toybox /cache/bin/toybox \
  install \
  --local-binary stage3/linux_init/helpers/a90_android_execns_probe

python3 scripts/revalidation/wifi_linker_crash_capture_probe.py \
  --out-dir tmp/wifi/v239-devnull-linker-capture-live \
  --null-device-mode dev-null \
  probe
```

## Acceptance

- v236/v237/v238 `0xa1` early abort must disappear from all selected matrix
  rows.
- Baseline non-Wi-Fi targets should reach normal linker list output.
- `cnss-daemon` may still fail with a dependency/runtime namespace error; that
  is a new blocker, not a v239 failure.
- No daemon entrypoint execution or Wi-Fi action is allowed.

## Next Step After PASS

- Classify the new dependency/namespace blocker after `0xa1` is cleared.
- Current expected candidate: vendor target list reaches normal linker output,
  then fails on unresolved `libcutils.so` or linker namespace library search for
  `cnss-daemon`.
