# V891 eSoC Conditional Response Proof Plan

## Goal

Run the first bounded live conditional eSoC response proof using deployed helper
`v142`. V891 is not a Wi-Fi bring-up attempt. It only answers the observed
`ESOC_REQ_IMG` request with the smallest guarded response sequence needed to
test whether MDM3/SDX50M can progress past the previous D-state blocker.

## Inputs

- V890 deploy report:
  `docs/reports/NATIVE_INIT_V890_HELPER_V141_DEPLOY_2026-05-26.md`
- V889 helper build report:
  `docs/reports/NATIVE_INIT_V889_ESOC_CONDITIONAL_RESPONSE_HELPER_BUILD_2026-05-26.md`
- V892 helper allowlist repair/deploy evidence:
  `tmp/wifi/v892-execns-helper-v142-build/a90_android_execns_probe`
  and `tmp/wifi/v892-execns-helper-v142-deploy-preflight/manifest.json`
- runner:
  `scripts/revalidation/native_wifi_esoc_conditional_response_v891.py`
- plan evidence:
  `tmp/wifi/v891-esoc-conditional-response-plan/manifest.json`

## Method

1. Verify native health and remote helper `v141` sha/mode marker.
2. Mount Android system read-only and materialize only Android-equivalent
   `/dev/esoc-0`, `/dev/subsys_esoc0`, and `/dev/subsys_modem`.
3. Register only `REG_REQ_ENG` on `/dev/esoc-0`.
4. Open `/dev/subsys_esoc0` to trigger the kernel-owned powerup path.
5. In the response child, wait for `ESOC_REQ_IMG`.
6. If `ESOC_REQ_IMG` is observed, send `ESOC_IMG_XFER_DONE`.
7. Poll `ESOC_GET_STATUS`; send `ESOC_BOOT_DONE` only if status becomes ready.
8. Capture post-surface process, netdev, and dmesg evidence.
9. If a helper child remains unkillable, perform cleanup reboot and prove
   `bootstatus` plus `selftest fail=0` after reboot.

## Hard Gates

- Allowed eSoC actions:
  - `REG_REQ_ENG`
  - `ESOC_WAIT_FOR_REQ`
  - guarded `ESOC_NOTIFY(ESOC_IMG_XFER_DONE)`
  - `ESOC_GET_STATUS`
  - guarded `ESOC_NOTIFY(ESOC_BOOT_DONE)` only when status is ready
- Forbidden:
  - `REG_CMD_ENG`
  - direct userspace `CMD_EXE`
  - explicit userspace `PWR_ON`
  - blind `ESOC_BOOT_DONE`
  - Android actor start, `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS,
    service-manager, Wi-Fi HAL, scan/connect, credentials, DHCP/routes,
    external ping, module load/unload, boot image write, partition write,
    firmware mutation, GPIO/sysfs/debugfs write, or Wi-Fi link-up

## Success Criteria

- Decision is either:
  - `v891-img-xfer-done-sent-status-not-ready-reboot-cleaned`, or
  - `v891-boot-done-sent-reboot-cleaned`.
- Remote helper sha/mode marker matches V890.
- `ESOC_REQ_IMG` is observed.
- `ESOC_IMG_XFER_DONE` is sent.
- `ESOC_BOOT_DONE` is sent only if `ESOC_GET_STATUS` reports ready.
- Post-run actor and Wi-Fi surfaces remain clean.
- Cleanup reboot runs if needed and returns to healthy native state.

## Next

If V891 only reaches `ESOC_IMG_XFER_DONE` and `GET_STATUS` remains not-ready,
the next gate should classify why readiness does not advance after image-done.
If `ESOC_BOOT_DONE` is sent, the next gate should inspect WLFW/service69,
BDF, and `wlan0` deltas before any actor, HAL, scan, or connect work.
