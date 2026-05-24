# Native Init V764 Service180-gated MDM Helper Retry Plan

- date: `2026-05-24 KST`
- scope: bounded live retry below service-manager/HAL/connect
- runner: `scripts/revalidation/native_wifi_mdm_helper_service180_retry_v764.py`

## Goal

Rebase V764 away from kernel source instrumentation and back to the immediate
live question:

```text
Can current native service-notifier 180 gate mdm_helper,
and does mdm_helper move mdm3 / WLAN-PD / MHI / WLFW / BDF / wlan0?
```

Before the live retry, V764 must classify V745-V749 evidence and directly
capture current `mdm_helper` and esoc0 surfaces.

## Inputs

- V745 service180-gated `mdm_helper`: gate stayed closed, `mdm_helper` not started
- V746 sysmon-gated `mdm_helper`: `mdm_helper` started, no lower progress
- V747 QCA6390 driver-link gap: bind/unbind remains rejected
- V748 non-bind trigger classifier: blind `mdm_helper` retry was previously eliminated
- V749 trigger selector: lower-window `boot_wlan` selected after native surface capture

## Live Contract

The runner uses helper v124 with:

```text
wifi-companion-service180-gated-mdm-helper-start-only
qrtr_ns,rmt_storage,tftp_server,pd_mapper,cnss_diag,cnss_daemon,service180_gate,mdm_helper
```

Preflight additionally captures:

- `/vendor/bin/mdm_helper`
- `/mnt/system/system/vendor/bin/mdm_helper`
- `/sys/bus/esoc/devices/esoc0`
- `/sys/class/subsys/subsys_esoc0`
- `/dev/subsys_esoc0`
- safe esoc0 sysfs attributes (`esoc_name`, `esoc_link`, `esoc_link_info`)

## Forbidden

- no esoc0 char-device open or hold
- no subsystem state write
- no bind/unbind or `driver_override`
- no module load/unload
- no `boot_wlan` or `qcwlanstate`
- no service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping
- no boot image or partition write

## Success Criteria

- V745-V749 evidence is summarized in the V764 manifest.
- Current `mdm_helper` and esoc0 surfaces are captured before live action.
- The service180 gate result and `mdm_helper` lifecycle are classified.
- Lower markers are captured: mdm3, service `69`, MHI/QCA6390, WLFW, BDF, wiphy/`wlan0`.
- Postflight reboot cleanup leaves native status healthy.

