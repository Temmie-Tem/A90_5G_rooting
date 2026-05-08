# Native Init v164 Scheduler/Latency Baseline Plan (2026-05-09)

## Summary

- target label: `v164 Scheduler/Latency Baseline`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 native init 환경에서 bounded wakeup/run-loop latency 기준선을 만든다.
- 현재 host NCM helper deploy path는 sudo/host interface 설정에 영향을 받으므로, v164는 새 device binary 없이 `toybox usleep` + PID1 `run`/cmdv1 duration을 latency proxy로 사용한다.
- true `clock_nanosleep` cyclictest-style helper는 binary deploy path가 안정화된 뒤 v170+에서 재검토한다.

## Scope

- `scripts/revalidation/scheduler_latency_baseline.py` 추가.
- profile별로 `run /cache/bin/toybox usleep <sleep_us>`를 반복하고 `A90P1 END duration_ms`를 수집한다.
- profile:
  - `idle`
  - `post-cpustress`
  - `post-tmpfs-io`
- 각 profile에 대해 min/max/avg/p95/p99/max excess/missed deadline count를 계산한다.
- final `status`와 `longsoak status verbose`로 control channel health를 확인한다.

## Recommended Run

```bash
RUN_ID=v164-sched-latency-$(date +%Y%m%d-%H%M%S)
umask 077

python3 scripts/revalidation/scheduler_latency_baseline.py \
  --run-id "$RUN_ID" \
  --samples 20 \
  --sleep-us 10000 \
  --deadline-ms 300 \
  --stress-sec 2 \
  --stress-workers 2 \
  --io-mb 8 \
  --bridge-timeout 45
```

Output:

```text
tmp/soak/scheduler-latency/<run-id>/scheduler-latency-report.md
tmp/soak/scheduler-latency/<run-id>/scheduler-latency-report.json
```

## Guardrails

- no reboot/recovery/poweroff.
- no partition write/format/raw block access.
- no watchdog open.
- no active trace/ftrace enablement.
- tmpfs I/O profile uses `/tmp`, not Android/SD/raw block paths.
- host evidence files use private directory/file permissions and reject symlink destinations.

## Validation

- `python3 -m py_compile scripts/revalidation/scheduler_latency_baseline.py`
- `git diff --check`
- smoke run:
  - `--samples 3`
  - `--stress-sec 1`
  - `--stress-workers 1`
  - `--io-mb 1`
- full run:
  - `--samples 20`
  - `--sleep-us 10000`
  - `--deadline-ms 300`
  - `--stress-sec 2`
  - `--stress-workers 2`
  - `--io-mb 8`

## Acceptance

- every profile has the requested sample count.
- missed deadline count is 0 for the configured deadline.
- report includes min/max/avg/p95/p99/max excess for every profile.
- cpustress and tmpfs I/O profile setup commands succeed.
- final `status` and `longsoak status verbose` remain responsive.

## Known Limitation

- This is a PID1 run/cmdv1 latency proxy, not a pure in-process kernel wakeup latency test.
- `duration_ms` has an expected floor around the PID1 run wait cadence; v164 should be used as a regression baseline, not as a replacement for `clock_nanosleep`/`cyclictest`.

## Next

- If v164 passes, proceed to v165 USB Recovery Stability.
- If v164 fails, classify the failure as sample collection, missed deadline, cpustress primer, tmpfs I/O profile, or final control-channel health before continuing.
