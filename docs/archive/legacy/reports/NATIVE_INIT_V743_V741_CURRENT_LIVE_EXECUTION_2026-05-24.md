# Native Init V743 V741 Current Live Execution Report

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_mdm_helper_gated_live_v741.py`
- helper: `a90_android_execns_probe v122`
- evidence: `tmp/wifi/v743-v741-mdm-helper-gated-live-current/`
- decision: `v741-service74-gate-not-open`
- pass: `true`

## Summary

V743 executed the V741 gated `mdm_helper` proof after helper v122 deployment and
current-boot SELinux preparation. The run stayed inside the safety boundary:
firmware read-only mounts and `subsys_modem` holder were used, lower companion
and CNSS-only children started, but service-manager, Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, and external ping were not executed.

The service-`74` gate did not open, so the helper correctly did not start
`mdm_helper`. This means V743 did not test `mdm_helper` as a lower trigger; it
classified the immediate blocker as service publication/gate timing.

## Key Results

| item | result |
| --- | --- |
| helper mode | `wifi-companion-service74-gated-mdm-helper-start-only` |
| helper order | `qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,service74_gate,mdm_helper` |
| `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` | stayed `OFFLINING` |
| QRTR RX | present |
| QRTR TX / `sysmon-qmi` | absent in this gated run |
| service `180/74/69` | absent |
| `mdm_helper` | not started because service `74` gate stayed closed |
| MHI/QCA6390/WLFW/BDF/`wlan0` | absent |
| postflight | reboot cleanup and native health passed |

## Evidence

```text
decision: v741-service74-gate-not-open
pass: True
reason: service74 gate did not open, so mdm_helper was not started
mdm_helper_start_executed: False
service_manager_start_executed: False
wifi_hal_start_executed: False
scan_connect_executed: False
external_ping_executed: False
```

## Interpretation

The next step is not to force `mdm_helper`. The immediate question is whether
helper v122 can still reproduce the known CNSS-only service publication window.
That requires a V735-style CNSS-only comparison using helper v122.
