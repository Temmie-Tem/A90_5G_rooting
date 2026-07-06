# S22+ Native-Init M3.2 Live Incident - 2026-07-07

## Summary

- Candidate: S22+ M3.2 marker-only direct-PID1 native-init.
- Candidate AP SHA256:
  `6073e4988a98f741fa207df4efb8a05e144ad16b3a90f43db2ec408657936fc2`.
- Candidate boot image SHA256:
  `0bb1ef280e42aa2c6069538e77fc21b5330cf9419a19785f79d05da8429bf1fc`.
- Helper:
  `workspace/public/src/scripts/revalidation/s22plus_m32_marker_live_gate.py`.
- Private run log:
  `workspace/private/runs/s22plus_m32_marker_live_gate_20260706T190546Z/`.
- Incident: candidate boot-only Odin flash succeeded, but the candidate never
  returned to host-visible ADB or Odin download mode during the bounded
  observation and rollback windows. Host-side rollback could not run because the
  device became USB-invisible.
- Recovery status: the operator confirmed a bootloop and manually entered
  download mode. Codex then flashed the pinned Magisk boot-only rollback AP.
  Android returned with boot completed, `boot_recovery=0`, orange verified
  boot, and Magisk root.
- Current status after rollback: recovered to rooted Android baseline. No
  further S22+ native-init candidate flash is allowed until the M3.2 incident is
  analyzed and a new non-self-reboot proof channel is designed.

## Preflight

The helper verified:

- current Android baseline: `SM-S906N` / `g0q` / `S906NKSS7FYG8`,
  boot completed, orange verified boot, Magisk root;
- M3.2 candidate AP hash and single `boot.img.lz4` tar member;
- M3.2 legacy-LZ4 ramdisk manifest metadata;
- pinned Magisk boot-only rollback AP SHA256:
  `d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56`;
- pinned stock boot-only fallback AP SHA256:
  `1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e`;
- `AGENTS.md` M3.2 boot-only exception markers.

## Live Result

- `adb reboot download` returned success.
- Odin download mode appeared for candidate flashing.
- Candidate flash command used only the AP slot with the exact M3.2 boot-only
  AP.
- Odin reported candidate transfer success and rebooted the device.
- During the candidate observation window, repeated host snapshots showed:
  no Android ADB device and no Odin download device.
- During the rollback wait window, repeated Odin polling also showed no
  download-mode device.
- After the helper exited, manual host polling still showed no Android ADB
  device and no Odin device. `lsusb` showed no Samsung/S22+ USB endpoint.

## Evidence Interpretation

This run does not prove the M3.2 marker-only `/init` executed. It also does not
prove it did not execute. At helper exit, rollback had not run and no retained
evidence was available. After the operator manually entered download mode and
Codex restored the Magisk boot-only AP, `/proc/last_kmsg` was collectable but
did not contain the M3.2 marker.

The important new fact is narrower and stronger: stock-format legacy-LZ4 ramdisk
packaging did not restore the intended self-return-to-download behavior. The
direct-PID1 path still strands the device outside host-visible USB transports.

## Recovery Result

The operator manually forced Samsung download mode after confirming the bootloop.
Host checks then saw one Odin device. Codex verified the pinned rollback APs:

```text
magisk_boot_rollback_sha256=d2373bf88dda342709440dc3db468f11d80a4593856768a4d8ae402bef215a56
stock_boot_fallback_sha256=1ee92a86f30e4acb12509272630e1bef5215d1a12686ac69a3b399b43740535e
```

Both rollback APs contained exactly one `boot.img.lz4` member. Codex flashed
the Magisk boot-only AP with:

```text
/usr/bin/odin4 --reboot -a \
  workspace/private/outputs/s22plus_magisk_root_boot_only/AP.tar.md5
```

Odin returned rc 0 and transferred only `boot.img.lz4`. Android then returned:

```text
boot_completed=1
boot_recovery=0
model=SM-S906N
device=g0q
bootloader=S906NKSS7FYG8
verified_boot=orange
magisk_root=uid 0
```

Post-rollback retained evidence was captured privately:

```text
workspace/private/runs/s22plus_m32_post_rollback_capture_20260706T191347Z/
```

Summary:

- `/proc/last_kmsg` was readable at 2,097,136 bytes;
- `S22_NATIVE_INIT` and `S22_NATIVE_INIT_MARKER_ONLY_M32` were not found;
- `Kernel panic`, `not syncing`, `Unable to mount root`, and `Oops` were not
  found;
- retained bootloader logs showed repeated ABL `reboot_reason = 0x9` entries
  and a download-mode image load record.

## Manual Recovery Procedure If This Repeats

1. Force the phone into Samsung download mode.
2. Once `/usr/bin/odin4 -l` shows one device, flash only the pinned Magisk
   boot-only rollback AP:

   ```text
   /usr/bin/odin4 --reboot -a \
     workspace/private/outputs/s22plus_magisk_root_boot_only/AP.tar.md5
   ```

3. If Magisk rollback fails but download mode remains available, use the pinned
   stock boot-only fallback AP:

   ```text
   /usr/bin/odin4 --reboot -a \
     workspace/private/outputs/s22plus_native_init/odin4_stock_rollback_short/AP.tar.md5
   ```

4. After Android returns, verify boot completed, `boot_recovery=0`, orange
   verified boot, and Magisk root if the Magisk rollback path was used.
5. Then collect `/sys/fs/pstore` and `/proc/last_kmsg` before any further live
   native-init experiment.

## Stop Rule

No more S22+ native-init candidate flashes on the current design. M3.2 proves
that stock-format legacy-LZ4 ramdisk packaging alone does not make the direct
PID1 marker candidate self-return to download mode. The next design must avoid
relying on candidate self-reboot or Android/USB visibility as the first proof
channel.
