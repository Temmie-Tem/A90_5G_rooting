# F042. Reporter accepts unauthenticated tcpctl as PASS

## Metadata

| field | value |
|---|---|
| finding_id | `bfca11c90eb481919c3d98d0f7c66fdd` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/bfca11c90eb481919c3d98d0f7c66fdd |
| severity | `medium` |
| status | `mitigated-host-batch-c` |
| detected_at | `2026-05-08T18:19:54.338307Z` |
| committed_at | `2026-05-09 01:18:00 +0900` |
| commit_hash | `d77e58e0724c5305fe94dfcf7960713e41d53565` |
| relevant_paths | `docs/plans/NATIVE_INIT_V160_NCM_TCP_STABILITY_PLAN_2026-05-09.md` <br> `scripts/revalidation/ncm_tcp_stability_report.py` <br> `stage3/linux_init/a90_tcpctl.c` |
| source_csv | `docs/security/codex-security-findings-2026-05-08T18-39-05.112Z.csv` |

## CSV Description

The commit adds a reporter whose stated purpose is to validate a token-authenticated a90_tcpctl path, but validate_tcpctl() only checks for generic readiness, pass counters, zero failures, and a zero-loss ping. It never verifies that the captured tcpctl listener was started with authentication required, even though tcpctl_host/a90_tcpctl transcripts include an auth=required/auth=none marker. As a result, a transcript from tcpctl_host.py --no-auth soak, or from a wrong/legacy helper that listens with auth=none, can still produce a PASS report. This can falsely certify the USB NCM root command channel as token-authenticated and stable, masking an authentication regression before later operational decisions.

## Local Initial Assessment

- Valid evidence-integrity finding: a network stability report must verify the authentication property it claims.
- Related to earlier tcpctl auth findings and to v178-v184 serverization gate.
- Treat as a blocker for using NCM/TCP reports as Wi-Fi/server-readiness evidence.

## Local Remediation

- Implemented in `952e572` (`Require authenticated NCM tcpctl evidence`).
- Planned Batch C fix.
- Require `auth=required` in tcpctl transcript and fail if `auth=none` is present.
- Add a negative fixture/check where a `--no-auth` transcript cannot pass.
- Keep ping/status/run counters as stability checks, not as substitutes for auth verification.

## Codex Cloud Detail

Reporter accepts unauthenticated tcpctl as PASS
Link: https://chatgpt.com/codex/cloud/security/findings/bfca11c90eb481919c3d98d0f7c66fdd?sev=&repo=https%3A%2F%2Fgithub.com%2FTemmie-Tem%2FA90_5G_rooting
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: d77e58e
Author: shs02140@gmail.com
Created: 2026. 5. 9. 오전 3:19:54
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced: scripts/revalidation/ncm_tcp_stability_report.py validates stability evidence but omits an authentication-required check. The docs and report describe the validated path as token-authenticated, but the implemented checks do not enforce that property.
The commit adds a reporter whose stated purpose is to validate a token-authenticated a90_tcpctl path, but validate_tcpctl() only checks for generic readiness, pass counters, zero failures, and a zero-loss ping. It never verifies that the captured tcpctl listener was started with authentication required, even though tcpctl_host/a90_tcpctl transcripts include an auth=required/auth=none marker. As a result, a transcript from tcpctl_host.py --no-auth soak, or from a wrong/legacy helper that listens with auth=none, can still produce a PASS report. This can falsely certify the USB NCM root command channel as token-authenticated and stable, masking an authentication regression before later operational decisions.

