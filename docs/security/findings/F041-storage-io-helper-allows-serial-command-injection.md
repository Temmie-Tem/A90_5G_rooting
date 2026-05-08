# F041. Storage I/O helper allows serial command injection

## Metadata

| field | value |
|---|---|
| finding_id | `7d77ebb14688819185f9bda50a93e5e0` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/7d77ebb14688819185f9bda50a93e5e0 |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-08T18:20:33.341079Z` |
| committed_at | `2026-05-09 01:24:33 +0900` |
| commit_hash | `45215b98372b55a791aaa3cf52b59a04daef2dd3` |
| relevant_paths | `scripts/revalidation/storage_iotest.py` <br> `scripts/revalidation/tcpctl_host.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

The new storage_iotest.py validates device paths only with prefix and '../' substring checks, but it does not reject control characters, whitespace, '#', or other characters that are meaningful to the native-init line-oriented command parser. The transfer path uses BridgeRunThread, which writes the constructed command directly to the serial bridge as a raw line rather than as a cmdv1 argv-framed command. As a result, a malicious run id such as `ok\nwritefile /cache/native-init-netservice 1\n#` can be embedded into the `dd of=...` path. When the bridge sends the command, native init sees multiple input lines and executes the injected command as PID1/root after the netcat transfer command completes. The same pattern affects --test-root and --toybox, and the clean command also constructs `rm -rf` from these unsanitized values. This bypasses the script's stated guardrail that writes stay under `/mnt/sdext/a90/test-*` and can be used to run arbitrary native-init commands or destructive filesystem/partition operations if an attacker can influence these arguments in an operator workflow.

## Local Initial Assessment

- Valid and highest-priority finding in this batch: raw serial command construction can turn untrusted path text into additional PID1 shell commands.
- Related to F038: both are path confinement failures, but F041 is more severe because newline injection can become arbitrary native-init command execution.
- Treat as a blocker before any further NCM/storage automation.

## Local Remediation

- Planned Batch A fix, first item.
- Reject unsafe `--run-id`, `--test-root`, `--toybox`, device paths, and generated temp paths before raw bridge use.
- Prefer `cmdv1x`/argv-framed commands for non-streaming operations.
- Keep raw `BridgeRunThread` only where required for the netcat receiver and only after strict character validation.

## Codex Cloud Detail

Storage I/O helper allows serial command injection
Link: https://chatgpt.com/codex/cloud/security/findings/7d77ebb14688819185f9bda50a93e5e0?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 45215b9
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:20:33
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced a command-injection flaw in the new host-side storage I/O validation helper. The bug is not in the pre-existing bridge alone; the new script passes untrusted path/executable strings into raw serial commands without enforcing a safe character set or using argv-safe framing for the transfer command.
The new storage_iotest.py validates device paths only with prefix and '../' substring checks, but it does not reject control characters, whitespace, '#', or other characters that are meaningful to the native-init line-oriented command parser. The transfer path uses BridgeRunThread, which writes the constructed command directly to the serial bridge as a raw line rather than as a cmdv1 argv-framed command. As a result, a malicious run id such as `ok\nwritefile /cache/native-init-netservice 1\n#` can be embedded into the `dd of=...` path. When the bridge sends the command, native init sees multiple input lines and executes the injected command as PID1/root after the netcat transfer command completes. The same pattern affects --test-root and --toybox, and the clean command also constructs `rm -rf` from these unsanitized values. This bypasses the script's stated guardrail that writes stay under `/mnt/sdext/a90/test-*` and can be used to run arbitrary native-init commands or destructive filesystem/partition operations if an attacker can influence these arguments in an operator workflow.

