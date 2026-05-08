# F044. NCM/TCP preflight wrapper can never pass smoke mode

## Metadata

| field | value |
|---|---|
| finding_id | `2655549e3b64819184f679e26684673e` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/2655549e3b64819184f679e26684673e |
| severity | `informational` |
| status | `mitigated-host-batch-c` |
| detected_at | `2026-05-08T18:17:22.018854Z` |
| committed_at | `2026-05-09 02:58:08 +0900` |
| commit_hash | `e00f199081f3fb63e722f1e39b77fea494de0800` |
| relevant_paths | `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py` <br> `scripts/revalidation/tcpctl_host.py` |
| source_csv | `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

The commit adds scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py to wrap tcpctl_host.py smoke. Its run step treats the child command as successful only if the return code is 0 and the captured output contains the literal string "--- tcpctl-checks ---". However, the existing tcpctl_host.py smoke implementation prints individual section headers such as "--- ping ---", "--- version ---", "--- status ---", "--- shutdown ---", "--- serial-run ---", "--- bridge-version ---", and "--- ncm-ping ---"; it does not print "--- tcpctl-checks ---" anywhere. As a result, the new module only appears to work in the current skipped path. In a correctly configured NCM environment, a successful tcpctl smoke run will still be reported as a module failure.

## Local Initial Assessment

- Valid functional/evidence finding: current wrapper success predicate does not match `tcpctl_host.py smoke` output.
- Related to F042 because both can make NCM/TCP evidence misleading, one as false PASS and one as false FAIL.
- Informational severity, but should be fixed before mixed-soak gates rely on the module.

## Local Remediation

- Implemented in `952e572` (`Require authenticated NCM tcpctl evidence`).
- Planned Batch C fix.
- Replace `--- tcpctl-checks ---` expectation with actual smoke sections: `--- ping ---`, `--- version ---`, `--- status ---`, `--- shutdown ---`, and `[done] run`.
- Keep the structured SKIP behavior when host NCM is not configured.

## Codex Cloud Detail

NCM/TCP preflight wrapper can never pass smoke mode
Link: https://chatgpt.com/codex/cloud/security/findings/2655549e3b64819184f679e26684673e?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: informational (attack path: ignore)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: e00f199
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:17:22
Assignee: Unassigned
Signals: Validated, Attack-path

# Summary
A functional regression was introduced in the new NCM/TCP supervisor module. This is not a security vulnerability by itself, but it undermines validation by making the new NCM/TCP preflight fail on successful configured runs.
The commit adds scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py to wrap tcpctl_host.py smoke. Its run step treats the child command as successful only if the return code is 0 and the captured output contains the literal string "--- tcpctl-checks ---". However, the existing tcpctl_host.py smoke implementation prints individual section headers such as "--- ping ---", "--- version ---", "--- status ---", "--- shutdown ---", "--- serial-run ---", "--- bridge-version ---", and "--- ncm-ping ---"; it does not print "--- tcpctl-checks ---" anywhere. As a result, the new module only appears to work in the current skipped path. In a correctly configured NCM environment, a successful tcpctl smoke run will still be reported as a module failure.

# Validation
## Rubric
- [x] Confirm the new wrapper enters the run path only for configured NCM cases and invokes `tcpctl_host.py smoke`.
- [x] Confirm the wrapper requires both child return code 0 and the literal marker `--- tcpctl-checks ---`.
- [x] Confirm `tcpctl_host.py command_smoke()` returns 0 on success but prints only individual section headers, not the required marker.
- [x] Dynamically simulate a successful smoke run and show `NcmTcpPreflightModule.run()` returns `StepResult.ok == False` with `rc=0`.
- [x] Check for counter-evidence such as another producer of `--- tcpctl-checks ---`; none was found in targeted `scripts/revalidation` grep.
## Report
Validated the finding as a Python functional regression. Targeted code review showed `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:56-67` runs `tcpctl_host.py smoke`, writes the wrapper output, then sets `ok = result.returncode == 0 and "--- tcpctl-checks ---" in result.stdout`. The actual smoke implementation at `scripts/revalidation/tcpctl_host.py:507-545` prints section headers `--- ping ---`, `--- version ---`, `--- status ---`, `--- run-uname ---`, `--- run-ifconfig ---`, `--- shutdown ---`, `--- serial-run ---`, `--- bridge-version ---`, and `--- ncm-ping ---`, then returns 0; it does not emit `--- tcpctl-checks ---`. A targeted grep found the literal `tcpctl-checks` only in the wrapper expectation. I built a PoC that monkeypatches `tcpctl_host.command_smoke()` dependencies to simulate a successful configured NCM smoke run with return code 0, then feeds that real smoke-style output into `NcmTcpPreflightModule.run()` via a mocked `subprocess.run`. PoC output: `tcpctl_smoke_rc=0`, `contains_expected_wrapper_marker=False`, `wrapper_step_ok=False`, `wrapper_step_detail=rc=0`. A noninteractive pdb trace broke at `ncm_tcp_preflight.py:67` and printed `result.returncode` as `0`, marker containment as `False`, and `ok` as `False`, proving the successful child run is reported as a failed module step. Direct crash validation is not applicable because this is a Python validation false-negative, not a memory-safety crash. Valgrind was attempted but unavailable in the container (`valgrind not installed`).

# Evidence
scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py (L56 to 67)
  Note: The wrapper requires the child command to return 0 and contain the literal marker "--- tcpctl-checks ---". That marker is not produced by tcpctl_host.py smoke, so ok becomes false for successful smoke runs.
```
        result = subprocess.run(
            command,
            cwd=ctx.repo_root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=240,
        )
        ctx.store.write_text(f"modules/{self.name}/wrapper-output.txt", "$ " + " ".join(command) + "\n\n" + result.stdout)
        ok = result.returncode == 0 and "--- tcpctl-checks ---" in result.stdout
        return StepResult("run", ok, f"rc={result.returncode}", 0.0)
