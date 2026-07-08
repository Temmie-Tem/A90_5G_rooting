# S22+ Native-Init M28 S24 Retained-Log Postmortem (2026-07-08)

## Verdict

HOST-ONLY POSTMORTEM COMPLETE / S24 FAILURE NOT CAPTURED / NEXT UNIT MUST
IMPROVE CANDIDATE-OWNED EVIDENCE.

The retained `/proc/last_kmsg` collected after the M28 `S24` rollback is not a
usable log of the direct native-init `S24` failure. It contains the later
Magisk-rollback Android boot and the helper-driven `reboot,download` used for
stock-DTBO restore. Therefore the M28 `S24` failure mechanism remains
unobserved.

Do not run `F43` and do not rerun M28 under the consumed exception.

## Inputs

Run directory:

```text
workspace/private/runs/s22plus_m28_dep_complete_live_gate_20260708T143115Z/
```

Primary log:

```text
workspace/private/runs/s22plus_m28_dep_complete_live_gate_20260708T143115Z/s22plus_m28_dep_complete_live_gate.txt
```

Retained log:

```text
workspace/private/runs/s22plus_m28_dep_complete_live_gate_20260708T143115Z/android_pstore/post_m28_S24_rollback_last_kmsg.bin
```

Retained log shape:

```text
file: ASCII text
size: 2097136 bytes
```

No new flash or device mutation was performed for this postmortem.

## Run-Fact Recap

The helper flashed `S24`, observed the original Odin device disconnect, then
observed an Odin endpoint at sample 033:

```text
m28-S24-post-candidate-disconnect_odin_absent=1
m28_S24_self_download_032-odin devices=[]
m28_S24_self_download_033-odin devices=['/dev/bus/usb/...']
m28_S24_self_download_seen=1
m28_S24_result=self-download
```

The operator reported bootloop observation followed by manual Download-mode
entry during the observation window. That operator report overrides the helper's
raw endpoint classification: this is manual-download contaminated, not clean
S24 self-download proof.

Rollback completed:

```text
S24_magisk_boot_rollback_odin_rc=0
stock_dtbo_rollback_odin_rc=0
```

The helper also recorded that no retained candidate marker was found:

```text
post_m28_S24_rollback_pstore_files=[]
post_m28_S24_rollback_last_kmsg_rc=0
post_m28_S24_rollback_last_kmsg_bytes=2097136
post_m28_S24_rollback_last_kmsg_marker_found=0
post_m28_S24_rollback_retained_marker_found=0
m28_S24_capture_marker_found=0
```

## Retained-Log Findings

Searches for the candidate marker and module-load failure signals found no
useful M28/S24 evidence:

```text
S22_NATIVE: no hit
M28 / m28: no candidate hit
insmod: no hit
Unknown symbol: no hit
Kernel panic: no hit
Unable to handle: no hit
clk-rpmh: no hit
abc.ko: no hit
```

The retained log does show an Android userspace reboot to Download mode:

```text
[   26.138694] init: Received sys.powerctl='reboot,download' from pid: 5464 (/system/bin/reboot)
[   26.139257] init: Got shutdown_command 'reboot,download' Calling HandlePowerctlMessage()
[   26.139282] init: [PDP] S_D_ R_B_ TGT= download
[   26.139757] init: ####Reboot start, reason: reboot,download, reboot_target: download
```

That sequence matches the helper's later Android/Magisk rollback path for stock
DTBO restore, not direct native-init `S24` execution.

The log also contains bootloader/download-mode traces:

```text
[    4.354147] init: [softdog] /metadata/bootstat/persist.sys.boot.reason : reboot,download
[BLDP] bootloader_mode = 1
[BLDP] bootloader_mode = 0
```

Observed call traces are Android rollback-boot diagnostics, not candidate
crash evidence:

```text
rtnl_lock: __rtnl_unlock: kworker/5:3 took 1424 msec to unlock
rtnl_lock: __rtnl_unlock: wifi@1.0-servic took 1316 msec to unlock
glink_subdev_stop ... during shutdown/reboot
```

The repeated `Minidump: Entry name already exist` / `usb_ffs_* ret -17` lines
also occur during the later Android boot path and do not identify the `S24`
native-init failure.

## Source-Shape Note

`s22plus_init_m28_dep_complete_download.c` writes M28 progress only to
`/dev/kmsg`. It emits:

```text
phase=mounts
phase=module ... index=N ... name=...
phase=modules_load_done
phase=checkpoint ... action=reboot_download
```

It does not write a durable `/dev/pmsg0` marker. Because the collected
`last_kmsg` appears to be the rollback Android boot, marker absence cannot
distinguish:

1. the direct native-init `/init` never executed,
2. `/init` executed but `/dev/kmsg` output was not retained,
3. `/init` executed and faulted before the first retained candidate line,
4. the retained buffer was overwritten by later rollback/stock-DTBO activity.

## Decisions

- M28 `S24` remains a no-proof/manual-download-contaminated result.
- M28 one-shot authorization is consumed and must not be reused.
- `F43` is not authorized.
- The next unit should be host-only design for a fresh M29 candidate, not a live
  flash.
- M29 must improve candidate-owned evidence before broad module loading. At
  minimum it should add a durable marker path, explicitly separate PID1-entry
  proof from module-loop proof, and report per-module progress in a way that is
  more likely to survive rollback collection.

