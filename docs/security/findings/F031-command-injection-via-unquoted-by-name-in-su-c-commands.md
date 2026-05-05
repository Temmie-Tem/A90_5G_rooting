# F031. Command injection via unquoted by_name in su -c commands

## Metadata

| field | value |
|---|---|
| finding_id | `b7c48a7ce9b08191b3ea1cbdbff18ee2` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/b7c48a7ce9b08191b3ea1cbdbff18ee2 |
| severity | `informational` |
| status | `new` |
| detected_at | `2026-04-27T22:44:02.496556Z` |
| committed_at | `2026-04-23 03:55:06 +0900` |
| commit_hash | `5812a3f34ef45b3c7a96b0c31cd1c9245f70445e` |
| relevant_paths | `scripts/revalidation/capture_baseline.sh` |
| has_patch | `false` |

## CSV Description

`by_name` is read from device command output and then reused in later root commands. In this commit, calls were rewritten from patterns like `su -c "test -e '$by_name/$part'"` to `su -c $(sq_escape "test -e $by_name/$part")`. This only protects the outer shell tokenization, not the inner shell evaluation performed by `su -c`. If `by_name` contains shell metacharacters (e.g., `$(...)`, backticks, `;`, newlines), they can be evaluated by the shell that `su -c` invokes, leading to unintended command execution as root on the device.

## Codex Cloud Detail

Command injection via unquoted by_name in su -c commands
Link: https://chatgpt.com/codex/cloud/security/findings/b7c48a7ce9b08191b3ea1cbdbff18ee2?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: informational (attack path: ignore)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 5812a3f
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오전 7:44:02
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Security bug introduced. The previous version single-quoted `by_name` inside the command string itself; the new version removed that inner quoting and now embeds `by_name` directly into root shell command text.
`by_name` is read from device command output and then reused in later root commands. In this commit, calls were rewritten from patterns like `su -c "test -e '$by_name/$part'"` to `su -c $(sq_escape "test -e $by_name/$part")`. This only protects the outer shell tokenization, not the inner shell evaluation performed by `su -c`. If `by_name` contains shell metacharacters (e.g., `$(...)`, backticks, `;`, newlines), they can be evaluated by the shell that `su -c` invokes, leading to unintended command execution as root on the device.

# Validation
## Rubric
- [x] Identify untrusted data flow: `by_name` is sourced from device command output (`capture_baseline.sh:91`).
- [x] Confirm sink construction: `by_name` is embedded unquoted in `su -c` command text (`:106`, `:110`, `:117`).
- [x] Reproduce with controlled input: fake `adb` returns metacharacter payload in `by_name`.
- [x] Demonstrate impact: payload command substitution executes (`/tmp/adb_su_pwned` created).
- [x] Differential validation and tooling attempts: parent script control run (no pwn marker for same payload), plus attempted crash/valgrind/gdb paths (valgrind/gdb unavailable; used `bash -x` trace).
## Report
Rubric-driven validation completed on `scripts/revalidation/capture_baseline.sh` in commit `5812a3f34ef45b3c7a96b0c31cd1c9245f70445e`.

Key code points:
- Tainted source: `by_name` comes from device command output at `scripts/revalidation/capture_baseline.sh:91`.
- Dangerous sinks interpolate `by_name` into command text passed to `su -c` at `:106`, `:110`, `:117`.

Dynamic PoC (non-interactive):
1. Built a fake `adb` shim that returns malicious `by_name`:
   `/tmp/fake_by_name$(echo INJECTED>/tmp/adb_su_pwned)`
2. Ran the target script with PATH pointing to the fake `adb`.
3. Evidence (`/workspace/validation_work/final_evidence.txt`):
   - `by_name=/tmp/fake_by_name$(echo INJECTED>/tmp/adb_su_pwned)` recorded in manifest.
   - `/tmp/adb_su_pwned` was created with content `INJECTED`.
   - Script still completed image pulls.
4. Debug-style trace (`bash -x`, `/workspace/validation_work/trace_new.log`) shows command chain preserving unquoted metacharacters into inner `su -c` command, e.g.:
   - `adb shell 'su -c '\''ls -l /tmp/fake_by_name$(echo INJECTED>/tmp/adb_su_pwned)'\'''`
   - same pattern for `test -e` and `dd if=...`.

Regression check (parent version):
- Extracted pre-commit script and ran same fake-ADB scenario.
- Control evidence (`/workspace/validation_work/final_control_evidence.txt`): `pwn marker exists: no`.
- Old script used inner quoting for `ls`/`test` (`"ls -l '$by_name'"`, `"test -e '$by_name/$part'"`), preventing execution for this payload.

