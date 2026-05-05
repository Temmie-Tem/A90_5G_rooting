# F004. tcpctl_host install race allows root helper replacement

## Metadata

| field | value |
|---|---|
| finding_id | `278067d006948191916329f6cf010e27` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/278067d006948191916329f6cf010e27 |
| severity | `high` |
| status | `mitigated-v124` |
| detected_at | `2026-04-28T08:06:37.402346Z` |
| committed_at | `2026-04-26 00:22:55 +0900` |
| commit_hash | `c525cbada5e0efe571f844c5caf73e3a1f459028` |
| relevant_paths | `scripts/revalidation/tcpctl_host.py` |
| has_patch | `true` |

## Local Remediation

- v124 changes tcpctl_host install to upload to a temporary path, verify SHA-256 before replacement, clean up failed temp files, and refuse default ramdisk /bin target replacement.
- Report: `docs/reports/NATIVE_INIT_V124_SECURITY_BATCH2_2026-05-06.md`

## CSV Description

`command_install()` starts a device-side `netcat -l -p <port> ... dd of=/cache/bin/a90_tcpctl` receiver, then intentionally sleeps before connecting from the host. Because the receiver is unauthenticated and not source-restricted, any actor that can reach the device TCP port can connect first and provide attacker-controlled bytes for the target binary path. The wrapper does compute SHA-256 and raises on mismatch, but it does not roll back/delete the written file. Separately, `start`/`smoke` execute `/cache/bin/a90_tcpctl` via serial `run` without any integrity check, so a poisoned binary can later be launched as root (especially realistic when replacing an already-existing executable file).

## Codex Cloud Detail

tcpctl_host install race allows root helper replacement
Link: https://chatgpt.com/codex/cloud/security/findings/278067d006948191916329f6cf010e27
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: c525cba
Author: shs02140@gmail.com
Created: 2026. 4. 28. 오후 5:06:37
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced security bug: insecure unauthenticated transfer/race in `tcpctl_host.py install` can overwrite the root-executed helper binary and leave it in place even on verification failure.
`command_install()` starts a device-side `netcat -l -p <port> ... dd of=/cache/bin/a90_tcpctl` receiver, then intentionally sleeps before connecting from the host. Because the receiver is unauthenticated and not source-restricted, any actor that can reach the device TCP port can connect first and provide attacker-controlled bytes for the target binary path. The wrapper does compute SHA-256 and raises on mismatch, but it does not roll back/delete the written file. Separately, `start`/`smoke` execute `/cache/bin/a90_tcpctl` via serial `run` without any integrity check, so a poisoned binary can later be launched as root (especially realistic when replacing an already-existing executable file).

# Validation
## Rubric
- [x] Confirm `install` opens unauthenticated listener and introduces a pre-connect delay window (`tcpctl_host.py:262-269`).
- [x] Demonstrate first-connector preemption can write attacker bytes to `device_binary` before legitimate transfer (PoC CASE_A).
- [x] Demonstrate verification-failure path does not remove/restore poisoned file (`tcpctl_host.py:303-304`; PoC CASE_B leaves tampered executable in place).
- [x] Confirm `start` executes `device_binary` directly without integrity revalidation (`tcpctl_host.py:184-188,191-196`; PoC CASE_C).
- [x] Validate practical chain consistency: poisoned file persists after failed install and is the same path later executed by start/smoke.
## Report
I validated the finding on commit c525cbada5e0efe571f844c5caf73e3a1f459028 by combining targeted source inspection with a minimal Python PoC harness that executes the real `command_install()`/`command_start()` logic under simulated bridge/device sockets.

Pre-check attempts required by workflow:
1) Crash attempt: `python3 scripts/revalidation/tcpctl_host.py ... install --local-binary /tmp/does_not_exist` -> traceback (FileNotFoundError) in `command_install` (artifact: `crash_attempt.log`).
2) Valgrind attempt: unavailable (`bash: valgrind: command not found`) (artifact: `valgrind_attempt.log`).
3) Debugger attempt: non-interactive LLDB run on `ping` path produced Python traceback through `tcpctl_request()` socket connect (artifact: `debugger_attempt.log`).

Vulnerability-relevant code evidence:
- Unauthenticated receiver + race window: `command_install()` launches device-side `netcat -l -p <port> ... dd of=<device_binary>` and then sleeps before host connect (`scripts/revalidation/tcpctl_host.py:262-269`), then host connects (`:271-278`).
- No rollback on verification failure: hash mismatch only raises (`:303-304`), no delete/restore.
- Later execution without integrity re-check: `tcpctl_listen_command()` builds `run {device_binary} listen ...` (`:184-188`) and `command_start()` executes it directly (`:191-196`).

