# Native Init V258 CNSS Live Evidence Analyzer Report

## Summary

- Status: PASS
- Tool: `scripts/revalidation/wifi_cnss_live_evidence_analyzer.py`
- Input: `tmp/wifi/v257-cnss-live-start-only-run/`
- Output: `tmp/wifi/v258-cnss-live-evidence-analysis/`
- Decision: `cnss-start-only-evidence-classified`
- Device commands executed by analyzer: none

## Implementation

The analyzer parses the V257 `commands/cnss-start-only-run.txt` transcript and runner manifest, then writes private evidence outputs with `EvidenceStore`.

Parsed surfaces:

- helper top-level key/value lines
- `cnss_start.*` lifecycle fields
- `cnss_child.*` pre-exec fields
- `cnss.identity.before/after.*` identity and capability fields
- `A90_EXECNS_STDERR` lines
- `A90_EXECNS_CNSS_PROC_status` fields
- `A90_EXECNS_CNSS_PROC_maps` mapped library paths
- optional V257 postflight files for pidof, netdev, status, and wifi inventory

## Validation

Static:

```text
python3 -m py_compile scripts/revalidation/wifi_cnss_live_evidence_analyzer.py
git diff --check
```

Functional:

```text
python3 scripts/revalidation/wifi_cnss_live_evidence_analyzer.py
```

Result:

```text
decision: cnss-start-only-evidence-classified
pass: True
checks: 11/11
warnings: perfd-client-unavailable, kmsg-write-denied, shell-quote-noise
```

## Classified Evidence

Critical checks all passed:

```text
runner-start-only-pass: PASS
trusted-cnss-markers: PASS
start-observable: PASS
cleanup-reaped-safe: PASS
identity-and-capability: PASS
namespace-context: PASS
proc-status-captured: PASS
maps-captured: PASS
post-pidof-absent: PASS
post-netdev-no-wlan: PASS
post-wifiinv-no-wlan-like: PASS
```

Key values:

```text
cnss_start.result=start-only-pass
cnss_start.observable=1
cnss_start.reaped=1
cnss_start.postflight_safe=1
uid/gid=1000/1000
groups=1010,3003,3005
CAP_NET_ADMIN effective=1
proc state=S (sleeping)
threads=4
```

Mapped library summary:

```text
path_count=27
apex=12
system=6
vendor=8
target=1
qmi_related=6
```

QMI/peripheral related libraries observed:

```text
/vendor/lib64/libcld80211.so
/vendor/lib64/libperipheral_client.so
/vendor/lib64/libqmi_cci.so
/vendor/lib64/libqmi_common_so.so
/vendor/lib64/libqmi_encdec.so
/vendor/lib64/libqmiservices.so
```

## Runtime Warnings

The warnings are not start-only blockers, but they guide the next work:

- `perfd-client-unavailable`: `cnss-daemon` printed `Failed to become a perfd client`.
- `kmsg-write-denied`: stderr contains `/dev/kmsg` write denial from the logging path.
- `shell-quote-noise`: stderr contains `sh: no closing quote`, likely helper instrumentation/logging shell noise.

## Decision

- V257 evidence is now machine-classified and confirms start-only lifecycle readiness.
- This does not authorize Wi-Fi scan/connect/link-up.
- Next work should either classify the perfd/property/kmsg warning surface or inspect QRTR/QMI device/socket interaction without scan/connect/link-up.
