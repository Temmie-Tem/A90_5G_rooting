# F053. NCM preflight may run untrusted cache tcpctl as root

## Metadata

| field | value |
|---|---|
| finding_id | `893ea1f373148191b20516e1d75a843d` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/893ea1f373148191b20516e1d75a843d |
| severity | `medium` |
| status | `duplicate-of-F046-currently-mitigated` |
| detected_at | `2026-05-10T00:42:33.867773Z` |
| committed_at | `2026-05-09 05:28:21 +0900` |
| commit_hash | `c2ee250a976b1626444510afd9bd7d5a3da7ac94` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py` <br> `scripts/revalidation/tcpctl_host.py` <br> `stage3/linux_init/init_v73.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The new NCM preflight logic now accepts /cache/bin/a90_tcpctl whenever the device-side stat command succeeds. That check only proves that a path exists; it does not require the file to be executable, owned by a trusted user, non-symlink, or equal to the expected authenticated tcpctl build. The selected path is passed as --device-binary to tcpctl_host.py, which constructs a native-init command of the form run <device_binary> listen .... native init then execve()s that path as root. Because /cache/bin is persistent helper storage and is less trustworthy than the ramdisk /bin helper, a stale, unauthenticated, or attacker-planted /cache/bin/a90_tcpctl can be launched as root when an operator runs the NCM preflight on a device where /bin/a90_tcpctl is missing or unavailable. The later transcript auth checks can fail the validation, but they occur after the helper has already been executed and after any malicious payload or temporary unauthenticated listener could have run.

## Local Initial Assessment

- Full detail matches the previously tracked `F046` pattern. Current `ncm_tcp_preflight.py` only accepts trusted ramdisk `/bin/a90_tcpctl` and explicitly refuses `/cache/bin` fallback. Treat as duplicate/reopened unless a fresh scan targets current code.

## Local Remediation

- No new patch required from this finding unless Codex Cloud still reproduces against current code. Keep linked to `F046` closure evidence.

## Codex Cloud Detail

NCM preflight may run untrusted cache tcpctl as root
Link: https://chatgpt.com/codex/cloud/security/findings/893ea1f373148191b20516e1d75a843d?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: c2ee250
Author: shs02140@gmail.com
Created: 2026. 5. 10. 오전 9:42:33
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced: the patch expands the preflight trust boundary from the fixed /bin/a90_tcpctl helper to a /cache/bin/a90_tcpctl fallback without integrity or trust validation before root execution.
The new NCM preflight logic now accepts /cache/bin/a90_tcpctl whenever the device-side stat command succeeds. That check only proves that a path exists; it does not require the file to be executable, owned by a trusted user, non-symlink, or equal to the expected authenticated tcpctl build. The selected path is passed as --device-binary to tcpctl_host.py, which constructs a native-init command of the form run <device_binary> listen .... native init then execve()s that path as root. Because /cache/bin is persistent helper storage and is less trustworthy than the ramdisk /bin helper, a stale, unauthenticated, or attacker-planted /cache/bin/a90_tcpctl can be launched as root when an operator runs the NCM preflight on a device where /bin/a90_tcpctl is missing or unavailable. The later transcript auth checks can fail the validation, but they occur after the helper has already been executed and after any malicious payload or temporary unauthenticated listener could have run.

# Validation
## Rubric
- [x] Identify the exact introduced fallback and verify whether selection depends only on `stat` success.
- [x] Demonstrate that an untrusted-looking `/cache/bin/a90_tcpctl` is selected when `/bin/a90_tcpctl` is unavailable.
- [x] Demonstrate that the selected path is passed as `--device-binary` to tcpctl_host.py.
- [x] Demonstrate that tcpctl_host.py converts the selected path into a native-init `run /cache/bin/a90_tcpctl listen ...` command.
- [x] Verify the privilege-boundary sink: native init `cmd_run` execve()s argv[1], so the unverified path becomes the executable launched by native init.
## Report
Validated the finding at commit c2ee250a976b1626444510afd9bd7d5a3da7ac94. The changed preflight code in scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:39-51 probes only `stat` for `/bin/a90_tcpctl` then `/cache/bin/a90_tcpctl`; any successful stat sets `self._device_binary`. There is no executable-bit, owner, symlink, hash, or version validation. The selected value is then passed to tcpctl_host.py as `--device-binary` at ncm_tcp_preflight.py:58-68. tcpctl_host.py:326-330 formats it directly into `run {args.device_binary} listen ...`. The device-side native init `run` implementation in stage3/linux_init/init_v73.c:8256-8283 forks and execve()s argv[1] with the root/native-init environment.

