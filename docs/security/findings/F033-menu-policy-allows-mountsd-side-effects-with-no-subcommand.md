# F033. Menu policy allows mountsd side effects with no subcommand

## Metadata

| field | value |
|---|---|
| finding_id | `ac9fa71b54608191a236dd6983b52094` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/ac9fa71b54608191a236dd6983b52094 |
| severity | `low` |
| status | `mitigated-shared-controller` |
| detected_at | `2026-05-07 03:35:47 +0900` |
| committed_at | `2026-05-07` |
| commit_hash | `f90db28` |
| relevant_paths | `stage3/linux_init/a90_controller.c` <br> `stage3/linux_init/a90_storage.c` <br> `stage3/linux_init/v128/80_shell_dispatch.inc.c` |
| has_patch | `true` |

## Description

The v128 subcommand-aware menu busy gate allowed bare `mountsd` while the screen menu was active because `subcmd_absent_or_one_of()` treats a missing subcommand as safe. That assumption is valid for commands whose default is `status`, but `a90_storage_cmd_mountsd()` defaults a missing subcommand to `ro`. Bare `mountsd` can therefore unmount/remount the SD mount point read-only, which violates the menu-active read-only-query policy.

## Local Remediation

- Added `subcmd_one_of()` for commands that require an explicit safe subcommand.
- Changed menu-active `mountsd` policy to allow only `mountsd status`.
- Kept `hudlog` and `netservice` on the absent-or-status rule because their bare command behavior is status-only.
- Kept normal shell behavior outside the menu unchanged: bare `mountsd` still means `ro` when no menu busy gate is active.

## Security Impact

This is a low-severity local availability/state-change issue. It requires access to the trusted root shell/control channel while the menu is visible. It does not grant code execution, but it can change SD mount state during a UI/menu-active period where only observation commands should pass.

## Validation

- Static source review confirms `mountsd` now uses `subcmd_one_of()` under `a90_controller_command_busy_reason_ex()`.
- Local security rescan includes S014 for this policy and passes.
- `git diff --check` passes.
- Host Python tooling `py_compile` passes.

## Codex Cloud Detail

Menu policy allows mountsd side effects with no subcommand
Link: https://chatgpt.com/codex/cloud/security/findings/ac9fa71b54608191a236dd6983b52094?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: low
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: f90db28
Author: shs02140@gmail.com
Created: 2026. 5. 7. 오전 3:35:47
Assignee: Unassigned
Signals: Security

# Summary
Introduced. v127 used the older command-level busy gate, which blocked mountsd while the menu was active. v128 dispatch now calls a90_controller_command_busy_reason_ex(), whose status-only rule accidentally permits bare `mountsd`; the mountsd handler then performs a mount/remount side effect.

The commit adds a subcommand-aware busy-gate path for commands issued while the screen menu is visible. The helper subcmd_absent_or_one_of() returns true when argc <= 1, and that helper is used for mountsd under the assumption that the default behavior is a read-only status query. However, a90_storage_cmd_mountsd() defaults a missing subcommand to "ro", not "status". Therefore, when the menu is active, `mountsd` with no arguments is allowed through the new v128 policy and can unmount/remount the SD mount point read-only. This violates the intended deny-by-default/read-only-query-only policy and can affect storage/log availability or change mount state during menu-visible operation.
