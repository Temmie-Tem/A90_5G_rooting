# Native Init V610 QMI Publication Precondition Plan

- date: `2026-05-23 KST`
- status: `planned`
- target: classify why Android publishes service-notifier immediately after
  modem `sysmon-qmi` while native V609 does not

## Context

V609 proved that native can reach QRTR RX, QRTR TX, and modem `sysmon-qmi` with
only the lower companion layer:

```text
qrtr_ns,rmt_storage,tftp_server,pd_mapper
```

`service-notifier`, WLAN-PD, WLFW service `69`, BDF, firmware-ready, and `wlan0`
remained absent. Because V609 did not start CNSS, service-manager, Wi-Fi HAL, or
scan/connect, the next useful step is not another live Wi-Fi userspace retry. It
is a deterministic comparison of Android and native lower QMI publication
preconditions.

## Scope

V610 is host-only by default. It reads existing Android reference evidence and
V609 native evidence. It must not contact the device, start daemons, write
`qcwlanstate`, send QMI payloads, scan/connect/link-up, use credentials, run
DHCP, change routes, ping externally, flash boot images, or write partitions.

## Inputs

- Android reference dmesg/evidence from the latest successful Android handoff
  captures, including the `sysmon-qmi` to service-notifier window.
- V609 live observer evidence:
  `tmp/wifi/v609-post-sysmon-20260523-004918/v609-observer-live/`.
- Prior classifiers V597-V609 for timing, helper-version, service-manager, and
  no-CNSS deltas.

## Analysis Targets

1. Parse Android and native dmesg windows around modem `sysmon-qmi`.
2. Compare service-notifier instance publication order and latency.
3. Compare QRTR nameservice/service IDs, especially WLFW service `69`.
4. Compare `QIPCRTR` availability and socket counts.
5. Compare rpmsg/service-registry/sysmon/subsystem surfaces if captured.
6. Preserve whether native `mss` is `ONLINE` while sibling modem/esoc surfaces
   still show `OFFLINING`.

## Decision Labels

- `v610-android-has-lower-qmi-publication-trigger`
- `v610-native-capture-insufficient`
- `v610-publication-nondeterministic`
- `v610-companion-surface-gap`
- `v610-ready-for-targeted-live-trigger`

## Success Criteria

V610 passes if it produces one explicit decision and a table showing which
lower publication precondition is present in Android but absent in native V609.

V610 fails closed if the available Android evidence is insufficient; in that
case the next gate must be Android read-only recapture, not native daemon retry.

## Next Decision

- If Android evidence identifies a missing lower companion or kernel surface,
  implement a bounded start-only proof for that one surface.
- If Android evidence is insufficient, perform a read-only Android recapture.
- If no lower delta is found, treat service-notifier publication as
  nondeterministic and require repeated bounded V609-style observations before
  CNSS or HAL work resumes.
