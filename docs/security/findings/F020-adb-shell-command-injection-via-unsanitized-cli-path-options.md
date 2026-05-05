# F020. ADB shell command injection via unsanitized CLI path options

## Metadata

| field | value |
|---|---|
| finding_id | `177a42c608b88191b083f1a1034515c2` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/177a42c608b88191b083f1a1034515c2 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-04-28T09:18:43.256101Z` |
| committed_at | `2026-04-25 01:56:45 +0900` |
| commit_hash | `5ee4cb0c923e562c68a420cbfd642fc08983d65d` |
| relevant_paths | `scripts/revalidation/native_init_flash.py` |
| has_patch | `false` |

## CSV Description

`scripts/revalidation/native_init_flash.py` concatenates `--remote-image` and `--boot-block` directly into shell command strings passed to `adb shell`. Because `adb shell <string>` is interpreted by a remote shell, metacharacters (e.g. `;`, `&&`, backticks, `$()`) in these arguments can execute unintended extra commands as recovery/root on the device. This is introduced in this commit with the new script. In a strictly trusted single-operator workflow this is less likely, but if arguments are sourced from untrusted input (shared automation, copied command lines, CI parameters), it becomes a command-injection primitive.

## Codex Cloud Detail

ADB shell command injection via unsanitized CLI path options
Link: https://chatgpt.com/codex/cloud/security/findings/177a42c608b88191b083f1a1034515c2?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 5ee4cb0
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 6:18:43
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced bug: command injection in remote shell command construction for both hash verification and flashing paths.
`scripts/revalidation/native_init_flash.py` concatenates `--remote-image` and `--boot-block` directly into shell command strings passed to `adb shell`. Because `adb shell <string>` is interpreted by a remote shell, metacharacters (e.g. `;`, `&&`, backticks, `$()`) in these arguments can execute unintended extra commands as recovery/root on the device. This is introduced in this commit with the new script. In a strictly trusted single-operator workflow this is less likely, but if arguments are sourced from untrusted input (shared automation, copied command lines, CI parameters), it becomes a command-injection primitive.

# Validation
## Rubric
- [x] Confirm target commit introduced the vulnerable script/path (`git show` shows `native_init_flash.py` added in `5ee4cb0`).
- [x] Verify unquoted user-controlled interpolation into `adb shell` command strings (`remote_sha256` at lines 99-103; flash command at 176-180).
- [x] Verify attack surface is reachable from CLI arguments with no validation (`--remote-image`, `--boot-block` at 211-212).
- [x] Reproduce injection effects with a minimal PoC against real script functions (marker files created by injected commands in both paths).
- [x] Attempt higher-priority native-memory validation modes first: crash attempt made (not applicable to this Python command-injection class), valgrind/gdb checked but unavailable in container (`command not found`), then finalized via code-understanding + dynamic PoC.
## Report
I validated the suspected command-injection finding in `scripts/revalidation/native_init_flash.py` at commit `5ee4cb0c923e562c68a420cbfd642fc08983d65d`.

Key code evidence:
- `remote_sha256()` builds `adb shell` with direct string interpolation of `remote_path` (`scripts/revalidation/native_init_flash.py:99-103`): `f"sha256sum {remote_path} ... || toybox sha256sum {remote_path}"`.
- `flash_boot_image()` builds `flash_cmd` with direct interpolation of `args.remote_image` and `args.boot_block` then passes it to `adb shell` (`:176-180`).
- CLI inputs are user-controllable and unsanitized (`--remote-image`, `--boot-block`) (`:211-212`).
- `git show` confirms this file was introduced in the target commit (new file in `5ee4cb0`).

Dynamic reproduction (non-interactive PoC):
- I created a fake `adb` shim that emulates `adb shell <string>` via `/bin/sh -c` and logs executed shell command strings.
- Ran `python3 /workspace/validation_artifacts/native_init_flash_injection/poc_injection.py`.
- PoC output showed successful payload execution in both vulnerable paths:
  - `marker_remote_sha_exists=True`, `marker_remote_sha_content=remote_sha_injected`
  - `marker_flash_exists=True`, `marker_flash_content=flash_injected`
- Logged shell commands in `fake_adb.log` include injected metacharacter payloads (`;` and `#`) inside the exact strings passed by the script.

