# Native Init v136 Structure Audit 3

Date: `2026-05-07`
Build: `A90 Linux init 0.9.36 (v136)`
Marker: `0.9.36 v136 STRUCTURE AUDIT 3`
Baseline: `A90 Linux init 0.9.35 (v135)`
Plan: `docs/plans/NATIVE_INIT_V136_STRUCTURE_AUDIT_PLAN_2026-05-07.md`

## Summary

v136 is the C candidate selected after v135: a post-security/post-policy-matrix
structure audit checkpoint. It does not add a new listener, does not change Wi-Fi
state, and does not broaden root-control exposure.

The v135 source tree was copied to `init_v136.c` and `v136/*.inc.c`, versioned to
`0.9.36 (v136)`, built, flashed, and verified on the A90. The audit found no
blocking module-boundary issue requiring a risky refactor in v136. The next
high-value work is v137: integrated validation matrix / host harness expansion.

## Source Changes

- Added `stage3/linux_init/init_v136.c` and `stage3/linux_init/v136/*.inc.c` from v135.
- Updated `stage3/linux_init/a90_config.h` to `0.9.36` / `v136`.
- Added `0.9.36 v136 STRUCTURE AUDIT 3` changelog entry.
- Updated default soak expectation and local targeted security rescan scope to v136.
- Updated latest-state docs after real-device validation.

## Structure Audit Findings

### Module Ownership Drift

Search scope:

```bash
rg -n "setup_acm_gadget|reap_tcpctl_child|/config/usb_gadget/g1/UDC|storage_state|boot_storage|tcpctl_pid|rshell_pid|console_fd|kms_state\." \
  stage3/linux_init/init_v136.c stage3/linux_init/v136 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Result:

- `console_fd` remains private inside `a90_console.c`.
- `kms_state` remains private inside `a90_kms.c`.
- `storage_state` remains private inside `a90_storage.c`.
- `tcpctl_pid` is exposed through netservice/exposure/diag status snapshots, not
  as a mutable include-tree global.
- `rshell_pid` is exposed through exposure snapshots, not as mutable shell state.
- No active v136 include tree directly writes `/config/usb_gadget/g1/UDC`.

Conclusion: no ownership drift that requires source cleanup in v136.

### Duplicate Policy Logic

Search scope:

```bash
rg -n "CMD_DANGEROUS|A90_CONTROLLER_BUSY|subcmd_|status_only|read[-_ ]only|trusted-lab|accepted|guard|token|required|manifest|sha256" \
  stage3/linux_init/v136 stage3/linux_init/a90_*.c stage3/linux_init/a90_*.h
```

Result:

- `a90_controller.c` remains the owner of menu-visible/power-page busy policy.
- `a90_controller.c` also owns the v135 policy matrix. This is intentional test
  duplication, not runtime drift, because the matrix calls the real controller
  decision function and compares expected outcomes.
- `a90_exposure.c` remains the owner of root-control boundary snapshots.
- Helper/runtime trust logic remains split by responsibility:
  - `a90_helper.c`: manifest/SHA-256 preference;
  - `a90_runtime.c`: runtime paths;
  - `a90_userland.c`: BusyBox/toybox inventory;
  - `a90_storage.c`: SD/cache mount and log-storage state.

Conclusion: v137 should add broader validation coverage around these owners
instead of moving policy in v136.

### Include-Tree Residue

Search scope:

```bash
rg -n "native_logf|timeline_record\(|cprintf\(|read_line\(|cmdv1x_decode|struct kms_display_state|cpustress_worker|auto_hud_loop|handle_.*status|fork\(|waitpid\(|kill\(" \
  stage3/linux_init/init_v136.c stage3/linux_init/v136
