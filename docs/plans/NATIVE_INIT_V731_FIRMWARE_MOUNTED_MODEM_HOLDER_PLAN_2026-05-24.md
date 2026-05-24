# Native Init V731 Firmware-mounted Modem Holder Plan

- date: `2026-05-24 KST`
- cycle: `v731`
- runner: `scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py`
- evidence target: `tmp/wifi/v731-firmware-mounted-modem-holder/`
- gate: current-build read-only firmware mounts plus `subsys_modem` holder

## Goal

V730 reclassified V729 as a no-global-firmware open-pending result. V731
recreates the known-good lower prerequisite from V594/V595/V596 on the current
V724 build:

```text
mount /vendor/firmware_mnt + /vendor/firmware-modem read-only
  -> confirm modem.b00 visibility
    -> open and hold only subsys_modem
      -> observe mss, QRTR RX/TX, sysmon, service-notifier, WLFW/BDF/wlan0
        -> reboot cleanup
```

## Scope

Allowed:

- read native baseline with `version`, `status`, and `selftest`;
- resolve `apnhlos` and `modem` partitions using the V584 preflight contract;
- temporarily replace the native `/vendor` symlink only for read-only firmware
  mount parity;
- mount `/vendor/firmware_mnt` and `/vendor/firmware-modem` read-only;
- stat known modem blob paths;
- create a temporary private `subsys_modem` node under the proof directory;
- open and hold only `subsys_modem`;
- observe `mss/mdm3` state, crash counts, QRTR, sysmon, MHI/QCA6390, WLFW, BDF,
  and `wlan0` markers;
- reboot as cleanup boundary and verify native returns healthy;
- write private host-side evidence.

Blocked:

- creating or opening any `esoc0` node;
- subsystem state writes such as `echo online`;
- deliberate holder close before cleanup;
- module load/unload;
- daemon start, service-manager start, Wi-Fi HAL start, supplicant, hostapd,
  wificond, or `qcwlanstate`;
- scan/connect/link-up, credentials, DHCP, routes, or external ping;
- boot image or partition writes.

## Success Criteria

V731 passes if it proves:

- current native baseline is healthy;
- V730 routing decision is present;
- both firmware partitions mount read-only;
- at least one global modem blob path is visible;
- `subsys_modem` holder opens without `esoc0`;
- `mss` reaches `ONLINE` and/or QRTR RX appears;
- no kernel warning/reference mismatch marker appears;
- reboot cleanup returns to healthy V724 native;
- guardrail booleans show no daemon/HAL, scan/connect, credentials, DHCP,
  routes, or external ping.

Expected decision:

```text
v731-firmware-mounted-modem-holder-qrtr-rx-pass
```

## Validation Plan

```bash
python3 -m py_compile scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py

python3 scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py \
  --out-dir tmp/wifi/v731-firmware-mounted-modem-holder-plan plan

python3 scripts/revalidation/native_wifi_firmware_mounted_modem_holder_v731.py \
  --out-dir tmp/wifi/v731-firmware-mounted-modem-holder run

python3 scripts/revalidation/a90ctl.py --timeout 20 status

python3 scripts/revalidation/a90ctl.py --timeout 20 cat /proc/mounts \
  | rg '/vendor/firmware_mnt|/vendor/firmware-modem| /firmware ' || true

git diff --check
```

## Next Gate

If V731 restores QRTR RX safely, V732 should add only the lower companion stack
inside the same firmware-mounted modem holder window. It should still block
service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP, routes, and
external ping until QRTR TX/`sysmon-qmi` and later WLAN markers are restored.