# Validation
## Rubric
- [x] Documentation/report scope says the path being validated is token-authenticated.
- [x] Reporter CLI has no option or default requiring an expected authentication mode.
- [x] validate_tcpctl() never rejects auth=none or requires auth=required while it does enforce other stability checks.
- [x] The real tcpctl/tcpctl_host transcript path can expose unauthenticated mode through auth=none/--no-auth markers.
- [x] A transcript explicitly showing auth=none can still produce a PASS report with no auth-related check in output.
## Report
Validated the finding against commit d77e58e0724c5305fe94dfcf7960713e41d53565. The plan/report state the validation objective is a token-authenticated a90_tcpctl path: docs/plans/NATIVE_INIT_V160_NCM_TCP_STABILITY_PLAN_2026-05-09.md:7 and docs/reports/NATIVE_INIT_V160_NCM_TCP_STABILITY_2026-05-09.md:9. The reporter CLI exposes --expect-ready/--expect-version but no expected auth mode option at scripts/revalidation/ncm_tcp_stability_report.py:80-90. validate_tcpctl() checks ready/banner, summary/shutdown, serial run, final ping, duration/cycles, failures, and pass counters at scripts/revalidation/ncm_tcp_stability_report.py:129-178, but contains no auth=required/auth=none validation. The tcpctl service provides a concrete listener auth marker at stage3/linux_init/a90_tcpctl.c:642-647, and tcpctl_host.py can start a legacy unauthenticated listener with --no-auth at scripts/revalidation/tcpctl_host.py:326-330 and :706-709. I created a minimal soak transcript containing both 'auth=none' and a '--no-auth' serial run while satisfying the reporter's other stability markers. Running ncm_tcp_stability_report.py on it exited 0 and printed PASS. Generated JSON had pass=true, the input contained auth=none, and the emitted check names were only: tcpctl ready banner, summary present, shutdown marker, serial run done, final ncm ping, duration threshold, cycle threshold, failure count zero, no fail lines, tcp ping count, host ping count, status count, run count, ncm setup transcript, longsoak trend report. Non-interactive pdb tracing of validate_tcpctl() confirmed 'auth=none' in text evaluated True, args only had expect_ready/expect_version/min thresholds, all relevant checks were added as passing, and auth_check_present=False. Direct crash reproduction is not applicable because this is a Python logic validation flaw, not memory corruption; the direct dynamic PoC reproduces the false PASS. Valgrind was attempted but is not installed in the container and is not applicable to this Python logic flaw.

# Evidence
docs/plans/NATIVE_INIT_V160_NCM_TCP_STABILITY_PLAN_2026-05-09.md (L7 to 20)
  Note: The plan states the goal is validating a token-authenticated tcpctl path, but the listed machine checks do not include verifying auth is required.
```
- 목적은 Wi-Fi 작업 전에 USB NCM과 token-authenticated `a90_tcpctl` 경로를 장시간 반복 검증하는 것이다.
- v160은 먼저 host-side stability evidence/report 경로를 고정한다. device boot image bump는 NCM/TCP 안정성 검증에 필요한 device-side 변경이 생길 때만 별도 판단한다.

## Scope

- `scripts/revalidation/tcpctl_host.py soak`를 공식 NCM/TCP stability loop로 사용한다.
- `scripts/revalidation/ncm_host_setup.py setup` 출력, `tcpctl_host.py soak` 출력, optional longsoak report JSON을 하나의 PASS/FAIL report로 묶는다.
- `scripts/revalidation/ncm_tcp_stability_report.py`를 추가해 다음 조건을 기계적으로 검증한다.
  - tcpctl ready banner 확인
  - NCM ping zero packet loss 확인
  - tcpctl ping/status/run pass count 확인
  - final serial bridge recovery 확인
  - optional longsoak trend pass 확인
- helper mismatch는 `tcpctl_host.py smoke/soak`의 ready/version output과 local expected helper path/hash 점검으로 잡는다.
```

scripts/revalidation/ncm_tcp_stability_report.py (L129 to 151)
  Note: validate_tcpctl() checks readiness, summary markers, run completion, ping, duration, cycles, and failure counts, but does not reject transcripts showing auth=none or require auth=required.
