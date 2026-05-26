# V1009 V911/V1008 Contract Comparator Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only comparator | `tmp/wifi/v1009-v911-v1008-contract-comparator/manifest.json` | `v1009-select-reduced-service-defaults-mdm-helper-isolation` |

V1009 compared V911 and V1008 without running any device command or live actor.
It selects a reduced V911-style runtime-contract retry under the current
service-defaults SELinux mode before adding CNSS, HAL, or the full service
window back.

## Evidence Split

| Signal | V911 reduced runtime-contract | V1008 full service-window |
| --- | --- | --- |
| Result | `mdm-helper-esoc-fd-observed` | `subsys-trigger-not-attempted-no-mdm-helper-esoc-fd` |
| `/dev/esoc-0` fd | `window=1 final=1` | `seen=0 max=0` |
| `/dev/subsys_esoc0` trigger | `0` | `0` |
| `mdm_helper` expected uid/gid/groups | `0/1000/1000,3010,2000` | `0/1000/1000,3010,2000` |
| `mdm_helper` target context | `u:r:vendor_mdm_helper:s0` | `u:r:vendor_mdm_helper:s0` |
| `mdm_helper` actual exec context | `kernel` | `u:r:vendor_mdm_helper:s0` |
| `per_mgr` lifecycle | `per_mgr_light` alive during window | `per_mgr` exited `0` |

## Interpretation

The positive V911 path is useful, but it is not equivalent to the current
Android service-window path. The main unresolved deltas are:

1. V911's actual execution context stayed `kernel`, while V1008 transitioned
   `mdm_helper` into `u:r:vendor_mdm_helper:s0`.
2. V911 kept `per_mgr_light` alive during the window, while V1008's full
   `per_mgr` exited cleanly before the fd predicate became true.
3. V1008 did not miss a transient fd: helper `v171` polled after `mdm_helper`
   spawn and after `cnss-daemon` spawn and still saw `0`.

Therefore the next gate should isolate these deltas before another full
service-window retry.

## Next

Plan V1010 as a bounded live gate:

1. keep the reduced V911 order: property shim, `per_mgr_light`, `mdm_helper`;
2. use helper `v171`;
3. force `--android-selinux-context-mode service-defaults`;
4. do not start service-manager, CNSS, Wi-Fi HAL, scan/connect, DHCP, routes, or
   external ping;
5. classify whether `mdm_helper` still opens `/dev/esoc-0`.

If V1010 is fd-positive, the blocker is actor ordering or `per_mgr` lifecycle in
the full service-window. If V1010 is fd-negative, the blocker is the
service-defaults SELinux/runtime input delta in the reduced path itself.

## Guardrails

V1009 was host-only:

- no device command;
- no Android boot or ADB command;
- no actor start;
- no `/dev/esoc-0`, `/dev/subsys_esoc0`, eSoC ioctl, GPIO, sysfs, or debugfs access;
- no Wi-Fi scan/connect/link-up;
- no credential use;
- no DHCP/routes;
- no external ping;
- no boot image, partition, firmware, or filesystem mutation.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_v911_v1008_contract_comparator_v1009.py
python3 scripts/revalidation/native_wifi_v911_v1008_contract_comparator_v1009.py
```

Result:

```text
decision: v1009-select-reduced-service-defaults-mdm-helper-isolation
pass: True
route: v1010-reduced-mdm-helper-runtime-contract-with-service-defaults
```
