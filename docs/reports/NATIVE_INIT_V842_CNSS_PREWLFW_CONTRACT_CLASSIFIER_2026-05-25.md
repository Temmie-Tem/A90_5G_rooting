# Native Init V842 CNSS Pre-WLFW Contract Classifier Report

## Result

- decision: `v842-current-window-cnss-stall-snapshot-selected`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_cnss_prewlfw_contract_classifier_v842.py`
- evidence: `tmp/wifi/v842-cnss-prewlfw-contract-classifier/`

## Scope

V842 was host-only. It did not contact the device, start daemons, start
service-manager, start Wi-Fi HAL, scan/connect, use credentials, run DHCP,
change routes, ping externally, write sysfs/debugfs, write boot images, write
partitions, or flash a custom kernel.

## Key Signals

| Signal | Value |
| --- | --- |
| Android service command | `/system/vendor/bin/cnss-daemon -n -l` |
| Android domain/capability | `u:r:vendor_wcnss_service:s0`, `CAP_NET_ADMIN` |
| Native domain/capability | `u:r:vendor_wcnss_service:s0`, `CAP_NET_ADMIN` |
| Native process state | alive, `S (sleeping)`, `4` threads |
| Native fd surface | `16` fds, `10` sockets, vndbinder present |
| Native V840 positive surface | service `180/74`, CNSS netlink, CLD80211 |
| Native V840 missing surface | no `wlfw_start`, no WLAN-PD, no QMI connected, no BDF, no `wlan0` |
| Provider/Binder branch | not primary after V840 because current Binder failures are `0` |

## Interpretation

The broad CNSS launcher contract is no longer the strongest blocker. Android
and native both satisfy the relevant command, identity, SELinux domain,
capability, and fd surfaces for the current start-only contract.

The current blocker is a live pre-WLFW stall: native `cnss-daemon` starts and
stays alive with expected runtime surfaces, but never enters `wlfw_start`.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_prewlfw_contract_classifier_v842.py
python3 scripts/revalidation/native_wifi_cnss_prewlfw_contract_classifier_v842.py \
  --out-dir tmp/wifi/v842-plan-check \
  plan
python3 scripts/revalidation/native_wifi_cnss_prewlfw_contract_classifier_v842.py \
  --out-dir tmp/wifi/v842-cnss-prewlfw-contract-classifier \
  run
```

Result:

```text
decision: v842-current-window-cnss-stall-snapshot-selected
pass: True
device_commands_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Next Gate

V843 should run a bounded current-window `cnss-daemon` stall snapshot around the
provider-first retry. Capture `wchan`, syscall, task status/stat, optional
stack, fd targets, socket inode mappings, and dmesg deltas before cleanup.

Keep Wi-Fi HAL, scan/connect, DHCP/routes, credentials, external ping, `esoc0`,
subsystem writes, module load/unload, and boot image writes blocked.