PoC results (artifact `poc_output.log`, script `poc_tcpctl_host_validation.py`):
- CASE_A_RACE_FIRST_CONNECTOR: attacker connects first, writes `MALICIOUS-FIRST-CONNECTOR`; host install fails (`ConnectionRefusedError`), but target file content remains attacker-controlled and mode remains executable (`0o755`).
- CASE_B_HASH_MISMATCH_NO_CLEANUP: tampered transfer causes `RuntimeError('device sha256 did not match local ...')`; after failure, tampered file still present and executable (`0o755`).
- CASE_C_START_NO_REVALIDATION: captured start command is `run <device_binary> listen 2325 60 8` with no sha/integrity check.

This confirms the introduced bug: install path is vulnerable to unauthenticated transfer/race and does not clean up poisoned helper on failure; subsequent start path executes that helper without revalidation.

# Evidence
scripts/revalidation/tcpctl_host.py (L184 to 188)
  Note: `start` command is built to execute `run /cache/bin/a90_tcpctl listen ...` as root from serial bridge.
```
def tcpctl_listen_command(args: argparse.Namespace) -> str:
    return (
        f"run {args.device_binary} listen "
        f"{args.tcp_port} {args.idle_timeout} {args.max_clients}"
    )
```

scripts/revalidation/tcpctl_host.py (L191 to 196)
  Note: Execution path that launches the helper binary without integrity revalidation, enabling later execution of a poisoned file.
```
def command_start(args: argparse.Namespace) -> int:
    best_effort_hide_menu(args)
    command = tcpctl_listen_command(args)
    log(f"starting via bridge: {command}")
    runner = BridgeRunThread(args, command, echo=True)
    runner.start()
```

scripts/revalidation/tcpctl_host.py (L262 to 269)
  Note: Starts unauthenticated device-side netcat listener writing directly to `/cache/bin/a90_tcpctl`, then waits (`transfer_delay`), creating a race window for third-party connection.
```
    receive_command = (
        f"run {args.toybox} netcat -l -p {args.transfer_port} "
        f"{args.toybox} dd of={args.device_binary} bs=4096"
    )
    log(f"device receive command: {receive_command}")
    runner = BridgeRunThread(args, receive_command, echo=args.verbose)
    runner.start()
    time.sleep(args.transfer_delay)
```

scripts/revalidation/tcpctl_host.py (L271 to 278)
  Note: Host connects to the same transfer port after listener launch; first-connector wins behavior allows attacker preemption.
```
    with socket.create_connection((args.device_ip, args.transfer_port), timeout=args.connect_timeout) as sock:
        with local_binary.open("rb") as fp:
            while True:
                chunk = fp.read(1024 * 1024)
                if not chunk:
                    break
                sock.sendall(chunk)
        sock.shutdown(socket.SHUT_WR)
```

scripts/revalidation/tcpctl_host.py (L303 to 304)
  Note: On hash mismatch, code only raises an exception; it does not remove/restore the potentially attacker-written binary.
```
    if local_hash not in sha_output:
        raise RuntimeError(f"device sha256 did not match local {local_hash}")
```

Proposed patch:
diff --git a/scripts/revalidation/tcpctl_host.py b/scripts/revalidation/tcpctl_host.py
index a9858aa5091afcf544118dd1368754c5aec6cf24..dae856bf074b8e44affd4f1c6b8c05a8c63a90f5 100755
--- a/scripts/revalidation/tcpctl_host.py
+++ b/scripts/revalidation/tcpctl_host.py
@@ -256,93 +256,112 @@ def command_status(args: argparse.Namespace) -> int:
 def command_run(args: argparse.Namespace) -> int:
     if not args.run_args:
         raise SystemExit("run requires an absolute path and optional args")
     run_args = args.run_args
     if run_args and run_args[0] == "--":
         run_args = run_args[1:]
     if not run_args:
         raise SystemExit("run requires an absolute path and optional args")
     command = "run " + " ".join(shlex.quote(part) for part in run_args)
     print(tcpctl_request(args, command), end="")
     return 0


 def command_stop(args: argparse.Namespace) -> int:
     print(tcpctl_request(args, "shutdown"), end="")
     return 0


 def command_install(args: argparse.Namespace) -> int:
     local_binary = Path(args.local_binary)
     if not local_binary.exists():
         raise FileNotFoundError(local_binary)

     local_hash = sha256_file(local_binary)
     best_effort_hide_menu(args)
