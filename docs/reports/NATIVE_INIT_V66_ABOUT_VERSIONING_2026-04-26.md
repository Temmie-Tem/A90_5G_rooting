# Native Init v66 About / Versioning Report

Date: `2026-04-26`

## Summary

`A90 Linux init 0.7.3 (v66)` adds official version metadata, creator display,
and an `APPS / ABOUT` menu for version, changelog, and credits.

- official version: `0.7.3`
- build tag: `v66`
- display name: `A90 Linux init 0.7.3 (v66)`
- creator: `made by temmie0214`

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v66` | `31a8c6e8da1f2ab07fe26a96d6fa78ba02a9cb43e6bc4ea3080220f4efb41715` |
| `stage3/ramdisk_v66.cpio` | `446b070e9df82b6368122ca190c27c3298a147eb778f70c9d08cc7e9bcf7e972` |
| `stage3/boot_linux_v66.img` | `320a325531b6e2ffc35c8165179396638c1c8af5ee4a59517f1074dc92b3eb08` |

## Source Changes

- `stage3/linux_init/init_v66.c`
  - `INIT_VERSION "0.7.3"`
  - `INIT_BUILD "v66"`
  - `INIT_CREATOR "made by temmie0214"`
  - `INIT_BANNER "A90 Linux init 0.7.3 (v66)"`
  - splash, `version`, `status`, timeline banner updated
  - `APPS / ABOUT` menu added
  - `VERSION`, `CHANGELOG`, `CREDITS` screens added

## Flash Validation

실행:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v66.img \
  --from-native \
  --expect-version "A90 Linux init 0.7.3 (v66)" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

결과:

- local marker/SHA256 확인 — PASS
- remote `/tmp/native_init_boot.img` SHA256 확인 — PASS
- boot partition prefix SHA256 readback — PASS
- bridge `version` — `A90 Linux init 0.7.3 (v66)`

## Runtime Validation

`version`:

```text
A90 Linux init 0.7.3 (v66)
made by temmie0214
version: 0.7.3 build=v66
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
```

`status`:

```text
init: A90 Linux init 0.7.3 (v66)
creator: made by temmie0214
boot: BOOT OK shell 3S
autohud: running
netservice: disabled tcpctl=stopped
```

`timeline`:

```text
00     1352ms init-start         rc=0 errno=0 A90 Linux init 0.7.3 (v66)
11     1519ms display-splash     rc=0 errno=0 boot splash applied
13     3783ms autohud            rc=0 errno=0 started refresh=2
14     3783ms shell              rc=0 errno=0 interactive shell ready
```

## Manual Visual Check

- Splash should show `A90 Linux init 0.7.3 (v66)` and `made by temmie0214`.
- Auto menu path:
  - `APPS >`
  - `ABOUT >`
  - `VERSION`, `CHANGELOG`, `CREDITS`

## Next

1. 사용자 육안으로 `APPS / ABOUT` 화면 확인
2. 문제 없으면 v66 기준점 commit
3. 다음 후보는 storage detail 또는 network detail app

