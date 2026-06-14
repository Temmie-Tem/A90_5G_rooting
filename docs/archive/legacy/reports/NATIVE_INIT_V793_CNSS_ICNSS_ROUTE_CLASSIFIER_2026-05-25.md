# Native Init V793 CNSS/ICNSS Route Classifier Report

## Result

- decision: `v793-route-mdm3-icnss-wlfw-continuation`
- pass: `true`
- runner: `scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py`
- evidence: `tmp/wifi/v793-cnss-icnss-route-classifier/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py
python3 scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py plan
python3 scripts/revalidation/native_wifi_cnss_icnss_route_classifier_v793.py run
```

## Evidence Summary

| Signal | Result |
| --- | --- |
| V792 decision | `v792-known-warning-cnss-no-wlfw-classified` |
| V792 `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| V792 `mdm3` | `OFFLINING -> OFFLINING -> OFFLINING` |
| V792 service-notifier / `sysmon-qmi` | `2 / 4` |
| V792 `cnss-daemon` netlink / `cnss_diag` netlink | `79 / 33` |
| V792 binder ioctl/transaction `-22` | `1 / 33` |
| V792 ICNSS-QMI / WLFW / BDF / `wlan0` | `0 / 0 / 0 / 0` |
| service-manager readiness route | demoted by V660/V666 |
| binder-only route | secondary; not an unchanged retry target |
| blind `boot_wlan`/qcwlanstate route | demoted by V750/V752 |
| CNSS2/MHI route | demoted by V763 ICNSS rebase |
| memshare-only route | demoted by V785 |

## Classification

V793 selects the mdm3 + ICNSS/WLFW continuation route. The reason is not that
binder is irrelevant; V792 still shows binder `-22`. The point is narrower:
unchanged service-manager or binder-only retries have already been tested and
did not produce WLFW/service `69`, BDF, firmware-ready, or `wlan0`.

The strongest current blocker chain is:

```text
V792:
  mss ONLINE
  mdm3 OFFLINING
  service 180/74 present
  cnss_diag/cnss-daemon netlink present
  binder -22 present
  ICNSS-QMI/WLFW/BDF/wlan0 absent

Prior evidence:
  service-manager readiness and fresh CNSS retry still no WLFW
  boot_wlan/qcwlanstate writes still no WLFW
  SM-A908N route is ICNSS/QCACLD, not CNSS2/MHI
  memshare/CMA failure is common and not the sole blocker
```

Therefore the next live action should observe mdm3 and ICNSS/WLFW surfaces, not
start Wi-Fi HAL or repeat unchanged CNSS/service-manager orderings.

## Safety

- V793 was host-only.
- No device command, reboot, mount, daemon start, Wi-Fi action, credential use,
  network change, boot image write, partition write, or custom kernel flash.
- Evidence reads were bounded.

## Next

V794 should be a bounded read-only/current-live mdm3 + ICNSS/WLFW surface
observer:

1. capture `/sys/bus/msm_subsys/devices`, esoc, ICNSS, `/sys/module/wlan`,
   qcwlanstate, dmesg, QRTR/service `69`, and binder counters;
2. do not start service-manager, Wi-Fi HAL, `boot_wlan`, qcwlanstate, scan,
   connect, DHCP, route changes, or external ping;
3. route the following step only after proving whether the current missing edge
   is mdm3, ICNSS service-arrival, HDD/PLD, or binder/runtime context.
