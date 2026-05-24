# Native Init V794 mdm3/ICNSS Surface Observer Report

## Result

- decision: `v794-idle-modem-esoc-offlining-icnss-bound-captured`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py`
- evidence: `tmp/wifi/v794-mdm3-icnss-surface-observer/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py
python3 scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py plan
python3 scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py run \
  --assume-yes \
  --allow-live-readonly
```

## Evidence Summary

| Signal | Result |
| --- | --- |
| modem state | `OFFLINING` |
| mdm3 named subsystem | absent in `msm_subsys` list |
| esoc0 subsystem state | `OFFLINING` |
| esoc0 surface | present |
| ICNSS device / driver | `true / true` |
| WLAN module / qcwlanstate / `boot_wlan` node | `true / false / true` |
| `wlan0` | absent |
| QRTR table | absent at idle |
| ICNSS-QMI / WLFW / BDF / `wlan0` dmesg | `0 / 0 / 0 / 0` |
| mutations | none |

## Classification

V794 confirms the current idle surface is not already in a usable Wi-Fi lower
window. Modem and esoc0 are offlining at idle, while ICNSS is bound and WLAN
control nodes are present. This explains why a pure idle read-only view cannot
show WLFW/service `69`, BDF, or `wlan0`.

The next gate should observe the same mdm3/esoc/ICNSS/WLFW surfaces inside the
known lower window:

```text
firmware mounts
  -> subsys_modem holder
    -> read modem/esoc0 state
    -> read ICNSS/WLFW/QRTR/service69/BDF/wlan0 surfaces
```

Do not add service-manager, `boot_wlan`, qcwlanstate write, HAL, scan/connect,
DHCP, or external ping to that gate.

## Safety

- V794 was read-only live.
- No daemon start, service-manager start, Wi-Fi HAL start, `boot_wlan` write,
  qcwlanstate write, scan/connect, credential use, DHCP/routes, external ping,
  `esoc0` open/hold, module bind/unbind, boot image write, partition write, or
  custom kernel flash.

## Next

V795 should be a lower-window mdm3/esoc observer:

1. prepare read-only firmware mounts;
2. open only the proven `subsys_modem` holder path;
3. read modem/esoc0, ICNSS, QRTR/service `69`, WLFW, BDF, and `wlan0` surfaces;
4. cleanup with reboot and prove v724 health;
5. still block service-manager, Wi-Fi HAL, `boot_wlan`, qcwlanstate writes,
   scan/connect, credentials, DHCP/routes, and external ping.
