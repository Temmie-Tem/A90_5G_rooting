# V1045 PM/PIL Prerequisite Delta Classifier

- date: `2026-05-26`
- scope: host-only classifier over V1043 PM full-contract, V1044 summary, v724 init source, and OSRC PIL source
- decision: `v1045-pm-pil-prereq-modem-count-zero-classified`
- pass: `True`
- evidence: `tmp/wifi/v1045-pm-pil-prerequisite-delta/manifest.json`

## Summary

V1045 classifies why native `pm_proxy_helper` blocks in `pil_boot/flush_work` while
Android reaches the `/dev/subsys_modem` fd contract.

Root cause: native v724 init boots the modem via `v641_run_sibling_ssctl_once()` using
SSCTL sysfs writes, **not** `subsys_device_open()`. This leaves the subsys modem
refcount at 0. When `pm_proxy_helper` opens `/dev/subsys_modem`, `__subsystem_get()`
sees count=0 and calls `subsys_start()` → `subsys_powerup()` → `pil_boot()`, which
then blocks at `pil_load_segs/flush_work` — attempting a redundant PIL boot on an
already-SSCTL-running modem.

Android boots the modem via its init service path (`subsys_device_open`), bringing
modem count to ≥1. When `pm_proxy_helper` opens `/dev/subsys_modem`, it just
increments the count and returns immediately.

## Root Cause

### Native v724 Modem Boot Mechanism

`v641_run_sibling_ssctl_once()` in v724 init:

- Armed via one-shot flag file `/cache/native-init-sibling-fwssctl-v641`
- Calls `v641_prepare_firmware_mounts()` — mounts `sda29` → `/vendor/firmware_mnt`
- Calls `v641_sibling_ssctl_child()` — writes to SSCTL sysfs nodes
- **Does NOT open `/dev/subsys_modem`** → subsys modem refcount stays 0

### pm_proxy_helper PIL Boot Block Chain

```
pm_proxy_helper open(/dev/subsys_modem)
  → subsys_device_open()
    → __subsystem_get() [count=0]
      → subsys_start()
        → subsys_powerup()
          → pil_boot()
            → proxy_vote → init_image → mem_setup → hyp_assign
              → pil_load_segs()
                → flush_work()  ← D-state block
```

The `flush_work()` block in `pil_load_segs` is a redundant PIL boot attempt on an
already-running modem. The firmware segment load hangs, likely because modem memory
regions are in use or the hypervisor assignment conflicts with the existing SSCTL boot.

### Android Contrast

Android boots modem via standard init service path using `subsys_device_open()`,
completing modem PIL boot and leaving count ≥1. When `pm_proxy_helper` later opens
`/dev/subsys_modem`, count≥1 → `__subsystem_get()` skips `subsys_start()` → returns
immediately with incremented count.

## Checks

| check | value |
| --- | --- |
| v1043_input_present | True |
| v1044_summary_present | True |
| v724_ssctl_modem_boot | True |
| v724_ssctl_is_oneshot_gated | True |
| v724_subsys_modem_fd_held_in_init | False |
| v724_firmware_mount_present | True |
| pil_flush_work_at_segment_load_phase | True |
| pil_hyp_assign_before_flush | True |
| v1043_pm_proxy_helper_started | True |
| v1043_pm_proxy_helper_subsys_modem_fd_count | 0 |
| v1043_pm_proxy_helper_d_state | True |
| v1043_mdm_helper_esoc0_fd_seen | True |
| v1043_order_has_lower_companion | False |

## Android Timeline Evidence (V1044)

| event | time |
| --- | ---: |
| sysmon-qmi modem SSCTL connected | ~7.002s |
| mdm_helper start | 8.148s |
| cnss_daemon start | 8.172s |
| wlfw_start | 8.349s |
| esoc0 subsys_get (pm-service) | 8.402s |
| PCIe RC1 link initialized | 8.820s |
| WLAN-PD UP | ~9.414s |

## Guardrails

No device contact, Android boot, ADB command, eSoC ioctl, `/dev/subsys_esoc0` open,
actor start, daemon start, Wi-Fi HAL, scan/connect, credentials, DHCP/routes,
external ping, boot image write, partition write, firmware mutation, GPIO write,
sysfs write, or debugfs write occurred in V1045.

## Validation

Commands:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_pil_prerequisite_delta_v1045.py
python3 scripts/revalidation/native_wifi_pm_pil_prerequisite_delta_v1045.py
```

Result:

```text
decision: v1045-pm-pil-prereq-modem-count-zero-classified
pass: True
next_step: v1046-add-subsys-modem-holder-prereq-before-pm-actors
```

## Next

V1046 should add a pre-PM modem holder prerequisite to the PM full-contract sequence:

1. Firmware mounts (`sda29`) + open `/dev/subsys_modem` holder BEFORE `pm_proxy_helper`
2. This brings modem count to ≥1 via `subsys_device_open()`, analogous to V490/lower-companion
3. With modem count≥1 set, `pm_proxy_helper` opening `subsys_modem` should just succeed
4. Gate: modem PIL boot completes → `pm_proxy_helper` gets `subsys_modem` fd →
   `per_mgr` gets `subsys_modem` fd → `mdm_helper` gets `esoc-0` → `subsys_esoc0` open

Do not widen to Wi-Fi HAL, scan/connect, DHCP/routes, credentials, external ping,
or boot image writes. Keep `/dev/subsys_esoc0` open gated behind PM fd contract.
