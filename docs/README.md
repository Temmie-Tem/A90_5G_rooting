# Samsung Galaxy A90 5G - Native Linux Boot Project

## 프로젝트 개요

Samsung Galaxy A90 5G (SM-A908N) 디바이스에서 안드로이드를 제거하고 네이티브 Linux를 부팅하여 RAM 사용량을 5GB에서 150-300MB로 줄이는 프로젝트입니다.

**목표**: WiFi 기능을 유지한 SSH 서버로 활용

## 디바이스 정보

- **모델**: SM-A908N (Samsung Galaxy A90 5G)
- **SoC**: Qualcomm Snapdragon 855 (SM8150)
- **RAM**: 5.5GB
- **상태**: 부트로더 언락, TWRP 설치, Magisk 루트

## 프로젝트 문서

- **[NATIVE_LINUX_BOOT_PLAN.md](NATIVE_LINUX_BOOT_PLAN.md)** - 전체 구현 계획 (Phase 0-5)
- **[PROGRESS_LOG.md](PROGRESS_LOG.md)** - 상세 진행 일지 및 명령어 기록

## 현재 진행 상황

**Phase 0: Kexec 테스트 환경 구축** - 🔄 60% 완료

- ✅ 개발 환경 구축 (pmbootstrap 3.6.0, 크로스 컴파일 도구)
- ✅ 중요 파티션 백업 (198MB)
- ✅ WiFi 펌웨어 추출 (4.3MB)
- 🔄 Linux 6.1 LTS 커널 빌드 중
- ⏳ initramfs 생성 대기
- ⏳ kexec 테스트 부팅 대기

## 디렉토리 구조

```
A90_5G_rooting/
├── README.md                    # 본 문서
├── NATIVE_LINUX_BOOT_PLAN.md    # 전체 계획 (40KB)
├── PROGRESS_LOG.md              # 진행 일지
│
├── backups/                     # 파티션 백업 (198MB)
│   ├── backup_boot.img          (64MB)
│   ├── backup_recovery.img      (79MB)
│   ├── backup_dtbo.img          (10MB)
│   └── ... (기타)
│
├── wifi_firmware/               # WiFi 펌웨어 (4.3MB)
│   ├── wlan/qca_cld/
│   └── wlanmdsp.mbn
│
└── kernel_build/                # 커널 빌드 (3.7GB)
    ├── linux/                   # Linux 6.1 소스
    └── build.log
```

## 주요 기술 스택

- **OS**: PostmarketOS (Alpine Linux 기반)
- **커널**: Linux 6.1 LTS (Mainline)
- **WiFi**: Qualcomm WCN3998 (ath10k_snoc 드라이버 예상)
- **부팅**: Kexec 테스트 → Fastboot 플래싱

## 빠른 시작

### 백업 복원 (비상 시)

```bash
# Fastboot 모드로 부팅
adb reboot bootloader

# 부트 파티션 복원
fastboot flash boot backups/backup_boot.img
fastboot reboot
```

### 커널 빌드 상태 확인

```bash
cd kernel_build/linux
tail -f ../build.log
```

## 안전 수칙

⚠️ **중요**: 모든 작업은 백업 완료 후 진행
⚠️ **복구**: TWRP 리커버리 항상 사용 가능
⚠️ **비상**: `backups/` 폴더의 파티션 이미지로 복원 가능

## 타임라인

| Phase | 내용 | 예상 기간 | 상태 |
|-------|------|-----------|------|
| Phase 0 | Kexec 테스트 환경 | 1-2일 | 🔄 60% |
| Phase 1 | PostmarketOS 베이스 포팅 | 3-5일 | ⏳ |
| Phase 2 | WiFi 드라이버 통합 | 5-7일 | ⏳ |
| Phase 3 | SSH 서비스 설정 | 1-2일 | ⏳ |
| Phase 4 | 안정성 테스트 | 2-3일 | ⏳ |
| Phase 5 | 최적화 | 1-2일 | ⏳ |

**총 예상 기간**: 2-3주

## 참고 자료

- [PostmarketOS Wiki](https://wiki.postmarketos.org/)
- [Snapdragon 855 (SM8150)](https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_855_(SM8150))
- [OnePlus 7 Pro 포팅 사례](https://wiki.postmarketos.org/wiki/OnePlus_7_Pro_(oneplus-guacamole))

## 라이선스

개인 프로젝트 - 교육 목적

---

**마지막 업데이트**: 2025년 11월 13일
**연락처**: temmie
**디바이스 ID**: RFCM90CFWXA
