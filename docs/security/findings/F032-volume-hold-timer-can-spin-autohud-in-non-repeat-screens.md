# F032. Volume hold timer can spin autohud in non-repeat screens

## Metadata

| field | value |
|---|---|
| finding_id | `feb29f8ed2608191bab6fdb4a07fdeb3` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/feb29f8ed2608191bab6fdb4a07fdeb3 |
| severity | `low` |
| status | `mitigated-retained-source` |
| detected_at | `2026-05-07 03:34:01 +0900` |
| committed_at | `2026-05-07` |
| commit_hash | `e771b90` |
| relevant_paths | `stage3/linux_init/v131/40_menu_apps.inc.c` <br> `stage3/linux_init/v132/40_menu_apps.inc.c` <br> `stage3/linux_init/v133/40_menu_apps.inc.c` |
| has_patch | `true` |

## Description

The v131 timer-based hold-scroll implementation arms `menu_hold_code` for any volume key-down event. On poll timeout, the code advanced `menu_hold_next_ms` only when `auto_menu_handle_volume_step()` consumed a repeat step. For non-ABOUT active apps, ABOUT pages with only one page, and other non-repeat contexts, that helper returns false. Once the initial hold delay expired, the timer stayed expired and the auto-HUD child could repeatedly poll with timeout `0`, redrawing until key release.

## Local Remediation

- Patched retained v131, v132, and v133 menu sources so an expired hold timer is cleared when the current screen cannot consume a repeat step.
- Repeat-capable screens still reschedule `menu_hold_next_ms` at `AUTO_MENU_HOLD_REPEAT_INTERVAL_MS`.
- Non-repeat screens no longer leave a stale expired timer that can force a zero-timeout poll loop.

## Security Impact

This is a low-severity local availability issue. It requires physical/input access or a stuck/injected volume key event and affects the auto-HUD child responsiveness/CPU use rather than enabling code execution.

## Validation

- Static source review confirms v131, v132, and v133 now clear `menu_hold_code` and `menu_hold_next_ms` when `auto_menu_handle_volume_step()` returns false after the hold timer deadline.
- `git diff --check` passes.
- Host Python tooling `py_compile` passes.

## Codex Cloud Detail

Volume hold timer can spin autohud in non-repeat screens
Link: https://chatgpt.com/codex/cloud/security/findings/feb29f8ed2608191bab6fdb4a07fdeb3?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: low
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: e771b90
Author: shs02140@gmail.com
Created: 2026. 5. 7. 오전 3:34:01
Assignee: Unassigned
Signals: Security

# Summary
Introduced availability bug in the v131 timer-based hold-scroll implementation. The timer state should be cleared or rescheduled even when the current screen cannot consume a repeat step.

v131 starts menu_hold_code for any volume key-down event, but on poll timeout it only advances menu_hold_next_ms when auto_menu_handle_volume_step() succeeds. For non-ABOUT active apps, ABOUT pages with only one page, or other contexts where no repeat action is available, the helper returns false. Once the initial 450 ms delay expires, wait_ms remains <= 0, poll() is repeatedly called with timeout 0, and the autohud child loops continuously redrawing until a key release is processed. This can cause local CPU/battery drain or UI responsiveness degradation. Exploitation requires physical/input access or a stuck/injected key event, and it affects the HUD child rather than directly granting code execution.
