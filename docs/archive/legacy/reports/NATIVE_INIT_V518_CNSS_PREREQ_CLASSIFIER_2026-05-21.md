# Native Init V518 CNSS Prerequisite Classifier

## Summary

- target: read-only classification after V517 CNSS private data-Wi-Fi proof
- runner: `scripts/revalidation/native_wifi_cnss_prereq_classifier_v518.py`
- decision: `v518-cnss-prereq-classified`
- pass: `true`
- daemon start: not executed
- Wi-Fi bring-up: not executed

V518 confirms that the V517 user-socket blocker is closed and that the remaining
gap is earlier than WLFW/QMI/BDF/FW-ready. Because QMI/WLFW markers are still
zero, a bounded `qcwlanstate` retry is not the next step yet. The next gate is a
read-only Android/native delta for QRTR/modem/perfd/property runtime state.

## Evidence

Evidence root:

```text
tmp/wifi/v518-cnss-prereq-classifier/
```

Key decision:

```text
decision: v518-cnss-prereq-classified
pass: True
reason: data Wi-Fi user socket gap closed; QMI/WLFW still absent, so the next gate is read-only QRTR/modem/perfd/property delta
next: compare Android/native QRTR modem, perfd, and property runtime before any qcwlanstate retry
device_mutations: False
daemon_start_executed: False
wifi_bringup_executed: False
```

## Findings

| item | result |
| --- | --- |
| native baseline | `A90 Linux init 0.9.61 (v319)`, `fail=0` |
| V517 prerequisite | `v517-cnss-userspace-readiness-no-fw-marker`, pass |
| data Wi-Fi socket gap | closed; private `/data/vendor/wifi/sockets` present in V517 |
| `Fail to bind user socket` | absent in V517 |
| active Wi-Fi/CNSS processes | none |
| Wi-Fi link surface | none |
| QIPCRTR protocol | present |
| `/proc/net/qrtr` / `/dev/qrtr` | absent |
| `/dev/wlan` | present |
| perfd runtime | socket absent; only client libraries found |
| property runtime | `/dev/socket/property_service` and `/dev/__properties__` absent |

Interpretation:

- Perfd/property remain classified warnings, not the proven next blocker.
- `cnss-daemon` static strings still show QMI/WLFW capability and property
  references.
- Since V517 still shows `qmi_server_connected=0`, `BDF=0`, and `WLFW=0`, the
  next differentiated test should not write `qcwlanstate` yet.
- First compare Android and native QRTR/modem/perfd/property readiness surfaces
  to identify why `cnss-daemon` does not reach QMI/WLFW under native init.

## Validation

Commands run:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_prereq_classifier_v518.py
python3 scripts/revalidation/native_wifi_cnss_prereq_classifier_v518.py plan
python3 scripts/revalidation/native_wifi_cnss_prereq_classifier_v518.py run
```

## Next Gate

Recommended V519:

1. compare Android boot evidence and native evidence around QRTR/modem service
   readiness before `wlfw_start`;
2. classify whether perfd/property runtime absence is only warning context or a
   prerequisite for QMI/WLFW startup;
3. collect current native QRTR/protocol/netlink/service surfaces without QRTR
   transmit, QMI payloads, CNSS daemon starts, or Wi-Fi operations;
4. produce a concrete blocker list before any `qcwlanstate` retry.

Do not start Wi-Fi HAL or attempt SSID credentials until a native `wlan0` or
firmware-ready equivalent is proven.
