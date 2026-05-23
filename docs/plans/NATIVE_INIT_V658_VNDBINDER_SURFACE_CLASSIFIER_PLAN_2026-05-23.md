# Native Init V658 Vndbinder Surface Classifier Plan

- date: `2026-05-23 KST`
- cycle: `v658`
- scope: host-only classifier
- target: use V657 to update the V654 binder/runtime conclusion before another
  live retry

## Background

V657 proved that helper v106 can reproduce the V653 service `74` gate when it
uses the exact V653-compatible mode. That removes a broad "helper v106 broke
service `74`" explanation.

The remaining evidence is narrower:

```text
V653/V657: service 74 opens -> service-manager trio starts -> cnss-daemon binder -22 -> no WLFW
V655:      CNSS retry mode times out before service 74 -> no service-manager -> no retry tail
```

V658 is host-only. It determines whether the next live gate should retry V655
unchanged or isolate `vndservicemanager` readiness first.

## Guardrails

V658 must not:

- contact the device;
- write sysfs, DSP boot nodes, `qcwlanstate`, or driver state;
- open or hold `esoc0`;
- start daemons or service-manager;
- start Wi-Fi HAL, `wificond`, supplicant, or hostapd;
- scan/connect/link-up, use credentials, run DHCP, change routes, or ping
  externally.

## Inputs

- V653 positive/binder blocker:
  `tmp/wifi/v653-service74-gated-live-20260523-085337/manifest.json`
- V657 helper-v106 replay:
  `tmp/wifi/v657-service74-v106-replay-live/manifest.json`
- V655 service `74` gate timeout:
  `tmp/wifi/v655-vndservicemanager-cnss-retry-live/manifest.json`
- V654 prior binder/runtime classifier:
  `tmp/wifi/v654-binder-runtime-mismatch-classifier/manifest.json`
- Companion transcripts and dmesg deltas from the same evidence directories

## Checks

1. Confirm V657 restored service `74` under helper v106 exact V653 mode.
2. Confirm V653 and V657 both stop at `cnss-daemon` vndbinder transaction
   failure before WLFW/WLAN-PD/BDF.
3. Confirm V655 did not actually test `vndservicemanager` readiness or the fresh
   CNSS retry tail because the service `74` gate timed out first.
4. Compare binder failure amplification:
   - V653/V657: bounded transaction failure after service-manager start;
   - V655: repeated CNSS binder failures before service `74`.
5. Select the next live gate only if it keeps Wi-Fi HAL and scan/connect
   blocked.

## Success Criteria

V658 passes if it produces one of these outcomes:

- `v658-vndservicemanager-readiness-isolation-ready`
- `v658-vndbinder-surface-review-required`

Passing V658 does not authorize Wi-Fi HAL, scan/connect, credentials, DHCP,
route changes, or external ping. The expected next gate is a service `74` gated
`vndservicemanager` readiness-only proof, without the V655 CNSS retry tail.
