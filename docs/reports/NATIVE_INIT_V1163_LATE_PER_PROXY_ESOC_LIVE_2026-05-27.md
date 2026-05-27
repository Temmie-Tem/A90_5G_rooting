# Native Init V1163 Late pm-proxy eSoC Live Report

Date: `2026-05-27`

## Result

- Decision: `v1163-late-per-proxy-no-esoc-trigger`
- Pass: `true`
- Live runner: `scripts/revalidation/native_wifi_late_per_proxy_esoc_live_v1163.py`
- Helper: `a90_android_execns_probe v216`
- Current-boot prerequisites:
  - `tmp/wifi/v1163-v401-selinuxfs-mount/manifest.json`
  - `tmp/wifi/v1163-v490-policy-load/manifest.json`
- Evidence: `tmp/wifi/v1163-late-per-proxy-esoc-live-after-v490/manifest.json`
- Summary: `tmp/wifi/v1163-late-per-proxy-esoc-live-after-v490/summary.md`

## Summary

V1163 executed the bounded late `pm-proxy` gate introduced in helper `v216`.
The first run without a current-boot Android SELinux policy load classified as
`v1163-pm-service-exited-before-late-per-proxy`; that result is now treated as
a prerequisite gap, not the authoritative V1163 blocker.

After V401 `selinuxfs` mount proof and V490 native Android policy-load proof
were rerun in the same boot, the late gate became positive:

```text
upper holder + firmware mounts + Android policy load
  -> pm_proxy_helper holds /dev/subsys_modem
    -> post-PM mdm_helper holds /dev/esoc-0
      -> late pm-proxy starts
        -> pm-service remains alive with /dev/subsys_modem + /dev/vndbinder
          -> pm-service never opens /dev/subsys_esoc0
            -> no lower eSoC/MHI/ks/WLFW/service69/wlan0 artifacts
```

This narrows the active blocker from `pm-service` lifetime to the `pm-proxy`
Binder transaction/actionability gap: native can now keep the PM service alive
and start late `pm-proxy`, but the Android-good `pm-service` Binder thread path
that enters `__subsystem_get(esoc0)` is still not reproduced.

## Key Evidence

| key | value |
| --- | --- |
| `decision` | `v1163-late-per-proxy-no-esoc-trigger` |
| `firmware_mounts_executed` | `true` |
| `global_modem_holder_opened` | `true` |
| `post_pm_mdm_helper_executed` | `true` |
| `post_pm_mdm_helper_lower_trace_emitted` | `true` |
| `late.gate_mdm_helper_observable` | `1` |
| `late.gate_mdm_helper_esoc0_fd_count` | `1` |
| `late.gate_positive` | `1` |
| `late.started` | `1` |
| `late.poll_count` | `6` |
| `per_mgr_subsys_modem_count` | `1` in every late poll |
| `per_mgr_subsys_esoc0_count` | `0` in every late poll |
| `per_mgr_vndbinder_count` | `1` in every late poll |
| `pm_proxy_helper_subsys_modem_count` | `1` in every late poll |
| `pm_proxy_helper_vndbinder_count` | `0` in every late poll |
| `mss` | `OFFLINING -> ONLINE -> OFFLINE` |
| `mdm3` | `OFFLINING -> OFFLINING -> OFFLINING` |
| `qrtr_rx_seen` | `true` |
| `qrtr_services` | `{"180": 0, "69": 0, "74": 0}` |
| `lower artifacts` | no `/dev/subsys_esoc0`, MHI, `ks`, WLFW, service `69`, or `wlan0` |

The PM service snapshot showed `pm-service` alive after late `pm-proxy` start:
main/POSIX timer threads were in `do_sigtimedwait`, one `pm-service` thread was
in `do_select`, and Binder worker threads remained in `binder_ioctl_write_read`.
No poll captured a transition to `/dev/subsys_esoc0`.

## Validation

Executed prerequisites:

```bash
python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --out-dir tmp/wifi/v1163-v401-selinuxfs-mount \
  --apply --assume-yes \
  --approval-phrase "approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up" \
  run

python3 scripts/revalidation/a90ctl.py --timeout 20 mountsystem ro

python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --out-dir tmp/wifi/v1163-v490-policy-load \
  --helper-sha256 b9518555ef53f8e721f8a057c8145085b3ba91899c34609c59cb1885e8b71241 \
  --apply --assume-yes \
  --approval-phrase "approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up" \
  run
```

Executed authoritative live gate:

```bash
python3 scripts/revalidation/native_wifi_late_per_proxy_esoc_live_v1163.py \
  --out-dir tmp/wifi/v1163-late-per-proxy-esoc-live-after-v490 \
  --allow-tracefs-mount \
  --allow-tracefs-write \
  --allow-vendor-mount \
  --allow-selinuxfs-mount \
  --allow-pm-service-trigger-observer \
  --allow-cnss-daemon-start \
  --assume-yes \
  run
```

Result:

```text
decision: v1163-late-per-proxy-no-esoc-trigger
pass: True
late_per_proxy_started: True
wifi_hal_start_executed: False
wifi_bringup_executed: False
external_ping_executed: False
```

Post-cleanup device health:

```text
A90 Linux init 0.9.68 (v724)
selftest: pass=11 warn=1 fail=0
netservice: enabled=no ncm0=absent tcpctl=stopped
```

## Safety

- Allowed live scope: tracefs/vendor/selinuxfs mounts, Android policy load,
  global modem holder, PM observer, CNSS daemon start, `mdm_helper` observer,
  and late `pm-proxy` start.
- Wi-Fi HAL, scan/connect/link-up, credential use, DHCP, route, external ping,
  partition writes, boot image writes, and flash were not executed.
- Cleanup reboot completed by health proof even though the reboot command
  naturally lost its END marker during restart.

## Next Gate

V1164 should classify why late `pm-proxy` does not make `pm-service` open
`/dev/subsys_esoc0`, despite V490 policy load and positive `mdm_helper`
`/dev/esoc-0` readiness.

The most direct next checks are:

1. Compare Android V1159 `vendor.per_proxy -> pm-service Binder esoc0 get`
   against V1163-after-V490 where Binder threads stay idle.
2. Capture `pm-proxy` stdout/stderr, exit state, Binder transaction timing, and
   service/provider preconditions across a longer bounded late window.
3. Preserve V401 + V490 as mandatory current-boot preconditions for future
   PM/CNSS live gates.
