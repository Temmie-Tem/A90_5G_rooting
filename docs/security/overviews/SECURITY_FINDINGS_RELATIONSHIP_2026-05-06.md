# Codex Security Findings Relationship Analysis

Date: 2026-05-06

Source:

- CSV: `docs/security/scans/codex-security-findings-2026-05-05T16-26-57.929Z.csv`
- Split index: `docs/security/findings/README.md`
- Finding details: `docs/security/findings/F001-*.md` through `docs/security/findings/F031-*.md`

## Summary

31개 finding은 개별 버그라기보다 몇 개의 같은 신뢰 경계 문제에서 파생된다.
특히 Wi-Fi나 외부 네트워크를 본격적으로 붙이기 전에는 `tcpctl`/root shell 노출, host tooling 신뢰 경계, SD/cache writable runtime trust를 먼저 정리해야 한다.

Severity count:

| severity | count |
|---|---:|
| high | 7 |
| medium | 14 |
| low | 4 |
| informational | 6 |

## Root Cause Groups

| group | theme | related findings | primary risk |
|---|---|---|---|
| G1 | Unauthenticated root control surfaces | F001, F003, F005, F010, F014, F021, F023, F030 | USB/NCM/TCP/serial 경로에서 root command execution 또는 위험 서비스 활성화 |
| G2 | Writable runtime trust and helper execution | F002, F004, F011, F012, F013 | SD/cache/runtime helper 조작으로 root write, helper replacement, persistence |
| G3 | Host tooling trust boundary failures | F008, F015, F016, F017, F018, F019, F020, F022, F031 | host에서 sudo, adb, bridge, cmdv1, path 처리 실수로 host/device compromise |
| G4 | Sensitive log and diagnostics disclosure | F009, F024, F025 | log/diagnostics/HUD tail이 command activity와 system state를 노출 |
| G5 | Legacy or side-track high impact tooling | F006, F007 | chroot SSH 기본 root credential, unsafe archive extraction |
| G6 | Historical reproducibility and UX regressions | F026, F027, F028, F029 | 최신 보안 노출보다는 rollback/build/input reliability 문제 |

## G1: Unauthenticated Root Control Surfaces

### Related findings

- F005 is the core issue: `a90_tcpctl` accepts unauthenticated network commands and can run absolute-path binaries as root.
- F001 turns `rshell` into an accidental `tcpctl` exposure path because `rshell_start_service()` can start netservice/tcpctl as a side effect.
- F003 makes the same tcpctl exposure persistent by trusting a boot flag and `/cache/bin` helpers.
- F014 shows host validation can leave tcpctl running after tests even when cleanup fails.
- F010 and F023 are policy bypasses: dangerous command gating can be bypassed through service/menu state paths.
- F021 and F030 are the older USB ACM/bridge form of the same unauthenticated root shell model.

### Relationship

`tcpctl` is the central sink. `netservice`, `rshell`, boot flags, reconnect tests, and service commands are activation paths into that sink.
Fixing only one activation path does not remove the class if `tcpctl` itself remains unauthenticated or binds broadly.

Primary chain:

```text
USB/NCM reachable host
  -> netservice or rshell enables NCM/tcpctl
  -> tcpctl listens without auth
  -> remote client sends run <absolute-path>
  -> PID1/root execve path
```

Persistence chain:

```text
writable /cache flag/helper
  -> boot-time netservice autostart
  -> tcpctl exposed again after reboot
  -> unauthenticated root run command
```

### Fix direction

Treat `tcpctl` as unsafe-by-default until it has authentication and narrow bind policy.
Recommended baseline:

- default OFF for tcpctl/rshell/netservice autostart;
- bind to NCM device IP only, not `INADDR_ANY`;
- require one-time or boot-session token for remote control;
- split observation commands from command-execution commands;
- make dangerous service activation require explicit local serial confirmation or policy override;
- make cleanup failure in host tests fail closed.

## G2: Writable Runtime Trust and Helper Execution

### Related findings

- F002 allows helper manifest/runtime package to redirect `cpustress` to unverified code.
- F004 allows `tcpctl_host install` races to replace `/cache/bin/a90_tcpctl`.
- F011 and F013 are root symlink/clobber issues from SD/runtime boot probes.
- F012 redirects logs to unverified SD media from interactive `mountsd`.

### Relationship

This group is the storage-side counterpart to G1. G1 exposes root command surfaces; G2 gives attackers a way to plant or redirect files those root paths later trust.

Attack chain:

```text
attacker-controlled SD/cache/runtime content
  -> helper path, boot flag, log path, or probe path is trusted
  -> PID1 follows symlink or executes helper as root
  -> persistence or root file clobber
```

### Fix direction

Make runtime storage explicitly untrusted until proven otherwise.
Recommended baseline:

- verify helper hashes before preferred selection;
- use immutable ramdisk helper unless runtime helper passes identity/hash checks;
- use `O_NOFOLLOW`, `openat()`, directory fd anchoring, and strict type checks for SD/cache writes;
- make SD identity check mandatory before log redirection;
- avoid predictable probe filenames or create them with no-follow exclusive semantics;
- separate operator convenience storage from trusted execution storage.

## G3: Host Tooling Trust Boundary Failures

### Related findings

