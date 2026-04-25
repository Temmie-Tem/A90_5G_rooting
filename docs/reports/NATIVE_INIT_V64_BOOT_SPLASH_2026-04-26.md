# Native Init v64 Custom Boot Splash Report

Date: `2026-04-26`

## Summary

`A90 Linux init v64`는 부팅 직후 보이던 큰 `TEST` 디버그 화면을
프로젝트 전용 splash 화면으로 교체한다.

- Boot splash title: `A90 NATIVE INIT`
- Subtitle: `BOOTING CUSTOM USERSPACE`
- Status rows: kernel, display, serial, runtime 준비 상태
- 기존 흐름 유지: splash 약 2초 후 `autohud`와 버튼 메뉴로 전환
- Timeline: `display-splash` 단계로 기록

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v64` | `f80152f02db376080bdcae3600ce6daf03e64bc08e0e092a8ae3b9116ea7bde2` |
| `stage3/ramdisk_v64.cpio` | `8560785b5e2832d40913b3b0e91a90e633041809a788200ebb6aa875c12ed018` |
| `stage3/boot_linux_v64.img` | `aa628f70f09a62f704b9d2078aae888ad57d95349fcaf8d3af47d95a3ad864ca` |

## Source Changes

- `stage3/linux_init/init_v64.c`
  - `INIT_VERSION "v64"`
  - `BOOT_SPLASH_SECONDS 2`
  - `kms_draw_boot_splash()` 추가
  - `boot_auto_frame()`이 splash를 그리고 `display-splash` timeline 기록
  - serial boot 안내를 `# Boot display: splash 2s -> autohud 2s.`로 변경

## Flash Validation

실행:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v64.img \
  --from-native \
  --expect-version "A90 Linux init v64" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

결과:

- local image SHA256 확인 — PASS
- remote `/tmp/native_init_boot.img` SHA256 확인 — PASS
- boot partition prefix SHA256 readback — PASS
- bridge `version` — `A90 Linux init v64`

## Runtime Validation

Bridge 확인:

```text
version
A90 Linux init v64
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
```

Status 확인:

```text
status
init: A90 Linux init v64
boot: BOOT OK shell 3S
autohud: running
netservice: disabled tcpctl=stopped
```

Timeline 확인:

```text
11     1647ms display-splash     rc=0 errno=0 boot splash applied
12     3649ms console            rc=0 errno=0 serial console attached
13     3911ms autohud            rc=0 errno=0 started refresh=2
14     3911ms shell              rc=0 errno=0 interactive shell ready
```

Log 확인:

```text
[1646ms] boot: display boot splash applied
[1647ms] timeline: display-splash rc=0 errno=0 detail=boot splash applied
```

## Notes

- `kms_draw_giant_test_probe()`는 debug/test pattern용으로 남겨 두지만 boot path에서는 더 이상 사용하지 않는다.
- 사용자 육안 검증은 splash가 `A90 NATIVE INIT` / `BOOTING CUSTOM USERSPACE`를 읽기 좋게 표시하는지 확인하면 된다.
- 화면이 너무 짧게 보이면 `BOOT_SPLASH_SECONDS`만 조정하면 된다.

## Next

1. 사용자가 육안으로 splash 디자인/가독성을 확인
2. splash가 좋으면 v63/v64 변경을 commit 기준점으로 고정
3. 다음 UI 후보는 앱 메뉴의 sensor detail/storage/network detail 화면
