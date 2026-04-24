# Revalidation Scripts

현재 디렉토리는 rooted baseline과
`native Linux rechallenge` 전단계인 부트체인 재검증에 직접 필요한 스크립트만 두는 자리입니다.

현재 포함 범위:

- `verify_device_state.sh`
  - `adb devices`
  - `sys.boot_completed`
  - `su -c id`
  - 기본 verified boot 관련 prop
  - 필요 시 Wi-Fi 상태
- `capture_baseline.sh`
  - 현재 `boot`, `recovery`, `vbmeta` 백업
  - `getprop`, root 상태, Wi-Fi 상태 저장
  - 다운로드 모드 수동 기록용 노트 템플릿 생성
- `serial_tcp_bridge.py`
  - host의 `/dev/ttyACM0` 또는 `/dev/serial/by-id/...`를
    `127.0.0.1:<port>`로 노출하는 최소 브릿지
  - USB ACM shell을 TCP 클라이언트 한 개로 전달
  - serial 재연결 시 자동 재오픈
  - v48 이후 USB 재열거로 device node identity가 바뀌면 stale fd를 닫고 재연결
  - 빠른 개발용 게이트 용도
- `serial_console.py`
  - 위 브릿지에 붙는 interactive console client
  - raw shell 출력은 그대로 보여주되, `waitkey`/`blindmenu`/`key ...` 같은
    라인을 `[watch]` 메모로 한 번 더 띄워서 버튼 입력을 더 눈에 띄게 보여줌
  - `Ctrl-]` 로 로컬 콘솔만 종료 가능
- `native_init_flash.py`
  - TWRP recovery ADB에서 native init boot image를 boot 파티션에 기록
  - `adb devices` 출력을 whitespace split으로 파싱해 `recovery` 상태를 안정적으로 감지
  - TWRP에서 system으로 돌아갈 때 `adb shell twrp reboot system`을 우선 사용
  - 부팅 후 serial bridge에 붙어 `version`으로 기대 버전을 확인
- `build_static_toybox.sh`
  - 공식 `toybox-0.8.13` tarball을 해시 검증 후 다운로드
  - `aarch64-linux-gnu-gcc`로 static ARM64 toybox를 빌드
  - 산출물은 gitignore된 `external_tools/userland/bin/toybox-aarch64-static-0.8.13`
  - native init 실기 검증 시 `/cache/bin/toybox`로 올려 `run /cache/bin/toybox ...` 형태로 사용
- `build_usbnet_helper.sh`
  - `stage3/linux_init/a90_usbnet.c`를 static ARM64 helper로 빌드
  - 산출물은 gitignore된 `external_tools/userland/bin/a90_usbnet-aarch64-static`
  - TWRP ADB로 `/cache/bin/a90_usbnet`에 배치해 USB ACM/NCM/RNDIS probe에 사용

권장 순서:

```bash
./scripts/revalidation/verify_device_state.sh
./scripts/revalidation/capture_baseline.sh --label baseline_a
```

브릿지 실행 예:

```bash
sudo python3 ./scripts/revalidation/serial_tcp_bridge.py --port 54321
```

접속 예:

```bash
nc 127.0.0.1 54321
```

권장 콘솔 예:

```bash
python3 ./scripts/revalidation/serial_console.py --port 54321
```

관찰 전용 예:

```bash
python3 ./scripts/revalidation/serial_console.py --port 54321 --watch-only
```

native init 이미지 플래시/검증 예:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v48.img \
  --expect-version "A90 Linux init v48"
```

현재 native init에서 recovery로 전환한 뒤 플래시까지 이어가는 예:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v48.img \
  --expect-version "A90 Linux init v48" \
  --from-native
```

이미 부팅된 native init 버전만 확인하는 예:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  --verify-only \
  --expect-version "A90 Linux init v48"
```

static toybox 빌드 예:

```bash
./scripts/revalidation/build_static_toybox.sh
```

USB net helper 빌드 예:

```bash
./scripts/revalidation/build_usbnet_helper.sh
```

참고:

- 현재 호스트 계정이 `dialout` 그룹이 아니면 `sudo`로 실행해야 할 수 있습니다.
- 이 브릿지는 빠른 개발용 최소 구현이라 클라이언트 1개만 허용합니다.
- 따라서 `serial_console.py`와 `nc`는 동시에 붙지 않습니다.
- serial device가 없는 상태에서는 기본적으로 TCP client를 거절합니다.
  - 이전처럼 serial 없이도 client를 유지하고 싶으면 `--allow-client-without-serial`을 사용합니다.
- 장기적으로는 `USB networking + SSH` 또는 안정적인 `ADB` 채널이 더 적합합니다.

생성 산출물은 기본적으로 `backups/` 아래에 저장합니다.
`.img`와 백업 디렉토리는 이미 `.gitignore`에 포함되어 있습니다.

과거 AOSP, headless Android, Magisk 모듈, 커널 최적화 스크립트는 `../archive/legacy/`를 참고합니다.
