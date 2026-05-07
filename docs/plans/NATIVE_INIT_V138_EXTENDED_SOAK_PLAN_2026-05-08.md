# v138 Plan: Release-candidate Extended Soak

## Summary

v138 targets `A90 Linux init 0.9.38 (v138)` / `0.9.38 v138 EXTENDED SOAK`.

This version is the first post-v137 release-candidate soak pass. v137 added one
integrated validation gate, but it still proves only a short single-run matrix.
Before another controller/UI/network-facing change, v138 should exercise the
same verified surface repeatedly and preserve enough evidence to decide whether
the current build is stable enough for the next refactor.

Current baseline:

- latest verified build is `A90 Linux init 0.9.37 (v137)`;
- v137 integrated validation passed with `PASS commands=24`;
- v137 quick soak passed with `PASS cycles=3 commands=14`;
- local targeted v137 security rescan is `PASS=17`, `WARN=1`, `FAIL=0`;
- remaining warning is the accepted trusted-lab USB ACM/local bridge boundary;
- no fresh Codex Cloud blocker is currently recorded in the active queue.

## Scope Decision

Choose `release-candidate extended soak` for v138.

Rationale:

- v136 found no blocking structure issue, but identified the auto-HUD/menu
  controller and shell/storage command handlers as future hotspots.
- v137 added the first integrated host gate; the next step should prove that
  gate remains stable across repeated command cycles and UI/menu transitions.
- Auto-HUD/menu controller cleanup should wait until an extended baseline exists
  because it touches the largest remaining live UI loop.
- Wi-Fi or broader network-facing changes should wait until the current
  USB-local/root-control boundary has fresh soak evidence.

Do not add Wi-Fi bring-up, new listeners, new authentication protocols, new
root-control commands, or broad source movement in v138.

## Key Changes

- Copy v137 into `init_v138.c` and `v138/*.inc.c`.
- Bump metadata in `a90_config.h` to `0.9.38` / `v138` and add changelog text
  `0.9.38 v138 EXTENDED SOAK`.
- Keep native behavior unchanged unless soak exposes a concrete bug.
- Add or extend a host orchestration script for RC soak evidence:
  `scripts/revalidation/native_rc_soak.py`.
- Keep `scripts/revalidation/native_integrated_validate.py` as the primary
  single-pass gate and use it from the RC soak flow rather than duplicating all
  semantic checks.
- Update `native_soak_validate.py` default expected version to v138 after
  real-device flash verification.
- Update `local_security_rescan.py` scope to active v138 and keep the v137
  integrated harness wiring check.
- Write `docs/reports/NATIVE_INIT_V138_EXTENDED_SOAK_2026-05-08.md` after
  real-device validation.

## RC Soak Harness

New or extended script:

```text
scripts/revalidation/native_rc_soak.py
```

Default phases should be non-destructive and bounded:

1. preflight `version` and `status`;
2. one `native_integrated_validate.py` pass;
3. repeated core soak cycles through `native_soak_validate.py`;
4. focused UI/menu cycles:
   - `screenmenu`
   - `status`
   - `policycheck run`
   - `hide`
   - `statushud`
   - `autohud 2`
5. focused storage/runtime cycles:
   - `runtime`
   - `helpers status`
   - `userland status`
   - `storage`
   - `mountsd status`
6. focused exposure/service cycles:
   - `exposure guard`
   - `netservice status`
   - `rshell audit`
   - `service list`
   - `service status autohud`
7. final `bootstatus`, `diag summary`, and `status`.

The script should:

- default to `--expect-version "A90 Linux init 0.9.38 (v138)"`;
- use repo-root pinned host scripts;
- write text transcript to `tmp/soak/native-rc-v138.txt`;
- optionally write JSON summary to `tmp/soak/native-rc-v138.json`;
- record command count, phase count, per-command durations, and failure phase;
- stop on first failure by default;
- support `--keep-going` for diagnostic runs;
- support `--cycles` for core repeated cycles;
- keep NCM/TCP checks status-only by default;
- expose opt-in `--with-ncm-ping` only if host NCM is already configured;
- avoid destructive commands and avoid enabling netservice/rshell automatically.

