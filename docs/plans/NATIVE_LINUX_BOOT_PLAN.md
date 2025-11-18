# Samsung Galaxy A90 5G (SM-A908N) 네이티브 Linux 부팅 프로젝트

## 프로젝트 개요

### 목표
Samsung Galaxy A90 5G에서 안드로이드를 제거하고 네이티브 Linux 환경을 구축하여 시스템 리소스를 최대한 확보

### 현재 상태
- **디바이스**: SM-A908N (한국 KT 모델)
- **SoC**: Qualcomm Snapdragon 855 (SM8150)
- **RAM**: 5.5GB (현재 5GB 사용 중)
- **저장공간**: 110GB /data 파티션 중 102GB 사용 가능
- **부트로더**: 언락 완료
- **리커버리**: TWRP 설치됨
- **루트**: Magisk 활성화
- **현재 OS**: Android 12

### 사용자 요구사항
- ✅ WiFi 필수 (핵심 요구사항)
- ✅ SSH 원격 접속 위주 사용
- ✅ 최소한의 디스플레이 출력 (부팅/디버깅용)
- ❌ 모뎀/셀룰러 불필요
- 🔌 충전하면서 사용 (서버처럼)
- ⏱️ 몇 주 투자 가능
- 🛡️ TWRP 복구 가능

### 예상 결과
- **RAM 사용량**: 5GB → 150-300MB (약 4.5GB 절약, 89% 감소)
- **성공 확률**: 75%
- **예상 기간**: 4-6주

---

## 하드웨어 분석

### 주요 컴포넌트

#### WiFi 칩셋
- **모델**: Qualcomm WCN3998
- **드라이버**: ath10k_snoc (SNOC = System-on-Chip, PCIe 아님)
- **펌웨어 위치**: `/vendor/firmware_mnt/image/wlan/`
- **지원 상태**: 메인라인 지원 양호
- **중요도**: 🔴 필수

#### 디스플레이
- **패널**: S6E3FC2_AMS670TA01
- **해상도**: 1080x2400 FHD+
- **인터페이스**: DSI (Display Serial Interface)
- **드라이버**: 삼성 전용 (메인라인 미지원)
- **대안**: simplefb 또는 fbcon으로 기본 콘솔
- **중요도**: 🟡 선택사항

#### 스토리지
- **타입**: UFS 3.0
- **컨트롤러**: 1d84000.ufshc
- **드라이버**: ufshcd (메인라인 지원 완벽)
- **중요도**: 🔴 필수

#### USB
- **컨트롤러**: dwc3-qcom
- **지원**: USB gadget mode 포함
- **용도**: ADB 대체, USB 네트워킹
- **중요도**: 🔴 필수

### 작동 예상 기능

#### 작동 가능 (HIGH CONFIDENCE)
- ✅ UFS 스토리지
- ✅ USB (gadget mode, networking)
- ✅ WiFi (ath10k with firmware)
- ✅ 기본 framebuffer 콘솔
- ✅ 배터리 모니터링
- ✅ 온도 관리 (thermal)

#### 작동 불가 (설계상)
- ❌ 카메라 (ISP 드라이버 없음)
- ❌ 오디오 (WCD9340 코덱 미지원)
- ❌ 모뎀/셀룰러 (불필요)
- ❌ 블루투스 (불필요)
- ❌ 센서류 (가속도, 자이로 등)
- ❌ 지문인식
- ❌ NFC

---

## 구현 전략

### 선택한 접근 방식: PostmarketOS 포팅

#### 선택 이유
1. **Snapdragon 855 참조 구현 존재**: OnePlus 7 Pro 포트 활용 가능
2. **패키지 관리**: Alpine Linux APK로 WiFi 펌웨어 등 쉽게 관리
3. **커뮤니티 지원**: PostmarketOS 커뮤니티 문서와 도구 활용
4. **USB 네트워킹 내장**: WiFi 실패 시 fallback 옵션

#### 대안들과 비교

| 방법 | RAM 절약 | 난이도 | 기간 | 추천도 |
|------|----------|--------|------|--------|
| **PostmarketOS 포팅** | 4.5GB | 중상 | 4-6주 | ⭐⭐⭐⭐⭐ |
| Chroot Linux | 1-2GB | 하 | 2-4일 | ⭐⭐ (안드로이드 여전히 실행) |
| Kexec Boot | 4.5GB | 상 | 동일 | ⭐⭐⭐ (테스트용으로만) |
| 완전 커스텀 빌드 | 4.5GB | 최상 | 3-6개월 | ⭐ (비현실적) |

---

## 단계별 실행 계획

## Phase 0: 네이티브 부팅 실현 가능성 연구 (완료)

### 결론: **네이티브 부팅 불가능**

**최종 판단 날짜**: 2025-11-14

### 실행된 조사 및 테스트

#### 1. 커널 부팅 시도 (5회)
- ✅ Mainline kernel 6.1 + External ramdisk
- ✅ Stock kernel 4.14 + External ramdisk
- ✅ Samsung kernel 4.14 + External ramdisk + rdinit=/bin/sh
- ✅ Samsung kernel 4.14 + Integrated ramdisk + rdinit=/bin/sh
- ✅ Samsung kernel 4.14 + Integrated ramdisk (no rdinit)

**결과**: 모든 시도에서 ABL이 강제로 Android ramdisk를 주입하여 `/system/bin/init` 실행

#### 2. Android Init 하이재킹 시도
- ✅ `/system/etc/init/early-hijack.rc` 생성
- ✅ `/system/bin/custom_init.sh` 스크립트 배포
- ✅ 권한 및 SELinux 컨텍스트 설정

**결과**: AVB/dm-verity가 재부팅 시 /system 파티션 수정 자동 복원

#### 3. 웹 리서치 및 대안 조사
- ✅ Magisk overlay.d 시스템 (systemless 수정)
- ✅ PostmarketOS/Halium 방식
- ✅ Samsung CVE 취약점 조사
- ✅ Snapdragon 855 mainline 지원 현황

### 발견된 기술적 장벽

#### 1. **ABL (Android Bootloader) 하드코딩**
```
증거: docs/overview/PROGRESS_LOG.md:1758,2247
- 커널 파라미터로 initramfs 지정 무시
- CONFIG_INITRAMFS_SOURCE 통합 방식 무시
- rdinit= 파라미터 무시
- ABL이 알 수 없는 소스에서 Android ramdisk 강제 주입
```

**우회 불가능 이유**: ABL은 서명된 바이너리이며 수정 시 다운로드 모드 차단

#### 2. **Knox/AVB 무결성 검증**
```
증거: /system 파티션 수정 시 자동 복원
- dm-verity가 부팅 시 해시 검증
- 불일치 시 백업에서 자동 복원
- vbmeta 파티션 쓰기 보호로 비활성화 불가
```

