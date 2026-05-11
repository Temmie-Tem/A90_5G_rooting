# F050. Outer soak timeout can orphan live broker processes

## Metadata

| field | value |
|---|---|
| finding_id | `e354d34c6c70819199f24eb1fcc36cdd` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/e354d34c6c70819199f24eb1fcc36cdd |
| severity | `medium` |
| status | `confirmed-pending-patch` |
| detected_at | `2026-05-11T19:23:35.362120Z` |
| committed_at | `2026-05-11 22:04:38 +0900` |
| commit_hash | `8edda96203df2af80ce2963cd3c6109c5ab71395` |
| author | `shs02140@gmail.com` |
| repo | `Temmie-Tem/A90_5G_rooting` |
| relevant_paths | `scripts/revalidation/a90_broker_soak_suite.py` <br> `scripts/revalidation/a90_broker_mixed_soak_gate.py` <br> `scripts/revalidation/a90_broker.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-11T19-48-19.047Z.csv` |

## CSV Description

The newly added a90_broker_soak_suite.py executes each validator with subprocess.run(..., timeout=timeout_sec). On timeout, Python kills only the immediate child process and raises TimeoutExpired. The suite does not catch that exception, so it aborts without writing a failure summary. More importantly, the called broker validators start their broker with start_new_session=True and rely on their own finally blocks to stop it. If the outer suite kills the validator process, that finally block is bypassed and the broker subprocess may remain alive. In live mode, the mixed-soak broker is an ACM command broker to the native-init root control path, so an orphaned same-user UNIX socket can unexpectedly remain as a root device command channel after the suite has exited.

## Local Initial Assessment

- Confirmed against current code: `a90_broker_soak_suite.py` wraps validators with `subprocess.run(..., timeout=...)`, while child validators start brokers in new sessions and rely on their own `finally` blocks. Timeout can bypass child cleanup.

## Local Remediation

- Replace outer `subprocess.run(timeout=...)` with process-group-aware launch/kill/communicate helper and always write timeout failure evidence.

## Codex Cloud Detail

Outer soak timeout can orphan live broker processes
Link: https://chatgpt.com/codex/cloud/security/findings/e354d34c6c70819199f24eb1fcc36cdd?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 8edda96
Author: shs02140@gmail.com
Created: 2026. 5. 12. 오전 4:23:35
Assignee: Unassigned
Signals: Security, Validated

# Summary
Introduced bug: the new orchestration layer adds an outer timeout around broker validators without process-tree cleanup or TimeoutExpired handling. Existing validators clean up their own broker child when they exit normally, but the new wrapper can prevent that cleanup by killing the validator process from outside.
The newly added a90_broker_soak_suite.py executes each validator with subprocess.run(..., timeout=timeout_sec). On timeout, Python kills only the immediate child process and raises TimeoutExpired. The suite does not catch that exception, so it aborts without writing a failure summary. More importantly, the called broker validators start their broker with start_new_session=True and rely on their own finally blocks to stop it. If the outer suite kills the validator process, that finally block is bypassed and the broker subprocess may remain alive. In live mode, the mixed-soak broker is an ACM command broker to the native-init root control path, so an orphaned same-user UNIX socket can unexpectedly remain as a root device command channel after the suite has exited.

# Validation
## Rubric
- [x] Confirm the orchestration layer uses subprocess.run(..., timeout=...) without TimeoutExpired handling or process-tree cleanup.
- [x] Confirm the new suite wraps the broker-backed mixed-soak validator, and the live path is non-dry-run/acm-cmdv1.
- [x] Confirm the mixed-soak validator starts its broker with start_new_session=True and relies on its own finally block for cleanup.
- [x] Dynamically force an outer timeout and verify the validator cleanup is bypassed while the broker process is reparented and remains alive.
- [x] Verify the orphaned broker UNIX socket can still accept a command after the suite timeout.
## Report
Validated the finding at commit 8edda96203df2af80ce2963cd3c6109c5ab71395. Code evidence: scripts/revalidation/a90_broker_soak_suite.py:65-72 calls subprocess.run(..., timeout=timeout_sec) and lines 169-170 call run_step without catching subprocess.TimeoutExpired. The suite wraps broker-mixed-soak at scripts/revalidation/a90_broker_soak_suite.py:110-129. The mixed-soak validator starts the broker with start_new_session=True at scripts/revalidation/a90_broker_mixed_soak_gate.py:94-120 and only stops it from its own finally block at lines 336-390. The live mixed-soak CLI defaults to/accepts acm-cmdv1 at scripts/revalidation/a90_broker_mixed_soak_gate.py:49. Broker sockets remain capable of accepting and dispatching requests: scripts/revalidation/a90_broker.py:704-713 binds/listens, and lines 615-628 dispatch non-rebind commands to the backend.