## Validation Coverage

The v138 RC gate should cover these risks:

| Risk | Evidence |
|---|---|
| Version/protocol drift | `version`, `status`, framed `A90P1 END status=ok` |
| Boot health drift | `bootstatus`, `selftest verbose`, `pid1guard verbose` |
| Menu busy policy drift | `policycheck run`, `screenmenu`, `hide` |
| UI background loop drift | repeated `screenmenu`/`hide`/`autohud 2` |
| Storage/runtime drift | `runtime`, `storage`, `mountsd status` |
| Network exposure drift | `exposure guard`, `netservice status`, `rshell audit` |
| Service registry drift | `service list`, `service status autohud/tcpctl/rshell` |
| Diagnostics consistency | `diag summary`, final `status` |

## Deferred Work

v138 must not include these:

- auto-HUD/menu controller refactor;
- shell/storage handler split;
- active Wi-Fi bring-up;
- default NCM/tcpctl/rshell enablement;
- dropbear/SSH addition;
- new remote command surface;
- destructive storage, mount, format, reboot, recovery, or poweroff tests in the
  default soak.

## Test Plan

### Local Build

Build v138 with the same module set as v137 and confirm markers:

```bash
strings stage3/linux_init/init_v138 | rg "A90 Linux init 0\.9\.38 \(v138\)|A90v138|0\.9\.38 v138 EXTENDED SOAK"
```

### Static Checks

```bash
git diff --check
python3 -m py_compile \
  scripts/revalidation/a90ctl.py \
  scripts/revalidation/native_init_flash.py \
  scripts/revalidation/local_security_rescan.py \
  scripts/revalidation/native_soak_validate.py \
  scripts/revalidation/native_integrated_validate.py \
  scripts/revalidation/native_rc_soak.py
rg -n "A90v137|0\.9\.37|init_v137|v137/" stage3/linux_init/init_v138.c stage3/linux_init/v138 stage3/linux_init/a90_config.h || true
```

### Device Validation

Flash and verify:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v138.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --verify-protocol auto
```

Integrated validation:

```bash
python3 scripts/revalidation/native_integrated_validate.py \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --out tmp/validation/native-integrated-v138.txt \
  --json-out tmp/validation/native-integrated-v138.json
```

Extended RC soak:

```bash
python3 scripts/revalidation/native_rc_soak.py \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --cycles 10 \
  --out tmp/soak/native-rc-v138.txt \
  --json-out tmp/soak/native-rc-v138.json
```

Quick compatibility soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --out tmp/soak/v138-quick-soak.txt
```

Optional host NCM status-only check, only when host NCM is already configured:

```bash
python3 scripts/revalidation/native_rc_soak.py \
  --expect-version "A90 Linux init 0.9.38 (v138)" \
  --cycles 3 \
  --with-ncm-ping \
  --out tmp/soak/native-rc-v138-ncm.txt
```

## Acceptance

- v138 boots and verifies as `A90 Linux init 0.9.38 (v138)`.
- `native_integrated_validate.py` passes with all default commands.
- `native_rc_soak.py --cycles 10` passes without command timeout, missing
  frame, protocol failure, or semantic failure.
- `native_soak_validate.py --cycles 3` remains compatible and passes.
- Local targeted v138 security rescan remains `FAIL=0`.
- `screenmenu` remains nonblocking and `hide` remains available.
- `policycheck run` remains `fail=0`.
- `exposure guard` remains `guard=ok` and `fail=0`.
- No new network exposure is introduced.
- Artifacts, transcripts, hashes, and device validation results are recorded in
  `docs/reports/NATIVE_INIT_V138_EXTENDED_SOAK_2026-05-08.md`.

## Assumptions

- v137 is latest verified when v138 starts.
- v138 is primarily a validation/release-candidate soak release.
- Native behavior should remain v137-compatible apart from version/changelog
  marker updates unless soak exposes a concrete defect.
- The accepted USB-local/localhost root-control warning remains accepted only
  while bridge and ACM use stay local/trusted-lab-only.
- Fresh Codex Cloud findings, if any appear before implementation starts, can
  preempt v138 or become a required v138 fix.