+    temp_device_binary = f"{args.device_binary}.tmp.{os.getpid()}.{int(time.time())}"
     receive_command = (
         f"run {args.toybox} netcat -l -p {args.transfer_port} "
-        f"{args.toybox} dd of={args.device_binary} bs=4096"
+        f"{args.toybox} dd of={temp_device_binary} bs=4096"
     )
     log(f"device receive command: {receive_command}")
     runner = BridgeRunThread(args, receive_command, echo=args.verbose)
     runner.start()
-    time.sleep(args.transfer_delay)
-
-    with socket.create_connection((args.device_ip, args.transfer_port), timeout=args.connect_timeout) as sock:
-        with local_binary.open("rb") as fp:
-            while True:
-                chunk = fp.read(1024 * 1024)
-                if not chunk:
-                    break
-                sock.sendall(chunk)
-        sock.shutdown(socket.SHUT_WR)
-
-    runner.join(args.transfer_timeout)
-    if runner.is_alive():
-        raise RuntimeError("device transfer did not finish")
-    if runner.error is not None:
-        raise RuntimeError(f"bridge transfer failed: {runner.error}")
-    if "[done] run" not in runner.text():
-        raise RuntimeError(f"device transfer did not report done:\n{runner.text()}")
+    try:
+        time.sleep(args.transfer_delay)

