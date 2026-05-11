# A90 v184 24h Serverization Readiness Report

Date: `2026-05-11`
Cycle label: `v184` host harness, not a native-init boot image
Native build: `A90 Linux init 0.9.59`
Device build tag: `v159`
Device flash: none
Host commit under test: `8a36b6a`

## Summary

v184 24h+ serverization readiness gate passed.

The run kept the ACM serial observer active while scheduling CPU/memory,
USB NCM/TCP, and SD storage I/O workloads across a 24h window. The observer
recorded no failures, all workloads passed, and the failure classifier produced
no findings.

This closes the v178-v184 mixed-soak/serverization gate cycle.

## Setup

- Run dir: `tmp/soak/harness/v184-24h-readiness-20260510-095036/`
- Serial bridge: `127.0.0.1:54321` to `/dev/ttyACM0`
- Device NCM: `ncm0`
- Device IP: `192.168.7.2/24`
- Host NCM: `192.168.7.1/24`
- TCP helper path used by harness: `/cache/bin/a90_tcpctl`
- Native longsoak: running during and after the readiness gate

This was a host-harness validation cycle. It did not flash a new boot image.

## Command

```bash
RUN_DIR=tmp/soak/harness/v184-24h-readiness-20260510-095036
python3 scripts/revalidation/native_test_supervisor.py mixed-soak \
  --duration-sec 86400 \
  --observer-interval 30 \
  --profile balanced \
  --workload-profile quick \
  --seed 184 \
  --allow-ncm \
  --stop-on-failure \
  --workload ncm-tcp-preflight \
  --workload storage-io \
  --workload cpu-memory-profiles \
  --run-dir "$RUN_DIR"
```

## Result

- result: PASS
- duration: `86400.95598973002s`
- workloads: `3`
- pass: `3`
- skipped: `0`
- blocked: `0`
- failed: `0`
- interrupted: `false`
- stop reason: `complete`
- observer cycles: `2626`
- observer samples: `18382`
- observer failures: `0`
- observer stop reason: `duration`
- failure classifications: `0`

Canonical result artifact:

- `tmp/soak/harness/v184-24h-readiness-20260510-095036/mixed-soak-result.json`

## Workloads

### `cpu-memory-profiles`

- status: PASS
- scheduled window: `0s` to `28800s`
- actual duration: `26.17736444598995s`
- profiles: `4`
- max CPU usage: `38%`
- memory mismatch: `0`

### `ncm-tcp-preflight`

- status: PASS
- scheduled window: `28800s` to `57600s`
- actual duration: `4.4745358530199155s`
- host NCM ping: PASS
- tcpctl path: `/cache/bin/a90_tcpctl`
- tcp ping/version/status/run/shutdown: PASS
- auth: `auth=required`, authenticated command path PASS
- serial bridge returned after tcpctl shutdown

### `storage-io`

- status: PASS
- scheduled window: `57600s` to `86400s`
- actual duration: `31.56419815000845s`
- host NCM ping: PASS
- files: `3`
- sizes: `4096`, `65536`, `1048576`
- write/read/hash/sync: PASS
- cleanup: PASS

## Final Device State

Final observer status remained healthy:

- `selftest`: `pass=11 warn=1 fail=0`
- `pid1guard`: `pass=10 warn=1 fail=0`
- `exposure`: `guard=ok warn=0 fail=0 ncm=present tcpctl=stopped rshell=stopped boundary=usb-local`
- `longsoak`: `health=ok`, running, session `v159-108319`
- `runtime`: `backend=sd root=/mnt/sdext/a90 fallback=no writable=yes`
- `uptime`: `125711.56s`
- `battery`: `100% Full temp=31.8C`
- `power`: `now=0.4W avg=0.4W`
- `thermal`: `cpu=39.9C gpu=38.1C`
- `memory`: `275/5375MB used`
- `netservice`: disabled, `tcpctl=stopped`
- `storage`: SD backend, mounted, expected, `rw=yes`
- `mountsd`: size `59968MB`, available `56851MB`

Known warning:

- `selftest helpers`: `WARN`, manifest missing. This is pre-existing and does
  not block v184.

## Artifact Hashes

```text
eccba48ea389f838d5e234f9576b5a5aafbd9f629017ad8fb3577e7a9146fa13  mixed-soak-result.json
530e881d685b9c901e34bcb2de395cdfe8cd7f421f9d99da399d4a3c06b31ba0  observer-summary.json
5afee4464690f34566e1b392406f16e218e81ec74a5869303812cef41b68b903  workload-events.jsonl
1d9068efe6b9a54defa64eea6faa7699794b0fe5ef1a53a4c85bbc6f9e43b784  summary.md
25ebf45368a4313ccb17fb32e76b69bb4f777bffb87452550ae2def7b96ff700  failure-classification.json
```

## Readiness Decision

Decision: `GO`

Rationale:

- 24h+ wall-clock gate completed.
- All scheduled workloads passed.
- Observer failures remained `0`.
- Failure classifier produced no findings.
- SD runtime remained mounted, expected, and writable.
- NCM/TCP remained usable under the explicit USB-local boundary.
- ACM serial control remained usable.
- Final device health was stable.

## Next

The next work should not immediately widen network exposure. Recommended order:

1. Keep the versioning policy as the default for future plans/reports.
2. Decide the post-v184 roadmap.
3. Prioritize communication protocol/broker design, security scan patch loop,
   kernel diagnostic facilities, and contention stress tests before Wi-Fi bring-up.
