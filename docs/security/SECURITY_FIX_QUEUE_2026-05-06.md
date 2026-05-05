# Security Fix Queue

Date: 2026-05-06

Source relationship analysis: `docs/security/SECURITY_FINDINGS_RELATIONSHIP_2026-05-06.md`
Current exposure map: `docs/security/SECURITY_FINDINGS_CURRENT_EXPOSURE_2026-05-06.md`

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
- Batch 0 output is recorded in `docs/security/SECURITY_FINDINGS_CURRENT_EXPOSURE_2026-05-06.md`.

## Batch 1: Remote Root Control Surface Hardening

Status: complete in `A90 Linux init 0.9.23 (v123)`.

Report: `docs/reports/NATIVE_INIT_V123_SECURITY_BATCH1_2026-05-06.md`

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

Implemented version:

- `v123`: tcpctl auth/bind policy, ramdisk tcpctl helper path, dangerous service gate, and reconnect cleanup fail-closed.

Validation:

- `tcpctl` rejects unauthenticated `run`/`shutdown` commands.
- `netservice status/start/stop` still works through intended local control.
- `rshell start` no longer implicitly exposes unauthenticated tcpctl.
- host reconnect validators fail if cleanup leaves tcpctl running.
- USB ACM and localhost serial bridge remain documented trusted-lab-only root control paths.

## Batch 2: Runtime Storage and Helper Trust

Status: complete in `A90 Linux init 0.9.24 (v124)`.

Report: `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md`

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

Implemented version:

- `v124`: helper manifest SHA-256 verification, runtime-root path policy, no-follow storage/log writes, mountsd SD identity gate, and host tcpctl install fail-closed rollback.

Validation:

- unverified SD runtime `busybox` remains non-preferred and produces a helper warning instead of execution preference.
- `a90_cpustress` and `a90_tcpctl` continue to select ramdisk helpers.
- `storage`/`mountsd status` verify the expected SD UUID before SD log use.
- `tcpctl_host.py install` refuses the default `/bin/a90_tcpctl` ramdisk target and uses temp-file replacement for allowed runtime/cache targets.

## Batch 3: Host Tooling Trust Boundary

Status: complete in host tooling Batch 3. No native image bump was needed for
Batch 3 itself.

Report: `docs/reports/NATIVE_INIT_SECURITY_BATCH3_HOST_TOOLING_2026-05-06.md`

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

Implemented scope:

- host path resolution, remote shell quoting, and temporary-file fixes.
- cmdv1 retry/framing parser hardening.
- host NCM interface explicit selection and serial bridge identity pinning.

Validation:

- running host scripts from untrusted CWD does not execute local attacker paths.
- non-idempotent cmdv1 commands are not retried automatically.
- fake `A90P1 END` in command output cannot forge result status.
- host NIC reconfiguration requires explicit operator-selected interface.

## Batch 4: Logs, Diagnostics, and On-Screen Disclosure

Status: complete in `A90 Linux init 0.9.25 (v125)`.

Report: `docs/reports/NATIVE_INIT_V125_SECURITY_BATCH4_2026-05-06.md`

Findings:

- F009: diagnostics bundles weak permissions
- F024: HUD log tail information disclosure
- F025: world-readable fallback log

Implementation direction:

- Use `0700` directories and `0600` files for logs/diagnostics.
- Redact sensitive command args, helper paths, and service tokens in diagnostic output.
- Add HUD privacy mode or log-tail opt-in gate.
- Avoid `/tmp` fallback for sensitive logs, or create private fallback directory first.

Implemented version:

- `v125`: private runtime log/state directories, owner-only diagnostic outputs,
  private emergency fallback log path, and opt-in HUD log tail.

Validation:

- device and host diagnostic outputs are not world-readable under normal umask.
- HUD log tail is disabled by default and requires explicit `hudlog on`.
- default `diag full` and stored bundles omit/redact native log tails.

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

Batch 0 through Batch 4 are complete. Continue with Batch 5 legacy high-impact
tooling cleanup before Wi-Fi or broader network work.

Reason:

```text
Wi-Fi increases reachability.
Reachability makes unauthenticated root-control paths materially worse.
Therefore tcpctl/rshell/netservice authentication and bind policy should precede Wi-Fi active bring-up.
```
