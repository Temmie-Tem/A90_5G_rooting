# F028. v42 run cancel logic steals child stdin and aborts on 'q'

## Metadata

| field | value |
|---|---|
| finding_id | `07b347be8ba08191b87e2e36b4720ff3` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/07b347be8ba08191b87e2e36b4720ff3 |
| severity | `informational` |
| status | `mitigated-v126` |
| detected_at | `2026-04-28T09:20:22.584349Z` |
| committed_at | `2026-04-25 02:19:21 +0900` |
| commit_hash | `3556c02cff151a5815317d01412e59a87e87a36c` |
| relevant_paths | `stage3/linux_init/init_v42.c` |
| has_patch | `true` |

## CSV Description

In v42, `run`/`runandroid` switched from blocking `waitpid()` to `wait_child_cancelable()`, which polls `STDIN` for cancel keys. But child processes also inherit the same console FD as their stdin/stdout/stderr. This creates competing readers on the same input stream: the parent consumes bytes via `read_console_cancel_event()`. Non-cancel bytes are dropped, and a regular 'q' intended for the child is interpreted as cancel, causing the parent to send SIGTERM/SIGKILL to the child. This is an introduced reliability/availability bug in privileged workflows (interactive child commands become unstable and can be killed unintentionally).

## Local Remediation

- Batch 6 changes retained v42 `run`/`runandroid` child stdio so child stdin is `/dev/null` instead of the parent-polled console stream.

## Codex Cloud Detail

v42 run cancel logic steals child stdin and aborts on 'q'
Link: https://chatgpt.com/codex/cloud/security/findings/07b347be8ba08191b87e2e36b4720ff3?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: informational (attack path: ignore)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 3556c02
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 6:20:22
Assignee: Unassigned
Signals: Validated, Attack-path

# Summary
Bug introduced in this commit: cancel handling for `run`/`runandroid` adds parent-side stdin consumption that races with child stdin, causing dropped input and unintended child termination on 'q'.
In v42, `run`/`runandroid` switched from blocking `waitpid()` to `wait_child_cancelable()`, which polls `STDIN` for cancel keys. But child processes also inherit the same console FD as their stdin/stdout/stderr. This creates competing readers on the same input stream: the parent consumes bytes via `read_console_cancel_event()`. Non-cancel bytes are dropped, and a regular 'q' intended for the child is interpreted as cancel, causing the parent to send SIGTERM/SIGKILL to the child. This is an introduced reliability/availability bug in privileged workflows (interactive child commands become unstable and can be killed unintentionally).

# Validation
## Rubric
- [x] Confirm v42 parent-side stdin consumption exists and is reachable during child wait (`init_v42.c:441-449`, `3543-3562`).
- [x] Confirm cancel classification maps ordinary `q/Q` to cancellation (`init_v42.c:427-438`).
- [x] Confirm child shares the same console stdin source as parent polling (`init_v42.c:3588-3593`).
- [x] Reproduce runtime effect: parent consumes stdin bytes, causing dropped child input and/or child termination on `q` (PoC logs `test_v42_q.log`, `test_v42_abc.log`; controls `test_v41_*.log`).
- [x] Corroborate execution path with debugger trace; attempt valgrind/asan (LLDB backtrace captured, valgrind unavailable, ASan run completed).
## Report
I validated the finding with targeted source review plus a debug PoC that mirrors the v42 wait/cancel path.

Source evidence in commit 3556c02:
- `stage3/linux_init/init_v42.c:441-449` reads 1 byte from parent `STDIN` (`read_console_cancel_event`), consuming shared input.
- `stage3/linux_init/init_v42.c:427-438` treats `'q'/'Q'` as `CANCEL_SOFT` and consumes trailing bytes.
- `stage3/linux_init/init_v42.c:3543-3562` `wait_child_cancelable()` repeatedly polls stdin and calls `terminate_child_for_cancel()` when cancel is detected.
- `stage3/linux_init/init_v42.c:3588-3593` child `run` process inherits same console FD for stdin/stdout/stderr.
- Regression context: `stage3/linux_init/init_v41.c:3391-3394` used blocking `waitpid(pid, &status, 0)` (no parent-side stdin polling).

Dynamic reproduction (PoC built with `-O0 -g`):
1) Control behavior (v41-style):
- `printf 'q\n' | validation/poc_cancel_race v41`
  Output: `child: read byte 'q' (0x71)` then `[exit 0]`.
2) v42 cancel race:
- `printf 'q\n' | validation/poc_cancel_race v42`
  Output: `parent consumed byte: 'q'`, `run: terminating pid=...`, `run: cancelled by q`, `parent rc=-125`.
  This demonstrates child termination triggered by parent consuming `q`.
3) Non-cancel byte loss:
- `printf 'abc\n' | validation/poc_cancel_race v42`
  Output shows parent consumes `a`,`b`,`c`,`\n`; child reports `no input available` and exits 77.
- v41 control with same input reads `a` in child and exits normally.

Debugger confirmation:
- Non-interactive LLDB breakpoint hit in `terminate_child_for_cancel`, backtrace shows chain `wait_child_cancelable -> terminate_child_for_cancel` (`validation/lldb_bt.log`).

Valgrind/ASan attempts:
- `valgrind` unavailable in container (`bash: command not found: valgrind`).
- ASan build/run (`poc_cancel_race_asan`) reproduced same cancel behavior (no memory-safety findings, as expected for logic bug).

