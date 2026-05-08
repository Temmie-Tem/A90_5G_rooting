# Native Init v165 USB Recovery Stability Plan (2026-05-09)

## Summary

- target label: `v165 USB Recovery Stability`
- baseline device build: `A90 Linux init 0.9.59 (v159)`
- 목적은 software USB re-enumeration 후 ACM bridge가 반복 복구되는지, NCM composite 전환/ACM-only rollback이 정상인지 확인하는 것이다.
- host-side IPv4 assignment and ping can still require local sudo, so v165 validates device-side NCM presence and serial/control recovery; v166 handles network throughput separately.

## Scope

- `scripts/revalidation/usb_recovery_validate.py` 추가.
- raw-control 성격 명령은 END marker가 없을 수 있으므로 command send 후 `version` polling으로 복구 시간을 측정한다.
- 검증 순서:
  - baseline `status`
  - repeated `usbacmreset`
  - `run /cache/bin/a90_usbnet ncm`
  - device-side `a90_usbnet status`에서 `ncm.ifname: ncm0` 확인
  - `run /cache/bin/a90_usbnet off`
  - final ACM-only state 확인
  - final `version`, `selftest verbose`

## Recommended Run

```bash
RUN_ID=v165-usb-recovery-$(date +%Y%m%d-%H%M%S)
umask 077

python3 scripts/revalidation/usb_recovery_validate.py \
  --run-id "$RUN_ID" \
  --cycles 3 \
  --timeout 12 \
  --recovery-timeout 35
```

Output:

```text
tmp/soak/usb-recovery/<run-id>/usb-recovery-report.md
tmp/soak/usb-recovery/<run-id>/usb-recovery-report.json
```

## Guardrails

- no reboot/recovery/poweroff.
- no partition write/format/raw block access.
- no watchdog open.
- no host network mutation inside the validator.
- final state must be ACM-only unless a test explicitly requests otherwise.
- host evidence files use private directory/file permissions and reject symlink destinations.

## Validation

- `python3 -m py_compile scripts/revalidation/usb_recovery_validate.py`
- `git diff --check`
- smoke run:
  - `--cycles 1`
- full run:
  - `--cycles 3`
  - includes NCM on and ACM-only off rollback

## Acceptance

- every recovery step returns to working `cmdv1 version`.
- NCM device function appears after the NCM step.
- final state is ACM-only.
- final `version` and `selftest verbose` pass.
- recovery report includes per-step recovery time and max recovery time.

## Next

- If v165 passes, proceed to v166 Network Throughput / Impairment.
- If v165 fails, classify the failure as ACM reset, NCM enable, ACM-only rollback, bridge polling, or final selftest before continuing.
