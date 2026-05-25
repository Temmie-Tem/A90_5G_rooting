# Native Init V934 CNSS Fresh-PID Attribution Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v934-cnss-fresh-pid-attribution/manifest.json` | `v934-fresh-pid-binder-cleared-wlfw-still-missing` |

V934 corrects the V931/V933 interpretation by attributing dmesg lines to the
current helper-spawned child PIDs. The post dmesg tail can retain earlier CNSS
runs, so raw tail counts overstate current Binder failures.

## Corrected Findings

| Case | Current CNSS PID | Current Binder Failures | Stale Binder Failures | Current `cld80211` | Current WLFW | Current MDM Queue Failures |
| --- | --- | --- | --- | --- | --- | --- |
| V927 no service-manager | `785` | `18` | `38` | `2` | `0` | `0` |
| V931 after `mdm_helper` `/dev/esoc-0` fd | `952` | `0` | `18` | `2` | `0` | `1` |
| V933 before CNSS | `1016` | `0` | `18` | `2` | `0` | `1` |

The service-manager matrix runs did clear current `cnss-daemon` Binder
failures. The remaining blocker is no longer Binder ordering. Both V931 and
V933 still stop before WLFW, while `mdm_helper` reports an SDX50M event queue
failure in the same dmesg tail.

## Corrections To Prior Interpretation

- V932 selected `before-cnss` using raw dmesg-tail counts. The live test was
  still useful, but V934 shows the true blocker after V931 was already below
  Binder.
- V933 did not have `18` current Binder failures. Those lines belonged to an
  earlier `cnss-daemon` PID retained in the tail.
- V933's important result is: service managers started before CNSS, current
  Binder failures stayed `0`, `mdm_helper` reached `/dev/esoc-0`, and WLFW still
  did not appear.

## Interpretation

The next work should not be another service-manager order retry. The remaining
gap is lower:

```text
service-manager + CNSS Binder path: current PASS
CNSS cld80211 reachability: PASS
mdm_helper /dev/esoc-0 fd: PASS
mdm_helper / SDX50M queue and WLFW publication: FAIL
```

The most likely next unit is a host-only V935 classifier for `mdm_helper`
SDX50M queue and property-context inputs. The current helper transcript shows
repeated property-context misses for `mdm_helper` keys, while dmesg reports
`unable to queue event for SDX50M`. Those need to be separated before another
live gate.

## Guardrails

V934 is host-only:

- no device command;
- no daemon start;
- no service-manager start;
- no Wi-Fi HAL start;
- no scan/connect/link-up;
- no credential use;
- no DHCP, route change, or external ping;
- no eSoC ioctl, subsystem open, GPIO/sysfs/debugfs write, boot image write, or
  partition write.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_cnss_fresh_pid_attribution_v934.py
python3 scripts/revalidation/native_wifi_cnss_fresh_pid_attribution_v934.py
```

## Next

V935 should be host-only. Compare Android/Vendor `mdm_helper` property and
SDX50M queue contract against the native helper environment, especially:

- `persist.vendor.mdm_helper.*` property-context availability;
- `log.tag.*` / `persist.log.tag.*` context availability;
- `vendor.peripheral.SDX50M.*` property state and timing;
- whether `unable to queue event for SDX50M` is caused by missing property
  context, peripheral-manager queue readiness, or a lower eSoC state.
