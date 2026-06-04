# Native Init V2032 Full-Chain Wlanmdsp/FW-Ready Branch

## Summary

- Cycle: `V2032`
- Type: host-side synthesis of the already-run rollbackable native full-chain measurements `V2029` and `V2031`
- Decision: `v2032-full-chain-wlanmdsp-served-fwmem-only-no-fwready-rollback-pass`
- Label: `full-chain-wlanmdsp-served-fwmem-only-no-fwready`
- Result: PASS
- Reason: native now reaches WLAN-PD UP, serves the requested `wlanmdsp.mbn`, and completes WLFW cap/BDF/cal, but only receives the non-queued fw-mem indication (`msg_id=0x2b`); no queueable FW-ready/status indication (`0x28`/`0x2a`/`0x41`), WLFW service 69, FW-ready, or `wlan0` follows.

## Evidence Matrix

| area | result | evidence |
| --- | --- | --- |
| rollback | pass | `V2029` and `V2031` both rolled back to `stage3/boot_linux_v724.img` and verified selftest fail=0 |
| bridges | pass | readonly dual RFS paths exist/open; readwrite tmpfs bridge exists; `server_check.txt` exists; `sda29_write=0` |
| full chain | pass | stock service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, `cnss-daemon`, `rmt_storage`, `tftp_server`, and `pd-mapper` were present in the lower-window route |
| WLAN-PD | pass | `wlan_pd=1`, `icnss_qmi=1`; first UP was in the native lower window |
| wlanmdsp TFTP | pass | `V2029` saw RRQ `/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn` and successful open of `/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn` |
| post-UP hold | pass | `V2029` held `124.494141s` after WLAN-PD UP; `V2031` held `81.817161s` after WLAN-PD UP |
| WLFW consumer | pass | `V2031` reached WLFW cap/BDF/cal success: `cap=0x0`, `bdf=0x0`, `cal=0x0` |
| post-cal indication | blocked | `V2031` saw `wlfw_qmi_ind_cb_entry` hits with first `msg_id=0x2b`, `payload_len=0x0`, and `wlfw_qmi_ind_fw_mem_flag=1`; no queue link, no worker handler, no `0x28`/`0x2a`/`0x41` decode |
| downstream cascade | blocked | `wlfw69=0`, `fw_ready=0`, `wlan0=0` |

## Branch Decision

- The requested full-chain branch is `wlan_pd UP + cnss-daemon running + wlanmdsp requested/served + cap/BDF/cal complete`, but `WLFW 69` remains absent.
- This selects the second branch from the requested unit: WLAN-PD registers enough state for ICNSS and cap/BDF/cal QMI, but it does not publish the queueable FW-ready/status indication that drives FW-ready/`wlan0`.
- The prior `V2031` label `callback-not-queued` was too broad: `msg_id=0x2b` is the fw-mem flag/condition path and is not expected to queue a worker indication. The missing edge is the later queueable FW-ready/status indication, not queue insertion for `0x2b`.

## Next Bounded Target

- Stay on the internal modem/WLAN-PD route.
- Do not rerun AP-side RIL/CNSS/PM strace or QRTR matrices; the AP consumer chain has already reached cap/BDF/cal.
- The next useful measurement is the modem/WLAN-PD post-cal producer edge: why no queueable WLFW FW-ready/status indication (`0x28`/`0x2a`/`0x41`) is emitted after successful `wlanmdsp.mbn` serve and WLFW cap/BDF/cal.
- If a live run is needed, use the same rollbackable lower-window route with readonly/readwrite bridges and a light post-cal indication tracer; do not add boot-time QRTR matrix or multi-strace.

## Safety

- No new live flash, reboot, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping was performed for this synthesis.
- No rild/cnss/pm-service strace, boot-time QRTR matrix, active QRTR readback, QMI payload send, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, fake ONLINE, forced RC1/case, or PMIC/GPIO/GDSC/regulator write was performed.
- Evidence reused only existing rollback-verified runs under `tmp/wifi/v2029-dual-rfs-wlanmdsp-tftp-handoff` and `tmp/wifi/v2031-dual-rfs-post-cal-indication-handoff`.
