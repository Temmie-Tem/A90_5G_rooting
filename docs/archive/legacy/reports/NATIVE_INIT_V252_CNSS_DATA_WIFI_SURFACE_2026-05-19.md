# Native Init v252 CNSS Data Wi-Fi Runtime Surface Report

## Summary

- status: PASS
- decision: `cnss-data-wifi-surface-missing`
- boot image change: none
- daemon start: not executed
- output: `tmp/wifi/v252-cnss-data-wifi-surface/`
- host tool: `scripts/revalidation/wifi_cnss_data_wifi_surface.py`

v252 checked the runtime filesystem/socket paths that `cnss-daemon` references
under `/data/vendor/wifi`. The native init environment currently has `/data`, but
not `/data/vendor`, `/data/vendor/wifi`, or `/data/vendor/wifi/sockets`.

## Validation

```bash
python3 -m py_compile scripts/revalidation/wifi_cnss_data_wifi_surface.py
git diff --check
python3 scripts/revalidation/wifi_cnss_data_wifi_surface.py \
  --out-dir tmp/wifi/v252-cnss-data-wifi-surface
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
```

Result:

```text
decision: cnss-data-wifi-surface-missing
pass: True
```

Post-check: `pidof cnss-daemon` returned rc=1.

## Findings

| Check | Result |
| --- | --- |
| v251 prerequisite | PASS |
| required control captures | PASS |
| cnss-daemon absent | PASS |
| `/data` | present |
| `/data/vendor` | missing |
| `/data/vendor/wifi` | missing |
| `/data/vendor/wifi/sockets` | missing |

Relevant `cnss-daemon` strings:

```text
/data/vendor/wifi/%s
/data/vendor/wifi/iotap_ps.bin
/data/vendor/wifi/qdss_trace.bin
/data/vendor/wifi/qdss_trace_config.bin
/data/vendor/wifi/sockets/cnss_user_client
/data/vendor/wifi/sockets/cnss_user_server
/data/vendor/wifi/wlfw_cal_%02d.bin
cnss_user_socket_init
```

## Interpretation

- Native root currently lacks the Android runtime Wi-Fi data directory tree.
- A live start-only run may fail when it tries to use `/data/vendor/wifi` files
  or sockets, even though this is separate from property service and QRTR.
- v252 intentionally did not create directories, mount userdata, or change
  ownership/permissions.
- This should be treated as a runtime filesystem gap, not a reason to start
  framework services.

## Guardrails Preserved

- no `/data/vendor/wifi` creation
- no userdata mount/remount
- no ownership/permission mutation
- no `cnss-daemon` execution
- no rfkill unblock, `wlan*` link-up, scan/connect, credentials, DHCP, or routing
- no ICNSS bind/unbind, firmware mutation, Android partition write, or reboot

## Next Step

The first bounded live start-only attempt remains approval-gated. If approval is
still withheld, the next safe candidate is a no-mutation plan for private
runtime directory materialization inside the helper namespace, or a live approval
review that explicitly accepts this filesystem gap.
