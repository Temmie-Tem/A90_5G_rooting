# F008. Soak validator can execute a90ctl from an untrusted CWD

## Metadata

| field | value |
|---|---|
| finding_id | `546954b382d48191ae18852d95ce2c2c` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/546954b382d48191ae18852d95ce2c2c |
| severity | `medium` |
| status | `new` |
| detected_at | `2026-05-04T10:28:54.160265Z` |
| committed_at | `2026-05-04 00:58:55 +0900` |
| commit_hash | `e959e00df066f1adf429dcda570a51d19e7c9159` |
| relevant_paths | `scripts/revalidation/native_soak_validate.py` |
| has_patch | `false` |

## CSV Description

The newly added soak validator builds its subprocess command with the literal relative path "scripts/revalidation/a90ctl.py". Because subprocess.run is called without cwd, that path is resolved relative to the process current working directory, not relative to native_soak_validate.py or the repository root. If an operator invokes /workspace/A90_5G_rooting/scripts/revalidation/native_soak_validate.py while their current directory is attacker-controlled, an attacker can place scripts/revalidation/a90ctl.py in that directory and have it executed by sys.executable with the operator's host privileges. Other nearby revalidation scripts avoid this by deriving REPO_ROOT from __file__ and passing an absolute A90CTL path. The fix is to compute REPO_ROOT = Path(__file__).resolve().parents[2], use str(REPO_ROOT / "scripts" / "revalidation" / "a90ctl.py"), and preferably set cwd=REPO_ROOT in subprocess.run.

## Codex Cloud Detail

Soak validator can execute a90ctl from an untrusted CWD
Link: https://chatgpt.com/codex/cloud/security/findings/546954b382d48191ae18852d95ce2c2c
Criticality: medium (attack path: medium)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: e959e00
Author: shs02140@gmail.com
Created: 2026. 5. 4. 오후 7:28:54
Assignee: Unassigned
Signals: Security, Validated, Attack-path

# Summary
Introduced a host-side arbitrary code execution risk in the new native_soak_validate.py script due to resolving the helper program through the caller's current working directory.
The newly added soak validator builds its subprocess command with the literal relative path "scripts/revalidation/a90ctl.py". Because subprocess.run is called without cwd, that path is resolved relative to the process current working directory, not relative to native_soak_validate.py or the repository root. If an operator invokes /workspace/A90_5G_rooting/scripts/revalidation/native_soak_validate.py while their current directory is attacker-controlled, an attacker can place scripts/revalidation/a90ctl.py in that directory and have it executed by sys.executable with the operator's host privileges. Other nearby revalidation scripts avoid this by deriving REPO_ROOT from __file__ and passing an absolute A90CTL path. The fix is to compute REPO_ROOT = Path(__file__).resolve().parents[2], use str(REPO_ROOT / "scripts" / "revalidation" / "a90ctl.py"), and preferably set cwd=REPO_ROOT in subprocess.run.

# Validation
## Rubric
- [x] Confirm native_soak_validate.py constructs the a90ctl helper path as a literal relative path rather than an absolute path derived from __file__.
- [x] Confirm subprocess.run executes that command without cwd=REPO_ROOT or another safe cwd.
- [x] Confirm the validator can be invoked by absolute path from an arbitrary current directory and reaches run_one/subprocess.run.
- [x] Demonstrate that an attacker-controlled scripts/revalidation/a90ctl.py in the caller cwd is executed with the operator's Python interpreter and privileges.
- [x] Compare nearby revalidation scripts to verify the expected safe pattern is deriving REPO_ROOT/A90CTL from __file__ and setting cwd=REPO_ROOT.
## Report
Validated the finding on commit e959e00df066f1adf429dcda570a51d19e7c9159. The vulnerable code is present in scripts/revalidation/native_soak_validate.py:64-75, where a90ctl_command() returns sys.executable plus the literal relative path "scripts/revalidation/a90ctl.py". It is executed at scripts/revalidation/native_soak_validate.py:78-87 via subprocess.run(...) without cwd=..., so the helper path is resolved relative to the caller's current working directory. Nearby scripts use the safer pattern, e.g. scripts/revalidation/helper_deploy.py:21-39 and scripts/revalidation/diag_collect.py:14-26 derive REPO_ROOT from __file__, build an absolute A90CTL path, and pass cwd=REPO_ROOT.

Dynamic reproduction: I created an attacker-controlled cwd at /workspace/poc_attacker_cwd containing scripts/revalidation/a90ctl.py. That malicious helper wrote /workspace/validation_artifacts/native_soak_marker.txt and printed output satisfying the validator checks. Running the trusted validator by absolute path from the attacker cwd succeeded and executed the malicious helper:
Command: cd /workspace/poc_attacker_cwd && python3 /workspace/A90_5G_rooting/scripts/revalidation/native_soak_validate.py --cycles 1 --sleep 0 --timeout 1 --command version --out /workspace/validation_artifacts/native-soak-transcript.txt
Output: PASS cycles=1 commands=1
Marker evidence: MALICIOUS_A90CTL_EXECUTED; argv=['scripts/revalidation/a90ctl.py', '--host', '127.0.0.1', '--port', '54321', '--timeout', '1', 'version']; cwd=/workspace/poc_attacker_cwd; uid=0.

