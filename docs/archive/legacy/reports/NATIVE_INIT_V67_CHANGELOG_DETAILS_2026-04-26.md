# Native Init v67 Changelog Detail Report

Date: `2026-04-26`

## Summary

`A90 Linux init 0.7.4 (v67)` keeps the v66 ABOUT/versioning foundation and
turns changelog into a button-navigable version list with detailed per-version
screens. ABOUT-style text is also reduced so the A90's tall display can show
more content without clipping.

- official version: `0.7.4`
- build tag: `v67`
- display name: `A90 Linux init 0.7.4 (v67)`
- creator: `made by temmie0214`

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v67` | `642da01258a4a43016e5362d74fb2c142a30c42001217c88fa2ae2fe8aa05e04` |
| `stage3/ramdisk_v67.cpio` | `55d2b9c0323e2642c9d7095a62d668b85774476fe5079a43113ef7a5b3e7b6b2` |
| `stage3/boot_linux_v67.img` | `8b087d08ecc5dd459ffd36c22c520f5de9fb2c3ddecee0c212bd4fece57f8623` |

## Source Changes

- `stage3/linux_init/init_v67.c`
  - `INIT_VERSION "0.7.4"`
  - `INIT_BUILD "v67"`
  - `A90v67` kmsg and `mark_step(..._v67)` markers
  - compact ABOUT text scale for version/changelog/credits screens
  - `APPS / ABOUT / CHANGELOG >` submenu
  - detail screens for `0.7.4 v67`, `0.7.3 v66`, `0.7.2 v65`, `0.7.1 v64`, `0.7.0 v63`, and `0.6.0 v62`

## Flash Validation

실행:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v67.img \
  --from-native \
  --expect-version "A90 Linux init 0.7.4 (v67)" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

결과:

- local marker/SHA256 확인 — PASS
- remote `/tmp/native_init_boot.img` SHA256 확인 — PASS
- boot partition prefix SHA256 readback — PASS
- bridge `version` — `A90 Linux init 0.7.4 (v67)`

## Runtime Validation

`version`:

```text
A90 Linux init 0.7.4 (v67)
made by temmie0214
version: 0.7.4 build=v67
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
```

`status`:

```text
init: A90 Linux init 0.7.4 (v67)
creator: made by temmie0214
boot: BOOT OK shell 3S
autohud: running
netservice: disabled tcpctl=stopped
```

`timeline`:

```text
00     1362ms init-start         rc=0 errno=0 A90 Linux init 0.7.4 (v67)
11     1538ms display-splash     rc=0 errno=0 boot splash applied
13     3802ms autohud            rc=0 errno=0 started refresh=2
14     3802ms shell              rc=0 errno=0 interactive shell ready
```

## Manual Visual Check

- `APPS >` → `ABOUT >` → `CHANGELOG >` should show a version list.
- Selecting a version should open a compact detail screen.
- ABOUT detail screens should use smaller text than the main menu and should not clip in normal portrait layout.

## Next

1. 사용자 육안으로 version list/detail 화면 확인
2. 문제 없으면 v67 기준점 commit
3. 다음 후보는 physical USB reconnect soak 또는 serial noise fragment hardening