Dynamic evidence: I created a targeted PoC that imports the real Python modules and stubs only unavailable device/ping interfaces. It simulates `/bin/a90_tcpctl` missing and `stat /cache/bin/a90_tcpctl` succeeding with stat text showing mode 0644 and uid shell. Output showed: `prepare_detail: host NCM ping ok; tcpctl=/cache/bin/a90_tcpctl`, `selected_device_binary: /cache/bin/a90_tcpctl`, `wrapper_device_binary_arg: /cache/bin/a90_tcpctl`, and `tcpctl_listen_command: run /cache/bin/a90_tcpctl listen 192.168.7.2 2325 60 8 /cache/native-init-tcpctl.token`.

I also ran the real scripts/revalidation/tcpctl_host.py against a local fake raw native-init bridge. The fake bridge captured the actual command sent by the host tool: `run /cache/bin/a90_tcpctl listen 192.168.7.2 2325 60 8 -`; tcpctl_host exited rc=0. This confirms the selected cache path crosses into the native-init `run` command.

Debugger evidence: a non-interactive pdb run stopped at ncm_tcp_preflight.py:49 and, after the first candidate failed, showed `candidate == '/cache/bin/a90_tcpctl'`, `record.ok == True`, and untrusted-looking stat text `Access: (0644/-rw-r--r--) Uid: (2000/ shell)`, proving the code accepts mere existence.

Crash/Valgrind: this is a trust-boundary/command-selection vulnerability rather than memory corruption, so a crash is not expected. I attempted the requested valgrind path, but valgrind is not installed in the container (`bash: valgrind: command not found`).

# Evidence
scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py (L39 to 51)
  Note: New fallback selects /cache/bin/a90_tcpctl when stat succeeds, without checking executable bit, ownership, symlink status, version, or hash.
```
        for candidate in ("/bin/a90_tcpctl", "/cache/bin/a90_tcpctl"):
            record, output = ctx.client.run(
                f"stat-{candidate}",
                ["stat", candidate],
                timeout=ctx.timeout,
            )
            ctx.store.write_text(
                f"modules/{self.name}/stat-{candidate.strip('/').replace('/', '-')}.txt",
                output,
            )
            if record.ok:
                self._device_binary = candidate
                return StepResult("prepare", True, f"host NCM ping ok; tcpctl={candidate}", 0.0)
```

scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py (L58 to 68)
  Note: The selected helper path is passed to tcpctl_host.py as --device-binary, so the unverified /cache/bin fallback becomes the executable used by the smoke test.
```
        command = [
            sys.executable,
            str(ctx.repo_root / "scripts/revalidation/tcpctl_host.py"),
            "--bridge-host",
            ctx.host,
            "--bridge-port",
            str(ctx.port),
            "--device-binary",
            self._device_binary,
            "--toybox",
            "/cache/bin/toybox",
```

scripts/revalidation/tcpctl_host.py (L326 to 330)
  Note: tcpctl_host.py turns --device-binary into a native-init run command, causing the chosen path to be launched on the device.
```
def tcpctl_listen_command(args: argparse.Namespace) -> str:
    return (
        f"run {args.device_binary} listen "
        f"{args.device_ip} {args.tcp_port} {args.idle_timeout} "
        f"{args.max_clients} {args.token_path if not args.no_auth else '-'}"
```

stage3/linux_init/init_v73.c (L8256 to 8283)
  Note: The native-init run command forks and execve()s the supplied path as root, which is the privilege boundary crossed by the unverified /cache/bin fallback.
