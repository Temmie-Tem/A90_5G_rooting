# Native Init V630 Sibling-SSCTL Boot-Window Proof Plan

- date: `2026-05-23 KST`
- cycle: `v630`
- native build: `A90 Linux init 0.9.65 (v630)`
- scope: opt-in boot-image proof
- target: test the Android-equivalent ADSP/CDSP/SLPI sibling SSCTL trigger in a
  safer boot window, then use the result to decide whether service `74`,
  WLAN-PD, and WLFW can advance before Wi-Fi HAL work.

## Background

V629 selected the next gate:

```text
Android visible trigger: early-boot ADSP/CDSP/SLPI boot-node writes
Native v319: no equivalent boot-time path
V627: warning-free service-locator + service-notifier 180 only
V619: late direct writes exposed sibling sysmon but produced warnings and no service 74
```

V572 also set a safety constraint. A pre-ACM PID1 bootprobe can block before USB
returns, making host recovery difficult. V630 therefore does not run a helper
before ACM. It runs only after `/dev/ttyGS0` is available and the console has
attached.

## Design

V630 adds a disabled-by-default one-shot proof:

- arm flag: `/cache/native-init-sibling-ssctl-v630`
- required flag content: `run`
- proof log: `/cache/native-init-sibling-ssctl-v630.log`
- write targets:
  - `/sys/kernel/boot_adsp/boot`
  - `/sys/kernel/boot_cdsp/boot`
  - `/sys/kernel/boot_slpi/boot`
- execution point: after USB ACM console attach, before auto-HUD/netservice
- timeout: `5000ms`
- isolation: forked child does the sysfs writes; PID1 waits with timeout,
  kills on timeout, records evidence, and continues to shell
- one-shot behavior: the arm flag is removed before any write is attempted

## Guardrails

V630 must not:

- start service-manager, CNSS, Wi-Fi HAL, supplicant, or hostapd;
- touch `boot_wlan`, `qcwlanstate`, or `shutdown_wlan`;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally;
- run pre-ACM helper code;
- keep repeating the proof after failure or reboot.

## Build Contract

The builder is:

```text
scripts/revalidation/build_native_init_boot_v630.py
```

It recompiles `stage3/linux_init/init_v630.c`, repacks a ramdisk with the V319
trusted helper layout, and reuses the verified V319 boot image header/kernel
arguments while replacing only the ramdisk.

Expected local artifacts are ignored by git:

- `stage3/linux_init/init_v630`
- `stage3/ramdisk_v630/`
- `stage3/ramdisk_v630.cpio`
- `stage3/boot_linux_v630.img`

## Live Gate

1. Disabled-smoke flash with the flag absent.
2. Verify `A90 Linux init 0.9.65 (v630)` returns through cmdv1.
3. Arm `/cache/native-init-sibling-ssctl-v630` with exact content `run`.
4. Reboot V630 once to run the proof.
5. Collect:
   - `version`
   - `status`
   - `timeline`
   - `dmesg`/kmsg markers for `A90v630`, `sysmon-qmi`,
     `service-notifier`, WLAN-PD, WLFW, BDF, and kernel warnings
   - `/cache/native-init-sibling-ssctl-v630.log`
6. Roll back to `stage3/boot_linux_v319.img`.

## Success Criteria

V630 passes if it classifies one of these outcomes with rollback completed:

- `v630-service74-advanced`
- `v630-sibling-sysmon-only`
- `v630-boot-window-warning-blocked`
- `v630-proof-timeout-rollback-complete`
- `v630-disabled-smoke-only`

Wi-Fi final success remains separate and requires native Wi-Fi association plus
`google.com` ping. V630 does not authorize credentials or external ping by
itself.