# Evidence
stage3/linux_init/init_v42.c (L3543 to 3562)
  Note: Cancelable wait loop polls STDIN in parent and terminates child on detected cancel.
```
static int wait_child_cancelable(pid_t pid, const char *tag, int *status_out) {
    while (1) {
        pid_t got = waitpid(pid, status_out, WNOHANG);
        enum cancel_kind cancel;

        if (got == pid) {
            return 0;
        }
        if (got < 0) {
            int saved_errno = errno;

            cprintf("%s: waitpid: %s\r\n", tag, strerror(saved_errno));
            return -saved_errno;
        }

        cancel = poll_console_cancel(100);
        if (cancel != CANCEL_NONE) {
            terminate_child_for_cancel(pid, tag);
            return command_cancelled(tag, cancel);
        }
```

stage3/linux_init/init_v42.c (L3588 to 3593)
  Note: Child `run` process uses the same console FD for stdin/stdout/stderr, creating competing reads with parent cancel polling.
```
    if (pid == 0) {
        dup2(console_fd, STDIN_FILENO);
        dup2(console_fd, STDOUT_FILENO);
        dup2(console_fd, STDERR_FILENO);
        execve(argv[1], &argv[1], envp);
        cprintf("run: execve(%s): %s\r\n", argv[1], strerror(errno));
```

stage3/linux_init/init_v42.c (L427 to 438)
  Note: A normal 'q'/'Q' byte is classified as soft cancel; non-cancel bytes are still consumed and discarded.
```
static enum cancel_kind classify_console_cancel_char(char ch) {
    if (ch == 0x03) {
        return CANCEL_HARD;
    }
    if (ch == 'q' || ch == 'Q') {
        drain_console_cancel_tail();
        return CANCEL_SOFT;
    }
    if (ch == 0x1b) {
        consume_escape_sequence();
    }
    return CANCEL_NONE;
```

stage3/linux_init/init_v42.c (L441 to 449)
  Note: Parent reads one byte from STDIN for cancel detection, consuming input that may have been intended for the child process.
```
static enum cancel_kind read_console_cancel_event(void) {
    char ch;
    ssize_t rd = read(STDIN_FILENO, &ch, 1);

    if (rd != 1) {
        return CANCEL_NONE;
    }
    return classify_console_cancel_char(ch);
}
```

# Attack-path analysis
Final: ignore | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept as real bug but downgraded for security triage: (1) in-scope and reproducible availability regression is proven by code + executable PoC, yet (2) required actor already controls privileged shell input path, and (3) outcome is only unintended cancellation/DoS of current child command, not a material increase in attacker capability. Under the project threat model this is operational reliability debt, not a standalone security vulnerability.
## Likelihood
low - Triggering is easy once shell input access exists, but exploitation value is low because attacker with that access already has stronger native capabilities.
## Impact
ignore - Primary effect is command reliability/availability degradation (dropped stdin and unintended child termination). No new privilege gain, auth bypass, or data-boundary break is demonstrated.
## Assumptions
- The deployed runtime corresponds to init_v42 (repo states latest source is stage3/linux_init/init_v42.c).
- Attackers considered in-scope are those who can send bytes to the serial shell path (physical USB host or localhost bridge client).
- Assessment is static-only plus provided validation artifact logs; no live device/cloud interaction was performed.
- Access to init shell stdin stream (/dev/ttyGS0 or bridged TCP client)
- Operator/attacker triggers run or runandroid with an interactive child
- Parent cancel loop and child share the same console FD
## Path
stdin source -> [child shares console_fd] + [parent poll/read STDIN] -> cancel classification -> terminate child
## Path evidence
- `README.md:17-21` - Shows init_v42 as latest source and serial/bridge control channel in active workflow.
- `stage3/linux_init/init_v42.c:427-449` - Cancel classification maps 'q'/'Q' to soft cancel and parent reads one byte from STDIN.
- `stage3/linux_init/init_v42.c:3543-3562` - Cancelable wait loop polls console and kills child when cancel is detected.
- `stage3/linux_init/init_v42.c:3588-3593` - Child run process duplicates same console_fd to stdin/stdout/stderr, creating competing readers.
- `stage3/linux_init/init_v41.c:3391-3394` - Prior version used blocking waitpid without parent-side stdin polling (regression context).
- `scripts/revalidation/serial_tcp_bridge.py:17-18` - Default bridge exposure is localhost:54321, limiting default external reach.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_3556c02cff151a5815317d01412e59a87e87a36c/extracted/validation/test_v42_q.log:1-5` - Executable PoC log shows parent consumed 'q' and terminated child (run cancelled).
## Narrative
Code evidence confirms the bug: v42 parent polling reads from STDIN (init_v42.c:441-449), classifies plain 'q' as cancel (427-434), and in wait_child_cancelable() terminates child on cancel (3543-3562) while child stdin is the same console_fd (3588-3591). Validation artifact logs show executable PoC reproduction (parent consumes 'q', child terminated; non-cancel bytes lost). This is a real reachability/availability regression in an in-scope runtime path, but it is not a meaningful security escalation because any actor able to drive this stdin already controls the privileged shell channel and can directly execute stronger disruptive commands.
## Controls
- Bridge defaults to localhost (127.0.0.1) and single-client behavior.
- Serial channel generally implies physical/local operator trust.
- No explicit authentication/authorization on shell commands.
## Blindspots
- Static-only review cannot measure real-world frequency under hardware timing/latency.
- No runtime validation on actual device in this step; relied on provided PoC artifacts.
- If future versions expose this channel to broader networks, risk calibration could change.
