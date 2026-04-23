# Native Linux Rechallenge Progress Log

## 2026-04-23

### Stage 0 기준점 캡처 완료
- `scripts/revalidation/verify_device_state.sh` 통과 — 기준점 A 신호 전부 정상
- `scripts/revalidation/capture_baseline.sh --label baseline_a` 완료
  - 저장 경로: `backups/baseline_a_20260423_030309/`
  - boot.img (64MB), recovery.img (82MB), vbmeta.img (64KB) + SHA256SUMS
- 캡처 스크립트 버그 수정: Magisk `su -c` 인용 문제 → `sq_escape` 헬퍼로 단일 따옴표 래핑
- 다운로드 모드 값 사진으로 캡처 후 매트릭스 기준점 섹션 채움

### Stage 1 row 2, 4 완료
- row 2 (patched AP + stock recovery): 현재 기준점 A 상태 그대로 기록 (플래시 없음)
- row 4 (patched AP + TWRP): `adb shell su -c dd`로 recovery 파티션에 TWRP 직접 기록
  - sha256 검증 후 재부팅 → 정상 시스템 부팅, recovery fallback 없음
  - Magisk root / ADB / Wi-Fi 전부 유지
  - `verifiedbootstate=orange` 유지 (vbmeta Magisk 패치가 TWRP 서명 불일치 흡수)
- row 1, 3 (stock AP 포함 조합): stock AP 롤백이 필요한 시점에 자연 관찰 예정으로 deferred

### 기준점 재설정
- 기존 2025 방향 문서를 `docs/archive/legacy/`로 이동
- 상단 문서 트리를 현재 rooted baseline 중심으로 재구성

### native Linux rechallenge 재개
- 공식 목표를 `부트체인 재검증 자체`에서 `native Linux 부팅 재도전`으로 다시 고정
- rooted baseline A를 모든 후속 실험의 유일한 출발점으로 설정
- debloat와 최소 패키지화는 메인 목표에서 분리하고 참고용 보조 실험으로 유지

### 실행 문서 정비
- `docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md` 추가
- `docs/plans/REVALIDATION_PLAN.md`를 단계형 실행 체크리스트로 재작성
- `docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md` 작업 시트 추가
- `scripts/revalidation/`에 기준점 점검과 캡처용 헬퍼 추가

### 현재 rooted baseline
- patched AP 부팅 성공
- `Magisk 30.7` 확인
- `su` 동작 확인
- ADB 정상
- Wi-Fi 등록 및 연결 확인

### 다운로드 모드 스냅샷
- `RPMB Fuse Set`
- `RPMB PROVISIONED`
- `CURRENT BINARY : Custom (0x303)`
- `FRP LOCK : OFF`
- `OEM LOCK : OFF (U)`
- `WARRANTY VOID : 0x1 (0xE03)`
- `QUALCOMM SECUREBOOT : ENABLE`
- `RP SWREV : B5(1,1,1,5,1,1) K5 S5`
- `SECURE DOWNLOAD : ENABLE`
- `DID : 2030A54C447F3A11`
- `KG` 줄은 이번 사진 크롭에 보이지 않아 미확인 상태로 유지

### KG 미표시 관련 공식 문서 재확인
- Samsung Knox 공식 문서 기준으로 `KG STATE`가 다운로드 모드에 항상 표시된다는 규칙은 찾지 못함
- 공식 문서에서 Knox Guard는 cloud-managed device state로 설명되며,
  장치는 콘솔 등록, 활성화, 완료, 삭제에 따라 관리 상태가 변함
- 공식 문서상 `Completed` 또는 삭제 이후에는 Knox Guard client가
  비활성화되거나 영구 제거되고 더 이상 추적되지 않음
- 따라서 `KG 줄 자체가 안 뜨는 현상`은 공식 문서와 모순되지 않음
- 다만 공식 문서만으로 `KG 미표시 = 특정 KG 상태`라고 단정할 근거는 없음

참고 링크:

- https://docs.samsungknox.com/admin/knox-guard/
- https://docs.samsungknox.com/dev/knox-guard/how-knox-guard-works/
- https://docs.samsungknox.com/admin/knox-guard/kbas/what-happens-to-device-once-it-is-fully-paid/
- https://docs.samsungknox.com/admin/knox-guard/how-to-guides/manage-devices/view-device-details/

### 최소 부팅 상태
- allowlist 재적용 후 `user 0` 패키지 수 `92`
- 남은 extra `3개`
  - `com.samsung.android.game.gos`
  - `com.samsung.android.themecenter`
  - `com.sec.android.sdhms`

### 비고
- `com.google.android.documentsui`는 `user 0` 제거 후 재부팅 유지 확인
- `com.google.android.partnersetup`는 제거 시도 후 재부팅 시 복귀
- `GOS`, `SDHMS`는 `pm uninstall --user 0` / `su -c` 모두 실질 제거 실패
- `ThemeCenter`는 `DELETE_FAILED_INTERNAL_ERROR`

### Stage 3 후속 점검
- TWRP에서 `/cache/v2c_step = 9_udc_set` 확인
  - `v2c`는 최소한 configfs/functionfs 설정과 UDC 활성화까지 도달
- `/cache/adbd_exec_failed = 013` 파일은 남아 있었으나, TWRP에서
  `LD_LIBRARY_PATH=/cache/adb/lib /cache/adb/adbd --help` 재현 시
  `Permission denied`가 아니라 `Segmentation fault (rc=139)` 확인
- 커널 설정 재확인:
  - `CONFIG_USB_CONFIGFS_ACM=y`
  - `CONFIG_USB_F_ACM=y`
  - `CONFIG_USB_CONFIGFS_RNDIS=y`
- 따라서 다음 후보를 `Android adbd`에서 `USB ACM serial mini-shell`로 전환
  - 새 산출물:
    - `stage3/linux_init/init_v3.c`
    - `stage3/ramdisk_v3.cpio`
    - `stage3/boot_linux_v3.img`
- `boot_linux_v3.img`를 boot 파티션에 기록 후 `twrp reboot system` 실행
  - host `lsusb`: `04e8:6861 Samsung Electronics Co., Ltd SAMSUNG_Android`
  - host `adb devices -l`: 빈 목록
  - host `/dev/ttyACM0` 생성 확인
- 결론:
  - `native init -> USB ACM gadget` 경로는 실증
  - 마지막 남은 확인은 host serial open 후 mini-shell 배너/명령 응답 검증
  - 현재 Codex 세션 계정은 `dialout` 그룹이 아니어서 `/dev/ttyACM0` 직접 열 수 없음

### Native shell probe 정리
- `serial -> TCP` 브릿지로 `v8` shell에 직접 접속해 `/proc`, `/dev`, `/sys/class` probe 수행
- 확인된 것:
  - `SM8150` 기반 kernel/userspace shell 정상
  - `/cache`와 `/mnt/system` 마운트 정상
  - `backlight`, `input`, `drm`, `power_supply`, `udc` 클래스가 이미 커널에 노출됨
  - 현재 brightness `255 / 365`
  - `event0`~`event8` 존재
  - `/sys/class/drm`에 `card0`, `card0-DSI-1`, `renderD128`, `sde-crtc-*` 존재
- `adbd` 추적 결과:
  - `startadbd`는 실행되지만 `adbd`는 zombie
  - `/dev/usb-ffs/adb`에는 `ep0`만 있고 `ep1/ep2` 미생성
  - host `lsusb -v`도 ACM 2-interface만 표시
- 외부 문서 대조 결과:
  - FunctionFS는 descriptors/strings가 `ep0`에 써져야 `ep#` 파일 생성
  - AOSP init도 `start adbd -> sys.usb.ffs.ready -> ffs.adb symlink -> UDC bind` 순서를 사용
- 현재 권장 방향:
  - Android dynamic binary / ADB 추적은 잠시 보류
  - 다음 probe는 `input + backlight + drm`
  - 장기 통신층 후보는 `USB networking + SSH`
- 상세 보고서:
  - `docs/reports/NATIVE_INIT_SHELL_PROBE_2026-04-23.md`
