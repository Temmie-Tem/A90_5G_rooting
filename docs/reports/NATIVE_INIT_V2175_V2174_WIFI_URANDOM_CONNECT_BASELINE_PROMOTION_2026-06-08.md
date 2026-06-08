# Native Init V2175 V2174 Wi-Fi Urandom Connect Baseline Promotion

Date: `2026-06-08`

## Summary

- Run ID: `V2175`
- Promoted baseline tag: `v2174-wifi-urandom-connect`
- Native init: `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`
- Decision: `v2175-v2174-wifi-urandom-connect-baseline-promoted`
- Device flash: `yes`
- Host commit at live flash: `5b99b453`
- Source/build report: `docs/reports/NATIVE_INIT_V2174_WIFI_URANDOM_CONNECT_SOURCE_BUILD_2026-06-08.md`
- Carrier validation report: `docs/reports/NATIVE_INIT_V2174_WIFI_URANDOM_CONNECT_LIVE_VALIDATION_2026-06-08.md`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2174_wifi_urandom_connect.img`
- Boot SHA256: `cda957e4302d66e407fc97a95932501f0ef2ac655ee264c94519111fece0b3ba`
- Previous rollback image: `workspace/private/inputs/boot_images/boot_linux_v2169_transport_contract.img`
- Previous rollback SHA256: `190b93d0741a6eeba17913c940f3bb398fed765f38532d5e0009840112166d6d`

## Promotion Evidence

V2175 flashed the V2174 boot image from the native-init bridge via TWRP/recovery
and left the device on V2174 as the current baseline.

Observed flash/verify markers:

- Local image marker matched:
  `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`.
- Local image SHA256 matched:
  `cda957e4302d66e407fc97a95932501f0ef2ac655ee264c94519111fece0b3ba`.
- Remote pushed image SHA256 matched the local SHA.
- Boot partition prefix readback SHA256 matched the local SHA.
- Post-boot `cmdv1 version` observed:
  `A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`.
- Post-boot `selftest` observed: `pass=11 warn=1 fail=0`.

Phase timings from `native_init_flash.py`:

| Phase | Seconds | OK |
| --- | ---: | --- |
| `inspect_local_image` | `0.060` | `1` |
| `native_to_recovery` | `3.705` | `1` |
| `wait_recovery_adb` | `27.129` | `1` |
| `adb_push` | `0.837` | `1` |
| `remote_sha256` | `0.107` | `1` |
| `boot_dd_write` | `0.434` | `1` |
| `boot_readback_sha256` | `0.330` | `1` |
| `flash_boot_image` | `1.707` | `1` |
| `reboot_twrp_to_system` | `2.246` | `1` |
| `verify_native_init` | `32.055` | `1` |
| `total` | `66.903` | `1` |

## Current Baseline Status

Post-promotion `cmdv1 status` confirmed:

- `init: A90 Linux init 0.9.251 (v2174-wifi-urandom-connect)`
- `boot: BOOT OK shell 5.0s`
- `selftest: pass=11 warn=1 fail=0`
- `transport.contract=1`
- `transport.serial=ready`
- `transport.ncm=ready`
- `transport.tcpctl=ready`
- `transport.upload=tcpctl-ready`
- `transport.preferred=tcpctl`
- `runtime: backend=sd ... writable=yes`
- `storage: sd present=yes mounted=yes expected=yes rw=yes`

## Scope

This promotion does not claim DHCP, route installation, DNS, external ping,
autoconnect, or long hold/idle stability. Those remain separate Wi-Fi lifecycle
follow-up gates.

V2174 is now the current Wi-Fi carrier-capable baseline. V2169 remains the
immediate rollback image.
