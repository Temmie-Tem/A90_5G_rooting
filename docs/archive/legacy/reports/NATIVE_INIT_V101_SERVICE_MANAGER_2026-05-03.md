# Native Init v101 Service Manager Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.9.1 (v101)` / `0.9.1 v101 SERVICE MANAGER`.
- Baseline: v100 remote shell over USB NCM.
- v101 extends `a90_service.c/h` from PID registry into a minimal metadata/status API.
- v101 adds `service [list|status|start|stop|enable|disable] [name]` as a common operator view for `autohud`, `tcpctl`, `adbd`, and `rshell`.
- Service start/stop behavior remains owned by each existing component; v101 does not add supervision or dependency solving.

## Key Changes

- Added `stage3/linux_init/init_v101.c` and `stage3/linux_init/v101/*.inc.c`.
- Updated `stage3/linux_init/a90_config.h` to `0.9.1` / `v101`.
- Extended `stage3/linux_init/a90_service.c/h` with:
  - service kind and flags
  - service metadata/status snapshot
  - name lookup and alias `netservice -> tcpctl`
  - enabled state mirror
  - `a90_service_reap_all()`
- Added v101 `service` command dispatch:
  - `service list`
  - `service status [name]`
  - `service start <name>`
  - `service stop <name>`
  - `service enable <name>`
  - `service disable <name>`
- Preserved compatibility commands: `autohud`, `stophud`, `netservice`, `rshell`, `startadbd`, `stopadbd`.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v101` | `5921c53e5c6992bb20c3d2ee55e653dd793cb5d76bf020ccb4d3e9fc621e620c` |
| `stage3/ramdisk_v101.cpio` | `2a72368840d4c531be28972bd99ff736953aa5160b40e4bc023e64fd3a870ff6` |
| `stage3/boot_linux_v101.img` | `c5d4f970534d7b7ddc42083ec1b3b7cbc98d0f56a9c726a1932d27cdff266624` |

Ramdisk entries:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- Static ARM64 init build with `-Wall -Wextra` — PASS.
- `stage3/ramdisk_v101.cpio` and `stage3/boot_linux_v101.img` generated from v100 boot args with only ramdisk replaced — PASS.
- Boot image markers found:
  - `A90 Linux init 0.9.1 (v101)`
  - `A90v101`
  - `0.9.1 v101 SERVICE MANAGER`
  - `service [list|status|start|stop|enable|disable] [name]`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `rshell_host.py`, `helper_deploy.py` — PASS.
- v101 stale marker scan for `A90v100`, `mark_step(...v100)`, and `0.9.0 v101` — PASS.

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v101.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.1 (v101)" \
  --verify-protocol auto
```

Result:

- Local image marker and SHA256 check — PASS.
- TWRP push and remote SHA256 check — PASS.
- boot partition prefix SHA256 matched `stage3/boot_linux_v101.img` — PASS.
- Post-boot `cmdv1 version/status` — PASS.

## Device Baseline

- `version`: PASS, `A90 Linux init 0.9.1 (v101)`.
- `status`: PASS, `selftest pass=11 warn=0 fail=0`, runtime SD backend, BusyBox/toybox ready.
- `bootstatus`: PASS.
- `selftest verbose`: PASS, service row present.
- `storage`: PASS.
- `mountsd status`: PASS.

## Service Command Validation

`service list` output showed all tracked services:

```text
service: autohud kind=display running=yes pid=... enabled=no flags=boot-optional
service: tcpctl kind=network running=no pid=-1 enabled=no flags=boot-optional,raw-control,requires-ncm,dangerous
service: adbd kind=android running=no pid=-1 enabled=no flags=raw-control,dangerous
service: rshell kind=remote running=no pid=-1 enabled=no flags=boot-optional,raw-control,requires-ncm,dangerous
```

Per-service status commands passed:

```bash
service status autohud
service status tcpctl
service status rshell
service status adbd
```

Lifecycle checks:

- `service stop autohud` then `service status autohud`: PASS, running `no`.
- `service start autohud` then `service status autohud`: PASS, running `yes`.
- `service enable autohud`: PASS expected error, `-EOPNOTSUPP`.
- `service enable adbd`: PASS expected error, `-EOPNOTSUPP`.

## TCP/NCM Service Validation

- `service enable tcpctl` re-enumerated USB as expected; framed `A90P1 END` may be interrupted.
- Post-reconnect `service status tcpctl`: PASS, running `yes`, NCM present.
- Host temporary NetworkManager config:

```bash
nmcli connection add type ethernet ifname <enx...> con-name a90-v101-ncm \
  ipv4.method manual ipv4.addresses 192.168.7.1/24 \
  ipv4.never-default yes ipv6.method disabled
nmcli connection up a90-v101-ncm
```

- Host ping `192.168.7.2`: PASS, 3/3, 0% loss.
- `tcpctl_host.py ping`: PASS, `pong`.
- `tcpctl_host.py status`: PASS, kernel/uptime/load/mem returned.
- `service disable tcpctl`: PASS after USB reconnect, serial bridge recovered.
- Final `service status tcpctl`: PASS, running `no`, enabled `no`, NCM absent.

## Remote Shell Service Validation

- `service start rshell` re-enumerated USB through NCM startup as expected; framed `A90P1 END` may be interrupted.
- `service status rshell`: PASS after reconnect, remote shell running.
- Host NCM ping `192.168.7.2`: PASS, 3/3.
- `rshell_host.py smoke`: PASS.
  - `echo A90_RSHELL_OK`
  - `busybox uname -a`
  - `busybox ls /proc | busybox head -5`
- `service stop rshell`: PASS.
- `service status rshell`: PASS, running `no`, enabled `no`.
- `service enable rshell` / `service disable rshell`: PASS for flag path and service shutdown; USB reconnect still recovered.
- Final `service disable tcpctl` rollback: PASS, `ncm=absent`, `tcpctl=stopped`.

## UI / Runtime Regression

- `statushud`: PASS.
- `autohud 2`: PASS.
- `screenmenu`: PASS, nonblocking command returns immediately.
- `hide`: PASS.
- `cpustress 3 2`: PASS, `/bin/a90_cpustress` completes.
- `storage`: PASS.
- `mountsd status`: PASS.

## Notes

- `service start/stop/enable/disable tcpctl` and `service start/stop/enable/disable rshell` can re-enumerate USB. Host tooling should treat those as raw-control-like operations or run a status check after reconnect.
- During USB re-enumeration, partial serial fragments can briefly appear and may produce a harmless `unknown command: [done]` line. Serial bridge recovered and `version`/`service status` passed afterward.
- v101 intentionally does not supervise or auto-restart services. It only gives a consistent operator view and dispatches existing lifecycle owners.

## Latest Verified

`A90 Linux init 0.9.1 (v101)` is now the latest verified native init baseline.

## Next

v102 should implement diagnostics/log bundle on top of the v101 service view.
