# Claude Handoff Prompt

Date: `2026-04-25`

아래 블록을 Claude나 다른 에이전트에게 그대로 붙여 넣는다.
목표는 **먼저 상태를 확인하고, known-good v48 복구 경로와 latest v53 작업 경로를 혼동하지 않게 하는 것**이다.

```text
너는 /home/temmie/dev/A90_5G_rooting 저장소에서 작업한다.

먼저 반드시 다음 문서를 읽고, 문서와 충돌하는 행동을 하지 마라.

1. docs/operations/NATIVE_INIT_FLASH_AND_BRIDGE_GUIDE.md
2. docs/operations/CLAUDE_NATIVE_INIT_RUNBOOK.md
3. docs/overview/PROJECT_STATUS.md

현재 기준:

- latest verified native init: A90 Linux init v53
- latest source: stage3/linux_init/init_v53.c
- latest boot image: stage3/boot_linux_v53.img
- latest boot image SHA256:
  44cb9ebb3cc65ab0b3316afe69592c8b7fa7a05a96c872dfd2a4f9f884d98046
- known-good fallback native init: A90 Linux init v48
- known-good fallback source: stage3/linux_init/init_v48.c
- known-good fallback boot image: stage3/boot_linux_v48.img
- known-good fallback boot image SHA256:
  1c87fa59712395027c5c2e489b15c4f6ddefabc3c50f78d3c235c4508a63e042
- control channel: USB CDC ACM serial bridge at 127.0.0.1:54321
- TWRP recovery is available.

절대 하지 말 것:

- stage3/boot_linux_v49.img를 stable처럼 flash하지 마라.
- stage3/linux_init/init_v49.c를 다음 기준으로 삼지 마라.
- 수동 adb shell dd로 boot/recovery/vbmeta/efs/sec_efs/modem/persist/key 계열 partition을 쓰지 마라.
- twrp reboot system을 쓰지 마라. 이 기기에서는 no-op처럼 TWRP에 머물 수 있다.
- adb reboot 또는 adb shell reboot를 TWRP system exit로 신뢰하지 마라. recovery로 되돌아올 수 있다.
- bridge 응답이 없다는 이유만으로 곧바로 다시 flash하지 마라.
- v53 화면 메뉴가 떠 있을 때 `[busy]`가 나오면 정상 보호 동작이다. 먼저 `hide`를 보내라.

v49 주의:

- v49 image는 local marker와 boot partition prefix readback은 맞았지만,
  system boot 후 Android /system/bin/init second_stage로 진입했다.
- 따라서 v49는 현재 "격리된 실패 실험"이다.
- 새 실험 버전은 v50 이상으로 잡고, 현재 latest verified에서 최소 diff로 시작한다.

작업 시작 시 반드시 먼저 실행:

git status --short
ps -ef | rg 'serial_tcp_bridge.py|native_init_flash.py' | rg -v rg || true
lsusb | rg 'Samsung|04e8' || true
ls -l /dev/ttyACM* /dev/serial/by-id 2>/dev/null || true
adb devices -l || true
printf 'version\n' | nc -w 5 127.0.0.1 54321 || true

판단:

- bridge에서 A90 Linux init v53이 나오면 latest verified native init 상태다.
- bridge에서 A90 Linux init v48이 나오면 known-good fallback native init 상태다.
- adb devices -l에서 recovery면 TWRP 상태다.
- adb devices -l에서 device이고 /proc/1/exe가 /system/bin/init이면 Android 상태다.
- 04e8:6861 + /dev/ttyACM0인데 bridge가 안 되면 사용자가 sudo bridge를 재시작해야 한다.

latest v53 flash가 정말 필요할 때만 이 스크립트를 사용:

python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v53.img \
  --from-native \
  --expect-version "A90 Linux init v53" \
  --bridge-timeout 240 \
  --recovery-timeout 180

이 스크립트는 local marker/SHA 확인, remote SHA 확인,
boot partition prefix readback 확인, TWRP no-argument reboot,
bridge version 검증을 수행한다. v53 메뉴가 떠 있어 `recovery`가 `[busy]`이면
자동으로 `hide`를 보내고 재시도한다.

known-good v48로 되돌릴 때만:

python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v48.img \
  --expect-version "A90 Linux init v48" \
  --bridge-timeout 240 \
  --recovery-timeout 180

TWRP에서 system/native init으로 나갈 때 수동 명령이 필요하면:

adb shell 'twrp reboot'

새 native init 버전을 만들 때:

- latest verified source를 기준으로 복사한다. 단, v48 known-good fallback은 보존한다.
- 현재 실패 번호 v49는 재사용하지 말고 v50 이상을 사용한다.
- local build 후 marker 문자열을 확인한다.
- TWRP flash 전 user confirmation을 받는다.
- flash 후에는 반드시 boot partition prefix SHA readback과 bridge version을 확인한다.

응답할 때는 다음을 명확히 보고한다.

1. 현재 상태가 native init / TWRP / Android 중 무엇인지
2. 어떤 boot image SHA를 확인했는지
3. bridge가 살아 있는지
4. 다음 행동이 read-only인지 write/flash인지
```