This confirms command injection is reachable when untrusted values are provided for `remote_path`/`--remote-image`/`--boot-block` and the script invokes `adb shell` with concatenated command strings.

# Evidence
scripts/revalidation/native_init_flash.py (L176 to 180)
  Note: `args.remote_image` and `args.boot_block` are concatenated into a single shell command for `adb shell`, allowing metacharacter-based command injection.
```
    flash_cmd = (
        f"dd if={args.remote_image} of={args.boot_block} "
        "bs=4M conv=fsync && sync"
    )
    run_command(adb_base(serial) + ["shell", flash_cmd])
```

scripts/revalidation/native_init_flash.py (L211 to 212)
  Note: These CLI options feed directly into the vulnerable shell command construction paths with no validation or escaping.
```
    parser.add_argument("--remote-image", default=DEFAULT_REMOTE_IMAGE)
    parser.add_argument("--boot-block", default="/dev/block/by-name/boot")
```

scripts/revalidation/native_init_flash.py (L99 to 103)
  Note: User-controlled `remote_path` is interpolated directly into an `adb shell` command string without quoting, enabling shell injection.
```
def remote_sha256(serial: str | None, remote_path: str) -> str:
    command = adb_base(serial) + [
        "shell",
        f"sha256sum {remote_path} 2>/dev/null || toybox sha256sum {remote_path}",
    ]
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Kept at medium. Technical impact is high (root command execution on device), but exploitability depends on a narrower precondition: attacker must control parameters passed to a local operational script and have the operator run it against a connected device. This is in-scope per threat model (host tooling + flashing boundary) and demonstrably real via PoC, but lacks broad unauthenticated remote reach.
## Likelihood
low - Requires attacker influence over operator-provided script arguments (shared host/automation/CI), so not broadly exposed by default single-operator workflow.
## Impact
high - Successful exploitation executes arbitrary commands on the device in recovery/root context and can alter critical partitions or boot state.
## Assumptions
- Attacker can influence script arguments (direct CLI, shared automation, CI/job parameters, or copied command snippets).
- Operator runs scripts/revalidation/native_init_flash.py against a connected device in TWRP/recovery.
- adb shell in that state has sufficient privilege to execute dd and other root-level commands on-device.
- Ability to supply or alter --remote-image or --boot-block (or remote_path input to remote_sha256 path)
- Operator executes vulnerable script
- ADB connectivity to target device
## Path
[CLI/automation input] -> [f-string command build] -> [adb shell parses string] -> [root command exec on device]
## Path evidence
- `scripts/revalidation/native_init_flash.py:99-103` - remote_path is directly interpolated into an adb shell string used for sha256 computation.
- `scripts/revalidation/native_init_flash.py:176-180` - flash_cmd concatenates --remote-image and --boot-block into one shell command passed to adb shell.
- `scripts/revalidation/native_init_flash.py:211-212` - CLI arguments feeding vulnerable sinks are user-supplied and not validated/sanitized.
- `scripts/revalidation/README.md:29-33` - Script is documented as normal operational flashing workflow, confirming in-scope usage.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_5ee4cb0c923e562c68a420cbfd642fc08983d65d/extracted/native_init_flash_injection/fake_adb.log:1-7` - PoC log shows metacharacter payloads embedded in adb shell strings and executed.
## Narrative
The finding is valid: scripts/revalidation/native_init_flash.py interpolates attacker-influenceable values directly into adb shell command strings, which are interpreted by a remote shell. Repo evidence shows unsanitized interpolation in both hash and flash paths, and executable PoC evidence demonstrates injected commands creating marker files. Reachability is realistic in shared automation/parameterized workflows, but not broadly remote by default; impact is high on a targeted device, with overall severity best kept at medium due preconditions.
## Controls
- Host-side subprocess.run uses argument lists (no host shell=True), reducing local shell injection only.
- Image hash checks exist for integrity workflow but do not mitigate command-string injection sink.
- Default boot block/path values reduce accidental misuse but remain overrideable.
## Blindspots
- Static review cannot measure how often arguments are sourced from untrusted CI/job inputs in real deployment.
- No live-device verification here of exact privilege mode across all recovery images; assessed from script intent and documented workflow.
- Repository-only scope: no enterprise network controls, host hardening, or CI trust boundaries were inspected.
