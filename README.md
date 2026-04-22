# Samsung Galaxy A90 5G Native Linux Rechallenge Workspace

이 저장소는 `Samsung Galaxy A90 5G (SM-A908N)`에서
이미 확보된 rooted baseline을 기준점으로 삼아
`native Linux 부팅 재도전`을 진행하기 위한 작업 공간입니다.

현재 공식 순서는 다음과 같습니다.

1. rooted baseline 유지
2. 부트체인과 보안 경계 재검증
3. 그 결과를 바탕으로 native Linux 진입 경로 재개방

예전의 `headless Android`, `AOSP minimal build`, 초기 `native Linux boot` 문서는
삭제하지 않고 `archive/legacy`로 옮겨 참고용으로만 보관합니다.

## Current Baseline

- device: `SM-A908N`
- build: `A908NKSU5EWA3`
- Android 12 stock 기반
- patched AP 부팅 성공
- `Magisk 30.7` / `su` 동작 확인
- ADB 가능
- WPA2 Wi-Fi 등록 및 연결 가능
- 현재 `user 0` 패키지 수: `92`

## Current Objective

현재 메인 목표는 `native Linux rechallenge`입니다.

이 목표는 바로 커스텀 이미지를 늘리는 방식으로 접근하지 않고,
먼저 다음 4개 조합을 순서대로 밟습니다.

1. `stock AP + stock recovery`
2. `patched AP + stock recovery`
3. `stock AP + TWRP`
4. `patched AP + TWRP`

위 네 조합을 같은 형식으로 다시 기록해
어느 이미지 경계에서 차단되는지 고정합니다.

그 다음 아래 보안 경계를 분해합니다.

- boot image 수용 여부
- recovery 교체 허용 여부
- `official binaries only` 발생 조건
- KG 표기 변화와 결과 상관관계
- factory reset 유무 영향

패키지 최소화와 debloat는 메인 목표가 아니라 참고용 보조 실험으로만 유지합니다.

## Repository Layout

- [docs/](/home/temmie/dev/A90_5G_rooting/docs/README.md:1)
  현재 문서 인덱스와 rechallenge 로드맵, 진행 로그, 실험 기록 템플릿
- [firmware/](/home/temmie/dev/A90_5G_rooting/firmware/README.md:1)
  stock firmware, patched AP, TWRP 이미지
- [mkbootimg/](/home/temmie/dev/A90_5G_rooting/mkbootimg)
  boot / recovery / vendor_boot 분석과 repack에 쓰는 upstream 도구
- [scripts/](/home/temmie/dev/A90_5G_rooting/scripts/README.md:1)
  기준점 점검과 실험 전후 캡처용 최소 헬퍼 구조

## Active Documents

- [docs/overview/PROJECT_STATUS.md](/home/temmie/dev/A90_5G_rooting/docs/overview/PROJECT_STATUS.md:1)
- [docs/overview/PROGRESS_LOG.md](/home/temmie/dev/A90_5G_rooting/docs/overview/PROGRESS_LOG.md:1)
- [docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md](/home/temmie/dev/A90_5G_rooting/docs/plans/NATIVE_LINUX_RECHALLENGE_PLAN.md:1)
- [docs/plans/REVALIDATION_PLAN.md](/home/temmie/dev/A90_5G_rooting/docs/plans/REVALIDATION_PLAN.md:1)
- [docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md](/home/temmie/dev/A90_5G_rooting/docs/reports/BOOTCHAIN_REVALIDATION_MATRIX_2026-04-23.md:1)
- [docs/reports/MINIMAL_BOOT_STATUS_2026-04-22.md](/home/temmie/dev/A90_5G_rooting/docs/reports/MINIMAL_BOOT_STATUS_2026-04-22.md:1)

## Archive

- [docs/archive/README.md](/home/temmie/dev/A90_5G_rooting/docs/archive/README.md:1)
- [scripts/archive/README.md](/home/temmie/dev/A90_5G_rooting/scripts/archive/README.md:1)

archive에는 다음 과거 트랙이 들어 있습니다.

- native Linux boot planning
- headless Android automation
- Magisk module templates
- custom kernel / AOSP minimal build
- Debian rootfs helper scripts

## Working Rule

- 현재 실험은 항상 기준점 A에서 시작합니다.
- 각 실험 전에는 현재 `boot`, `recovery`, `vbmeta`를 백업합니다.
- 다운로드 모드의 `KG`, `OEM LOCK`, custom binary 문구를 같이 기록합니다.
- 한 번에 하나의 변수만 바꿉니다.
- 부팅, ADB, `su`, Wi-Fi 중 하나라도 깨지면 `stock firmware + patched AP`로 복구합니다.
- 부트체인 실험 중 추가 debloat는 하지 않습니다.
- 새 실험 스크립트는 `scripts/revalidation/` 아래에만 추가합니다.

## Note

이 저장소에는 실제 플래시 대상 바이너리와 Samsung 전용 이미지가 포함될 수 있습니다.
실험 전에는 항상 현재 boot / recovery / vbmeta 상태를 따로 백업해 두는 것을 전제로 합니다.
