# Native Init v165 USB Recovery Stability Report (2026-05-09)

## Result

- status: PASS
- label: `v165 USB Recovery Stability`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- device build was not bumped for this host-side validation step.
- objective: verify ACM bridge recovery after repeated software rebind and NCM on/off rollback.

## Implemented

- Added `scripts/revalidation/usb_recovery_validate.py`.
- Added `docs/plans/NATIVE_INIT_V165_USB_RECOVERY_PLAN_2026-05-09.md`.
- The validator captures private host evidence under `tmp/soak/usb-recovery/<run-id>`.
- The validator treats USB rebind commands as raw-control and uses post-command `cmdv1 version` polling as recovery evidence.

## Evidence Paths

```text
tmp/soak/usb-recovery/v165-smoke-20260509-015552/usb-recovery-report.md
tmp/soak/usb-recovery/v165-smoke-20260509-015552/usb-recovery-report.json
tmp/soak/usb-recovery/v165-usb-recovery-20260509-015633/usb-recovery-report.md
tmp/soak/usb-recovery/v165-usb-recovery-20260509-015633/usb-recovery-report.json
```

## Smoke Profile

```text
run_id: v165-smoke-20260509-015552
result: PASS
cycles: 1
recovered: 3/3
```

## Full Profile

```text
run_id: v165-usb-recovery-20260509-015633
result: PASS
duration: 10.611s
cycles: 3
recovered: 5/5
max_recovery_sec: 1.904982188003487
ncm_present_after_ncm_step: True
final_acm_only: True
```

| Step | Command | Recovered | Recovery sec | Verify |
|---|---|---|---:|---|
| `usbacmreset-01` | `usbacmreset` | `True` | `1.061662662003073` | `ok/0` |
| `usbacmreset-02` | `usbacmreset` | `True` | `1.0614305490016704` | `ok/0` |
| `usbacmreset-03` | `usbacmreset` | `True` | `1.0611723479960347` | `ok/0` |
| `usbnet-ncm` | `run /cache/bin/a90_usbnet ncm` | `True` | `1.904982188003487` | `ok/0` |
| `usbnet-off` | `run /cache/bin/a90_usbnet off` | `True` | `1.9037301869975636` | `ok/0` |

## Check Matrix

| Check | Result | Detail |
|---|---|---|
| baseline status | PASS | `rc=0 status=ok` |
| ncm device function present | PASS | `rc=0 status=ok present=True` |
| recovery steps | PASS | `recovered=5 total=5` |
| final acm-only | PASS | `rc=0 status=ok acm_only=True` |
| final version | PASS | `rc=0 status=ok` |
| final selftest | PASS | `rc=0 status=ok` |

## Static Validation

```text
python3 -m py_compile scripts/revalidation/usb_recovery_validate.py
git diff --check
```

Result: PASS.

## Notes

- Host-side IP assignment and ping were not performed inside v165 because the host interface setup path may require local sudo. v166 is reserved for network throughput and can start from an operator-configured NCM host interface.
- Final state was returned to ACM-only.

## Next

- v166: Network Throughput / Impairment.
