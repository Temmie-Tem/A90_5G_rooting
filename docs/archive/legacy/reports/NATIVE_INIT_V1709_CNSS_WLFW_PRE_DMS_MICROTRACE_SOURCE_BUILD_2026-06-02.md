# Native Init V1709 CNSS WLFW Pre-DMS Microtrace Source Build

## Summary

- Cycle: `V1709`
- Type: source/build-only rollbackable CNSS `wlfw_start` pre-DMS microtrace test boot artifact
- Decision: `v1709-cnss-wlfw-pre-dms-microtrace-source-build-pass`
- Result: PASS
- Reason: extends V1708 from entry-only `wlfw_start` proof to call/retcheck tracepoints for the four pre-DMS pthread init calls
- Manifest: `tmp/wifi/v1709-cnss-wlfw-pre-dms-microtrace-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1709-cnss-wlfw-pre-dms-microtrace-test-boot/boot_linux_v1709_cnss_wlfw_pre_dms_microtrace.img`
- Boot SHA256: `b794a0f49f0750e63ded778cec55f9c9117a8c4945dd591f04b66e4d0cf8cbbe`
- Init: `A90 Linux init 0.9.131 (v1709-cnss-wlfw-pre-dms-microtrace)`
- Helper marker: `a90_android_execns_probe v317`
- Helper SHA256: `7c6bb9dab761c7e7768b5c8a71cd58d016de5b534814643c55473d967bc0b63c`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-cnss-output-visibility-start-only`
- Property root: `/mnt/sdext/a90/private-property-v317/v1709/dev/__properties__`
- Actors: `qrtr-ns`, `pd-mapper`, `rmt_storage`, `tftp_server`, `/dev/subsys_modem` holder, `cnss_diag`, stock `cnss-daemon`.
- No service-manager, PM trio, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## New Trace Targets

- `cnss-daemon+0xec58` / `0xec5c`: first `pthread_mutex_init` call and return check.
- `cnss-daemon+0xec78` / `0xec7c`: second `pthread_mutex_init` call and return check.
- `cnss-daemon+0xec9c` / `0xeca0`: first `pthread_cond_init` call and return check.
- `cnss-daemon+0xecbc` / `0xecc0`: second `pthread_cond_init` call and return check.
- Existing V1708 targets remain armed: `wlfw_start`, failure branches, DMS init, pthread_create, worker/QMI targets.

## Live Labels

- `wlfw-start-cal-mutex-call-no-return`
- `wlfw-start-cal-mutex-retcheck-no-mutex`
- `wlfw-start-mutex-call-no-return`
- `wlfw-start-mutex-retcheck-no-cond`
- `wlfw-start-cond-call-no-return`
- `wlfw-start-cond-retcheck-no-cond-rsp`
- `wlfw-start-cond-rsp-call-no-return`
- `wlfw-start-cond-rsp-retcheck-no-dms`
- Existing downstream labels from V1708 remain valid.

## Safety Scope

This build script performed host-side source/build work only. It did not issue live device commands, flash, reboot, scan/connect, use credentials, configure DHCP/routes, perform external ping, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
