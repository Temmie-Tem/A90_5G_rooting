# Native Init v112 USB/NCM Service Soak

Date: `2026-05-04`
Build: `A90 Linux init 0.9.12 (v112)`
Marker: `0.9.12 v112 USB SERVICE SOAK`
Baseline: `A90 Linux init 0.9.11 (v111)`

## Summary

v112 is an opt-in USB/NCM service soak checkpoint after the v111 extended soak RC.
It keeps netservice disabled by default, validates NCM/tcpctl start over the real USB link, and verifies rollback to ACM-only control.

No runtime UX feature was added.

## Source Changes

- Added `stage3/linux_init/init_v112.c` and `stage3/linux_init/v112/*.inc.c` from v111.
- Updated `stage3/linux_init/a90_config.h` to `0.9.12` / `v112`.
- Added v112 ABOUT/changelog entries.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v112` | `c4f3f29ec7817d07a52e8e465d5f6c13b115bd9f71a6d7123b4d29d977bb19c9` |
| `stage3/ramdisk_v112.cpio` | `6ed5b49a2f166ae58f6c3f52a83161238adb7faf6f65efb7e47afec7d273e757` |
| `stage3/boot_linux_v112.img` | `60fd3451dd8853f047098ab0f3143cd7d4edf80e6d38a58e66b9a18b44825ede` |
| `stage3/linux_init/helpers/a90_cpustress` | `2130ddf1821c4331d491706636e0197b0f587a086f182e8745e5b41333a069bd` |
| `stage3/linux_init/helpers/a90_rshell` | `235d30bc6bc0b6254b8f1383697cf03bbd6760eaf42944b786510d835ebdf02d` |

## Static Validation

- ARM64 static build with `-static -Os -Wall -Wextra` — PASS.
- `strings` markers found:
  - `A90 Linux init 0.9.12 (v112)`
  - `A90v112`
  - `0.9.12 v112 USB SERVICE SOAK`
- `git diff --check` — PASS.
- Host Python `py_compile` for `a90ctl.py`, `native_init_flash.py`, `native_soak_validate.py`, `tcpctl_host.py`, and `ncm_host_setup.py` — PASS.
- v112 include tree marker check for `0.9.12`, `v112`, and `A90v112` — PASS.

## Device Validation

Flash command:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v112.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.12 (v112)" \
  --verify-protocol auto
```

Result:

- Native bridge v111 to TWRP recovery path succeeded.
- Boot partition prefix SHA matched `stage3/boot_linux_v112.img` — PASS.
- Post-boot `cmdv1 version/status` verified `A90 Linux init 0.9.12 (v112)` — PASS.
- Boot selftest reported `pass=11 warn=0 fail=0` — PASS.

## USB/NCM Service Soak

Device-side setup:

- `netservice status` initially showed `enabled=no`, `ncm0=absent`, `tcpctl=stopped` — PASS.
- `ncm_host_setup.py setup` brought up composite ACM+NCM on the device — PASS.
- USB re-enumeration changed the host NCM interface from `enx6ea82aab10ac` to `enxaa46a6adcb05`; `ncm_host_setup.py status` correctly identified the new `ncm.host_addr` — PASS.
- Host IPv4 was applied through NetworkManager profile update because sudo interactive authentication was unavailable in the agent shell:

```bash
nmcli connection modify "유선 연결 2" \
  ipv4.method manual \
  ipv4.addresses 192.168.7.1/24 \
  ipv4.gateway '' \
  ipv4.never-default yes \
  ipv4.may-fail no \
  ipv6.method link-local
nmcli connection up "유선 연결 2" ifname enxaa46a6adcb05
```

NCM link validation:

| Check | Result |
|---|---|
| `ping -c 3 -W 2 192.168.7.2` | PASS, 3/3 replies |
| IPv6 link-local ping | PASS |
| device `/proc/net/tcp` | PASS, `0.0.0.0:2325` LISTEN |

TCP control validation:

| Command | Result |
|---|---|
| `python3 scripts/revalidation/tcpctl_host.py ping` | PASS, `pong` |
| `python3 scripts/revalidation/tcpctl_host.py status` | PASS, kernel/uptime/load/memory output |
| `python3 scripts/revalidation/tcpctl_host.py run /bin/a90sleep 1` | PASS, helper exited `0` |

Rollback validation:

- `python3 scripts/revalidation/ncm_host_setup.py off` interrupted during USB re-enumeration as expected and then confirmed ACM serial response — PASS.
- `version` over serial bridge after rollback returned `A90 Linux init 0.9.12 (v112)` — PASS.
- `netservice stop` left `ncm0=absent` and `tcpctl=stopped` — PASS.
- `selftest verbose` after rollback reported `pass=11 warn=0 fail=0` — PASS.

## Soak Regression

Command:

```bash
python3 scripts/revalidation/native_soak_validate.py \
  --cycles 3 \
  --sleep 2 \
  --expect-version "A90 Linux init 0.9.12 (v112)" \
  --out tmp/soak/v112-usb-service-soak.txt
```

Result: `PASS cycles=3 commands=14`.

## Notes

- Netservice remains disabled by default after the test.
- `netservice start|stop` and USB gadget rebind operations can drop framed `A90P1 END` output; host tooling should continue treating them as raw-control/reconnect operations.
- v113 should focus on runtime/package layout and keep USB/NCM as a verified rescue/service path.