Dynamic validation: I created a bounded PoC that calls the real suite run_step() with timeout_sec=1.0 against a validator stand-in that uses the real a90_broker_mixed_soak_gate.start_broker()/stop_broker() helpers. The stand-in starts a real a90_broker.py server in a new session, writes its PID, then sleeps inside a try/finally cleanup block. run_step() timed out and raised TimeoutExpired; because subprocess.run kills only the immediate child, the broker remained alive. Evidence from reproduce_orphan.py/last-result.json: timeout_exception=true; broker_alive_after_timeout=true; socket_exists_after_timeout=true; cleanup_marker_exists=false; suite_step_output_exists=false; suite_summary_exists=false. ps output captured the orphan as PPID 1 and SID equal to its PID: `/workspace/A90_5G_rooting/scripts/revalidation/a90_broker.py serve --backend fake ...`.

The orphaned socket was functional after the suite timeout: the PoC invoked `a90_broker.py call --socket <orphan socket> ... status`, receiving rc=0 and JSON `{ "backend": "fake", "ok": true, "status": "ok", "text": "fake status\n" }`. The fake backend was used only to keep validation self-contained; the vulnerable process-tree behavior is the same real start_broker helper, while the actual live mixed-soak parser uses acm-cmdv1.

Crash/abort attempt: crash_driver_unhandled_timeout.py let the TimeoutExpired propagate, producing a traceback at a90_broker_soak_suite.py:65 and showing a broker process orphaned under PPID 1 before cleanup. Valgrind attempt: valgrind was not installed and is not applicable to this Python subprocess lifetime bug. Debugger validation: debugger_trace_driver.py used non-interactive pdb at a90_broker_soak_suite.py:65; it captured the call stack into subprocess.run(timeout=...), then PDB_RESULT showed timed_out=true, broker_alive=true, socket_exists=true, cleanup_marker_exists=false.

# Evidence
scripts/revalidation/a90_broker_mixed_soak_gate.py (L336 to 390)
  Note: The validator relies on its own finally block to stop the broker. If the new suite kills this process due to its outer timeout, this cleanup path is bypassed.
```
    try:
        if not args.dry_run:
            broker_process = start_broker(args, runtime_dir)
            wait_for_broker(socket_path, broker_process, args.ready_timeout)

        supervisor_result = run_supervisor(args, runtime_dir, supervisor_dir)
        supervisor_rc = supervisor_result.returncode
        store.write_text("supervisor-output.txt", supervisor_result.stdout)
        if supervisor_result.returncode != 0:
            failures.append(f"supervisor exited rc={supervisor_result.returncode}")

        manifest_path = supervisor_dir / "manifest.json"
        if manifest_path.exists():
            manifest = load_json(manifest_path)
            failures.extend(validate_manifest(manifest, args))
        else:
            failures.append(f"missing supervisor manifest: {manifest_path}")

        if audit_path.exists():
            records, malformed = read_audit_jsonl(audit_path)
            audit_summary = summarize_audit(records, malformed, audit_path)
            store.write_json("broker-audit-summary.json", audit_summary)
            store.write_text("broker-audit-report.md", render_audit_markdown(audit_summary))
            failures.extend(validate_audit(audit_summary, args))
        elif not args.dry_run:
            failures.append(f"missing broker audit: {audit_path}")

        summary = {
            "schema": "a90-broker-mixed-soak-gate-v190",
            "pass": not failures,
            "backend": args.backend,
            "duration_sec": round(time.monotonic() - started, 6),
            "workload": args.workload or ["cpu-memory-profiles"],
            "profile": args.profile,
            "workload_profile": args.workload_profile,
            "seed": args.seed,
            "supervisor_rc": supervisor_rc,
            "run_dir": str(store.run_dir),
            "supervisor_dir": str(supervisor_dir),
            "broker_runtime_dir": str(runtime_dir),
            "socket": str(socket_path),
            "audit": str(audit_path),
            "dry_run": args.dry_run,
            "failures": failures,
        }
        store.write_json("broker-mixed-soak-summary.json", summary)
        store.write_text("broker-mixed-soak-report.md", render_report(summary, manifest, audit_summary))
        print(
            f"{'PASS' if summary['pass'] else 'FAIL'} backend={args.backend} "
            f"workloads={','.join(args.workload or ['cpu-memory-profiles'])} supervisor_rc={supervisor_rc} "
            f"failures={len(failures)} out={store.run_dir}"
        )
        return 0 if summary["pass"] else 1
    finally:
        broker_stdout, broker_stderr = stop_broker(broker_process)
```