#### 3. **PBL (Primary Boot Loader) 제약**
```
증거: 전문가 의견
- Snapdragon 855 PBL은 ROM 코드로 고정
- eMMC/UFS 내부만 검색
- SD 카드 부팅 경로 없음
```

#### 4. **Mainline 커널 지원 부족**
```
증거: sm8150-mainline 프로젝트
- 디스플레이 드라이버 부재
- WiFi 펌웨어 로딩 불안정
- Samsung 특화 하드웨어 미지원
```

### 시도 가능한 대안들의 한계

#### Option A: Magisk overlay.d
- ✅ 장점: AVB 우회, systemless 수정
- ❌ 단점: **Android 커널 + init 유지 필요**
- 예상 RAM: ~600-800MB (목표 150-300MB 미달성)

#### Option B: Halium/Ubuntu Touch
- ✅ 장점: Linux 사용자 공간
- ❌ 단점: **Android HAL + 프레임워크 유지**
- 예상 RAM: ~1.5GB+ (목표 대비 5배 초과)

#### Option C: Termux + proot
- ✅ 장점: 가장 안전, 검증됨
- ❌ 단점: **완전한 Android 위에서 실행**
- 예상 RAM: ~600-800MB + Android overhead

### 근본적 결론

**"완전한 네이티브 Linux 부팅"은 Samsung Galaxy A90 5G (SM-A908N)에서 불가능**

이유:
1. ABL이 커스텀 ramdisk 실행 경로 차단 (구조적 한계)
2. Android 커널/init 없이는 부팅 체인 완성 불가
3. 완전 우회 시도는 Knox 제약으로 실패
4. Verified Boot 비활성화 불가능

### Phase 0 완료 상태: ✅ 연구 완료

**다음 단계**: Phase 1 대안 계획 수립 (Android 기반 슬림화)

### 중요성
- **브릭 위험 제로**: 재부팅만 하면 안드로이드 복귀
- **빠른 반복**: 플래시 없이 커널 설정 테스트
- **검증**: 기본 드라이버 작동 확인

### 작업 내용

#### 1. 개발 환경 구축
```bash
# 개발 PC에서 (Ubuntu/Debian)
sudo apt update
sudo apt install -y \
    git gcc-aarch64-linux-gnu make bc \
    bison flex libssl-dev \
    device-tree-compiler \
    python3-pip python3-dev \
    abootimg cpio \
    android-sdk-platform-tools \
    fastboot
```

#### 2. 테스트 커널 빌드
```bash
# 메인라인 커널 클론
git clone https://github.com/torvalds/linux.git linux-test
cd linux-test
git checkout v6.1  # LTS 버전

# ARM64 크로스 컴파일 설정
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

# 기본 설정으로 시작
make defconfig

# 필수 드라이버 활성화
make menuconfig
# 설정:
# - CONFIG_UFS_QCOM=y (스토리지)
# - CONFIG_USB_DWC3_QCOM=y (USB)
# - CONFIG_USB_GADGET=y (USB gadget)
# - CONFIG_USB_ETH=y (USB 네트워킹)
# - CONFIG_SERIAL_MSM=y (시리얼 콘솔)
# - CONFIG_SERIAL_MSM_CONSOLE=y

# 컴파일
make -j$(nproc)
```

#### 3. 최소 initramfs 생성
```bash
mkdir -p ~/initramfs
cd ~/initramfs

# 기본 init 스크립트
cat > init << 'EOF'
#!/bin/sh
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev

# USB 네트워킹 시작
echo "Starting USB Ethernet..."
modprobe g_ether
sleep 2
ifconfig usb0 10.15.19.82 netmask 255.255.255.0 up

echo "Boot successful! Starting shell..."
exec /bin/sh
EOF

chmod +x init

# Busybox 다운로드
wget https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox
chmod +x busybox
mkdir -p bin
ln -s /busybox bin/sh

# CPIO 아카이브 생성
find . | cpio -o -H newc | gzip > ~/initramfs.cpio.gz
```

#### 4. Kexec로 테스트 부팅
```bash
# 커널과 initramfs를 디바이스로 전송
adb push ~/linux-test/arch/arm64/boot/Image /sdcard/test_kernel
adb push ~/initramfs.cpio.gz /sdcard/

# 디바이스에 접속
adb shell
su

# kexec로 로드 및 실행
kexec --load /sdcard/test_kernel \
    --initrd=/sdcard/initramfs.cpio.gz \
    --command-line="console=ttyMSM0,115200 root=/dev/ram0"

# 실행 (디바이스가 새 커널로 재부팅됨)
kexec -e
```

#### 5. USB 네트워킹 테스트
```bash
# PC에서 (디바이스가 kexec로 부팅된 후)
# USB 이더넷 인터페이스가 나타나야 함
ip link show  # usb0 또는 ethX 확인

# IP 설정
sudo ip addr add 10.15.19.1/24 dev usb0
sudo ip link set usb0 up

# 디바이스로 텔넷 연결 (또는 SSH if configured)
telnet 10.15.19.82
```

### 성공 기준
- ✅ 디바이스가 새 커널로 부팅
- ✅ USB 콘솔 또는 USB 네트워킹 작동
- ✅ 셸 프롬프트 접근 가능
- ✅ 기본 명령어 실행 (ls, cat, mount 등)

### 롤백 방법
```bash
# 단순히 재부팅
adb reboot
# 또는 디바이스에서 전원 버튼 길게 눌러 재시작
```

### 예상 소요 시간
- 1-3일 (처음 하는 경우)
- 대부분의 시간은 커널 설정 조정과 드라이버 문제 해결

### 예상 문제점
1. **디스플레이 작동 안 함**: 예상됨, 시리얼/USB 콘솔 사용
2. **스토리지 마운트 실패**: DTS(Device Tree) 문제, Samsung 소스 필요
3. **USB가 안 뜰 때**: 시리얼 콘솔 케이블 필요하거나 삼성 커널 소스 사용

---

## Phase 1: PostmarketOS 기본 포팅 (Week 1-2, Day 4-14)

### 목표
부팅 가능한 PostmarketOS 환경 구축 (WiFi 제외)

### 작업 내용

#### 1. pmbootstrap 설치 및 초기화
```bash
# pmbootstrap 설치
pip3 install --user pmbootstrap

# 초기화
pmbootstrap init

# 프롬프트 응답:
# - Work path: 기본값 (~/.local/var/pmbootstrap)
# - Channel: edge (최신)
# - Vendor: samsung
# - Device codename: r3q (새로 생성)
# - Username: user
# - UI: none (CLI only)
# - Extra packages: openssh
```