```
static int cmd_run(char **argv, int argc) {
    static char *const envp[] = {
        "PATH=/cache:/cache/bin:/bin:/system/bin",
        "HOME=/",
        "TERM=vt100",
        "LD_LIBRARY_PATH=/cache/adb/lib",
        NULL
    };
    pid_t pid;
    int status;

    if (argc < 2) {
        cprintf("usage: run <path> [args...]\r\n");
        return -EINVAL;
    }

    pid = fork();
    if (pid < 0) {
        cprintf("run: fork: %s\r\n", strerror(errno));
        return negative_errno_or(EAGAIN);
    }

    if (pid == 0) {
        dup2(console_fd, STDIN_FILENO);
        dup2(console_fd, STDOUT_FILENO);
        dup2(console_fd, STDERR_FILENO);
        execve(argv[1], &argv[1], envp);
        cprintf("run: execve(%s): %s\r\n", argv[1], strerror(errno));
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Keep medium. The code evidence supports the vulnerability: a stat-only fallback selects /cache/bin/a90_tcpctl, the selected path is passed to tcpctl_host.py, and native init execve()s it as root. The affected components are in scope because the threat model explicitly includes host revalidation tooling, tcpctl_host.py, native init root execution, and persistent /cache/bin helper trust. However, this is a local/USB lab workflow with constrained reachability, not a public remote attack. Exploitation requires an attacker to have already planted or influenced a persistent helper and then wait for or induce operator preflight execution when /bin/a90_tcpctl is unavailable. The impact on one attached device is severe, but probability is limited by those preconditions, making medium more appropriate than high or critical.
## Likelihood
low - The path is not publicly exposed by default and requires several preconditions: prior influence over /cache/bin/a90_tcpctl, /bin/a90_tcpctl missing or unavailable, USB/NCM reachability, and an operator running the preflight. These are plausible in the repository's lab threat model but not easy for an unauthenticated remote attacker.
## Impact
high - If triggered with a malicious cache helper, native init executes attacker-controlled code as root on the attached device. That can compromise device integrity, availability, and confidentiality in the lab device context.
## Assumptions
- The affected revalidation harness is part of the intended lab workflow, not dead code.
- A realistic attacker must be able to plant, replace, or leave a stale malicious helper at /cache/bin/a90_tcpctl before a trusted operator runs the NCM TCP preflight.
- The native-init command interpreter runs with root/PID1 privileges as described by the repository's device-control model.
- No cloud, Kubernetes, or external deployment manifests are present or needed for this attack path.
- Host-side NCM preflight is run by an operator
- USB NCM path to 192.168.7.2 is reachable
- /bin/a90_tcpctl is missing or unavailable
- /cache/bin/a90_tcpctl exists
- Attacker previously controlled or influenced the contents of /cache/bin/a90_tcpctl
## Path
Attacker controls /cache/bin/a90_tcpctl
  -> operator runs NCM preflight
  -> stat-only fallback selects /cache/bin/a90_tcpctl
  -> tcpctl_host sends 'run /cache/bin/a90_tcpctl listen ...'
  -> native init execve()s helper as root
  -> root code execution on device
## Path evidence
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:12-14` - Defines the NCM TCP preflight harness module that is part of the revalidation workflow.
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:39-51` - Selects /cache/bin/a90_tcpctl when stat succeeds, with no executable-bit, owner, symlink, hash, or version validation.
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:58-68` - Passes the selected helper path to tcpctl_host.py as --device-binary.
- `scripts/revalidation/tcpctl_host.py:326-330` - Converts --device-binary directly into a native-init run command.
- `stage3/linux_init/init_v73.c:8256-8283` - Native init run command forks and execve()s argv[1] using the root/native-init environment.
- `scripts/revalidation/native_test_supervisor.py:25-39` - Imports and registers NcmTcpPreflightModule, supporting that the affected module is operational workflow code.
- `scripts/revalidation/a90harness/scheduler.py:93-99` - Default workload preference includes ncm-tcp-preflight for non-idle profiles.
- `scripts/revalidation/serial_tcp_bridge.py:16-18` - Serial bridge defaults to localhost port 54321, limiting default network exposure.
- `scripts/revalidation/tcpctl_host.py:18-24` - tcpctl host defaults show localhost bridge, device IP 192.168.7.2, and TCP port 2325 for the USB/NCM path.
## Narrative
The finding is real and in scope. ncm_tcp_preflight.py checks /bin/a90_tcpctl and then /cache/bin/a90_tcpctl with only stat; any successful stat sets self._device_binary. The run step passes that value to tcpctl_host.py as --device-binary. tcpctl_host.py interpolates it into a native-init command of the form run <device_binary> listen ..., and init_v73.c cmd_run forks and execve()s argv[1] with the root native-init environment. This creates a root execution path for an untrusted persistent cache helper. Severity remains medium because exploitation requires meaningful preconditions: prior ability to plant or influence /cache/bin/a90_tcpctl, /bin helper unavailability, and operator interaction in a local USB/NCM lab workflow. The impact is high on the single attached device once triggered, but likelihood is constrained and not remotely/publicly exposed by default.
## Controls
- USB/local lab workflow rather than public Internet exposure
- serial_tcp_bridge.py defaults to 127.0.0.1:54321
- NCM preflight first requires successful ping to 192.168.7.2
- tcpctl_host.py normally uses token authentication for tcpctl requests after the listener starts
- tcpctl listener has idle-timeout and max-client parameters
- No pre-execution integrity control exists for the selected /cache/bin/a90_tcpctl fallback
## Blindspots
- Static review cannot verify actual device filesystem permissions for /cache/bin or who can write it in each operating mode.
- Static review cannot confirm how often /bin/a90_tcpctl is absent in real operator workflows.
- No runtime device was available in this attack-path stage to observe real native-init UID/GID or mount options.
- Repository contains lab tooling rather than deployment manifests, so exposure assessment is based on source defaults and documented workflow.

