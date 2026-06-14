# Native Init V1361 MHI Surface Ownership Classifier

## Summary

- Cycle: `V1361`
- Type: host-only classifier
- Decision: `v1361-mhi-surfaces-downstream-no-safe-mutation`
- Result: PASS
- Script: `scripts/revalidation/native_wifi_mhi_surface_ownership_classifier_v1361.py`
- Evidence:
  - `tmp/wifi/v1361-mhi-surface-ownership-classifier/manifest.json`
  - `tmp/wifi/v1361-mhi-surface-ownership-classifier/summary.md`

## Decision

V1360 found MHI bus/client-driver surfaces but no MHI or PCI device instances. OSRC shows the MHI controller is created from pci_dev via mhi_pci_probe, while the visible MHI bind files belong to client drivers that require existing mhi_device instances. Therefore these surfaces are downstream of pcie1 enumeration and are not a narrower safe mutation.

## Checks

| check | pass |
| --- | --- |
| client_drivers_probe_mhi_device | true |
| dt_binds_sdx50m_to_mhi_pci_path | true |
| live_mhi_drivers_are_client_drivers | true |
| mhi_devices_created_by_controller_state | true |
| mhi_driver_bind_is_client_only | true |
| mhi_esoc_hook_is_downstream_of_pci_dev | true |
| mhi_pci_controller_requires_pci_dev | true |
| mhi_pci_driver_waits_for_pci_enumeration | true |
| v1360_live_has_mhi_topology | true |
| v1360_live_has_no_mhi_or_pci_devices | true |

## Source Facts

| fact | value |
| --- | --- |
| mhi_pci_probe | int mhi_pci_probe(struct pci_dev *pci_dev, |
| mhi_pci_driver | static struct pci_driver mhi_pcie_driver = { |
| mhi_esoc_power_on | static int mhi_arch_esoc_ops_power_on(void *priv, unsigned int flags) |
| mhi_create_devices | void mhi_create_devices(struct mhi_controller *mhi_cntrl) |
| mhi_driver_register | int mhi_driver_register(struct mhi_driver *mhi_drv) |
| mhi_uci_register | ret = mhi_driver_register(&mhi_uci_driver); |
| mhi_netdev_register | return mhi_driver_register(&mhi_netdev_driver); |
| rmnet_ctl_register | module_driver(rmnet_ctl_driver, |
| qdss_bridge_register | ret = mhi_driver_register(&qdss_mhi_driver); |

## Rejected Next Mutations

- MHI client driver bind/unbind: requires existing mhi_device instances and cannot create PCI/MHI enumeration
- /dev/mhi* open: no device nodes exist in V1360 evidence
- MHI debugfs/client surfaces: observational or client-side, not pcie1 RC enable controls
- pci-msm bind/unbind or global PCI rescan: still too broad until V1362 risk classifier

## Safety

- Host-only; no device command or live runtime access.
- No MHI bind/unbind, platform bind/unbind, PCI rescan, PMIC/GPIO/GDSC write,
  eSoC notify/`BOOT_DONE`, Wi-Fi HAL, scan/connect, credential handling,
  DHCP/routes, external ping, flash, boot image write, or partition write.

## Next

V1362 host-only pci-msm/pcie1 mutation risk classifier before any bind/rescan attempt
