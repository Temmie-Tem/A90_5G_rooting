# Native Init V935 mdm_helper SDX50M Queue Contract Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v935-mdm-helper-sdx50m-queue-contract/manifest.json` | `v935-mdm-helper-sdx50m-queue-property-gap-classified` |

V935 closes another service-manager ordering retry. Fresh service-manager runs
have current `cnss-daemon` Binder failures cleared, but `mdm_helper` current
worker PIDs still hit the lower SDX50M queue failure and WLFW remains absent.

## Inputs

- V934 fresh child-PID attribution:
  `tmp/wifi/v934-cnss-fresh-pid-attribution/manifest.json`.
- V931 service-manager-after-`mdm_helper` evidence:
  `tmp/wifi/v931-cnss-service-manager-matrix-live/manifest.json`.
- V933 service-manager-before-CNSS evidence:
  `tmp/wifi/v933-cnss-service-manager-before-cnss-live/manifest.json`.
- Helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`.

## Findings

| Case | Current mdm_helper queue fail | Current cnss Binder fail | Current cld80211 | Current WLFW | Property-context misses |
| --- | --- | --- | --- | --- | --- |
| V931 | `1` | `0` | `2` | `0` | `5` key families |
| V933 | `1` | `0` | `2` | `0` | `5` key families |

The repeated property lookup misses are:

- `arm64.memtag.process.mdm_helper`;
- `persist.vendor.mdm_helper.fail_action`;
- `persist.vendor.mdm_helper.timeout`;
- `persist.log.tag.mdm_helper`;
- `log.tag.mdm_helper`.

The helper property shim currently handles property-service set requests only.
It allowed the expected bounded set requests for `hwservicemanager.ready`,
`vendor.peripheral.SDX50M.state`, `vendor.peripheral.modem.state`, and
`vendor.peripheral.shutdown_critical_list`. It does not repair bionic
property-info/context lookup for read paths.

## Interpretation

The blocker is lower than service-manager ordering. Current evidence supports
this chain:

```text
service-manager present
  -> current cnss-daemon Binder failures cleared
  -> cnss-daemon reaches cld80211
  -> mdm_helper owns /dev/esoc-0 but worker reports SDX50M queue failure
  -> WLFW/BDF/wlan0 remain absent
```

The property-context gap is co-present and should be instrumented, but V935 does
not claim it is the proven root cause of the SDX50M queue failure. The next unit
should separate property-info/context readiness from per_mgr/eSoC queue
readiness before another live trigger.

## Guardrails

- Host-only classifier only.
- No device command, daemon start, service-manager start, Wi-Fi HAL, scan,
  connect, credential use, DHCP/route, or external ping.
- No eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write, boot image write, or
  partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_sdx50m_queue_contract_v935.py
python3 scripts/revalidation/native_wifi_mdm_helper_sdx50m_queue_contract_v935.py
```

## Next

V936 should be source/build-only helper work that adds bounded `mdm_helper`
lower-contract diagnostics:

- property-info/context coverage for the `mdm_helper` keys;
- observed/default values for `mdm_helper` property reads;
- SDX50M queue readiness and per_mgr state surfaces;
- no live eSoC trigger until the diagnostic contract is in place.
