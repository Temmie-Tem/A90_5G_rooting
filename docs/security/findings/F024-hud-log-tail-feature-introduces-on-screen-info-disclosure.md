# F024. HUD log-tail feature introduces on-screen info disclosure

## Metadata

| field | value |
|---|---|
| finding_id | `d6c8f25861c08191af70ed83953c32ff` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/d6c8f25861c08191af70ed83953c32ff |
| severity | `low` |
| status | `mitigated-v125` |
| detected_at | `2026-04-28T05:01:45.433205Z` |
| committed_at | `2026-04-26 05:27:40 +0900` |
| commit_hash | `badb353ee32e244d24bc07da139905ae2228cf71` |
| relevant_paths | `stage3/linux_init/init_v68.c` |
| has_patch | `true` |

## CSV Description

In init_v68, the auto-HUD path now calls a new renderer that opens native-init.log and draws the last 14 lines directly onto the display whenever the menu is not active. This creates a new confidentiality exposure channel: log content that was previously file-based is now passively broadcast on-screen. In this project, logs include command lifecycle and runtime state records; in shared labs or physically exposed setups this can leak sensitive operator activity and system state via shoulder-surfing/camera capture.

## Local Remediation

- v125 makes passive background HUD log-tail rendering opt-in through `hudlog on`; default `hudlog status` is off.

## Codex Cloud Detail

HUD log-tail feature introduces on-screen info disclosure
Link: https://chatgpt.com/codex/cloud/security/findings/d6c8f25861c08191af70ed83953c32ff?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: low (attack path: low)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: badb353
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 2:01:45
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced vulnerability: passive information disclosure via always-visible HUD log tail in non-menu mode.
In init_v68, the auto-HUD path now calls a new renderer that opens native-init.log and draws the last 14 lines directly onto the display whenever the menu is not active. This creates a new confidentiality exposure channel: log content that was previously file-based is now passively broadcast on-screen. In this project, logs include command lifecycle and runtime state records; in shared labs or physically exposed setups this can leak sensitive operator activity and system state via shoulder-surfing/camera capture.

# Validation
## Rubric
- [x] Confirm commit-introduced control-flow change: non-menu HUD now calls `kms_draw_hud_log_tail` (`init_v68.c:3046-3049`) and prior v67 path lacked this.
- [x] Confirm renderer behavior: opens native log path, tails lines, and draws them on display (`init_v68.c:3788-3822`).
- [x] Confirm sensitive/operational content exists in those logs (`native_logf("cmd", ...)` at `init_v68.c:7315-7337`).
- [ ] Validate with valgrind on target binary (not possible: valgrind not installed in container).
- [x] Perform bounded dynamic reproduction demonstrating disclosure effect (PoC harness output shows command log lines rendered in menu-hidden mode).
## Report
I validated the finding as a real passive information disclosure introduced in v68.

1) Targeted code comparison showed a new always-on non-menu rendering path:
- v68: `stage3/linux_init/init_v68.c:3046-3049` calls `kms_draw_hud_log_tail(&kms_state)` when `menu_active` is false.
- v67 baseline: `stage3/linux_init/init_v67.c:2988-2991` had no `else` branch, so no log-tail rendering in non-menu mode.

2) The new renderer reads the native log file and paints recent lines on screen:
- `stage3/linux_init/init_v68.c:3788-3805` opens `native_log_current_path()` and stores the last 14 non-empty lines.
- `stage3/linux_init/init_v68.c:3811-3822` draws label `LOG TAIL` and each stored line via `kms_draw_text(...)`.

3) The same log contains command execution metadata:
- `stage3/linux_init/init_v68.c:7315-7337` logs `cmd start` / `cmd end` with command name, argc, flags, rc, errno, duration.

4) Compiled-stack dynamic attempts (as requested):
- Debug build succeeded: `gcc -O0 -g ... init_v68.c`.
- Direct run with 2s timeout did not crash (exit 137 from forced kill; no crash trace) because PID1/device-init flow blocks on unavailable hardware paths in container.
- Valgrind unavailable (`bash: command not found: valgrind`).
- ASan build/run attempted; also no crash in bounded run (forced timeout kill).
- Debugger attempt with LLDB succeeded and reached `main` at `init_v68.c:7365`, confirming executable/debug path, but no memory-safety fault was observable in this environment.

5) Reproduction artifact PoC:
- I built a minimal harness that preserves the v68 log-tail logic and branch semantics, then fed a sample `native-init.log` containing sensitive command text.
- Output (`poc_output.txt`) shows when menu is hidden it renders `LOG TAIL` plus recent log lines including:
  - `[cmd] start ... token=SECRETTOKEN12345`
  - `[cmd] end name=flashall rc=0 ...`
- When menu is visible, it renders menu section instead of log tail.

Conclusion: the suspected issue is valid. v68 introduces a non-menu HUD path that passively displays tail lines from `native-init.log`, which includes operational command metadata, creating shoulder-surf/camera disclosure risk.

# Evidence
stage3/linux_init/init_v68.c (L3046 to 3049)
  Note: New control flow: when menu is hidden, HUD now renders log tail instead of just status overlay.
```
            if (menu_active)
                kms_draw_menu_section(&kms_state, page, menu_sel);
            else
                kms_draw_hud_log_tail(&kms_state);
```

stage3/linux_init/init_v68.c (L3788 to 3822)
  Note: New log-tail renderer opens native log and draws recent lines to screen, creating the on-screen disclosure path.
