# F022. Predictable /tmp file in BusyBox build validation

## Metadata

| field | value |
|---|---|
| finding_id | `91a0342469308191ada6eaa2453cb478` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/91a0342469308191ada6eaa2453cb478 |
| severity | `low` |
| status | `mitigated-host-batch3` |
| detected_at | `2026-05-04T10:31:59.152488Z` |
| committed_at | `2026-05-03 22:36:11 +0900` |
| commit_hash | `2c69abe3468adaf35aa38b5018868fcbf77c59e5` |
| relevant_paths | `scripts/revalidation/build_static_busybox.sh` |
| has_patch | `true` |

## CSV Description

scripts/revalidation/build_static_busybox.sh stores readelf output in the hard-coded path /tmp/a90_busybox_dynamic_check.txt. Because /tmp is shared, another local user can pre-create this path as a symlink or controlled file before the operator runs the script. On systems without symlink protections, the redirection can overwrite an arbitrary file writable by the operator. Even when redirection fails, the command is masked with `|| true`, so the subsequent `cat`/`grep` can consume stale attacker-controlled contents and potentially bypass the dynamic-section validation. Use `mktemp` with a private file, a trap for cleanup, and avoid ignoring redirection/readelf failures; alternatively write the check output under the script-owned build directory.

## Local Remediation

- Batch 3 replaces the predictable `/tmp/a90_busybox_dynamic_check.txt` with a `mktemp` file removed by an EXIT trap.

## Codex Cloud Detail

Predictable /tmp file in BusyBox build validation
Link: https://chatgpt.com/codex/cloud/security/findings/91a0342469308191ada6eaa2453cb478?repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting&sev=&page=2
Criticality: low (attack path: low)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 2c69abe
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:31:59
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
A security-relevant local temporary-file handling bug was introduced in the newly added BusyBox build script. A similar pattern exists elsewhere, but this commit adds a new exploitable instance for the BusyBox workflow.
scripts/revalidation/build_static_busybox.sh stores readelf output in the hard-coded path /tmp/a90_busybox_dynamic_check.txt. Because /tmp is shared, another local user can pre-create this path as a symlink or controlled file before the operator runs the script. On systems without symlink protections, the redirection can overwrite an arbitrary file writable by the operator. Even when redirection fails, the command is masked with `|| true`, so the subsequent `cat`/`grep` can consume stale attacker-controlled contents and potentially bypass the dynamic-section validation. Use `mktemp` with a private file, a trap for cleanup, and avoid ignoring redirection/readelf failures; alternatively write the check output under the script-owned build directory.

# Validation
## Rubric
- [x] Confirm the vulnerable script and lines were introduced in this commit.
- [x] Confirm the script uses a hard-coded shared /tmp pathname for security-relevant readelf validation.
- [x] Confirm failures at the readelf/redirection step are masked by `|| true` and the later check trusts file contents anyway.
- [x] Reproduce a negative control where actual dynamic-section output causes the script to fail.
- [x] Reproduce attacker influence over the predictable temp path causing validation bypass, and assess symlink overwrite behavior/environmental constraints.
## Report
Validated the finding against commit 2c69abe3468adaf35aa38b5018868fcbf77c59e5. The parent commit does not contain scripts/revalidation/build_static_busybox.sh, so this instance was introduced by the checked-out commit. The vulnerable code is present at scripts/revalidation/build_static_busybox.sh:152-154: readelf output is redirected to the predictable shared path /tmp/a90_busybox_dynamic_check.txt, the command/redirection failure is masked with `|| true`, and subsequent `cat`/`grep` trust that same path. I exercised the real script with mocked toolchain commands to avoid downloading/building BusyBox while still reaching the vulnerable block. Control case: with no preexisting temp file, mocked `readelf -d` reported a dynamic section and the script failed as intended: output included `Dynamic section at offset 0x123...`, `warning: dynamic section found; binary may not be static`, and `CONTROL_RC=1`. Attack case: a distinct attacker user pre-created `/tmp/a90_busybox_dynamic_check.txt` as world-readable but not writable by the operator, containing `There is no dynamic section in this file.`. Running the real script as the operator produced `/workspace/A90_5G_rooting/scripts/revalidation/build_static_busybox.sh: line 152: /tmp/a90_busybox_dynamic_check.txt: Permission denied`, then printed the stale attacker-controlled content, and exited successfully with `ATTACK_RC=0`. This confirms the `|| true` masking plus trusted predictable file can bypass the static/dynamic validation. I also demonstrated symlink clobber behavior using an operator-owned symlink at the predictable path: the script followed `/tmp/a90_busybox_dynamic_check.txt -> /tmp/av_operator_target.txt` and overwrote the target with readelf output. Cross-user symlink following is protected in this container (`fs.protected_symlinks=1`), matching the finding's caveat that arbitrary symlink overwrite depends on host symlink protections. Crash/Valgrind/debugger validation is not applicable to this shell temporary-file logic bug; additionally valgrind and gdb were not installed in the container.

