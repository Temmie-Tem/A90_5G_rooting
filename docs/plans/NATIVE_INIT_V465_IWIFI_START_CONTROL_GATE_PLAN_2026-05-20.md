# Native Init V465 IWifi.start Control Gate Plan

Date: 2026-05-20

## Goal

Create the next native-init Wi-Fi gate after V464:

> Prove whether a minimal native `IWifi.start()`-equivalent control call can
> create a WLAN surface (`wlan0`, `phy*`, `/proc/net/wireless`, or Wi-Fi rfkill)
> without credentials, scan/connect, DHCP, route changes, or external packets.

This is still **not** the final Wi-Fi connect/ping gate.  It is the missing
surface-creation gate that must pass before credential use is allowed.

## Inputs

- V462 native connect/ping gate:
  - result: `v462-native-wifi-ping-blocked-no-wlan-surface`
  - conclusion: no native WLAN surface means no credential/scan/ping attempt.
- V463 blocker refresh:
  - result: `wifi-service-order-replay-model-ready`
  - conclusion: first missing native event is Android's Wi-Fi action path.
- V464 surface composite:
  - result: `v464-native-wlan-surface-not-observed`
  - conclusion: service-manager + Wi-Fi HAL + `cnss-daemon` process lifetime is
    clean but insufficient.

## Reference Basis

- AOSP Wi-Fi HAL defines `IWifi.start()` as the setup call that makes the Wi-Fi
  HAL usable and should trigger start notification on success:
  <https://android.googlesource.com/platform/hardware/interfaces/+/master/wifi/1.0/IWifi.hal>
- Android Wi-Fi architecture separates vendor Wi-Fi HAL, supplicant HAL, and
  hostapd HAL surfaces:
  <https://source.android.com/docs/core/connect/wifi-hal>
- Qualcomm ICNSS/WLFW readiness depends on firmware/QMI/BDF readiness, so
  process start alone is not enough:
  <https://android.googlesource.com/kernel/msm/+/15cf51a0f2ebde6529357685543e0b4170fb3b5c/drivers/soc/qcom/icnss.c>

## Design

V465 should split into two artifacts:

1. **Static/host HIDL contract mapper**
   - consumes AOSP `IWifi.hal` and local generated/Android evidence;
   - determines the safest native transaction strategy:
     - generated HIDL client binary, if buildable from available headers;
     - existing Android `lshal`/service-manager mediation, if usable;
     - raw hwbinder transaction only if the ABI/transaction code is proven.
2. **Bounded native live runner**
   - starts the V464 private runtime;
   - issues exactly one `IWifi.start()`-equivalent call;
   - snapshots only WLAN surface state before/during/after;
   - cleans all child processes;
   - refuses to read credentials or send packets.

## Guardrails

- No SSID/password read.
- No `wpa_supplicant` network configuration.
- No scan/connect/link-up request.
- No DHCP, DNS, route, or external ping.
- No rfkill write, driver bind/unbind, module load/unload, firmware mutation,
  Android partition write, persistent boot autostart, or unbounded daemon.
- If any process or WLAN surface leaks after cleanup, stop and require manual
  review before further Wi-Fi work.

## Live Decision Labels

- `v465-iwifi-start-plan-ready`
- `v465-iwifi-start-preflight-ready`
- `v465-iwifi-start-contract-blocked`
- `v465-iwifi-start-approval-required`
- `v465-iwifi-start-surface-observed-cleaned`
- `v465-iwifi-start-no-surface-delta`
- `v465-iwifi-start-surface-leaked`
- `v465-iwifi-start-review-required`

## Completion Criteria

V465 is successful only if all are true:

1. helper/client contract is explicit and reproducible;
2. live run starts only the bounded private runtime;
3. one `IWifi.start()`-equivalent call is attempted;
4. `wlan0`, `phy*`, `/proc/net/wireless`, or Wi-Fi rfkill appears during the
   observation window;
5. postflight cleanup is clean;
6. V462 rerun changes from `blocked-no-wlan-surface` to a visible-surface state.

If V465 does not create a WLAN surface, the next branch should be Android
framework mediation rather than daemon start widening.

## Validation Commands

```text
python3 -m py_compile scripts/revalidation/native_wifi_surface_composite_v464.py
python3 -m py_compile scripts/revalidation/wifi_iwifi_start_contract_v465.py
git diff --check
python3 scripts/revalidation/native_wifi_connect_ping_v462.py preflight
python3 scripts/revalidation/wifi_iwifi_start_contract_v465.py plan
python3 scripts/revalidation/wifi_iwifi_start_contract_v465.py preflight
python3 scripts/revalidation/native_wifi_connect_ping_v462.py preflight
```

## V465 Contract Mapper Result

Implemented:

```text
scripts/revalidation/wifi_iwifi_start_contract_v465.py
```

Latest validated preflight:

```text
tmp/wifi/v465-iwifi-start-contract-preflight-20260520-234757/
decision: v465-iwifi-start-contract-ready-raw-hwbinder-next
```

Conclusion:

- Generated HIDL client path is not available in this repo because `hidl-gen`
  and generated `IWifi` headers are absent.
- Existing Android tools are not a valid native-init substitute: `lshal` can
  enumerate/wait/status services, while `cmd`/`svc` require Android framework
  services.
- Next implementation should be V466 helper `v32` with a raw hwbinder
  `IServiceManager.get` + `IWifi.start()` primitive.
