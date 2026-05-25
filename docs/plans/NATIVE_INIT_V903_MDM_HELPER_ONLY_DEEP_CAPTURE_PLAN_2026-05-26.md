# V903 mdm_helper-only Deep Capture Plan

## Goal

Classify native `/vendor/bin/mdm_helper` runtime behavior without repeating the
V900/V902 `/dev/subsys_esoc0` open that blocks in `mdm_subsys_powerup`.

V903 starts `mdm_helper` in the same private Android namespace, captures its
process/fd/socket surface, and proves whether it independently opens
`/dev/esoc-0`, spawns `/vendor/bin/ks`, or touches the MHI pipe.

## Inputs

- V902 report:
  `docs/reports/NATIVE_INIT_V902_MDM_HELPER_KS_BLOCKER_CAPTURE_2026-05-26.md`
- helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`
- V900 runner skeleton:
  `scripts/revalidation/native_wifi_mdm_helper_ks_contract_live_v900.py`
- Android positive-control classifier:
  `docs/reports/NATIVE_INIT_V896_ANDROID_MDM_HELPER_IMAGE_CONTRACT_2026-05-26.md`

## Method

1. Bump helper marker to `a90_android_execns_probe v147`.
2. Add `wifi-companion-mdm-helper-only-deep-capture` mode guarded by
   `--allow-mdm-helper-only-capture`.
3. Materialize the same private eSoC/subsys node surface, but do not open
   `/dev/subsys_esoc0`.
4. Start `/vendor/bin/mdm_helper` only.
5. Capture `mdm_helper`:
   - `wchan`, `syscall`, `stack`, `stat`, `status`, `sched`, and task state;
   - `attr/current`, `maps`, fd links, socket fdinfo;
   - `/proc/net/unix`, `/proc/net/netlink`, `/proc/net/qrtr`, and protocols;
   - fd matches for `/dev/esoc-0`, `/dev/subsys_esoc0`, and MHI pipe;
   - process matches for `/vendor/bin/ks` and the MHI pipe command line.
6. Cleanup the helper process and verify native health.

## Hard Gates

- No `/dev/subsys_esoc0` open.
- No `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, explicit `PWR_ON`,
  `ESOC_WAIT_FOR_REQ`, `ESOC_NOTIFY`, or `ESOC_BOOT_DONE`.
- No service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, or Wi-Fi link-up.
- No module load/unload, boot image write, partition write, firmware mutation,
  GPIO/sysfs/debugfs write, or Wi-Fi configuration.

## Success Criteria

- Helper `v147` builds static ARM64 with no dynamic section.
- Deploy returns `execns-helper-v147-deploy-pass`.
- Live manifest returns a bounded diagnostic pass.
- `subsys_esoc0_open_attempted=0`.
- `mdm_helper` process evidence is captured or cleanly classified as not
  observable.
- Native postflight has no leftover helper/ks process and no Wi-Fi link-up.

## Next

If native `mdm_helper` is observable but does not open `/dev/esoc-0`, compare
Android `mdm_helper` runtime inputs instead of retrying subsystem open. The
likely next gate is Android/native property, init, argv/basename, SELinux
context, socket, and environment parity.