#### 2. 디바이스 패키지 생성
```bash
# pmaports 디렉토리로 이동
cd ~/.local/var/pmbootstrap/cache_git/pmaports

# 디바이스 패키지 디렉토리 생성
mkdir -p device/testing/device-samsung-r3q

# APKBUILD 파일 생성
cat > device/testing/device-samsung-r3q/APKBUILD << 'EOF'
# Maintainer: Your Name <email@example.com>
pkgname=device-samsung-r3q
pkgdesc="Samsung Galaxy A90 5G"
pkgver=1
pkgrel=0
url="https://github.com/postmarketOS"
license="MIT"
arch="aarch64"
options="!check !archcheck"
depends="
    postmarketos-base
    linux-samsung-r3q
    mkbootimg
"
makedepends="devicepkg-dev"
source="deviceinfo"

package() {
    devicepkg_package $startdir $pkgname
}

sha512sums="SKIP"
EOF

# deviceinfo 파일 생성
cat > device/testing/device-samsung-r3q/deviceinfo << 'EOF'
# Reference: <https://postmarketos.org/deviceinfo>
# Please use double quotes only. You can source this file in shell scripts.

deviceinfo_format_version="0"
deviceinfo_name="Samsung Galaxy A90 5G"
deviceinfo_manufacturer="Samsung"
deviceinfo_codename="samsung-r3q"
deviceinfo_year="2019"
deviceinfo_dtb=""
deviceinfo_modules_initfs=""
deviceinfo_arch="aarch64"

# Device related
deviceinfo_chassis="handset"
deviceinfo_keyboard="false"
deviceinfo_external_storage="true"
deviceinfo_screen_width="1080"
deviceinfo_screen_height="2400"

# Bootloader related
deviceinfo_flash_method="fastboot"
deviceinfo_kernel_cmdline="console=ttyMSM0,115200n8 androidboot.console=ttyMSM0 androidboot.hardware=qcom"
deviceinfo_generate_bootimg="true"
deviceinfo_bootimg_qcdt="false"
deviceinfo_bootimg_mtk_mkimage="false"
deviceinfo_bootimg_dtb_second="false"
deviceinfo_flash_offset_base="0x00000000"
deviceinfo_flash_offset_kernel="0x00008000"
deviceinfo_flash_offset_ramdisk="0x01000000"
deviceinfo_flash_offset_second="0x00f00000"
deviceinfo_flash_offset_tags="0x00000100"
deviceinfo_flash_pagesize="4096"
deviceinfo_flash_sparse="true"
EOF
```

#### 3. Samsung 커널 소스 다운로드 및 설정
```bash
# 홈 디렉토리에 작업 공간 생성
mkdir -p ~/samsung_kernel
cd ~/samsung_kernel

# Samsung 오픈소스에서 커널 다운로드
# URL: https://opensource.samsung.com/
# 검색: SM-A908N
# 다운로드: kernel.tar.gz

# 압축 해제
tar -xzf kernel.tar.gz
cd kernel

# PostmarketOS용 커널 패키지 생성
cd ~/.local/var/pmbootstrap/cache_git/pmaports
mkdir -p device/testing/linux-samsung-r3q

cat > device/testing/linux-samsung-r3q/APKBUILD << 'EOF'
# Maintainer: Your Name <email@example.com>
pkgname=linux-samsung-r3q
pkgver=4.14.190
pkgrel=0
pkgdesc="Samsung Galaxy A90 5G kernel"
arch="aarch64"
_flavor="samsung-r3q"
url="https://opensource.samsung.com"
license="GPL-2.0-only"
options="!strip !check !tracedeps pmb:cross-native"
makedepends="
    bash
    bc
    bison
    devicepkg-dev
    flex
    openssl-dev
    perl
"

# Source
_repository="samsung_kernel"
_commit="COMMIT_HASH"
_config="config-$_flavor.$arch"
source="
    $pkgname-$_commit.tar.gz::KERNEL_SOURCE_PATH
    $_config
"

builddir="$srcdir/kernel"

prepare() {
    default_prepare
    . downstreamkernel_prepare
}

build() {
    unset LDFLAGS
    make O="$_outdir" ARCH="$_carch" CC="${CC:-gcc}" \
        KBUILD_BUILD_VERSION="$((pkgrel + 1))-postmarketOS"
}

package() {
    downstreamkernel_package "$builddir" "$pkgdir" "$_flavor" "$_outdir"
}

sha512sums="SKIP"
EOF

# 커널 config 복사
cp ~/samsung_kernel/kernel/arch/arm64/configs/r3q_defconfig \
   device/testing/linux-samsung-r3q/config-samsung-r3q.aarch64
```

#### 4. 빌드 및 설치
```bash
# 커널 빌드
pmbootstrap build linux-samsung-r3q

# 디바이스 패키지 빌드
pmbootstrap build device-samsung-r3q

# PostmarketOS 설치 (rootfs 생성)
pmbootstrap install

# 부트 이미지 내보내기
pmbootstrap export
```

#### 5. 첫 플래싱 및 부팅
```bash
# 백업 먼저! (매우 중요)
adb reboot recovery  # TWRP로 부팅

# TWRP에서:
adb shell
dd if=/dev/block/bootdevice/by-name/boot of=/sdcard/backup_boot.img
dd if=/dev/block/bootdevice/by-name/recovery of=/sdcard/backup_recovery.img
exit

adb pull /sdcard/backup_boot.img ~/A90_backup/
adb pull /sdcard/backup_recovery.img ~/A90_backup/

# 부트로더로 재부팅
adb reboot bootloader

# PostmarketOS 부팅 이미지 플래시
fastboot flash boot /tmp/postmarketOS-export/boot.img

# 부팅
fastboot reboot
```

#### 6. USB 콘솔로 접속
```bash
# PC에서 USB 네트워킹 활성화
# 디바이스가 부팅되면 USB 이더넷 인터페이스가 나타남

# 네트워크 설정 (Ubuntu/Debian PC)
sudo ip addr add 172.16.42.1/24 dev usb0
sudo ip link set usb0 up

# 텔넷으로 접속 (초기 부팅 시)
telnet 172.16.42.2

# 또는 SSH (설정된 경우)
ssh user@172.16.42.2
```

### 성공 기준
- ✅ PostmarketOS가 부팅됨
- ✅ USB를 통한 콘솔 접근 가능
- ✅ 로그인 성공
- ✅ 기본 시스템 명령어 작동 (df, free, ps 등)
- ✅ APK 패키지 매니저 작동

### 롤백 방법
```bash
# 부트로더로 부팅
# 전원 + 볼륨 다운 길게 누르기

# 백업 복원
fastboot flash boot ~/A90_backup/backup_boot.img
fastboot reboot
```

### 예상 RAM 사용량
- **150-200MB** (WiFi 제외, 기본 시스템만)

### 예상 소요 시간
- 7-10일
- 커널 컴파일 에러 수정에 시간 소요 예상

