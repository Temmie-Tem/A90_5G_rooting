# Native Init V845 mdm3/ext-sdx50m Surface Snapshot Plan

## Goal

Capture the live read-only mdm3/ext-sdx50m eSoC GPIO/sysfs/devicetree/device-node
surface selected by V844, before any state-changing attempt to advance mdm3 or
publish WLFW service 69.

## Scope

V845 is live but read-only. It may run bounded `version`, `bootstatus`,
`selftest`, and shell read commands through the serial bridge. It must not open
raw `esoc0`, write GPIO/sysfs/debugfs, write subsystem state, bind/unbind
drivers, load/unload modules, start daemons, start service-manager, start Wi-Fi
HAL, scan/connect, use credentials, run DHCP, change routes, ping externally,
write boot images, write partitions, or flash a custom kernel.

## Inputs

- V844 boot-interface classifier:
  `tmp/wifi/v844-mdm3-ext-sdx50m-boot-interface-classifier/manifest.json`
- Current stock native runtime:
  `A90 Linux init 0.9.68 (v724)`
- Serial bridge at `127.0.0.1:54321`

## Collection Targets

V845 captures only bounded read surfaces:

1. mdm3/eSoC sysfs paths under `/sys/bus/esoc`, `/sys/devices/platform/soc/soc:qcom,mdm3`,
   `/sys/bus/msm_subsys/devices/subsys9`, and related class symlinks.
2. Access-mode matrix for candidate files such as `esoc_link`, `esoc_link_info`,
   `esoc_name`, and `subsys9/state`.
3. GPIO read surfaces for `/sys/class/gpio`, existing exported GPIOs, gpiochips,
   and `/sys/kernel/debug/gpio` if already readable.
4. Live devicetree mdm3 properties, including compatible/status/link info,
   SSCTL/sysmon IDs, and AP/MDM GPIO properties.
5. Device-node boundary for `/dev/esoc*` and `/dev/subsys*`, without opening any
   node.
6. Focused dmesg markers for mdm3/eSoC/SSCTL/sysmon/WLFW context.

## Expected Decision

Expected result: `v845-mdm3-ext-sdx50m-surface-captured`.

This means the next step can be source-backed classification of the eSoC
state-control contract. It does not authorize a write, GPIO manipulation, Wi-Fi
HAL start, scan/connect, DHCP, route change, or external ping.

## Next Gate

V846 should classify the source-backed mdm3/eSoC state-control contract from
OSRC source plus V845 access-mode evidence before any bounded write or GPIO
action.
