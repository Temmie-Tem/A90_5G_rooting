# F038-F044 Patch Plan

Date: `2026-05-09`
Source analysis: `docs/security/batches/SECURITY_FINDINGS_F038_F044_ANALYSIS_2026-05-09.md`
Source CSV: `docs/security/scans/codex-security-findings-2026-05-08T18-39-05.112Z.csv`

## Summary


## Implementation Status

- Batch A implemented in `0b8e9bc`: shared path safety, `storage_iotest.py`, and `fs_exerciser_mini.py`.
- Batch B implemented in `c214478`: unsafe replay removal and bounded observer accounting.
- Batch C/D implemented in `952e572`: authenticated tcpctl evidence checks, NCM preflight marker fix, and explicit-interface docs.
- Batch E implemented in this follow-up: local security rescan coverage and F038-F044 status updates.

This patch plan fixes the fresh v160-v177 harness/security findings before
v178-v184 mixed-soak/serverization work continues.

The implementation order is intentional:

1. stop raw serial command injection and destructive path escape;
2. stop unsafe replay and unbounded observer memory growth;
3. make NCM/TCP evidence verify authentication and real wrapper output;
4. correct unsafe NCM resume instructions;
5. extend local targeted security checks for F038-F044.

No device firmware, boot image, Wi-Fi, rfkill, kernel module, watchdog, or
partition behavior is changed by this plan. The first fixes are host-side
validation tooling and documentation.

## Batch A: Path Boundary and Raw Serial Command Hardening

Findings:

- F041: Storage I/O helper allows serial command injection.
- F038: Weak fs exerciser path guard can delete outside test dir.

Priority: `P0/P1`.

### A1. Add shared host validation helpers

Preferred target:

- `scripts/revalidation/a90harness/path_safety.py`

APIs:

```python
SAFE_COMPONENT_RE = re.compile(r"[A-Za-z0-9._-]+")
SAFE_ABSOLUTE_PATH_RE = re.compile(r"/[A-Za-z0-9._/-]+")

def require_safe_component(value: str, label: str) -> str
def normalize_device_path(path: str, label: str) -> str
def require_path_under(path: str, root: str, label: str) -> str
def require_run_child(root: str, run_id: str) -> str
def require_safe_raw_arg(value: str, label: str) -> str
```

Rules:

- reject empty values;
- reject `.`, `..`;
- reject `/` in a component;
- reject whitespace, control characters, newline, carriage return, `#`, quotes,
  backslash, semicolon, pipe, ampersand, dollar, backtick, angle brackets, NUL;
- normalize POSIX paths and reject paths that change meaning after normalization;
- path boundary is exact `root` or `root + "/"`, never a loose prefix.

Rationale:

- F038 and F041 have the same root cause; duplicating validators in each script
  invites drift.
- The helper lives under `a90harness` because it is host tooling safety, not
  device PID1 logic.

### A2. Patch `storage_iotest.py`

Hotspots:

- `scripts/revalidation/storage_iotest.py:131`
- `scripts/revalidation/storage_iotest.py:163`
- `scripts/revalidation/storage_iotest.py:247`
- `scripts/revalidation/storage_iotest.py:302`

Changes:

- Validate `args.test_root` with `normalize_device_path()` and strict allowed
  root policy.
- Validate `args.run_id` with `require_safe_component()`.
- Validate `args.toybox` as an absolute safe device path.
- Compute `device_run_root = require_run_child(args.test_root, args.run_id)`.
- Reject `clean` without a safe `run_id`; do not allow cleaning the test root.
- Validate all generated file/temp paths with `require_path_under()`.
- For non-streaming operations, keep using `device_command()` so `cmdv1x` can
  encode argv when possible.
- For the `BridgeRunThread` listener command, only interpolate values after
  `require_safe_raw_arg()` has accepted them.

Expected behavior after patch:

- `--run-id ok` works.
- `--run-id .` fails before any device command.
- `--run-id '..'` fails before any device command.
- `--run-id $'ok\nwritefile /cache/native-init-netservice 1\n#'` fails before
  any device command.
- `--test-root /mnt/sdext/a90/test-io-other` fails unless explicitly added as an
  allowed root.
- `clean` cannot remove `/mnt/sdext/a90/test-io` itself.

### A3. Patch `fs_exerciser_mini.py`

Hotspots:

- `scripts/revalidation/fs_exerciser_mini.py:113`
- `scripts/revalidation/fs_exerciser_mini.py:241`
- `scripts/revalidation/fs_exerciser_mini.py:331`

Changes:

- Use the same `a90harness.path_safety` helpers.
- Validate `args.test_root` as exactly `/mnt/sdext/a90/test-fsx` or a strict
  child only if intentionally allowed.
