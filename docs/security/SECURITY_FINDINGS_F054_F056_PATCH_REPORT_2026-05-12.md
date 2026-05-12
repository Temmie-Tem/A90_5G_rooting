# F054-F056 Patch Report

Date: 2026-05-12

Source analysis: `docs/security/SECURITY_FINDINGS_F054_F056_ANALYSIS_2026-05-12.md`
Patch plan: `docs/security/SECURITY_FINDINGS_F054_F056_PATCH_PLAN_2026-05-12.md`

## Summary

Implemented the three small patch batches:

- Batch I1 / `F054`: broker observe read boundary.
- Batch I2 / `F055`: Wi-Fi capability summary fail-closed behavior.
- Batch I3 / `F056`: lifecycle token namespace compatibility.

No native boot image or PID1 code was changed. This is host tooling only.

## Batch I1: Broker Observe Read Boundary

Files:

- `scripts/revalidation/a90_broker.py`
- `scripts/revalidation/a90_broker_auth_hardening_check.py`

Changes:

- Removed unrestricted `cat` from `OBSERVE_COMMANDS`.
- Added `cat` to `OPERATOR_COMMANDS`.
- Added sensitive device read path checks for:
  - `/cache/native-init-tcpctl.token`
  - `/mnt/sdext/a90/runtime/`
  - `/cache/a90/runtime/`
- Added broker selftest coverage for `cat /cache/native-init-tcpctl.token`.
- Added auth hardening check coverage that verifies the sensitive `cat` remains blocked even under `--allow-exclusive`.

Result:

- `F054` status: `mitigated-host-batch-i1`.

## Batch I2: Wi-Fi Capability Summary Fail-Closed

File:

- `scripts/revalidation/kernel_capability_summary.py`

Changes:

- `wifi_gate()` now returns parsed decision, text, `wifi_gate_ok`, and status.
- `build_summary()` includes `wifi_gate_ok` in `pass_ok`.
- Manifest records `wifi_gate_ok` and `wifi_gate_status`.
- Missing or malformed live Wi-Fi gate output now makes the summary fail by default.

Result:

- `F055` status: `mitigated-host-batch-i2`.

## Batch I3: Lifecycle Token Namespace Regression

File:

- `scripts/revalidation/a90_broker_ncm_lifecycle_check.py`

Changes:

- Added missing tcpctl-host-compatible parser fields:
  - `--device-protocol`
  - `--busy-retries`
  - `--busy-retry-sleep`
  - `--menu-hide-sleep`
- Existing dry-run behavior and token redaction were preserved.

Result:

- `F056` status: `mitigated-host-batch-i3`.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/a90_broker.py \
  scripts/revalidation/a90_broker_auth_hardening_check.py \
  scripts/revalidation/a90_broker_concurrent_smoke.py \
  scripts/revalidation/kernel_capability_summary.py \
  scripts/revalidation/a90_kernel_tools.py \
  scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  scripts/revalidation/tcpctl_host.py
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker.py selftest
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_auth_hardening_check.py \
  --run-dir tmp/a90-i1-auth-check-3
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_concurrent_smoke.py \
  --backend fake \
  --clients 2 \
  --rounds 2 \
  --include-blocked \
  --run-dir tmp/a90-i1-fake-smoke-3
```

Result: PASS.

```bash
python3 scripts/revalidation/a90_broker_ncm_lifecycle_check.py \
  --dry-run \
  --token 0123456789ABCDEF0123456789ABCDEF \
  --run-dir tmp/a90-i3-lifecycle-dry-3
```

Result: PASS.

Additional local fixtures:

- Wi-Fi gate failed capture fixture: PASS, `pass_ok=false`, `wifi_gate_ok=false`.
- Lifecycle token namespace fixture: PASS, required token helper fields present.
- `git diff --check`: PASS.

Live bridge validation:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py wififeas gate
python3 scripts/revalidation/a90ctl.py netservice token show
```

Result: PASS on `A90 Linux init 0.9.59 (v159)`.

- `wififeas gate`: `decision=baseline-required`, `status=ok`.
- `netservice token show`: token available; report output redacted during validation.

```bash
python3 scripts/revalidation/kernel_capability_summary.py \
  --out tmp/kernel-capability/i2-live-recheck.md \
  --json-out tmp/kernel-capability/i2-live-recheck.json
```

Result: PASS, `pass=true`, `wifi_gate_ok=true`, `wifi_gate_status=ok`.

```bash
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts/revalidation').resolve()))
import a90_broker_ncm_lifecycle_check as lifecycle
args = lifecycle.build_parser().parse_args(['--run-dir', 'tmp/a90-i3-live-token-check'])
token = lifecycle.get_tcpctl_token(args)
print(len(token), all(c in '0123456789abcdefABCDEF' for c in token))
PY
```

Result: PASS, live token capture returned a 32-byte hex token without starting tcpctl.

## Acceptance

- Default broker observe-only mode can no longer read the tcpctl token through `cat`.
- Wi-Fi capability summary no longer passes when the live `wififeas gate` cannot be verified.
- Lifecycle wrapper no longer lacks the parser namespace fields required by token acquisition.