# Validation
## Rubric
- [x] Confirm dangerous CLI-controlled values are embedded in device paths/commands without a strict safe-character validator.
- [x] Confirm validators accept a newline/# payload while still satisfying the `/mnt/sdext/a90/test-*` prefix checks.
- [x] Exercise the actual storage_iotest transfer path rather than only string-building code.
- [x] Capture raw bridge bytes proving the injected payload becomes a separate serial command line.
- [x] Confirm the native-init shell is line-oriented and treats `#` as comment syntax, making the injected line executable independently.
## Report
Validated the finding against commit 45215b98372b55a791aaa3cf52b59a04daef2dd3. The bug is a Python/host-side command injection, not a memory-safety crash, so a crashing PoC/valgrind reproduction is not applicable; a direct PoC returned rc=0 and valgrind was not installed in the container. I then ran the PoC under pdb and captured the vulnerable command construction. Evidence: scripts/revalidation/storage_iotest.py:131-142 only checks prefix and ../ and does not reject newlines or #. storage_iotest.py:163-175 constructs receive_command from args.toybox, transfer_port, and tmp_path, then passes it to BridgeRunThread. storage_iotest.py:206-230 embeds args.run_id into device_path and later mv/rm commands. storage_iotest.py:302-306 similarly constructs clean rm -rf. scripts/revalidation/tcpctl_host.py:230-238 sends '\n' + self.command + '\n' directly over the raw bridge. Native-side relevance is confirmed by stage3/linux_init/a90_console.c:416-419, where newline terminates a command line; stage3/linux_init/v159/50_boot_services.inc.c:68-81, where # starts a comment; stage3/linux_init/v159/80_shell_dispatch.inc.c:1248-1288, where parsed lines are executed as shell commands; and writefile is a registered command at stage3/linux_init/v159/80_shell_dispatch.inc.c:963 with implementation at stage3/linux_init/v159/70_storage_android_net.inc.c:126-163. The PoC imports the real storage_iotest.transfer_file(), uses a malicious run-id equivalent to `ok\nwritefile /cache/native-init-netservice 1\n#`, and records bytes received by a mock bridge. Output showed `validators_accepted: true` and raw bridge lines: ['', 'run /cache/bin/toybox netcat -l -p ... /cache/bin/toybox dd of=/mnt/sdext/a90/test-io/ok', 'writefile /cache/native-init-netservice 1', '#/file-01-1.bin.tmp... bs=4096']. This proves the helper emits the attacker-controlled `writefile` as a separate native-init command line.

# Evidence
scripts/revalidation/storage_iotest.py (L131 to 142)
  Note: The device-root/path validators only enforce a string prefix and reject '../'; they do not reject newlines, carriage returns, whitespace, '#', or other characters that can alter the line-oriented native-init command stream.
```
def validate_device_test_root(path: str) -> None:
    if not path.startswith("/mnt/sdext/a90/test-"):
        raise RuntimeError(f"refusing test root outside /mnt/sdext/a90/test-*: {path}")
    if "//" in path or "/../" in path or path.endswith("/.."):
        raise RuntimeError(f"unsafe test root: {path}")


def validate_device_path(path: str, root: str) -> None:
    if not path.startswith(root.rstrip("/") + "/"):
        raise RuntimeError(f"refusing path outside test root: {path}")
    if "/../" in path or path.endswith("/.."):
        raise RuntimeError(f"unsafe device path: {path}")
```

scripts/revalidation/storage_iotest.py (L163 to 175)
  Note: The transfer command is assembled with unsanitized args.toybox, args.transfer_port, and tmp_path derived from args.test_root/run_id, then executed via BridgeRunThread as raw serial input.
```
def transfer_file(args: argparse.Namespace, local_path: Path, device_path: str) -> str:
    tmp_path = f"{device_path}.tmp.{os.getpid()}.{int(time.time())}"
    validate_device_path(device_path, args.test_root)
    validate_device_path(tmp_path, args.test_root)
    receive_command = (
        f"run {args.toybox} netcat -l -p {args.transfer_port} "
        f"{args.toybox} dd of={tmp_path} bs=4096"
    )
    cleanup_command = f"run {args.toybox} rm -f {tmp_path}"

    run_device(args, cleanup_command, timeout=args.bridge_timeout, allow_error=True)
    runner = BridgeRunThread(args, receive_command, echo=args.verbose)
    runner.start()
```

scripts/revalidation/storage_iotest.py (L206 to 230)
  Note: args.run_id is embedded into device_path and subsequent root mv/rm/stat commands without a safe component validation step.