- F008 runs `a90ctl.py` from untrusted current working directory.
- F015 makes cmdv1 retry at-least-once and can replay privileged commands.
- F016 lets command output spoof `A90P1 END` framing.
- F017 and F018 let untrusted device MAC/interface data drive host `sudo ip` reconfiguration.
- F019 can bridge the wrong ACM device after re-enumeration.
- F020 and F031 are shell command injection issues in host scripts.
- F022 uses predictable `/tmp` paths in build validation.

### Relationship

These are not one device-side bug. They are host automation trust boundary bugs.
The repeated pattern is that data from the device, current directory, CLI paths, or temporary filesystem is treated as trusted while scripts may run with sudo or operator privileges.

Primary chains:

```text
untrusted CWD
  -> relative script path
  -> host executes attacker-controlled a90ctl.py
```

```text
device-provided MAC/interface
  -> host helper chooses NIC
  -> sudo ip addr/link modifies wrong interface
```

```text
bridge reconnect or command output injection
  -> host parser misattributes device/result
  -> privileged command replay or spoofed PASS
```

### Fix direction

Host tooling should be treated like deployment tooling, not convenience scripts.
Recommended baseline:

- resolve all repo tools from `__file__` and use `cwd=REPO_ROOT`;
- never parse device output as authoritative framing unless escaped and length-bound;
- separate retryable observation commands from non-idempotent privileged commands;
- require host interface allowlist or explicit confirmation before `sudo ip`;
- pin serial device identity across re-enumeration;
- quote or avoid shell strings; prefer argv arrays;
- use private temp directories and exclusive file creation.

## G4: Sensitive Log and Diagnostics Disclosure

### Related findings

- F009 writes diagnostics bundles with weak permissions on device and host.
- F024 shows HUD log tail can expose command/system activity on screen.
- F025 creates world-readable fallback logs in `/tmp`.

### Relationship

These issues do not generally create command execution by themselves, but they leak the operational state that makes G1/G2 easier to exploit: helper paths, commands, service state, partitions, IPs, and log tails.

### Fix direction

- create log/diagnostic directories with `0700`;
- create sensitive files with `0600`;
- redact command args and network/helper paths where possible;
- make HUD log tail opt-in or privacy-filtered;
- avoid `/tmp` fallback for sensitive logs, or create a private directory first.

## G5: Legacy or Side-Track High Impact Tooling

### Related findings

- F006 enables root SSH with default credentials through automation scripts.
- F007 allows unsafe archive extraction and host file overwrite.

### Relationship

These are high impact but less coupled to native init module work.
They should be fixed as independent hardening work because they can compromise host or chroot environments outside the A90 native init runtime.

### Fix direction

- remove hardcoded root credentials and disable default password login;
- require user-provided password/key material;
- validate archive members before extraction;
- reject path traversal, absolute paths, symlinks, and special files in untrusted archives.

## G6: Historical Reproducibility and UX Regressions

### Related findings

- F026 older source builds break after metrics refactor.
- F027 v84 changelog detail screen is not rendered.
- F028 v42 run cancel logic competes for child stdin.
- F029 input event names allow path traversal in old probing helpers.

### Relationship

These are mostly historical or reliability issues.
They matter because this repository intentionally keeps old versioned sources for rollback/reproducibility.
If old versions remain build targets, shared header/API changes need compatibility wrappers or version-pinned headers.

### Fix direction

- define supported historical build window;
- add compatibility wrappers or pin copied headers for supported old versions;
- add validation command that builds the supported rollback set;
- apply low-risk input validation fixes to retained legacy utilities when practical.

## Cross-Group Attack Chains

### Chain A: Runtime helper to remote root service

```text
F004/F002 helper replacement
  -> F003 boot flag or F001 rshell/netservice path
  -> F005 tcpctl unauthenticated run
  -> persistent root command execution
```

### Chain B: SD trust to root write/log leak

```text
F011/F013 symlink-capable SD probe
  -> F012 SD log redirection
  -> F025/F009 readable logs or diagnostics
  -> command paths/service state exposed
```

### Chain C: Host validation makes device less safe

```text
F017/F018/F019 host auto-detection
  -> wrong NIC/serial target or stale bridge
  -> F014 cleanup silently fails
  -> F005 tcpctl remains exposed
```

### Chain D: Protocol reliability becomes security boundary

```text
F015 retry replays command
  + F016 spoofable END marker
  -> host believes command succeeded/failed incorrectly
  -> destructive or service commands can run more than once
```

## Priority Interpretation

The highest-risk cluster is not simply all `high` findings.
The immediate blocker for Wi-Fi or broader network work is any unauthenticated root-control path that can become reachable beyond the local USB lab model.

Recommended first security theme:

```text
P0 theme: close unauthenticated root-control surfaces
  F005 -> F001/F003/F010/F014/F021/F030
```

Recommended second theme:

```text
P1 theme: stop trusting writable runtime helpers/storage
  F002/F004/F011/F012/F013
```

Recommended third theme:

```text
P1 theme: harden host tooling before more automation
  F008/F015/F016/F017/F018/F019/F020/F022/F031
```

## Planning Notes

- Do not start Wi-Fi active networking before G1 has at least a minimal authentication/bind policy.
- Do not expand helper execution or runtime package loading before G2 has helper verification and safe path handling.
- Do not add more reconnect/soak automation before G3 has stable host trust boundaries.
- Logs and diagnostics are useful for development, but should be treated as sensitive once network paths exist.
