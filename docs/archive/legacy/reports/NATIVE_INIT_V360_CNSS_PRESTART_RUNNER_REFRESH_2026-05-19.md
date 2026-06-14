# v360 Report: CNSS Pre-Start Runner Refresh After V320

- date: `2026-05-19`
- scope: no-start CNSS pre-start runner refresh after V320 PASS
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- plan: `docs/plans/NATIVE_INIT_V360_CNSS_PRESTART_RUNNER_REFRESH_PLAN_2026-05-19.md`
- result: `PASS`

## Summary

After V320 live property lookup PASS, the existing CNSS start-only runner still
expected the old v10 helper SHA by default. That caused a false `start-only-blocked`
preflight result even though the device had the v11 helper deployed and verified.

v360 updates the default expected helper SHA to the v11 artifact used by V320 and
re-runs the no-start plan/preflight/dry-run gates. No daemon was started and no
Wi-Fi bring-up action was performed.

## Evidence

| item | path | decision |
| --- | --- | --- |
| CNSS start plan | `tmp/wifi/v360-cnss-prestart-plan-after-v320/` | `cnss-start-plan-ready` |
| runner plan | `tmp/wifi/v360-cnss-start-only-runner-plan-default-v11-after-v320/` | `dry-run-ready` |
| runner preflight | `tmp/wifi/v360-cnss-start-only-runner-preflight-default-v11-after-v320/` | `preflight-ready` |
| runner dry-run | `tmp/wifi/v360-cnss-start-only-runner-dryrun-default-v11-after-v320/` | `preflight-ready` |

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_cnss_start_only_runner.py
python3 scripts/revalidation/wifi_cnss_start_plan.py \
  --out-dir tmp/wifi/v360-cnss-prestart-plan-after-v320
python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v360-cnss-start-only-runner-plan-default-v11-after-v320 \
  plan
python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v360-cnss-start-only-runner-preflight-default-v11-after-v320 \
  preflight
python3 scripts/revalidation/wifi_cnss_start_only_runner.py \
  --out-dir tmp/wifi/v360-cnss-start-only-runner-dryrun-default-v11-after-v320 \
  dry-run
git diff --check
```

Observed decisions:

```text
cnss-start-plan-ready
runner plan: dry-run-ready
runner preflight: preflight-ready
runner dry-run: preflight-ready
```

Preflight summary with the default v11 SHA:

```text
helper_sha256_expected=f40db33a2823662f64d7a2b3c6dca9ce174801208c14c4a83647a12db1ce636b
helper_sha256_match=true
required_failures=[]
daemon_start_executed=false
```

## Guardrails

- No `run` mode was executed.
- No `--allow-daemon-start` flag was used.
- No `cnss-daemon`, `cnss_diag`, supplicant, wificond, hostapd, or Wi-Fi HAL was
  started.
- No Wi-Fi scan/connect/link-up, credential, DHCP, routing, rfkill, firmware, or
  partition mutation was performed.

## Decision

- decision: `cnss-prestart-runner-refresh-pass`
- current status: no-start CNSS start-only runner is aligned with V320's v11 helper
- next step: choose between a separately approved bounded start-only run and
  another no-start readiness probe.
