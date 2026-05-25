# Native Init V905 mdm_helper Runtime Repair Design Plan

## Goal

Classify whether the newly suggested Android dmesg/Magisk capture path should
become the next gate, or whether the newer V896-V904 evidence already narrows
the next unit to native `mdm_helper` runtime-input repair design.

## Inputs

- V895 MDM2AP IRQ snapshot proof.
- V896 Android `mdm_helper` / `ks` image-link contract classifier.
- V904 Android/native `mdm_helper` runtime-input parity classifier.
- V478-V487 SELinux context handoff reports.
- V860-V868 PeripheralManager and eSoC contract reports.
- Current helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`.

## Scope

- Host-only classifier.
- No device contact, Android boot, ADB command, Magisk module, actor start, live
  eSoC ioctl, subsystem open, daemon start, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, reboot, boot image write, partition write,
  firmware mutation, GPIO/sysfs/debugfs write, or Wi-Fi bring-up.

## Classification Questions

1. Does the Android dmesg/Magisk capture direction answer a still-open blocker,
   or did V896 already capture sufficient positive Android IRQ/PCIe evidence?
2. Is native SELinux domain transition a viable primary repair gate, given
   V478-V487 kernel-stuck evidence?
3. Can full PeripheralManager init-contract replay be repeated safely after V867
   produced `pm_proxy_helper` D-state?
4. Does current helper source already support the smallest next
   `mdm_helper` runtime-contract capture mode, or is a source/build unit needed?

## Success Criteria

- Produce a private manifest and summary under
  `tmp/wifi/v905-mdm-helper-runtime-repair-design/`.
- Produce a report under `docs/reports/`.
- Select exactly one next gate and record blocked/deprioritized alternatives.

## Expected Decision

If V896 is sufficient, V905 should not schedule a Magisk/Android dmesg recapture
as the immediate next unit. The likely next unit is V906 source/build-only helper
support for a fail-closed `mdm_helper` runtime-contract capture:

- add explicit `mdm_helper`/`ks` source context mappings;
- use existing property shim support;
- optionally order a light `pm-service` start before `mdm_helper`;
- exclude `pm_proxy_helper`;
- avoid controller `/dev/subsys_esoc0` open;
- observe only whether Android-equivalent actors naturally reach `/dev/esoc-0`,
  MHI, GPIO142, `mdm3`, WLFW/BDF, or `wlan0`.

