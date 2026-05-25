# V902 mdm_helper/ks Blocker Capture Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v902-execns-helper-v146-build/a90_android_execns_probe` | static ARM64 build pass |
| helper deploy | `tmp/wifi/v902-execns-helper-v146-deploy-preflight/manifest.json` | `execns-helper-v146-deploy-pass` |
| live capture | `tmp/wifi/v902-mdm-helper-ks-blocker-capture-live/manifest.json` | `v902-reboot-required-cleaned` |

V902 captured the exact blocked task evidence for the V900 lower contract.

## Findings

- Remote helper `v146` sha/marker/mode matched the expected artifact.
- `/vendor/bin/mdm_helper` started and became observable.
- `mdm_helper` did not hold `/dev/esoc-0` in the captured window. Its visible
  fds were `/dev/ttyGS0`, stdout/stderr pipes, and one socket.
- `/dev/subsys_esoc0` open was attempted only after
  `mdm_helper_observable=1`.
- The trigger child blocked in D-state:
  - `wchan`: `mdm_subsys_powerup`
  - state: `D (disk sleep)`
  - stack:
    `mdm_subsys_powerup -> __subsystem_get -> subsys_device_open ->
    chrdev_open -> do_dentry_open -> vfs_open -> path_openat -> do_sys_open ->
    SyS_openat`
- Blocker snapshot was captured:
  `mdm_helper_ks_image_contract.subsys_trigger.blocker_snapshot_captured=1`.
- `/vendor/bin/ks` was not observed:
  `ks_count.before=0`, `ks_count.window=0`, `ks_count.after=0`.
- MHI pipe command line was not observed:
  `mhi_pipe_cmdline_count.window=0`.
- Cleanup reboot restored native health; direct post-cleanup checks showed
  `selftest fail=0` and `bootstatus` OK.

## Interpretation

V902 confirms that the V900 block is the same lower-kernel provider wait seen
earlier in V849, but now under the Android-derived `mdm_helper` ordering. The
critical new clue is that native `mdm_helper` itself did not open or hold
`/dev/esoc-0`, so it likely did not enter the full Android state-machine path
that registers engines, spawns `ks`, and handles MHI image transfer.

The next step should not be another `/dev/subsys_esoc0` open retry. It should
classify `mdm_helper` runtime inputs and wait state directly, preferably with a
`mdm_helper`-only deep capture that records its `wchan`, `syscall`, stack,
socket/proc-net context, properties, and fd evolution without attempting
`/dev/subsys_esoc0`.

## Guardrails

- No controller-side `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, explicit
  `PWR_ON`, `WAIT_FOR_REQ`, `ESOC_NOTIFY`, or `BOOT_DONE`.
- No service-manager, CNSS daemon, Wi-Fi HAL, scan/connect, credentials,
  DHCP/routes, external ping, boot image write, partition write, firmware
  mutation, GPIO/sysfs/debugfs write, module load/unload, or Wi-Fi link-up.
- A cleanup reboot was intentionally executed because the trigger child was not
  proven stopped.

## Next

V903 should focus on `mdm_helper` itself:

1. start `mdm_helper` in the same namespace;
2. do not open `/dev/subsys_esoc0`;
3. capture `mdm_helper` `wchan`/`syscall`/stack/fds/socket context and property
   reads;
4. determine why it does not open `/dev/esoc-0` or spawn `ks`.