Debugger validation: I used pdb non-interactively and broke before subprocess.run at native_soak_validate.py:80. Pdb printed a90ctl_command(args, command) as ['/root/.pyenv/versions/3.10.19/bin/python3', 'scripts/revalidation/a90ctl.py', '--host', '127.0.0.1', '--port', '54321', '--timeout', '1', 'version'] and os.getcwd() as '/workspace/poc_attacker_cwd', confirming the subprocess command contains a relative helper path while the process cwd is attacker-controlled. Valgrind/gdb were not installed and are not applicable to this Python subprocess path-hijack issue; a native crash is not expected.

# Evidence
scripts/revalidation/native_soak_validate.py (L64 to 75)
  Note: a90ctl_command constructs the helper invocation using the relative path "scripts/revalidation/a90ctl.py", which is resolved against the current working directory instead of the repository/script location.
```
def a90ctl_command(args: argparse.Namespace, command: str) -> list[str]:
    return [
        sys.executable,
        "scripts/revalidation/a90ctl.py",
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--timeout",
        str(int(args.timeout)),
        *shlex.split(command),
    ]
```

scripts/revalidation/native_soak_validate.py (L78 to 87)
  Note: subprocess.run executes the command without setting cwd, so a malicious scripts/revalidation/a90ctl.py in an attacker-controlled current directory can be run by the Python interpreter.
```
def run_one(args: argparse.Namespace, cycle: int, command: str) -> CheckResult:
    started = time.monotonic()
    proc = subprocess.run(
        a90ctl_command(args, command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=args.timeout + 5,
        check=False,
    )
```

# Attack-path analysis
Final: medium | Decider: model_decided | Matrix severity: ignore | Policy adjusted: ignore
## Rationale
Adjusted from high to medium. The code issue is valid and in-scope, and the impact is credible host-side arbitrary code execution as the operator. The decisive limiting factors are reachability and exploit preconditions: this is local filesystem/CWD hijacking, not a network-exposed service; it requires a malicious directory layout plus operator interaction; and the documented example runs from the repository root, where the legitimate helper would be resolved. Probability × impact therefore supports medium risk rather than high, while still warranting prompt remediation because the fix is straightforward.
## Likelihood
low - The bug is not reachable over a public network or service endpoint. It requires attacker write/control over the operator's current working directory and user interaction to invoke the validator from that directory. The documented workflow shows a repository-root relative invocation, which makes accidental exploitation less likely, though absolute-path invocation from arbitrary directories is plausible.
## Impact
high - Successful exploitation executes arbitrary Python code on the host as the operator running the validation script. This can compromise operator files and the device-control environment; impact could be greater if the script is run with elevated privileges.
## Assumptions
- The attacker can create files under an operator-visible or operator-current working directory, specifically scripts/revalidation/a90ctl.py.
- The operator invokes the trusted native_soak_validate.py by absolute path or otherwise from outside the repository root while the current working directory is attacker-controlled.
- The operator runs the host-side validation script with the normal privileges of their workstation account; if run with elevated privileges, impact increases accordingly.
- No cloud or deployed infrastructure was queried; assessment is based only on repository artifacts and supplied validation evidence.
- attacker-controlled current working directory contents
- malicious file at scripts/revalidation/a90ctl.py relative to that current working directory
- operator user interaction to run native_soak_validate.py from that working directory
- Python interpreter available on the host
## Path
Attacker CWD
  └─ scripts/revalidation/a90ctl.py  [malicious]
        ▲
        │ relative path lookup
Trusted native_soak_validate.py ──subprocess.run(no cwd)──> Python executes helper
        │
        └─ result: arbitrary code as operator on host
## Path evidence
- `scripts/revalidation/native_soak_validate.py:64-75` - a90ctl_command returns sys.executable followed by the literal relative path "scripts/revalidation/a90ctl.py".
- `scripts/revalidation/native_soak_validate.py:78-87` - subprocess.run executes the constructed argv without setting cwd, so the relative helper path is resolved against the caller's current working directory.
- `scripts/revalidation/helper_deploy.py:21-39` - Nearby host tooling shows the safer intended pattern: derive REPO_ROOT from __file__, build an absolute A90CTL path, and pass cwd=REPO_ROOT.
- `docs/reports/NATIVE_INIT_V105_SOAK_RC_2026-05-04.md:99-104` - Repository documentation includes native_soak_validate.py in the v105 quick soak validation workflow, supporting in-scope operational relevance.
## Narrative
The finding is real: native_soak_validate.py constructs the helper invocation with the relative path "scripts/revalidation/a90ctl.py" and executes it with subprocess.run without cwd. That means the helper is resolved relative to the caller's current working directory, not the repository. The supplied validation evidence demonstrates execution of a malicious helper from an attacker-controlled CWD. The issue is in-scope because this script is documented host-side validation tooling. However, it is not remotely exposed and exploitation requires attacker-controlled filesystem placement plus operator interaction from a non-repository CWD; documented examples run it from the repository root. Therefore the impact is high when triggered, but practical likelihood is low, making medium a more calibrated final risk than the original high.
## Controls
- No public network ingress for this bug
- Documented command examples run from repository root, which reduces but does not eliminate risk
- No authentication or authorization control applies to local subprocess helper resolution
- No cwd pinning or absolute helper path in the vulnerable script
- Nearby scripts use absolute paths and cwd=REPO_ROOT, showing an available control pattern
## Blindspots
- Static review cannot determine how operators normally invoke this script in real environments or CI.
- No repository CI manifests were identified in this review to confirm whether the vulnerable script is run from arbitrary workspaces.
- Actual host privilege level depends on operator behavior outside the repository.
- The supplied dynamic PoC evidence was considered, but this attack-path assessment did not execute new exploit code beyond reading repository artifacts.
