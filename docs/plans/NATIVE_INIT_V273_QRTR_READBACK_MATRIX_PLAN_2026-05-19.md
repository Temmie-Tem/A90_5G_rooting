# Native Init v273 QRTR Readback Matrix Plan

## Summary

- target: v273 QRTR nameservice readback matrix
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- tool: `scripts/revalidation/wifi_qrtr_readback_matrix.py`
- helper: `/cache/bin/a90_qrtr_ns_probe`

v272 resolved two important facts: DMS service id is `2`, and the prior service
`1` probe maps to WDS rather than a Wi-Fi firmware-control service. v273 runs a
small explicit-approval QRTR nameservice matrix for WDS and DMS, using only
`NEW_LOOKUP` plus cleanup `DEL_LOOKUP` control packets and bounded readback.

## Matrix

Default matrix:

```text
wds:1:0,1
dms:2:0,1
```

Notes:

- service id `0` remains blocked as global wildcard.
- instance `0` is allowed only with a nonzero service id as a service-specific
  instance wildcard.
- no QMI request payload is sent.

## Guardrails

v273 must not:

- send QMI payloads
- start `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, hostapd, DHCP,
  or routing commands
- scan/connect/link-up Wi-Fi
- mutate rfkill, ICNSS, firmware paths, Android partitions, property service,
  perfd, kmsg, `/data/vendor/wifi`, or routing
- use service id `0` global wildcard
- run unbounded QRTR receive loops

## Validation

Non-transmitting:

```bash
python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v273-qrtr-readback-matrix-plan \
  plan
```

Preflight:

```bash
python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v273-qrtr-readback-matrix-preflight \
  preflight
```

Approved live matrix:

```bash
python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v273-qrtr-readback-matrix-live-$(date +%Y%m%d-%H%M%S) \
  --allow-qrtr-ns-transmit \
  --assume-yes \
  --i-understand-qrtr-packet-transmission \
  run
```

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_qrtr_readback_matrix.py \
  scripts/revalidation/wifi_qmi_service_object_extractor.py \
  scripts/revalidation/wifi_qrtr_service_selector.py \
  scripts/revalidation/a90ctl.py

git diff --check
```

## Acceptance

- plan mode sends no packets.
- preflight proves device build, helper presence, and bounded matrix.
- live run sends exactly the bounded matrix of QRTR nameservice control packets.
- every case reports `qmi_attempted=0`.
- every case either observes service events, reaches end-of-list, or times out
  in the bounded readback window.
- final postflight leaves `cnss-daemon` absent and no `wlan*` interface present.
