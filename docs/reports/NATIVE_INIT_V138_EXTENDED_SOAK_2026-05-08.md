# Native Init v138 Extended Soak

Date: 2026-05-08
Build: `A90 Linux init 0.9.38 (v138)`
Marker: `0.9.38 v138 EXTENDED SOAK`
Baseline: `A90 Linux init 0.9.37 (v137)`

## Summary

v138 is a release-candidate validation release. It adds the host RC soak harness
`native_rc_soak.py` and keeps native runtime behavior v137-compatible apart from
version, marker, and changelog metadata.

The purpose is to make repeated post-boot validation cheap enough to run before
larger controller/UI/network-facing changes.

## Key Changes

- Added `stage3/linux_init/init_v138.c` and `stage3/linux_init/v138/*.inc.c` from v137.
- Updated `stage3/linux_init/a90_config.h` to `0.9.38` / `v138`.
- Added `0.9.38 v138 EXTENDED SOAK` changelog entry.
- Added `scripts/revalidation/native_rc_soak.py`.
- Updated `native_integrated_validate.py` and `native_soak_validate.py` default expected version to v138.
- Updated `local_security_rescan.py` scope to active v138.

## Pre-v138 Long-uptime Baseline

Before flashing v138, the existing v137 boot was validated after `72429.47s`
uptime.

Evidence files:

- `tmp/validation/v137-long-uptime-status-20260508-010706.txt`
- `tmp/validation/v137-long-uptime-core-20260508-010706.txt`
- `tmp/validation/native-integrated-v137-long-uptime-20260508-010706.txt`
- `tmp/validation/native-integrated-v137-long-uptime-20260508-010706.json`

Result:

- `status` showed `selftest fail=0`, `pid1guard fail=0`, `exposure guard=ok`, SD runtime writable, and memory `256/5375MB`.
- Core gates passed: `bootstatus`, `selftest verbose`, `pid1guard verbose`, `exposure guard`, `policycheck run`, `storage`, `mountsd status`, `netservice status`.
- Integrated validation passed: `PASS commands=24`.

## Artifacts

| Artifact | SHA-256 |
|---|---|
| `stage3/linux_init/init_v138` | `a7f96960d724c1141ca436076634f3d2b5882db0ac20d9baf94d09364b0789a5` |
| `stage3/ramdisk_v138.cpio` | `3838a8f72e79aa81c0c0698173ecfc0f895261ce97354762911eee58fd0f74a6` |
| `stage3/boot_linux_v138.img` | `8f608a3273f8ee53b46859b29d419a6e1b3fedd1bde96ca10ce69e02020405d9` |

## Static Validation

- `git diff --check` — PASS.
- Python compile check for active host tools including `native_rc_soak.py` — PASS.
- v138 stale marker check for `A90v137`, `0.9.37`, `init_v137`, `v137/`, `_v137` in the active v138 tree and active validation tools — PASS.
- Local targeted v138 security rescan — PASS 17 / WARN 1 / FAIL 0.

Security report:

- `docs/security/SECURITY_FRESH_SCAN_V138_2026-05-08.md`

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v138.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --verify-protocol auto
```

Result:

- Local image marker found — PASS.
- Local image SHA-256: `8f608a3273f8ee53b46859b29d419a6e1b3fedd1bde96ca10ce69e02020405d9`.
- TWRP recovery path reached — PASS.
- Boot partition prefix SHA matched local image — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.38 (v138)` — PASS.

## Runtime Validation

Integrated validation:

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --out tmp/validation/native-integrated-v138.txt \
  --json-out tmp/validation/native-integrated-v138.json
```

Result: `PASS commands=24`.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --out tmp/soak/v138-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

RC soak:

```bash
python3 scripts/revalidation/native_rc_soak.py \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --cycles 3 \
  --out tmp/soak/native-rc-v138.txt \
  --json-out tmp/soak/native-rc-v138.json
```

Result: `PASS commands=62 failures=0`.

Final status:

- `selftest: pass=10 warn=1 fail=0`
- `pid1guard: pass=10 warn=1 fail=0`
- `exposure: guard=ok warn=0 fail=0`
- `runtime: backend=sd root=/mnt/sdext/a90 fallback=no writable=yes`
- `autohud: running`
- `netservice: disabled tcpctl=stopped`
- `rshell: stopped`
- `storage: backend=sd root=/mnt/sdext/a90 fallback=no`

## Notes

- The first attempt to run `native_integrated_validate.py` and
  `native_soak_validate.py` in parallel failed due to serial bridge contention.
  They were rerun sequentially and passed.
- `native_rc_soak.py` dry-run on v137 initially exposed a harness ordering issue:
  `autohud 2` could leave menu-active state before storage/userland checks. The
  harness now sends a trailing `hide` after the auto-HUD UI phase.

## Acceptance

- v138 boots and verifies as `A90 Linux init 0.9.38 (v138)`.
- Integrated validation passes.
- Quick soak passes.
- RC soak harness passes on device.
- Local targeted v138 security rescan remains `FAIL=0`.
- No new network exposure is introduced.

## Next Candidates

- run a longer `native_rc_soak.py --cycles 10` or higher while unattended;
- auto-HUD/menu controller cleanup, using v138 as the regression baseline;
- fresh Codex Cloud security scan follow-up if new findings appear;
- network-facing changes only after the v138 RC soak gate remains green.
