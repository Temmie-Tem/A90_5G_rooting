# v178 Plan: Post-Security Harness Baseline

Date: `2026-05-09`
Baseline native init: `A90 Linux init 0.9.59 (v159)`
Baseline host patches:

- `0b8e9bc` — storage/fs path safety hardening
- `c214478` — unsafe replay removal and bounded observer accounting
- `952e572` — authenticated NCM/tcpctl evidence checks
- `fafa6d6` — F038-F044 local security rescan coverage

## Summary

v178 is no longer a pure mixed-soak scheduler planning step. F038-F044 showed
that several v160-v177 host validators had security and evidence-correctness
defects. Therefore v178 becomes the **post-security harness baseline**.

The goal is to prove the patched host harness is trustworthy enough to produce
new mixed-soak evidence. Only after v178 passes should v179 start implementing
the mixed-soak scheduler.

## Why This Is Needed

The device-side native init baseline remains `v159`, but the host-side evidence
chain changed materially:

- path guards now reject unsafe run ids, sibling-prefix roots, and raw command
  injection before device contact;
- mutating root commands are no longer retried through unsafe replay paths;
- unlimited observer mode now streams counters and bounded recent failures
  instead of retaining every sample in memory;
- NCM/TCP reports now require authenticated `tcpctl` transcript evidence;
- NCM resume docs now prefer explicit host interface pinning.

This means old v160-v177 reports are still useful as historical development
evidence, but they should not be treated as final server-readiness evidence.
Post-security runs must regenerate the key host/device stability evidence.

## Scope

No native init source, boot image, Wi-Fi, rfkill, kernel module, firmware,
watchdog, or partition behavior changes in v178.

v178 only validates and documents the patched host harness:

1. local security rescan for F001-F044 pattern families;
2. negative input checks for storage/fs path safety;
3. unauthenticated tcpctl transcript rejection;
4. short real-device observer smoke;
5. short real-device CPU/memory/storage/NCM smoke where the environment is
   available;
6. evidence classification for any unavailable NCM/USB/SD prerequisite.

## Required Validation

### Static / Host-Only

```bash
python3 -m py_compile \
  scripts/revalidation/a90harness/path_safety.py \
  scripts/revalidation/storage_iotest.py \
  scripts/revalidation/fs_exerciser_mini.py \
  scripts/revalidation/cpu_mem_thermal_stability.py \
  scripts/revalidation/a90harness/observer.py \
  scripts/revalidation/ncm_tcp_stability_report.py \
  scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py \
  scripts/revalidation/ncm_host_setup.py \
  scripts/revalidation/local_security_rescan.py

python3 scripts/revalidation/local_security_rescan.py \
  --out docs/security/SECURITY_FRESH_SCAN_F038_F044_2026-05-09.md

git diff --check
```

Expected:

- local scan has `FAIL=0`;
- the only accepted warning remains USB ACM/local serial root-control lab
  boundary;
- no new generated output path permission regression.

### Negative Safety Checks

These checks must fail before any device command is sent:

```bash
python3 scripts/revalidation/storage_iotest.py --run-id . run --sizes 4096
python3 scripts/revalidation/storage_iotest.py --run-id '..' run --sizes 4096
python3 scripts/revalidation/storage_iotest.py --run-id $'ok\nwritefile /cache/native-init-netservice 1\n#' run --sizes 4096
python3 scripts/revalidation/fs_exerciser_mini.py --run-id .
python3 scripts/revalidation/fs_exerciser_mini.py --test-root /mnt/sdext/a90/test-fsx-other
```

Unauthenticated NCM/TCP transcript fixture must fail:

```bash
python3 scripts/revalidation/ncm_tcp_stability_report.py \
  --tcpctl-soak <no-auth-fixture> \
  --out-md tmp/security/noauth-report.md \
  --out-json tmp/security/noauth-report.json
```

Expected:

- report exits non-zero;
- report contains failed checks for missing `auth=required` and/or `auth=none`
  presence.

### Real-Device Smoke

Run with bridge available:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py selftest verbose

python3 scripts/revalidation/native_test_supervisor.py observe \
  --duration-sec unlimited \
  --max-cycles 2 \
  --interval 2 \
  --run-dir tmp/soak/harness/v178-post-security-observe
```

Optional if SD/NCM are currently configured:

```bash
python3 scripts/revalidation/fs_exerciser_mini.py \
  --run-id v178-fsx-smoke \
  --ops 16 \
  --out-dir tmp/soak/fs-exerciser

python3 scripts/revalidation/storage_iotest.py \
  --run-id v178-storage-smoke \
  run \
  --sizes 4096,65536 \
  --out-md tmp/soak/storage-iotest-v178.md \
  --out-json tmp/soak/storage-iotest-v178.json

python3 scripts/revalidation/native_test_supervisor.py run ncm-tcp-preflight \
  --allow-ncm \
  --run-dir tmp/soak/harness/v178-ncm-preflight
```

If SD or NCM is not available, record `SKIP/DEFERRED` with the reason instead of
forcing a failing environment-dependent result.

## Acceptance

v178 passes when:

- F038-F044 local rescan remains `FAIL=0`;
- safety negative checks fail before device contact;
- observer smoke records bounded counters, valid heartbeat, and no failures;
- authenticated NCM/TCP evidence check is enforced;
- any unavailable SD/NCM prerequisite is recorded as `SKIP/DEFERRED`, not hidden;
- task queue and next-work docs point to v179 scheduler foundation only after
  v178 baseline evidence exists.

## Impact On v179-v184

v179-v184 remain the mixed-soak/serverization gate cycle, but their input
evidence must be post-v178:

- v179: implement mixed-soak scheduler foundation;
- v180: CPU/memory workload profiles;
- v181: NCM/TCP + storage workload integration using patched validators;
- v182: failure classifier and recovery policy;
- v183: 8h pilot mixed soak;
- v184: 24h+ serverization readiness gate.

Any pre-v178 v160-v177 evidence should be referenced as historical baseline
only, not as final readiness proof.
