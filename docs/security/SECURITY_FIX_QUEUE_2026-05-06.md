# Security Fix Queue

Date: 2026-05-06

Source relationship analysis: `docs/security/SECURITY_FINDINGS_RELATIONSHIP_2026-05-06.md`

This queue groups the 31 Codex security findings into implementation batches.
The batch order is based on exploit chain reduction, not only finding severity.

## Batch 0: Confirm Current Exposure

Goal: avoid fixing obsolete paths blindly while still treating the findings as real until disproven.

Tasks:

- Map each finding to current latest source around `v122`.
- Mark each finding as `current`, `legacy-only`, `host-tooling`, or `needs-runtime-check`.
- Run `rg` for central sinks: `a90_tcpctl`, `netservice`, `rshell`, `cmdv1`, `native-init-netservice`, `/cache/bin`, `mountsd`, `diag`.
- Decide which legacy versions remain supported rebuild targets.

Acceptance:

- A status column exists for all F001 through F031.
- No finding is closed only because it originated in an old version if the same pattern still exists in shared modules.

## Batch 1: Remote Root Control Surface Hardening

Findings:

- F005: unauthenticated NCM tcpctl root command execution
- F001: rshell start exposes tcpctl root command port
- F003: boot flag enables persistent tcpctl exposure
- F010: service command bypasses dangerous-command gating
- F014: reconnect checker can leave tcpctl running
- F021: unauthenticated USB ACM root shell enabled at boot
- F023: auto-menu busy gate bypass
- F030: unauthenticated USB ACM and TCP bridge root shell

Implementation direction:

- Add tcpctl authentication or remove remote `run` from tcpctl until authenticated.
- Bind tcpctl to the intended NCM address only.
- Make tcpctl/netservice/rshell default-off and non-persistent unless explicitly enabled.
- Treat `service start/enable tcpctl|rshell|adbd` as dangerous through controller policy.
- Make reconnect/soak cleanup fail closed when tcpctl remains active.
- Document USB ACM shell and local bridge as trusted-lab-only control channels.

Suggested version theme:

- `v123`: tcpctl auth/bind policy and dangerous service gate.
- `v124`: host reconnect cleanup fail-closed and bridge exposure documentation.

Validation:

- `tcpctl` rejects unauthenticated commands.
- `netservice status/start/stop` still works through intended local control.
- `rshell start` does not implicitly expose unauthenticated tcpctl.
- host reconnect validators fail if cleanup leaves tcpctl running.

## Batch 2: Runtime Storage and Helper Trust

Findings:

- F002: helper manifest redirects cpustress to unverified code
- F004: tcpctl_host install race allows helper replacement
- F011: runtime SD probes follow symlinks as root
- F012: mountsd redirects logs to unverified SD media
- F013: v79 SD probe symlink root clobber

Implementation direction:

- Require helper hash verification before runtime helper preference.
- Keep ramdisk helper as fallback/canonical helper if runtime helper verification is missing or failed.
- Use no-follow safe file creation for probes/logs where supported.
- Validate path components under SD/cache runtime roots.
- Make `mountsd rw/init` enforce expected SD identity before log redirection.
- Delete or quarantine failed helper installs.

Suggested version theme:

- `v125`: helper manifest verification and tcpctl install rollback.
- `v126`: SD/cache safe-open and mountsd log trust policy.

Validation:

- crafted symlink under SD/cache cannot redirect PID1 writes.
- invalid helper manifest never becomes preferred execution path.
- failed helper install cannot leave executable poison at target path.

## Batch 3: Host Tooling Trust Boundary

Findings:

- F008: soak validator executes a90ctl from untrusted CWD
- F015: cmdv1 retry replays privileged commands
- F016: cmdv1 framing spoof through injected END
- F017: untrusted MAC triggers sudo wrong NIC reconfig
- F018: untrusted device MAC drives sudo host network reconfiguration
- F019: auto re-enumeration bridge device hijack
- F020: adb shell command injection
- F022: predictable `/tmp` file
- F031: unquoted by-name in `su -c`

Implementation direction:

- Resolve all repo scripts through absolute paths from `__file__`.
- Use `cwd=REPO_ROOT` in revalidation subprocesses.
- Restrict cmdv1 retry to idempotent observation commands by default.
- Escape or length-prefix framed payloads so child output cannot spoof `A90P1 END`.
- Require explicit host interface argument or allowlist before `sudo ip`.
- Pin serial device identity across reconnect.
- Replace shell strings with argv arrays.
- Use `mktemp -d` or Python temporary directories for build validation.

Suggested version theme:

- `v127`: host path/shell injection fixes.
- `v128`: cmdv1 framing/retry hardening.
- `v129`: host USB/NCM identity pinning.

Validation:

- running host scripts from untrusted CWD does not execute local attacker paths.
- non-idempotent cmdv1 commands are not retried automatically.
- fake `A90P1 END` in command output cannot forge result status.
- host NIC reconfiguration requires explicit operator-selected interface.

## Batch 4: Logs, Diagnostics, and On-Screen Disclosure

Findings:

- F009: diagnostics bundles weak permissions
- F024: HUD log tail information disclosure
- F025: world-readable fallback log

Implementation direction:

- Use `0700` directories and `0600` files for logs/diagnostics.
- Redact sensitive command args, helper paths, and service tokens in diagnostic output.
- Add HUD privacy mode or log-tail opt-in gate.
- Avoid `/tmp` fallback for sensitive logs, or create private fallback directory first.

Suggested version theme:

- `v130`: log/diagnostic permissions and HUD privacy mode.

Validation:

- device and host diagnostic outputs are not world-readable under normal umask.
- HUD log tail can be disabled and does not show sensitive values by default.

## Batch 5: Legacy High Impact Tools

Findings:

- F006: hardcoded root SSH credentials
- F007: unsafe archive extraction

Implementation direction:

- Remove default root password automation.
- Disable password auth or require operator-provided credentials.
- Validate archive members before extraction.
- Reject traversal, absolute paths, symlinks, hardlinks, devices, and special files.

Suggested version theme:

- can be fixed independently before or during v123-v130 because it is host/rootfs tooling, not native init boot flow.

Validation:

- no script writes `root:root` or starts SSH with known default credential.
- malicious archive fixture cannot write outside extraction directory.

## Batch 6: Historical Reproducibility and Reliability

Findings:

- F026: metrics refactor breaks older builds
- F027: v84 changelog detail blank
- F028: v42 run cancel steals child stdin
- F029: input event path traversal in old helper

Implementation direction:

- Define retained historical build support window.
- Add rollback build validation for the supported window.
- Add compatibility wrappers or version-pinned headers where needed.
- Apply strict `event[0-9]+` validation to input helper paths.
- Fix low-risk UI regression where retained historical versions are still used.

Suggested version theme:

- `v131`: historical build/rollback support policy and compatibility cleanup.

Validation:

- supported rollback versions build.
- input event arguments cannot escape event-node scope.

## Recommended Immediate Next Step

Start with Batch 0 and Batch 1 before Wi-Fi or broader network work.

Reason:

```text
Wi-Fi increases reachability.
Reachability makes unauthenticated root-control paths materially worse.
Therefore tcpctl/rshell/netservice authentication and bind policy should precede Wi-Fi active bring-up.
```
