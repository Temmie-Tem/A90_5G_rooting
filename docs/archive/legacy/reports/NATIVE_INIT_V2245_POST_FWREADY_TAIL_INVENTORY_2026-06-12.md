# Native Init V2245 Post-FWREADY Tail Inventory (2026-06-12)

## Scope

Host-only inventory over existing private helper artifacts. No device I/O, no
flash, no BPF attach, no tracefs write, no Wi-Fi scan/connect, no network route
change, and no private raw helper output is published here.

Inputs:

- `workspace/private/runs/kernel/v2229-live-20260612-080114/device/helper_result.txt`
- `workspace/private/runs/kernel/v2231-live-20260612-081302/device/helper_result.txt`
- `workspace/private/runs/kernel/v2233-live-20260612-083738/device/helper_result.txt`
- `workspace/private/runs/kernel/v2244-semantic-timeline-merge-20260612-113706/summary.json`

Generated private summary:

- `workspace/private/runs/kernel/v2245-post-fwready-tail-inventory-20260612-114711/summary.json`
- `workspace/private/runs/kernel/v2245-post-fwready-tail-inventory-20260612-114711/post_fwready_tail_inventory.json`

## Result

Decision: `v2245-post-fwready-tail-inventory-pass`.

| Run | Outcome | Tail Stage | Notes |
| --- | --- | --- | --- |
| V2229 | no `wlan0` | `tail_absent` | No post-FWREADY boot_wlan/fwclass tail keys. |
| V2231 | no `wlan0` | `tail_absent` | No post-FWREADY boot_wlan/fwclass tail keys. |
| V2233 | `wlan0-ready` | `tail_complete_wlan0_ready` | Tail executes and completes the driver-start path. |

V2244 already showed the WLFW/QMI semantic edge sets and semantic signatures are
identical across V2229/V2231/V2233. V2245 therefore pins the remaining success
delta to the downstream post-FWREADY tail, not to another WLFW/QMI ordering
capture.

## V2233 Tail Evidence

V2233 key signals from the private helper summary:

- `post_fw_ready_boot_wlan_trigger.executed=1`
- `post_fw_ready_boot_wlan_trigger.write_rc=0`
- `post_fw_ready_boot_wlan_trigger.reason=boot-wlan-write-ok`
- firmware-class feeder served `wlan/qca_cld/WCNSS_qcom_cfg.ini`
- fed INI bytes: `13343`
- long-window ICNSS `register_driver.processed=1`
- long-window ICNSS CFG request/response: `1/1`
- long-window ICNSS MODE request/response: `2/2`
- long-window ICNSS INI request/response: `1/1`
- long-window ICNSS state: `0xd8d`
- `wlan0_present=1`, supervisor result `wlan0-ready`

The public-safe stack sample caught the qcacld firmware-class/probe path in a
kernel worker:

- `comm=kworker/u16:9`
- `wchan=_request_firmware`
- stack functions include `_request_firmware`, `request_firmware`,
  `qdf_file_read`, `qdf_ini_parse`, `cfg_parse`, `hdd_context_create`, and
  `wlan_hdd_pld_probe`

## Interpretation

The active discriminator is now:

`FW_READY -> boot_wlan write -> firmware_class request for WCNSS_qcom_cfg.ini -> qcacld/HDD probe -> ICNSS register/cfg/mode/ini completion -> wlan0`

This is a different layer from the already-closed WLFW/QMI order. Future T1 live
work should instrument the post-FWREADY firmware-class/qcacld-HDD tail if code
path identity is still needed. Re-running PerMgr/WLFW/QMI order captures is now
low-value unless new contradictory evidence appears.

## Safety

- Host-only parser.
- Private raw helper outputs stay under `workspace/private/**`.
- No device boot, flash, tracefs mutation, BPF attach, Wi-Fi scan/connect, or
  network change.
