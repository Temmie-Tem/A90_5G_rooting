# Samsung Galaxy A90 5G (SM-A908N) Native Linux Boot Project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Device: SM-A908N](https://img.shields.io/badge/Device-SM--A908N-blue.svg)]()
[![SoC: Snapdragon 855](https://img.shields.io/badge/SoC-Snapdragon%20855-green.svg)]()

## 🎯 프로젝트 목표

Samsung Galaxy A90 5G에서 Android를 제거하고 네이티브 Linux 환경(PostmarketOS)을 구축하여 시스템 리소스를 최대한 확보합니다.

- **RAM 절약**: 5GB → 150-300MB (약 4.5GB 절약, 89% 감소)
- **주요 기능**: WiFi, SSH, 기본 콘솔
- **예상 성공률**: 75%

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

- **[네이티브 Linux 부팅 계획](NATIVE_LINUX_BOOT_PLAN.md)** - 전체 로드맵 (6주 계획)
- **[하드웨어 문서](temp_docs/)** - 디바이스 상세 정보

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

자세한 내용은 [NATIVE_LINUX_BOOT_PLAN.md](NATIVE_LINUX_BOOT_PLAN.md)를 참조하세요.

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

**⚡ 현재 상태**: Phase 0 준비 중
**📅 마지막 업데이트**: 2025-11-13
