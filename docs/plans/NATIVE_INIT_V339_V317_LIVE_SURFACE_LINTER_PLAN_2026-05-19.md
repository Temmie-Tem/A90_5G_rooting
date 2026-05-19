# v339 Plan: V317 Live Surface Linter

- date: `2026-05-19`
- scope: host-only static linter for V317 live command surface
- boot image change: none planned
- device mutation: none planned
- status: implemented / validated

## Summary

V317 is now staged behind exact approval, V336 pre-live audit, and V337 runner
checks. v339 adds one more host-only guard: a static linter that inspects the
V317 runner's `device_cmd()` surface and ensures only approved private-workdir
file operations can execute.

This does not run V317 and does not open the bridge.

## Implementation

- Add `scripts/revalidation/wifi_v317_live_surface_linter.py`.
- Parse `wifi_private_property_namespace_proof.py` with `ast`.
- Enumerate all `device_cmd()` calls and canonicalize their argv signatures.
- Allow only:
  - `mkdir <private path>`
  - `appendfile <private temp file> <chunk>`
  - `toybox rm/uudecode/sha256sum/mv` bounded to V317 workdir paths
- Check the V331 handoff packet includes `v336-prelive-gate` and
  `--prelive-gate-manifest`.
- Check forbidden scope text remains present in the handoff packet.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_v317_live_surface_linter.py
python3 scripts/revalidation/wifi_v317_live_surface_linter.py \
  --out-dir tmp/wifi/v339-v317-live-surface-linter \
  lint
git diff --check
```

Expected result:

```text
decision: v317-live-surface-lint-pass
pass: True
```

## Acceptance

- Every `device_cmd()` call in the V317 runner has an allowlisted signature.
- No forbidden Wi-Fi/network/daemon/rfkill/module command token appears in the
  live command surface.
- Readiness packet still passes and includes the V336 gate argument.
- `device_commands_executed=false` and `device_mutations=false`.
