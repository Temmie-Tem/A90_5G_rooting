# Native Init V658 Vndbinder Surface Classifier Report

- date: `2026-05-23 KST`
- status: `classified`; Wi-Fi external ping is **not** complete
- runner: `scripts/revalidation/native_wifi_vndbinder_surface_classifier_v658.py`
- plan: `docs/plans/NATIVE_INIT_V658_VNDBINDER_SURFACE_CLASSIFIER_PLAN_2026-05-23.md`
- evidence: `tmp/wifi/v658-vndbinder-surface-classifier/`
- decision: `v658-vndservicemanager-readiness-isolation-ready`

## Scope

V658 is host-only. It reads V653, V657, V655, and V654 evidence and does not
contact the device, write sysfs, start daemons, start service-manager, start
Wi-Fi HAL, scan/connect, use credentials, run DHCP, change routes, or ping
externally.

## Result

```text
decision: v658-vndservicemanager-readiness-isolation-ready
pass: True
reason: V657 proves helper v106 can reproduce the V653 service74 gate, while V653/V657 both stop at the cnss-daemon vndbinder transaction before WLFW. V655's combined readiness+CNSS retry mode times out before service74 and amplifies cnss binder failures, so the next gate should isolate vndservicemanager readiness without the retry tail.
next: plan V659 as service74-gated vndservicemanager readiness-only proof; no fresh cnss-daemon retry, no Wi-Fi HAL, no scan/connect, no external ping
```

## Evidence Matrix

| subject | classification | evidence | next |
| --- | --- | --- | --- |
| helper v106 exact-mode replay | confirmed | V657 `service74=1`, gate `open`, wait `16ms` | do not blame helper v106 generically |
| V653/V657 binder blocker parity | confirmed | V653 `cnss_tx=1`, V657 `cnss_tx=1`, V657 `wlfw=0` | post-service74 blocker remains vndbinder transaction before WLFW |
| V655 retry mode before gate | regressed | V655 `service74=0`, `cnss_tx=33`, `service_manager_started=0` | do not retry full V655 tail unchanged |
| `vndservicemanager` readiness | still unproven | V657 readiness disabled; V655 readiness enabled but gate timed out first | isolate readiness without CNSS retry tail |
| V654 prior classification | still valid | `v654-vndbinder-readiness-gap-classified` | retain binder namespace/SELinux framing and update next gate with V657 evidence |

## Interpretation

V657 changes the post-V656 conclusion in one important way: helper v106 is not
generically unable to reproduce service `74`. The exact V653-compatible mode
works with helper v106.

The remaining blocker is not a Wi-Fi HAL or scan/connect problem yet:

```text
V653/V657: service 74 opens -> service-manager trio starts -> cnss-daemon vndbinder transaction -22 -> no WLFW
V655:      retry/readiness combined mode -> service 74 timeout -> no service-manager -> no retry tail
```

Therefore retrying V655 unchanged is low value. The next live gate should split
the combined V655 tail:

1. preserve the V657 exact service `74` gate;
2. start the service-manager trio;
3. prove `vndservicemanager` readiness explicitly;
4. do **not** start a fresh `cnss-daemon` retry in the same gate;
5. keep Wi-Fi HAL, scan/connect, credentials, DHCP, routes, and external ping
   blocked.

## Next Gate

Proceed to V659:

- helper mode: service `74` gated `vndservicemanager` readiness-only;
- no CNSS retry tail;
- success criteria: readiness observed without losing service `74` and without
  widening into Wi-Fi HAL or link-up;
- if V659 passes, the following gate can attempt a fresh `cnss-daemon` binder
  attempt after proven `vndservicemanager` readiness.