```

Result:

- Pre-module names such as `native_logf`, `cprintf`, `read_line`,
  `cmdv1x_decode`, `cpustress_worker`, and public `kms_state` access are absent.
- `auto_hud_loop()` remains in `v136/40_menu_apps.inc.c` and still orchestrates
  HUD/menu/app routing. This is the largest remaining UI/controller hotspot.
- Shell handler functions remain in `v136/80_shell_dispatch.inc.c`. This is
  still intentional because command handler visibility and command table wiring
  are high-risk to split casually.
- `fork()` remains in the auto-HUD service spawn path. This is acceptable because
  v85 run/service APIs do not own the persistent HUD child model completely yet.

Conclusion: no stale pre-module API residue is blocking; UI/controller and shell
handler migration remain future candidates.

### PID1 Growth Hotspots

Top active source-size hotspots from `wc -l ... | sort -n | tail`:

| File | Lines | Note |
|---|---:|---|
| `stage3/linux_init/v136/40_menu_apps.inc.c` | 1835 | Largest remaining orchestration surface: auto HUD loop, menu controller, app routing. |
| `stage3/linux_init/v136/80_shell_dispatch.inc.c` | 1252 | Command table and handlers; keep until a safer handler split exists. |
| `stage3/linux_init/v136/70_storage_android_net.inc.c` | 1204 | Storage/Android/network command handlers; policy is mostly delegated to modules. |
| `stage3/linux_init/a90_helper.c` | 904 | Helper manifest and SHA-256 verification; acceptable compiled module size. |
| `stage3/linux_init/a90_storage.c` | 697 | Storage state/mountsd implementation; acceptable compiled module size. |
| `stage3/linux_init/a90_kms.c` | 682 | DRM/KMS primitive owner; acceptable compiled module size. |
| `stage3/linux_init/a90_app_displaytest.c` | 678 | Display test app; UI-heavy but isolated. |
| `stage3/linux_init/a90_app_inputmon.c` | 677 | Input monitor app; UI-heavy but isolated. |

Conclusion: v137 should not split these files yet. A later cleanup version can
target `auto_hud_loop()` controller extraction once validation coverage is wider.

## Keep / Split / Merge Candidates

| Candidate | Decision | Reason |
|---|---|---|
| `a90_controller` + `policycheck` | Keep | Runtime owner plus self-test matrix are intentionally adjacent. |
| `a90_exposure` | Keep | Current owner for F021/F030 boundary evidence. |
| `a90_helper` | Keep | Large but cohesive: manifest, hash, preference, command output. |
| `v136/40_menu_apps.inc.c` | Split later | Biggest hotspot, but it mixes live UI state and physical input behavior. Needs v137 harness first. |
| `v136/80_shell_dispatch.inc.c` | Split later | Handler visibility and command table coupling still make broad movement risky. |
| `v136/70_storage_android_net.inc.c` | Split later | Command handlers are delegated enough; split after validation matrix expansion. |
| `local_security_rescan.py` | Extend in v137 | v136 scan is useful but targeted; broaden into an integrated validation gate. |

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v136` | `8a0baaef6395b074660b90a12626028965d2372813c45371daacc066fc7c5849` |
| `stage3/ramdisk_v136.cpio` | `1a6bfdf02e17b26f609f90bcf122b810ad2f21fa6b546c9753a1b2769adb9839` |
| `stage3/boot_linux_v136.img` | `b5c7233e10f826d6ae4e29b8ac46e11ec8b9ddccaf29f5a10906c343bf2f72e9` |

Ramdisk contents:

```text
.
bin
bin/a90_cpustress
bin/a90_rshell
bin/a90_tcpctl
bin/a90sleep
init
```

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.36 (v136)`
  - `A90v136`
  - `0.9.36 v136 STRUCTURE AUDIT 3`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`,
  `local_security_rescan.py`, and `native_soak_validate.py` — PASS.
- v136 active tree stale marker check for `A90v135`, `0.9.35`, `init_v135`,
  `v135/`, and `_v135` — PASS.
- Local targeted v136 security rescan — PASS 16 / WARN 1 / FAIL 0.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v136.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.36 (v136)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA-256 checked — PASS.
- TWRP recovery path through native bridge succeeded — PASS.
- Boot partition prefix SHA matched `stage3/boot_linux_v136.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.36 (v136)` — PASS.

Command regression:

| Command | Result |
|---|---|
| `bootstatus` | PASS |
| `selftest verbose` | PASS, `pass=10 warn=1 fail=0` |
| `exposure guard` | PASS, `guard=ok warn=0 fail=0` |
| `policycheck run` | PASS, `cases=91 pass=91 fail=0 allowed=45 blocked=46` |
| `screenmenu` | PASS, immediate nonblocking return |
| `hide` | PASS |

Quick soak:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 1 \
  --expect-version "A90 Linux init 0.9.36 (v136)" \
  --out tmp/soak/v136-quick-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Next Input For v137

v137 should take the B candidate: integrated validation matrix / host harness
expansion. Recommended scope:

- combine `selftest verbose`, `pid1guard`, `exposure guard`, `policycheck run`,
  `service list/status`, `netservice status`, `rshell audit`, and quick soak into
  one host-side validation gate;
- emit a single machine-readable report usable before Wi-Fi or broader network
  changes;
- keep device behavior unchanged unless the harness finds a concrete gap.

