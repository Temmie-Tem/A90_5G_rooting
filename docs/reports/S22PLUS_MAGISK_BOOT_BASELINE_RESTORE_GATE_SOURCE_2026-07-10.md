# S22+ Magisk Boot Baseline Restore Gate Source

Date: 2026-07-10 01:13 KST / 2026-07-09 16:13 UTC

## Verdict

Added a narrow host-side restore gate for the current S22+ state:

```text
workspace/public/src/scripts/revalidation/s22plus_magisk_boot_baseline_restore_gate.py
tests/test_s22plus_magisk_boot_baseline_restore_gate.py
```

The helper is for restoring the pinned Magisk boot measurement baseline after
S10C0 recovered to stock boot. It is intentionally narrower than the older
TWRP+Magisk restore window:

```text
flash target: boot partition only, via Odin AP slot
AP.tar.md5 SHA256: d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
tar member: boot.img.lz4
boot.img.lz4 SHA256: b33b63d9d2c56cbe10170820e88cf136be8fe9ad621a21752da19fdd9b642d31
post-restore boot SHA256: 2e541703951dc725bad35850faf7028c2d910dd5f21166449b63f1248c29967e
```

No live action was performed. No Odin flash, reboot, partition write, or
rollback was performed for this source unit.

## Safety Contract

Default execution and `--offline-check` verify host artifacts only:

```text
offline_check=ok device_action=0 agents_exception_checked=0
```

Live modes are locked behind all of:

```text
--live-from-download or --live-from-android
--ack S22PLUS-MAGISK-BOOT-BASELINE-RESTORE-GATE
active AGENTS.md exception containing the exact helper, ACK, AP hash, member hash, and boot hash
```

The generated active-exception template explicitly denies recovery, vendor_boot,
vbmeta, dtbo, BL, CP, CSC, super, userdata, EFS, sec_efs, RPMB, keymaster,
modem, bootloader, raw host `dd`, fastboot, Magisk modules, multidisabler,
format data, native-init candidates, kernel rebuilds, and A90 actions.

## Offline Evidence

Command:

```text
RUN_DIR=workspace/private/runs/s22plus_magisk_boot_baseline_restore_offline_20260709T161328Z
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 \
  workspace/public/src/scripts/revalidation/s22plus_magisk_boot_baseline_restore_gate.py \
  --offline-check \
  --run-dir "$RUN_DIR"
```

Result:

```text
offline-check ok: Magisk boot baseline restore artifact verified; no device action
magisk_ap_sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
magisk_ap_members=['boot.img.lz4']
magisk_member_sha256=b33b63d9d2c56cbe10170820e88cf136be8fe9ad621a21752da19fdd9b642d31
```

## Validation

Commands:

```text
PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m py_compile \
  workspace/public/src/scripts/revalidation/s22plus_magisk_boot_baseline_restore_gate.py \
  tests/test_s22plus_magisk_boot_baseline_restore_gate.py

PYTHONPYCACHEPREFIX=/tmp/a90_pycache python3 -m unittest \
  tests/test_s22plus_magisk_boot_baseline_restore_gate.py
```

Result:

```text
Ran 7 tests in 0.014s
OK
```

## Next

To restore the measurement baseline, first insert the helper-generated active
exception into `AGENTS.md`, verify it with `--verify-agents-candidate`, then
wait for explicit operator live approval. If the device is already in Download
mode, use `--live-from-download`; if ADB is visible in Android, use
`--live-from-android`.