scripts/revalidation/a90_broker_mixed_soak_gate.py (L94 to 120)
  Note: The mixed-soak validator starts the broker with start_new_session=True, so an outer kill of the validator process will not automatically kill the broker child.
```
def start_broker(args: argparse.Namespace, runtime_dir: Path) -> subprocess.Popen[str]:
    ensure_private_dir(runtime_dir)
    command = [
        sys.executable,
        str(broker_script()),
        "serve",
        "--backend",
        args.backend,
        "--runtime-dir",
        str(runtime_dir),
        "--socket-name",
        args.socket_name,
        "--audit-name",
        args.audit_name,
        "--bridge-host",
        args.bridge_host,
        "--bridge-port",
        str(args.bridge_port),
    ]
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
```

scripts/revalidation/a90_broker_soak_suite.py (L110 to 129)
  Note: The live broker-backed mixed-soak validator is wrapped by the outer timeout; in non-dry-run mode this subvalidator starts a live ACM broker.
```
        (
            "broker-mixed-soak",
            [
                sys.executable,
                str(script("a90_broker_mixed_soak_gate.py")),
                "--run-dir",
                str(mixed_dir),
                "--duration-sec",
                str(args.duration_sec),
                "--observer-interval",
                str(args.observer_interval),
                "--workload-profile",
                "smoke",
                "--seed",
                "195",
                "--expect-version",
                args.expect_version,
                *(["--dry-run"] if args.dry_run else []),
            ],
            max(args.duration_sec + 360.0, 120.0),
```

scripts/revalidation/a90_broker_soak_suite.py (L164 to 173)
  Note: The main loop calls run_step without exception handling, so a timeout aborts the suite instead of recording a controlled failure and cleanup.
```
def main() -> int:
    args = build_parser().parse_args()
    store = EvidenceStore(args.run_dir)
    planned_steps = build_steps(args, store)
    steps: list[SuiteStep] = []
    for name, command, timeout_sec in planned_steps:
        step = run_step(store, name, command, timeout_sec=timeout_sec)
        steps.append(step)
        if args.stop_on_failure and not step.ok:
            break
```

scripts/revalidation/a90_broker_soak_suite.py (L59 to 73)
  Note: The new suite runs each subvalidator with subprocess.run(timeout=...), but does not catch TimeoutExpired or explicitly kill a process group/tree.
```
def run_step(store: EvidenceStore,
             name: str,
             command: list[str],
             *,
             timeout_sec: float) -> SuiteStep:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_sec,
    )
```

scripts/revalidation/a90_broker.py (L615 to 623)
  Note: The broker executes non-destructive/non-rebind requests through its backend; an orphaned live broker can therefore continue dispatching allowed device commands.
```
            self.audit(
                "dispatch",
                {
                    **audit_request_payload(request),
                    "backend": self.backend.name,
                },
            )
            try:
                if request.command_class == "rebind-destructive":
```

