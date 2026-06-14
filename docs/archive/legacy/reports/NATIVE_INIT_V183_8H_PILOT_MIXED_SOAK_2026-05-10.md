# A90 v183 8h Pilot Mixed Soak Report

Date: `2026-05-10`
Cycle label: `v183` host harness, not a native-init boot image
Baseline device build: `A90 Linux init 0.9.59 (v159)`
Git commit under test: `fa6c1da`

## Summary

v183 8h pilot mixed-soak validation passed.

This is the first full-duration mixed-soak gate after the post-security harness
baseline. It validates that the host harness can keep the serial observer alive
while running SD storage I/O, CPU/memory profiles, and USB NCM/TCP control checks
over an 8h window.

This closes the v183 gate. The next gate is v184 24h+ serverization readiness.

## Setup

- Run dir: `tmp/soak/harness/v183-8h-pilot-20260509-230134/`
- Serial bridge: `127.0.0.1:54321` to `/dev/ttyACM0`
- Device NCM: `ncm0`
- Device IP: `192.168.7.2/24`
- Host NCM interface: `enxa63ce1dd2035`
- Host IP: `192.168.7.1/24`
- Host NCM ping: `3/3` PASS
- TCP helper path used by harness: `/cache/bin/a90_tcpctl`
- Native longsoak: running during and after the pilot

`/bin/a90_tcpctl` is still absent on this v159 boot image, so the harness used
the verified `/cache/bin/a90_tcpctl` fallback.

## Command

```bash
RUN_DIR=tmp/soak/harness/v183-8h-pilot-20260509-230134
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 28800 \
  --observer-interval 30 \
  --profile balanced \
  --workload-profile quick \
  --seed 183 \
  --allow-ncm \
  --stop-on-failure \
  --workload ncm-tcp-preflight \
  --workload storage-io \
  --workload cpu-memory-profiles \
  --run-dir "$RUN_DIR"
```

## Result

- result: PASS
- duration: `28800.03940728301s`
- workloads: `3`
- pass: `3`
- skipped: `0`
- blocked: `0`
- failed: `0`
- interrupted: `false`
- stop reason: `complete`
- observer cycles: `876`
- observer samples: `6132`
- observer failures: `0`
- observer stop reason: `stop-event`
- failure classifications: `0`

Canonical result artifact:

- `tmp/soak/harness/v183-8h-pilot-20260509-230134/mixed-soak-result.json`

The older generic `result.json` filename is not used for this mixed-soak output;
`mixed-soak-result.json` is the canonical result artifact for v179+ mixed-soak
runs.

## Workloads

### `storage-io`

- status: PASS
- scheduled window: `0s` to `9600s`
- actual duration: `31.36329594400013s`
- host NCM ping: PASS
- files: `3`
- sizes: `4096`, `65536`, `1048576`
- write/read/hash/sync: PASS
- cleanup: PASS

This confirms the earlier v183 storage failure was fixed. The failed pre-report
attempt had fallen back from cmdv1 to raw bridge and timed out on
`mkdir /mnt/sdext/a90/test-io`; the passing run used the hardened cmdv1 storage
path.

### `cpu-memory-profiles`

- status: PASS
- scheduled window: `9600s` to `19200s`
- actual duration: `23.659533864993136s`
- profiles: `4`
- max CPU usage: `38%`
- memory mismatch: `0`
- cleanup: PASS

### `ncm-tcp-preflight`

- status: PASS
- scheduled window: `19200s` to `28800s`
- actual duration: `4.754778808011906s`
- host NCM ping: PASS
- tcpctl path: `/cache/bin/a90_tcpctl`
- tcp ping/version/status/run/shutdown: PASS
- auth: `auth=required`, `OK authenticated`
- serial bridge returned after tcpctl shutdown

## Final Device Checks

Post-run `status` over the ACM bridge remained healthy:

- `selftest`: `pass=11 warn=1 fail=0`
- `pid1guard`: `pass=10 warn=1 fail=0`
- `runtime`: `backend=sd root=/mnt/sdext/a90 fallback=no writable=yes`
- `storage`: SD backend, mounted, expected, `rw=yes`
- `mountsd`: size `59968MB`, available `56855MB`
- `longsoak`: `health=ok`, running, session `v159-108319`
- `netservice`: disabled, `ncm0=present`, `tcpctl=stopped`
- `rshell`: stopped
- `adbd`: stopped
- uptime at post-run check: `38182.04s`
- battery: `100% Full`
- CPU temperature: `39.8C`
- GPU temperature: `38.2C`
- memory: `266/5375MB used`

Known warnings:

- `selftest helpers`: `WARN`, manifest missing. This is pre-existing and does
  not block v183.
- `netservice helpers tcpctl=no` reflects native netservice helper status; the
  harness explicitly used the verified `/cache/bin/a90_tcpctl` fallback.

## Artifact Hashes

```text
c891b6c9ce4b0501b6c3f0281db00b6d9b12cd26b147b4d08901745e1da0ecac  mixed-soak-result.json
28923a13213c0b90da7690ee926931f5aa81f7a8974d1c97cca74c920f3f75e8  observer-summary.json
fa24862b3700bbc196988bb6ba5ef26acaa73765a8707453450eb13a2912fe77  workload-events.jsonl
2462ca27fc6514d90de9fb820598921fd4ab50ed0e9720e0aa8c31950c5f39c0  summary.md
```

## Acceptance Mapping

| Requirement | Evidence | Result |
| --- | --- | --- |
| 8h wall-clock gate completes | `duration_sec=28800.03940728301` | PASS |
| All scheduled workloads pass | `pass_count=3 fail_count=0` | PASS |
| Observer stays healthy | `observer.failures=0` | PASS |
| Failure classifier has no findings | `classification_summary.count=0` | PASS |
| SD storage remains stable | `storage-io`, final `storage rw=yes` | PASS |
| CPU/memory profiles pass | `cpu-memory-profiles` event | PASS |
| NCM/TCP path passes | `ncm-tcp-preflight` event | PASS |
| ACM rescue/control remains available | post-run `status` command | PASS |

## Next

- v184 24h+ serverization readiness can start.
- Keep v184 on the same guardrails: ACM rescue active, NCM explicit opt-in,
  private evidence bundle, `--stop-on-failure`, no Wi-Fi/public listener changes.
