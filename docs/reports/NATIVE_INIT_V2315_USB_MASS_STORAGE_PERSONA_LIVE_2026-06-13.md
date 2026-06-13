# Native Init V2315 USB Mass Storage Persona Live Validation

## Summary

- Cycle: `V2315`
- Artifact: `A90 Linux init 0.9.279 (v2315-usb-ms-persona)`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2315_usb_ms_persona.img`
- Boot SHA256: `49d21d98dc75d73277d2c690ed389e75ac2c4d18ae14ae42cda7c38bd92ac0cf`
- Decision: `v2315-usb-ms-persona-live-pass`
- Result: PASS
- Scope: U3 of the USB gadget runtime-control epic: first mass-storage persona end-to-end.
- Rollback checkpoint remains: `v2237-supplicant-terminate-poll`.

## Validation

- Static validation:
  - `python3 -m py_compile workspace/public/src/scripts/revalidation/build_native_init_boot_v2315_usb_mass_storage_persona.py tests/test_build_native_init_boot_v2315_usb_mass_storage_persona.py`
  - `PYTHONPATH=tests python3 -m unittest tests.test_build_native_init_boot_v2315_usb_mass_storage_persona` → 3 tests PASS.
  - `python3 -m unittest discover -s tests -p 'test_*.py'` → 993 tests PASS.
  - `file workspace/private/builds/native-init/v2315-usb-ms-persona/init_v2315_usb_ms_persona` → AArch64 static executable.
  - `git diff --check` PASS.
- Flash path:
  - Used only `workspace/public/src/scripts/revalidation/native_init_flash.py`.
  - Reconfirmed `v2237` rollback SHA256: `b2ea2d26d160b7702ce7d4438b84367788eea26c6a5bbe4ed93f3d270292ac7f`.
  - Reconfirmed fallback `boot_linux_v48.img` SHA256: `1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042`.
  - Boot partition write/readback SHA256 matched the V2315 image.
- Device health:
  - `version` matched `A90 Linux init 0.9.279 (v2315-usb-ms-persona)`.
  - Post-flash health check returned `selftest fail=0`.
  - Final post-remove `selftest verbose` returned `fail=0`.

## U3 Runtime Results

Preflight `usb status` before mutation showed the control-only V2315 gadget:

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

`usb mass-storage expose` scheduled one detached worker and returned before the expected USB drop:

| Field | Value |
| --- | --- |
| `usb.mass_storage.action` | `expose` |
| `usb.mass_storage.persona` | `readonly-backing` |
| `usb.mass_storage.backing_file` | `/cache/a90-usb-mass-storage-v2315.img` |
| `usb.mass_storage.backing_bytes` | `8388608` |
| `usb.mass_storage.read_only` | `1` |
| `usb.mass_storage.control_required` | `NCM+ACM` |
| `usb.mass_storage.watchdog_sec` | `8` |
| `usb.mass_storage.decision` | `scheduled` |

After re-enumeration, the serial bridge returned and `usb status` showed the persona active:

| Field | Value |
| --- | --- |
| `config.0.link_count` | `3` |
| `configs/b.1/f3` | `mass_storage.0`, `aux` |
| `configs/b.1/f2` | `ncm.usb0`, `control-ncm` |
| `configs/b.1/f1` | `acm.usb0`, `control-acm` |
| `function.0.name` | `mass_storage.0` |
| `function.0.linked` | `1` |
| `function.0.mass_storage.file.present` | `1` |
| `function.0.mass_storage.file.path` | `/cache/a90-usb-mass-storage-v2315.img` |
| `function.0.mass_storage.ro` | `1` |
| `function.0.mass_storage.removable` | `1` |
| `function.0.mass_storage.cdrom` | `0` |
| `control.ok` | `1` |

Host-side enumeration was observed without mounting or writing the device. `lsblk` showed one new read-only USB disk during expose:

| Field | Value |
| --- | --- |
| Device node class | USB disk |
| Vendor / model | `SAMSUNG` / `File-Stor Gadget` |
| Size | `8M` |
| Read-only | `1` |
| Type | `disk` |

`usb mass-storage remove` then scheduled the symmetric reconfigure. After re-enumeration, the serial bridge returned, host-side `lsblk` no longer showed the `File-Stor Gadget` disk, and `usb status` showed control-only no-medium state:

| Field | Value |
| --- | --- |
| `config.0.link_count` | `2` |
| `configs/b.1/f2` | `ncm.usb0`, `control-ncm` |
| `configs/b.1/f1` | `acm.usb0`, `control-acm` |
| `function.0.name` | `mass_storage.0` |
| `function.0.linked` | `0` |
| `function.0.mass_storage.file.present` | `0` |
| `function.0.mass_storage.file.path` | `-` |
| `function.0.mass_storage.ro` | `1` |
| `control.ok` | `1` |

## Serial Re-sync Note

The expected USB ACM disconnect can leave the first post-cycle command with partial prompt/protocol text while the host bridge is reattaching. As in V2314, clean read-only retries returned full `A90P1` responses. No second expose/remove mutation was issued; final pass criteria are based on the clean recovery reads.

## Safety Result

- Every mutation preserved `acm.usb0` plus `ncm.usb0` in the rebuilt config.
- Reconfigure used the bounded detached worker and V2314 watchdog/known-good restore path.
- The U3 backing file is generated under `/cache`, bounded to 8 MiB, and exposed read-only.
- Remove unlinks the aux function and clears the LUN file attribute, returning to no-medium state.
- Host-side validation was read-only enumeration only; no mount, filesystem write, credentials, network, adb-over-ffs, HID, BadUSB, or forbidden partition work.
- Final `selftest fail=0` and `control.ok=1` confirm the control channel returned.

## Epic Result

Layer 1 of the USB gadget runtime-control epic is complete:

- U1 `usb status` inventory: DONE at V2313.
- U2 atomic aux add/remove: DONE at V2314.
- U3 mass-storage persona end-to-end: DONE at V2315.

Do not proceed to adb-over-ffs or HID/BadUSB in this epic. Those are separate follow-on epics and require a new explicit goal.
