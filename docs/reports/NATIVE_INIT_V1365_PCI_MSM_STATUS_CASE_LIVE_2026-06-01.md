# Native Init V1365 pci-msm Status-only Case Live

## Summary

- Cycle: `V1365`
- Type: bounded live status-only proof
- Decision: `v1365-case26-transport-reset-reboot-risk`
- Result: FAIL
- Script: `scripts/revalidation/native_wifi_pci_msm_status_case_live_v1365.py`
- Evidence:
  - `tmp/wifi/v1365-pci-msm-status-case-live/manifest.json`
  - `tmp/wifi/v1365-pci-msm-status-case-live/summary.md`
  - `tmp/wifi/v1365-pci-msm-status-case-live/native/`

## Decision

case=26 status-only proof caused command transport loss before after-captures completed

## Post-run Recovery Check

A separate manual health check after the transport loss returned native
`selftest` with `fail=0`. This recovery check is outside the V1365 captured
window and does not turn V1365 into a PASS; it only confirms the device returned
to a healthy native state after the failed proof.

## Key Observations

| field | value |
| --- | --- |
| mounted_before | False |
| mounted_by_v1365 | True |
| mounted_during | True |
| mounted_after | None |
| cleanup_ok | None |
| write_ok | False |
| before_pci_count | 0 |
| after_pci_count | None |
| before_mhi_present | False |
| after_mhi_present | None |
| gdsc_changed | None |
| clk_changed | None |
| pcie_link_seen | False |
| enumerate_seen | False |
| post_selftest_fail0 | False |
| reset_after_write | True |
| after_captures_ok | False |

## Captures

| name | ok | rc | status | file |
| --- | --- | --- | --- | --- |
| version | True | 0 | ok | native/version.txt |
| selftest | True | 0 | ok | native/selftest.txt |
| status | True | 0 | ok | native/status.txt |
| mounts-before | True | 0 | ok | native/mounts-before.txt |
| debugfs-mount | True | 0 | ok | native/debugfs-mount.txt |
| mounts-during | True | 0 | ok | native/mounts-during.txt |
| pci-msm-find | True | 0 | ok | native/pci-msm-find.txt |
| pci-msm-case-read | True | 0 | ok | native/pci-msm-case-read.txt |
| before-regulator-pcie | True | 0 | ok | native/before-regulator-pcie.txt |
| before-clk-pcie | True | 0 | ok | native/before-clk-pcie.txt |
| before-gpio-pcie | True | 0 | ok | native/before-gpio-pcie.txt |
| before-pci-devices | True | 0 | ok | native/before-pci-devices.txt |
| before-mhi-devices | True | 0 | ok | native/before-mhi-devices.txt |
| before-interrupts | True | 0 | ok | native/before-interrupts.txt |
| before-dmesg-pcie-tail | True | 0 | ok | native/before-dmesg-pcie-tail.txt |
| write-rc1-case26-status-only | False | None | missing | native/write-rc1-case26-status-only.txt |
| settle | False | None | missing | native/settle.txt |
| after-regulator-pcie | False | None | missing | native/after-regulator-pcie.txt |
| after-clk-pcie | False | None | missing | native/after-clk-pcie.txt |
| after-gpio-pcie | False | None | missing | native/after-gpio-pcie.txt |
| after-pci-devices | False | None | missing | native/after-pci-devices.txt |
| after-mhi-devices | False | None | missing | native/after-mhi-devices.txt |
| after-interrupts | False | None | missing | native/after-interrupts.txt |
| after-dmesg-pcie-tail | False | None | missing | native/after-dmesg-pcie-tail.txt |
| debugfs-umount | False | None | missing | native/debugfs-umount.txt |
| mounts-after | False | None | missing | native/mounts-after.txt |
| post-selftest | False | None | missing | native/post-selftest.txt |
| post-status | False | None | missing | native/post-status.txt |

## Safety

- V1365 writes only `rc_sel=1` and status-only `case=26`.
- No `case=11` enumerate, PERST assert/deassert cases, MMIO write cases,
  boot option write, platform bind/unbind, PCI rescan, PMIC/GPIO/GDSC
  direct write, eSoC notify/`BOOT_DONE`, Wi-Fi HAL, scan/connect, credential
  handling, DHCP/routes, external ping, flash, boot image write, or partition write.

## Next

treat pci-msm debugfs case writes as unsafe; do not attempt enumerate without source/disasm proof
