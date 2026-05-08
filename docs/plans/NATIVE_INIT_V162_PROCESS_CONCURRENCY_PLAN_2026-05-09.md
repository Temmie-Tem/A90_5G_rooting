# Native Init v162 Process/Concurrency Stability Plan (2026-05-09)

## Summary

- target label: `v162 Process/Concurrency Stability`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 PID1 shell, run helper lifecycle, service registry, tcpctl multi-client path가 동시에 움직일 때 응답성과 reap 상태가 유지되는지 확인하는 것이다.
- v162는 host-side validation helper를 추가한다. device boot image bump는 process-side 계측 명령이 필요해질 때만 별도 판단한다.

## Scope

- `scripts/revalidation/process_concurrency_validate.py` 추가.
- serial/cmdv1 경로에서 short helper churn을 반복한다.
  - `run /cache/bin/toybox true`
  - `run /cache/bin/toybox uptime`
  - `stat /proc/1/status`
  - `echo v162-concurrency-ping`
- NCM/tcpctl 경로에서 bounded multi-client 요청을 병렬 실행한다.
- `longsoak`, `autohud`, tcpctl listener, short `/bin/a90_cpustress` burst를 동시에 둔다.
- 전후 process snapshot을 수집한다.
  - `toybox ps -A -o pid,stat,comm`
  - `/proc/1/fd` count
  - zombie/global controlled process count
- menu visible 상태의 unsafe `run` busy gate를 확인한다.

## Recommended Run

```bash
RUN_ID=v162-process-$(date +%Y%m%d-%H%M%S)
umask 077

python3 scripts/revalidation/process_concurrency_validate.py \
  --run-id "$RUN_ID" \
  --churn-loops 8 \
  --client-workers 4 \
  --client-loops 4 \
  --cpustress-sec 3 \
  --cpustress-workers 2 \
  --bridge-timeout 45 \
  --tcp-timeout 15 \
  --fd-growth-limit 8
```

Output:

```text
tmp/soak/process-concurrency/<run-id>/process-concurrency-report.md
tmp/soak/process-concurrency/<run-id>/process-concurrency-report.json
```

## Guardrails

- no reboot/recovery/poweroff.
- no partition write/format/raw block access.
- no watchdog open.
- no active trace/ftrace enablement.
- tcpctl listener uses bounded `max_clients`, adjusted to cover expected validation requests.
- host evidence files use private directory/file permissions and reject symlink destinations.

## Validation

- `python3 -m py_compile scripts/revalidation/process_concurrency_validate.py`
- `git diff --check`
- smoke run:
  - `--churn-loops 1`
  - `--client-workers 2`
  - `--client-loops 1`
  - `--cpustress-sec 1`
- full run:
  - `--churn-loops 8`
  - `--client-workers 4`
  - `--client-loops 4`
  - `--cpustress-sec 3`
- post-test:
  - `status`
  - `selftest verbose`
  - `longsoak status verbose`

## Acceptance

- helper churn succeeds for every command.
- tcpctl multi-client operations all return OK.
- concurrent `/bin/a90_cpustress` returns OK.
- tcpctl shutdown returns OK and serial run reports `[done] run`.
- controlled zombie count remains 0.
- PID1 fd count does not grow beyond the configured threshold.
- menu visible state blocks unsafe `run`.
- PID1 shell/cmdv1 remains responsive after the test.

## Next

- If v162 passes, proceed to v163 CPU/Memory/Thermal Stability.
- If v162 fails, classify the failure as serial busy gate, tcpctl client limit, tcpctl transport, cpustress helper, zombie/reap, or fd growth before continuing.
