# S22+ Native-Init M17 Postmortem and Observation Plan - 2026-07-08

## Verdict

M17 is a useful negative result, but it is not a module-index proof.

The live result proves this external behavior:

```text
M13 no-module configfs floor  -> non-looping no-transport park
M15 two PHY-side modules      -> boot loop
M17 power/clock substrate+QMP -> boot loop
```

It does not prove that execution reached `phy-msm-ssusb-qmp.ko`. M17 writes
phase markers only to `/dev/kmsg`, and rollback found no retained M17 marker in
pstore or `last_kmsg`. With no retained marker, any reset before ACM can only
be placed somewhere inside the M17 runtime, not at a specific module.

Do not run another live S22+ native-init candidate until the next candidate has
a retained or host-observable progress channel stronger than "loop vs park".

## Evidence Reviewed

Reports:

```text
docs/reports/S22PLUS_NATIVE_INIT_M13_NOMODULE_CONFIGFS_LIVE_RESULT_2026-07-07.md
docs/reports/S22PLUS_NATIVE_INIT_M15_PHY_SPLIT_LIVE_RESULT_2026-07-08.md
docs/reports/S22PLUS_NATIVE_INIT_M17_POWER_QMP_LIVE_RESULT_2026-07-08.md
docs/reports/S22PLUS_NATIVE_INIT_M4T3_LIVE_RESULT_2026-07-07.md
docs/reports/S22PLUS_NATIVE_INIT_QMP_PHY_POWER_STEER_OPERATOR_2026-07-08.md
```

Source and build metadata:

```text
workspace/public/src/native-init/s22plus_init_usb_acm_m17_power_qmp_park.c
workspace/public/src/scripts/revalidation/build_s22plus_inplace_m17_power_qmp_park.py
workspace/public/src/scripts/revalidation/s22plus_m17_power_qmp_live_gate.py
workspace/private/outputs/s22plus_native_init/inplace_m17_power_qmp_v0_1/manifest.json
```

M17 main path:

```text
setup_minimal_fs()
emit(k_marker)                         -> /dev/kmsg only
load_power_qmp_modules()               -> 21 sequential finit_module calls
force_usb_roles_device()
create_acm_gadget()
serial_probe_loop()
```

M17 module order:

```text
01 clk-rpmh.ko
02 gcc-waipio.ko
03 icc-rpmh.ko
04 qcom_ipc_logging.ko
05 rpmh-regulator.ko
06 clk-dummy.ko
07 clk-qcom.ko
08 cmd-db.ko
09 debug-regulator.ko
10 gdsc-regulator.ko
11 icc-bcm-voter.ko
12 icc-debug.ko
13 minidump.ko
14 qti-fixed-regulator.ko
15 proxy-consumer.ko
16 qcom_rpmh.ko
17 qcom-scm.ko
18 sec_debug.ko
19 smem.ko
20 socinfo.ko
21 phy-msm-ssusb-qmp.ko
```

M17 live result:

```text
candidate Odin flash rc=0
bounded observation: no ACM, no ADB, no Odin
operator visual: boot loop
manual download-mode rollback rc=0
Android returned
Magisk root available
boot hash restored to the pinned Magisk baseline
retained M17 markers: none
```

## What M17 Proves

M17 falsifies the simple "M15 only failed because QMP was naked" branch.

The candidate added the expected recovery-order power/clock substrate closure
before `phy-msm-ssusb-qmp.ko`, excluded watchdog modules, used the stable M13
no-module floor, and still looped.

M17 also proves that the current `/dev/kmsg` marker strategy is insufficient
for this reset class. It may be useful when the device later reaches Android,
ACM, or pstore, but this path leaves no retained phase line after rollback.

## What M17 Does Not Prove

M17 does not identify the failing module.

The failure could be:

```text
before the first marker survives anywhere
during one of module indices 1..20 in the substrate
during the QMP module at index 21
after the module loop but before ACM enumeration
```

The last branch is less likely because no ACM, ADB, or Odin appeared during the
bounded observation, but the current evidence cannot rule it out. The next
candidate must make the boundary observable.

## Observation Upgrade Options

### Option A: UART Console

Preferred when the physical path is available.

Required proof before another native-init live flash:

```text
host captures a live kernel console stream from the S22+ boot path
the stream is tied to the same candidate boot attempt, not a later Android log
panic/oops/reset output can be captured without relying on pstore
operator can still enter download mode and rollback if the candidate loops
```

Why this is best: a bus abort, regulator/GDSC/clock failure, BUG, panic, or
watchdog reset should name the faulting subsystem directly. That is the only
path that can turn a loop into a single-run root cause.

No new boot artifact is needed for the first UART readiness check.

### Option B: Prefix-Download Discriminator

Fallback if UART is not ready.

Use the already live-proven M4T3 external proof channel: a custom raw/static
PID1 can call `reboot(..., "download")`, and the host can observe the later
download-mode endpoint. Build a host-only M18 family from the M13 floor:

```text
setup minimal fs
load first N entries of the M17 module list
if execution reaches the checkpoint, immediately reboot("download")
```

Interpretation:

```text
self-download appears       -> prefix 1..N did not reset before checkpoint
no self-download / loop     -> reset occurred inside prefix 1..N or earlier setup
```

Run as a bounded binary search, not broad add-back:

```text
M18P00  N=0   proves the M13 setup + checkpoint-download path still works
M18P10  N=10  splits substrate lower half
M18P16  N=16  narrows high substrate
M18P20  N=20  proves substrate before QMP
M18P21  N=21  isolates QMP if P20 passes and P21 loops
```

The exact next N should be selected from the first passing/failing pair. Every
prefix AP must be SHA-pinned, boot-only, separately gated, and rolled back to
the pinned Magisk baseline after each live run.

This is not another blind module-subset permutation: every candidate has a
specific host-observable checkpoint and a monotonic prefix relation.

## Next Unit

No live flash is authorized by this report.

Next bounded unit should be one of:

```text
UART path available:
  host-only UART readiness checklist + capture procedure, then supervised capture

UART path unavailable:
  host-only M18 prefix-download discriminator build design, starting with P00
  and P10 artifacts only, plus dry-run helper; live gate only after a fresh
  SHA-pinned AGENTS.md exception
```

Keep all existing S22+ constraints: boot-only AP, no forbidden partitions, no
raw host partition writes, no fastboot, attended ack for any live flash, and
pinned Magisk boot-only rollback.
