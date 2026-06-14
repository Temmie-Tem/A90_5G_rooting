# Native Init v232 Linkerconfig Materialization Probe

## Summary

- Goal: test whether a private `/linkerconfig/ld.config.txt` materialized only
  inside the helper temp root changes `linker64 --list /vendor/bin/cnss-daemon`
  from the v231 `SIGSEGV(11)` boundary into a normal linker diagnostic.
- Result: EXECUTED / CRASH PERSISTS.
- Device baseline: `A90 Linux init 0.9.59 (v159)`.
- Helper version: `a90_android_execns_probe v2`.
- Local/remote helper SHA256:
  `a4a56e6b1cc263602b143003c2807b0f896bbdd94c75d8bbd945776434b85e23`.

v232 did not start `cnss-daemon`, did not run `cnss_diag`, did not perform Wi-Fi
scan/connect/link-up, did not create global bind mounts, and did not write to
Android partitions.

## Changes

- Extended `stage3/linux_init/helpers/a90_android_execns_probe.c` with
  `--linkerconfig-mode none|copy-real|minimal-vendor`.
- Added private `minimal-vendor` materialization under
  `<temp-root>/linkerconfig/ld.config.txt`.
- Added `linkerconfig_mode`, `linkerconfig_source`, `linkerconfig_bytes`, and
  `linkerconfig_hash` fields to helper output.
- Added `scripts/revalidation/wifi_linkerconfig_materialization_probe.py` as
  the v232 host wrapper.
- Extended `scripts/revalidation/wifi_android_exec_namespace_probe.py` so v232
  can require `--allow-private-linkerconfig` before materialized modes run.

## Local Validation

```bash
scripts/revalidation/build_android_execns_probe_helper.sh
python3 -m py_compile \
  scripts/revalidation/wifi_android_exec_namespace_probe.py \
  scripts/revalidation/wifi_linkerconfig_materialization_probe.py \
  scripts/revalidation/helper_deploy.py \
  scripts/revalidation/tcpctl_host.py
git diff --check
```

Result: PASS.

Static helper:

```text
ELF 64-bit LSB executable, ARM aarch64, statically linked
There is no dynamic section in this file.
```

## Deployment

NCM transfer path was used:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_android_execns_probe \
  --toybox /cache/bin/toybox \
  install \
  --local-binary stage3/linux_init/helpers/a90_android_execns_probe \
  --transfer-timeout 120 \
  --transfer-delay 2.0
```

Remote verification:

```bash
python3 scripts/revalidation/a90ctl.py run \
  /cache/bin/toybox sha256sum /cache/bin/a90_android_execns_probe
python3 scripts/revalidation/a90ctl.py run \
  /cache/bin/a90_android_execns_probe --help
```

Result:

- remote SHA256:
  `a4a56e6b1cc263602b143003c2807b0f896bbdd94c75d8bbd945776434b85e23`
- helper help output reports `a90_android_execns_probe v2`.

## Live Probe: minimal-vendor

Command:

```bash
python3 scripts/revalidation/wifi_linkerconfig_materialization_probe.py \
  --out-dir tmp/wifi/v232-linkerconfig-materialization-live-minimal \
  probe \
  --allow-temp-namespace \
  --allow-linker-list \
  --allow-private-linkerconfig \
  --linkerconfig-mode minimal-vendor \
  --assume-yes
```

Result:

- decision: `android-linkerconfig-crash-persists`
- pass: `False`
- reason: `linker process terminated by signal 11`
- evidence: `tmp/wifi/v232-linkerconfig-materialization-live-minimal`

Helper fields:

- `helper_status=namespace-ready`
- `linkerconfig_mode=minimal-vendor`
- `linkerconfig_mount_source=<private-materialized>`
- `linkerconfig_bytes=489`
- `linkerconfig_hash=0xbbd95d7d750406d1`
- `child_exit_code=-1`
- `child_signal=11`
- `timed_out=0`
- stdout/stderr: empty
- `cleanup_status=attempted`

Postflight checked the device after helper cleanup. No `/tmp/a90-v231-*` or
`/tmp/a90-v232-*` mount leak was observed in captured mounts.

## Live Probe: none baseline

Command:

```bash
python3 scripts/revalidation/wifi_linkerconfig_materialization_probe.py \
  --out-dir tmp/wifi/v232-linkerconfig-materialization-live-none \
  probe \
  --allow-temp-namespace \
  --allow-linker-list \
  --assume-yes
```

Result:

- decision: `android-namespace-manual-review-required`
- pass: `False`
- reason: `linker process terminated by signal 11`
- evidence: `tmp/wifi/v232-linkerconfig-materialization-live-none`

Baseline fields:

- `linkerconfig_mode=none`
- `linkerconfig_mount_source=/mnt/system/linkerconfig`
- `linkerconfig_bytes=0`
- `child_signal=11`

## Interpretation

The synthetic private linkerconfig did not change the failure mode. The linker
still terminates by `SIGSEGV(11)` before emitting a normal namespace or missing
library diagnostic. This weakens the hypothesis that the only blocker is a
missing `/linkerconfig/ld.config.txt` file, but it does not fully close the
linkerconfig question because the synthetic config is not the stock Android
generated config.

The next defensible step is either:

1. boot stock Android and capture real `/linkerconfig` read-only, then rerun
   v232 `copy-real`; or
2. instrument the helper to capture more crash context around `linker64 --list`
   without executing `cnss-daemon`.

Wi-Fi scan/connect/link-up remains blocked until the linker boundary produces a
normal diagnostic or a controlled start-only decision can be defended.