### 예상 문제점
1. **커널 컴파일 에러**: GCC 버전 문제, 패치 필요
2. **부팅 루프**: 커널 패닉, initramfs 문제
3. **파티션 마운트 실패**: fstab 또는 device tree 문제

---

## Phase 2: WiFi 드라이버 통합 (Week 3, Day 15-21)

### 목표
Qualcomm WCN3998 WiFi 작동시키기 (가장 중요!)

### WiFi 하드웨어 정보
- **칩셋**: Qualcomm WCN3998
- **드라이버**: ath10k_snoc (System-on-Chip 버전)
- **펌웨어 경로**: `/vendor/firmware_mnt/image/wlan/`

### 작업 내용

#### 1. 안드로이드에서 WiFi 펌웨어 추출
```bash
# 안드로이드로 부팅
fastboot flash boot ~/A90_backup/backup_boot.img
fastboot reboot

# 펌웨어 추출
adb root
adb shell

# WiFi 펌웨어 위치 확인
ls -la /vendor/firmware_mnt/image/wlan/
ls -la /vendor/firmware/wlan/

# 필요한 파일들:
# - qwlan30.bin (WiFi firmware)
# - bdwlan30.bin (board data)
# - Data.msc (calibration data)

exit

# PC로 복사
mkdir -p ~/wifi_firmware
adb pull /vendor/firmware_mnt/image/wlan/ ~/wifi_firmware/
adb pull /vendor/firmware/wlan/ ~/wifi_firmware/vendor/
```

#### 2. 커널에 ath10k 드라이버 추가
```bash
# 커널 config 수정
cd ~/.local/var/pmbootstrap/cache_git/pmaports
nano device/testing/linux-samsung-r3q/config-samsung-r3q.aarch64

# 다음 옵션 추가/활성화:
CONFIG_ATH10K=m
CONFIG_ATH10K_SNOC=m
CONFIG_ATH10K_DEBUG=y
CONFIG_ATH10K_DEBUGFS=y
CONFIG_ATH10K_TRACING=y
CONFIG_CFG80211=y
CONFIG_MAC80211=y

# 커널 재빌드
pmbootstrap build linux-samsung-r3q --force
pmbootstrap install
pmbootstrap export
```

#### 3. WiFi 펌웨어 패키지 생성
```bash
# 펌웨어 패키지 디렉토리 생성
cd ~/.local/var/pmbootstrap/cache_git/pmaports
mkdir -p device/testing/firmware-samsung-r3q

# 펌웨어 파일 복사
cp ~/wifi_firmware/qwlan30.bin device/testing/firmware-samsung-r3q/
cp ~/wifi_firmware/bdwlan30.bin device/testing/firmware-samsung-r3q/
cp ~/wifi_firmware/Data.msc device/testing/firmware-samsung-r3q/

# APKBUILD 생성
cat > device/testing/firmware-samsung-r3q/APKBUILD << 'EOF'
pkgname=firmware-samsung-r3q
pkgdesc="Firmware for Samsung Galaxy A90 5G"
pkgver=1
pkgrel=0
arch="aarch64"
license="proprietary"
options="!check !strip !archcheck !tracedeps"
source="
    qwlan30.bin
    bdwlan30.bin
    Data.msc
"

package() {
    # ath10k 펌웨어 경로
    install -Dm644 "$srcdir"/qwlan30.bin \
        "$pkgdir"/lib/firmware/ath10k/WCN3990/hw1.0/firmware-5.bin

    install -Dm644 "$srcdir"/bdwlan30.bin \
        "$pkgdir"/lib/firmware/ath10k/WCN3990/hw1.0/board.bin

    install -Dm644 "$srcdir"/Data.msc \
        "$pkgdir"/lib/firmware/ath10k/WCN3990/hw1.0/board-2.bin
}

sha512sums="SKIP"
EOF

# 빌드
pmbootstrap build firmware-samsung-r3q
```

#### 4. 디바이스 패키지에 펌웨어 의존성 추가
```bash
# device-samsung-r3q APKBUILD 수정
nano device/testing/device-samsung-r3q/APKBUILD

# depends 섹션에 추가:
depends="
    postmarketos-base
    linux-samsung-r3q
    mkbootimg
    firmware-samsung-r3q
    wireless-tools
    wpa_supplicant
"

# 재빌드 및 설치
pmbootstrap build device-samsung-r3q
pmbootstrap install
pmbootstrap export

# 새 부트 이미지 플래시
adb reboot bootloader
fastboot flash boot /tmp/postmarketOS-export/boot.img
fastboot reboot
```

#### 5. WiFi 테스트
```bash
# USB 콘솔로 접속
ssh user@172.16.42.2

# 루트로 전환
sudo su

# WiFi 모듈 로드
modprobe ath10k_snoc

# 드라이버 로그 확인
dmesg | grep ath10k
# 정상적으로 로드되면:
# ath10k_snoc 18800000.wifi: firmware 5.bin loaded
# ath10k_snoc 18800000.wifi: board.bin loaded
# wlan0 created

# 인터페이스 확인
ip link show wlan0

# WiFi 활성화
ip link set wlan0 up

# 주변 네트워크 스캔
iw dev wlan0 scan | grep SSID

# WPA 설정 파일 생성
wpa_passphrase "YourSSID" "YourPassword" > /etc/wpa_supplicant/wpa_supplicant.conf

# WiFi 연결
wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf

# DHCP로 IP 받기
udhcpc -i wlan0

# 연결 확인
ip addr show wlan0
ping -c 4 8.8.8.8
ping -c 4 google.com
```

#### 6. 부팅 시 자동 WiFi 연결 설정
```bash
# OpenRC 네트워크 설정
cat > /etc/network/interfaces << 'EOF'
auto lo
iface lo inet loopback

auto wlan0
iface wlan0 inet dhcp
    pre-up modprobe ath10k_snoc
    pre-up sleep 2
    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
EOF

# 네트워킹 서비스 활성화
rc-update add networking boot

# wpa_supplicant 서비스 활성화
rc-update add wpa_supplicant default

# 재부팅 테스트
reboot
```

### 성공 기준
- ✅ `wlan0` 인터페이스가 나타남
- ✅ 네트워크 스캔 성공
- ✅ WiFi 연결 성공
- ✅ 인터넷 접속 가능 (ping 성공)
- ✅ 부팅 시 자동 연결

### 트러블슈팅

#### 문제 1: 펌웨어 로드 실패
```bash
# dmesg 확인
dmesg | grep -i firmware
# "firmware not found" 에러가 나오면

# 펌웨어 경로 확인
ls -la /lib/firmware/ath10k/WCN3990/hw1.0/

# 파일명 확인 (대소문자, 버전)
# 때로는 다른 경로 필요:
# /lib/firmware/ath10k/WCN3990/hw1.0/
# 또는
# /lib/firmware/ath10k/QCA6390/hw2.0/
```

