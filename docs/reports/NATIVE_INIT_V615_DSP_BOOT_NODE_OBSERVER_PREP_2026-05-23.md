# Native Init V615 DSP Boot-Node Observer Prep Report

- date: `2026-05-23 KST`
- runner: `scripts/revalidation/native_wifi_dsp_boot_node_observer_v615.py`
- status: prepared; live observer not executed yet
- plan evidence: `tmp/wifi/v615-dsp-boot-node-plan/`
- current preflight evidence: `tmp/wifi/v615-dsp-boot-node-preflight-current/`

## Scope

V615 implements the V614 next gate: write only the Android-equivalent
ADSP/CDSP/SLPI boot nodes, then run the V609 no-CNSS companion observer.

Allowed live actions:

- firmware surface mounts already used by V613;
- write `1` to ADSP/CDSP/SLPI boot nodes;
- open and hold only `subsys_modem`;
- start `qrtr-ns`, `rmt_storage`, `tftp_server`, and `pd-mapper`;
- reboot cleanup.

Forbidden live actions:

- raw `subsys_esoc0` open/close;
- `boot_wlan` write;
- CNSS daemon or `cnss_diag`;
- service-manager or Wi-Fi HAL;
- qcwlanstate write;
- scan/connect/link-up, credentials, DHCP, routing, or external ping.

## Static Validation

```text
py_compile: pass
plan decision: v615-dsp-boot-node-observer-plan-ready
current preflight decision: v615-preflight-blocked
current blocker: v490-current-policy-load
```

The blocker is expected after the V613 reboot cleanup because V490 SELinux
policy-load freshness is per boot.

## Next Gate

Refresh current-boot V401/V490, rerun V615 preflight, then run the bounded live
observer. A pass should be interpreted only as lower-publication progress; it is
not a Wi-Fi connect or external ping proof.
