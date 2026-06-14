# Native Init v174 USB/NCM Module Port Report (2026-05-09)

## Summary

- label: `v174 USB/NCM Module Port`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- scope: host-side supervisor module wrappers only; no boot image change
- result: `PASS with NCM/TCP SKIP`

v174 ports USB/NCM-related validators onto the supervisor module runner:

- `usb-recovery`
- `ncm-tcp-preflight`

The USB recovery module ran a real bounded rebind/recovery smoke test. The
NCM/TCP module reached its preflight gate and correctly skipped because host USB
NCM (`192.168.7.2`) was not reachable in the current ACM-only environment.

## Implemented

- `scripts/revalidation/a90harness/modules/usb_recovery.py`
  - wraps `scripts/revalidation/usb_recovery_validate.py`
  - smoke profile: `cycles=1`
  - verifies final `version` and `selftest`
- `scripts/revalidation/a90harness/modules/ncm_tcp_preflight.py`
  - wraps `scripts/revalidation/tcpctl_host.py smoke`
  - preflights host NCM ping
  - structured SKIP when NCM is absent
- `scripts/revalidation/native_test_supervisor.py`
  - registers `usb-recovery`
  - registers `ncm-tcp-preflight`

## Validation

Static validation:

```bash
python3 -m py_compile \
  scripts/revalidation/native_test_supervisor.py \
  scripts/revalidation/a90harness/*.py \
  scripts/revalidation/a90harness/modules/*.py

git diff --check
```

USB recovery validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run usb-recovery \
  --profile smoke \
  --observer-duration-sec 0
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v174-usb-recovery-20260508T175639Z module=usb-recovery observer_failures=n/a
```

USB evidence:

- run directory: `tmp/soak/harness/v174-usb-recovery-20260508T175639Z/`
- module result: `modules/usb-recovery/module-result.json`
- child report: `modules/usb-recovery/v174-usb-1778262999/usb-recovery-report.json`
- module skipped: `False`
- module steps: `prepare=True`, `run=True`, `cleanup=True`, `verify=True`
- max recovery: `1.9041382130089914s`

NCM/TCP validation:

```bash
python3 scripts/revalidation/native_test_supervisor.py \
  run ncm-tcp-preflight \
  --profile smoke \
  --observer-duration-sec 5
```

Result:

```text
PASS run_dir=/home/temmie/dev/A90_5G_rooting/tmp/soak/harness/v174-ncm-tcp-preflight-20260508T175654Z module=ncm-tcp-preflight observer_failures=0
```

NCM/TCP evidence:

- run directory: `tmp/soak/harness/v174-ncm-tcp-preflight-20260508T175654Z/`
- module result: `modules/ncm-tcp-preflight/module-result.json`
- preflight transcript: `modules/ncm-tcp-preflight/preflight-ping.txt`
- observer samples: `14`
- observer failures: `0`
- module skipped: `True`
- skip reason: `host NCM path 192.168.7.2 is not reachable; not attempting sudo or USB rebind`

## Acceptance

| Requirement | Evidence | Result |
| --- | --- | --- |
| USB recovery module runs under supervisor | `v174-usb-recovery-20260508T175639Z/manifest.json` | PASS |
| USB recovery leaves bridge recoverable | subsequent `ncm-tcp-preflight` observer completed with failures=0 | PASS |
| NCM/TCP module wrapper exists and preflights NCM | `v174-ncm-tcp-preflight-20260508T175654Z/modules/ncm-tcp-preflight/preflight-ping.txt` | PASS |
| NCM/TCP avoids host mutation when NCM absent | structured SKIP; no sudo/rebind attempted | PASS |
| Existing standalone scripts remain usable | wrappers invoke existing scripts; no CLI contract removed | PASS |
| Static validation passes | `py_compile` and `git diff --check` | PASS |

## Follow-Up

- Re-run `ncm-tcp-preflight` with host NCM configured to obtain full tcpctl smoke evidence.
- Proceed to v175 Unified Evidence Bundle.