```
def validate_tcpctl(args: argparse.Namespace, text: str, summary: TcpctlSummary, checks: list[Check]) -> None:
    add_check(checks, "tcpctl ready banner", args.expect_ready in text, args.expect_ready)
    add_check(checks, "summary present", "--- summary ---" in text, "tcpctl_host.py soak summary marker")
    add_check(checks, "shutdown marker", "--- shutdown ---" in text, "shutdown section present")
    add_check(checks, "serial run done", "[done] run" in text, "serial run reports [done] run")
    add_check(checks, "final ncm ping", "0% packet loss" in text, "final ping reports zero packet loss")
    if args.expect_version:
        add_check(checks, "expected native version", args.expect_version in text, args.expect_version)

    add_check(
        checks,
        "duration threshold",
        summary.duration_sec is not None and summary.duration_sec >= args.min_duration,
        f"duration={summary.duration_sec} min={args.min_duration}",
    )
    add_check(
        checks,
        "cycle threshold",
        summary.cycles is not None and summary.cycles >= args.min_cycles,
        f"cycles={summary.cycles} min={args.min_cycles}",
    )
    add_check(checks, "failure count zero", summary.failures == 0, f"failures={summary.failures}")
    add_check(checks, "no fail lines", summary.fail_lines == 0, f"fail_lines={summary.fail_lines}")
```

scripts/revalidation/ncm_tcp_stability_report.py (L80 to 90)
  Note: The reporter exposes only an expected ready-banner option; there is no expected auth mode option.
```
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tcpctl-soak", required=True, help="tcpctl_host.py soak transcript")
    parser.add_argument("--ncm-setup", help="optional ncm_host_setup.py setup transcript")
    parser.add_argument("--longsoak-report-json", help="optional native_long_soak_report.py JSON")
    parser.add_argument("--expect-version", help="expected native init version banner in bridge-version output")
    parser.add_argument("--expect-ready", default="a90_tcpctl v1 ready")
    parser.add_argument("--min-duration", type=float, default=0.0)
    parser.add_argument("--min-cycles", type=int, default=1)
    parser.add_argument("--out-md", default="tmp/soak/ncm-tcp-stability-report.md")
    parser.add_argument("--out-json", default="tmp/soak/ncm-tcp-stability-report.json")
```

stage3/linux_init/a90_tcpctl.c (L642 to 647)
  Note: The tcpctl service emits an auth=required/auth=none marker in its listener banner, so the new reporter has a concrete transcript field it could validate but currently ignores.
