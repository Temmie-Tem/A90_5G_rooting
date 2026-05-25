# Native Init V936 mdm_helper Lower-Contract Support Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper source/build verifier | `tmp/wifi/v936-mdm-helper-lower-contract-support/manifest.json` | `v936-mdm-helper-lower-contract-support-pass` |
| helper artifact | `tmp/wifi/v936-execns-helper-v155-build/a90_android_execns_probe` | `sha256=44d7820e7bc33ab9886ea4f5f39248b1902c404c694c48fcd00a3ecc0fb76063` |

V936 adds bounded lower-contract diagnostics to the existing
`wifi-companion-mdm-helper-runtime-contract-capture` helper mode. It does not
add a new live trigger or expand Wi-Fi bring-up behavior.

## Implementation

- Helper marker advanced to `a90_android_execns_probe v155`.
- Added `mdm_helper_lower_contract` snapshots inside the existing
  runtime-contract mode at:
  - `runtime_contract_before`;
  - `runtime_contract_window`;
  - `runtime_contract_final`;
  - `runtime_contract_after`.
- Added bounded scans for property-context coverage of:
  - `arm64.memtag.process.mdm_helper`;
  - `persist.vendor.mdm_helper.fail_action`;
  - `persist.vendor.mdm_helper.timeout`;
  - `persist.log.tag.mdm_helper`;
  - `log.tag.mdm_helper`.
- Added read-only path stats for private property root, property service socket,
  private `/dev/esoc-0`, eSoC sysfs, and MSM subsystem sysfs surfaces.

## Why This Is The Right Next Step

V935 established that current service-manager matrix runs clear fresh
`cnss-daemon` Binder failures but still leave WLFW absent while `mdm_helper`
reports `unable to queue event for SDX50M`. The property-context misses are
co-present but not proven as the root cause.

V936 gives the next live runtime-contract capture enough evidence to separate:

- missing bionic property-info/context data;
- private property root and property-service socket readiness;
- private `/dev/esoc-0` device-node readiness;
- per_mgr/eSoC queue readiness.

## Guardrails

- Source/build-only unit.
- No device command, daemon start, service-manager start, Wi-Fi HAL, scan,
  connect, credential use, DHCP/route, or external ping.
- No eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write, boot image write, or
  partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_lower_contract_support_v936.py
python3 scripts/revalidation/native_wifi_mdm_helper_lower_contract_support_v936.py
```

Verifier checks passed:

- helper marker `v155`;
- bounded property-context key scan;
- lower path stats;
- runtime snapshots inserted;
- no new trigger or Wi-Fi bring-up path;
- static ARM64 helper build;
- artifact strings confirm `mdm_helper_lower_contract`.

## Next

Deploy helper `v155` only. After deploy, run a bounded
`wifi-companion-mdm-helper-runtime-contract-capture` live capture to collect the
new lower-contract evidence before any eSoC trigger retry.