- Validate `args.run_id` as one safe component.
- Compute `args.run_root = require_run_child(args.test_root, args.run_id)`.
- Reject cleanup when `args.run_root == args.test_root`.
- Replace loose prefix checks with `require_path_under()`.
- Validate `args.toybox` as an absolute safe device path.

Expected behavior after patch:

- normal `--run-id v167-...` works.
- `--run-id .` fails before `mkdir` or `rm -rf`.
- `/mnt/sdext/a90/test-fsx-other` is no longer accepted as inside the root.

### A4. Batch A validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/a90harness/path_safety.py \
  scripts/revalidation/storage_iotest.py \
  scripts/revalidation/fs_exerciser_mini.py

git diff --check
```

Negative local argument checks:

```bash
python3 scripts/revalidation/storage_iotest.py --run-id . run --sizes 4096
python3 scripts/revalidation/storage_iotest.py --run-id '..' run --sizes 4096
python3 scripts/revalidation/storage_iotest.py --run-id $'ok\nwritefile /cache/native-init-netservice 1\n#' run --sizes 4096
python3 scripts/revalidation/fs_exerciser_mini.py --run-id .
python3 scripts/revalidation/fs_exerciser_mini.py --test-root /mnt/sdext/a90/test-fsx-other
```

Expected:

- each exits non-zero before contacting the serial bridge;
- no device-side command is sent.

Functional smoke:

- `storage_iotest.py` normal smoke can be run only when NCM is configured.
- `fs_exerciser_mini.py --ops 1 --keep-device-files` can be run only when bridge
  is intentionally available.

## Batch B: Unsafe Replay and Observer Memory

Findings:

- F040: Validator re-enables unsafe replay of root commands.
- F043: Unlimited observer retains samples until memory exhaustion.

Priority: `P1`.

### B1. Patch `cpu_mem_thermal_stability.py`

Hotspots:

- `scripts/revalidation/cpu_mem_thermal_stability.py:169`
- `scripts/revalidation/cpu_mem_thermal_stability.py:288`
- `scripts/revalidation/cpu_mem_thermal_stability.py:408`
- `scripts/revalidation/cpu_mem_thermal_stability.py:426`

Changes:

- Keep `run_cmd(... attempts=1)` as the default for mutating operations.
- Remove `retry_unsafe=True` from:
  - memory `dd`;
  - memory cleanup `rm`;
  - `longsoak start`;
  - `/bin/a90_cpustress`;
  - process snapshot `run toybox ps` unless it is explicitly treated as
    read-only and safe for retry.
- Optionally add helper names:

```python
run_readonly_cmd(...)
run_mutating_cmd(...)
```

The goal is to make unsafe retry opt-in structurally hard, not just manually
removed in a few call sites.

Expected behavior:

- bridge disconnect after command delivery produces a validator failure instead
  of command replay.
- read-only `status` samples may still retry through the default safe allowlist.

### B2. Patch `a90harness/observer.py`

Hotspots:

- `scripts/revalidation/a90harness/observer.py:103`
- `scripts/revalidation/a90harness/observer.py:113`
- `scripts/revalidation/a90harness/observer.py:116`
- `scripts/revalidation/a90harness/observer.py:140`

Changes:

- Remove `all_samples`.
- Maintain only:
  - `sample_count`;
  - `failure_count`;
  - bounded `recent_failures`, max 16 entries.
- Continue writing every sample to `observer.jsonl`.
- Summary uses counters, not list length.
- Heartbeat uses counters, not `sum()` over accumulated objects.

Expected behavior:

- `observe --duration-sec unlimited` has constant memory growth independent of
  cycle count, aside from Python runtime noise.

### B3. Batch B validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/cpu_mem_thermal_stability.py \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/observer.py

rg -n "retry_unsafe=True" scripts/revalidation/cpu_mem_thermal_stability.py
rg -n "all_samples" scripts/revalidation/a90harness/observer.py
git diff --check
```

Functional:

```bash
python3 scripts/revalidation/native_test_supervisor.py observe \
  --duration-sec unlimited \
  --max-cycles 2 \
  --interval 2
```

Expected:

- PASS;
- `observer-summary.json` still has cycles/samples/failures;
- `observer.jsonl` contains all samples.

## Batch C: NCM/TCP Evidence Correctness

Findings:

- F042: Reporter accepts unauthenticated tcpctl as PASS.
- F044: NCM/TCP preflight wrapper can never pass smoke mode.

Priority: `P1/P2`.

### C1. Patch `ncm_tcp_stability_report.py`

Hotspots:

- `scripts/revalidation/ncm_tcp_stability_report.py:129`

Changes:

- Add transcript auth checks:

```python
auth_required = "auth=required" in text
auth_none = "auth=none" in text
authenticated_flow = "OK authenticated" in text or "auth=required" in text
```