```
    printf("tcpctl: listening bind=%s port=%u idle_timeout=%ds max_clients=%d auth=%s\n",
           config->bind_addr,
           config->port,
           config->idle_timeout_sec,
           config->max_clients,
           auth_required(config) ? "required" : "none");
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: low | Policy adjusted: low
## Rationale
The original medium rating is appropriate. Static evidence confirms the bug: the project documents the validation target as token-authenticated, tcpctl emits auth=required/auth=none, and tcpctl_host.py can intentionally start unauthenticated mode, while ncm_tcp_stability_report.py has no auth-mode check and derives PASS only from non-auth stability checks. The issue is in scope because the threat model includes host-side revalidation and false-positive automation around root control channels. It should not be raised to high or critical because the reporter is a local/internal evidence-generation tool and does not itself expose the tcpctl service or grant remote code execution; an attacker must influence validation artifacts or operator behavior and the security harm is downstream masking of an auth regression. It is more than informational because the affected evidence is used to validate a root-capable TCP control path.
## Likelihood
medium - Exploitation requires local influence over validation inputs/invocation or a mistaken/shared-lab workflow; there is no public network entry point in the reporter itself. The path is nevertheless plausible because --no-auth is an exposed option and the reporter is intended to process normal tcpctl_host.py soak transcripts.
## Impact
medium - The direct impact is integrity compromise of validation evidence, not immediate attacker command execution. However, the evidence concerns a root-capable TCP control service, so falsely certifying unauthenticated mode can mask a serious authentication regression and influence unsafe operational decisions.
## Assumptions
- The host-side revalidation scripts are part of the intended operational workflow for this repository, not disposable tests.
- The attacker model for this specific flaw is a local/shared-lab actor, compromised host process, CI/artifact tamperer, or mistaken operator who can influence the transcript or invocation of the stability report.
- No cloud deployment, Kubernetes ingress, or public load balancer artifacts were present or needed for this assessment.
- A stability report is generated from a tcpctl soak transcript as part of the validation workflow
- The transcript or tcpctl_host invocation reflects unauthenticated mode, such as auth=none or --no-auth
- A downstream operator or automation trusts the resulting PASS report as evidence that the path is token-authenticated
## Path
tcpctl_host soak transcript
        |
        v
 auth=none / --no-auth evidence
        |
        v
 ncm_tcp_stability_report.validate_tcpctl()
        |  (no auth=required check)
        v
 PASS report
        |
        v
 false trust in token-authenticated root TCP control path
## Path evidence
- `docs/plans/NATIVE_INIT_V160_NCM_TCP_STABILITY_PLAN_2026-05-09.md:7-20` - The plan defines the goal as validating a USB NCM and token-authenticated a90_tcpctl path, but the listed mechanical checks omit authentication mode.
- `docs/reports/NATIVE_INIT_V160_NCM_TCP_STABILITY_2026-05-09.md:5-9` - The report labels the result PASS and describes the objective as proving a token-authenticated a90_tcpctl control loop.
- `scripts/revalidation/ncm_tcp_stability_report.py:80-90` - The reporter CLI exposes expected ready/version and thresholds, but no expected authentication-mode option.
- `scripts/revalidation/ncm_tcp_stability_report.py:129-178` - validate_tcpctl() validates stability markers and counters but has no check for auth=required and no rejection of auth=none.
- `scripts/revalidation/ncm_tcp_stability_report.py:269-283` - The reporter reads the transcript, runs validate_tcpctl(), and computes pass_ok solely from the added checks; therefore absent checks cannot fail the report.
- `stage3/linux_init/a90_tcpctl.c:642-647` - The tcpctl listener emits an auth=required/auth=none marker that the reporter could validate.
- `stage3/linux_init/a90_tcpctl.c:272-280` - The runtime distinguishes auth-required and unauthenticated modes; client authorization succeeds automatically when auth is not required.
- `stage3/linux_init/a90_tcpctl.c:405-407` - The root-capable run command depends on client_authorized(), making an auth=none listener materially important.
- `scripts/revalidation/tcpctl_host.py:326-330` - tcpctl_host.py starts the listener with '-' instead of the token path when --no-auth is set.
- `scripts/revalidation/tcpctl_host.py:706-708` - The host workflow exposes a documented --no-auth legacy mode.
## Narrative
The finding is real and in scope. The v160 plan and report state that the workflow is intended to prove a USB NCM plus token-authenticated a90_tcpctl path, but the reporter only validates generic stability signals. Its CLI has --expect-ready and --expect-version but no expected authentication-mode option. validate_tcpctl() checks the ready banner, summary/shutdown markers, serial run completion, zero-loss ping, duration, cycles, failures, and pass counters, but never requires auth=required or rejects auth=none. This omission is reachable through the normal revalidation workflow because tcpctl_host.py supports --no-auth and constructs the device listen command with '-' instead of the token path when that flag is used. The device tcpctl service emits auth=required/auth=none in listener/status output, so the reporter has a concrete field it could enforce. The impact is not direct remote command execution by itself; it is integrity loss in security evidence that can mask an unauthenticated root TCP command channel. Medium severity is appropriate given the constrained local/artifact preconditions and potentially serious downstream consequence.
## Controls
- tcpctl runtime supports token authentication when configured with a token path
- tcpctl_host.py defaults include a token path and only disables auth with --no-auth
- NCM/tcpctl workflow is lab-local and opt-in rather than public Internet-facing
- Reporter output files are written with private directory/file modes
- No reporter-level auth-mode control currently enforces auth=required
## Blindspots
- Static-only review cannot determine how often operators or CI consume this reporter output for release/blocking decisions.
- No repository deployment manifests were present to show whether tcpctl is ever exposed beyond the USB NCM lab network.
- The previous dynamic validation demonstrated a false PASS, but this assessment did not interact with a real A90 device or live tcpctl listener.
- Downstream operational consequences depend on human or automation trust in the generated report.
