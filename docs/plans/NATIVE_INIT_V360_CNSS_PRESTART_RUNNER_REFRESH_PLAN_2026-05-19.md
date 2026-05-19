# v360 Plan: CNSS Pre-Start Runner Refresh After V320

- date: `2026-05-19`
- scope: refresh the no-start CNSS start-only runner boundary after V320 private property lookup PASS
- boot image change: none
- native baseline: `A90 Linux init 0.9.61 (v319)`
- approval boundary: no daemon start, no Wi-Fi scan/connect/link-up, no rfkill/firmware/routing mutation

## Summary

V320 proved that `/system/bin/getprop` can read four allowlisted properties from
the private V317 property namespace when the v11 `a90_android_execns_probe`
helper is deployed and `/mnt/system` is mounted read-only.

The next safe step is not daemon start. The next safe step is to refresh the
existing CNSS start-only runner so its preflight uses the v11 helper SHA by
default, then prove `plan`/`preflight`/`dry-run` still pass without executing
`cnss-daemon`.

## Changes

- Update `scripts/revalidation/wifi_cnss_start_only_runner.py` default helper
  SHA from v10 to v11:
  `f40db33a2823662f64d7a2b3c6dca9ce174801208c14c4a83647a12db1ce636b`.
- Keep the helper path as `/cache/bin/a90_android_execns_probe`.
- Keep the start-only helper command blocked unless the existing explicit
  dangerous run flags are supplied.
- Do not change boot image, native init, NCM, rfkill, firmware, or Wi-Fi link
  state.

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

Expected decisions:

- `cnss-start-plan-ready`
- `dry-run-ready`
- `preflight-ready`
- `preflight-ready`

## Non-Goals

- Do not execute `wifi_cnss_start_only_runner.py run`.
- Do not pass `--allow-daemon-start`.
- Do not start `cnss-daemon`, `cnss_diag`, supplicant, wificond, hostapd, or
  Android Wi-Fi HAL.
- Do not scan/connect/link-up Wi-Fi.
- Do not write rfkill, firmware paths, partitions, or Android properties.

## Acceptance

- v11 helper default SHA matches the deployed helper.
- no-start plan/preflight/dry-run pass without extra `--helper-sha256` override.
- manifests record `daemon_start_executed=false`.
- next step remains a separately approved bounded CNSS start-only run or another
  no-start readiness probe.
