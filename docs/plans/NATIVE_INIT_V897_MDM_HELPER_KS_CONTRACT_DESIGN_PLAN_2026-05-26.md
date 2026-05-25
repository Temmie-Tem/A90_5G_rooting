# V897 Native mdm_helper/ks Contract Design Plan

## Goal

Classify, host-only, the smallest safe native contract needed to mirror
Android's `mdm_helper` / `ks` SDX50M image/link path before any new live actor
start.

## Inputs

- Android image/link contract classifier:
  `tmp/wifi/v896-android-mdm-helper-image-contract/manifest.json`
- Earlier service-gated `mdm_helper` attempt:
  `tmp/wifi/v764-mdm-helper-service180-retry/manifest.json`
- eSoC node parity proof:
  `tmp/wifi/v855-esoc-node-parity-preflight/manifest.json`
- PeripheralManager init-contract negative/cleanup proof:
  `tmp/wifi/v867-pm-init-contract-live-r3/manifest.json`
- Native MDM2AP IRQ negative control:
  `tmp/wifi/v895-mdm2ap-irq-snapshot-live/manifest.json`
- Current helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`

## Method

1. Confirm V896 proves Android reaches GPIO 142 IRQ, `mdm3=ONLINE`, WLFW/BDF,
   and `wlan0` while `mdm_helper` and `ks` hold `/dev/esoc-0`.
2. Confirm V895 proves native immediate `ESOC_IMG_XFER_DONE` leaves GPIO 142
   IRQ delta at `0`.
3. Confirm V764's old service-gated `mdm_helper` path did not advance lower
   state.
4. Confirm V855 already proves `/dev/esoc-0`, `/dev/subsys_esoc0`, and
   `/dev/subsys_modem` node parity can be materialized and cleaned.
5. Inspect the current helper for existing old service-gated modes and absence
   of a distinct pre-subsys `mdm_helper`/`ks` image-contract mode.

## Required Contract

1. Materialize Android-equivalent `/dev/esoc-0`, `/dev/subsys_esoc0`, and
   `/dev/subsys_modem`.
2. Start `/vendor/bin/mdm_helper` before opening `/dev/subsys_esoc0`.
3. Do not `REG_REQ_ENG` or send `ESOC_NOTIFY` from the controller in this
   mode; let `mdm_helper` own `/dev/esoc-0` request handling.
4. Open `/dev/subsys_esoc0` only after `mdm_helper` is observable, in a bounded
   child with explicit cleanup/reboot-required classification.
5. Observe whether `mdm_helper` spawns `ks` and whether `ks` uses
   `/dev/mhi_0305_01.01.00_pipe_10`.
6. Treat private `/dev` MHI pipe visibility or mirroring as an explicit
   implementation requirement before live proof.

## Hard Gates

- No device contact, Android boot, ADB command, Magisk module, live eSoC ioctl,
  `/dev/subsys_esoc0` open, actor start, `mdm_helper` start, `ks` start,
  daemon start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external
  ping, GPIO/sysfs/debugfs write, boot image write, partition write, firmware
  mutation, or Wi-Fi link-up.

## Success Criteria

- Host-only classifier writes private evidence.
- Decision records whether a new helper image-contract mode is required.
- The next implementation step is source/build-only, not live actor start.

## Next

If the helper lacks the contract, V898 should add a fail-closed
`mdm_helper`/`ks` image-contract helper mode source/build-only. Deploy and live
execution remain separate gates.
