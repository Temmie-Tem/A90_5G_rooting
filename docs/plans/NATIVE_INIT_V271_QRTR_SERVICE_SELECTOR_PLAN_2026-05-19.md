# Native Init v271 QRTR Service Selector Plan

## Summary

- target: v271 QRTR service/instance evidence selector
- boot image change: none
- device command: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- tool: `scripts/revalidation/wifi_qrtr_service_selector.py`

v270 proved that QRTR nameservice control packets can be sent and read back, but
service `1`, instance `1` produced no nameservice notifications in either the
1s or 3s readback windows. v271 therefore stays host-only and correlates prior
v270 evidence with vendor binary strings/symbols before any further live QRTR
lookup or QMI-control payload plan.

## Reference Model

- QRTR nameservice lookup requires an evidence-based service/instance selector;
  an arbitrary service id can produce a valid send path and still return no
  visible service events.
- Qualcomm userspace normally derives numeric QMI service ids from service
  object metadata rather than hard-coded guesses. The next safe target is
  service-object introspection, not QMI request payloads.
- Linux QRTR nameservice control packets remain distinct from QMI payloads.

Reference sources:

- Linux QRTR UAPI: `https://codebrowser.dev/linux/linux/include/uapi/linux/qrtr.h.html`
- Linux QRTR nameservice implementation: `https://codebrowser.dev/linux/linux/net/qrtr/ns.c.html`
- LKDDB QRTR overview: `https://cateee.net/lkddb/web-lkddb/QRTR.html`

## Scope

- Read prior manifests:
  - `tmp/wifi/v270-qrtr-ns-readback-live-20260519-103623/manifest.json`
  - `tmp/wifi/v270-qrtr-ns-readback-live-long-20260519-103732/manifest.json`
- Read host-side vendor export:
  - `tmp/wifi/v226-vendor-root-live-export/vendor-source/bin/cnss-daemon`
  - `tmp/wifi/v226-vendor-root-live-export/vendor-source/lib64/libqmiservices.so`
  - `tmp/wifi/v226-vendor-root-live-export/vendor-source/lib64/libqmi_cci.so`
- Extract:
  - `cnss-daemon` QMI client imports
  - DMS/WLFW/WLAN/CNSS string evidence
  - exported `*_get_service_object_internal_vXX` symbols
  - `qmi_idl_get_service_id` availability
- Produce candidate table:
  - service `1`/instance `1`
  - DMS
  - WLFW
  - WLAN

## Guardrails

v271 must not:

- open QRTR sockets
- send QRTR nameservice packets
- send QMI payloads
- execute device commands
- start `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, hostapd, DHCP,
  or routing commands
- scan/connect/link-up Wi-Fi
- mutate rfkill, ICNSS, firmware paths, Android partitions, property service,
  perfd, kmsg, `/data/vendor/wifi`, or routing

## Validation

```bash
python3 scripts/revalidation/wifi_qrtr_service_selector.py \
  --out-dir tmp/wifi/v271-qrtr-service-selector \
  analyze

python3 -m py_compile \
  scripts/revalidation/wifi_qrtr_service_selector.py \
  scripts/revalidation/wifi_qrtr_nameservice_runner.py \
  scripts/revalidation/a90ctl.py

git diff --check

rg -n "v271|qrtr-service-selector-ready|DMS|WLFW" \
  docs/plans docs/reports scripts/revalidation/wifi_qrtr_service_selector.py
```

## Acceptance

- manifest decision is `qrtr-service-selector-ready`
- v270 primary and long readback evidence are both recognized as service `1`,
  instance `1`, zero events, no QMI attempted
- DMS is classified as strong evidence via `dms_get_service_object_internal_v01`
- WLFW is classified as strong but unresolved because a public service object
  symbol is not exported in current evidence
- next step is service-object ID extraction without QMI payloads