```

scripts/revalidation/tcpctl_host.py (L507 to 545)
  Note: The smoke command prints section headers for individual checks and returns 0 on success, but never emits the "--- tcpctl-checks ---" marker expected by the new wrapper.
```
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

    print("--- shutdown ---")
    shutdown_output = tcpctl_expect_ok(args, "shutdown")
    print(shutdown_output, end="" if shutdown_output.endswith("\n") else "\n")

    runner.join(args.bridge_timeout)
    if runner.is_alive():
        raise RuntimeError("tcpctl serial run did not finish after shutdown")
    if runner.error is not None:
        raise RuntimeError(f"bridge run failed: {runner.error}")

    print("--- serial-run ---")
    print(runner.text(), end="" if runner.text().endswith("\n") else "\n")
    if "[done] run" not in runner.text():
        raise RuntimeError("tcpctl serial run did not finish cleanly")

    print("--- bridge-version ---")
    bridge_output = device_command(
        args,
        "version",
        timeout=args.bridge_timeout,
    )
    print(bridge_output, end="" if bridge_output.endswith("\n") else "\n")

    print("--- ncm-ping ---")
    print(host_ping(args, 3), end="")

    return 0
```

# Attack-path analysis
Final: ignore | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Adjusted from low to ignore for security triage. Static evidence confirms a real functional regression: scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:66 requires '--- tcpctl-checks ---', while scripts/revalidation/tcpctl_host.py:507-545 never prints that marker and returns 0 on successful smoke. The affected component is in-scope host validation tooling, but the only demonstrated effect is a false-negative harness result for a trusted operator. There is no attacker-controlled input, public ingress, privilege escalation, data exposure, command injection, auth bypass, or cross-boundary security impact. Probability × impact for security purposes is therefore negligible even though the correctness bug should be fixed.
## Likelihood
ignore - The bug is likely reproducible in normal configured NCM testing, but exploitation likelihood as a security vulnerability is ignored because there is no realistic attacker-controlled entry point or security payoff.
## Impact
ignore - The defect can make a valid NCM/TCP smoke run fail in the harness, reducing validation reliability. It does not grant an attacker capabilities, bypass authentication, expose secrets, mutate privileged state unexpectedly, or increase command-channel exposure.
## Assumptions
- Analysis is limited to repository artifacts in /workspace/A90_5G_rooting and prior validation evidence; no device, network, cloud, or external APIs were invoked.
- The NCM/TCP preflight module is operator-run host validation tooling, not an automatically exposed production service.
- Default bridge/NCM assumptions from the repository threat model apply: localhost bridge by default and USB/NCM lab-local use.
- A trusted operator runs native_test_supervisor.py run ncm-tcp-preflight or equivalent harness path.
- The host USB NCM path to 192.168.7.2 is reachable so the module does not skip.
- tcpctl_host.py smoke completes successfully and returns 0 while emitting its normal section headers.
## Path
Operator CLI -> NCM preflight -> tcpctl_host.py smoke rc=0 -> stdout has normal section headers only -> wrapper missing-marker check fails -> harness false-negative
## Path evidence
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:12-17` - Defines the affected host-side module as ncm-tcp-preflight and marks it as requiring NCM.
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:22-36` - Prepare step only proceeds when 192.168.7.2 is reachable; otherwise the module skips, limiting reachability to configured lab NCM use.
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:41-67` - Run step invokes tcpctl_host.py smoke and sets ok only when return code is 0 and stdout contains the nonexistent '--- tcpctl-checks ---' marker.
- `scripts/revalidation/tcpctl_host.py:507-545` - Smoke command emits individual section headers and returns 0; it does not emit '--- tcpctl-checks ---'.
- `scripts/revalidation/native_test_supervisor.py:31-35` - Registers NcmTcpPreflightModule in the operator-run native test supervisor module list.
- `scripts/revalidation/native_test_supervisor.py:300-303` - Host supervisor defaults to localhost 127.0.0.1 and port 54321 for the control bridge.
- `scripts/revalidation/a90harness/runner.py:64-74` - Module runner aggregates step.ok values, so the false run-step failure becomes a module failure.
- `scripts/revalidation/tcpctl_host.py:20-32` - tcpctl_host.py defaults show local bridge, USB/NCM device IP, TCP port, and token path context; no public ingress is defined here.
## Narrative
The finding is factually correct as a bug: ncm_tcp_preflight.py invokes tcpctl_host.py smoke and then requires stdout to contain '--- tcpctl-checks ---', while tcpctl_host.py smoke prints specific headers such as '--- ping ---', '--- version ---', '--- status ---', '--- shutdown ---', '--- serial-run ---', '--- bridge-version ---', and '--- ncm-ping ---' before returning 0. Grep found the required marker only in the wrapper. The reachable path is normal trusted-operator validation when NCM is already configured. No evidence shows attacker-controlled input, public exposure, auth bypass, privilege escalation, code execution, sensitive data access, or a security boundary being crossed. The impact is limited to false failure/noise in validation.
## Controls
- Default host bridge is localhost 127.0.0.1:54321.
- NCM preflight skips rather than reconfiguring when 192.168.7.2 is not reachable.
- tcpctl_host.py retrieves a tcpctl token unless run with --no-auth.
- Module is explicit operator-run validation tooling, not an automatically internet-exposed service.
- Module runner still attempts cleanup and verify steps after run.
## Blindspots
- Static-only attack-path review did not run against a physical A90/NCM device in this stage.
- The prior validation PoC demonstrates rc=0 with wrapper ok=False, but this stage did not execute that artifact.
- If a separate CI/CD or automation workflow later treats this harness result as authority for security-critical deployment decisions, that downstream coupling would need separate review.
