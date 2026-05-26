# V1020 After-Fd Subsystem Window Live Plan

- date: `2026-05-26`
- type: bounded live gate
- selected after: V1019 helper `v173` deploy
- helper: `a90_android_execns_probe v173`

## Objective

Run the V1018/V1019 scoped subsystem-window support on-device, using the
fd-positive V1016 upper surface but opening `/dev/subsys_esoc0` only after the
full upper stack has started and WLFW is still absent.

Order:

```text
after-mdm-helper-esoc-fd-with-wifi-surface-subsys-window
```

Gate:

```text
post-upper-surface-no-wlfw
```

## Rationale

V1016 proved that native init can start:

- `mdm_helper` with `/dev/esoc-0` fd predicate
- service-manager trio
- Wi-Fi HAL legacy/ext
- `wificond`
- `cnss_diag`
- `cnss-daemon`

but WLFW/BDF/`wlan0` never appeared and the helper did not open
`/dev/subsys_esoc0`.

Android dmesg shows `/dev/subsys_esoc0` acquisition in the same narrow window
as `cnss-daemon wlfw_start`. Therefore, waiting for WLFW before opening
`/dev/subsys_esoc0` can be a circular gate. V1020 tests the corrected scoped
window directly.

## Live Scope

V1020 permits only:

- read-only `/system` mount preparation
- bounded selinuxfs mount/cleanup
- private property root use
- `/vendor/bin/pm-service`
- `/vendor/bin/mdm_helper`
- service-manager trio
- Wi-Fi HAL legacy/ext
- `wificond`
- `/vendor/bin/cnss_diag`
- `/vendor/bin/cnss-daemon -n -l`
- post-upper-surface no-WLFW-gated `/dev/subsys_esoc0` child open
- cleanup reboot if a child remains unproven stopped

## Hard Gates

- no `IWifi.start`
- no `qcwlanstate` write
- no scan/connect/link-up
- no credential use
- no DHCP, route, or external ping
- no raw eSoC controller ioctl
- no controller notify or BOOT_DONE
- no GPIO/sysfs/debugfs write
- no module load/unload
- no boot image, partition, or firmware write

## Success Criteria

Pass is one of:

- `v1020-post-upper-surface-subsys-trigger-clean`
- `v1020-wlfw-precondition-observed-trigger-clean`
- `v1020-reboot-required-cleaned` with healthy post-reboot state

The main diagnostic outputs are:

- whether `/dev/subsys_esoc0` was opened
- child `wchan`/stack if it stalls
- WLFW/BDF/`wlan0` presence or absence after the scoped window
- cleanup reboot health if required

## Validation

Run:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_after_fd_subsys_window_live_v1020.py
python3 scripts/revalidation/native_wifi_after_fd_subsys_window_live_v1020.py \
  --out-dir tmp/wifi/v1020-after-fd-subsys-window-plan \
  plan
python3 scripts/revalidation/native_wifi_after_fd_subsys_window_live_v1020.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-cleanup-reboot \
  --assume-yes \
  run
git diff --check
```

