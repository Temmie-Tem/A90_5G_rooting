# V898 mdm_helper/ks Contract Helper v144 Build Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper build | `tmp/wifi/v898-mdm-helper-ks-contract-helper-build/manifest.json` | `v898-helper-v144-build-pass` |
| contract marker validation | `tmp/wifi/v898-v897-contract-presence-validate/manifest.json` | `v897-mdm-helper-ks-contract-support-present` |

V898 was source/build-only. It did not deploy the helper, did not contact the
device for the new mode, did not execute live eSoC ioctls, did not open
`/dev/subsys_esoc0`, did not start `mdm_helper` or `ks`, and did not bring up
Wi-Fi.

## Changes

- Updated `stage3/linux_init/helpers/a90_android_execns_probe.c` to helper
  marker `a90_android_execns_probe v144`.
- Added mode `wifi-companion-mdm-helper-ks-image-contract-preflight`.
- Added allow flag `--allow-mdm-helper-ks-contract-preflight`.
- Added a dedicated fail-closed contract path:
  - materializes `/dev/esoc-0`, `/dev/subsys_esoc0`, and `/dev/subsys_modem`;
  - starts `/vendor/bin/mdm_helper` before any `/dev/subsys_esoc0` open;
  - opens `/dev/subsys_esoc0` only after `mdm_helper` is observable;
  - does not register REQ engine or send `ESOC_NOTIFY`/`BOOT_DONE`;
  - scans for `/vendor/bin/ks` and
    `/dev/mhi_0305_01.01.00_pipe_10`;
  - reports reboot-required if actor or trigger cleanup is not proven safe.

## Build

```text
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v898-mdm-helper-ks-contract-helper-build/a90_android_execns_probe
```

Artifact:

- path: `tmp/wifi/v898-mdm-helper-ks-contract-helper-build/a90_android_execns_probe`
- size: `1057232`
- sha256:
  `c7b02320f143f57a837b5f1cf8af17258307439be3b8969dc33000735116ce4e`
- type: static AArch64 ELF
- dynamic section: absent

String checks passed for:

- `a90_android_execns_probe v144`
- `wifi-companion-mdm-helper-ks-image-contract-preflight`
- `--allow-mdm-helper-ks-contract-preflight`
- `mdm_helper_ks_image_contract.order=mdm_helper-before-subsys_esoc0`
- `/vendor/bin/mdm_helper`
- `/vendor/bin/ks /dev/mhi_0305_01.01.00_pipe_10 -w /dev/block/bootdevice/by-name/ -t -1 -l -g mdm1`
- `mdm_helper_ks_image_contract.reg_req_eng_attempted=0`
- `mdm_helper_ks_image_contract.notify_attempted=0`
- `mdm_helper_ks_image_contract.subsys_esoc0_open_gate=mdm_helper_observable`
- `mdm_helper_ks_image_contract.result=ks-mhi-observed`
- `mdm_helper_ks_image_contract.result=reboot-required`

## Interpretation

V898 implements the helper-side contract that V897 identified as missing.
This does not prove that native init can bring up Wi-Fi yet. It only makes the
next safe deploy/live gates possible without returning to the old
service-gated `mdm_helper` path or the blind `IMG_XFER_DONE` path.

The next meaningful gate is deploy-only checksum/version/mode parity for
helper `v144`. After deploy parity, a separate bounded live proof can start
`mdm_helper`, trigger `/dev/subsys_esoc0`, and observe whether `ks`, MHI,
GPIO 142 IRQ, `mdm3=ONLINE`, WLFW/BDF, and `wlan0` advance.

## Guardrails

- No helper deploy or new live device action occurred in V898.
- No live `REG_REQ_ENG`, `REG_CMD_ENG`, `CMD_EXE`, `PWR_ON`,
  `WAIT_FOR_REQ`, `NOTIFY`, `BOOT_DONE`, or `/dev/subsys_esoc0` open.
- No `mdm_helper` start, `ks` start, service-manager, CNSS daemon, Wi-Fi HAL,
  scan/connect, credentials, DHCP/routes, external ping, boot image write,
  partition write, firmware mutation, GPIO/sysfs/debugfs write, module
  load/unload, reboot, or Wi-Fi link-up.

## Next

V899 should deploy helper `v144` only and prove remote checksum/version/mode
parity. The first live `mdm_helper`/`ks` contract execution remains a later
bounded cycle with timeout and cleanup/reboot-required evidence.