```
    fp = fopen(native_log_current_path(), "r");
    if (fp != NULL) {
        char line[HUD_LOG_LMAX];
        int idx = 0;

        while (fgets(line, sizeof(line), fp) != NULL) {
            size_t len = strlen(line);
            while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r'))
                line[--len] = '\0';
            if (len == 0)
                continue;
            snprintf(buf[idx % HUD_LOG_TAIL], HUD_LOG_LMAX, "%.*s",
                     HUD_LOG_LMAX - 1, line);
            ++idx;
        }
        fclose(fp);
        nstored   = idx < HUD_LOG_TAIL ? idx : HUD_LOG_TAIL;
        ring_start = idx >= HUD_LOG_TAIL ? (idx % HUD_LOG_TAIL) : 0;
    }

    if (nstored <= 0)
        return;

    kms_fill_rect(state, x, area_y - hud_scale * 2, card_w, 1, 0x282828);
    kms_draw_text(state, x, area_y, "LOG TAIL", 0xffcc33, scale);
    area_y += lh + scale * 2;

    for (i = 0; i < nstored; ++i) {
        uint32_t row_y = area_y + (uint32_t)i * (lh + 2);
        int ri = (ring_start + i) % HUD_LOG_TAIL;

        if (row_y + lh > state->height)
            break;
        kms_draw_text(state, x, row_y, buf[ri], 0x606060,
                      shrink_text_scale(buf[ri], scale, card_w));
```

stage3/linux_init/init_v68.c (L7315 to 7337)
  Note: Log records include command execution metadata; this data is now exposed by the new on-screen log-tail rendering path.
```
        native_logf("cmd", "start name=%s argc=%d flags=0x%x",
                    argv[0], argc, command->flags);

        if ((command->flags & CMD_DISPLAY) != 0) {
            stop_auto_hud(false);
        }

        errno = 0;
        started_ms = monotonic_millis();
        result = command->handler(argv, argc);
        duration_ms = monotonic_millis() - started_ms;
        if (duration_ms < 0) {
            duration_ms = 0;
        }

        if (result < 0) {
            result_errno = -result;
        } else {
            result_errno = 0;
        }
        save_last_result(argv[0], result, result_errno, duration_ms, command->flags);
        native_logf("cmd", "end name=%s rc=%d errno=%d duration=%ldms flags=0x%x",
                    argv[0],
```

# Attack-path analysis
Final: low | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Severity remains low. Evidence strongly supports that the bug is real and reachable, but the attacker model is primarily physical observation (or camera capture) rather than remote/network exploitation. Probability is moderate in shared lab contexts, while security impact is limited to low-grade confidentiality leakage of runtime/operator metadata. No auth bypass, code execution, or privilege escalation is created.
## Likelihood
medium - Exploitation needs physical visibility and menu-hidden state, but those are plausible in shared benches/labs and the feature is reachable in normal runtime.
## Impact
low - Confidentiality impact is limited to on-screen leakage of recent operational logs (command/state metadata). No direct integrity or availability compromise is introduced by this change.
## Assumptions
- init_v68 is actually built/flashed in at least some operator workflows (not just kept as archival source).
- An attacker can obtain physical line-of-sight (or camera view) to the device display in a shared lab/bench setup.
- native-init.log may contain operationally sensitive context (command lifecycle/state), even if not always credentials.
- Device boots the v68 native init HUD path
- HUD menu enters hidden state (menu_active=false)
- Attacker can visually observe or record the screen
## Path
N1(auto_hud) -> N2(menu hidden) -> N3(read /cache/native-init.log) -> N4(draw LOG TAIL) -> N5(observer sees data)
## Path evidence
- `stage3/linux_init/init_v68.c:3046-3049` - When menu is not active, code calls kms_draw_hud_log_tail().
- `stage3/linux_init/init_v68.c:3788-3822` - Renderer opens native_log_current_path(), tails recent lines, and draws each line on HUD.
- `stage3/linux_init/init_v68.c:7315-7337` - Command lifecycle metadata is written into the same log source later displayed on screen.
- `stage3/linux_init/init_v67.c:2988-2991` - Previous version lacked the non-menu else branch (supports commit-introduced regression).
- `stage3/linux_init/init_v68.c:2664-2669` - Menu includes HIDE MENU action, making menu-hidden state an intended runtime mode.
- `stage3/linux_init/init_v68.c:7290-7294` - Serial hide words can also trigger hidden-menu state.
- `stage3/linux_init/init_v68.c:7450-7453` - Auto HUD is started during boot, so renderer path is part of normal runtime.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_badb353ee32e244d24bc07da139905ae2228cf71/extracted/hud-log-tail-disclosure/poc_output.txt:1-19` - Executable PoC output shows 'LOG TAIL' plus sample sensitive command log lines when menu is hidden.
## Narrative
Code evidence confirms a real confidentiality issue: v68 introduces a new non-menu HUD branch that reads /cache/native-init.log and draws the last 14 lines on screen. This is reachable in normal operation (auto HUD starts at boot, menu can be hidden), and a validation PoC shows the disclosure effect. Impact is limited to local physical observers/cameras, so severity remains low.
## Controls
- Disclosure path only executes when menu_active == false.
- Displayed tail is capped (HUD_LOG_TAIL=14, HUD_LOG_LMAX=80).
- Attack requires physical/camera observation; no network listener is introduced by this specific code path.
## Blindspots
- Static review cannot prove how often v68 (vs other init versions) is deployed in real operator workflows.
- No direct measurement of real log contents in production benches; sensitivity may vary by operator usage.
- Assessment does not include live device physical controls (camera restrictions, lab access policy).
