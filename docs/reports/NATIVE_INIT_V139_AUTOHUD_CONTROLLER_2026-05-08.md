# Native Init v139 Auto-HUD Controller Cleanup

Date: 2026-05-08
Build: `A90 Linux init 0.9.39 (v139)`
Marker: `0.9.39 v139 AUTOHUD CONTROLLER`
Baseline: `A90 Linux init 0.9.38 (v138)`

## Summary

v139 is a thin UI/controller structure cleanup release. It keeps v138 runtime
behavior and validation scope while making the `auto_hud_loop()` state changes
easier to reason about.

The main change is local to `stage3/linux_init/v139/40_menu_apps.inc.c`: auto-HUD
state, menu/app transitions, hold-repeat timer reset, and special app input
paths are grouped behind helper functions instead of being mutated directly
throughout the loop.

## Key Changes

- Added `stage3/linux_init/init_v139.c` and `stage3/linux_init/v139/*.inc.c`
  from v138.
- Updated `stage3/linux_init/a90_config.h` to `0.9.39` / `v139`.
- Added `0.9.39 v139 AUTOHUD CONTROLLER` changelog entry.
- Added `struct auto_hud_state` in the v139 include tree.
- Centralized auto-HUD transitions with helpers for show, hide, app entry,
  app exit/back, controller state update, hold timer reset, poll timeout, and
  current-screen draw.
- Updated active validation defaults to `A90 Linux init 0.9.39 (v139)`.
- Updated `native_integrated_validate.py` to send `hide` before blocking
  runtime/userland checks so the gate is robust to boot-time menu-visible state.
- Updated `local_security_rescan.py` to scan active v139 source and recognize
  the v139 hold-repeat helper pattern.

## Artifacts

| Artifact | SHA-256 |
|---|---|
| `stage3/linux_init/init_v139` | `a31ac8158fb13f116ae7180294cfe262788962ec9f9ebd2a0bbbb3936e97c620` |
| `stage3/ramdisk_v139.cpio` | `c42fe08311a78cb25793ec90b27744ebce8c7fb8c7ec91986b26eba004ec4c09` |
| `stage3/boot_linux_v139.img` | `8dec8e4fe4312c69453ad0212c865beb3c2cde5c6a9a632d73450cde8c10911c` |

## Static Validation

- Static ARM64 build — PASS.
- Boot image marker strings for `A90 Linux init 0.9.39 (v139)`, `A90v139`,
  and `0.9.39 v139 AUTOHUD CONTROLLER` — PASS.
- `git diff --check` — PASS.
- Python compile check for active host tools — PASS.
- v139 stale marker check for `A90v138`, `0.9.38`, `init_v138`, `v138/`,
  `_v138` in the active v139 tree and active validation tools — PASS.
- Local targeted v139 security rescan — PASS 17 / WARN 1 / FAIL 0.

Security report:

- `docs/security/SECURITY_FRESH_SCAN_V139_2026-05-08.md`

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v139.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.39 (v139)" \
  --verify-protocol auto
```

Result:

- Local image marker found — PASS.
- Local image SHA-256: `8dec8e4fe4312c69453ad0212c865beb3c2cde5c6a9a632d73450cde8c10911c`.
- TWRP recovery path reached — PASS.
- Boot partition prefix SHA matched local image — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.39 (v139)` — PASS.

## Runtime Validation

Integrated validation:

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.39 (v139)" \
  --out tmp/validation/native-integrated-v139.txt \
  --json-out tmp/validation/native-integrated-v139.json
```

Result: `PASS commands=25`.

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --expect-version "A90 Linux init 0.9.39 (v139)" \
  --out tmp/soak/v139-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

RC soak:

```bash
python3 scripts/revalidation/native_rc_soak.py \
  --expect-version "A90 Linux init 0.9.39 (v139)" \
  --cycles 3 \
  --out tmp/soak/native-rc-v139.txt \
  --json-out tmp/soak/native-rc-v139.json
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

- The first integrated validation attempt after flash reached v139 correctly
  but failed at `userland status` because auto-HUD was still menu-active from
  boot. This was not a native command execution failure; it exposed a harness
  ordering weakness.
- The harness now sends `hide` before blocking runtime/userland checks. After
  that normalization, integrated validation passed with `commands=25`.
- The v139 hold-repeat logic still clears the hold timer when a screen cannot
  consume repeat steps, preserving the F032 mitigation.
- The menu-visible `mountsd` side-effect policy remains covered by
  `policycheck run` and local security rescan.

## Acceptance

- v139 boots and verifies as `A90 Linux init 0.9.39 (v139)`.
- Integrated validation passes.
- Quick soak passes.
- RC soak passes.
- Local targeted v139 security rescan remains `FAIL=0`.
- `screenmenu` remains nonblocking and `hide` restores command availability.
- No new network exposure is introduced.

## Next Candidates

- run a longer `native_rc_soak.py --cycles 10` or higher while unattended;
- wait for a fresh Codex Cloud security scan and address any new finding;
- revisit network-facing expansion only after v139 remains green;
- consider deeper `40_menu_apps.inc.c` app-renderer split only if the next
  feature requires it.
