# Native Init v116 Diagnostics Bundle 2

Date: `2026-05-04`
Build: `A90 Linux init 0.9.16 (v116)`
Marker: `0.9.16 v116 DIAG BUNDLE 2`
Baseline: `A90 Linux init 0.9.15 (v115)`

## Summary

v116 closes the v109-v116 service/runtime hardening cycle by extending diagnostics evidence for runtime package paths, helper manifest/deploy state, service/network state, and remote shell security posture.

The change is read-only from an operations perspective. It does not enable Wi-Fi, auto-start remote shell, download helpers, write partitions, or change netservice opt-in policy.

## Source Changes

- Added `stage3/linux_init/init_v116.c` and `stage3/linux_init/v116/*.inc.c` from v115.
- Updated `stage3/linux_init/a90_config.h` to `0.9.16` / `v116`.
- Extended `stage3/linux_init/a90_diag.c` with:
  - runtime package paths: `pkg_bin`, `pkg_helpers`, `pkg_services`, `pkg_manifests`, `state_services`
  - helper state paths: manifest, helper state, deploy log
  - helper verbose evidence: role, required flag, manifest flag, mode, expected SHA, actual SHA
  - remote shell evidence: helper/BusyBox presence, token mode, owner-only flag, flag/token paths, NCM/tcpctl state
  - bundle log tails for helper deploy log and rshell log
- Extended `scripts/revalidation/diag_collect.py` with default device evidence commands and optional `--rshell-harden` smoke.
- Added v116 ABOUT/changelog/menu entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v116` | `423769cc2eea841306dca2d14411384967bb3afe50ea00353574fd9bd7e91c35` |
| `stage3/ramdisk_v116.cpio` | `0ce1218c3e01e19c9d77909b3cc3968fad77f1584323d0da9063f4d30346b3a3` |
| `stage3/boot_linux_v116.img` | `6c7a320973a417abc4f423dadd0e2a0ee6420eb3a739cdd9eb2549ba24069e8f` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- Boot image built by reusing v115 mkbootimg header/kernel args and replacing ramdisk — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.16 (v116)`
  - `A90v116`
  - `0.9.16 v116 DIAG BUNDLE 2`
  - `pkg_manifests`
  - `helper-deploy-log`
  - `token_owner_only`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `diag_collect.py`, `rshell_host.py`, `native_soak_validate.py`, and `ncm_host_setup.py` — PASS.
- v116 include tree stale marker check for v115 current markers — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v116.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.16 (v116)" \
  --verify-protocol auto
```

Result:

- Native bridge v115 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v116.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.16 (v116)` — PASS.
- Boot selftest reported `pass=11 warn=0 fail=0 duration=36ms` — PASS.
- Runtime backend reported SD root `/mnt/sdext/a90`, fallback `no`, writable `yes` — PASS.

Device evidence commands:

| Command | Result |
|---|---|
| `version` | PASS, `0.9.16 build=v116` |
| `status` | PASS, selftest `pass=11 warn=0 fail=0`, runtime SD root, rshell stopped |
| `bootstatus` | PASS, timeline `18/32` |
| `selftest verbose` | PASS, 11 non-destructive checks all PASS |
| `diag` | PASS, runtime/helper/service/network/rshell evidence printed |
| `diag full` | PASS, timeline, mounts, partitions, log tails, helper deploy log tail, rshell log tail included |
| `diag paths` | PASS, default dir `/mnt/sdext/a90/logs` |
| `diag bundle` | PASS, device bundle path `/mnt/sdext/a90/logs/a90-diag-25680.txt` |
| `runtime` | PASS, package and state paths visible |
| `helpers verbose` | PASS, deploy log path and per-helper role/mode/hash fields visible |
| `helpers verify` | PASS, `entries=7 warn=0 fail=0` |
| `service list` | PASS, autohud/tcpctl/adbd/rshell metadata visible |
| `netservice status` | PASS, disabled, `ncm0=absent`, `tcpctl=stopped` |
| `rshell audit` | PASS, token mode `0600`, strict `yes`, warnings `0` |

## Host Diagnostics

Command:

```bash
python3 scripts/revalidation/diag_collect.py \
  --boot-image stage3/boot_linux_v116.img \
  --device-bundle \
  --out tmp/diag/v116-diag-bundle.txt
```

Result: PASS, wrote `tmp/diag/v116-diag-bundle.txt` and collected default v116 device evidence commands.

## Soak Regression

Command:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.16 (v116)" \
  --out tmp/soak/v116-diagnostics-bundle.txt
```

Result: `PASS cycles=3 commands=14`.

## Cycle Closure

v116 provides the evidence bundle needed to audit the v109-v116 cycle:

- v109 structure audit
- v110 app controller cleanup
- v111 extended soak RC
- v112 USB/NCM service soak
- v113 runtime package layout
- v114 helper deployment visibility
- v115 remote shell hardening
- v116 diagnostics bundle 2

Next work should be a completion audit that checks report/docs/evidence consistency before opening a new development cycle.
