# A90 v181 NCM/TCP + Storage Full Mixed Soak Report

Date: `2026-05-09`
Cycle label: `v181` host harness, not a native-init boot image
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Git commit under test: `c2ee250`

## Summary

v181 full NCM/TCP + storage mixed-soak validation passed after host NCM was
configured through NetworkManager on the explicit USB/NCM interface.

This closes the previous v181 blocker. The next gate is v183 8h pilot mixed-soak.

## Setup

- Device NCM: `ncm0`
- Device IP: `192.168.7.2/24`
- Host IP: `192.168.7.1/24`
- Host NCM setup: explicit USB/NCM interface, not `--allow-auto-interface`
- Host ping: `3/3` PASS
- TCP helper path used by harness: `/cache/bin/a90_tcpctl`
- TCP helper install hash:
  `4fa39e9fca2e5c221d757bd2e09f0930f31864f41ae1daf79271dd5ccb41c764`

`/bin/a90_tcpctl` was absent on this v159 boot image, so the v181 harness was
patched to prefer `/bin/a90_tcpctl` but fall back to verified `/cache/bin/a90_tcpctl`.

## Command

```bash
RUN_DIR=tmp/soak/harness/v181-ncm-full-20260509-052830
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 3600 \
  --observer-interval 15 \
  --seed 181 \
  --allow-ncm \
  --workload-profile quick \
  --run-dir "$RUN_DIR"
```

## Result

- result: PASS
- run_dir: `tmp/soak/harness/v181-ncm-full-20260509-052830/`
- duration: `2434.220617544008s`
- workloads: `3`
- pass: `3`
- skipped: `0`
- blocked: `0`
- failed: `0`
- observer failures: `0`
- observer cycles: `135`
- observer samples: `945`
- stop reason: `complete`
- failure classifications: `0`

The run ended earlier than the requested 3600 seconds because the current
mixed-soak scheduler executes the planned workloads at `0s`, `1200s`, and
`2400s`, then finalizes after the last scheduled workload. This is acceptable
for v181 integration validation because all required workloads ran and passed.
The v183/v184 plans still require effective 8h/24h runtime gates.

## Workloads

### `ncm-tcp-preflight`

- status: PASS
- detail: `host NCM ping ok; tcpctl=/cache/bin/a90_tcpctl`
- tcpctl smoke: ping/version/status/run/shutdown PASS
- auth: `auth=required`, `OK authenticated`
- serial bridge returned after tcpctl shutdown

### `cpu-memory-profiles`

- status: PASS
- profiles: `4`
- max CPU usage: `38%`
- memory mismatch: `0`

### `storage-io`

- status: PASS
- files: `3`
- sizes: `4096`, `65536`, `1048576`
- write/read/hash/sync: PASS
- cleanup: PASS

## Final Device Checks

- `selftest verbose`: `pass=11 warn=1 fail=0`
- `storage`: SD backend, mounted, expected, `rw=yes`
- `netservice status`: `ncm0=present`, `tcpctl=stopped`
- `longsoak status verbose`: `health=ok`, `running=yes`
- host ping to `192.168.7.2`: `3/3` PASS

Known warning:

- `selftest helpers`: `WARN`, manifest missing. This is pre-existing and does
  not block v181.
- `netservice helpers tcpctl=no` still reflects native netservice helper status,
  while the harness explicitly used verified `/cache/bin/a90_tcpctl`.

## Acceptance Mapping

| Requirement | Evidence | Result |
| --- | --- | --- |
| `--allow-ncm` full mixed workload runs | `mixed-soak-result.json` | PASS |
| NCM/TCP workload passes | `ncm-tcp-preflight` event | PASS |
| CPU/memory workload passes | `cpu-memory-profiles` event | PASS |
| Storage workload passes | `storage-io` event | PASS |
| Observer remains healthy | `observer_failures=0` | PASS |
| Failure classifier has no failures | `failure-classification.json` empty | PASS |
| Final SD state is stable | `storage rw=yes` | PASS |
| Final NCM ping works | `ping 3/3` | PASS |

## Next

- v183 8h pilot mixed-soak can start.
- v184 24h+ readiness remains gated on v183 PASS or explicit accepted WARN-only
  outcome.
