# A90 Native Init v124 Security Batch 2

Date: 2026-05-06
Build: `A90 Linux init 0.9.24 (v124)`
Marker: `0.9.24 v124 SECURITY BATCH2`

## Summary

v124 implements Security Batch 2 runtime storage and helper trust hardening.
Runtime-root helpers are no longer preferred merely because an executable file
exists on SD/cache runtime storage. A runtime helper must be covered by an
allowed manifest path and a matching SHA-256 before it can override the ramdisk
or cache fallback. Storage probes, logs, runtime state writes, and selected
service/token writes now use no-follow creation where supported.

## Changes

- Added device-side SHA-256 verification for helper manifest entries.
- Required runtime helper path to stay under the active runtime root before preference.
- Required valid manifest SHA-256 before runtime helper preference.
- Kept ramdisk/cache fallback helpers when runtime helper verification is missing or failed.
- Changed directory creation to reject symlink/file collisions instead of accepting any `EEXIST`.
- Added `O_NOFOLLOW` and `0600` creation to runtime probes, SD probe/identity files, native logs, diag bundles, run log redirection, netservice flags/tokens, and rshell state writes.
- Changed `mountsd rw/init` to verify the expected SD UUID before log redirection and to run workspace identity/RW probes before selecting the SD log path.
- Changed `tcpctl_host.py install` to upload to a temporary file, verify SHA-256 before `mv -f`, remove temporary files on failure, and refuse ramdisk `/bin` install targets by default.

## Finding Coverage

| finding | v124 result |
|---|---|
| F002 | Mitigated: runtime helper is preferred only after allowed path + matching SHA-256 verification; otherwise fallback remains selected. |
| F004 | Mitigated: host install no longer writes directly to the target path and refuses `/bin/a90_tcpctl` ramdisk replacement. |
| F011 | Mitigated: runtime directory creation rejects symlink collisions and RW probes use no-follow private files. |
| F012 | Mitigated: SD log redirection is gated on expected UUID, identity marker, and RW probe; native log opens are no-follow `0600`. |
| F013 | Mitigated for current code: the current runtime/storage probe class now uses no-follow writes; historical v79 remains legacy-source only. |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v124` | `2a79cb710989e83ca22c34a3601f07917ccd722aa3dbcb4d0e98ce502b6e3c57` |
| `stage3/ramdisk_v124.cpio` | `e255ed6611ebf4c9a1121fbe6db6747f6e8e79530b6ff4a4d922419928ebceb7` |
| `stage3/boot_linux_v124.img` | `9692e6ce56e5e85bccfd89197487f29f15e3c1b2edf468ea563926bcd7082f06` |
| `external_tools/userland/bin/a90_tcpctl-aarch64-static` | `4fa39e9fca2e5c221d757bd2e09f0930f31864f41ae1daf79271dd5ccb41c764` |

## Validation

### Static

- ARM64 static init build — PASS.
- `strings` marker check for `A90 Linux init 0.9.24 (v124)`, `A90v124`, and `0.9.24 v124 SECURITY BATCH2` — PASS.
- host Python `py_compile` for flash/control/netservice/helper scripts — PASS.
- `git diff --check` — PASS.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v124.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.24 (v124)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Checks

- `version` — PASS, reports `A90 Linux init 0.9.24 (v124)`.
- `status` — PASS, `selftest: pass=10 warn=1 fail=0`, `helpers: entries=7 warn=1 fail=0`.
- `selftest verbose` — PASS, one expected helper warning because SD runtime `busybox` exists without manifest hash and is intentionally not preferred.
- `helpers verbose` — PASS, unverified runtime `busybox` reports `preferred=-` and `runtime helper sha256 required before preference`.
- `helpers path a90_cpustress` — PASS, selects ramdisk `/bin/a90_cpustress`.
- `helpers path a90_tcpctl` — PASS, selects ramdisk `/bin/a90_tcpctl`.
- `storage` and `mountsd status` — PASS, expected SD UUID matches and log path remains `/mnt/sdext/a90/logs/native-init.log`.
- `cpustress 3 2` — PASS, executes `/bin/a90_cpustress` and exits rc=0.
- `netservice status` — PASS, disabled by default, bind remains `192.168.7.2`, auth required.
- `statushud`, `autohud 2`, `screenmenu`, `hide` — PASS.
- `tcpctl_host.py install` with default `/bin/a90_tcpctl` target — PASS fail-closed with explicit refusal.

## Notes

- The v124 helper warning is intentional with the current SD card contents: an SD runtime `busybox` binary exists, but no matching `helpers.manifest` SHA-256 entry exists yet.
- To use SD/runtime helpers intentionally, generate a manifest line with `helper_deploy.py manifest`, place it under the active runtime manifest path, and rerun `helpers verify`.
- Full NCM host TCP soak was not repeated for Batch 2 because this change targets helper/storage trust and current host-side sudo NCM setup remains interactive.
