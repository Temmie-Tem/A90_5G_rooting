# Native Init V2033 Wlanmdsp TFTP Transfer Completion Gap

## Summary

- Cycle: `V2033`
- Type: host-side synthesis/correction of existing Android-good and native lower-window evidence
- Decision: `v2033-wlanmdsp-fallback-transfer-completion-gap-host-pass`
- Label: `wlanmdsp-fallback-transfer-completion-unverified-native-oack-only`
- Result: PASS
- Reason: native has proven WLAN-PD UP plus WLFW cap/BDF/cal with `wlanmdsp.mbn` RRQ/OACK/open, but has not proven completed `wlanmdsp.mbn` payload transfer. Android-good reaches `wlan0` through the fallback RFS path after the first `firmware_mnt/image` probe fails.

## Evidence Matrix

| area | result | evidence |
| --- | --- | --- |
| Android-good baseline | clean | `V1982`/`V1753` reaches `wlan0` at `14.866239s` with no pre-wlan0 PCIe/MHI contamination |
| Android first probe | absent | `tftp_server` first resolves `readonly/vendor/firmware_mnt/image/wlanmdsp.mbn` to `/vendor/rfs/msm/mpss/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn`, then open fails with `ENOENT` |
| Android fallback | complete | `readonly/vendor/firmware/wlanmdsp.mbn` opens and later reports `total-blocks = 554`, `total-bytes = 4251884`, and `RRQ was successfully processed` |
| Native V2029 dual path | open-only | `RRQ=29`, `WRQ=8`, `OACK=15`, `ERROR=3`, `ACK=0`, `DATA=0`; first path opens twice, but no transfer-complete stats appear |
| Native V2029 fallback path | not requested | packet paths contain `/readonly/vendor/firmware_mnt/image/wlanmdsp.mbn` and `/readwrite/mcfg.tmp`, not `/readonly/vendor/firmware/wlanmdsp.mbn` |
| Native V2025 fallback-only | unmeasured | Android-parity fallback bridge preserved the lower-window route without `tftp_server` ptrace, but did not measure transfer completion |
| Native V2027 fallback trace | unresolved | fallback-only with all-task ptrace saw repeated first-probe errors and no fallback transfer; this does not close the non-ptrace transfer-completion gap |
| Native V2031 post-cal | downstream partial | cap/BDF/cal and `msg_id=0x2b` fw-mem indication were observed, but the run intentionally omitted TFTP ptrace and therefore inherits the V2029 open-only limitation |

## Correction

- `V2029` and `V2032` must not be read as proving a completed native `wlanmdsp.mbn` serve.
- The proved native edge is `WLAN-PD UP + RRQ/OACK/open + cap/BDF/cal`; the unproved edge is `wlanmdsp.mbn` ACK/DATA payload transfer or tftp_server transfer-complete stats.
- Dual-RFS may be over-satisfying the first `firmware_mnt/image` probe path that Android-good leaves absent, preventing the modem from following Android's successful fallback path.

## Next Bounded Unit

- Build/run the Android-parity fallback route, not the dual-RFS route: keep `readonly/vendor/firmware_mnt/image/wlanmdsp.mbn` absent, keep `readonly/vendor/firmware/wlanmdsp.mbn` present, and keep `/vendor/rfs/msm/mpss/readwrite` on tmpfs.
- Run the full downstream consumer chain in the same lower-window boot: clean-DSP/sibling-sysmon companion, service managers, `pm-service`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`, `rmt_storage`, `tftp_server`, and `pd-mapper`.
- Prefer a non-ptrace `tftp_server` log/stat observer for `RRQ stats`, `END OF TRANSFER`, `RRQ was successfully processed`, and `total-bytes = 4251884`; if unavailable, use the least intrusive single-`tftp_server` observer and classify request/open/OACK separately from payload transfer.
- Hold at least `30s` after WLAN-PD UP and watch the cascade: `wlan_pd UP -> WLFW 69 -> cap_req -> BDF -> fw_ready -> wlan0`.

## Branches

- `fallback-transfer-complete-fwready-progress`: fallback `wlanmdsp.mbn` transfer completes and WLFW 69/FW-ready/`wlan0` appears; continue downstream toward real `wlan0`.
- `fallback-transfer-complete-no-fwready`: fallback transfer completes but no WLFW 69/FW-ready follows; only then pivot to the WLAN-PD post-transfer FW-ready/status producer edge.
- `fallback-request-open-oack-only`: fallback request/open/OACK occurs without ACK/DATA or transfer-complete stats; inspect stock `tftp_server` transport/server behavior.
- `fallback-not-requested`: Android-parity fallback bridge still never receives the fallback `wlanmdsp.mbn` request; characterize why the modem stops after the failed first probe.

## Safety

- No new live flash, reboot, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, `/dev/subsys_esoc0`, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, fake ONLINE, forced RC1/case, or PMIC/GPIO/GDSC/regulator write was performed for this host-side synthesis.
- The allowed live mutation for the next unit remains rollbackable test-boot to `stage3/boot_linux_v724.img` plus namespace-local readonly/readwrite RFS tmpfs/symlink bridges; `sda29` stays read-only.
