# Native Init V691 Peripheral Post-Property Exit Classifier Report

## Result

- decision: `v691-provider-post-property-exit-classified`
- pass: `true`
- evidence: `tmp/wifi/v691-peripheral-post-property-exit-classifier/`
- device commands: `false`
- device mutations: `false`
- Wi-Fi bring-up: `false`
- external ping: `false`

## Classification

V691 used the existing V690 evidence only. The exact private property ack
remained clean:

| name | value | allowed | result |
| --- | --- | ---: | --- |
| `hwservicemanager.ready` | `true` | `1` | `0x00000000` |
| `vendor.peripheral.SDX50M.state` | `OFFLINE` | `1` | `0x00000000` |
| `vendor.peripheral.modem.state` | `OFFLINE` | `1` | `0x00000000` |

No `Unable to set property ... 0x18` line remained.

## Provider Exit Surface

The provider children were observable but did not persist:

| child | pid | observable | exit_code | signal | fd_count | vndbinder |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `per_mgr` | `839` | `1` | `0` | `0` | `8` | `1` |
| `per_proxy` | `1010` | `1` | `1` | `0` | `0` | `0` |
| `cnss_daemon_retry` | `1179` | `1` | `-1` | `9` | `16` | `1` |

The post-window process snapshot had no residual provider or companion service
processes:

| process | count |
| --- | ---: |
| `pm-service` | `0` |
| `pm-proxy` | `0` |
| `vndservicemanager` | `0` |
| `cnss-daemon` | `0` |
| `cnss_diag` | `0` |
| `qrtr-ns` | `0` |
| `pd-mapper` | `0` |

This means `pm-service` exit `0` is not enough to prove a persistent provider
registration, and `pm-proxy` still exits with status `1`.

## Remaining Noise

The remaining property denials are property-read context misses, mostly logging
and linker debug properties:

| property | count |
| --- | ---: |
| `persist.log.tag.PerMgrSrv` | `30` |
| `log.tag.PerMgrSrv` | `30` |
| `debug.ld.app.pm-service` | `20` |
| `debug.ld.app.pm-proxy` | `20` |
| `persist.log.tag.PerMgrProxy` | `4` |
| `log.tag.PerMgrProxy` | `4` |
| `arm64.memtag.process.pm-service` | `2` |
| `arm64.memtag.process.pm-proxy` | `2` |

These are no longer the same blocker as the V688/V690
`vendor.peripheral.*.state` write denial. They should not be broadened blindly
before the provider exit/registration path is observed.

## Wi-Fi Markers

The lower path still stops before WLFW:

| marker | count |
| --- | ---: |
| service-notifier `180` | `1` |
| service-notifier `74` | `1` |
| `cnss-daemon` netlink | `10` |
| `cnss-daemon` `cld80211` | `4` |
| Binder transaction failed | `1` |
| QMI server connected | `0` |
| WLFW start/request | `0` |
| BDF `regdb`/`bdwlan` | `0` |
| WLAN firmware ready | `0` |
| `wlan0` | `0` |

## Guardrails

- no bridge or device command;
- no helper deploy;
- no daemon or service start;
- no Wi-Fi HAL, wificond, supplicant, hostapd, scan/connect, DHCP, route,
  credential, or external ping;
- no boot image or partition write.

## Next Gate

V692 should add targeted provider exit/registration capture before changing
more functionality:

1. capture `pm-service`/`pm-proxy` exit path with a bounded provider-only or
   provider-focused mode;
2. snapshot vndservicemanager service registry around provider start;
3. preserve the exact private property ack from V690;
4. keep Wi-Fi HAL, credentials, scan/connect, DHCP, route changes, and external
   ping blocked.
