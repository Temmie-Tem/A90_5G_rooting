# Native Init V932 CNSS Service-Manager Order Delta Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| host-only classifier | `tmp/wifi/v932-cnss-service-manager-order-delta/manifest.json` | `v932-select-before-cnss-matrix-live` |

V932 compares the existing V927, V601/V603, and V931 evidence. It does not
contact the device. The result selects the next bounded live order as
`before-cnss`, using helper `v154` and the existing WLFW-precondition gate.

> Correction: V934 later re-attributed V931/V933 dmesg lines by current child
> PID and showed that raw post-tail Binder counts included stale lines from an
> earlier `cnss-daemon`. V932's selected live test was still useful, but the
> blocker interpretation is superseded by V934.

## Findings

| Case | Key Result |
| --- | --- |
| V927 no service-manager | Preserves `mdm_helper` `/dev/esoc-0` fd and reaches CNSS `cld80211`, but `cnss-daemon` repeats Binder failures and WLFW remains absent. |
| V601/V603 service-manager before CNSS | Binder transaction failures are cleared, but lower service-notifier publication still does not reach WLFW. |
| V931 after `mdm_helper` `/dev/esoc-0` fd | Preserves the lower fd window and starts service-manager/CNSS actors. V934 later corrected the current-pid Binder count to `0`; WLFW still remains absent. |

V931 improved the matrix coverage but did not satisfy the same-window
intersection: it kept the `mdm_helper` lower fd window, and V934 later proved
the current `cnss-daemon` Binder path was clear, yet WLFW/BDF/`wlan0` still did
not appear.

## Interpretation

The remaining untested intersection is service managers before CNSS while still
running the newer `mdm_helper` lower-window sequence:

```text
property-shim
  -> servicemanager + hwservicemanager + vndservicemanager
    -> pm-service
      -> mdm_helper
        -> cnss_diag + cnss-daemon
          -> WLFW-precondition gate
```

That is exactly helper `v154` matrix order `before-cnss`. It is the next
highest-value live test because:

- it preserves the V929/V930 namespace and helper fixes;
- it tests the Binder-clearing order from V601/V603;
- it still requires the WLFW precondition before `/dev/subsys_esoc0` is opened;
- it remains below Wi-Fi HAL, scan/connect, credentials, DHCP/routes, and
  external ping.

`after-cnss` is lower priority. It intentionally starts CNSS before service
managers, so it is best kept as a later negative-control order if fresh-pid
attribution ever requires another service-manager matrix.

## Guardrails

V932 is host-only:

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
python3 -m py_compile scripts/revalidation/native_wifi_cnss_service_manager_order_delta_v932.py
python3 scripts/revalidation/native_wifi_cnss_service_manager_order_delta_v932.py
```

## Next

V933 should reuse `scripts/revalidation/native_wifi_cnss_service_manager_matrix_live_v931.py`
with:

```bash
--service-manager-order before-cnss
```

Keep the same hard gates: no Wi-Fi HAL, no scan/connect, no credentials, no
DHCP/routes, no external ping, and no `/dev/subsys_esoc0` open unless the WLFW
precondition appears.
