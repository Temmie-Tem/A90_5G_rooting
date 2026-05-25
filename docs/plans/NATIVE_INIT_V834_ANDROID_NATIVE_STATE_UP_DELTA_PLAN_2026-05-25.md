# Native Init V834 Android/Native State-Up Delta Plan

## Goal

Classify the V833 Android-positive-control result against the native V830/V831
`UNINIT` results and select the next native lower-state gate without repeating
closed service-locator or listener-timing experiments.

## Why This Gate

V829 proved the service-locator path is populated:

```text
wlan/fw -> msm/modem/wlan_pd instance 180
```

V830 and V831 proved native can register the service-notifier listener for that
domain, but native still reports `UNINIT`. V833 then proved the same listener
request returns Android state `UP`. That means the payload/model is valid and
the active native gap is the lower WLAN-PD state transition.

## Scope

V834 adds a host-only classifier:

- `scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py`

Inputs:

- V775 custom-kernel boot incompatibility postmortem
- V792 known-ASoC-warning clean-DSP/CNSS lower window
- V817 lower-window mdm3/service gap
- V829 service-locator domain-list proof
- V830/V831 native service-notifier listener probes
- V833 Android service-notifier positive control

## Hard Guardrails

- Host-only: no bridge command, device command, reboot, bootloader handoff, or
  boot image write.
- No QRTR socket and no QRTR/QMI payload.
- No service-manager, Wi-Fi HAL, scan/connect/link-up, credential use, DHCP,
  route change, or external ping.
- No `esoc0` open, subsystem state write, bind/unbind, driver override, module
  load/unload, partition write, or custom-kernel flash.

## Classification Criteria

Select V835 only if:

- V829 still proves `msm/modem/wlan_pd` instance `180`;
- V830/V831 still reproduce native listener `UNINIT`;
- V833 Android positive control canonically maps raw state `0x1fffffff` to
  `UP`;
- V792 remains the best bounded native lower window with service `180/74`
  evidence and no WLFW/BDF/`wlan0`;
- custom OSRC diagnostic kernel flashing remains paused by V775.

## Validation

```bash
python3 -m py_compile \
  scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py

python3 scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py \
  --out-dir tmp/wifi/v834-android-native-state-up-delta-plan-check \
  plan

python3 scripts/revalidation/native_wifi_android_native_state_up_delta_v834.py \
  run
```

## Expected Next Gate

If V834 passes, V835 should run a bounded corrected service-notifier listener
query inside the known-ASoC-warning clean-DSP/CNSS lower window. That is the
smallest native replay that changes the lower-state precondition while still
staying below service-manager, Wi-Fi HAL, scan/connect, DHCP, routes, and
external ping.
