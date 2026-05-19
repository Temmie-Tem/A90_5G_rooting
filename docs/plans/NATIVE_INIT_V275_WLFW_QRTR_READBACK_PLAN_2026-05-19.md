# Native Init v275 WLFW QRTR Readback Plan

## Summary

- target: v275 WLFW QRTR nameservice readback matrix
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- tool: `scripts/revalidation/wifi_qrtr_readback_matrix.py`
- helper: `/cache/bin/a90_qrtr_ns_probe`
- WLFW candidate: service id `69` / `0x45`, version `1`

v274 identified WLFW as a concrete Wi-Fi firmware-control service-id candidate
from public Android kernel headers and matching local `cnss-daemon` strings.
v275 performs a bounded explicit-approval QRTR nameservice readback for WLFW
only. It sends `NEW_LOOKUP` plus cleanup `DEL_LOOKUP` control packets and never
sends QMI request payloads.

## Matrix

Explicit WLFW matrix:

```text
wlfw:69:0,1
```

Notes:

- service id `0` remains blocked as global wildcard.
- instance `0` is allowed only as a service-specific instance wildcard for
  service id `69`.
- instance `1` is tested because WLFW headers define service version `1`.
- no QMI request payload is sent.

## Guardrails

v275 must not:

- send QMI payloads
- start `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, hostapd, DHCP,
  or routing commands
- scan/connect/link-up Wi-Fi
- mutate rfkill, ICNSS, firmware paths, Android partitions, property service,
  perfd, kmsg, `/data/vendor/wifi`, or routing
- use service id `0` global wildcard
- run unbounded QRTR receive loops

## Validation

Non-transmitting plan:

```bash
python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v275-wlfw-qrtr-readback-plan \
  --matrix 'wlfw:69:0,1' \
  plan
```

Preflight:

```bash
python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v275-wlfw-qrtr-readback-preflight \
  --matrix 'wlfw:69:0,1' \
  preflight
```

Approved live matrix:

```bash
python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v275-wlfw-qrtr-readback-live-$(date +%Y%m%d-%H%M%S) \
  --matrix 'wlfw:69:0,1' \
  --allow-qrtr-ns-transmit \
  --assume-yes \
  --i-understand-qrtr-packet-transmission \
  run
```

Static:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_qrtr_readback_matrix.py \
  scripts/revalidation/wifi_wlfw_service_locator.py \
  scripts/revalidation/a90ctl.py

git diff --check
```

Postflight:

```bash
python3 scripts/revalidation/a90ctl.py --json version
python3 scripts/revalidation/a90ctl.py status
python3 scripts/revalidation/a90ctl.py run /cache/bin/toybox pidof cnss-daemon || true
python3 scripts/revalidation/a90ctl.py cat /proc/net/dev
```

## Acceptance

- plan mode sends no packets.
- preflight proves the device build, helper presence, and bounded WLFW matrix.
- live run sends only WLFW QRTR nameservice control packets for service `69`.
- every case reports `qmi_attempted=0`.
- every case either observes service events, reaches end-of-list, or times out
  in the bounded readback window.
- final postflight leaves `cnss-daemon` absent and no `wlan*` interface present.
