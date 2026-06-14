# V903 mdm_helper-only Deep Capture Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v903-execns-helper-v147-build/a90_android_execns_probe` | static ARM64 build pass |
| helper deploy | `tmp/wifi/v903-execns-helper-v147-deploy-preflight/manifest.json` | `execns-helper-v147-deploy-pass` |
| live capture | `tmp/wifi/v903-mdm-helper-only-deep-capture-live/manifest.json` | `v903-mdm-helper-no-esoc-fd` |

V903 captured native `mdm_helper` directly without opening
`/dev/subsys_esoc0`.

## Findings

- Remote helper `v147` sha/marker/mode matched the expected artifact.
- `/vendor/bin/mdm_helper` started and was observable.
- V903 did not open `/dev/subsys_esoc0`:
  `mdm_helper_only_capture.subsys_esoc0_open_attempted=0`.
- `mdm_helper` held no `/dev/esoc-0` fd:
  `fd_esoc0_count.window=0`, `fd_esoc0_count.final=0`.
- `mdm_helper` held no `/dev/subsys_esoc0` fd:
  `fd_subsys_esoc0_count.window=0`, `fd_subsys_esoc0_count.final=0`.
- No MHI pipe fd or command line appeared:
  `fd_mhi_pipe_count.window=0`, `fd_mhi_pipe_count.final=0`,
  `mhi_pipe_cmdline_count.window=0`.
- `/vendor/bin/ks` was not observed:
  `ks_count.window=0`.
- Process snapshots were captured in both windows:
  `window_snapshot_captured=1`, `final_snapshot_captured=1`.
- Cleanup was clean without reboot:
  `mdm_helper.postflight_safe=1`, `all_postflight_safe=1`.
- Postflight showed no helper/ks leftovers, no Wi-Fi link, and mdm3 remained
  `OFFLINING`; GPIO 142 `mdm status` IRQ count remained at zero.

## Interpretation

V903 removes the `/dev/subsys_esoc0` block from the experiment and proves that
native `mdm_helper` alone does not enter the Android state-machine branch that
opens `/dev/esoc-0`, spawns `ks`, or touches the MHI pipe.

This means the next blocker is above the kernel `mdm_subsys_powerup` wait and
inside the Android `mdm_helper` activation contract: runtime properties, init
service context, argv/basename, SELinux label, socket availability, or another
Android-only environment input.

The Magisk-module style question is already mostly answered by the existing
Android evidence classified in V896: Android reaches AP2MDM/MDM2AP activity,
GPIO 142 IRQ, `mdm3=ONLINE`, WLFW/BDF, and `wlan0`. A fresh Android handoff or
Magisk boot script is only useful if the next parity check lacks a specific
Android-side input; it is not required before comparing `mdm_helper` runtime
inputs.

## Guardrails

- No `/dev/subsys_esoc0` open occurred.
- No controller-side `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, explicit
  `PWR_ON`, `WAIT_FOR_REQ`, `ESOC_NOTIFY`, or `BOOT_DONE`.
- No service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, boot image write, partition write, firmware
  mutation, GPIO/sysfs/debugfs write, module load/unload, or Wi-Fi link-up.
- No cleanup reboot was needed.

## Next

V904 should be an Android/native `mdm_helper` runtime-input parity classifier:

1. compare Android `mdm_helper` argv/basename, service name, SELinux context,
   environment, fd/socket surface, and relevant property reads;
2. compare native V903 captures against Android V852/V896 evidence;
3. decide whether the next live gate should emulate missing init/property
   context, adjust namespace device/socket materialization, or run a focused
   Android recapture.
