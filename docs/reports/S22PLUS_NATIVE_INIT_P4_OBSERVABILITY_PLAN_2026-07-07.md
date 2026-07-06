# S22+ Native-Init P4 Observability Plan

Date: 2026-07-07 KST

Status: host-only plan. No S22+ live action is authorized until the current P3
boot candidate is rolled back to the pinned stock boot AP.

## Current Boundary

P3 live transferred the SHA-pinned direct-PID1 boot candidate successfully, but
the host did not observe Android ADB, TWRP/recovery ADB, Odin download mode, or a
Samsung USB device afterward.

Therefore the immediate device action remains fixed:

```text
Recover to TWRP/recovery or download mode.
Collect P3 evidence if recovery/ADB is available.
Restore pinned stock boot-only rollback AP.
Validate Android boot.
```

No P4 candidate may be flashed before that recovery step.

## Useful Facts From P0/P3

P0 confirmed that the S22+ stock kernel has:

```text
CONFIG_MODULES=y
CONFIG_DEVTMPFS is not set
CONFIG_PSTORE=y
CONFIG_PSTORE_CONSOLE=y
CONFIG_PSTORE_PMSG=y
CONFIG_PSTORE_RAM=y
/proc/filesystems includes pstore
```

Implications:

- Direct native PID1 should not expect Android-style USB/ADB to appear unless it
  brings up module loading, uevent/devnode handling, configfs, and adbd itself.
- P3 intentionally avoided that work and relied on `reboot(..., "recovery")` for
  observation. That observation path failed.
- pstore is the best existing forensic channel to check after physical recovery.

## Recovery-Time Evidence Gate

When any transport comes back, use:

```text
python3 workspace/public/src/scripts/revalidation/s22plus_p3_collect_and_rollback.py \
  --live \
  --ack S22PLUS-P3-COLLECT-AND-ROLLBACK
```

If ADB is available, it collects:

- selected boot/recovery properties,
- `/proc/last_kmsg`,
- `/sys/fs/pstore` listing and text,
- boot/recovery/vendor_boot/vbmeta/vbmeta_system read-only hashes where readable.

Then it reboots to download mode and delegates the stock boot rollback to:

```text
workspace/public/src/scripts/revalidation/s22plus_p2_stock_boot_rollback_guard.py
```

If Odin download mode is already available, it skips collection and performs only
the pinned stock boot rollback.

## Interpretation Matrix

| Evidence after recovery | Meaning | Next action |
| --- | --- | --- |
| `S22_NATIVE_INIT_DIRECT_P3` in last_kmsg/pstore | P3 `/init` executed; recovery reboot or USB observation failed | Build P4 around a stronger self-contained proof channel, not around boot format fixes |
| kernel panic/oops before `/init` marker | Boot image loaded but early userspace failed before marker or kernel rejected ramdisk/init | Fix boot/ramdisk/init packaging before more PID1 logic |
| no marker and no useful pstore/last_kmsg | Observation channel is too weak | Do not infer non-execution; add a deliberate pstore/panic or other non-USB proof |
| boot partition hash still equals P3 candidate | Failure is confined to boot candidate | Roll back stock boot, then redesign |
| recovery/vendor_boot/vbmeta changed unexpectedly | Safety incident | Stop and investigate before any further candidate work |

## P4 Candidate Direction After Rollback

The next boot artifact should be selected only after the evidence gate above.
Current preferred order:

1. **P4A pstore-first direct PID1 proof**:
   - direct `/init` writes high-priority kmsg/pstore markers,
   - uses pstore/ramoops as the primary proof,
   - does not depend on Android, Magisk, USB gadget, or automatic recovery ADB,
   - has a bounded terminal action that is recoverable by download mode.

2. **P4B corrected Magisk/Android observer wrapper**:
   - only if rooted Android observation is needed again,
   - first re-establish Magisk boot baseline after stock rollback,
   - redesign the wrapper from P2 instead of retrying it.

3. **P4C early USB gadget bring-up**:
   - larger unit, only after direct PID1 execution is proven,
   - must account for `CONFIG_DEVTMPFS is not set` and the S22+ module stack.

Do not start module bring-up or Stage-1 distro work until static `/init` PID1
first-light is proven.

## Stop Rule

The current P3 incident is still unrecovered. This plan is preparation only. Any
new boot flash requires:

1. successful stock boot rollback,
2. Android or recovery health evidence,
3. a new deterministic host-built artifact,
4. a new SHA-pinned `AGENTS.md` S22+ boot-only exception.