```
def run_one_file(args: argparse.Namespace,
                 local_dir: Path,
                 index: int,
                 size: int) -> FileResult:
    name = f"file-{index:02d}-{size}.bin"
    local_path = local_dir / name
    device_path = posixpath.join(args.test_root, args.run_id, name)
    renamed_path = device_path + ".renamed"
    data = deterministic_bytes(size, f"{args.run_id}:{index}:{size}")
    digest = sha256_bytes(data)
    write_private_bytes(local_path, data)

    transfer_file(args, local_path, device_path)
    first_hash = device_sha256(args, device_path)
    sha_ok = first_hash == digest
    run_device(args, f"run {args.toybox} mv -f {device_path} {renamed_path}", timeout=args.bridge_timeout)
    run_device(args, f"run {args.toybox} mv -f {renamed_path} {device_path}", timeout=args.bridge_timeout)
    second_hash = device_sha256(args, device_path)
    rename_ok = second_hash == digest
    run_device(args, "sync", timeout=args.bridge_timeout)
    fsync_ok = device_sha256(args, device_path) == digest

    unlink_probe = device_path + ".unlink-probe"
    transfer_file(args, local_path, unlink_probe)
    run_device(args, f"run {args.toybox} rm -f {unlink_probe}", timeout=args.bridge_timeout)
```

scripts/revalidation/storage_iotest.py (L302 to 306)
  Note: The clean path constructs a root `rm -rf` command from args.test_root and args.run_id after the same insufficient validation.
```
def command_clean(args: argparse.Namespace) -> int:
    validate_device_test_root(args.test_root)
    target = posixpath.join(args.test_root, args.run_id) if args.run_id else args.test_root
    validate_device_path(posixpath.join(target.rstrip("/"), "probe"), args.test_root)
    text = run_device(args, f"run {args.toybox} rm -rf {target}", timeout=args.bridge_timeout, allow_error=True)
```

scripts/revalidation/storage_iotest.py (L312 to 318)
  Note: The dangerous values are exposed as CLI arguments, but no type/regex validator is attached to enforce path-component safety.
```
def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bridge-host", default=DEFAULT_BRIDGE_HOST)
    parser.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
    parser.add_argument("--device-ip", default=DEFAULT_DEVICE_IP)
    parser.add_argument("--toybox", default=DEFAULT_TOYBOX)
    parser.add_argument("--test-root", default=DEFAULT_TEST_ROOT)
    parser.add_argument("--run-id", default=f"v161-{int(time.time())}")
```

scripts/revalidation/tcpctl_host.py (L230 to 238)
  Note: BridgeRunThread sends the command string directly to the serial bridge surrounded by newlines, so embedded newlines in the storage helper's command become additional device commands.
