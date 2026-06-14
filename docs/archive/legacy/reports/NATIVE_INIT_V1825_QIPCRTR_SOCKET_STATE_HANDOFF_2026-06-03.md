# Native Init V1825 QIPCRTR Socket-State Handoff

## Summary

- Cycle: `V1825`
- Type: one-run rollbackable passive QIPCRTR socket-state discriminator
- Decision: `v1825-qipcrtr-socket-open-getname-close-passive-rollback-pass`
- Result: PASS
- Reason: AF_QIPCRTR opened, getsockname succeeded, and the socket closed without lookup/control payload while service74 and wlan_pd stayed absent
- Evidence: `tmp/wifi/v1825-qipcrtr-socket-state-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`
- Post-rollback version evidence: `tmp/wifi/v1825-qipcrtr-socket-state-handoff/post-rollback-version-filtered.stdout.txt`
- Post-rollback selftest evidence: `tmp/wifi/v1825-qipcrtr-socket-state-handoff/post-rollback-selftest.stdout.txt`

## Post-Run Native Verification

- Version: `A90 Linux init 0.9.68 (v724)`
- Selftest: `pass=11 warn=1 fail=0`

## Gate Label

- QIPCRTR socket label: `qipcrtr-socket-open-getname-close-passive`
- service74 raw label: `service74-raw-absent`
- PM-client return label: `pm-client-return-success`
- lower-state label: `stable-mdm3-offlining`
- safety ok: `True`

## Socket State

- mode/family/type: `passive-open-getsockname-close` / `AF_QIPCRTR` / `SOCK_DGRAM`
- open rc/errno/error: `0` / `` / ``
- getsockname rc/family/node/port: `0` / `42` / `1` / `0`
- close rc/errno/error: `0` / `` / ``
- socket counts before/after-open/after-close: `0` / `0` / `0`
- count rises only while open: `False`
- no bind/connect/send/lookup/control/service-start: `1` / `1` / `1` / `1` / `1` / `1`
- `before_open` qipcrtr present/size/sockets: `1` / `1416` / `0`
- `after_open` qipcrtr present/size/sockets: `1` / `1416` / `0`
- `after_close` qipcrtr present/size/sockets: `1` / `1416` / `0`

## Registry And Publication State

- registry readable: `False`
- proc_net_qrtr open counts: `0,0,0`
- service-locator/domain/wlan-fw/wlan-pd-domain/qmi-server: `2,2,2` / `0,0,0` / `0,0,0` / `0,0,0` / `0,0,0`
- service180/service74/wlan_pd raw: `1,1,1` / `0,0,0` / `0,0,0`
- precondition pd-mapper/subsys/pil/qmi/wlfw: `0,0,0` / `9,10,10` / `5,5,5` / `7,7,7` / `30,30,30`

## Lower State

- early/late service-notifier state: `uninit` / `uninit`
- mdm3/MHI/WLFW69/wlan0: `OFFLINING` / `False` / `False` / `False`
- PM-client register/connect/return-path rc: `0` / `0` / `0`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1824/dev/__properties__`
- Transport: `serial-uudecode-tar-gz`
- Uploaded files/bytes: `22` / `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- The route opened one passive AF_QIPCRTR datagram socket, called `getsockname`, and closed it without bind, connect, send, QRTR lookup, QRTR control payload, or service start.
- The route did not open `/dev/subsys_esoc0`, did not fake ONLINE, and did not write PMIC/GPIO/GDSC controls.
- Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, `boot_wlan`, restart-PD request, forced RC1, eSoC notify, BOOT_DONE spoof, PCI rescan, and platform bind/unbind were not used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Stop after this one label; do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
