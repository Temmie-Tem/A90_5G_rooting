# Native Init V1175 PM Ack FD Target Live Plan

Date: `2026-05-27`

## Goal

Decode the device fd opened by the V1174 PM-service state-2 ack body.  V1174
proved the `pm-service+0x8788` state-transition body opens a device and receives
fd `8`, then moves PM state to `3`, but `/dev/subsys_esoc0`, mdm3, WLFW, and
`wlan0` still do not appear.  V1175 samples `/proc/<pm-service>/fd` during the
same bounded live window to classify fd `8`.

## Preconditions

- Native v724 is healthy.
- Serial bridge is available on `127.0.0.1:54321`.
- V401 selinuxfs mount and V490 policy-load proof are rerun in the same boot.
- Helper `a90_android_execns_probe v217` remains deployed.
- V1174 live result is `v1174-state2-open-success-state3-no-esoc0`.

## Added Collection

V1175 reuses the V1174 uprobes and adds one collector-side sampler:

| item | source | purpose |
| --- | --- | --- |
| `pm_ack_state2_open_result` | tracefs uprobe | records the opened fd, expected `8` |
| `sample_pm_service_fds` | `/proc/<pm-service>/fd` | maps each live fd to its symlink target |
| `pm_service_fd_sample` | collector output | stores `index`, `fd`, and `target` in the manifest |

The live run uses a denser bounded sampling window so the fd table is captured
while PM-service is still alive:

```text
--thread-sample-count 120
--thread-sample-interval-sec 0.1
```

## Success Criteria

- Manifest decision is one of:
  - `v1175-state2-opened-subsys-modem-not-esoc0`
  - `v1175-state2-opened-subsys-esoc0`
  - `v1175-state2-opened-other-fd-target`
  - `v1175-subsys-modem-fd-seen-fd8-missed`
  - `v1175-subsys-esoc0-fd-seen-fd8-missed`
  - `v1175-pm-service-fd-sample-missing`
- V1174 state-2 open success is reproduced.
- PM-service fd samples and fd `8` targets are recorded when visible.
- Cleanup returns to native v724 health.
- No Wi-Fi HAL, scan/connect, credential use, DHCP, route, external ping,
  partition write, boot image write, or flash is performed.

## Next Branches

- fd `8` is `/dev/subsys_modem`: compare Android state-3 post-open actor that
  later opens or requests mdm3/eSoC.
- fd `8` is `/dev/subsys_esoc0`: move to bounded MHI/WLFW/BDF publication gate.
- fd `8` is another target or missed: align fd sampling with the open result or
  fetch the `device_path` string directly from tracefs if supported.