#### 문제 2: 모듈이 로드되지 않음
```bash
# 커널 로그 확인
dmesg | grep ath10k

# 모듈이 빌드되었는지 확인
find /lib/modules -name "ath10k*"

# 수동 로드 시도
modprobe -v ath10k_core
modprobe -v ath10k_snoc

# 의존성 확인
modinfo ath10k_snoc
```

#### 문제 3: 연결은 되지만 인터넷 안 됨
```bash
# 라우팅 테이블 확인
ip route show

# 기본 게이트웨이 수동 추가
ip route add default via 192.168.1.1 dev wlan0

# DNS 확인
cat /etc/resolv.conf

# DNS 수동 설정
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf
```

### 예상 소요 시간
- 5-7일
- 대부분 펌웨어 경로와 파일명 매칭에 시간 소요

---

## Phase 3: SSH 및 핵심 서비스 (Week 3-4, Day 22-28)

### 목표
WiFi를 통한 안정적인 SSH 접속 및 기본 서비스 구축

### 작업 내용

#### 1. OpenSSH 서버 설치 및 설정
```bash
# SSH로 디바이스 접속 (WiFi 또는 USB)
ssh user@<device-ip>

# 루트 권한 획득
sudo su

# OpenSSH 서버 설치 (아직 안 됐다면)
apk add openssh openssh-server

# SSH 설정 파일 편집
nano /etc/ssh/sshd_config

# 권장 설정:
Port 22
PermitRootLogin no  # 보안상 권장
PasswordAuthentication yes
PubkeyAuthentication yes
PermitEmptyPasswords no
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/ssh/sftp-server

# SSH 서비스 시작 및 자동 시작 설정
rc-service sshd start
rc-update add sshd default

# 방화벽 설정 (iptables)
apk add iptables

cat > /etc/iptables/rules-save << 'EOF'
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]

# Loopback
-A INPUT -i lo -j ACCEPT

# Established connections
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

# SSH
-A INPUT -p tcp --dport 22 -j ACCEPT

# ICMP (ping)
-A INPUT -p icmp -j ACCEPT

COMMIT
EOF

# 방화벽 시작
rc-service iptables start
rc-update add iptables default
```

#### 2. 공개키 인증 설정
```bash
# PC에서 SSH 키 생성 (없는 경우)
ssh-keygen -t ed25519 -C "a90_linux"

# 공개키를 디바이스로 복사
ssh-copy-id user@<device-ip>

# 테스트
ssh user@<device-ip>
# 비밀번호 없이 로그인되어야 함

# 비밀번호 인증 비활성화 (선택사항, 보안 강화)
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo rc-service sshd restart
```

#### 3. 필수 CLI 도구 설치
```bash
# 기본 도구
apk add \
    bash bash-completion \
    vim nano \
    htop iotop \
    wget curl \
    git \
    python3 py3-pip \
    tmux screen \
    rsync \
    net-tools \
    iftop nethogs \
    bind-tools \
    tzdata

# 타임존 설정
setup-timezone -z Asia/Seoul

# 개발 도구 (필요시)
apk add \
    gcc g++ make cmake \
    nodejs npm \
    go \
    rust cargo
```

#### 4. 시스템 서비스 최적화
```bash
# 실행 중인 서비스 확인
rc-status

# 불필요한 서비스 비활성화
rc-update del chronyd  # NTP (시간 동기화 불필요하면)

# 로그 설정 최소화 (RAM 절약)
nano /etc/syslog.conf
# 모든 로그를 에러 레벨로만 제한

# busybox syslog를 가벼운 설정으로
rc-update add syslog boot
```

#### 5. ZRAM 설정 (선택적 스왑)
```bash
# ZRAM 설치
apk add zram-init

# 설정
echo "SIZE=512M" > /etc/conf.d/zram-init
echo "COMP_ALG=lz4" >> /etc/conf.d/zram-init

# 활성화
rc-update add zram-init boot
rc-service zram-init start

# 확인
free -m
# Swap 행에 512MB 정도 나타나야 함
```

#### 6. 시스템 모니터링 스크립트
```bash
# 간단한 상태 확인 스크립트
cat > /usr/local/bin/status << 'EOF'
#!/bin/sh
echo "=== System Status ==="
echo "Uptime:"
uptime
echo ""
echo "Memory:"
free -h
echo ""
echo "Disk:"
df -h /
echo ""
echo "WiFi:"
iw dev wlan0 link
echo ""
echo "IP Address:"
ip -4 addr show wlan0 | grep inet
echo ""
echo "Top Processes:"
ps aux --sort=-rss | head -10
EOF

chmod +x /usr/local/bin/status

# 사용법
status
```

#### 7. 자동 재연결 스크립트
```bash
# WiFi 연결 감시 및 자동 재연결
cat > /usr/local/bin/wifi-watchdog << 'EOF'
#!/bin/sh
while true; do
    if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo "$(date): Connection lost, reconnecting..."
        ifconfig wlan0 down
        sleep 2
        ifconfig wlan0 up
        wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
        sleep 5
        udhcpc -i wlan0
    fi
    sleep 30
done
EOF

chmod +x /usr/local/bin/wifi-watchdog

# Cron으로 실행 (선택사항)
# 또는 OpenRC 서비스로 만들기
```

### 성공 기준
- ✅ WiFi를 통해 SSH 접속 가능
- ✅ USB 케이블 없이 작동
- ✅ 부팅 후 60초 이내 SSH 가능
- ✅ 재부팅 후에도 자동 연결
- ✅ 기본 개발 환경 사용 가능

### 예상 RAM 사용량
- **150-250MB** (idle 상태)

### 예상 소요 시간
- 4-6일

---

## Phase 4: 디스플레이 콘솔 (Week 4, Day 29-35) - 선택사항

### 목표
기본 프레임버퍼 콘솔 출력 (비상/디버깅용)

### 우선순위
🟡 **낮음** - SSH가 주 접속 방법이므로 나중에 추가 가능

### 작업 내용

#### 1. Framebuffer 콘솔 활성화
```bash
# 커널 config 수정
nano device/testing/linux-samsung-r3q/config-samsung-r3q.aarch64

# 추가/활성화:
CONFIG_FB=y
CONFIG_FB_SIMPLE=y
CONFIG_FRAMEBUFFER_CONSOLE=y
CONFIG_FRAMEBUFFER_CONSOLE_DETECT_PRIMARY=y
CONFIG_LOGO=y
CONFIG_LOGO_LINUX_CLUT224=y
CONFIG_VT=y
CONFIG_VT_CONSOLE=y

# 커널 cmdline에 추가 (deviceinfo)
deviceinfo_kernel_cmdline="console=tty0 console=ttyMSM0,115200n8 ..."

# 재빌드
pmbootstrap build linux-samsung-r3q --force
pmbootstrap install
pmbootstrap export
```

