# Native Init v273 QRTR Readback Matrix Report

## Summary

- status: PASS
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- tool: `scripts/revalidation/wifi_qrtr_readback_matrix.py`
- helper: `/cache/bin/a90_qrtr_ns_probe`
- helper sha256: `375c30c21e5715218698a67832bf31d8052be95d4933d2ab98c198d73a45076a`
- live evidence: `tmp/wifi/v273-qrtr-readback-matrix-live-20260519-110229/`
- decision: `qrtr-readback-matrix-timeout`

v273 ran a small evidence-based QRTR nameservice readback matrix. It used only
`NEW_LOOKUP` and cleanup `DEL_LOOKUP` control packets through the reviewed
helper. It did not send QMI payloads and did not start Wi-Fi daemons.

## Matrix

| name | service | instance | classification | events | service events | end of list | timeout | qmi attempted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WDS | `1` | `0` | timeout | `0` | `0` | `0` | `1` | `0` |
| WDS | `1` | `1` | timeout | `0` | `0` | `0` | `1` | `0` |
| DMS | `2` | `0` | timeout | `0` | `0` | `0` | `1` | `0` |
| DMS | `2` | `1` | timeout | `0` | `0` | `0` | `1` | `0` |

## Validation

Static and non-transmitting plan:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_qrtr_readback_matrix.py \
  scripts/revalidation/wifi_qmi_service_object_extractor.py \
  scripts/revalidation/wifi_qrtr_service_selector.py \
  scripts/revalidation/a90ctl.py

python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v273-qrtr-readback-matrix-plan \
  plan

git diff --check
```

Preflight:

```text
decision: qrtr-readback-matrix-preflight-ready
pass: True
```

Approved live run:

```text
decision: qrtr-readback-matrix-timeout
pass: True
reason: all matrix cases completed with bounded readback timeouts
```

Postflight:

- `version`: `A90 Linux init 0.9.60 (v261)`
- `status`: shell responsive, `selftest fail=0`, `netservice: disabled tcpctl=stopped`
- `pidof cnss-daemon`: rc `1`, process absent
- `/proc/net/dev`: `ncm0` present; no `wlan*` interface observed

## Interpretation

- The QRTR nameservice control path is still functional.
- WDS service id `1` and DMS service id `2` both produced no nameservice
  events for instance `0` or instance `1`.
- Because DMS is exported by `libqmiservices.so` but still produced no
  readback events, the remaining blocker is likely not only service-id
  selection. It may require a CNSS/runtime endpoint state that is absent until
  a daemon or platform service registers, or it may require locating the
  Wi-Fi-specific WLFW service object instead of cellular/modem services.
- This result does not justify QMI request payloads yet.

## Guardrails Preserved

- no QMI payload
- no Wi-Fi scan/connect/link-up
- no credentials, DHCP, routing, or Internet-facing exposure
- no `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, or hostapd start
- no rfkill write, ICNSS bind/unbind, firmware mutation, Android partition
  write, property service mutation, perfd mutation, kmsg mutation, or reboot
- service id `0` global wildcard remained blocked

## Next Step

v274 should locate the WLFW service object or service id from Android source,
additional vendor blobs, or cnss-daemon embedded data before any further live
packet escalation. QMI request payloads remain blocked.
