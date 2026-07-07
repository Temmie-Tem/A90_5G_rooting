# S22+ Ramoops Android Baseline Preflight (2026-07-08)

## Scope

Read-only Android/ADB preflight. No flash, no reboot, no sysfs write, no
partition write, no file staging on device, and no `AGENTS.md` edit.

This validates that the connected S22+ is still on the expected baseline before
any future ramoops DTBO + M18 capture approval.

## Added

`workspace/public/src/scripts/revalidation/s22plus_ramoops_android_baseline_preflight.py`

The helper checks:

- exactly one matching S22+ ADB device;
- `SM-S906N` / `g0q` / `S906NKSS7FYG8`;
- Android boot completed and boot animation stopped;
- `ro.boot.verifiedbootstate=orange`;
- root is available through Magisk;
- current `boot` partition SHA equals the known Magisk boot baseline;
- current `dtbo` partition SHA equals stock FYG8 DTBO;
- live DT ramoops status is still `disabled`.

## Live Read-Only Result

Command:

```sh
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_ramoops_android_baseline_preflight.py

python3 workspace/public/src/scripts/revalidation/s22plus_ramoops_android_baseline_preflight.py \
  > /tmp/s22plus_ramoops_android_baseline_preflight.json
```

Summary:

```json
{
  "result": "pass",
  "props": {
    "boot_completed": "1",
    "boot_recovery": "0",
    "bootanim": "stopped",
    "bootloader": "S906NKSS7FYG8",
    "device": "g0q",
    "incremental": "S906NKSS7FYG8",
    "model": "SM-S906N",
    "su_id_root": true,
    "vbstate": "orange"
  },
  "boot_sha": "2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e",
  "dtbo_sha": "97a4864fee4e61892d733962d1ec76f8d14b52bc19e6f47440bc27d9dfc4bd0c",
  "checks": {
    "boot_completed": true,
    "boot_recovery_zero": true,
    "boot_sha_matches_magisk_baseline": true,
    "bootanim_stopped": true,
    "bootloader": true,
    "device": true,
    "dtbo_sha_matches_stock": true,
    "incremental": true,
    "model": true,
    "ramoops_status_disabled": true,
    "root_available": true,
    "vbstate_orange": true
  }
}
```

No serial number is recorded in this report.

## Interpretation

The current connected S22+ is in the right baseline state for a future attended
capture approval:

- Magisk boot baseline is installed and readable.
- Stock DTBO is currently installed.
- The disabled-vbmeta/orange condition required by the patched DTBO caveat is
  present.
- The live DT still disables ramoops, so the planned DTBO patch remains relevant.

Live capture remains unauthorized until the reviewed `AGENTS.md` exception is
explicitly activated.