# Evidence
scripts/revalidation/build_static_busybox.sh (L152 to 154)
  Note: The script writes readelf output to a predictable shared /tmp path, ignores failures with `|| true`, then trusts the same path for cat/grep validation.
```
aarch64-linux-gnu-readelf -d "${OUT_BIN}" >/tmp/a90_busybox_dynamic_check.txt 2>&1 || true
cat /tmp/a90_busybox_dynamic_check.txt
if ! grep -q "There is no dynamic section" /tmp/a90_busybox_dynamic_check.txt; then
```

# Attack-path analysis
Final: low | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Severity remains low. The vulnerability is real and in-scope for host-side operational tooling, with code evidence at scripts/revalidation/build_static_busybox.sh:152-154 and documented workflow evidence in scripts/revalidation/README.md:49-53. However, the attack path is local-only, requires operator interaction, and the main demonstrated outcomes are validation bypass or file clobber limited to files writable by the operator. Host symlink protections can further reduce clobber impact. These constraints keep both likelihood and impact low in the repository's threat model.
## Likelihood
low - Exploitation requires local access to the build host, pre-creation of a specific /tmp path, and an operator running the script. Shared lab or CI hosts make this plausible, but default single-operator use makes exploitation unlikely. There is no public ingress or network listener involved.
## Impact
low - A successful attack can bypass a build validation check or overwrite an operator-writable file in permissive/same-user conditions. It does not directly grant remote code execution, device root access, credentials, or broad data exposure. The affected surface is a local host build script rather than the runtime command channel.
## Assumptions
- The script is run manually by a trusted operator on a host workstation or shared lab/CI host.
- A realistic attacker for this finding is another local user or process able to pre-create files in the shared /tmp directory before the operator runs the script.
- The script runs with the operator's normal local OS permissions; no repository evidence indicates this BusyBox build script itself requires sudo.
- Cross-user symlink overwrite impact depends on host kernel hardening such as protected_symlinks/protected_regular; same-user or weakly hardened hosts remain more exposed.
- Attacker has local access to the same build host or can run a process that writes to /tmp.
- Attacker pre-creates /tmp/a90_busybox_dynamic_check.txt as a controlled file or symlink before script execution.
- Operator runs scripts/revalidation/build_static_busybox.sh and reaches the readelf validation block.
- For arbitrary file clobber, the target must be writable by the operator and host symlink/file protections must allow the write path.
## Path
Local attacker
  -> pre-create /tmp/a90_busybox_dynamic_check.txt
  -> operator runs build_static_busybox.sh
  -> readelf redirection failure is ignored / file is trusted
  -> static validation bypass or writable-file clobber
## Path evidence
- `scripts/revalidation/build_static_busybox.sh:152-154` - Vulnerable sequence: readelf output is redirected to a hard-coded shared /tmp path, failure is suppressed with `|| true`, and the same path is trusted by cat and grep.
- `scripts/revalidation/build_static_busybox.sh:147-150` - There is a prior INTERP-segment staticness check, which partially limits some dynamic-binary bypass scenarios but does not fix the predictable temp-file bug.
- `scripts/revalidation/README.md:49-53` - The repository documents build_static_busybox.sh as the intended script for building static ARM64 BusyBox artifacts used in v99 validation.
- `docs/reports/NATIVE_INIT_V99_BUSYBOX_USERLAND_2026-05-03.md:22-29` - The v99 report confirms the BusyBox build script and produced artifact are part of the project's documented workflow.
## Narrative
The finding is real: the BusyBox build script writes security-relevant readelf validation output to a predictable shared /tmp path, ignores failure, and then trusts that path for cat/grep. Repository documentation shows this script is an intended host-side build artifact path for v99 BusyBox evaluation, so it is in scope. The attack is local-only and requires user interaction by the operator running the build script. Impact is limited to the operator's local context and build validation integrity, with symlink clobber depending on host hardening. This supports the original low severity rather than escalation.
## Controls
- Tarball SHA-256 verification before build
- set -euo pipefail at script start
- Prior INTERP program-header check before the dynamic-section temp-file check
- No public network exposure for this script
- Host kernel symlink protections may mitigate cross-user symlink clobber on hardened systems
## Blindspots
- Static review cannot determine whether downstream users run this script on shared multi-user hosts or CI runners.
- Static review cannot determine host kernel hardening settings such as protected_symlinks and protected_regular.
- The precise downstream effect of accepting a non-static BusyBox artifact depends on deployment steps and whether an attacker can also influence the built binary or toolchain.
- No cloud, Kubernetes, or deployment manifests were relevant to this local build-script issue.
