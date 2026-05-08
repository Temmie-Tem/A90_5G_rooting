# A90 v184 24h+ Serverization Readiness Gate Plan

Date: `2026-05-09`
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Cycle label: `v184` host harness, not a native-init boot image
Parent roadmap: `docs/plans/NATIVE_INIT_V178_V184_MIXED_SOAK_SECURITY_ROADMAP_2026-05-09.md`

## Summary

v184 is the final pre-Wi-Fi/serverization readiness gate for the current cycle.
It is not a feature release and does not produce a new boot image. It runs a
24 hour or longer mixed-soak test on the v159 device using the post-security
host harness.

The output is an explicit `GO`, `WARN-GO`, or `NO-GO` recommendation for the next
Wi-Fi baseline refresh and later server-style network exposure work.

## Preconditions

v184 must not start until these are true:

- v181 full NCM/TCP + storage run has PASS evidence.
- v183 8h pilot has PASS evidence, or a documented WARN-only result explicitly
  accepted by the operator.
- Bridge responds to `cmdv1 version`.
- Device version is `A90 Linux init 0.9.59 (v159)`.
- `selftest verbose` has `FAIL=0`.
- SD storage reports expected UUID, mounted, and `rw=yes`.
- Host NCM ping to `192.168.7.2` succeeds.
- `tcpctl_host.py ping/status/run` succeeds before the run.
- Host suspend and USB autosuspend are disabled or explicitly accounted for.

## Recommended Host Prep

```bash
cat /sys/module/usbcore/parameters/autosuspend
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend

ip -br link | grep enx
python3 scripts/revalidation/ncm_host_setup.py setup \
  --interface <known-usb-ncm-ifname> \
  --manual-host-config \
  --sudo "sudo -n"
ping -c 3 -W 2 192.168.7.2

python3 scripts/revalidation/a90ctl.py version
python3 scripts/revalidation/a90ctl.py selftest verbose
python3 scripts/revalidation/a90ctl.py storage
python3 scripts/revalidation/a90ctl.py 'netservice status'
```

## Run Command

Primary 24 hour run:

```bash
RUN_DIR=tmp/soak/harness/v184-24h-readiness-$(date +%Y%m%d-%H%M%S)
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 86400 \
  --observer-interval 30 \
  --profile balanced \
  --workload-profile quick \
  --seed 184 \
  --allow-ncm \
  --workload ncm-tcp-preflight \
  --workload storage-io \
  --workload cpu-memory-profiles \
  --run-dir "$RUN_DIR"
```

Optional unlimited run:

```bash
RUN_DIR=tmp/soak/harness/v184-unlimited-readiness-$(date +%Y%m%d-%H%M%S)
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 315360000 \
  --observer-interval 30 \
  --profile balanced \
  --workload-profile quick \
  --seed 184 \
  --allow-ncm \
  --workload ncm-tcp-preflight \
  --workload storage-io \
  --workload cpu-memory-profiles \
  --run-dir "$RUN_DIR"
```

For unlimited mode, operator interrupt is acceptable only after at least 24 hours
if the partial bundle is valid and the interruption is classified as
`operator-interrupt`.

## Workload and Observer Requirements

- Observer remains read-only and records device status, storage, longsoak,
  netservice, selftest, and heartbeat state.
- NCM/TCP workload confirms host ping and tcpctl command path.
- Storage workload performs bounded SD write/read/hash/sync validation.
- CPU/memory workload uses bounded profiles only; no OOM or destructive pressure.
- USB rebind/recovery workloads are excluded from the default v184 gate.
- Wi-Fi, rfkill writes, module load/unload, watchdog open, reboot loops, public
  listener widening, and destructive partition writes remain out of scope.

## Evidence Requirements

The run directory must include:

- `manifest.json`
- `schedule.json`
- `observer.jsonl`
- `observer-summary.json`
- `workload-events.jsonl`
- `failure-classification.json`
- `mixed-soak-result.json`
- `heartbeat.json`
- `summary.md`
- child module reports copied with private/no-follow handling

The final report must additionally record:

- git commit
- exact command
- host NCM interface name and IP
- device version
- run start/end time
- elapsed duration
- observer sample count and maximum sample gap
- workload pass/fail/skip counts
- CPU/GPU thermal trend
- battery/charging/power trend
- memory used range
- storage final state and log path stability
- NCM/TCP final state
- serial bridge final state
- all warnings and whether each warning blocks Wi-Fi/serverization

## GO / WARN-GO / NO-GO Criteria

### GO

- 24h+ completed.
- `mixed-soak-result.json` is PASS.
- No unclassified failures.
- No storage mismatch.
- No repeated bridge disconnect.
- No unexplained NCM/TCP failure.
- No thermal runaway.
- Final `selftest verbose`, `storage`, `netservice status`, and
  `longsoak status verbose` are acceptable.
- USB ACM rescue bridge remains available.
- Security posture still defaults to USB-local / disabled network exposure.

### WARN-GO

Allowed only when every warning is understood, bounded, and documented. Examples:

- one operator-caused interrupt after 24h with complete partial bundle
- transient host-side sleep/network disturbance with device observer continuity
- isolated workload skip caused by an explicitly documented lab environment issue

WARN-GO requires explicit operator approval before Wi-Fi baseline refresh.

### NO-GO

Any of these blocks serverization:

- less than 24h effective runtime without explicit operator override
- unclassified failure
- storage hash mismatch or SD/log path instability
- repeated or unrecovered bridge loss
- repeated or unrecovered NCM/TCP loss
- selftest `FAIL>0`
- uncontrolled zombie/process leak evidence
- thermal runaway or power trend that cannot be explained
- security scan reports an open high-risk listener/auth/path finding

## Report

On completion, write:

`docs/reports/NATIVE_INIT_V184_24H_SERVERIZATION_READINESS_2026-05-09.md`

The report must end with one of:

- `Recommendation: GO`
- `Recommendation: WARN-GO`
- `Recommendation: NO-GO`

## Assumptions

- v184 validates the current v159 native-init build and host harness stack.
- It does not unblock public network exposure by itself; it only permits the next
  read-only Wi-Fi baseline refresh if the recommendation is GO or approved WARN-GO.
- v184 should be rerun after any major native-init, storage, network, or security
  policy change before treating the device as server-like.
