# Native Init v275 WLFW QRTR Readback Report

## Summary

- status: PASS
- boot image change: none
- baseline device build: `A90 Linux init 0.9.60 (v261)`
- tool: `scripts/revalidation/wifi_qrtr_readback_matrix.py`
- helper: `/cache/bin/a90_qrtr_ns_probe`
- helper sha256: `375c30c21e5715218698a67832bf31d8052be95d4933d2ab98c198d73a45076a`
- live evidence: `tmp/wifi/v275-wlfw-qrtr-readback-live-20260519-111529/`
- decision: `qrtr-readback-matrix-timeout`

v275 ran the WLFW-specific QRTR nameservice readback matrix. It used only
`NEW_LOOKUP` plus cleanup `DEL_LOOKUP` control packets through the reviewed
helper. It did not send QMI payloads and did not start Wi-Fi daemons.

## Matrix

| name | service | instance | classification | events | service events | end of list | timeout | qmi attempted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WLFW | `69` | `0` | timeout | `0` | `0` | `0` | `1` | `0` |
| WLFW | `69` | `1` | timeout | `0` | `0` | `0` | `1` | `0` |

## Validation

Static and non-transmitting plan:

```bash
python3 -m py_compile \
  scripts/revalidation/wifi_qrtr_readback_matrix.py \
  scripts/revalidation/wifi_wlfw_service_locator.py \
  scripts/revalidation/a90ctl.py

python3 scripts/revalidation/wifi_qrtr_readback_matrix.py \
  --out-dir tmp/wifi/v275-wlfw-qrtr-readback-plan \
  --matrix 'wlfw:69:0,1' \
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

- WLFW service id `69` is a source-backed Wi-Fi firmware-control candidate, but
  in the current native state it produced no QRTR nameservice notifications for
  instance `0` or instance `1`.
- Since WDS, DMS, and now WLFW all time out in bounded readback, the blocker is
  more likely current runtime endpoint registration or CNSS/platform state than
  just choosing the wrong cellular service id.
- This result still does not justify QMI request payloads. The next useful step
  should be a no-payload runtime registration or CNSS state correlation plan,
  not a WLFW request-payload escalation.

## Guardrails Preserved

- no QMI payload
- no Wi-Fi scan/connect/link-up
- no credentials, DHCP, routing, or Internet-facing exposure
- no `cnss-daemon`, `cnss_diag`, HAL, supplicant, wificond, or hostapd start
- no rfkill write, ICNSS bind/unbind, firmware mutation, Android partition
  write, property service mutation, perfd mutation, kmsg mutation, or reboot
- service id `0` global wildcard remained blocked

## Next Step

v276 should correlate why QRTR nameservice readback sees no WDS/DMS/WLFW server
notifications in native state. Candidate paths are read-only QRTR endpoint table
inspection, CNSS registration-state evidence, or Android-side comparison of QRTR
nameservice visibility before any QMI payload is considered.