Crash/valgrind/gdb attempts:
- `valgrind` and `gdb` are unavailable in container (`command not found`), so memory/crash tooling is not applicable here.
- Used `bash -x` trace as the bounded debugger-equivalent for shell execution flow.

# Evidence
scripts/revalidation/capture_baseline.sh (L106 to 106)
  Note: `by_name` is interpolated unquoted into command text (`ls -l $by_name`) before `su -c`, allowing inner-shell metacharacter interpretation.
```
"${adb_cmd[@]}" shell "su -c $(sq_escape "ls -l $by_name")" | trim_cr > "$output_dir/by_name_listing.txt"
```

scripts/revalidation/capture_baseline.sh (L110 to 110)
  Note: Same pattern in existence check (`test -e $by_name/$part`), vulnerable to command injection via crafted `by_name`.
```
    if ! "${adb_cmd[@]}" shell "su -c $(sq_escape "test -e $by_name/$part")" >/dev/null 2>&1; then
```

scripts/revalidation/capture_baseline.sh (L117 to 117)
  Note: Same pattern in `dd` execution (`dd if=$by_name/$part ...`), potentially enabling arbitrary root command execution.
```
    "${adb_cmd[@]}" exec-out "su -c $(sq_escape "dd if=$by_name/$part bs=4M status=none")" > "$out_file"
```

scripts/revalidation/capture_baseline.sh (L91 to 91)
  Note: `by_name` is populated from command output and treated as trusted input later.
```
by_name="$("${adb_cmd[@]}" shell "su -c $(sq_escape "$find_by_name_cmd")" 2>/dev/null | trim_cr || true)"
```

# Attack-path analysis
Final: ignore | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
The code-level injection claim is valid and PoC-backed, but the vulnerable component is a local experimental helper script for a single rooted phone, not an exposed product service. Practical attacker reachability is limited to scenarios where the attacker already controls adb/device responses (or equivalent local environment), making this primarily self-impact and outside typical in-scope external threat surfaces. Therefore triage criticality is downgraded from medium to ignore for security prioritization in this repo context.
## Likelihood
low - Exploitation requires uncommon preconditions (control over device/adb output in this local lab workflow). No public interface or remote trigger exists in repo artifacts.
## Impact
low - If reached, attacker-controlled by_name can execute arbitrary commands as root on the attached device. But impact is constrained to that single device and does not expose a broader service/control plane.
## Assumptions
- This repository is a local device-revalidation workspace, not an internet-facing service.
- scripts/revalidation/capture_baseline.sh is run manually by the device owner/operator.
- No broader enterprise/fleet threat model is defined in-repo for hostile external users targeting this script.
- Operator runs scripts/revalidation/capture_baseline.sh
- ADB-connected device is present and responds to shell commands
- Magisk su -c path is available
- Attacker can influence by_name value returned from device-side command output (or adb shim)
## Path
n1 Operator
  -> n2 read by_name (adb/su)
  -> n3 tainted by_name
  -> n4 su -c "... $by_name ..."
  -> n5 root command execution on device
## Path evidence
- `scripts/revalidation/capture_baseline.sh:91` - by_name is read from adb shell su -c output (tainted source).
- `scripts/revalidation/capture_baseline.sh:106` - by_name is interpolated into su -c ls command string.
- `scripts/revalidation/capture_baseline.sh:110` - by_name is interpolated into su -c test command string.
- `scripts/revalidation/capture_baseline.sh:117` - by_name is interpolated into su -c dd command string.
- `scripts/revalidation/README.md:19-24` - Script is intended for manual local execution in revalidation workflow.
- `docs/plans/REVALIDATION_PLAN.md:14-21` - Workflow assumes one rooted device with su/ADB available.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_5812a3f34ef45b3c7a96b0c31cd1c9245f70445e/extracted/by_name_injection_artifacts/final_evidence.txt:1-8` - Executable PoC evidence shows injected marker file creation via by_name payload.
## Narrative
The injection primitive is real in code: by_name is sourced from device command output and then embedded into su -c command strings used for ls/test/dd. Validation artifacts include an executable PoC demonstrating command substitution execution. However, repository context shows this is a local, manual rooted-device lab script with no network exposure; realistic exploitation requires control of device/adb output in an operator-run workflow, making it largely self-impact and out of main external threat scope.
## Controls
- Manual operator-triggered script execution
- Requires connected authorized ADB device
- Requires su availability on target device
- Local/private workflow (no network ingress component)
## Blindspots
- No explicit formal threat model document in-repo; scope inferred from README/plans.
- Static review cannot prove how easily real devices can manipulate by_name path output without prior high privilege.
- No fleet/deployment manifests exist to assess broader operational exposure.
