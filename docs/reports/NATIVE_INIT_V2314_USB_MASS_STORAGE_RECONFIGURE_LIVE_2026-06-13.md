# Native Init V2314 USB Mass Storage Reconfigure Live Validation

## Summary

- Cycle: `V2314`
- Artifact: `A90 Linux init 0.9.278 (v2314-usb-ms-reconfigure)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2314_usb_ms_reconfigure.img`
- Boot SHA256: `0ad0c5eb29e8ddf8a34a906d4a0107104f51880eb1d4d736866e78bb0f289022`
- Decision: `v2314-usb-ms-reconfigure-live-pass`
- Result: PASS
- Scope: U2 of the USB gadget runtime-control epic: atomic auxiliary `mass_storage.0` add/remove while preserving control ACM plus NCM.
- Rollback checkpoint remains: `v2237-supplicant-terminate-poll`.

## Validation

- Static validation:
  - `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2314_usb_mass_storage_reconfigure.py tests/test_build_native_init_boot_v2314_usb_mass_storage_reconfigure.py`
  - `PYTHONPATH=tests python3 -m unittest tests.test_build_native_init_boot_v2314_usb_mass_storage_reconfigure` → 3 tests PASS.
  - `python3 -m unittest discover -s tests -p 'test_*.py'` → 990 tests PASS.
  - `file workspace/private/builds/native-init/v2314-usb-ms-reconfigure/init_v2314_usb_ms_reconfigure` → AArch64 static executable.
  - `git diff --check` PASS.
- Flash path:
  - Used only `workspace/public/src/scripts/revalidation/native_init_flash.py`.
  - Reconfirmed `v2237` rollback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
  - Reconfirmed fallback `boot_linux_v48.img` SHA256: `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
  - First native-to-recovery request was stopped before any boot write because the host serial bridge was not running.
  - After restarting the serial bridge on `/dev/ttyACM0`, the second flash wrote only the boot partition and read back the V2314 SHA256.
- Device health:
  - `version` matched `A90 Linux init 0.9.278 (v2314-usb-ms-reconfigure)`.
  - Post-flash health check returned `selftest fail=0`.
  - Post-U2 final `selftest verbose` returned `fail=0`.

## U2 Runtime Results

Preflight `usb status` before mutation showed the V2313 topology still intact:

| Field | Value |
| --- | --- |
| `gadget.udc` | `a600000.dwc3` |
| `gadget.bound` | `1` |
| `idVendor` / `idProduct` | `0x04e8` / `0x6861` |
| `config.0.name` | `b.1` |
| `config.0.link_count` | `2` |
| `configs/b.1/f2` | `ncm.usb0`, `control-ncm` |
| `configs/b.1/f1` | `acm.usb0`, `control-acm` |
| `control.ok` | `1` |

`usb mass-storage add` scheduled one detached worker and returned before the expected USB drop:

| Field | Value |
| --- | --- |
| `usb.mass_storage.action` | `add` |
| `usb.mass_storage.expected_usb_disconnect` | `1` |
| `usb.mass_storage.control_required` | `NCM+ACM` |
| `usb.mass_storage.watchdog_sec` | `8` |
| `usb.mass_storage.host_enumeration_required` | `parked` |
| `usb.mass_storage.decision` | `scheduled` |

After re-enumeration, the serial bridge returned and `usb status` showed the auxiliary function linked while both control functions remained present:

| Field | Value |
| --- | --- |
| `config.0.link_count` | `3` |
| `configs/b.1/f3` | `mass_storage.0`, `aux` |
| `configs/b.1/f2` | `ncm.usb0`, `control-ncm` |
| `configs/b.1/f1` | `acm.usb0`, `control-acm` |
| `function.0.name` | `mass_storage.0` |
| `function.0.linked` | `1` |
| `control.ok` | `1` |

`usb mass-storage remove` then scheduled the symmetric detached worker. After re-enumeration, the serial bridge returned and `usb status` showed no active mass-storage config link:

| Field | Value |
| --- | --- |
| `config.0.link_count` | `2` |
| `configs/b.1/f2` | `ncm.usb0`, `control-ncm` |
| `configs/b.1/f1` | `acm.usb0`, `control-acm` |
| `function.0.name` | `mass_storage.0` |
| `function.0.linked` | `0` |
| `control.ok` | `1` |

The `mass_storage.0` function instance is intentionally left present but unlinked after remove; the active config no longer exposes it. This avoids extra configfs deletion risk while preserving the control-only gadget state.

## Serial Re-sync Note

Both add/remove cycles caused the expected USB ACM disconnect. The first post-cycle `usb status` attempts hit partial serial/protocol output while the host bridge was reattaching. Pure read-only retries then returned clean `A90P1` responses. No second mutation was issued; the successful topology checks came from read-only `version`, `usb status`, and `selftest` commands after control returned.

## Safety Result

- Every mutation preserved `acm.usb0` plus `ncm.usb0` in the rebuilt config.
- Reconfigure ran as bounded unbind -> reconfigure -> rebind in a detached device-side worker.
- The watchdog/known-good restore path was present; it did not need to fire in this run.
- `mass_storage.0` used a removable no-media LUN; no backing file was exposed in U2.
- No adb-over-ffs, HID, BadUSB, Wi-Fi scan/connect/DHCP/ping, credentials, or forbidden partition work.
- Host-side enumeration of the mass-storage function remains a parked operator checkpoint for U3; this U2 pass validates serial control return plus configfs topology only.

## Next Unit

Proceed only to U3 in a later iteration: first persona end-to-end validation. Recommended path is mass-storage with an explicit bounded backing image and host-side enumeration/control-return checklist. Do not start adb-over-ffs or HID/BadUSB in the layer-1 U3 step.
