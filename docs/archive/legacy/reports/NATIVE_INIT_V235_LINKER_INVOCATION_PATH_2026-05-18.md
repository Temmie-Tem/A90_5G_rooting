# Native Init v235 Linker Invocation Path Comparison

## Summary

- Goal: compare `/system/bin/linker64` symlink invocation with direct
  `/apex/com.android.runtime/bin/linker64` invocation inside the same private
  native-init namespace.
- Result: PASS / `android-linker-crash-path-independent`.
- Reason: both linker invocation paths crashed with child `SIGSEGV(11)` across
  all clean target profiles.
- Device baseline: `A90 Linux init 0.9.59 (v159)`.
- No Wi-Fi daemon entrypoint, `cnss_diag`, scan, connect, credential, DHCP,
  routing, global bind mount, or persistent Android partition write was used.

## Implementation

Existing committed v235 implementation was used:

- helper source: `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper version: `a90_android_execns_probe v4`
- local helper SHA256: `43a80100930a8b3af38720a2718f730982ccff532675c52974927db0893f9b68`
- deployed helper path: `/cache/bin/a90_android_execns_probe`
- host wrapper: `scripts/revalidation/wifi_linker_invocation_path_probe.py`
- live evidence: `tmp/wifi/v235-linker-invocation-path-live`

v4 helper additions verified live:

- linker profiles:
  - `system-linker` -> `/system/bin/linker64`
  - `apex-linker` -> `/apex/com.android.runtime/bin/linker64`
- target profile:
  - `apex-linker64-self` -> `/apex/com.android.runtime/bin/linker64`

## Inputs

Real Android generated linkerconfig captured during v233 and redeployed
transiently under `/cache/bin`:

| temporary native path | SHA256 |
| --- | --- |
| `/cache/bin/a90_real_ld.config.txt` | `1ab340f0ee1e5f6d7c43e372dfe3bc9164d34b348dd9c716ded1b4e56e079f1a` |
| `/cache/bin/a90_real_apex.libraries.config.txt` | `5419adf6ed8f74c480d79096681a19a8570470ab8359c6e8c0be110da434f16e` |

Both temporary files were removed after the probe and verified absent with
`stat` returning `ENOENT`.

## Commands

Host NCM setup was restored by assigning `192.168.7.1/24` to
`enxcec41d20b954`; ping to `192.168.7.2` passed 3/3.

Deploy helper and linkerconfig inputs:

```bash
python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_android_execns_probe \
  --toybox /cache/bin/toybox \
  install \
  --local-binary stage3/linux_init/helpers/a90_android_execns_probe \
  --transfer-timeout 120

python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_real_ld.config.txt \
  --toybox /cache/bin/toybox \
  install \
  --local-binary tmp/wifi/v233-android-linkerconfig-source-live/files/linkerconfig__ld.config.txt \
  --transfer-timeout 120

python3 scripts/revalidation/tcpctl_host.py \
  --device-binary /cache/bin/a90_real_apex.libraries.config.txt \
  --toybox /cache/bin/toybox \
  install \
  --local-binary tmp/wifi/v233-android-linkerconfig-source-live/files/linkerconfig__apex.libraries.config.txt \
  --transfer-timeout 120
```

Run matrix:

```bash
python3 scripts/revalidation/wifi_linker_invocation_path_probe.py \
  --out-dir tmp/wifi/v235-linker-invocation-path-live \
  --linkerconfig-mode copy-real \
  --linkerconfig-source /cache/bin/a90_real_ld.config.txt \
  --apex-libraries-source /cache/bin/a90_real_apex.libraries.config.txt \
  --linker-profiles system-linker,apex-linker \
  --target-profiles system-toybox,system-sh,linker64-self,apex-linker64-self,cnss-daemon \
  --env-modes clean,ld-debug-1 \
  probe
```

Cleanup:

```bash
python3 scripts/revalidation/a90ctl.py --timeout 20 run /cache/bin/toybox rm -f \
  /cache/bin/a90_real_ld.config.txt \
  /cache/bin/a90_real_apex.libraries.config.txt
```

## Matrix Result

| env | linker | target profile | result | signal | exit | stdout | stderr |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `clean` | `system-linker` | `system-toybox` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `system-linker` | `system-sh` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `system-linker` | `linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `system-linker` | `apex-linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `system-linker` | `cnss-daemon` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `apex-linker` | `system-toybox` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `apex-linker` | `system-sh` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `apex-linker` | `linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `apex-linker` | `apex-linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `clean` | `apex-linker` | `cnss-daemon` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `system-linker` | `system-toybox` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `system-linker` | `system-sh` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `system-linker` | `linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `system-linker` | `apex-linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `system-linker` | `cnss-daemon` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `apex-linker` | `system-toybox` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `apex-linker` | `system-sh` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `apex-linker` | `linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `apex-linker` | `apex-linker64-self` | crashed | 11 | -1 | 0 | 0 |
| `ld-debug-1` | `apex-linker` | `cnss-daemon` | crashed | 11 | -1 | 0 | 0 |

Decision:

```text
android-linker-crash-path-independent
```

Reason:

```text
both linker invocation paths crashed signals=[11]
```

## Postflight

- `/cache/bin/a90_real_ld.config.txt`: removed, `stat` returned `ENOENT`.
- `/cache/bin/a90_real_apex.libraries.config.txt`: removed, `stat` returned `ENOENT`.
- final `selftest verbose`: `pass=11 warn=1 fail=0`.
- `post-mounts` capture in wrapper: PASS.

## Interpretation

v235 rules out `/system/bin/linker64` symlink invocation as the primary cause.
Direct APEX linker invocation crashes the same way.  The next useful direction is
not controlled CNSS start and not further linkerconfig path tweaking.  The next
bounded step should inspect process crash context or Android process-context
assumptions:

1. bounded crash context capture: wait status plus child `/proc/<pid>/maps`, auxv,
   executable path, signal info if feasible without broad ptrace exposure;
2. Android process-context comparison: compare relevant auxv, `/proc/self/exe`,
   cwd, argv[0], chroot/mount namespace, and linker-visible procfs assumptions;
3. only after that, decide whether a safer non-linker execution route exists.

Wi-Fi scan/connect/link-up remains blocked.
