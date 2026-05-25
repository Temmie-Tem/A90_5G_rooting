# Native Init V830 Service-notifier Listener Probe Plan

## Goal

Use the V829 service-locator result to send one bounded service-notifier
`REGISTER_LISTENER` request for `msm/modem/wlan_pd` instance `180`, then parse
the current-state response and any immediate state indication.

## Basis

- V829 proved `GET_DOMAIN_LIST wlan/fw` succeeds through service-locator
  `64/257`.
- The returned domain is `msm/modem/wlan_pd` with instance `180`.
- Samsung OSRC service-notifier uses service `66`, version `1`, encoded
  instance `1 | (180 << 8) = 46081`.
- `REGISTER_LISTENER` response TLV `0x10` carries the current state.

## Implementation

- Bump exec namespace helper to `a90_android_execns_probe v127`.
- Add `--allow-service-notifier-listener-probe`.
- Discover service-notifier endpoint through AF_QIPCRTR lookup of `66/46081`.
- Send only this QMI request:

```text
00 01 00 20 00 18 00 01 01 00 01 02 11 00
6d 73 6d 2f 6d 6f 64 65 6d 2f 77 6c 61 6e 5f 70 64
```

- Parse register response result/error and current state.
- If a `STATE_UPDATED` indication appears in the bounded window, ACK it and
  record its state.

## Guardrails

- No service-manager start.
- No Wi-Fi HAL, wificond, supplicant, scan, connect, link-up, DHCP, route, or
  external ping.
- No credentials.
- No `esoc0` open, qcwlanstate write, bind/unbind, driver override, module
  load/unload, boot image write, partition write, or custom-kernel flash.
- Cleanup reboot remains required after the bounded live window.

## Commands

```bash
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v830-execns-helper-v127-build/a90_android_execns_probe

python3 scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  --out-dir tmp/wifi/v830-service-notifier-listener-plan-check \
  plan

python3 scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  --out-dir tmp/wifi/v830-service-notifier-listener-preflight \
  preflight

python3 scripts/revalidation/native_wifi_service_notifier_listener_probe_v830.py \
  --out-dir tmp/wifi/v830-service-notifier-listener-run \
  run
```

## Decision

- `state-up`: proceed to WLFW service `69/1` observer before HAL/connect.
- `state-not-up`: classify modem/WLAN-PD online trigger gap.
- `no-response` or response error: classify service-notifier endpoint/QMI
  transaction routing before wider retries.
