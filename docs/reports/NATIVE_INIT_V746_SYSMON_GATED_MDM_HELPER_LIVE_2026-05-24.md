# Native Init V746 Sysmon-gated MDM Helper Live Report

- date: `2026-05-24 KST`
- native build on device: `A90 Linux init 0.9.68 (v724)`
- helper version deployed: `a90_android_execns_probe v124`
- helper sha256: `d44cbb538db11a280aa789ccafb008476ac541ec08bb96f549670ae28db7cec6`
- deploy evidence: `tmp/wifi/v746-execns-helper-v124-deploy-run-serial1850/`
- live evidence: `tmp/wifi/v746-mdm-helper-sysmon-live-current/`

## Summary

V746 deployed helper v124 and ran the sysmon-gated `mdm_helper` live proof.
The `sysmon-qmi` gate opened, `mdm_helper` started, stayed observable, and was
terminated cleanly by the bounded helper cleanup. The run still produced no
lower WLAN progress: `mdm3` stayed `OFFLINING`, and MHI/QCA6390/WLFW/service
`69`/BDF/`wlan0` remained absent.

## Results

| item | result |
| --- | --- |
| v124 deploy | `execns-helper-v124-deploy-pass` |
| remote helper SHA | `d44cbb538db11a280aa789ccafb008476ac541ec08bb96f549670ae28db7cec6` |
| live decision | `v746-mdm-helper-started-no-lower-progress` |
| `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` | `OFFLINING -> OFFLINING -> OFFLINING` |
| QRTR RX/TX | present |
| `sysmon-qmi` gate | opened: baseline `0`, final `1` |
| `mdm_helper` | started, observable, postflight-safe |
| service-notifier `180` / `74` | absent |
| MHI/QCA6390/WLFW/BDF/`wlan0` | absent |
| service-manager / Wi-Fi HAL / scan / connect / ping | not executed |
| postflight cleanup | reboot cleanup healthy |

## Additional Evidence

- `a0000000.qcom,cnss-qca6390` platform device exists.
- `/sys/bus/platform/devices/a0000000.qcom,cnss-qca6390/driver` is missing.
- `/sys/bus/platform/drivers/cnss2` is missing in native evidence.
- `/sys/bus/mhi/devices` is empty while `/sys/bus/mhi/drivers` is populated.

This shifts the next blocker away from `mdm_helper`: the current lower gap is
now the QCA6390 platform-device driver binding / power-up path before MHI.

## Interpretation

`mdm_helper` is not sufficient for the current native Wi-Fi lower blocker. It
can run in the bounded window after `sysmon-qmi`, but it does not move `mdm3`,
WLAN-PD, MHI, WLFW, BDF, or `wlan0`.

The next proof should be read-only first: compare Android and native binding
state for `a0000000.qcom,cnss-qca6390`, `/sys/bus/platform/drivers/*`, ICNSS
driver links, MHI bus state, and any Android event that binds or powers the
QCA6390 device. Do not perform generic bind/unbind yet.
