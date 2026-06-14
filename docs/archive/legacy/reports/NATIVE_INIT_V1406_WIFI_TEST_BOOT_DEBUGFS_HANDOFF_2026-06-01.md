# Native Init V1406 Wi-Fi Test Boot Debugfs Handoff

## Summary

- Cycle: `V1406`
- Type: bounded live debugfs-prepared test-boot handoff with rollback
- Decision: `v1406-test-boot-rc1-ltssm-link-failed-no-l0-rollback-pass`
- Result: PASS for rollback/procedure; BLOCKED for Wi-Fi connect readiness
- Reason: test boot mounted debugfs and reached corrected RC1/LTSSM, then failed before L0/MHI/WLFW/`wlan0`; rollback verified
- Evidence: `tmp/wifi/v1406-wifi-test-boot-debugfs-handoff`
- Handoff/rollback pass: `True`
- Strict Wi-Fi progress mode: `True`
- Wi-Fi progress pass: `True`
- Connect ready: `False`
- Progress decision: `rc1-ltssm-link-failed-no-l0`

## Key Observations

- Test boot reached `A90 Linux init 0.9.72 (v1404-wifitest)`.
- PID1 prepared debugfs successfully: `debugfs prepare rc=0 mounted_by_pid1=1`.
- Summary showed `debugfs_mount_requested=1`, `debugfs_mounted_by_pid1=1`, and `debugfs_pci_msm_case_present=1`.
- The helper triggered corrected RC1 enumerate: dmesg contains `PCIe: TEST: 11`.
- RC1 reached PHY-ready and LTSSM states `DETECT_QUIET`, `POLL_ACTIVE`, and `POLL_COMPLIANCE`.
- RC1 then failed before L0: `PCIe RC1 link initialization failed (LTSSM_STATE:0x3)`.
- No MHI, WLFW, BDF/FW-ready, or `wlan0` marker appeared; `/sys/class/net/wlan0` stayed absent.
- The supervised helper timed out at `40s` (`helper_wait_rc=-110`, `helper_timed_out=1`) after the RC1 failure path.
- Rollback from native verified return to `A90 Linux init 0.9.68 (v724)`.

## Progress Classification

- `provider_trigger`: `True`
- `rc1_progress`: `True`
- `rc1_l0`: `False`
- `rc1_link_failed`: `True`
- `mhi_progress`: `False`
- `wlfw_progress`: `False`
- `bdf_progress`: `False`
- `fw_ready_progress`: `False`
- `wlan0_present`: `False`
- `connect_ready`: `False`

## Safety Scope

No Wi-Fi scan/connect, credential handling, DHCP/routes, external ping,
PMIC/GPIO/GDSC direct write, or blind eSoC notify/`BOOT_DONE` spoof was
performed by this runner. Device mutation was limited to flashing the V1404
test boot image and rolling back to `stage3/boot_linux_v724.img`.

## Images

- Test image: `tmp/wifi/v1404-wifi-test-boot-debugfs/boot_linux_v1404_wifi_test.img`
- Rollback image: `stage3/boot_linux_v724.img`

## Next

V1407 should be host-only: compare this V1406 boot-time RC1 failure against
Android and earlier V1370/V1371/V1372/V1391 RC1 evidence to choose the next
endpoint-readiness action. Do not proceed to scan/connect, credentials,
DHCP/routes, or external ping until MHI/WLFW/`wlan0` progress is proven.
