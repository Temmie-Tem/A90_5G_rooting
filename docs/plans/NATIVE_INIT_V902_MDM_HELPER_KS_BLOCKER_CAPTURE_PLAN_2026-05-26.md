# V902 mdm_helper/ks Blocker Capture Plan

## Goal

Capture the exact blocker for the V900 `mdm_helper` before
`/dev/subsys_esoc0` live contract without widening toward Wi-Fi HAL or network
bring-up.

V902 keeps the V900 ordering but adds evidence for the blocked
`/dev/subsys_esoc0` open child: `/proc/<pid>/wchan`, `syscall`, `stack`,
`stat`, `status`, `sched`, and task-level status/wchan/syscall.

## Inputs

- V900 report:
  `docs/reports/NATIVE_INIT_V900_MDM_HELPER_KS_CONTRACT_LIVE_2026-05-26.md`
- helper source:
  `stage3/linux_init/helpers/a90_android_execns_probe.c`
- V900 runner:
  `scripts/revalidation/native_wifi_mdm_helper_ks_contract_live_v900.py`

## Method

1. Bump helper marker to `a90_android_execns_probe v146`.
2. Add generic blocker snapshot capture in the existing
   `wifi-companion-mdm-helper-ks-image-contract-preflight` mode.
3. Deploy helper `v146` only.
4. Re-run the same bounded ordered contract:
   - start `/vendor/bin/mdm_helper`;
   - require `mdm_helper_observable=1`;
   - then attempt `/dev/subsys_esoc0`;
   - capture blocker snapshot before TERM/KILL cleanup if the child blocks.
5. Cleanup reboot if the child cannot be reaped, then verify native health.

## Hard Gates

- No service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, or Wi-Fi link-up.
- No controller-side `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, explicit
  `PWR_ON`, `ESOC_WAIT_FOR_REQ`, `ESOC_NOTIFY`, or `ESOC_BOOT_DONE`.
- No module load/unload, boot image write, partition write, firmware mutation,
  GPIO/sysfs/debugfs write, or Wi-Fi configuration.

## Success Criteria

- Helper `v146` builds static ARM64 with no dynamic section.
- Deploy returns `execns-helper-v146-deploy-pass`.
- Live manifest returns a bounded diagnostic pass.
- Blocker snapshot is captured:
  `mdm_helper_ks_image_contract.subsys_trigger.blocker_snapshot_captured=1`.
- Native health is restored after cleanup reboot if needed.

## Next

If the child still blocks in `mdm_subsys_powerup`, do not repeat the same open.
Use the new evidence to classify why native `mdm_helper` does not reproduce
Android's `/dev/esoc-0`/`ks` behavior.
