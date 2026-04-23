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
  - 빠른 개발용 게이트 용도
- `serial_console.py`
  - 위 브릿지에 붙는 interactive console client
  - raw shell 출력은 그대로 보여주되, `waitkey`/`blindmenu`/`key ...` 같은
    라인을 `[watch]` 메모로 한 번 더 띄워서 버튼 입력을 더 눈에 띄게 보여줌
  - `Ctrl-]` 로 로컬 콘솔만 종료 가능

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

참고:

- 현재 호스트 계정이 `dialout` 그룹이 아니면 `sudo`로 실행해야 할 수 있습니다.
- 이 브릿지는 빠른 개발용 최소 구현이라 클라이언트 1개만 허용합니다.
- 따라서 `serial_console.py`와 `nc`는 동시에 붙지 않습니다.
- 장기적으로는 `USB networking + SSH` 또는 안정적인 `ADB` 채널이 더 적합합니다.

생성 산출물은 기본적으로 `backups/` 아래에 저장합니다.
`.img`와 백업 디렉토리는 이미 `.gitignore`에 포함되어 있습니다.

과거 AOSP, headless Android, Magisk 모듈, 커널 최적화 스크립트는 `../archive/legacy/`를 참고합니다.
