# Native Init V523/V524 Companion Contract

## Summary

- target: convert Android companion-service recapture into native start-only contract
- classifier: `scripts/revalidation/native_wifi_companion_contract_v523.py`
- recapture update: `scripts/revalidation/native_wifi_android_companion_recapture_v521.py`
- lifecycle collector update: `scripts/revalidation/wifi_icnss_lifecycle_collect.py`
- V523 decision on first evidence: `v523-companion-contract-path-gap`
- V524 exact recapture handoff decision: `v522-handoff-pass`
- V523 decision after exact recapture: `v523-companion-contract-ready`
- Wi-Fi bring-up: not executed

V523 found that the original V521/V522 evidence had enough proof for
`qrtr-ns`, `pd-mapper`, `cnss_diag`, and `cnss-daemon`, but not exact native
paths for `rmt_storage` and `tftp_server`. The V521 Android filters were
widened to include `rmt_storage`, `tftp`, and `tftp_server`; then the existing
V522 handoff wrapper was rerun into a new evidence directory. The device was
rolled back to native init and verified after the Android read-only recapture.

## Evidence

Evidence roots:

```text
tmp/wifi/v523-companion-contract/
tmp/wifi/v524-android-companion-exact-recapture-handoff/
tmp/wifi/v524-android-companion-exact-recapture-handoff/v521-android-companion-recapture-run/
tmp/wifi/v524-companion-contract/
```

Key first V523 result:

```text
decision: v523-companion-contract-path-gap
pass: True
reason: required companions were observed but exact native paths are unresolved for: rmt_storage, tftp_server
```

Key V524 handoff result:

```text
decision: v522-handoff-pass
pass: True
reason: Android handoff, V521 recapture, and native rollback completed
boot_partition_write_executed: True
wifi_bringup_executed: False
```

Key post-recapture V523 result:

```text
decision: v523-companion-contract-ready
pass: True
reason: required companion service contracts have startable native candidate paths
next: implement bounded native companion start-only proof
```

## Native Rollback State

Post-handoff live native status:

```text
init: A90 Linux init 0.9.61 (v319)
boot: BOOT OK shell 4.1s
selftest: pass=11 warn=1 fail=0
exposure: guard=ok warn=0 fail=0 ncm=absent tcpctl=stopped rshell=stopped boundary=usb-local
adbd: stopped
netservice: disabled tcpctl=stopped
```

## Android Companion Contract

| order | key | native path | argv | Android state |
| --- | --- | --- | --- | --- |
| 1 | `qrtr_ns` | `/vendor/bin/qrtr-ns` | `-f` | process-running |
| 2 | `rmt_storage` | `/vendor/bin/rmt_storage` | none | process-running |
| 3 | `tftp_server` | `/vendor/bin/tftp_server` | none | process-running |
| 4 | `pd_mapper` | `/vendor/bin/pd-mapper` | none | process-running |
| 5 | `cnss_diag` | `/vendor/bin/cnss_diag` | `-q -f -t HELIUM` | process-running |
| 6 | `cnss_daemon` | `/vendor/bin/cnss-daemon` | `-n -l` | process-running |

Captured Android init service definitions:

```text
/vendor/etc/init/hw/init.qcom.rc:service vendor.qrtr-ns /vendor/bin/qrtr-ns -f
/vendor/etc/init/vendor.qti.rmt_storage.rc:service vendor.rmt_storage /vendor/bin/rmt_storage
/vendor/etc/init/vendor.qti.tftp.rc:service vendor.tftp_server /vendor/bin/tftp_server
/vendor/etc/init/hw/init.target.rc:service vendor.pd_mapper /vendor/bin/pd-mapper
/vendor/etc/init/hw/init.target.rc:service cnss_diag /system/vendor/bin/cnss_diag -q -f -t HELIUM
/vendor/etc/init/hw/init.qcom.rc:service cnss-daemon /system/vendor/bin/cnss-daemon -n -l
```

Captured Android processes:

```text
vendor_qrtr    889     1 S     qrtr-ns                     qrtr-ns -f
system         900     1 S     pd-mapper                   pd-mapper
nobody         947     1 S     rmt_storage                 rmt_storage
vendor_rfs     949     1 S     tftp_server                 tftp_server
system        1080     1 S     cnss_diag                   cnss_diag -q -f -t HELIUM
system        1177     1 S     cnss-daemon                 cnss-daemon -n -l
```

Captured Android service-state properties:

```text
[init.svc.vendor.qrtr-ns]: [running]
[init.svc.vendor.rmt_storage]: [running]
[init.svc.vendor.tftp_server]: [running]
[init.svc.vendor.pd_mapper]: [running]
[init.svc.cnss_diag]: [running]
[init.svc.cnss-daemon]: [running]
```

Captured binaries:

```text
/vendor/bin/cnss-daemon
/vendor/bin/cnss_diag
/vendor/bin/pd-mapper
/vendor/bin/qrtr-ns
/vendor/bin/rmt_storage
/vendor/bin/tftp_server
```

## Interpretation

- The companion-service gap is now concrete, not speculative.
- Android starts `rmt_storage` and `tftp_server` before the CNSS daemon reaches
  the WLFW path; the prior V521 filters under-captured these exact Samsung/QTI
  names.
- `qmiproxy` is declared as `/system/bin/qmiproxy`, but was not observed as a
  running process in the current recapture, so it stays optional until a later
  blocker proves it is required.
- The next native step should be a bounded start-only proof for the six required
  companion services above, with cleanup and no scan/connect/link-up.

## Guardrails

- Android handoff used the existing rollback wrapper and restored native init.
- V521 Android recapture remained read-only.
- V523 classifier is host-only and executed no device commands.
- No Wi-Fi HAL start, `qcwlanstate`, scan, credential, DHCP, routing, or
  external ping was executed.

## Validation

Commands run:

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_android_companion_recapture_v521.py \
  scripts/revalidation/wifi_icnss_lifecycle_collect.py \
  scripts/revalidation/native_wifi_companion_contract_v523.py

python3 scripts/revalidation/native_wifi_companion_contract_v523.py plan
python3 scripts/revalidation/native_wifi_companion_contract_v523.py run

python3 scripts/revalidation/android_companion_recapture_handoff_v522.py \
  --out-dir tmp/wifi/v524-android-companion-exact-recapture-handoff \
  --allow-android-boot-flash \
  --assume-yes \
  --i-understand-native-rollback \
  run

python3 scripts/revalidation/a90ctl.py --json status

python3 scripts/revalidation/native_wifi_companion_contract_v523.py \
  --out-dir tmp/wifi/v524-companion-contract \
  --v521-dir tmp/wifi/v524-android-companion-exact-recapture-handoff/v521-android-companion-recapture-run \
  run
```

## Next Gate

Recommended V525:

1. add guarded `wifi-companion-start-only` support to the execns helper or a
   dedicated native helper;
2. start only `qrtr-ns`, `rmt_storage`, `tftp_server`, `pd-mapper`,
   `cnss_diag`, and `cnss-daemon` in the Android-observed order;
3. observe native QRTR/QMI/WLFW/BDF/FW-ready markers;
4. clean every helper-owned process and verify no `wlan0` link-up, scan,
   credential, DHCP, route, or external ping occurred;
5. only if WLFW/BDF/FW-ready appears, proceed to a separate Wi-Fi HAL or
   `qcwlanstate` gate.
