# Native Init V670 Android/native Wi-Fi Service-order Delta Plan

- date: `2026-05-24 KST`
- cycle: `V670`
- status: planned
- script: `scripts/revalidation/native_wifi_android_service_order_delta_v670.py`

## Goal

V669 classified the runtime gap: Android advances from CNSS into WLFW/BDF and
`wlan0`, while native V668 sees icnss/QCA6390 platform devices but remains
before WLFW. V670 determines whether the next live mutation should target
Android service ordering rather than another raw CNSS retry.

## Scope

V670 is host-only. It consumes:

- V668 native companion order;
- V669 runtime-delta result;
- V206 Android props, process context, and init rc evidence;
- V649 Android dmesg service-start timing where available.

## Guardrails

V670 does not authorize:

- device commands or live mutation;
- service start or Wi-Fi HAL start;
- scan/connect/link-up, credentials, DHCP, routes, or external ping;
- boot image or partition writes.

## Success Criteria

The classifier passes if it proves:

- Android has Wi-Fi HAL legacy/ext, `cnss_diag`, and `wificond` running before
  `cnss-daemon`;
- Android init rc has service definitions for the relevant services;
- Android process contexts are captured;
- V668 native order lacks Wi-Fi HAL and `wificond`;
- supplicant is late and remains blocked until `wlan0` exists.

## Commands

```bash
python3 scripts/revalidation/native_wifi_android_service_order_delta_v670.py \
  --out-dir tmp/wifi/v670-android-service-order-delta-plan \
  plan

python3 scripts/revalidation/native_wifi_android_service_order_delta_v670.py \
  --out-dir tmp/wifi/v670-android-service-order-delta \
  run
```

## Next

If V670 classifies the order delta, the next live gate should be a
service74-gated Android userspace-order start-only proof: service-manager
surface plus Wi-Fi HAL/wificond before fresh CNSS retry, while keeping
supplicant, scan/connect, DHCP, routes, credentials, and external ping blocked.