-    print(runner.text(), end="" if runner.text().endswith("\n") else "\n")
-    chmod_output = bridge_command(
-        args.bridge_host,
-        args.bridge_port,
-        f"run {args.toybox} chmod 755 {args.device_binary}",
-        args.bridge_timeout,
-    )
-    print(chmod_output, end="" if chmod_output.endswith("\n") else "\n")
-    sha_output = bridge_command(
-        args.bridge_host,
-        args.bridge_port,
-        f"run {args.toybox} sha256sum {args.device_binary}",
-        args.bridge_timeout,
-    )
-    print(sha_output, end="" if sha_output.endswith("\n") else "\n")
-    if local_hash not in sha_output:
-        raise RuntimeError(f"device sha256 did not match local {local_hash}")
+        with socket.create_connection((args.device_ip, args.transfer_port), timeout=args.connect_timeout) as sock:
+            with local_binary.open("rb") as fp:
+                while True:
+                    chunk = fp.read(1024 * 1024)
+                    if not chunk:
+                        break
+                    sock.sendall(chunk)
+            sock.shutdown(socket.SHUT_WR)
+
+        runner.join(args.transfer_timeout)
+        if runner.is_alive():
+            raise RuntimeError("device transfer did not finish")
+        if runner.error is not None:
+            raise RuntimeError(f"bridge transfer failed: {runner.error}")
+        if "[done] run" not in runner.text():
+            raise RuntimeError(f"device transfer did not report done:\n{runner.text()}")
+
+        print(runner.text(), end="" if runner.text().endswith("\n") else "\n")
+        sha_output = bridge_command(
+            args.bridge_host,
+            args.bridge_port,
+            f"run {args.toybox} sha256sum {temp_device_binary}",
+            args.bridge_timeout,
+        )
+        print(sha_output, end="" if sha_output.endswith("\n") else "\n")
+        if local_hash not in sha_output:
+            raise RuntimeError(f"device sha256 did not match local {local_hash}")
+
+        chmod_output = bridge_command(
+            args.bridge_host,
+            args.bridge_port,
+            f"run {args.toybox} chmod 755 {temp_device_binary}",
+            args.bridge_timeout,
+        )
+        print(chmod_output, end="" if chmod_output.endswith("\n") else "\n")
+        move_output = bridge_command(
+            args.bridge_host,
+            args.bridge_port,
+            f"run {args.toybox} mv -f {temp_device_binary} {args.device_binary}",
+            args.bridge_timeout,
+        )
+        print(move_output, end="" if move_output.endswith("\n") else "\n")
+    finally:
+        cleanup_output = bridge_command(
+            args.bridge_host,
+            args.bridge_port,
+            f"run {args.toybox} rm -f {temp_device_binary}",
+            args.bridge_timeout,
+        )
+        if args.verbose:
+            print(cleanup_output, end="" if cleanup_output.endswith("\n") else "\n")

     log(f"installed {args.device_binary} sha256={local_hash}")
     return 0


 def command_smoke(args: argparse.Namespace) -> int:
     if args.install_first:
         command_install(args)

     best_effort_hide_menu(args)
     runner = BridgeRunThread(args, tcpctl_listen_command(args), echo=args.verbose)
     runner.start()
     wait_for_tcpctl(args, args.ready_timeout)

     checks = [
         ("ping", "ping"),
         ("version", "version"),
         ("status", "status"),
         ("run-uname", f"run {args.toybox} uname -a"),
         ("run-ifconfig", f"run {args.toybox} ifconfig ncm0"),
     ]
     for label, command in checks:
         print(f"--- {label} ---")
         output = tcpctl_expect_ok(args, command)
         print(output, end="" if output.endswith("\n") else "\n")

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Kept at High. Impact is major (device-root code execution path through replaced executable) and chain is concretely evidenced in code plus executable PoC. Not raised to Critical because reachability is not broad/public Internet: attacker must be local-network adjacent to the device NCM transfer port and depend on victim operational actions (`install` then later `start/smoke`). Probability is meaningful in shared lab/compromised-host conditions but not universally immediate.
## Likelihood
medium - Exploit requires local-network adjacency to USB NCM path and victim invoking install/start, but those are standard documented workflows; race is practical due explicit delay and first-connector behavior.
## Impact
high - Successful exploitation replaces a helper that is later executed from privileged native-init control flow, enabling attacker-controlled code execution on the rooted device and persistent integrity compromise of operations tooling.
## Assumptions
- Operator uses tcpctl_host.py in normal workflow (install/start/smoke) as documented.
- Attacker can reach device NCM IP/port from a local adjacent host/process during install.
- Device executes serial `run` commands in native init (PID1/root context) without privilege drop.
- Victim runs `tcpctl_host.py install` (or `smoke --install-first`)
- Attacker reaches `device_ip:transfer_port` before legitimate sender
- Victim later runs `start`/`smoke` to execute `/cache/bin/a90_tcpctl`
## Path
attacker(local NCM) -> [18083 netcat listener] -> write /cache/bin/a90_tcpctl -> hash mismatch (no cleanup) -> operator start/smoke -> run /cache/bin/a90_tcpctl as root
## Path evidence
- `scripts/revalidation/tcpctl_host.py:262-271` - Install starts unauthenticated listener (`netcat -l -p`) writing to target binary, then sleeps before host connects.
- `scripts/revalidation/tcpctl_host.py:303-304` - Hash mismatch only throws exception; no delete/restore of potentially poisoned binary.
- `scripts/revalidation/tcpctl_host.py:184-196` - `start` builds and executes `run {device_binary} listen ...` without integrity re-check.
- `scripts/revalidation/tcpctl_host.py:412-423` - Default transfer settings (`transfer-port`, `transfer-delay=2.0`) make race window part of normal use.
- `stage3/linux_init/a90_tcpctl.c:517-521` - Service listener binds `INADDR_ANY`, not source-restricted.
- `docs/reports/NATIVE_INIT_V57_TCPCTL_HOST_WRAPPER_2026-04-26.md:42-46` - Documents normal operator flow: install via netcat+dd and start via serial run.
- `docs/reports/NATIVE_INIT_V56_TCPCTL_2026-04-26.md:188-189` - Project explicitly notes TCP control channel has no authentication.
- `/workspace/validation_artifacts/attack_path/user-uCP64b5dIkMxZJ7N2kDGpa8n_github-1095371052_c525cbada5e0efe571f844c5caf73e3a1f459028/extracted/tcpctl_host_race/poc_output.log:5-7` - Executable PoC output shows first-connector overwrite, mismatch-without-cleanup, and start path lacking revalidation.
## Narrative
The finding is valid and reachable: `command_install()` opens an unauthenticated device-side `netcat -l` receiver writing directly to `/cache/bin/a90_tcpctl`, then waits (`transfer_delay`) before host connect, enabling first-connector preemption. The post-transfer SHA check is non-atomic and only raises on mismatch, leaving attacker-written executable content in place. `start`/`smoke` later execute the same path through serial `run` without integrity revalidation, creating a practical chain to root helper execution on the device from a local-network-adjacent attacker.
## Controls
- Post-transfer SHA-256 comparison exists but is fail-open for persistence (no rollback).
- tcpctl run requires absolute path (input-shape control only, not auth).
- Serial bridge default bind is localhost (limits one ingress but not NCM transfer race).
- No authentication/authorization on tcpctl or transfer listener.
## Blindspots
- Static-only review cannot confirm exact production/lab network isolation around USB NCM on all operator setups.
- No dynamic verification here of every init version; root-execution assumption relies on documented PID1 model and current command flow.
- Potential external compensating controls (host firewall, strict lab isolation) are operational, not inferable from repository code alone.
