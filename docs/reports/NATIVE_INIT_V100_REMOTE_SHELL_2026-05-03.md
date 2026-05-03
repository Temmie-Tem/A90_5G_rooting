# Native Init v100 Remote Shell Report

Date: `2026-05-03`

## Summary

- Version: `A90 Linux init 0.9.0 (v100)` / `0.9.0 v100 REMOTE SHELL`
- Result: PASS.
- v100 adds a custom token-authenticated TCP remote shell helper over USB NCM.
- The remote shell is disabled by default, binds to device NCM IP `192.168.7.2:2326`, and keeps USB ACM serial bridge as the rescue/control channel.
- Dropbear SSH remains deferred until key, PTY, and auth policy are fixed.

## Source Changes

- Added `stage3/linux_init/init_v100.c` and `stage3/linux_init/v100/*.inc.c`.
- Added `stage3/linux_init/helpers/a90_rshell.c`.
- Added host wrapper `scripts/revalidation/rshell_host.py`.
- Added `A90_SERVICE_RSHELL` service registry entry.
- Added helper inventory entry for `a90_rshell` with ramdisk fallback `/bin/a90_rshell`.
- Added `rshell [status|start|stop|enable|disable|token [show]|rotate-token [value]]` command.
- Updated `status`, `bootstatus`, `selftest verbose`, ABOUT/changelog, and helper deploy inventory for remote shell state.

## Artifacts

| Artifact | SHA256 |
| --- | --- |
| `stage3/linux_init/init_v100` | `073f80024682fbdc655a4b3e99a025ef1d045d3e3ddf5bb63e0ded97d55f5a54` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |
| `stage3/ramdisk_v100.cpio` | `a27217ece3bea98ce6f6bbf3a468d09ca50fade7d7b3efc05f1e28dea26ee79a` |
| `stage3/boot_linux_v100.img` | `1d15bcba2999d0c46caec3d568ac937201c13a924dd09a1586719154c22abd0c` |

Ramdisk entries:

```text
/init
/bin/a90sleep
/bin/a90_cpustress
/bin/a90_rshell
```

## Static Validation

- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` helper build — PASS.
- `aarch64-linux-gnu-gcc -static -Os -Wall -Wextra` init multi-source build — PASS.
- Local x86 protocol smoke of `a90_rshell.c` with fake BusyBox shim — PASS.
- `git diff --check` — PASS.
- `python3 -m py_compile scripts/revalidation/a90ctl.py scripts/revalidation/native_init_flash.py scripts/revalidation/rshell_host.py scripts/revalidation/helper_deploy.py` — PASS.
- `bash -n scripts/revalidation/build_static_busybox.sh` — PASS.
- Boot image strings contain `A90 Linux init 0.9.0 (v100)`, `A90v100`, `0.9.0 v100 REMOTE SHELL`, and `A90RSH1` — PASS.
- v100 source tree stale v99 marker scan — PASS.

## Flash Validation

Command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v100.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.0 (v100)" \
  --verify-protocol auto
```

Result:

- Local image SHA256 matched remote `/tmp/native_init_boot.img`.
- Boot partition prefix SHA256 matched `stage3/boot_linux_v100.img`.
- Post-boot `cmdv1 version/status` returned `rc=0`, `status=ok`.

## Device Regression

- `version`: PASS, `A90 Linux init 0.9.0 (v100)`.
- `status`: PASS, `selftest pass=11 warn=0 fail=0`, `helpers entries=7 warn=0 fail=0`, `rshell stopped` by default.
- `bootstatus`: PASS, `rshell: stopped pid=-1 port=2326`.
- `selftest verbose`: PASS, service row includes `rshell=-1` before start.
- `helpers verbose`: PASS, `a90_rshell` preferred `/bin/a90_rshell`, fallback present yes.
- `userland`: PASS, BusyBox ready, toybox ready.
- `storage`, `mountsd status`: PASS, SD runtime root `/mnt/sdext/a90` writable.
- `stat /bin/a90_rshell`: PASS, mode `0755`.

## Remote Shell Validation

Host NCM setup used NetworkManager because sudo passwordless `ip addr replace` was not available in this session:

```bash
nmcli connection add type ethernet ifname enx8aa99ba54b38 con-name a90-v100-ncm \
  ipv4.method manual ipv4.addresses 192.168.7.1/24 ipv4.never-default yes ipv6.method disabled
nmcli connection up a90-v100-ncm
ping -c 3 -W 2 192.168.7.2
nmcli connection delete a90-v100-ncm
```

Result:

- Host NCM interface: `enx8aa99ba54b38`.
- Device NCM IP: `192.168.7.2`.
- Host NCM IP: `192.168.7.1/24`.
- Ping: `3/3`, 0% packet loss.

`rshell` smoke:

```bash
python3 scripts/revalidation/rshell_host.py --bridge-timeout 60 start
python3 scripts/revalidation/rshell_host.py --timeout 15 exec 'echo A90_RSHELL_OK'
python3 scripts/revalidation/rshell_host.py --timeout 20 smoke
python3 scripts/revalidation/rshell_host.py --bridge-timeout 30 stop
```

Result:

- `rshell start`: PASS, pid started, token generated/read, helper `/bin/a90_rshell`.
- `exec 'echo A90_RSHELL_OK'`: PASS, `A90RSH1 END rc=0`.
- `busybox uname -a`: PASS, kernel string returned over TCP.
- `busybox ls /proc | busybox head -5`: PASS, payload returned over TCP.
- `rshell stop`: PASS, service stopped and `pid=-1`.
- Post-stop process check: no `a90_rshell` process left.

## Rollback / Rescue Check

- `netservice stop` caused expected USB re-enumeration and interrupted `cmdv1` END marker, then ACM serial bridge recovered.
- Post-rollback `version`: PASS.
- Post-rollback `rshell status`: PASS, `running=no`, `ncm=absent`, `tcpctl=stopped`.
- Post-rollback `netservice status`: PASS, `ncm0=absent`, `tcpctl=stopped`.

## Notes

- `rshell start` can interrupt framed `cmdv1` output when it has to start NCM first. `rshell_host.py` therefore treats `start/stop` as raw-control-like operations and waits for `rshell status` after the command.
- The helper uses token auth and does not expose token value through normal `status`; `rshell token show` is explicit.
- The listener binds to `192.168.7.2:2326`, not all interfaces.
- Interactive PTY/login shell is intentionally not part of v100 acceptance.

## Next

- v101 should focus on service manager policy cleanup: boot/start/stop dependencies, service state display, re-enumeration-aware control flow, and service rollback semantics.
