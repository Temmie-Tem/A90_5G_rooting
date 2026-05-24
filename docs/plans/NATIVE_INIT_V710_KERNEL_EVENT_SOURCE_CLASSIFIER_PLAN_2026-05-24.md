# Native Init V710 Kernel Event Source Classifier Plan

- date: `2026-05-24 KST`
- cycle: `v710`
- type: host-only classifier

## Goal

Consume the current V708/V709 provider-first CNSS stall evidence and Android
reference evidence to classify the missing edge after service-notifier `180/74`:

```text
service 180/74 + provider registration + cnss-daemon retry alive
  -> missing QCA6390/ICNSS/WLFW kernel event source
  -> no BDF/FW-ready/wlan0
```

## Scope

Allowed:

- parse V708 manifest, dmesg delta, and helper v120 focused sysfs/stall output;
- parse V709 `cnss-daemon` poll/futex stall classification;
- compare against Android ICNSS/WLFW reference evidence from V703;
- classify whether the next target is service publication, CNSS Binder,
  QCA6390 binding, ICNSS-QMI/WLFW, BDF, firmware-ready, or `wlan0`.

Forbidden:

- device command execution;
- daemon start, service-manager start, Wi-Fi HAL start, scan/connect/link-up;
- credential use, DHCP, route change, or external ping;
- sysfs/debugfs writes, subsystem state writes, `esoc0` access;
- boot image or partition writes.

## Version Mapping

The V666/V667 pd-notifier direction was correct, but it is already consumed by
existing evidence. V710 applies the same causal chain to the current V708/V709
state where service `180/74`, provider registration, and post-provider CNSS
retry are already positive.

Android reference logs show BDF activity via `cnss-daemon` after ICNSS-QMI/WLFW
readiness. Therefore V710 should not assert that BDF is kernel-only; it should
classify the missing prerequisite event that prevents BDF/WLFW from starting.

## Success Criteria

- V708 service-notifier `180/74` is positive;
- V709 proves retry `cnss-daemon` is alive in `poll`/`futex` pre-WLFW wait;
- V708 has no `cnss-daemon` Binder transaction failure in the post-provider
  retry;
- V708 has no ICNSS-QMI, WLFW, BDF, firmware-ready, or `wlan0` markers;
- V708 helper sysfs shows QCA6390 node visible but not bound to a driver;
- Android reference shows ICNSS-QMI/WLFW/BDF/FW-ready/`wlan0` progression;
- no live action is executed.

## Next Gate

If V710 classifies a QCA6390/WLFW event-source gap, plan the next unit around
read-only or tightly bounded capture of the QCA6390 bind/power/MHI/ICNSS event
edge before any Wi-Fi HAL, scan/connect, DHCP, credential, or external ping
work.
