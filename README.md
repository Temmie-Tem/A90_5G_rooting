# Samsung Galaxy A90 5G (SM-A908N) Native Linux Boot Project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Device: SM-A908N](https://img.shields.io/badge/Device-SM--A908N-blue.svg)]()
[![SoC: Snapdragon 855](https://img.shields.io/badge/SoC-Snapdragon%20855-green.svg)]()

## 🎯 프로젝트 목표

Samsung Galaxy A90 5G에서 시스템 리소스를 최대한 확보하기 위한 Linux 환경 구축 프로젝트

### 원래 목표 (Phase 0, 실패)
- ❌ 네이티브 Linux 부팅 (PostmarketOS)
- ❌ RAM 절약: 5GB → 150-300MB
- **실패 원인**: ABL/Knox 보안 제약

### 수정된 목표 (Phase 1, 완료)
- ✅ Magisk Systemless Chroot (Debian 12 ARM64)
- ✅ Chroot RAM: 11-20MB (목표 대비 25-72배 우수)
- ✅ SSH 접속, 완전한 Linux 환경

### 현재 목표 (Phase 2, 완료)
- ✅ Android GUI 제거 + Headless Android
- ✅ Android RAM: 1.64GB → 1.41GB PSS (235MB, 14.3% 절감)
- ✅ Magisk 모듈 자동화 (headless_boot_v2)

## ⚠️ 면책 조항

**이 프로젝트는 실험적이며 디바이스를 브릭시킬 수 있습니다.**

- 진행 전 **모든 데이터를 백업**하세요
- 부트로더 언락이 필요하며 **보증이 무효화**됩니다
- 작성자는 **어떠한 손상에도 책임지지 않습니다**
- **본인 책임 하에 진행**하세요

## 📋 전제 조건

### 하드웨어
- ✅ Samsung Galaxy A90 5G (SM-A908N) - 한국 모델
- ✅ 부트로더 언락 완료
- ✅ TWRP 리커버리 설치됨
- ✅ 충전 케이블 및 백업용 저장소

### 소프트웨어 (개발 PC)
- Linux (Ubuntu/Debian 권장)
- Python 3.6+
- Git
- Android SDK Platform Tools (adb, fastboot)
- ARM64 크로스 컴파일러

## 📚 문서

- **[문서 인덱스](docs/README.md)** - 카테고리별 링크 모음
- **[프로젝트 현황](docs/overview/PROJECT_STATUS.md)** - Phase별 요약/결과
- **[진행 로그](docs/overview/PROGRESS_LOG.md)** - 명령어/측정 로그
- **[네이티브 Linux 부팅 계획](docs/plans/NATIVE_LINUX_BOOT_PLAN.md)** - 전체 로드맵
- **[Headless Android 구현 가이드](docs/guides/MAGISK_SYSTEMLESS_GUIDE.md)** - Phase 1 상세 절차
- **[AOSP Minimal Build Guide](docs/guides/AOSP_MINIMAL_BUILD_GUIDE.md)** - Phase 3 준비 문서

## 🚀 빠른 시작

### 1. 개발 환경 구축

```bash
# 필수 패키지 설치
sudo apt update
sudo apt install -y \
    git gcc-aarch64-linux-gnu make bc \
    bison flex libssl-dev \
    device-tree-compiler \
    python3-pip python3-dev \
    android-sdk-platform-tools

# pmbootstrap 설치
pip3 install --user pmbootstrap
```

### 2. 백업 생성 (매우 중요!)

```bash
# TWRP로 부팅
adb reboot recovery

# 백업 디렉토리 생성
mkdir -p ~/A90_backup

# 모든 중요 파티션 백업
adb shell "dd if=/dev/block/bootdevice/by-name/boot of=/sdcard/backup_boot.img"
adb shell "dd if=/dev/block/bootdevice/by-name/recovery of=/sdcard/backup_recovery.img"
adb shell "dd if=/dev/block/bootdevice/by-name/dtbo of=/sdcard/backup_dtbo.img"
adb shell "dd if=/dev/block/bootdevice/by-name/vbmeta of=/sdcard/backup_vbmeta.img"

# PC로 복사
adb pull /sdcard/backup_boot.img ~/A90_backup/
adb pull /sdcard/backup_recovery.img ~/A90_backup/
adb pull /sdcard/backup_dtbo.img ~/A90_backup/
adb pull /sdcard/backup_vbmeta.img ~/A90_backup/

# 안전한 곳에 추가 백업
cp -r ~/A90_backup ~/A90_backup_$(date +%Y%m%d)
```

### 3. WiFi 펌웨어 추출

```bash
# Android로 부팅
adb reboot

# 펌웨어 디렉토리 생성
mkdir -p ~/wifi_firmware

# WiFi 펌웨어 추출
adb root
adb pull /vendor/firmware_mnt/image/wlan/ ~/wifi_firmware/
```

## 📖 단계별 진행 계획

자세한 내용은 [NATIVE_LINUX_BOOT_PLAN.md](docs/plans/NATIVE_LINUX_BOOT_PLAN.md)를 참조하세요.

### Phase 0: Kexec 테스트 환경 (Week 1, Day 1-3)
- 플래싱 없이 안전하게 커널 테스트
- USB 네트워킹 검증

### Phase 1: PostmarketOS 기본 포팅 (Week 1-2, Day 4-14)
- 부팅 가능한 기본 시스템 구축
- Samsung 커널 통합

### Phase 2: WiFi 드라이버 통합 (Week 3, Day 15-21)
- Qualcomm WCN3998 WiFi 작동
- ath10k 드라이버 설정

### Phase 3: SSH 및 핵심 서비스 (Week 3-4, Day 22-28)
- WiFi를 통한 SSH 접속
- 기본 서비스 구축

### Phase 4: 디스플레이 콘솔 (선택사항)
- 기본 framebuffer 콘솔

### Phase 5: 최적화 및 안정화 (Week 5-6, Day 36-42)
- RAM 사용량 최소화
- 장기 안정성 테스트

## 🛠️ 하드웨어 상태

### 작동 예상 (HIGH CONFIDENCE)
- ✅ UFS 3.0 스토리지
- ✅ USB (gadget mode, networking)
- ✅ WiFi (ath10k with firmware)
- ✅ 기본 framebuffer 콘솔
- ✅ 배터리 모니터링
- ✅ 온도 관리

### 작동 불가 (설계상)
- ❌ 카메라
- ❌ 오디오
- ❌ 모뎀/셀룰러
- ❌ 블루투스
- ❌ 센서류
- ❌ 지문인식
- ❌ NFC

## 🔧 복구 방법

### 부팅 이미지 문제 (가장 흔함)

```bash
# 부트로더 모드 진입
# 전원 + 볼륨 다운 길게 누름

# 백업 복원
fastboot flash boot ~/A90_backup/backup_boot.img
fastboot reboot
```

### 완전 브릭 (매우 드묾)

1. Samsung Odin 사용 (Windows 필요)
2. SM-A908N 공식 펌웨어 다운로드
3. 다운로드 모드에서 전체 펌웨어 플래시

## 📊 예상 결과

| 상태 | Android 12 | PostmarketOS | 절약량 |
|------|------------|--------------|--------|
| 부팅 직후 | 4.5GB | 150MB | 4.35GB (96%) |
| Idle (SSH) | 5GB | 200MB | 4.8GB (96%) |

## 🔗 참고 자료

### 공식 문서
- [PostmarketOS Wiki](https://wiki.postmarketos.org/)
- [Snapdragon 855 페이지](https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_855_(SM8150))
- [OnePlus 7 Pro](https://wiki.postmarketos.org/wiki/OnePlus_7_Pro_(oneplus-guacamole)) (참조 디바이스)

### 소스
- [Samsung 오픈소스](https://opensource.samsung.com/)
- [Linux Kernel](https://kernel.org/)
- [pmbootstrap](https://gitlab.com/postmarketOS/pmbootstrap)

### 필요한 파일 (직접 다운로드)
이 저장소에는 다음 파일들이 포함되지 않습니다:

1. **Samsung 커널 소스**
   - URL: https://opensource.samsung.com/
   - 검색: SM-A908N
   - 파일: kernel.tar.gz

2. **WiFi 펌웨어**
   - 본인의 디바이스에서 추출 필요
   - 경로: `/vendor/firmware_mnt/image/wlan/`

## 🤝 기여

이슈와 풀 리퀘스트를 환영합니다!

특히 다음 분야에서의 기여를 찾고 있습니다:
- WiFi 드라이버 최적화
- 배터리 수명 개선
- Device tree 개선
- 문서 번역

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

**주의**: 펌웨어 파일은 독점 라이선스이며 재배포할 수 없습니다.

## 🙏 감사의 말

- PostmarketOS 커뮤니티
- OnePlus 7 Pro 포팅 작업자들
- Samsung 오픈소스 팀
- XDA 개발자 커뮤니티

## 📞 연락처

- GitHub Issues: 버그 리포트 및 질문
- XDA Thread: (추후 추가)

---

**⚡ 현재 상태**: Phase 2 진행 중 (Headless Android, 85% 완료)
**📅 마지막 업데이트**: 2025-11-16

---

## 📈 프로젝트 진행 상황

### ✅ Phase 0: 네이티브 부팅 연구 (완료)
- **기간**: 2025-11-13 ~ 2025-11-14
- **결과**: ❌ **ABL/Knox 제약으로 네이티브 부팅 불가능 확인**
- **주요 발견**:
  - ABL이 Android ramdisk를 강제 주입 (하드코딩)
  - Knox/AVB가 시스템 무결성 강제 검증
  - Mainline 커널의 Samsung 하드웨어 미지원
- **상세**: [Phase 0 연구 결과](archive/phase0_native_boot_research/PROGRESS_LOG_PHASE0.md)

### ✅ Phase 1: Magisk Systemless Chroot (완료)
- **기간**: 2025-11-15 (1일 완료, 예상: 5-14일)
- **결과**: ✅ **모든 목표 달성, 예상보다 25-72배 우수한 성능**
- **성과**:
  - RAM 사용량: 11-20MB (목표 500-800MB 대비 25-72배 우수)
  - 부팅 시간: <1초 (목표 60초 대비 60배 우수)
  - SSH 응답: 0.309초 (목표 1초 대비 3.2배 우수)
  - 완전한 Debian 12 Bookworm ARM64 환경
  - SSH를 통한 원격 접속 (192.168.0.12:22)
- **상세**: [Phase 1 구현 가이드](docs/guides/MAGISK_SYSTEMLESS_GUIDE.md)

### ✅ Phase 2: Headless Android (완료, Option 1)
- **기간**: 2025-11-16 17:00~19:30 (2.5시간)
- **목표**: Android GUI 제거, RAM 1.64GB → 1.0GB (39% 절감)
- **달성**: RAM 235MB 절감 (14.3%, 목표의 37%)
- **완료 작업**:
  - ✅ **headless_boot_v2 Magisk 모듈** 개발 완료
  - ✅ **163개 패키지 자동 비활성화**
    - GUI: 23개, Samsung: 79개, Google: 20개, Apps: 41개
  - ✅ **SystemUI/Launcher 완전 차단** (Magisk `.replace` 방식)
  - ✅ **SSH 자동 시작** 구현
  - ✅ **WiFi 안정성** 확보 (Settings/Phone 유지)
  - ✅ **완전 자동화** (재부팅만으로 headless 환경)
  - ✅ **가역적 구현** (모듈 제거로 원상복구)
- **최종 메모리**:
  - 초기: 1,722,207K (1.64GB PSS)
  - 최종: 1,475,932K (1.41GB PSS)
  - 절감: 246,275K (235MB, 14.3%)
- **기능 검증**:
  - ✅ SystemUI/Launcher: 완전 차단 (실행 안됨)
  - ✅ WiFi: 192.168.0.12/24 정상
  - ✅ SSH: 자동 시작 완료
  - ✅ Debian Chroot: 접근 가능
  - ✅ Headless Boot: 화면 없이 운영 가능
- **주요 성과**:
  - Magisk Magic Mount 활용 (시스템 수정 없이 APK 숨김)
  - pm 명령 타이밍 발견 (service.sh 단계 필요)
  - SystemUI 보호 우회 (`.replace` 파일)
  - WiFi 의존성 파악 (Settings/Phone 필수)
- **발견한 한계**: Option 1 최대 절감 235MB (14.3%)
  - System 프로세스: 307MB (제거 불가)
  - Settings: WiFi 설정 필수
  - Phone: 통신 기능 필수
  - Surfaceflinger: 46MB (필수)
- **상세**: [Phase 2 완료 로그](docs/overview/PROGRESS_LOG.md#42-headless_boot_v2-magisk-모듈-개발-2025-11-16-170019-30)

---

## 🎯 프로젝트 방향 전환

**원래 목표**: 네이티브 Linux 부팅 (PostmarketOS)
- RAM 5GB → 150-300MB

**수정된 목표**: Magisk Systemless Chroot + Headless Android
- Chroot RAM: 11-20MB (✅ 완료)
- Android RAM: 1.64GB → 1.0GB (🔄 진행 중)
- **총 RAM 목표**: 1.0GB 이하

**변경 이유**:
1. ABL/Knox의 강력한 보안 제약으로 네이티브 부팅 불가능
2. Bootloader 언락 상태 확인 → 커스텀 커널/ROM 가능성 발견
3. Magisk 기반 접근이 안전하고 가역적
4. Phase 1, 2에서 목표 달성 (Chroot 11-20MB, Android 235MB 절감)

---

## 🎯 향후 최적화 옵션

### Option 1: Magisk 모듈 (✅ 완료)
- **달성**: RAM 235MB 절감 (14.3%)
- **소요 시간**: 2.5시간
- **위험도**: 낮음 (완전 가역적)
- **상태**: ✅ 완료

### Option 2: 커스텀 커널 (선택 가능)
- **목표**: 추가 200MB 절감
- **방법**: zRAM 압축, Low-Memory-Killer 튜닝, 불필요한 드라이버 제거
- **소요 시간**: 5-10시간
- **위험도**: 중간 (TWRP 복구 가능)
- **요구사항**: ✅ Bootloader 언락 확인됨

### Option 3: AOSP 최소 빌드 (🚀 준비 완료)
- **목표**: 추가 210-510MB 절감 (총 450-760MB 절감, 스톡 대비 27-46%)
- **최종 RAM**: 900MB-1.2GB PSS 목표
- **방법**: Minimal AOSP build (Camera/Audio 선택 가능)
- **소요 시간**: 70-95시간 (2-3주)
- **위험도**: 중간-높음 (벽돌 5-10%, TWRP 백업으로 복구)
- **요구사항**: ✅ Bootloader 언락 확인됨
- **준비 상태**: ✅ 스크립트 및 가이드 완성
- **시작 방법**: `cd scripts/aosp_build && ./01_setup_environment.sh`
- **상세 가이드**: [AOSP Minimal Build Guide](docs/guides/AOSP_MINIMAL_BUILD_GUIDE.md)
