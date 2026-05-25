# Native Init V909 mdm_helper eSoC FD Stall Support Plan

## Goal

Add source/build-only support for the next live classifier at the precise V908
boundary: `mdm_helper` holds `/dev/esoc-0`, but no `ks`, MHI pipe, GPIO142 IRQ,
WLFW, BDF, or `wlan0` appears.

## Gate

Build helper `v149` with extra passive captures around the existing
`wifi-companion-mdm-helper-runtime-contract-capture` mode:

- fdinfo for matching `/dev/esoc-0`, `/dev/subsys_esoc0`, and MHI pipe fds;
- `wchan`, `syscall`, `stack`, `stat`, `status`, `sched`, and task snapshots
  for `mdm_helper` at window/final capture points;
- no new live action, daemon start, or Wi-Fi bring-up in V909.

## Forbidden In V909

- Helper deployment.
- Device actor start.
- Live eSoC ioctl or controller `/dev/subsys_esoc0` open.
- Service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping.
- Reboot, boot image write, partition write, firmware mutation,
  GPIO/sysfs/debugfs write, module load/unload, Wi-Fi bring-up.

## Validation

Run:

```bash
scripts/revalidation/build_android_execns_probe_helper.sh tmp/wifi/v909-execns-helper-v149-build/a90_android_execns_probe
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_esoc_fd_stall_support_v909.py
python3 scripts/revalidation/native_wifi_mdm_helper_esoc_fd_stall_support_v909.py
```

## Next

If V909 passes, deploy helper `v149` and rerun the bounded runtime-contract
capture. The live run should remain diagnostic-only and must not proceed to
service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials, DHCP/routes,
or external ping.
