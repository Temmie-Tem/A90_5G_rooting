# V869 eSoC Control Preflight Helper Build Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper source | `stage3/linux_init/helpers/a90_android_execns_probe.c` | helper `v135` implements eSoC control preflight mode |
| build | `tmp/wifi/v869-execns-helper-v135-build/a90_android_execns_probe` | static ARM64 helper built |
| marker scan | `strings tmp/wifi/v869-execns-helper-v135-build/a90_android_execns_probe` | new mode and guardrail markers present |

V869 completed as source/build-only. It did not deploy the helper and did not
contact the device.

## Build

Command:

```sh
mkdir -p tmp/wifi/v869-execns-helper-v135-build
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v869-execns-helper-v135-build/a90_android_execns_probe
```

Result:

```text
artifact: tmp/wifi/v869-execns-helper-v135-build/a90_android_execns_probe
file: ELF 64-bit LSB executable, ARM aarch64, statically linked
sha256: ad1bbbf295be61ef612406091ccd469c4ef45ab44c0f753c4de034e487ddaad1
dynamic section: There is no dynamic section in this file.
```

## Added Helper Contract

- Helper marker: `a90_android_execns_probe v135`
- New mode: `wifi-companion-esoc-control-preflight`
- New allow flag: `--allow-esoc-control-preflight`
- Local A90 UAPI markers:
  - `ESOC_REG_REQ_ENG.nr=7`
  - `ESOC_REG_CMD_ENG.nr=8`
  - `ESOC_CMD_EXE.nr=1`
  - `ESOC_PWR_ON.value=1`
- Fail-closed markers:
  - `mdm_helper_start_executed=0`
  - `ks_start_executed=0`
  - `wifi_hal_start_executed=0`
  - `scan_connect_linkup=0`
  - `credentials=0`
  - `external_ping=0`
  - `reg_req_eng_attempted=0`
  - `reg_cmd_eng_attempted=0`
  - `cmd_exe_attempted=0`
  - `wait_for_req_attempted=0`
  - `notify_attempted=0`
  - `pwr_on_attempted=0`

## Interpretation

V869 creates the helper-side foundation for the next eSoC gate without changing
device state. The new mode can later prove `/dev/esoc-0` visibility and
read-only ioctl surface separately from the mutating Android state-machine
steps. It deliberately does not perform `REG_REQ_ENG`, `REG_CMD_ENG`,
`ESOC_CMD_EXE`, `WAIT_FOR_REQ`, `NOTIFY`, or `ESOC_PWR_ON`.

## Guardrails

- No helper deploy.
- No bridge/device contact.
- No live eSoC ioctl.
- No `mdm_helper`, `ks`, `pm_proxy_helper`, CNSS, Wi-Fi HAL, scan/connect,
  credentials, DHCP/routes, external ping, module load/unload, boot image
  write, or partition write.

## Next

V870 should deploy helper `v135` only and prove remote checksum/version/mode
parity plus clean native health. Live eSoC control preflight remains blocked
until after that deploy-only gate.
