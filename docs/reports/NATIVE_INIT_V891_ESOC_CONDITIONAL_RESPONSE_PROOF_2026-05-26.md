# V891 eSoC Conditional Response Proof Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| plan | `tmp/wifi/v891-esoc-conditional-response-plan/manifest.json` | `v891-esoc-conditional-response-plan-ready` |
| initial live | `tmp/wifi/v891-esoc-conditional-response-live/manifest.json` | `v891-step-failed` |
| repaired live | `tmp/wifi/v891-esoc-conditional-response-live-v142/manifest.json` | `v891-img-xfer-done-sent-status-not-ready-reboot-cleaned` |

V891 executed the first guarded live eSoC response proof after V892 deployed
helper `v142`.

## Initial Failure

The first V891 attempt with helper `v141` failed before any live eSoC action:

- helper rc: `2`
- message: `arguments do not match v235 allowlist`
- no `REG_REQ_ENG`
- no `/dev/subsys_esoc0` open
- no `ESOC_NOTIFY`

V892 fixed this by adding the conditional response mode to the global helper
allowlist and deploying helper `v142`.

## Live Findings

| Field | Value |
| --- | --- |
| helper | `a90_android_execns_probe v142` |
| `REG_REQ_ENG` | rc `0`, errno `0` |
| `/dev/subsys_esoc0` open | attempted, did not return |
| `ESOC_WAIT_FOR_REQ` | rc `4`, errno `0`, value `1` |
| request name | `ESOC_REQ_IMG` |
| `ESOC_IMG_XFER_DONE` | attempted `1`, sent `1`, rc `0`, errno `0` |
| `ESOC_GET_STATUS` | `87` polls, all value `0` |
| `ESOC_BOOT_DONE` | attempted `0`, sent `0` |
| conditional result | `status-not-ready-no-boot-done` |
| child cleanup | `term_sent=1`, `kill_sent=1`, `reaped=0` |
| cleanup | reboot executed, post-reboot `bootstatus` and `selftest fail=0` passed |

Key evidence lines:

- `tmp/wifi/v891-esoc-conditional-response-live-v142/native/esoc-conditional-response.txt`
- `tmp/wifi/v891-esoc-conditional-response-live-v142/reboot_cleanup/`

## Interpretation

V891 proves that the native path can receive `ESOC_REQ_IMG` and successfully
send `ESOC_IMG_XFER_DONE` through the eSoC control interface. That response is
not sufficient to make `ESOC_GET_STATUS` become ready within the bounded
window. Because status stayed `0`, the helper correctly refused to send
`ESOC_BOOT_DONE`.

This narrows the blocker:

1. The REQ engine registration path works.
2. The request FIFO path works.
3. `ESOC_NOTIFY(ESOC_IMG_XFER_DONE)` works.
4. The remaining blocker is the readiness transition after image-done.

The current evidence does not prove Wi-Fi bring-up readiness. No Wi-Fi actor,
HAL, scan/connect, credentials, DHCP/routes, or external ping was executed.

## Guardrails

- No `REG_CMD_ENG`.
- No direct userspace `CMD_EXE`.
- No explicit userspace `PWR_ON`.
- No blind `ESOC_BOOT_DONE`.
- No `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, service-manager, Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, or external ping.
- No module load/unload, boot image write, partition write, firmware mutation,
  GPIO/sysfs/debugfs write, or Wi-Fi link-up.

## Next

V893 should classify why `ESOC_GET_STATUS` remains `0` after
`ESOC_IMG_XFER_DONE`. The likely missing piece is the image-transfer side
effect expected by the eSoC driver, not another blind retry or actor/HAL start.
