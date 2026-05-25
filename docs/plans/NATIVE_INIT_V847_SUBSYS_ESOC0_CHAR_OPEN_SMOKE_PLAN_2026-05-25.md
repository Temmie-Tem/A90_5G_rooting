# Native Init V847 subsys_esoc0 Char-Device Open Smoke Plan

## Goal

Run the V846-selected userspace boot contract once: materialize only the
`subsys_esoc0` char-device advertised by V845, attempt a bounded open/hold, and
capture whether mdm3/eSoC advances toward MHI/WLFW service 69.

## Scope

V847 is a live bounded mutation. It may create `/dev/subsys_esoc0` from V845's
major/minor, start one background open/hold process, capture state/dmesg
evidence, remove the node, and reboot for cleanup. It must not open raw
`/dev/esoc*`, write sysfs/GPIO/debugfs, bind/unbind drivers, load/unload
modules, start daemons, start service-manager, start Wi-Fi HAL, scan/connect,
use credentials, run DHCP, change routes, ping externally, write boot images,
write partitions, or flash a custom kernel.

## Inputs

- V846 state-control contract classifier:
  `tmp/wifi/v846-mdm3-esoc-state-control-contract/manifest.json`
- V845 uevent contract: `subsys_esoc0`, major `236`, minor `9`
- Current stock native runtime:
  `A90 Linux init 0.9.68 (v724)`

## Live Contract

V847 runs with explicit flags:

```bash
--allow-mknod --allow-subsys-char-open --allow-reboot-cleanup --assume-yes
```

The live sequence is:

1. Verify native health and V846 input.
2. Create `/dev/subsys_esoc0` as char device `236:9`.
3. Start a background holder that opens the node and holds it briefly.
4. Capture holder status, mdm3/mss state, crash count, and focused dmesg.
5. Remove the node and kill any residual holder process.
6. Reboot and verify native health.

## Expected Decisions

- `v847-subsys-esoc0-open-advanced-mdm3-surface`: open completed and produced
  mdm3/MHI/WLFW-adjacent progress.
- `v847-subsys-esoc0-open-no-wlfw-progress`: open completed but no WLFW progress.
- `v847-subsys-esoc0-open-blocked-or-pending`: open did not report success
  inside the bounded window but cleanup reboot restored health.

## Next Gate

If the open blocks or does not advance WLFW, V848 should be host-only first:
classify dmesg/state evidence and choose whether to add in-window task
stack/wchan capture, inspect ext-mdm provider behavior, or defer to another
source-backed trigger.
