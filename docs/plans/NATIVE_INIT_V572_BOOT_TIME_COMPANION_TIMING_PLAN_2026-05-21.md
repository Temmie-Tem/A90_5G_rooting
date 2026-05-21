# Native Init V572 Boot-Time Companion Timing Plan

Date: `2026-05-21`

## Goal

V572 defines the next safe step after V570/V571:

- V570 proved the `rmt_storage` and `tftp_server` Android runtime identity
  mismatch is fixed in helper v94, but `IWifi.start()` still returns
  `ERROR_UNKNOWN/9` and `QIPCRTR` sockets stay `0`.
- V571 proved current native init has the `QIPCRTR` protocol registered, but
  never enters the Android-observed QRTR/service-notifier/WLAN-PD/QMI readiness
  sequence.
- The strongest remaining hypothesis is timing/order: the companion service
  window is being started too late from an interactive helper, while Android
  reaches modem readiness during early boot.

V572 should therefore move from a late interactive proof to a bounded,
opt-in boot-time companion timing proof.

## Version Scope

- Cycle label: `v572`
- Current native build: `A90 Linux init 0.9.61`
- Current device build tag: `v319`
- Current boot image: `stage3/boot_linux_v319.img`
- Planned boot artifact change: yes, only if implementation proceeds
- Planned native numeric build if PID1 changes: next numeric native build
  after `0.9.61`

Per `docs/operations/VERSIONING_POLICY.md`, the `v572` cycle label does not by
itself mean the device image changed. If PID1 boot hooks are implemented and
flashed, the numeric native build version must be bumped and the boot image
artifact/SHA256 must be recorded.

## Non-Goals

- no supplicant or hostapd;
- no Wi-Fi scan, connect, link-up, credential use, DHCP, route change, or
  external ping;
- no Wi-Fi HAL start in the first boot-time timing proof;
- no QMI payload beyond already-used QRTR nameservice readback;
- no persistent broad network exposure;
- no destructive deletion or unclear partition writes.

## Current Boot Flow Finding

The active native boot image is assembled from
`stage3/linux_init/init_v319.c`, which includes `stage3/linux_init/v319/*.inc.c`.

Relevant boot sequence in `stage3/linux_init/v319/90_main.inc.c`:

1. base mounts: `/proc`, `/sys`, `/dev`, `/tmp`, `/cache`;
2. cache mount and log handoff;
3. storage probe and runtime root initialization;
4. helper/userland inventory;
5. ACM USB gadget setup and boot selftest;
6. `/dev/ttyGS0` wait and console attach;
7. `autohud`;
8. optional NCM/tcpctl `netservice`;
9. interactive shell loop.

There is currently no boot-time hook that mounts Android system/vendor runtime
surfaces and starts Wi-Fi companion daemons before the serial console path.

## Required Precondition Analysis

The helper v94 path is safer than porting Android exec namespace logic into
PID1 because it already handles:

- private mount namespace;
- `/vendor` read-only `sda29` mount with `noload`;
- private `/proc` mount inside the helper namespace;
- linkerconfig/APEX materialization;
- binder/hwbinder/vndbinder device materialization;
- private property root;
- Android-observed service identity contracts for `rmt_storage` and
  `tftp_server`;
- bounded child cleanup and transcript capture.

However, a reboot loses live-only setup from earlier proofs. A boot-time proof
must explicitly account for:

- `/mnt/system/system` readiness from read-only `sda28` mount;
- `/sys/fs/selinux` availability;
- Android SELinux policy load state if service domain transitions are required;
- helper v94 presence and SHA256 under `/cache/bin/a90_android_execns_probe`;
- private property root presence under
  `/mnt/sdext/a90/private-property-v317/v535/dev/__properties__`.

Directly starting companion daemons at boot without those checks would make
failures ambiguous and could leave residue before serial control is available.

## Proposed Design

Implement V572 as a disabled-by-default PID1 boot probe, not as an automatic
Wi-Fi bring-up.

### Boot Flag

Use an explicit opt-in flag, for example:

```text
/cache/native-init-wifi-bootprobe
```

If the flag is absent, boot behavior remains identical to v319.

### Hook Point

Run the hook after:

- `/cache` is mounted;
- storage probe and runtime initialization have completed;
- helper inventory has run;
- before ACM USB gadget setup if the goal is true early timing;
- with a hard timeout and fail-open path back to normal native boot.

This places the proof earlier than the current interactive/NCM helper window,
while preserving a bounded fallback into the existing console and recovery
flow.

### Boot Hook Action

If the flag is present:

1. mount or verify Android system root read-only with existing
   `prepare_android_layout(false)` or a narrower read-only system mount helper;
2. verify `/cache/bin/a90_android_execns_probe` exists, is executable, and
   matches the expected helper v94 SHA256;