#### 2. 폰트 및 터미널 도구
```bash
# 디바이스에서
apk add \
    kbd \
    terminus-font \
    fbset

# 해상도 확인
fbset -i

# 폰트 크기 조정 (1080x2400에서는 작을 수 있음)
setfont /usr/share/consolefonts/ter-132n.psf.gz
```

#### 3. 간단한 부팅 스플래시 (선택)
```bash
# fbsplash 또는 plymouth
apk add plymouth plymouth-themes

# 설정
plymouth-set-default-theme bgrt
```

### 대안: 디스플레이 건너뛰기
SSH 접속이 주 사용 방식이므로, 디스플레이 작업을 완전히 건너뛰고 나중에 필요할 때 추가하는 것을 권장합니다.

### 예상 소요 시간
- 3-7일 (또는 건너뛰기)

---

## Phase 5: 최적화 및 안정화 (Week 5-6, Day 36-42)

### 목표
RAM 사용량 최소화 및 시스템 안정성 확보

### 작업 내용

#### 1. RAM 사용량 측정 및 분석
```bash
# 현재 메모리 사용량
free -m

# 프로세스별 메모리 사용
ps aux --sort=-rss | head -20

# 실행 중인 서비스
rc-status -a

# 커널 메모리 사용
cat /proc/meminfo
```

#### 2. 불필요한 패키지 제거
```bash
# 설치된 패키지 목록
apk list --installed

# 제거할 수 있는 것들:
apk del \
    modemmanager \
    ofono \
    bluez \
    pulseaudio \
    mesa-dri-gallium  # GPU 가속 불필요하면

# 정리
apk cache clean
```

#### 3. 커널 최적화
```bash
# 커널 config에서 불필요한 드라이버 비활성화
nano device/testing/linux-samsung-r3q/config-samsung-r3q.aarch64

# 비활성화할 것들:
# CONFIG_SOUND=n (오디오 불필요)
# CONFIG_SND=n
# CONFIG_MEDIA_SUPPORT=n (카메라)
# CONFIG_VIDEO_DEV=n
# CONFIG_CAMERA=n
# CONFIG_DRM=n (fbcon만 사용한다면)
# CONFIG_MODEM=n
# CONFIG_BLUETOOTH=n
# CONFIG_BT=n
# CONFIG_NFC=n

# 메모리 최적화 옵션 활성화:
# CONFIG_SLUB=y
# CONFIG_SLUB_DEBUG=n
# CONFIG_ZRAM=y
# CONFIG_ZSWAP=y
# CONFIG_LZ4_COMPRESS=y
# CONFIG_KALLSYMS=n (디버깅 심볼 제거)
# CONFIG_DEBUG_KERNEL=n

# 재빌드
pmbootstrap build linux-samsung-r3q --force
```

#### 4. Init 시스템 최적화
```bash
# 부팅 시간 측정
dmesg | grep "Boot took"

# OpenRC 서비스 최소화
rc-update show

# 필수만 남기기:
# - devfs, dmesg, hwclock, modules, sysctl (boot)
# - networking, sshd, wpa_supplicant (default)
# - killprocs, mount-ro, savecache (shutdown)
```

#### 5. 런타임 메모리 튜닝
```bash
# sysctl 설정
cat > /etc/sysctl.d/memory.conf << 'EOF'
# 메모리 최적화
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio=10
vm.dirty_background_ratio=5

# 네트워크 버퍼 감소
net.core.rmem_max=262144
net.core.wmem_max=262144
EOF

sysctl -p /etc/sysctl.d/memory.conf
```

#### 6. 스트레스 테스트
```bash
# stress-ng 설치
apk add stress-ng

# CPU 스트레스 (과열 테스트)
stress-ng --cpu 8 --timeout 60s --metrics

# 메모리 스트레스
stress-ng --vm 1 --vm-bytes 500M --timeout 300s

# 동시 실행 (실사용 시뮬레이션)
stress-ng --cpu 4 --vm 1 --vm-bytes 300M --timeout 3600s

# 온도 모니터링
watch -n 1 cat /sys/class/thermal/thermal_zone*/temp
```

#### 7. 장기 안정성 테스트
```bash
# 24시간 가동 테스트
# 메모리 사용량 로깅
cat > /usr/local/bin/memlog << 'EOF'
#!/bin/sh
while true; do
    echo "$(date): $(free -m | grep Mem | awk '{print $3}')" >> /var/log/memlog.txt
    sleep 300  # 5분마다
done
EOF

chmod +x /usr/local/bin/memlog
/usr/local/bin/memlog &

# 24시간 후 분석
cat /var/log/memlog.txt
# 메모리 사용량이 계속 증가하면 메모리 누수
```

### 목표 RAM 사용량
- **Idle**: 150-250MB
- **SSH 세션 활성**: 180-280MB
- **컴파일 작업 중**: 500MB-1GB (나머지 4GB는 작업에 사용 가능)

### 성공 기준
- ✅ RAM 사용 <300MB (idle)
- ✅ 24시간 가동 안정성
- ✅ 메모리 누수 없음
- ✅ WiFi 안정성 (장기간 연결 유지)
- ✅ SSH 응답성 양호
- ✅ 과열 없음

### 예상 소요 시간
- 4-7일

---

## 안전 및 복구

### 백업 전략

#### Phase 0 이전 필수 백업
```bash
# TWRP로 부팅
adb reboot recovery

# 모든 중요 파티션 백업
adb shell
dd if=/dev/block/bootdevice/by-name/boot of=/sdcard/backup_boot.img
dd if=/dev/block/bootdevice/by-name/recovery of=/sdcard/backup_recovery.img
dd if=/dev/block/bootdevice/by-name/dtbo of=/sdcard/backup_dtbo.img
dd if=/dev/block/bootdevice/by-name/vbmeta of=/sdcard/backup_vbmeta.img
dd if=/dev/block/bootdevice/by-name/abl of=/sdcard/backup_abl.img

# EFS (IMEI 데이터) 백업 - 매우 중요!
tar -czf /sdcard/backup_efs.tar.gz /efs

# PC로 복사
exit
adb pull /sdcard/backup_*.img ~/A90_backup/
adb pull /sdcard/backup_efs.tar.gz ~/A90_backup/

# 안전한 곳에 추가 백업
cp -r ~/A90_backup ~/A90_backup_$(date +%Y%m%d)
```

### 브릭 시나리오 및 복구

#### 시나리오 1: 부팅 이미지 문제 (가장 흔함)
**증상**: 부팅 루프, 로고에서 멈춤

**복구**:
```bash
# 부트로더 모드 진입
# 전원 버튼 + 볼륨 다운 길게 누름

# 백업 복원
fastboot flash boot ~/A90_backup/backup_boot.img
fastboot reboot
```

