# Native Init V712 Execns Helper v121 ICNSS Edge Plan

- date: `2026-05-24 KST`
- cycle: `v712`
- type: helper observability prep plus bounded future live proof

## Goal

Add helper v121 observability for the ICNSS-QMI/WLFW event-source edge selected
by V711:

```text
service 180/74 provider window
  -> ICNSS-QMI/WLFW edge capture
  -> decide why BDF/FW-ready/wlan0 do not follow
```

The goal is not to connect Wi-Fi yet. It is to capture the missing event source
inside the already proven provider-first CNSS retry window.

## Scope

Allowed for v121 prep:

- update `a90_android_execns_probe` version marker to `v121`;
- extend the existing `cnss2_focus` capture points with read-only ICNSS edge
  snapshots at `service74_open` and `window` phases;
- build static helper artifact and verify strings contract;
- add V712 provider-first and deploy/preflight wrappers;
- run deploy preflight only.

Allowed for the later V712 live proof, after helper deploy:

- deploy `/cache/bin/a90_android_execns_probe` v121 only;
- replay the existing provider-first service `180/74` + provider + CNSS retry
  path;
- capture ICNSS/QCA/MHI/PCI/RPMSG/module/wlan readiness surfaces;
- cleanup/reboot using the existing bounded proof contract.

Forbidden:

- Wi-Fi HAL start, scan/connect/link-up, credentials, DHCP, route changes, or
  external ping;
- ICNSS/QCA bind/unbind, `driver_override`, recovery, ramdump, assert, rfkill,
  or subsystem state writes;
- boot image or partition writes.

## v121 Capture Additions

Helper v121 adds read-only snapshots for:

- ICNSS and QCA6390 driver-link path status;
- `wlan0` and `/sys/kernel/shutdown_wlan` path status;
- MHI, PCI, RPMSG, ICNSS module, WLAN module, ICNSS power, QCA6390 power
  directories;
- selected ICNSS/WLAN module parameters;
- bounded `/proc/interrupts` sample.

These snapshots are embedded inside the existing `service74_open` and `window`
helper phases so they line up with the same live window that produced V708/V709.

## Success Criteria

- helper builds as static AArch64 ELF;
- helper strings include `a90_android_execns_probe v121` and ICNSS edge markers;
- V712 plan/preflight wrappers pass without live daemon execution;
- deploy preflight reports readiness and whether helper deployment is needed;
- no Wi-Fi connect path is executed.

## Next Gate

After committing v121 prep, deploy helper v121 and run the bounded V712
provider-first ICNSS edge proof. If WLFW/BDF/`wlan0` remain absent, classify the
captured ICNSS edge surface before any Wi-Fi HAL or connect attempt.
