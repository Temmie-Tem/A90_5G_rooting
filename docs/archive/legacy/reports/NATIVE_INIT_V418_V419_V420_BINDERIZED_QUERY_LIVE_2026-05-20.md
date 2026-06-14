# Native Init V418-V420 Binderized Query Live

Date: 2026-05-20

## Scope

This pass executed the next bounded Wi-Fi investigation gates after V417:

- V418 deployed helper v27 to `/cache/bin/a90_android_execns_probe`.
- V419 ran the bounded binderized `lshal` registration query.
- V420 routed the post-live result back through the registration router,
  static/runtime comparator, and current gate packet.

The live query did start the bounded private namespace trio needed for the
query gate.  It did not scan, connect, link up, configure credentials, run DHCP,
change routing, or bring up Wi-Fi.

## Evidence

```text
tmp/wifi/v418-v411-helper-v27-deploy-live-20260520-123040/
tmp/wifi/v419-v411-binderized-lshal-query-live-20260520-123721/
tmp/wifi/v419-postflight-clean-20260520-124100/
tmp/wifi/v420-registration-router-live-query-20260520-123842/
tmp/wifi/v420-runtime-static-comparator-live-query-20260520-123842/
tmp/wifi/v420-current-gate-packet-post-live-20260520-124014/
```

## V418 Deploy Result

```text
decision: v411-deploy-query-executor-deploy-pass
deploy_decision: execns-helper-v27-deploy-pass
pass: True
method: serial appendfile + uudecode
chunks_written: 783
encoded_bytes: 1094882
device_mutations: True
daemon_start_executed: False
wifi_hal_start_executed: False
wifi_bringup_executed: False
post_deploy_preflight: v411-hal-registration-query-preflight-ready
```

The NCM reachability check warned during the deploy preflight, so the helper
was installed through the serial fallback path.  The post-deploy V411 preflight
then passed with helper v27 present.

## V419 Live Query Result

```text
decision: v411-hal-registration-query-runtime-gap
pass: True
reason: service query failed: lshal-timeout
service_query_result: service-query-timeout
service_query_reason: lshal-timeout
all_postflight_safe: True
postflight.clean: True
postflight.processes: []
postflight.wifi_links: []
device_mutations: True
daemon_start_executed: True
wifi_hal_start_executed: True
wifi_bringup_executed: False
```

The helper started the bounded namespace and launched the binderized-only
`lshal list --types=binderized --neat` query child.  The child timed out and
was terminated with signal 15.  The result is a runtime gap, not a registration
match.

The immediate postflight clean check also passed:

```text
status: rc=0 status=ok fail=0
selftest: rc=0 status=ok fail=0
process_hits: 0
wifi_links: 0
```

## V420 Routing Result

```text
v412: v412-registration-router-micro-query-needed
v415: v415-runtime-static-comparator-micro-query-needed
v416_post_live: v416-current-gate-micro-query-needed
next_gate: micro-hwservicemanager-query-plan
primary_target: vendor.samsung.hardware.wifi@2.0-2::ISehWifi/default
```

Primary runtime match patterns remain:

```text
vendor.samsung.hardware.wifi@2.0::ISehWifi/default
vendor.samsung.hardware.wifi@2.1::ISehWifi/default
vendor.samsung.hardware.wifi@2.2::ISehWifi/default
```

## Tooling Fix

`scripts/revalidation/wifi_v416_current_gate_packet.py` now accepts both
pre-deploy and post-live bounded V411 evidence.  The packet still executes no
device command itself and still blocks any input evidence that shows Wi-Fi
bring-up.  This fixes the earlier false `v416-current-gate-packet-blocked`
result for valid V418/V419 bounded live inputs.

## Interpretation

The V411 path successfully advanced past the helper-deploy gate.  The
binderized `lshal` query remains too broad or too slow in this private runtime
namespace, so the next useful step is narrower than another `lshal` retry:

```text
V421: design and implement a micro hwservicemanager/HIDL query using the V414
primary Samsung Wi-Fi HAL target patterns.
```

That next gate should remain no-scan/no-link/no-Wi-Fi-bring-up and should only
prove whether the target Samsung Wi-Fi HAL service is visible or retrievable
through the minimal service-manager path.