#### 시나리오 2: TWRP 접근 가능
**증상**: 부팅 안 되지만 TWRP는 작동

**복구**:
```bash
# TWRP로 부팅
# 전원 버튼 + 볼륨 업 길게 누름

adb shell
cd /sdcard
# 백업 이미지를 다시 복사했다면
dd if=/sdcard/backup_boot.img of=/dev/block/bootdevice/by-name/boot
reboot
```

#### 시나리오 3: 완전 브릭 (매우 드묾)
**증상**: 부트로더도 TWRP도 안 됨

**복구**:
1. Samsung Odin 사용 (Windows 필요)
2. SM-A908N 공식 펌웨어 다운로드 (sammobile.com)
3. 다운로드 모드 진입 (전원 + 볼륨 다운 + USB 연결)
4. Odin으로 전체 펌웨어 플래시
5. 루트 및 TWRP 재설치

### 각 Phase별 롤백 전략

| Phase | 롤백 방법 | 위험도 |
|-------|-----------|--------|
| Phase 0 (Kexec) | 재부팅만 하면 됨 | 없음 |
| Phase 1 (Base) | fastboot flash boot backup_boot.img | 낮음 |
| Phase 2 (WiFi) | 동일 (부팅 이미지만 관련) | 낮음 |
| Phase 3 (SSH) | 소프트웨어만, 롤백 불필요 | 없음 |
| Phase 4 (Display) | fastboot flash boot backup_boot.img | 낮음 |
| Phase 5 (Optimize) | 소프트웨어/설정만 | 없음 |

### 비상 액세스 방법

#### 1차: USB 네트워킹
```bash
# PC에서
sudo ip addr add 172.16.42.1/24 dev usb0
sudo ip link set usb0 up
ssh user@172.16.42.2
```

#### 2차: TWRP ADB
```bash
# TWRP로 부팅
adb shell
# 시스템 복구 작업
```

#### 3차: fastboot
```bash
# 부트로더로 부팅
fastboot devices
fastboot flash boot backup_boot.img
```

#### 최종: Odin (Windows)
Samsung 공식 펌웨어로 완전 복구

---

## 예상 결과

### RAM 사용량 비교

| 상태 | Android 12 | PostmarketOS | 절약량 |
|------|------------|--------------|--------|
| **부팅 직후** | 4.5GB | 150MB | 4.35GB (96%) |
| **Idle (SSH 연결)** | 5GB | 200MB | 4.8GB (96%) |
| **작업 중 (예: 컴파일)** | 5GB+ (swap) | 500MB + 4GB 작업 | 자유로운 사용 |

### 기능 매트릭스

| 기능 | Android 12 | PostmarketOS | 비고 |
|------|------------|--------------|------|
| **WiFi** | ✅ | ✅ | ath10k 드라이버 |
| **SSH** | ❌ (앱 필요) | ✅ | 네이티브 |
| **개발 도구** | ⚠️ (Termux) | ✅ | 전체 Linux |
| **카메라** | ✅ | ❌ | 불필요 |
| **오디오** | ✅ | ❌ | 불필요 |
| **모뎀** | ✅ | ❌ | 불필요 |
| **배터리 수명** | 보통 | 향상 | 백그라운드 프로세스 없음 |
| **발열** | 높음 | 낮음 | 최소 서비스 |

### 성능 예상

#### 부팅 시간
- **Android 12**: ~60-90초
- **PostmarketOS**: ~20-40초 (최적화 후)

#### 유휴 전력 소비
- **Android 12**: ~500-800mW
- **PostmarketOS**: ~200-400mW (예상)

#### 네트워크 성능
- **WiFi 속도**: 동일 (하드웨어 제한)
- **SSH 응답성**: 향상 (시스템 부하 낮음)

---

## 타임라인 요약

### 보수적 일정 (6주)
```
Week 1: Phase 0-1 (Kexec 테스트 + 기본 포팅)
Week 2: Phase 1 계속 (부팅 안정화)
Week 3: Phase 2 (WiFi 통합)
Week 4: Phase 3 (SSH + 서비스)
Week 5: Phase 5 (최적화)
Week 6: Phase 5 계속 + 안정성 테스트
```

### 낙관적 일정 (4주)
```
Week 1: Phase 0-1 (순조로운 경우)
Week 2: Phase 2 (WiFi 한 번에 성공)
Week 3: Phase 3-5 (빠른 최적화)
Week 4: 안정화 및 여유
```

### 현실적 일정 (5주)
```
Week 1: Phase 0-1
Week 2: Phase 1-2 (WiFi 트러블슈팅)
Week 3: Phase 2-3
Week 4: Phase 5 (최적화)
Week 5: 안정화 테스트
```

---

## 의사결정 체크리스트

### 주요 결정 사항

#### 1. 커널 선택 (Week 1)
- [ ] **Option A**: Samsung 4.14.190 (downstream)
  - 장점: 드라이버 많음, 안정적
  - 단점: 오래됨, 보안 업데이트 없음
- [ ] **Option B**: Mainline 6.1 LTS
  - 장점: 최신, 장기 지원
  - 단점: 포팅 작업 많음

**권장**: Samsung 커널로 시작, 나중에 mainline 고려

#### 2. Init 시스템 (Week 1)
- [ ] **OpenRC** (PostmarketOS 기본)
  - RAM: ~5-10MB
  - 복잡도: 중
- [ ] **systemd**
  - RAM: ~30-40MB
  - 복잡도: 하 (익숙함)

**권장**: OpenRC (RAM 절약)

#### 3. 디스플레이 작업 (Week 3-4)
- [ ] **지금 구현**: 3-7일 투자
- [ ] **나중에 추가**: 시간 절약
- [ ] **완전히 스킵**: SSH만 사용

**권장**: 나중에 추가 (우선순위 낮음)

#### 4. 패키지 관리 (Week 2)
- [ ] **Alpine APK**: 쉬운 업데이트
- [ ] **정적 바이너리만**: 최소 RAM

**권장**: Alpine APK 유지

---

## 리소스 및 참고자료

### 공식 문서
- **PostmarketOS Wiki**: https://wiki.postmarketos.org/
- **Snapdragon 855 페이지**: https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_855_(SM8150)
- **OnePlus 7 Pro** (참조 디바이스): https://wiki.postmarketos.org/wiki/OnePlus_7_Pro_(oneplus-guacamole)

### 커널 소스
- **Samsung 오픈소스**: https://opensource.samsung.com/
- **CodeAuroraForum** (CAF): https://source.codeaurora.org/
- **Mainline 커널**: https://kernel.org/

### 펌웨어
- **ath10k 펌웨어**: https://github.com/kvalo/ath10k-firmware
- **LineageOS 펌웨어 리포**: https://github.com/TheMuppets

