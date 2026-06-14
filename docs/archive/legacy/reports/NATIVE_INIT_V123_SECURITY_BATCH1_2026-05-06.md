# A90 Native Init v123 Security Batch 1

Date: 2026-05-06
Build: `A90 Linux init 0.9.23 (v123)`
Marker: `0.9.23 v123 SECURITY BATCH1`

## Summary

v123 implements Security Batch 1 root-control hardening. The main change is that
`a90_tcpctl` no longer exposes unauthenticated network `run`/`shutdown` control:
the netservice path binds tcpctl to the intended device NCM address
`192.168.7.2`, starts it with token authentication, and uses the ramdisk
`/bin/a90_tcpctl` helper instead of writable `/cache/bin/a90_tcpctl`.

## Changes

- Added tcpctl `auth <token>` session state.
- Kept unauthenticated tcpctl `ping`, `version`, `status`, and `help` for liveness checks.
- Required tcpctl authentication for `run` and `shutdown`.
- Changed netservice tcpctl spawn to `listen 192.168.7.2 2325 3600 0 /cache/native-init-tcpctl.token`.
- Added `netservice token [show|rotate]`.
- Moved the netservice tcpctl executable path to ramdisk `/bin/a90_tcpctl`.
- Added `/bin/a90_tcpctl` to `stage3/ramdisk_v123.cpio`.
- Marked shell `service` command as `CMD_DANGEROUS`.
- Made `physical_usb_reconnect_check.py` cleanup fail closed.
- Updated host tcpctl/reconnect tools to use token auth by default, with `--no-auth` for legacy checks.

## Finding Coverage

| finding | v123 result |
|---|---|
| F005 | Mitigated: tcpctl network root `run` requires token auth and no longer binds all interfaces in netservice mode. |
| F001 | Mitigated: rshell can still start netservice, but tcpctl is no longer unauthenticated. |
| F003 | Mitigated: persistent netservice flag no longer persists unauthenticated tcpctl exposure. |
| F010 | Mitigated: shell `service` wrapper is now dangerous-command gated. |
| F014 | Mitigated in primary checker: reconnect cleanup failure now fails the script. |
| F021 | Accepted lab trust boundary: USB ACM root shell remains intentional local rescue/control path. |
| F023 | Partially covered: service wrapper bypass is closed; broader busy-gate policy remains unchanged. |
| F030 | Accepted lab trust boundary: localhost serial bridge remains operator-local root control path. |

## Artifacts

| artifact | sha256 |
|---|---|
| `stage3/linux_init/init_v123` | `c0441c3dd9951433f10cdca11b2cc79544491a7f90d0217282d8d7a85ebd98d7` |
| `stage3/ramdisk_v123.cpio` | `1d456ad6b7736bb856161e6c4462c7afd960d50781f3335fc1a005ab46658e1d` |
| `stage3/boot_linux_v123.img` | `289264335a14ad7b543fbc4425f856d5f1763b2bc2f0f7028b6dc7c118cc5b57` |
| `external_tools/userland/bin/a90_tcpctl-aarch64-static` | `4fa39e9fca2e5c221d757bd2e09f0930f31864f41ae1daf79271dd5ccb41c764` |

## Validation

### Static

- ARM64 static init build — PASS.
- ARM64 static tcpctl helper build — PASS.
- `strings` marker check for `A90 Linux init 0.9.23 (v123)`, `A90v123`, `0.9.23 v123 SECURITY BATCH1`, and `/bin/a90_tcpctl` — PASS.
- `python3 -m py_compile` for flash/control/netservice helper scripts — PASS.
- `git diff --check` — PASS.

### Host Protocol Smoke

Native host-compiled `a90_tcpctl` auth smoke — PASS:

- `ping` returns `pong` without auth.
- unauthenticated `run /bin/true` returns `ERR auth-required`.
- `auth <token>` then `run /bin/true` returns `OK`.
- `auth <token>` then `shutdown` returns `OK shutdown`.

### Flash

Command:

```sh
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v123.img \
  --from-native \
  --expect-version "A90 Linux init 0.9.23 (v123)" \
  --verify-protocol auto
```

Result: PASS.

Evidence:

- local image marker and SHA256 verified
- TWRP push and remote SHA256 verified
- boot partition prefix SHA256 matched image SHA256
- post-boot `cmdv1 version/status` PASS with `rc=0 status=ok`

### Runtime Checks

- `helpers path a90_tcpctl` — PASS: preferred/fallback path is `/bin/a90_tcpctl`.
- `netservice status` — PASS: `bind=192.168.7.2`, `auth=required`, token path `/cache/native-init-tcpctl.token`.
- `netservice token show` — PASS: generated/read token through `getrandom()` backed path.
- `netservice start` — PASS: `ncm0=present tcpctl=running`.
- `netservice stop` cleanup — PASS: `ncm0=absent tcpctl=stopped`.

Host NCM end-to-end TCP run validation was blocked by non-interactive host sudo:
`sudo-rs: interactive authentication is required` while configuring
`192.168.7.1/24` on the detected `enx...` interface. The script failed closed
and restored ACM-only state.

## Acceptance

Security Batch 1 is complete for the current native-init code path. The remaining
root-control work should continue with Batch 2 helper/runtime trust and Batch 3
host tooling trust-boundary hardening.
