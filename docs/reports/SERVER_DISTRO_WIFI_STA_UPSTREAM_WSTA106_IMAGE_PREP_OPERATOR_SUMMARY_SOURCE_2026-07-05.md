# WSTA106 Image Prep Operator Summary Source Gate

Date: 2026-07-05 01:54 KST host clock
Scope: WSTA42 to WSTA88 operator-facing image-prep summary
Device action: none
Boot flash / native reboot: none
Wi-Fi / DHCP / public tunnel / public smoke: none

## Summary

WSTA105 reduced redundant remote image SHA work, but the operator-facing output
still did not say whether a WSTA88 live run uploaded, restored, or reused the
Debian rootfs image.  WSTA106 adds a redacted image-prep summary and propagates
it through the public summary stack:

- WSTA42 now derives `image_prep_summary()` from the full private WSTA42 result.
- WSTA43 includes `wsta42.image_prep` in its redacted nested public summary.
- WSTA55 exposes top-level `image_prep` for a short-lived public proof.
- WSTA58 exposes `initial.image_prep` and `renewal.image_prep`.
- WSTA88 adds `workflow.image_prep_summary` and renders an `Image Prep` section
  in its workflow markdown when live image-prep data is present.

The summary is deliberately enum/boolean-only:

- `clean_action`: `disabled`, `uploaded`, `reused`, `verified`, or `pending`
- `work_action`: `uploaded`, `restored`, `reused`, `verified`, or `pending`
- `clean_sha_source` / `work_sha_source`: evidence source names only
- `clean_sha_verified` / `work_sha_verified`
- `duplicate_post_hash_skipped`
- upload/restore attempt booleans

It does not include local private image paths, remote image paths, SHA256 values,
public URLs, SSIDs, PSKs, or confirm-token values.

## Validation

Host-side:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/server-distro/run_wsta42_native_uplink_dpublic_tunnel.py \
  workspace/public/src/scripts/server-distro/run_wsta43_orchestrated_native_uplink_dpublic.py \
  workspace/public/src/scripts/server-distro/run_wsta45_appliance_operator.py \
  workspace/public/src/scripts/server-distro/run_wsta55_short_lived_public_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta58_renewal_manual_stop_proof.py \
  workspace/public/src/scripts/server-distro/run_wsta80_persistent_operator_execute_gate.py \
  workspace/public/src/scripts/server-distro/run_wsta88_persistent_operator_workflow.py \
  workspace/public/src/scripts/server-distro/run_wsta94_packet_filter_live_gate.py

PYTHONPATH=tests PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests.test_server_distro_wsta42_native_uplink_dpublic_tunnel \
  tests.test_server_distro_wsta43_orchestrated_native_uplink_dpublic \
  tests.test_server_distro_wsta45_appliance_operator \
  tests.test_server_distro_wsta55_short_lived_public_proof \
  tests.test_server_distro_wsta58_renewal_manual_stop_proof \
  tests.test_server_distro_wsta80_persistent_operator_execute_gate \
  tests.test_server_distro_wsta88_persistent_operator_workflow \
  tests.test_server_distro_wsta94_packet_filter_live_gate
```

Result: `Ran 87 tests ... OK`.

Focused coverage added:

- WSTA42 summary reports reused clean/work image state without paths or SHA
  values.
- WSTA43 redacted public summary carries image-prep status without public URL,
  private public-url path, token, or SHA leakage.
- WSTA55 exposes top-level image-prep state for short-lived public proof output.
- WSTA58 exposes initial and renewal image-prep state.
- WSTA88 workflow summary and markdown render initial/renewal image-prep actions.

## Next

The next WSTA polish unit can use this summary as a stable operator surface:
show public state, lease state, image-prep state, packet-filter state, and
manual-stop state in a compact WSTA88 status/HUD output without opening live
public exposure by default.
