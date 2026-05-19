# v339 V317 Live Surface Linter Report

- date: `2026-05-19`
- scope: host-only static linter for V317 live command surface
- device command: none
- device mutation: none
- result: `PASS`

## Summary

v339 validates the V317 live command surface before requesting operator approval.
The linter found exactly the expected `device_cmd()` calls and all are bounded to
private workdir file operations: directory creation, appendfile chunk upload, and
`toybox rm/uudecode/sha256sum/mv` verification/move cleanup.

## Evidence

- tool: `scripts/revalidation/wifi_v317_live_surface_linter.py`
- evidence: `tmp/wifi/v339-v317-live-surface-linter/`
- decision: `v317-live-surface-lint-pass`
- pass: `true`
- device commands executed: `false`
- device mutations: `false`

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_live_surface_linter.py
python3 scripts/revalidation/wifi_v317_live_surface_linter.py \
  --out-dir tmp/wifi/v339-v317-live-surface-linter \
  lint
git diff --check
```

Observed result:

```text
decision: v317-live-surface-lint-pass
pass: True
reason: V317 live surface is limited to approved private-workdir file operations
```

## Interpretation

- V317 live proof remains unexecuted.
- The live runner does not expose daemon start, Wi-Fi scan/connect/link-up,
  rfkill, module, routing, NCM, or tcpctl operations through `device_cmd()`.
- The remaining blocker is still the exact V317 approval phrase.