3. verify private property root exists and is not a symlink;
4. verify `/sys/fs/selinux/status` exists, or classify as
   `bootprobe-selinuxfs-missing`;
5. run helper v94 in companion-only mode with no HAL:

```text
/cache/bin/a90_android_execns_probe
  --system-root /mnt/system/system
  --vendor-block /dev/block/sda29
  --vendor-fstype ext4
  --mode wifi-companion-start-only
  --timeout-sec 10
  --allow-cnss-start-only
  --allow-wifi-companion-start-only
  --allow-qrtr-ns-readback
  --property-root /mnt/sdext/a90/private-property-v317/v535/dev/__properties__
```

6. append stdout/stderr to a private runtime log, for example
   `/mnt/sdext/a90/logs/wifi-bootprobe-v572.log` or cache fallback equivalent;
7. kill the helper process group on timeout;
8. record timeline and kmsg labels;
9. always continue into the normal native boot path.

### SELinux Policy Gate

Do not fold policy loading silently into the companion proof.

V572 should classify SELinux as one of:

- `selinuxfs-present-policy-current`: SELinuxfs visible and service contexts
  are usable;
- `selinuxfs-present-policy-missing`: SELinuxfs visible but service-domain
  transition evidence is missing;
- `selinuxfs-missing`: boot hook must not start companion daemons;
- `policy-load-required`: separate boot-time policy-load plan needed before
  companion retry.

If policy loading at boot is required, it should be a separate opt-in unit
because writing `/sys/fs/selinux/load` is a global policy mutation.

## Classification Criteria

Acceptable V572 outcomes:

| decision | meaning |
|---|---|
| `v572-bootprobe-disabled` | flag absent; boot unchanged |
| `v572-bootprobe-precondition-blocked` | helper/system/property/SELinux precondition missing; no daemon started |
| `v572-bootprobe-companion-window-pass` | companion-only boot window ran, cleaned up, and normal native boot continued |
| `v572-bootprobe-qrtr-progress` | boot-time window produced nonzero QRTR/service-notifier/WLAN-PD/QMI/BDF/FW marker |
| `v572-bootprobe-not-sufficient` | boot-time companion-only window still produced `QIPCRTR` sockets `0` and no readiness markers |
| `v572-bootprobe-cleanup-review` | child cleanup was not proven; stop further Wi-Fi work and use recovery/rollback if needed |

Success for V572 is not Wi-Fi connectivity. Success is narrowing whether early
boot timing changes the QRTR/modem readiness surface.

## Validation Plan

Static/local:

```text
git diff --check
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra ...
strings stage3/linux_init/init_<next> | rg 'A90 Linux init|wifi-bootprobe|native-init-wifi-bootprobe'
```

Artifact:

- build a new ramdisk and boot image from the verified v319 boot image
  arguments, replacing only `/init`;
- record SHA256 for init, ramdisk, and boot image;
- record known-good rollback image `stage3/boot_linux_v319.img`.

Live:

1. verify current native state with `version`, `status`, `selftest`;
2. deploy helper v94 if needed and verify SHA256;
3. create bootprobe flag only after helper and rollback path are verified;
4. flash the new boot image through `scripts/revalidation/native_init_flash.py`;
5. verify native boot reaches serial/NCM again;
6. collect:
   - `version`
   - `bootstatus`
   - `timeline`
   - `logpath`
   - `dmesg` filtered for QRTR/QMI/CNSS/WLFW/BDF/WLAN markers
   - bootprobe log
   - process residue
   - `/proc/net/protocols`, `/proc/net/netlink`, `/proc/net/dev`
7. remove the bootprobe flag and reboot/rollback if cleanup is not proven.

## Safety Boundaries

- The bootprobe flag must be absent by default.
- The hook must use a hard timeout.
- The hook must kill the helper process group on timeout.
- The hook must fail open into normal native boot.
- No scan/connect/link-up is allowed in V572.
- No Wi-Fi credentials are read in V572.
- No boot image flash is accepted without artifact SHA256, target partition,
  and rollback image recorded.
- Bypass mode may cover patch upload, boot image flash, reboot, and rollback
  verification only within `docs/operations/DEVELOPMENT_LOOP_STANDARD.md`.

## Next Implementation Unit

The next code unit should be small:

1. add constants for the bootprobe flag and log path;
2. add a `wifi_bootprobe_enabled()` check;
3. add a bounded `a90_run` wrapper that runs helper v94 in
   `wifi-companion-start-only`;
4. call it at the selected hook point only when the flag is present;
5. add timeline/kmsg/log evidence;
6. build a new native boot artifact and run disabled-flag smoke first.

Only after the disabled-flag boot proves unchanged behavior should the opt-in
bootprobe flag be enabled for a live companion-only timing proof.

