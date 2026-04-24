# Native Init V53 Menu Busy Gate

Date: `2026-04-25`

## Summary

`A90 Linux init v53`는 자동 화면 메뉴가 떠 있는 동안 serial shell의 위험/상태 변경 명령을
즉시 실행하지 않고 `[busy]`로 차단한다. `version`, `status` 같은 안전한 관찰 명령은
계속 허용하며, host automation은 `hide`를 보내 메뉴를 숨긴 뒤 재시도할 수 있다.

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v53` | `4c742213dc1d2541db2d45e61af2a64d829d2f008975622465e5b78ce5c4bdbd` |
| `stage3/ramdisk_v53.cpio` | `139f0dceea7c5c64d501463d678dd3f80c29385566e22babeb28a4465ddf6001` |
| `stage3/boot_linux_v53.img` | `44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046` |

## Behavior

- 자동 HUD/menu child가 켜지면 `/tmp/a90-auto-menu-active`에 active state를 기록한다.
- serial shell은 menu active 상태에서 위험하거나 오래 걸릴 수 있는 명령을 실행하지 않는다.
- 차단된 명령은 hang이 아니라 즉시 `[busy] auto menu active; send hide/q or select HIDE MENU`를 반환한다.
- `hide`, `hidemenu`, `resume`, `q`, `Q`는 `/tmp/a90-auto-menu-request`에 hide request를 남긴다.
- menu child는 hide request를 소비하고 화면 메뉴를 숨긴 뒤 active state를 `0`으로 바꾼다.
- `start_auto_hud()`가 fork 전에 active state를 먼저 세팅해 boot 직후 serial command race를 줄였다.

## Allowed While Menu Is Active

관찰/복구용 최소 명령은 메뉴가 떠 있어도 허용한다.

- `help`
- `version`
- `status`
- `bootstatus`
- `timeline`
- `last`
- `logpath`
- `logcat`
- `uname`
- `pwd`
- `mounts`
- `reattach`
- `stophud`

## Flash Automation Fix

`scripts/revalidation/native_init_flash.py --from-native`는 이제 `recovery`가 `[busy]`로 막히면
자동으로 `hide`를 보낸 뒤 `recovery`를 재시도한다. 이 때문에 v52/v53 화면 메뉴가 떠 있어도
native init → TWRP → flash → native init 검증 루프가 끊기지 않는다.

## Validation

Flash command:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v53.img \
  --from-native \
  --expect-version "A90 Linux init v53" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Observed:

```text
local image sha256: 44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046
remote image sha256: 44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046
boot block prefix sha256: 44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046
A90 Linux init v53
```

Menu gate checks:

```text
echo busytest
[busy] auto menu active; send hide/q or select HIDE MENU

version
A90 Linux init v53
[done] version (0ms)

hide
[busy] auto menu active; hide requested

echo afterhide
afterhide
[done] echo (0ms)

cat /tmp/a90-auto-menu-active
0
[done] cat (0ms)
```

## Notes

- v48 remains the conservative known-good fallback image.
- v49 remains quarantined because it booted Android userspace after a matching prefix readback.
- v53 is the latest verified native init for the display/menu/shell interaction path.
