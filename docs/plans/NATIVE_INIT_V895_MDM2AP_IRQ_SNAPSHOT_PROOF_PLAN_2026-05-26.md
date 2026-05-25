# V895 MDM2AP IRQ Snapshot Proof Plan

## Goal

Prove whether the MDM2AP status IRQ fires after the guarded
`ESOC_IMG_XFER_DONE` response selected by V888/V891/V893.

## Inputs

- V894 ready-surface evidence:
  `tmp/wifi/v894-mdm2ap-ready-surface/manifest.json`
- helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`
- helper deploy wrapper:
  `scripts/revalidation/wifi_execns_helper_v143_deploy_preflight.py`
- live runner:
  `scripts/revalidation/native_wifi_mdm2ap_irq_snapshot_v895.py`

## Method

1. Extend helper `v143` with read-only `/proc/interrupts` parsing for the
   `msmgpio-dc 142 Edge mdm status` line.
2. Capture IRQ snapshots before `ESOC_IMG_XFER_DONE`, immediately after it,
   during `ESOC_GET_STATUS` polling, and after the polling window.
3. Keep the existing V891 gate: `REG_REQ_ENG`, wait for `ESOC_REQ_IMG`,
   `ESOC_IMG_XFER_DONE`, poll `ESOC_GET_STATUS`, and send `ESOC_BOOT_DONE`
   only if status becomes ready.
4. Deploy helper `v143` separately from the live eSoC proof.
5. Reboot-clean the device if the subsystem-open child is not proven stopped.

## Hard Gates

- No `REG_CMD_ENG`.
- No direct userspace `CMD_EXE`.
- No explicit userspace `PWR_ON`.
- No blind `ESOC_BOOT_DONE`.
- No GPIO export/write, debugfs write, sysfs write, actor start, Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, external ping, module load/unload,
  boot image write, partition write, firmware mutation, or Wi-Fi link-up.

## Success Criteria

- Helper `v143` builds as static AArch64 and exposes the IRQ snapshot markers.
- Helper `v143` deploys with remote sha/mode parity.
- Live proof records parsed GPIO `142` IRQ snapshots across the image-done
  window.
- Cleanup reboot restores `bootstatus` and `selftest fail=0`.
- The result classifies either:
  - IRQ fired but status stayed not-ready, or
  - IRQ did not fire, meaning SDX50M did not drive MDM2AP status high.

## Next

If the IRQ does not fire, V896 should be host-only and classify the missing
Android-side image-transfer/MDM helper contract before any broader live retry.
