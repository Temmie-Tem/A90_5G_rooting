# A90 v183 8h Pilot Mixed Soak Plan

Date: `2026-05-09`
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v183` host harness, not a native-init boot image
Parent roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

v183 is the first real-duration pilot for the post-security mixed-soak harness.
It does not add a new native-init image. It runs the v179-v182 host harness stack
against the v159 device for an 8 hour balanced workload.

The run remains gated on v181 full NCM/TCP + storage readiness. If host NCM is not
configured, v183 must not be marked PASS. It may only produce a deferred bundle
with `env-ncm-missing` classification.

## Preconditions

- Bridge responds to `cmdv1 version`.
- Device version is `A90 Linux init 0.9.59 (v159)`.
- `storage` reports SD backend, mounted, expected, and `rw=yes`.
- `selftest verbose` reports `FAIL=0`.
- `longsoak status verbose` is healthy or can be restarted intentionally.
- Host NCM path is configured:

```bash
ip -br link | grep enx
python3 scripts/revalidation/ncm_host_setup.py setup \
  --interface <known-usb-ncm-ifname> \
  --manual-host-config \
  --sudo "sudo -n"
ping -c 3 -W 2 192.168.7.2
```

Expected NCM state:

- device `netservice status`: `ncm0=present` or equivalent running state
- host ping to `192.168.7.2`: `3/3` success
- `tcpctl_host.py ping/status/run`: PASS

## Run Command

Primary v183 run:

```bash
RUN_DIR=tmp/soak/harness/v183-8h-pilot-$(date +%Y%m%d-%H%M%S)
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 28800 \
  --observer-interval 30 \
  --profile balanced \
  --workload-profile quick \
  --seed 183 \
  --allow-ncm \
  --workload ncm-tcp-preflight \
  --workload storage-io \
  --workload cpu-memory-profiles \
  --run-dir "$RUN_DIR"
```

If the operator cannot keep the host awake for 8 hours, the run is invalid for
v183 PASS. Shorter runs are smoke evidence only and should be recorded as
deferred/pilot-prep.

## Workload Mix

- `ncm-tcp-preflight`: host/device TCP control path, host ping, tcpctl status/run.
- `storage-io`: bounded SD write/read/hash/sync validation.
- `cpu-memory-profiles`: low/medium/spike/cooldown CPU and bounded memory checks.
- observer: read-only `status`, `bootstatus`, `storage`, `longsoak`, `netservice`,
  and `selftest` samples.

USB rebind/recovery workloads are excluded from the default v183 run. They remain
separate recovery validation, not part of the first 8 hour serverization pilot.

## Failure Policy

The run must keep evidence even when interrupted or failed.

- `operator-interrupt`: acceptable only for an explicitly aborted run; not PASS.
- `env-ncm-missing`: deferred, not PASS.
- `policy-blocked`: harness configuration issue unless intentional negative test.
- `bridge-timeout` or `bridge-disconnect`: FAIL unless recovered and classified
  with enough evidence to explain the gap.
- `storage-mismatch`: FAIL.
- `device-command-failed`: FAIL unless it is a known safe skip.
- thermal runaway or repeated power anomalies: FAIL/WARN based on severity and
  whether cooldown recovered.

## Evidence Requirements

The v183 bundle must include:

- `manifest.json`
- `schedule.json`
- `observer.jsonl`
- `observer-summary.json`
- `workload-events.jsonl`
- `failure-classification.json`
- `mixed-soak-result.json`
- `heartbeat.json`
- `summary.md`
- final command captures or transcript references for:
  - `version`
  - `status`
  - `bootstatus`
  - `selftest verbose`
  - `storage`
  - `mountsd status`
  - `longsoak status verbose`
  - `netservice status`

Evidence files must be private/no-follow outputs, following the existing
`EvidenceStore` policy.

## Acceptance

v183 PASS requires all of the following:

- 8 hours elapsed or intentionally configured `28800` second run completed.
- `mixed-soak-result.json` reports PASS.
- `failure-classification.json` has no unclassified failures.
- Observer samples remain monotonic and have no unexplained long gap.
- NCM/TCP workload completes without unclassified failures.
- SD storage workload completes with zero hash/mismatch errors.
- CPU/memory profiles complete and cooldown returns to normal operating range.
- Final device checks pass:
  - `selftest verbose`: `FAIL=0`
  - `storage`: SD backend mounted and `rw=yes`
  - `netservice status`: expected NCM/TCP state
  - `longsoak status verbose`: health ok
- USB ACM rescue bridge remains available after the run.

## Report

On success, write:

`docs/reports/NATIVE_INIT_V183_8H_PILOT_MIXED_SOAK_2026-05-09.md`

The report must include:

- run directory
- exact command
- git commit
- start/end time
- duration
- host NCM interface and ping result
- summary of workload pass/fail counts
- thermal/battery/power trend summary
- storage and NCM final state
- any warnings and whether they block v184

## Assumptions

- v183 is a validation gate, not a firmware version.
- v159 remains the native-init build under test.
- v181 full NCM/TCP + storage must be unblocked before v183 can be PASS.
- v184 24h+ readiness should not start until v183 PASS or an explicit operator
  decision accepts a documented WARN-only v183 result.