- Add checks:
  - `tcpctl auth required`: `auth_required is True`;
  - `tcpctl no no-auth marker`: `auth_none is False`;
  - `tcpctl authenticated flow`: true when command transcript contains auth
    evidence.
- A no-auth transcript with otherwise perfect ping/status/run counters must fail.

### C2. Patch `ncm_tcp_preflight.py`

Hotspots:

- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:66`
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py:74`

Changes:

- Replace `--- tcpctl-checks ---` with actual `tcpctl_host.py smoke` sections:
  - `--- ping ---`;
  - `--- version ---`;
  - `--- status ---`;
  - `--- shutdown ---`;
  - `--- serial-run ---`;
  - `[done] run`.
- Keep `pong` and shutdown evidence in `verify()`, but check actual strings:
  - `pong`;
  - `OK shutdown` or `shutdown`;
  - `[done] run`.

### C3. Batch C validation

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/ncm_tcp_stability_report.py \
  scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py

git diff --check
```

Fixture/negative:

- Create or reuse a small transcript with `auth=none`, `--- summary ---`,
  `failures: 0`, and passing counters.
- Run `ncm_tcp_stability_report.py` against it and expect FAIL.

Functional:

- With NCM configured, `native_test_supervisor.py run ncm-tcp-preflight --allow-ncm`
  should pass when `tcpctl_host.py smoke` passes.

## Batch D: NCM Resume Documentation Safety

Finding:

- F039: NCM resume docs bypass interface pinning.

Priority: `P2`.

### D1. Patch deferred report

Target:

- `docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md`

Changes:

- Replace recommended:

```bash
python3 scripts/revalidation/ncm_host_setup.py setup --allow-auto-interface
```

with:

```bash
python3 scripts/revalidation/ncm_host_setup.py setup --interface <known-usb-ncm-ifname>
```

- Add note:
  - `--allow-auto-interface` trusts device-reported MAC and is diagnostic-only.
  - Do not use it in evidence-producing runs unless the host interface has been
    independently verified.

### D2. Optional CLI help hardening

Target:

- `scripts/revalidation/ncm_host_setup.py`

Change:

- Strengthen `--allow-auto-interface` help text to state it may configure a
  sudo target from device-reported MAC and should not be used for normal resume.

### D3. Batch D validation

```bash
rg -n "setup --allow-auto-interface" \
  docs/reports/NATIVE_INIT_V166_NETWORK_THROUGHPUT_DEFERRED_2026-05-09.md

python3 -m py_compile scripts/revalidation/ncm_host_setup.py
git diff --check
```

Expected:

- no recommended resume command uses `--allow-auto-interface`;
- help text remains valid.

## Batch E: Local Security Rescan Coverage

Goal:

- Make `scripts/revalidation/local_security_rescan.py` recognize F038-F044 so
  future work does not regress these fixes silently.

Checks to add:

- F038/F041:
  - path safety helper exists;
  - `storage_iotest.py` and `fs_exerciser_mini.py` import/use it;
  - malicious run-id test snippets are rejected in local unit-style checks if
    practical.
- F040:
  - no mutating `cpu_mem_thermal_stability.py` command uses `retry_unsafe=True`.
- F043:
  - `a90harness/observer.py` no longer has `all_samples`.
- F042:
  - `ncm_tcp_stability_report.py` checks `auth=required` and rejects `auth=none`.
- F044:
  - `ncm_tcp_preflight.py` no longer checks `--- tcpctl-checks ---`.
- F039:
  - v166 deferred report no longer recommends `setup --allow-auto-interface`.

Validation:

```bash
python3 scripts/revalidation/local_security_rescan.py \
  --out docs/security/scans/SECURITY_FRESH_SCAN_V178_PREP_2026-05-09.md
```

Expected:

- `FAIL=0`;
- F038-F044 families present in the scan output.

## Commit Plan

Recommended commits:

1. `Document F038 F044 patch plan`
   - documentation only.
2. `Harden storage and fs exerciser paths`
   - Batch A.
3. `Fix validator replay and observer accounting`
   - Batch B.
4. `Fix NCM TCP evidence checks`
   - Batch C and D, or split D if desired.
5. `Extend local security rescan for F038 F044`
   - Batch E.

Do not mix these fixes with v179 mixed-soak scheduler implementation. The
security fixes should land first so later long-run results are trustworthy.

## Acceptance Before Resuming v178-v184

- F038-F044 files have local remediation updated from `planned` to actual commit
  references.
- Local targeted security rescan covers the new families.
- `git diff --check` and Python `py_compile` pass.
- Existing normal smoke behavior still works for safe inputs.
- No fresh Codex Cloud finding remains open in the host validation trust-boundary
  category, or it is explicitly accepted with a documented reason.