### 도구
- **pmbootstrap**: https://gitlab.com/postmarketOS/pmbootstrap
- **mkbootimg**: https://github.com/osm0sis/mkbootimg
- **Android Image Kitchen**: https://github.com/osm0sis/Android-Image-Kitchen

### 커뮤니티
- **PostmarketOS Matrix**: #postmarketos:matrix.org
- **XDA SM-A908N**: https://forum.xda-developers.com/samsung-galaxy-a90-5g
- **Reddit**: /r/postmarketos

---

## 문제 해결 가이드

### 일반적인 문제

#### 문제: 커널 컴파일 에러
```
에러: implicit declaration of function...
```
**해결**:
1. GCC 버전 확인 (`gcc --version`)
2. Samsung 커널은 GCC 9 또는 10 필요
3. `apt install gcc-9 g++-9` 설치
4. `export CC=gcc-9` 설정

#### 문제: 부팅 루프
```
증상: 로고 반복, 커널 패닉
```
**해결**:
1. TWRP로 부팅
2. `adb logcat` 또는 `dmesg` 확인
3. initramfs 또는 root 마운트 문제 가능성
4. 백업으로 복원

#### 문제: WiFi 펌웨어 로드 실패
```
dmesg: ath10k_snoc: firmware file not found
```
**해결**:
1. 펌웨어 경로 확인: `/lib/firmware/ath10k/WCN3990/hw1.0/`
2. 파일명 정확히 일치: `firmware-5.bin`, `board.bin`
3. 권한 확인: `chmod 644 /lib/firmware/ath10k/...`
4. 다른 소스에서 펌웨어 시도 (LineageOS, CAF)

#### 문제: SSH 연결 안 됨
```
증상: Connection refused 또는 timeout
```
**해결**:
1. WiFi 연결 확인: `ip addr show wlan0`
2. SSH 서비스 확인: `rc-service sshd status`
3. 방화벽 확인: `iptables -L -n`
4. USB 네트워킹으로 접속해서 디버그

#### 문제: 메모리 부족
```
dmesg: Out of memory: Kill process...
```
**해결**:
1. ZRAM 활성화
2. 불필요한 서비스 중지
3. 커널 메모리 설정 조정

---

## 최종 체크리스트

### 시작 전
- [ ] 개발 PC 준비 (Linux, 충분한 디스크 공간)
- [ ] 모든 파티션 백업 완료
- [ ] 백업을 안전한 곳에 복사
- [ ] TWRP 부팅 확인
- [ ] fastboot 작동 확인
- [ ] WiFi 펌웨어 추출 완료

### Phase 0 완료 후
- [ ] Kexec로 테스트 커널 부팅 성공
- [ ] USB 네트워킹 작동
- [ ] 기본 명령어 실행 확인

### Phase 1 완료 후
- [ ] PostmarketOS 부팅 성공
- [ ] 로그인 가능
- [ ] APK 패키지 설치 가능
- [ ] 파일시스템 읽기/쓰기 정상

### Phase 2 완료 후
- [ ] wlan0 인터페이스 나타남
- [ ] 네트워크 스캔 성공
- [ ] WiFi 연결 및 인터넷 접속
- [ ] 부팅 시 자동 연결

### Phase 3 완료 후
- [ ] SSH를 통한 원격 접속
- [ ] USB 케이블 없이 작동
- [ ] 기본 도구 설치 완료
- [ ] 재부팅 후 자동 서비스 시작

### Phase 5 완료 후
- [ ] RAM 사용량 <300MB
- [ ] 24시간 안정성 테스트 통과
- [ ] 메모리 누수 없음
- [ ] 과열 문제 없음
- [ ] 모든 기능 정상 작동

---

## 성공 메트릭

### MVP (Minimum Viable Product)
✅ **기준**: WiFi를 통해 SSH 접속 가능한 Linux 시스템

- 부팅 성공
- WiFi 연결
- SSH 접속
- 기본 명령어 실행
- RAM <350MB

**목표 달성 시점**: Week 3-4

### 완전 기능 시스템
✅ **기준**: 안정적이고 최적화된 프로덕션 시스템

- 모든 MVP 기능
- 자동 부팅 및 연결
- RAM <250MB
- 24시간 안정성
- 개발 환경 구축 완료

**목표 달성 시점**: Week 5-6

### 최적화 시스템 (Stretch Goal)
✅ **기준**: 극한 최적화

- RAM <150MB
- 부팅 시간 <30초
- 커스텀 최적화 커널
- 모든 불필요한 코드 제거

**목표 달성 시점**: Week 7+ (선택)

---

## 결론

### 프로젝트 실행 가능성: 높음 (75%)

**성공 요인**:
- ✅ 언락된 부트로더
- ✅ TWRP 설치됨 (안전망)
- ✅ 잘 지원되는 SoC (Snapdragon 855)
- ✅ 표준 WiFi 칩셋 (WCN3998)
- ✅ 커널 소스 공개됨
- ✅ 참조 디바이스 존재 (OnePlus 7 Pro)
- ✅ 몇 주 투자 가능

**주요 도전 과제**:
1. WiFi 펌웨어 통합 (80% 성공 예상)
2. 커널 컴파일 및 부팅 (90% 성공 예상)
3. 시간 투자 (4-6주 필요)

**최악의 경우**:
- WiFi가 작동하지 않아도 USB 네트워킹으로 사용 가능
- TWRP로 언제든 안드로이드 복구 가능
- 실제 브릭 가능성은 5% 미만

### 권장사항

**이 프로젝트를 시작하세요!**

이유:
1. 기술적으로 실행 가능
2. 안전 장치 충분 (TWRP, 백업)
3. 목표(RAM 절약)가 명확하고 달성 가능
4. 학습 가치 높음
5. 커뮤니티에 기여 가능 (SM-A908N 최초 포팅)

---

## 다음 단계

### 지금 바로 시작하기

1. **개발 환경 구축** (1시간)
   ```bash
   sudo apt install git gcc-aarch64-linux-gnu make bc bison flex libssl-dev
   pip3 install pmbootstrap
   ```

2. **백업 생성** (30분)
   ```bash
   adb reboot recovery
   # TWRP에서 모든 파티션 백업
   ```

3. **WiFi 펌웨어 추출** (15분)
   ```bash
   adb pull /vendor/firmware_mnt/image/wlan/ ~/wifi_firmware/
   ```

4. **Kexec 테스트 시작** (Day 1-3)
   ```bash
   # 테스트 커널 빌드 및 kexec 부팅
   ```

**첫 주 목표**: Kexec로 테스트 커널 부팅 성공

---

**문서 버전**: 1.0
**작성일**: 2025년
**디바이스**: Samsung Galaxy A90 5G (SM-A908N)
**목표**: 네이티브 Linux 부팅, RAM 5GB → 150-300MB
**예상 기간**: 4-6주
**성공 확률**: 75%

**행운을 빕니다! 🚀🐧**
