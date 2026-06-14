# Native Init v245 CNSS Start-Only Runner

- generated: `2026-05-19`
- result: `PASS`
- decision: `preflight-ready`
- reason: safe plan/preflight/dry-run runner works and live daemon start remains fail-closed by default
- device baseline: `A90 Linux init 0.9.59 (v159)`
- boot image change: none
- daemon start: not executed
- evidence:
  - `tmp/wifi/v245-cnss-start-only-runner-plan/`
  - `tmp/wifi/v245-cnss-start-only-runner-preflight/`
  - `tmp/wifi/v245-cnss-start-only-runner-dryrun/`
  - `tmp/wifi/v245-cnss-start-only-runner-run-blocked/`

## Implementation

- plan: `docs/plans/NATIVE_INIT_V245_CNSS_START_ONLY_RUNNER_PLAN_2026-05-19.md`
- host tool: `scripts/revalidation/wifi_cnss_start_only_runner.py`
- helper prerequisite: `/cache/bin/a90_android_execns_probe`
- expected helper SHA-256: `4ce17edfdfe9935da8a320e5a570d301517d518d0ae1dcadaef8bafec7415647`

## Validation

- `python3 -m py_compile scripts/revalidation/wifi_cnss_start_only_runner.py scripts/revalidation/wifi_cnss_identity_probe.py` — PASS
- `git diff --check` — PASS
- `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v245-cnss-start-only-runner-plan plan` — PASS / `dry-run-ready`
- `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v245-cnss-start-only-runner-preflight preflight` — PASS / `preflight-ready`
- `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v245-cnss-start-only-runner-dryrun dry-run` — PASS / `preflight-ready`
- `python3 scripts/revalidation/wifi_cnss_start_only_runner.py --out-dir tmp/wifi/v245-cnss-start-only-runner-run-blocked run` — expected FAIL-CLOSED / `start-only-blocked`

## Live Preflight Result

| item | value |
| --- | --- |
| command count | `18` |
| ok commands | `18` |
| helper SHA match | `true` |
| required failures | `[]` |
| active Wi-Fi warnings | `[]` |
| daemon start executed | `false` |

## Runner Behavior

- `plan` validates prerequisite manifests only.
- `preflight` runs read-only native commands and verifies helper SHA/state.
- `dry-run` builds the future `cnss-start-only` helper argv and cleanup graph without executing it.
- `run` remains blocked unless dangerous flags are supplied, and v245 safe runner still does not implement live daemon start.

## Guardrails Confirmed

- No `cnss-daemon` execution.
- No `cnss_diag` execution.
- No Wi-Fi scan/connect/link-up/credential/DHCP/routing.
- No rfkill unblock, `ip link set wlan* up`, `iw scan/connect`, supplicant/HAL/wificond/hostapd.
- No ICNSS bind/unbind or persistent Android partition write.

## Interpretation

v245 closes the safe host-side runner foundation after v244. The next step is a reviewed v246 implementation of the helper `cnss-start-only` mode or a final approval gate for a live bounded daemon attempt. Actual daemon execution should remain blocked until the operator explicitly approves the start-only experiment after reviewing v245 dry-run evidence.
