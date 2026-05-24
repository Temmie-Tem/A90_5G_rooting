# Native Init V706 CNSS2 PD-Notifier Read-Only Plan

- date: `2026-05-24 KST`
- cycle: `v706`
- source request label: `v666`
- type: bounded read-only live classifier

## Goal

The current Wi-Fi hypothesis is that QRTR service `69` is published by the
QCA6390 WLAN processor only after WLAN-PD/service-notifier `180` causes the
kernel `icnss`/CNSS path to power the WLAN device. V706 checks the missing
edge without changing runtime state:

```text
service-notifier 180 -> kernel pd_notifier/server_arrive -> QCA6390 power -> WLFW/service 69
```

## Scope

Allowed:

- read current native status/selftest;
- read `/sys/bus/msm_subsys`, `/sys/class/subsys`, `icnss`, and QCA6390 sysfs
  surfaces;
- read `/proc/net/qrtr` and `/proc/net/netlink`;
- capture `dmesg` and classify CNSS/ICNSS/QCA/WLFW markers;
- accept either the original `v666` approval phrase or the normalized `v706`
  phrase for this same read-only scope.

Forbidden:

- daemon start;
- service-manager, Wi-Fi HAL, wificond, supplicant, or hostapd start;
- scan/connect/link-up;
- credential use;
- DHCP, route changes, or external ping;
- sysfs/debugfs/procfs writes;
- `esoc0` open/hold;
- boot image or partition writes.

## Implementation

Add `scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py`.

The runner supports:

```bash
python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py plan
python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py preflight
python3 scripts/revalidation/native_wifi_cnss2_pd_notifier_readonly_v706.py \
  --approval 'approve v706 cnss2 pd-notifier firing check and modem subsys state read; no Wi-Fi HAL start, no scan/connect, no DHCP, no external ping' \
  run
```

The run command writes private evidence under
`tmp/wifi/v706-cnss2-pd-notifier-readonly-live/`.

## Decision Labels

- `v706-service180-absent-current-boot`: current boot never reached WLAN-PD
  service-notifier `180`, so CNSS retry/HAL tests are premature.
- `v706-service180-without-kernel-cnss2-firing`: service `180` is visible but
  no kernel pd-notifier/power marker follows.
- `v706-service180-without-qca6390-power`: pd-notifier-like activity exists but
  no QCA6390 power transition follows.
- `v706-pre-wlfw-kernel-gap-classified`: kernel progression is visible but
  WLFW/service `69`/`wlan0` is still absent.
- `v706-wlfw-or-wlan0-progressed`: WLFW or netdev creation progressed and the
  next gate can classify Wi-Fi userspace state.

## Success Criteria

- Live run must report `device_mutations=False`.
- Live run must report no daemon, Wi-Fi HAL, scan/connect, DHCP, or external
  ping execution.
- The next action must be derived from current-boot evidence, not from stale
  prior service-notifier captures.