```
    def run(self) -> None:
        try:
            with socket.create_connection(
                (self.args.bridge_host, self.args.bridge_port),
                timeout=self.args.connect_timeout,
            ) as sock:
                sock.settimeout(0.25)
                sock.sendall(("\n" + self.command + "\n").encode())
                while True:
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Downgraded from high to medium on probability rather than impact. The impact on a connected device is high because injected lines are dispatched by native-init as root/PID1 and can invoke filesystem/process commands. Static evidence and the validation PoC confirm the bug. But the reachable attack surface is an internal revalidation script with operator-controlled CLI arguments and a default localhost bridge, not a public or broadly network-reachable service. A realistic exploit requires attacker influence over --run-id/--test-root/--toybox in an operator workflow while the device and bridge are active. This is a real in-scope security issue, but it does not meet the usual bar for high severity absent a clearer untrusted-input source or broader exposure.
## Likelihood
medium - The code path is real and documented, and the PoC demonstrates command splitting. However, attacker reachability is indirect: the default bridge is localhost, the script is an internal operator tool, and the attacker must influence CLI/workflow values rather than sending unauthenticated network traffic directly.
## Impact
high - Successful exploitation executes injected native-init commands as PID1/root on the connected device. This can alter persistent /cache flags, run trusted helper binaries, mutate filesystems, or perform destructive device operations. The blast radius is primarily the single attached lab device and its persistent state, not a fleet or internet service.
## Assumptions
- The attacker cannot directly access the native-init serial shell or localhost bridge; otherwise arbitrary root device commands are already possible by design.
- The relevant attacker path is influencing storage_iotest.py CLI values such as --run-id, --test-root, or --toybox in an operator workflow.
- The operator has a connected A90 device running the native-init command parser and a serial TCP bridge available on the configured bridge host and port.
- Attacker influences storage_iotest.py arguments or an environment/workflow variable used to populate them
- Operator runs the storage I/O validation or clean workflow
- Host can reach the serial TCP bridge, default 127.0.0.1:54321
- Device is booted into the native-init environment with the line-oriented command parser active
## Path
attacker arg -> storage_iotest validators -> raw command string -> localhost serial bridge -> native-init newline parser -> root/PID1 command
## Path evidence
- `scripts/revalidation/storage_iotest.py:131-142` - Path validators only check the /mnt/sdext/a90/test-* prefix and ../ patterns; they do not reject newlines, carriage returns, whitespace, #, or other native-init parser metacharacters.
- `scripts/revalidation/storage_iotest.py:163-175` - transfer_file constructs receive_command and cleanup_command by interpolating args.toybox, args.transfer_port, and tmp_path, then passes receive_command to BridgeRunThread.
- `scripts/revalidation/storage_iotest.py:206-230` - run_one_file embeds args.run_id into device_path and later uses that path in transfer, mv, rm, stat, and hash commands.
- `scripts/revalidation/storage_iotest.py:302-306` - The clean command builds a root rm -rf command from args.test_root and args.run_id after the same insufficient validation.
- `scripts/revalidation/storage_iotest.py:312-318` - The dangerous values are exposed as CLI arguments without a strict type or regex validator.
- `scripts/revalidation/tcpctl_host.py:230-238` - BridgeRunThread sends '\n' + command + '\n' directly to the bridge, so embedded newlines become separate serial command lines.
- `stage3/linux_init/a90_console.c:416-419` - The console input layer terminates a command line on CR or LF.
- `stage3/linux_init/v159/80_shell_dispatch.inc.c:1248-1288` - Parsed serial lines are dispatched as native-init commands, including raw non-cmdv1 commands.
- `stage3/linux_init/v159/80_shell_dispatch.inc.c:958-965` - The native-init command table registers filesystem and process primitives including writefile and run.
- `stage3/linux_init/v159/70_storage_android_net.inc.c:126-163` - writefile opens and writes to the supplied path in the native-init/root context.
- `docs/plans/NATIVE_INIT_V161_STORAGE_IO_INTEGRITY_PLAN_2026-05-09.md:30-41` - Project documentation shows storage_iotest.py as a normal v161 revalidation workflow using --run-id and clean.
## Narrative
The finding is valid: storage_iotest.py only enforces a prefix and simple traversal checks, then interpolates CLI-controlled values into native-init command lines. BridgeRunThread sends the resulting string as raw serial input with surrounding newlines. The native-init console treats CR/LF as command terminators and dispatches each parsed line; the command table includes dangerous root commands such as writefile and run. The validation PoC demonstrated that a malicious run ID containing a newline is accepted and causes an injected writefile command to appear as a separate raw bridge line. The main limiting factor is reachability: this is not public or unauthenticated remote exposure; an attacker must influence operator-supplied arguments in a lab workflow while a device/bridge is active. That makes the impact high on the connected device, but the likelihood lower than a network-exposed RCE.
## Controls
- serial_tcp_bridge defaults to localhost port 54321 rather than public exposure
- storage_iotest.py attempts a test-root guardrail, but it is prefix/traversal-only and does not sanitize line delimiters
- native-init supports cmdv1/cmdv1x framing, but this transfer path sends a raw line through BridgeRunThread
- Netservice/storage workflow is an operator-run lab tool, not an internet-facing service
- No authentication or authorization is enforced by the native-init command parser once serial input reaches it
## Blindspots
- Static-only review cannot confirm all deployed native-init versions or whether v159 include files are exactly the runtime used in every v161 test image.
- No cloud, CI, or operator workflow configuration was available to determine whether --run-id is ever populated from untrusted job parameters.
- The repository does not prove how often operators expose the bridge beyond localhost or run this helper in shared-host environments.
- The validation PoC used a mock bridge to prove emitted bytes; it did not execute commands on a real device in this container.
