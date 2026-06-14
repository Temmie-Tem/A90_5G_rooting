# Native Init v137 Validation Matrix

Date: `2026-05-07`
Build: `A90 Linux init 0.9.37 (v137)`
Marker: `0.9.37 v137 VALIDATION MATRIX`
Baseline: `A90 Linux init 0.9.36 (v136)`
Plan: `docs/plans/NATIVE_INIT_V137_INTEGRATED_VALIDATION_PLAN_2026-05-07.md`

## Summary

v137 is the B candidate selected after v136: integrated validation matrix / host
harness expansion. It adds a host-side non-destructive validation gate that runs
the major existing safety checks together before future Wi-Fi, broader network,
or large controller refactor work.

No new listener, Wi-Fi bring-up, service auto-enable, or root-control expansion
was added. Native behavior remains v136-compatible aside from the version and
changelog marker.

## Source Changes

- Added `stage3/linux_init/init_v137.c` and `stage3/linux_init/v137/*.inc.c` from v136.
- Updated `stage3/linux_init/a90_config.h` to `0.9.37` / `v137`.
- Added `0.9.37 v137 VALIDATION MATRIX` changelog entry.
- Added `scripts/revalidation/native_integrated_validate.py`.
- Updated `native_soak_validate.py` default expected version to v137.
- Updated `local_security_rescan.py` to active v137 and added integrated harness wiring check.
- Updated latest-state docs after real-device validation.

## Integrated Validation Harness

New script:

```text
scripts/revalidation/native_integrated_validate.py
```

Default non-destructive command set:

```text
version
status
bootstatus
selftest verbose
pid1guard verbose
exposure guard
exposure verbose
policycheck run
policycheck verbose
service list
service status autohud
service status tcpctl
service status rshell
netservice status
rshell audit
runtime
helpers status
userland status
storage
mountsd status
wififeas gate
diag summary
screenmenu
hide
```

The harness checks framed `A90P1` success plus command-specific semantics:

- expected v137 version banner;
- `selftest` and `pid1guard` `fail=0`;
- `exposure guard` `guard=ok` and `fail=0`;
- `policycheck` `fail=0`;
- service/netservice/rshell status visibility without starting services;
- diagnostics and exposure token redaction indicators;
- nonblocking `screenmenu` and successful `hide`.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v137` | `5763e59684f8ed283de8ff3cbc746c0096db9042b72b4a13697f5a628fcada4e` |
| `stage3/ramdisk_v137.cpio` | `78853760cfb282fd887a564f225e77af0712e35a2387fc586491d53681753d7a` |
| `stage3/boot_linux_v137.img` | `9446c90c9eaf73fb2ebd41e0de38617b0693ed48a8c143a8645965dfcde55ac7` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.37 (v137)`
  - `A90v137`
  - `0.9.37 v137 VALIDATION MATRIX`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`,
  `local_security_rescan.py`, `native_soak_validate.py`, and
  `native_integrated_validate.py` — PASS.
- v137 active tree stale marker check for `A90v136`, `0.9.36`, `init_v136`,
  `v136/`, and `_v136` — PASS.
- Local targeted v137 security rescan — PASS 17 / WARN 1 / FAIL 0.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v137.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.37 (v137)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA-256 checked — PASS.
- TWRP recovery path through native bridge succeeded — PASS.
- Boot partition prefix SHA matched `stage3/boot_linux_v137.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.37 (v137)` — PASS.

Integrated validation:

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.37 (v137)" \
  --out tmp/validation/native-integrated-v137.txt \
  --json-out tmp/validation/native-integrated-v137.json
```

Result: `PASS commands=24`.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.37 (v137)" \
  --out tmp/soak/v137-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- Initial harness draft used `pid1guard run`, which is intentionally blocked by
  the menu-active busy gate. The default gate was corrected to `pid1guard
  verbose`, keeping the integrated harness non-mutating/read-only.
- Initial `rshell audit` semantic check expected `rshell:` but actual output uses
  `rshell-audit:`. The harness now follows the actual command output.
- Initial `diag summary` semantic check expected `[diag]`; actual output uses
  `[A90 DIAG]`. The harness now follows the actual command output.

## Next Work

The next candidate should be chosen from:

1. use the v137 integrated gate before any Wi-Fi/network-facing change;
2. start a small controller cleanup around `auto_hud_loop()` only if the v137
   gate remains green;
3. run a longer release-candidate soak if no fresh security finding appears.
