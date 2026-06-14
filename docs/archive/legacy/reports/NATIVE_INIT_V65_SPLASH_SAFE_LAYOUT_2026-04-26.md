# Native Init v65 Splash Safe Layout Report

Date: `2026-04-26`

## Summary

`A90 Linux init v65`는 v64 custom boot splash에서 일부 텍스트가 잘리는 문제를 줄이기 위한
safe layout 버전이다.

- 긴 status row를 짧게 정리
- splash 기본 글자 크기 축소
- 좌우 안전 여백 확대
- 각 줄을 `shrink_text_scale()`로 자동 축소
- footer를 조금 위로 올리고 card 폭 안에 맞춤

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v65` | `2cb2b9e5e8d989cddb92f3c1ef93b8f4674ba4359408445b19af5745ddc2f373` |
| `stage3/ramdisk_v65.cpio` | `b8184bb241c52b0d99e9efbceed16ded50598a24068a359c8d8e3abf78f1c16f` |
| `stage3/boot_linux_v65.img` | `143acc7925b8ac0006d972ca463c1993f5306b63c5187e9c3007a34fa71ed7d4` |

## Source Changes

- `stage3/linux_init/init_v65.c`
  - `INIT_VERSION "v65"`
  - `kms_draw_text_fit()` 추가
  - `kms_draw_boot_splash()`에서 row/footer max width 계산
  - `BOOT_SPLASH_SECONDS 2` 유지

## Flash Validation

실행:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v65.img \
  --from-native \
  --expect-version "A90 Linux init v65" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

결과:

- local image SHA256 확인 — PASS
- remote `/tmp/native_init_boot.img` SHA256 확인 — PASS
- boot partition prefix SHA256 readback — PASS
- bridge `version` — `A90 Linux init v65`

## Runtime Validation

Status:

```text
init: A90 Linux init v65
boot: BOOT OK shell 3S
autohud: running
netservice: disabled tcpctl=stopped
```

Timeline:

```text
11     1528ms display-splash     rc=0 errno=0 boot splash applied
12     3531ms console            rc=0 errno=0 serial console attached
13     3792ms autohud            rc=0 errno=0 started refresh=2
14     3792ms shell              rc=0 errno=0 interactive shell ready
```

## Visual Check

- v64: splash는 보였지만 일부 텍스트가 잘림
- v65: code-level safe layout 적용, bridge/timeline 기준 정상 부팅 확인
- 최종 육안 판정은 사용자 화면 확인으로 마무리한다.

## Next

1. 사용자가 v65 splash 가독성과 잘림 여부 확인
2. 여전히 잘리면 v66에서 splash 요소 수를 더 줄이고 중앙 card 형태로 단순화
3. 문제가 없으면 v63~v65 변경을 commit 기준점으로 고정
