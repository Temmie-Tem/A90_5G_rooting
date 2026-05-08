# Native Init v163 CPU/Memory/Thermal Stability Plan (2026-05-09)

## Summary

- target label: `v163 CPU/Memory/Thermal Stability`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 bounded CPU stress, tmpfs memory verify, thermal/power/status trend를 묶어서 부하 중 PID1 안정성을 확인하는 것이다.
- v163은 host-side validation helper를 추가한다. device boot image bump는 device-side memory helper가 필요해질 때만 별도 판단한다.

## Scope

- `scripts/revalidation/cpu_mem_thermal_stability.py` 추가.
- CPU load는 기존 `/bin/a90_cpustress`를 반복 실행한다.
- memory verify는 tmpfs `/tmp/a90-<run-id>-mem.bin`에 bounded zero pattern을 쓰고 `sha256sum`으로 검증한다.
- 각 stress cycle 후 `status`를 수집해 다음 값을 trend로 남긴다.
  - CPU/GPU temperature
  - CPU/GPU usage percent
  - battery percent/temp
  - power now/avg
  - memory used/total
  - uptime/load
  - longsoak health
  - status command duration
- 마지막에 process snapshot으로 zombie count와 PID1 fd count를 확인한다.

## Recommended Run

```bash
RUN_ID=v163-cpu-mem-thermal-$(date +%Y%m%d-%H%M%S)
umask 077

python3 scripts/revalidation/cpu_mem_thermal_stability.py \
  --run-id "$RUN_ID" \
  --cycles 5 \
  --stress-sec 3 \
  --stress-workers 2 \
  --mem-size 32M \
  --bridge-timeout 45 \
  --max-cpu-temp-c 85 \
  --max-gpu-temp-c 85 \
  --max-battery-temp-c 45 \
  --max-status-duration-ms 2000
```

Output:

```text
tmp/soak/cpu-mem-thermal/<run-id>/cpu-mem-thermal-report.md
tmp/soak/cpu-mem-thermal/<run-id>/cpu-mem-thermal-report.json
```

## Guardrails

- no reboot/recovery/poweroff.
- no partition write/format/raw block access.
- no watchdog open.
- no active trace/ftrace enablement.
- memory verify is bounded and uses tmpfs `/tmp`, not SD or Android partitions.
- host evidence files use private directory/file permissions and reject symlink destinations.

## Validation

- `python3 -m py_compile scripts/revalidation/cpu_mem_thermal_stability.py`
- `git diff --check`
- smoke run:
  - `--cycles 1`
  - `--stress-sec 1`
  - `--stress-workers 1`
  - `--mem-size 1M`
- full run:
  - `--cycles 5`
  - `--stress-sec 3`
  - `--stress-workers 2`
  - `--mem-size 32M`

## Acceptance

- tmpfs memory write/hash/cleanup succeeds.
- every cpustress cycle exits 0.
- every status sample returns under the configured latency threshold.
- CPU/GPU/battery temperatures stay below configured thresholds.
- longsoak health stays `ok`.
- controlled zombie count remains 0.
- final `selftest verbose` and `longsoak status verbose` remain responsive.

## Next

- If v163 passes, proceed to v164 Scheduler/Latency Baseline.
- If v163 fails, classify the failure as cpustress helper, memory verify, thermal threshold, status responsiveness, longsoak health, or zombie/reap before continuing.
