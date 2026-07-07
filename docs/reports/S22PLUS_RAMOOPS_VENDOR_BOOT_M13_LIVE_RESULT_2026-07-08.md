# S22+ — Ramoops Vendor Boot + M13 Live Result (2026-07-08)

## Summary

The attended live gate was authorized and executed. The direct-patched
`vendor_boot` candidate flashed and booted Android successfully, and the live
partition hash matched the pinned patched image. However, the live device tree
still reported `ramoops_region/status=disabled`, so the helper stopped before
flashing the M13 boot candidate.

Result: fail-closed before M13. The boot partition was not changed in this run.

## Live Flow

Pre-live dry-run passed:

```text
dry-run ok: vendor_boot/M13 candidates, rollback APs, AGENTS exception,
Android stability, boot hash, and stock vendor_boot hash verified
```

The live command then performed only the first stage of the planned sequence:

1. Reboot Android to Download mode.
2. Flash the SHA-pinned direct-patched `vendor_boot` AP.
3. Wait for Android/root to return.
4. Verify the live `vendor_boot` partition hash.
5. Check the live device-tree `ramoops_region` status.

Verified live facts from the private run log:

- `vendor_boot_candidate_odin_rc=0`
- patched `vendor_boot` hash:
  `d62f2da241e1104db9e4b72aa0ba1927c0e85afd22fe380bff62c8df52bd3245`
- live ramoops status command returned successfully
- live DT values:
  - `status=disabled`
  - `compatible=ramoops`
  - pstore file list empty

The helper exited with the intended fail-closed condition:

```text
patched vendor_boot booted Android but live ramoops status is not okay
```

Because this check failed, M13 was not flashed.

## Recovery

The first attempted Android-side stock `vendor_boot` restore exposed a helper
bug: the restore path checked for stock `vendor_boot` before entering the restore
branch, so it refused to repair the known patched state.

Recovery was completed through the Download-mode restore path. A first
Download-mode restore attempt also exposed that the helper's rollback wait used
a hardcoded 5-second Odin timeout, which was too short for this host/device
transition. Re-running after the Odin endpoint was present restored stock
`vendor_boot` successfully.

Final read-only dry-run after recovery passed, re-verifying:

- Android/root baseline
- Magisk boot baseline
- stock FYG8 `vendor_boot` hash

## Helper Fix

`workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py`
was updated so recovery behaves correctly:

- `--restore-vendor-boot-from-android` now reads the current `vendor_boot` hash
  before the normal stock-only dry-run/live preflight.
- If the hash is already stock, the restore is a no-op and exits cleanly.
- If the hash is the pinned patched `vendor_boot`, the helper reboots to
  Download mode and restores stock.
- Any other `vendor_boot` hash remains fail-closed.
- `vendor_boot` restore and boot rollback now use `--odin-wait-sec` instead of a
  hardcoded 5-second Download-mode wait.

## Validation

Validation after the helper fix:

```text
python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py

python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py \
  --offline-check

python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py \
  --serial <redacted>

python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_vendor_boot_m13_capture_live_gate.py \
  --restore-vendor-boot-from-android \
  --ack S22PLUS-RAMOOPS-RESTORE-STOCK-VENDOR-BOOT \
  --serial <redacted>
```

Observed results:

- `py_compile`: pass
- `--offline-check`: pass
- read-only dry-run: pass
- stock-state `--restore-vendor-boot-from-android`: clean no-op

## Interpretation

This live run proves the direct-patched `vendor_boot` partition can boot and can
be recovered, but it also proves that the patched DTB bytes used by this
candidate are not the active source for the live `/proc/device-tree`
`ramoops_region/status` on this boot path.

The next useful unit is not another M13/M15 boot attempt. It is a host-only
active-DTB provenance audit:

1. Compare the live `/proc/device-tree` shape against each extracted
   `vendor_boot` DTB blob.
2. Identify whether the booted DT is coming from another DTB index, appended
   kernel image data, DTBO/overlay composition, or bootloader-provided state.
3. Build the next ramoops candidate only after the active FDT source is proven.

Until live `ramoops_region/status=okay` is proven, the ramoops positive-control
path should remain stopped before M13.
