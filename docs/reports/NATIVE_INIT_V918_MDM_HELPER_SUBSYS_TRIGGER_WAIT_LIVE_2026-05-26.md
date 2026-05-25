# Native Init V918 mdm_helper Wait-Gated Subsys Trigger Live Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper v151 source/build verifier | `tmp/wifi/v918-mdm-helper-subsys-trigger-wait-support/manifest.json` | `v918-mdm-helper-subsys-trigger-wait-support-pass` |
| helper v151 deploy | `tmp/wifi/v918-execns-helper-v151-deploy-preflight/manifest.json` | `execns-helper-v151-deploy-pass` |
| wait-gated trigger live gate | `tmp/wifi/v918-mdm-helper-subsys-trigger-capture-live/manifest.json` | `v918-reboot-required-cleaned` |

V918 fixed the V917 timing bug by waiting until `mdm_helper` actually holds `/dev/esoc-0` before starting the `/dev/subsys_esoc0` trigger child. The gate opened and the trigger child attempted the open, but the child entered uninterruptible sleep and required cleanup reboot.

## Key Evidence

- Helper v151 build artifact: `tmp/wifi/v918-execns-helper-v151-build/a90_android_execns_probe`.
- Helper v151 sha256: `aa8e833c292b1b906ec375a6eff9f2c2bd5691b9bfbffb951d6774a6b4ff06c8`.
- Serial deploy used safe chunk size `1850`: `chunks_written=837`, `max_cmdv1_line_bytes=3890`, `safe_line_limit=3968`.
- `mdm_helper` was observable.
- Gate poll detected `/dev/esoc-0`: `fd_esoc0_count.gate=1`, `gate_poll_count=1`.
- Trigger child started: `subsys_trigger.started=1`.
- Trigger child did not exit/reap: `subsys_trigger.exited=0`, `subsys_trigger.reaped=0`, `timed_out=1`.
- Kernel wait location: `sdx50m_toggle_soft_reset`.
- Kernel stack includes `sdx50m_toggle_soft_reset -> mdm4x_do_first_power_on -> mdm_cmd_exe -> mdm_subsys_powerup -> __subsystem_get -> subsys_device_open`.
- `mdm3` remained `OFFLINING` and `wlan0_captured=0`; no WLFW/BDF/wlan0 progression was observed.
- Cleanup reboot was requested and post-reboot health recovered: bootstatus/selftest `fail=0`.

## Guardrails

- `pm_proxy_helper_start_executed=0`.
- `service_manager_start_executed=0`.
- `cnss_start_executed=0`.
- `wifi_hal_start_executed=0`.
- `scan_connect_linkup=0`.
- `credentials=0`.
- `dhcp_routing=0`.
- `external_ping=0`.
- `notify_attempted=0`.
- `boot_done_attempted=0`.

## Interpretation

The native path can now reach the real SDX50M power-up path. The blocker moved from user-space ordering/timing to kernel/board-level SDX50M soft-reset handoff: opening `/dev/subsys_esoc0` enters `sdx50m_toggle_soft_reset` and does not return under the current native runtime conditions. This explains why MHI, KS, WLFW, BDF, and `wlan0` remain absent.

## Next

V919 should be host-only/read-only first: compare Android successful boot evidence and OSRC/DTS around SDX50M reset GPIOs, PMIC GPIO9, AP2MDM/MDM2AP status, and any vendor property or peripheral-manager sequencing that prevents `sdx50m_toggle_soft_reset` from blocking. Do not repeat `/dev/subsys_esoc0` live open until the missing reset/status precondition is classified.
