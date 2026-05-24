# Native Init V794 mdm3/ICNSS Surface Observer Plan

## Goal

Capture the current native idle mdm3/esoc, ICNSS, WLAN control, QRTR/netlink,
and dmesg surface without changing device state.

## Scope

- Read `/sys/bus/msm_subsys/devices`, esoc, ICNSS, `/sys/module/wlan`,
  qcwlanstate node presence, binder devnodes, `/proc/net/*`, `/proc/modules`,
  and focused dmesg.
- Use V793 as the route prerequisite.
- Classify whether the current idle surface already has modem/esoc/ICNSS/WLFW
  progression before planning a lower-window observer.

## Hard Gates

- Read-only live capture only.
- No daemon start, service-manager start, Wi-Fi HAL start, `boot_wlan` or
  qcwlanstate write, scan/connect, credential use, DHCP/routes, external ping,
  `esoc0` open/hold, module load/unload, bind/unbind, boot image write,
  partition write, or custom kernel flash.
- No Wi-Fi secret material in tracked output.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py
python3 scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py plan
python3 scripts/revalidation/native_wifi_mdm3_icnss_surface_observer_v794.py run \
  --assume-yes \
  --allow-live-readonly
git diff --check
```

## Expected Routing

- If `wlan0` is visible, stop before credentials and capture link state.
- If modem/esoc are already online at idle, reroute to ICNSS-QMI/WLFW trigger
  evidence.
- If modem/esoc are offlining at idle but ICNSS is bound, plan a lower-window
  mdm3/esoc observer using only firmware mounts and the `subsys_modem` holder.
