# A90 v181 NCM/TCP + Storage Workload Integration Preflight Report

Date: `2026-05-09`
Device build under test: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v181` host harness, not a native-init boot image
Plan: `docs/plans/NATIVE_INIT_V181_NCM_TCP_STORAGE_INTEGRATION_PLAN_2026-05-09.md`
Roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

Result: `PARTIAL / BLOCKED BY HOST NCM SETUP`

v181 preflight safety work is implemented and validated. Full NCM/TCP + storage
validation is not complete because host NCM is currently not configured and sudo
is not available non-interactively in this session.

## Implementation

- Added `DeviceClient.exclusive()` to reserve the serial bridge for external
  tools.
- Added `external_bridge_client` metadata to module definitions.
- Marked `ncm-tcp-preflight` and `storage-io` as external bridge clients.
- Added `external-bridge` resource lock in `a90harness/scheduler.py`.
- Scheduler now wraps external bridge workloads in `client.exclusive()` so the
  observer blocks on the same serial lock instead of racing independent bridge
  users.

## Validation

Static:

- Python compile: `PASS`
- `git diff --check`: `PASS`

Dry-run with NCM gate allowed:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --dry-run \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 181 \
  --allow-ncm \
  --run-dir tmp/soak/harness/v181-dry-run-20260509-045719
```

Result:

- `PASS dry-run`
- schedule includes `external-bridge` for `ncm-tcp-preflight`
- schedule includes `external-bridge` and `storage` for `storage-io`
- evidence: `tmp/soak/harness/v181-dry-run-20260509-045719/`

ACM-only smoke:

```bash
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 30 \
  --observer-interval 5 \
  --seed 181 \
  --run-dir tmp/soak/harness/v181-acm-only-smoke-20260509-045729
```

Result:

- `PASS`
- workload pass: `1`
- structured blocked/skipped: `2`
- observer failures: `0`
- evidence: `tmp/soak/harness/v181-acm-only-smoke-20260509-045729/`

## Blocker

Current live state:

- `netservice: enabled=no`
- `ncm0=absent`
- `ping 192.168.7.2`: `100% packet loss`
- `sudo -n true`: interactive authentication required

Full v181 acceptance requires the operator to configure host NCM first:

```bash
python3 scripts/revalidation/ncm_host_setup.py setup --allow-auto-interface
ping -c 3 -W 2 192.168.7.2
```

After ping succeeds, run the full v181 mixed workload with `--allow-ncm`.

## Result

v181 safety integration is ready, but v181 is not complete. The next action is
operator-assisted NCM setup followed by the full NCM/TCP + storage mixed run.
