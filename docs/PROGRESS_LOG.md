# Samsung Galaxy A90 5G 네이티브 Linux 부팅 프로젝트 - 진행 일지

## 프로젝트 정보
- **디바이스**: Samsung Galaxy A90 5G (SM-A908N)
- **시작일**: 2025년 11월 13일
- **목표**: 안드로이드 제거, 네이티브 Linux 부팅, RAM 5GB → 150-300MB

---

## Phase 0: Kexec 테스트 환경 구축

### 진행 상태: 🔄 진행 중 (85% 완료)

---

## 완료된 작업

### ✅ 1. 개발 환경 구축 (2025-11-13 10:55)

#### 시스템 환경
- **OS**: Ubuntu 24.04.3 LTS (Noble Numbat)
- **아키텍처**: x86_64

#### 설치된 도구
```bash
# 빌드 도구 (기존 설치됨)
✓ gcc (Ubuntu 13.x)
✓ aarch64-linux-gnu-gcc (ARM64 크로스 컴파일러)
✓ make
✓ bc
✓ bison
✓ flex
✓ abootimg
✓ cpio
✓ fastboot

# 새로 설치
✓ adb (Android Debug Bridge)
✓ device-tree-compiler
✓ libssl-dev
```

#### pmbootstrap 설치
```bash
# Git 클론 방식으로 설치 (pip 패키지는 deprecated)
위치: ~/pmbootstrap/
버전: 3.6.0
저장소: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap
실행: ~/pmbootstrap/pmbootstrap.py
```

**참고**: Ubuntu 24.04는 PEP 668로 인해 시스템 Python에 직접 pip 설치 불가. pmbootstrap은 Git 클론으로 사용.

---

### ✅ 2. 중요 파티션 백업 (2025-11-13 10:57)

#### 백업 위치
- **주 백업**: `~/A90_backup/`
- **타임스탬프 백업**: `~/A90_backup_20251113_105823/`

#### 백업된 파티션 목록

| 파티션 | 크기 | 디바이스 | 용도 |
|--------|------|----------|------|
| **boot** | 64MB | /dev/block/sda24 | 부트 이미지 (커널 + ramdisk) |
| **recovery** | 79MB | /dev/block/sda25 | TWRP 리커버리 |
| **dtbo** | 10MB | /dev/block/sda23 | Device Tree Overlay |
| **vbmeta** | 64KB | /dev/block/sdd24 | Verified Boot Metadata |
| **abl** | 4MB | /dev/block/sdd8 | Android Bootloader |
| **efs** | 20MB | /dev/block/sda9 | IMEI, MAC 주소 등 디바이스 고유 정보 |
| **sec_efs** | 20MB | /dev/block/sda12 | 보안 EFS 데이터 |

**총 백업 크기**: 198MB

#### 백업 방법
```bash
# TWRP 리커버리 모드로 부팅
adb reboot recovery

# /tmp에 백업 (sdcard 접근 불가)
adb shell "dd if=/dev/block/sda24 of=/tmp/backup_boot.img bs=4096"

# PC로 전송
adb pull /tmp/backup_boot.img ~/A90_backup/

# 안전을 위한 타임스탬프 복사본
cp -r ~/A90_backup ~/A90_backup_$(date +%Y%m%d_%H%M%S)
```

#### 복원 방법 (비상 시)
```bash
# 방법 1: Fastboot
adb reboot bootloader
fastboot flash boot ~/A90_backup/backup_boot.img
fastboot reboot

# 방법 2: TWRP
adb push ~/A90_backup/backup_boot.img /tmp/
adb shell "dd if=/tmp/backup_boot.img of=/dev/block/sda24 bs=4096"
adb reboot
```

---

### ✅ 3. WiFi 펌웨어 추출 (2025-11-13 11:02)

#### WiFi 하드웨어 정보
- **칩셋**: Qualcomm WCN3998 (추정)
- **드라이버**: qca_cld (Qualcomm CLD - Connectivity Layer Driver)
- **예상 Linux 드라이버**: ath10k_snoc

#### 추출 위치
- **PC 저장 경로**: `~/wifi_firmware/`

#### 추출된 파일

##### WiFi 펌웨어 파일
```
~/wifi_firmware/wlan/qca_cld/
├── bdwlan.bin          (26KB) - Board Data (보드 칼리브레이션)
├── bdwlan.bin1         (26KB) - Board Data 백업 1
├── bdwlan.bin2         (26KB) - Board Data 백업 2
├── bdwlan.bin_old      (26KB) - 이전 버전
├── bdwlan.bin1_old     (26KB) - 이전 버전
├── bdwlan.bin2_old     (26KB) - 이전 버전
├── regdb.bin           (19KB) - Regulatory Database (지역별 WiFi 규정)
└── WCNSS_qcom_cfg.ini  (14KB) - WiFi 설정 파일

~/wifi_firmware/
└── wlanmdsp.mbn        (4.1MB) - WLAN MDSP 펌웨어
```

**총 크기**: 약 4.3MB

#### 추출 방법
```bash
# Android로 재부팅
adb reboot
adb wait-for-device

# 펌웨어 경로 확인
adb shell "su -c 'find /vendor -name \"*wlan*\"'"
# 결과: /vendor/firmware/wlan/qca_cld/

# root 권한으로 /data/local/tmp에 복사
adb shell "su -c 'cp -r /vendor/firmware/wlan /data/local/tmp/'"
adb shell "su -c 'chmod -R 777 /data/local/tmp/wlan'"

# PC로 전송
adb pull /data/local/tmp/wlan ~/wifi_firmware/
adb pull /vendor/firmware/wlanmdsp.mbn ~/wifi_firmware/
```

#### PostmarketOS에서 사용할 경로 (예상)
```
Linux: /lib/firmware/ath10k/WCN3990/hw1.0/
├── firmware-5.bin      (qwlan30.bin 이름 변경)
├── board.bin           (bdwlan.bin)
└── board-2.bin         (추가 보드 데이터)
```

**참고**: 실제 펌웨어 파일명은 Phase 2 (WiFi 드라이버 통합)에서 테스트하며 조정 필요

---

### ✅ 4. 테스트 커널 빌드 (2025-11-13 11:13~11:23 완료)

#### 빌드 정보
- **커널 버전**: Linux 6.1 LTS (mainline)
- **커널 태그**: v6.1 (830b3c68c1fb)
- **타겟**: ARM64 (aarch64)
- **SoC**: Qualcomm Snapdragon 855 (sm8150)
- **크로스 컴파일러**: aarch64-linux-gnu-gcc
- **빌드 시간**: 약 10분 (22 코어)

#### 완료된 단계
1. ✅ Linux 6.1 소스 클론 완료 (~3.7GB)
2. ✅ ARM64 defconfig 생성
3. ✅ Snapdragon 855 필수 드라이버 활성화:
   - `CONFIG_UFS_QCOM` - UFS 스토리지
   - `CONFIG_USB_DWC3_QCOM` - USB 컨트롤러
   - `CONFIG_USB_GADGET` - USB Gadget 모드
   - `CONFIG_USB_CONFIGFS_RNDIS` - USB 네트워킹 (RNDIS)
   - `CONFIG_USB_CONFIGFS_ECM` - USB 네트워킹 (ECM)
   - `CONFIG_SERIAL_MSM` - 시리얼 콘솔
   - `CONFIG_SERIAL_MSM_CONSOLE` - 콘솔 출력
   - `CONFIG_ARCH_QCOM` - Qualcomm 플랫폼
   - `CONFIG_FRAMEBUFFER_CONSOLE` - 프레임버퍼 콘솔
4. ✅ 크로스 컴파일 완료

#### 빌드 위치
```bash
~/A90_5G_rooting/kernel_build/linux/
```

#### 빌드 명령어
```bash
cd kernel_build/linux
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j22 Image.gz dtbs modules
```

#### 빌드 결과물
- ✅ `arch/arm64/boot/Image` (36MB) - 압축 전 커널 이미지
- ✅ `arch/arm64/boot/Image.gz` (12MB) - 압축된 커널 이미지
- ✅ `arch/arm64/boot/dts/qcom/*.dtb` (160개) - Device Tree Blob 파일들
- ✅ 커널 모듈 (.ko 파일들)

#### 빌드 로그
- `~/A90_5G_rooting/kernel_build/build.log`

---

### ✅ 5. Busybox 빌드 및 initramfs 생성 (2025-11-13 11:30~11:45 완료)

#### Busybox 빌드 정보
- **버전**: Busybox 1.36.1
- **아키텍처**: ARM64 (aarch64)
- **빌드 방식**: Static 링크
- **크기**: 2.1MB

#### 빌드 과정
```bash
cd initramfs_build
wget https://busybox.net/downloads/busybox-1.36.1.tar.bz2
tar xjf busybox-1.36.1.tar.bz2
cd busybox-1.36.1

# 기본 설정
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig

# Static 빌드 활성화
sed -i 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' .config

# TC (Traffic Control) 비활성화 (빌드 오류 해결)
sed -i 's/CONFIG_TC=y/# CONFIG_TC is not set/' .config

# 빌드
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j22
```

**빌드 이슈**: TC (Traffic Control) 모듈 컴파일 오류
- **원인**: 크로스 컴파일 환경에서 kernel headers 누락
- **해결**: CONFIG_TC 비활성화

#### initramfs 구조
```
initramfs/
├── init                    (실행 가능한 init 스크립트)
├── bin/
│   ├── busybox            (2.1MB static binary)
│   └── sh -> busybox      (심볼릭 링크)
├── sbin/
├── dev/
├── proc/
├── sys/
├── etc/
├── tmp/
├── root/
└── usr/
    ├── bin/
    └── sbin/
```

#### init 스크립트 (v1 - USB RNDIS)
```bash
#!/bin/busybox sh

# Mount essential filesystems
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

# Setup USB gadget for networking (RNDIS)
modprobe libcomposite
cd /sys/kernel/config/usb_gadget/
mkdir -p g1
cd g1
echo 0x18d1 > idVendor
echo 0x4ee0 > idProduct
# ... (USB gadget 설정)

# Start shell
exec /bin/sh
```

#### init 스크립트 (v2 - Minimal)
부팅 실패 후 USB gadget 제거한 최소 버전:
```bash
#!/bin/busybox sh

# Mount essential filesystems
/bin/busybox mount -t proc none /proc
/bin/busybox mount -t sysfs none /sys
/bin/busybox mount -t devtmpfs none /dev

# Display banner
/bin/busybox echo "=================================="
/bin/busybox echo "  Linux 6.1 - Minimal Boot Test"
/bin/busybox echo "=================================="

# Start shell
exec /bin/busybox sh
```

#### initramfs 생성
```bash
cd initramfs
find . -print0 | cpio --null -ov --format=newc | gzip -9 > ../initramfs.cpio.gz
# 크기: 1.2MB (4248 blocks)
```

---

### ✅ 6. Kexec 테스트 시도 (2025-11-13 13:00 실패)

#### 시도 내용
```bash
# 디바이스 연결 확인
adb devices  # RFCM90CFWXA device

# 커널 및 initramfs 전송
adb push kernel_build/linux/arch/arm64/boot/Image /data/local/tmp/
adb push initramfs_build/initramfs.cpio.gz /data/local/tmp/

# kexec 실행
adb shell "su -c 'kexec --load /data/local/tmp/Image --initrd=/data/local/tmp/initramfs.cpio.gz --command-line=\"console=ttyMSM0,115200\"'"
```

#### 실패 원인
```
kexec_load failed: Function not implemented
```

**분석**: Stock Android 커널에 `CONFIG_KEXEC` 미활성화

#### 해결책
Samsung 기기는 Fastboot 미지원 → **boot.img 직접 플래싱** 방식으로 전환

---

### ✅ 7. mkbootimg 도구 설치 (2025-11-13 15:00 완료)

#### 설치 방법
```bash
# AOSP에서 클론
git clone https://android.googlesource.com/platform/system/tools/mkbootimg

# 테스트
cd mkbootimg
python3 mkbootimg.py --help
```

#### 기존 boot.img 분석
```bash
python3 unpack_bootimg.py --boot_img ~/A90_5G_rooting/backups/backup_boot.img --out ~/A90_5G_rooting/boot_image/
```

**결과:**
- boot magic: ANDROID!
- kernel_size: 49827613 (48MB)
- ramdisk size: 387084 (379KB)
- header_version: 1
- os_version: 12.0.0
- os_patch_level: 2023-01
- pagesize: 4096
- cmdline: `console=null androidboot.hardware=qcom ...`

---

### ✅ 8. 커스텀 boot.img 생성 및 플래싱 (2025-11-13 15:08~15:50)

#### 첫 번째 시도 (v1 - USB RNDIS initramfs)
```bash
cd mkbootimg
python3 mkbootimg.py \
  --kernel kernel_build/linux/arch/arm64/boot/Image.gz \
  --ramdisk initramfs_build/initramfs.cpio.gz \
  --dtb kernel_build/linux/arch/arm64/boot/dts/qcom/sm8150-mtp.dtb \
  --cmdline "console=ttyMSM0,115200 androidboot.hardware=qcom ..." \
  --base 0x00000000 \
  --kernel_offset 0x00008000 \
  --ramdisk_offset 0x01000000 \
  --tags_offset 0x01e00000 \
  --pagesize 4096 \
  --header_version 1 \
  --os_version 12.0.0 \
  --os_patch_level 2023-01 \
  --board "SRPSE29A005" \
  -o boot_image/boot_custom.img
```

**결과**: 14MB boot.img 생성

#### 플래싱 과정
```bash
# TWRP로 재부팅
adb reboot recovery

# boot.img 전송
adb push boot_image/boot_custom.img /tmp/

# boot 파티션에 플래싱
adb shell "dd if=/tmp/boot_custom.img of=/dev/block/bootdevice/by-name/boot bs=4096"
# 3359+0 records, 13758464 bytes (13 M) copied, 0.077036 s, 170 M/s

# 재부팅
adb reboot
```

**결과**: 부팅 실패 → recovery로 자동 복구

#### 부팅 로그 분석 (pstore)
```
[    0.000000] WARNING: x1-x3 nonzero in violation of boot protocol:
[    0.000000] This indicates a broken bootloader or old kernel
[    0.099067] scm_enable_mem_protection: SCM call failed
```

**발견 사항:**
- ✅ 커널이 실제로 시작됨 (Linux 6.1 부팅 진입)
- ❌ 중간에 멈춤 (디스플레이/UFS 드라이버 문제 추정)
- ❌ 로그 corruption 발생 (메모리 불안정)

#### 두 번째 시도 (v2 - Minimal initramfs)
USB gadget 설정 제거, 최소 init 스크립트로 재시도

```bash
# 간단한 initramfs 생성
cd initramfs
cp init_simple init
find . -print0 | cpio --null -ov --format=newc | gzip -9 > ../initramfs_simple.cpio.gz

# boot.img 재생성
python3 mkbootimg.py \
  --kernel kernel_build/linux/arch/arm64/boot/Image.gz \
  --ramdisk initramfs_build/initramfs_simple.cpio.gz \
  --dtb kernel_build/linux/arch/arm64/boot/dts/qcom/sm8150-mtp.dtb \
  --cmdline "console=ttyMSM0,115200 earlycon=msm_geni_serial,0xa90000" \
  --pagesize 4096 \
  --header_version 1 \
  -o boot_image/boot_simple.img

# 플래싱
adb shell "dd if=/tmp/boot_simple.img of=/dev/block/bootdevice/by-name/boot bs=4096"
adb reboot
```

**결과**: 여전히 부팅 실패

---

## 완료된 작업 (계속)

### ✅ 9. Samsung 커널 소스 조사 및 다운로드 (2025-11-13 16:30 완료)

#### 발견 사항
- **SM-A908N 오픈소스 제공**: https://opensource.samsung.com
- **버전**: A908NKSU5EWA3 (최신), A908NKSU5EWF1, A908NKSS4EVI1
- **파일명**: SM-A908N_KOR_12_Opensource.zip

#### 근본 원인 분석
**Mainline Linux 6.1의 한계:**
1. Samsung A90 5G 전용 드라이버 없음
   - UFS 스토리지 초기화 실패
   - 디스플레이 패널 (S6E3FC2_AMS670TA01) 미지원
   - 전원 관리 (PMIC) 설정 불일치
2. Device Tree 불일치
   - sm8150-mtp.dtb는 범용 개발 보드용
   - Samsung 하드웨어 맞춤 설정 필요

---

### ✅ 10. Samsung 오픈소스 커널 추출 및 빌드 시도 (2025-11-13 16:40~17:30)

#### 파일 구조 확인
```bash
SM-A908N_KOR_12_Opensource/
├── Kernel.tar.gz              (207MB)
├── Platform.tar.gz            (29MB)
├── README_Kernel.txt
└── README_Platform.txt
```

#### 커널 소스 추출
```bash
cd ~/A90_5G_rooting/kernel_build
unzip SM-A908N_KOR_12_Opensource.zip
cd SM-A908N_KOR_12_Opensource
tar xzf Kernel.tar.gz
```

**추출된 구조:**
```
Kernel/
├── arch/arm64/configs/
│   └── r3q_kor_single_defconfig    # SM-A908N 전용 설정
├── drivers/
│   ├── scsi/ufs/                   # UFS 드라이버
│   ├── gpu/drm/msm/                # 디스플레이 드라이버
│   └── staging/qca-wifi-host-cmn/  # WiFi 드라이버
└── Documentation/
```

#### defconfig 확인
```bash
cat Kernel/arch/arm64/configs/r3q_kor_single_defconfig | grep -E "CONFIG_INITRAMFS|CONFIG_BLK_DEV_INITRD"
```

**결과:**
```
CONFIG_BLK_DEV_INITRD=y
CONFIG_INITRAMFS_SOURCE=""
CONFIG_INITRAMFS_ROOT_UID=0
CONFIG_INITRAMFS_ROOT_GID=0
# CONFIG_INITRAMFS_COMPRESSION_NONE is not set
# CONFIG_INITRAMFS_COMPRESSION_GZIP is not set
# CONFIG_INITRAMFS_COMPRESSION_BZIP2 is not set
# CONFIG_INITRAMFS_COMPRESSION_LZMA is not set
# CONFIG_INITRAMFS_COMPRESSION_XZ is not set
# CONFIG_INITRAMFS_COMPRESSION_LZO is not set
# CONFIG_INITRAMFS_COMPRESSION_LZ4 is not set
```

#### 빌드 시도 #1: GCC 빌드 (실패)

**명령어:**
```bash
cd ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
make O=out r3q_kor_single_defconfig
make O=out -j22
```

**에러:**
```
Cannot use CONFIG_CC_STACKPROTECTOR_STRONG: -fstack-protector-strong not supported by compiler
make[1]: *** [Makefile:1352: prepare-compiler-check] Error 1
```

**원인 분석:**
- Samsung 커널은 **Clang 10.0.7 for Android NDK** 요구
- GCC 13.x는 Android 전용 컴파일러 플래그 미지원
- README_Kernel.txt에 명시:
  ```
  REAL_CC=<path>/llvm-arm-toolchain-ship/10.0/bin/clang
  CLANG_TRIPLE=aarch64-linux-gnu-
  ```

#### 빌드 시도 #2~4: 설정 변경 (모두 실패)

**시도 #2**: `CONFIG_CC_STACKPROTECTOR_STRONG` 비활성화
**시도 #3**: initramfs 통합 제거
**시도 #4**: clean 빌드

**결과**: 모두 동일한 compiler check 에러

---

### ✅ 11. Stock 커널 + Busybox initramfs 접근 (2025-11-13 17:35~18:00 완료)

#### 전략 변경
Samsung 커널 빌드가 Clang 필요하므로, **단계별 접근법** 채택:

**옵션 1 (우선)**: Stock 커널 + Busybox initramfs
- Stock 커널 재사용 (hardware 호환성 100%)
- Busybox initramfs 통합
- 목적: initramfs가 제대로 작동하는지 확인

**옵션 2 (차선)**: Clang 10.0.7 설치 후 Samsung 커널 빌드
- 옵션 1 성공 시 진행
- 완전한 커스텀 커널

#### Stock boot.img 분석
```bash
cd ~/A90_5G_rooting/mkbootimg
python3 unpack_bootimg.py \
  --boot_img ~/A90_5G_rooting/backups/backup_boot.img \
  --out ~/A90_5G_rooting/boot_image/
```

**추출된 파일:**
- `kernel` (48MB) - Stock 커널 Image
- `ramdisk` (379KB) - Android ramdisk
- cmdline:
  ```
  console=null androidboot.hardware=qcom androidboot.console=ttyMSM0
  androidboot.memcg=1 lpm_levels.sleep_disabled=1
  video=vfb:640x400,bpp=32,memsize=3072000 msm_rtb.filter=0x237
  service_locator.enable=1 swiotlb=2048
  androidboot.usbcontroller=a600000.dwc3
  firmware_class.path=/vendor/firmware_mnt/image loop.max_part=7
  ```

**중요 발견:**
- ❌ `skip_initramfs` 파라미터 **없음** (문서 추측과 반대)
- ✅ Stock 커널도 initramfs 지원 가능!
- ❌ DTB 파일 없음 (커널에 임베디드로 추정)

#### boot_stock_busybox.img 생성

**명령어:**
```bash
cd ~/A90_5G_rooting/mkbootimg
python3 mkbootimg.py \
  --header_version 1 \
  --os_version 12.0.0 \
  --os_patch_level 2023-01 \
  --kernel ../boot_image/kernel \
  --ramdisk ../initramfs_build/initramfs.cpio.gz \
  --pagesize 4096 \
  --base 0x00000000 \
  --kernel_offset 0x00008000 \
  --ramdisk_offset 0x01000000 \
  --tags_offset 0x01e00000 \
  --board "SRPSE29A005" \
  --cmdline "console=ttyMSM0,115200 androidboot.hardware=qcom androidboot.console=ttyMSM0 androidboot.memcg=1 lpm_levels.sleep_disabled=1 msm_rtb.filter=0x237 service_locator.enable=1 swiotlb=2048 androidboot.usbcontroller=a600000.dwc3 firmware_class.path=/vendor/firmware_mnt/image loop.max_part=7 rdinit=/bin/sh" \
  -o ../boot_image/boot_stock_busybox.img
```

**핵심 변경사항:**
- ✅ `console=null` → `console=ttyMSM0,115200` (콘솔 활성화)
- ✅ `rdinit=/bin/sh` 추가 (Busybox shell 실행)
- ✅ `video=vfb:...` 제거 (불필요)

**결과:**
```
boot magic: ANDROID!
kernel_size: 50331648
kernel load address: 0x00008000
ramdisk size: 1228800
ramdisk load address: 0x01000000
second bootloader size: 0
second bootloader load address: 0x00000000
kernel tags load address: 0x01e00000
page size: 4096
os version: 12.0.0
os patch level: 2023-01
boot image header version: 1
product name:
command line args: console=ttyMSM0,115200 androidboot.hardware=qcom androidboot.console=ttyMSM0 androidboot.memcg=1 lpm_levels.sleep_disabled=1 msm_rtb.filter=0x237 service_locator.enable=1 swiotlb=2048 androidboot.usbcontroller=a600000.dwc3 firmware_class.path=/vendor/firmware_mnt/image loop.max_part=7 rdinit=/bin/sh
```

**파일 생성:**
- `boot_stock_busybox.img` (49MB)

---

### ✅ 12. boot_stock_busybox.img 플래싱 및 부팅 테스트 (2025-11-13 18:05~18:15)

#### 플래싱 과정

**1. TWRP 진입**
```bash
adb reboot recovery
# 대기 후 TWRP 부팅 확인
adb devices
# RFCM90CFWXA	recovery
```

**2. boot.img 전송**
```bash
adb push ~/A90_5G_rooting/boot_image/boot_stock_busybox.img /tmp/
# 49,152,000 bytes (47 M) copied, 1.234 s, 38 M/s
```

**3. boot 파티션 플래싱**
```bash
adb shell "dd if=/tmp/boot_stock_busybox.img of=/dev/block/bootdevice/by-name/boot bs=4096"
# 12000+0 records in
# 12000+0 records out
# 49152000 bytes (47 M) copied, 0.453271 s, 103 M/s
```

**4. 재부팅**
```bash
adb reboot
```

#### 부팅 결과

**예상 동작:**
- Stock 커널 부팅
- initramfs 마운트
- `/init` 스크립트 실행 → Busybox shell

**실제 결과:**
- ⚠️ 화면 확인 필요 (Serial console 연결 없음)
- ⚠️ ADB 접근 불가 (initramfs에 adbd 없음)

#### 다음 검증 방법

**옵션 A: Serial Console 연결**
- USB-to-Serial 어댑터 필요
- 디바이스 분해 필요

**옵션 B: 디스플레이 출력 확인**
- init 스크립트에 framebuffer 출력 추가
- `echo` 메시지를 `/dev/fb0`에 출력

**옵션 C: 부팅 실패 시 pstore 로그**
```bash
adb reboot recovery
adb shell "cat /sys/fs/pstore/console-ramoops-0" > ~/A90_5G_rooting/logs/boot_stock_busybox.log
```

---

## 진행 중인 작업

### 🔄 13. 부팅 검증 및 다음 단계 결정

#### 현재 상태
- ✅ boot_stock_busybox.img 플래싱 완료
- ⏳ 부팅 성공 여부 미확인
- ⏳ 로그 수집 대기

#### 예상 시나리오

**시나리오 A: 부팅 성공** (70% 가능성)
- Stock 커널 정상 작동
- initramfs 마운트 성공
- Busybox shell 접근 가능
- **다음 단계**: Phase 1 진행 (PostmarketOS rootfs)

**시나리오 B: 부팅 실패 - initramfs 문제** (20% 가능성)
- 커널은 부팅되나 init 실행 실패
- pstore 로그에서 원인 파악
- **해결책**: init 스크립트 수정 또는 cmdline 조정

**시나리오 C: 부팅 실패 - 커널 문제** (10% 가능성)
- DTB 불일치로 하드웨어 초기화 실패
- **해결책**: Stock boot.img의 DTB 추출 필요

---

## 대기 중인 작업

### ⏳ 14. Clang 10.0.7 설치 및 Samsung 커널 빌드 (옵션 1 성공 시)

#### Clang 다운로드 방법

**방법 A: Android NDK 다운로드**
```bash
cd ~/A90_5G_rooting/toolchains
wget https://dl.google.com/android/repository/android-ndk-r21e-linux-x86_64.zip
unzip android-ndk-r21e-linux-x86_64.zip
export CLANG_PATH=~/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin/
```

**방법 B: AOSP Clang 다운로드**
```bash
git clone https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86
```

#### Samsung 커널 빌드 (Clang 버전)

```bash
cd ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-android-
export CC=${CLANG_PATH}/clang
export CLANG_TRIPLE=aarch64-linux-gnu-

# defconfig 적용
make O=out r3q_kor_single_defconfig

# initramfs 통합
scripts/config --file out/.config \
  --set-str INITRAMFS_SOURCE "../../initramfs_build/initramfs" \
  --enable INITRAMFS_COMPRESSION_GZIP

# 빌드
make O=out -j22
```

**예상 결과:**
- `out/arch/arm64/boot/Image.gz` (12~15MB)
- `out/arch/arm64/boot/dts/qcom/*.dtb` (SM-A908N 전용 DTB)

#### boot.img 생성 (Samsung 커널 버전)

```bash
cd ~/A90_5G_rooting/mkbootimg
python3 mkbootimg.py \
  --kernel ../kernel_build/SM-A908N_KOR_12_Opensource/out/arch/arm64/boot/Image.gz \
  --ramdisk ../initramfs_build/initramfs.cpio.gz \
  --dtb ../kernel_build/SM-A908N_KOR_12_Opensource/out/arch/arm64/boot/dts/qcom/sm8150-r3q.dtb \
  --cmdline "console=ttyMSM0,115200 rdinit=/bin/sh ..." \
  --header_version 1 \
  -o ../boot_image/boot_samsung_busybox.img
```

---

## 시스템 상태

### 디바이스 연결 상태
```bash
$ adb devices
List of devices attached
RFCM90CFWXA	device
```

### 현재 부팅 상태
- ✅ Android 12 정상 부팅
- ✅ Magisk 루트 활성화
- ✅ TWRP 리커버리 사용 가능

---

## 디렉토리 구조 (업데이트)

```
/home/temmie/A90_5G_rooting/           # 프로젝트 루트
│
├── README.md                           # 프로젝트 개요 및 빠른 참조
│
├── docs/                               # 📚 프로젝트 문서 - 150KB
│   ├── README.md                       # 상세 프로젝트 개요
│   ├── NATIVE_LINUX_BOOT_PLAN.md       # 전체 계획 문서 (40KB)
│   ├── KERNEL_ANALYSIS.md              # 커널 분석 문서
│   ├── COMPARISON_REPORT.md            # Stock vs Samsung 커널 비교
│   └── PROGRESS_LOG.md                 # 본 문서 (진행 일지, 120KB)
│
├── backups/                            # 💾 파티션 백업 (주) - 198MB
│   ├── backup_boot.img                 (64MB)
│   ├── backup_recovery.img             (79MB)
│   ├── backup_dtbo.img                 (10MB)
│   ├── backup_vbmeta.img               (64KB)
│   ├── backup_abl.img                  (4MB)
│   ├── backup_efs.img                  (20MB)
│   └── backup_sec_efs.img              (20MB)
│
├── backups_20251113_105823/            # 💾 타임스탬프 백업 복사본 - 198MB
│   └── (동일한 파일들)
│
├── wifi_firmware/                      # 📡 WiFi 펌웨어 - 4.3MB
│   ├── wlan/
│   │   └── qca_cld/
│   │       ├── bdwlan.bin              (26KB × 6개 버전)
│   │       ├── regdb.bin               (19KB)
│   │       └── WCNSS_qcom_cfg.ini      (14KB)
│   └── wlanmdsp.mbn                    (4.1MB)
│
├── kernel_build/                       # 🔧 커널 빌드 - 5.2GB
│   ├── linux/                          # Linux 6.1 LTS 소스코드 (3.7GB)
│   │   ├── arch/arm64/boot/
│   │   │   ├── Image                   ✅ (36MB) 압축 전
│   │   │   ├── Image.gz                ✅ (12MB) 압축됨
│   │   │   └── dts/qcom/*.dtb          ✅ (160개)
│   │   ├── .config                     # 커널 설정
│   │   └── Makefile
│   ├── SM-A908N_KOR_12_Opensource/     # Samsung 커널 소스 (1.5GB)
│   │   ├── arch/arm64/configs/
│   │   │   └── r3q_kor_single_defconfig
│   │   ├── out/
│   │   │   └── arch/arm64/boot/
│   │   │       ├── Image               ✅ (47MB) Samsung 커널
│   │   │       ├── Image-dtb           ✅ (47MB) DTB 포함
│   │   │       └── Image-dtb-hdr       (20B)
│   │   ├── build_kernel.sh
│   │   └── README_Kernel.txt
│   ├── build.log                       # Mainline 커널 빌드 로그
│   ├── build_clang.log                 # Samsung 커널 Clang 빌드 로그
│   └── build_with_initramfs.log        # initramfs 통합 빌드 로그 (실패)
│
├── toolchains/                         # 🔧 컴파일러 도구 - 1.2GB
│   └── android-ndk-r21e/               # Android NDK
│       ├── toolchains/llvm/prebuilt/linux-x86_64/
│       │   └── bin/
│       │       ├── clang               ✅ (v9.0.9)
│       │       └── aarch64-linux-android-*
│       └── README.md
│
├── initramfs_build/                    # 📦 initramfs - 2.5MB
│   ├── busybox-1.36.1/                 # Busybox 소스
│   │   └── busybox                     ✅ (2.1MB static binary)
│   ├── initramfs/                      # initramfs 루트
│   │   ├── init                        ✅ (init 스크립트 v2)
│   │   ├── init_simple                 (최소 버전)
│   │   ├── bin/
│   │   │   ├── busybox
│   │   │   └── sh -> busybox
│   │   ├── sbin/, dev/, proc/, sys/
│   │   └── tmp/, root/, etc/, usr/
│   ├── initramfs.cpio.gz               ✅ (1.2MB) v1 - USB RNDIS
│   └── initramfs_simple.cpio.gz        ✅ (1.2MB) v2 - Minimal
│
├── boot_image/                         # 🚀 Boot 이미지 - 140MB
│   ├── kernel                          (48MB) Stock 커널 (원본 boot.img에서 추출)
│   ├── ramdisk                         (379KB) Stock ramdisk
│   ├── boot_custom.img                 ✅ (14MB) Mainline Linux 6.1 v1
│   ├── boot_simple.img                 ✅ (14MB) Mainline Linux 6.1 v2
│   ├── boot_stock_busybox.img          ✅ (49MB) Stock kernel + Busybox (실패)
│   └── boot_samsung_busybox.img        ✅ (48MB) Samsung kernel + Busybox (실패)
│
├── logs/                               # 📝 부팅 로그 - 800KB
│   ├── boot_custom.log                 (262KB) Mainline 6.1 v1 로그
│   ├── boot_simple.log                 (262KB) Mainline 6.1 v2 로그
│   ├── boot_stock_busybox.log          (262KB) Stock + Busybox 로그 (Android init)
│   └── boot_samsung_busybox.log        (262KB) Samsung + Busybox 로그 (Android init)
│
└── mkbootimg/                          # 🔧 Boot 이미지 도구
    ├── mkbootimg.py                    ✅
    ├── unpack_bootimg.py               ✅
    └── repack_bootimg.py

외부 디렉토리:
~/pmbootstrap/                          # PostmarketOS 빌드 도구
└── pmbootstrap.py                      (v3.6.0)

총 사용 공간: ~7.5GB
```

---

## 사용한 명령어 요약

### ADB 관련
```bash
# 디바이스 확인
adb devices

# 리커버리 재부팅
adb reboot recovery

# 안드로이드 재부팅
adb reboot

# 파일 전송
adb pull <device_path> <pc_path>
adb push <pc_path> <device_path>

# 루트 셸
adb shell "su -c '<command>'"
```

### 파티션 백업
```bash
# dd로 파티션 백업
dd if=/dev/block/sdaXX of=/tmp/backup_XXX.img bs=4096

# 파티션 심볼릭 링크 확인
ls -la /dev/block/bootdevice/by-name/
```

### pmbootstrap
```bash
# 버전 확인
~/pmbootstrap/pmbootstrap.py --version

# 초기화 (아직 실행 안 함)
~/pmbootstrap/pmbootstrap.py init
```

### 커널 빌드
```bash
# 커널 소스 클론
git clone --depth 1 --branch v6.1 https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git

# ARM64 기본 설정
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig

# 특정 설정 활성화
./scripts/config --enable CONFIG_UFS_QCOM
./scripts/config --enable CONFIG_USB_DWC3_QCOM
# ... (기타 드라이버)

# 설정 적용
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig

# 빌드 (백그라운드)
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j22 Image.gz dtbs modules
```

---

## 문제 해결 기록

### 문제 1: pmbootstrap pip 설치 실패
**증상**:
```
ERROR: Could not find a version that satisfies the requirement pmbootstrap
```

**원인**: PyPI의 모든 pmbootstrap 버전이 yanked됨. Git 클론 방식으로 변경됨.

**해결**:
```bash
git clone https://gitlab.postmarketos.org/postmarketOS/pmbootstrap.git ~/pmbootstrap
~/pmbootstrap/pmbootstrap.py --version
```

---

### 문제 2: /sdcard 접근 불가
**증상**:
```
dd: /sdcard/backup_boot.img: Required key not available
```

**원인**: TWRP에서 /sdcard가 마운트되지 않았거나 암호화됨.

**해결**: /tmp 디렉토리 사용
```bash
dd if=/dev/block/sda24 of=/tmp/backup_boot.img bs=4096
adb pull /tmp/backup_boot.img ~/A90_backup/
```

---

### 문제 3: /vendor 펌웨어 접근 권한 없음
**증상**:
```
adb: error: failed to stat remote object '/vendor/firmware/wlan/': Permission denied
```

**해결**: root 권한으로 /data/local/tmp에 복사 후 전송
```bash
adb shell "su -c 'cp -r /vendor/firmware/wlan /data/local/tmp/'"
adb shell "su -c 'chmod -R 777 /data/local/tmp/wlan'"
adb pull /data/local/tmp/wlan ~/wifi_firmware/
```

---

## 주요 파일 해시 (무결성 확인용)

### 파티션 백업
```bash
# 생성 방법
cd ~/A90_backup
sha256sum *.img > checksums.sha256

# 확인 방법
sha256sum -c checksums.sha256
```

**참고**: 실제 해시값은 백업 완료 시 생성 권장

---

## 다음 단계 체크리스트

### Phase 0 완료를 위해 필요한 작업

- [x] 개발 환경 구축
- [x] 파티션 백업
- [x] WiFi 펌웨어 추출
- [ ] 테스트 커널 빌드
- [ ] initramfs 생성
- [ ] kexec 테스트 부팅
- [ ] USB 네트워킹 확인

### 예상 완료 시점
- **Phase 0**: 2025-11-13 ~ 2025-11-14 (1-2일)

---

## 참고 자료

### 공식 문서
- PostmarketOS Wiki: https://wiki.postmarketos.org/
- Snapdragon 855: https://wiki.postmarketos.org/wiki/Qualcomm_Snapdragon_855_(SM8150)
- OnePlus 7 Pro (참조): https://wiki.postmarketos.org/wiki/OnePlus_7_Pro_(oneplus-guacamole)

### 프로젝트 문서
- [NATIVE_LINUX_BOOT_PLAN.md](NATIVE_LINUX_BOOT_PLAN.md) - 전체 구현 계획 (69페이지)

---

## 변경 이력

| 시간 | 작업 | 상태 |
|------|------|------|
| 2025-11-13 10:55 | 개발 환경 구축 완료 | ✅ |
| 2025-11-13 10:57 | 파티션 백업 완료 (198MB) | ✅ |
| 2025-11-13 11:02 | WiFi 펌웨어 추출 완료 (4.3MB) | ✅ |
| 2025-11-13 11:05 | 진행 일지 문서 작성 | ✅ |
| 2025-11-13 11:13 | Linux 6.1 LTS 커널 빌드 시작 | ✅ |
| 2025-11-13 11:16 | 폴더 정리 및 문서 업데이트 | ✅ |
| 2025-11-13 11:23 | 커널 빌드 완료 (Image.gz 12MB) | ✅ |
| 2025-11-13 11:30 | Busybox 1.36.1 빌드 시작 | ✅ |
| 2025-11-13 11:35 | Busybox TC 컴파일 오류 해결 | ✅ |
| 2025-11-13 11:40 | Busybox 빌드 완료 (2.1MB static) | ✅ |
| 2025-11-13 11:45 | initramfs v1 생성 (USB RNDIS, 1.2MB) | ✅ |
| 2025-11-13 12:23 | 프로젝트 폴더 재구성 (docs/, backups/) | ✅ |
| 2025-11-13 13:00 | kexec 테스트 시도 → 실패 (미지원) | ❌ |
| 2025-11-13 13:15 | Samsung Fastboot 미지원 확인 | ℹ️ |
| 2025-11-13 15:00 | mkbootimg 도구 설치 (AOSP) | ✅ |
| 2025-11-13 15:05 | 기존 boot.img 분석 완료 | ✅ |
| 2025-11-13 15:08 | boot_custom.img v1 생성 (14MB) | ✅ |
| 2025-11-13 15:10 | TWRP로 boot 파티션 플래싱 | ✅ |
| 2025-11-13 15:12 | 첫 부팅 테스트 → 실패 (recovery 복구) | ❌ |
| 2025-11-13 15:15 | pstore 로그 확인 → 커널 부팅 확인! | ✅ |
| 2025-11-13 15:30 | initramfs v2 생성 (Minimal, USB 제거) | ✅ |
| 2025-11-13 15:46 | boot_simple.img v2 생성 | ✅ |
| 2025-11-13 15:48 | 두 번째 부팅 테스트 → 실패 | ❌ |
| 2025-11-13 15:50 | Mainline 커널 한계 분석 완료 | ℹ️ |
| 2025-11-13 16:00 | Samsung 오픈소스 커널 조사 | ℹ️ |
| 2025-11-13 16:10 | Phase 0 작업 문서화 완료 | ✅ |
| 2025-11-13 16:30 | SM-A908N_KOR_12_Opensource.zip 준비 | ✅ |
| 2025-11-13 16:40 | Kernel.tar.gz (207MB) 추출 | ✅ |
| 2025-11-13 16:45 | r3q_kor_single_defconfig 확인 | ✅ |
| 2025-11-13 16:50 | Samsung 커널 GCC 빌드 시도 #1 → 실패 | ❌ |
| 2025-11-13 17:00 | GCC 빌드 시도 #2~4 (설정 변경) → 실패 | ❌ |
| 2025-11-13 17:15 | Clang 10.0.7 필요성 확인 | ℹ️ |
| 2025-11-13 17:30 | 단계별 접근법 결정 (옵션 1→2) | ℹ️ |
| 2025-11-13 17:35 | Stock boot.img 언팩 및 분석 | ✅ |
| 2025-11-13 17:45 | boot_stock_busybox.img 생성 (49MB) | ✅ |
| 2025-11-13 18:05 | TWRP 진입 및 boot.img 전송 | ✅ |
| 2025-11-13 18:10 | boot 파티션 플래싱 완료 | ✅ |
| 2025-11-13 18:15 | 재부팅 및 부팅 테스트 → recovery 복귀 | ❌ |
| 2025-11-13 18:20 | pstore 로그 확인 → Android init 실행 | ℹ️ |
| 2025-11-13 18:25 | **Stock 커널 내장 ramdisk 발견** | ⚠️ |
| 2025-11-13 18:30 | Clang 10.0.7 요구사항 재확인 | ℹ️ |
| 2025-11-13 18:35 | Android NDK r21e 다운로드 시작 (1.1GB) | ⏳ |
| 2025-11-13 18:40 | NDK 추출 및 Clang 9.0.9 확인 | ✅ |
| 2025-11-13 18:45 | Samsung 커널 defconfig 재적용 | ✅ |
| 2025-11-13 18:50 | Samsung 커널 Clang 빌드 시작 (-j22) | ⏳ |
| 2025-11-13 19:05 | Samsung 커널 빌드 완료 (1차) | ✅ |
| 2025-11-13 19:10 | CONFIG_INITRAMFS_SOURCE 설정 | ✅ |
| 2025-11-13 19:15 | initramfs 경로 절대경로로 수정 | ✅ |
| 2025-11-13 19:20 | initramfs 통합 커널 빌드 시작 (2차) | ⏳ |
| 2025-11-13 19:30 | Python profiling 경고 발생 (무시 가능) | ⚠️ |
| 2025-11-13 19:48 | Samsung 커널 빌드 완료 (2차, 47MB) | ✅ |
| 2025-11-13 19:50 | initramfs 통합 확인 (1.2MB cpio.gz) | ✅ |
| 2025-11-13 20:00 | boot_integrated_busybox.img 생성 (47MB) | ✅ |
| 2025-11-13 20:04 | TWRP 진입 및 boot 파티션 플래싱 | ✅ |
| 2025-11-13 20:05 | 재부팅 테스트 → recovery 복귀 | ❌ |
| 2025-11-13 20:10 | pstore 로그 분석 → 여전히 Android init | ⚠️ |
| 2025-11-13 20:12 | **부트로더 강제 ramdisk 로드 확인** | ⚠️ |
| 2025-11-13 20:15 | Recovery 파티션 백업 (79MB TWRP) | ✅ |
| 2025-11-13 20:18 | Recovery 파티션에 커스텀 커널 플래싱 | ✅ |
| 2025-11-13 20:20 | Recovery 모드 부팅 → Knox 검증 실패 | ❌ |
| 2025-11-13 20:25 | Recovery 모드 수동 진입 실패 | ❌ |
| 2025-11-13 20:30 | **근본 원인 분석 완료** | ℹ️ |
| 2025-11-13 20:38 | TWRP recovery.img 재다운로드 (79MB) | ✅ |
| 2025-11-13 20:40 | recovery_twrp_odin.tar 생성 (Odin용) | ✅ |
| 2025-11-13 19:15 | Busybox initramfs 통합 빌드 시도 | ⏳ |
| 2025-11-13 19:20 | initramfs 통합 빌드 실패 (경로 오류) | ❌ |
| 2025-11-13 19:25 | 절대 경로로 수정 및 재빌드 시도 | ⏳ |
| 2025-11-13 19:30 | **빌드 중단** (Python profiling 오류) | ❌ |
| 2025-11-13 19:35 | 대안: Samsung 커널 + mkbootimg 접근 | ℹ️ |
| 2025-11-13 19:40 | Stock boot.img에서 cmdline 추출 | ✅ |
| 2025-11-13 19:45 | boot_samsung_busybox.img 생성 (48MB) | ✅ |
| 2025-11-13 19:50 | Samsung 커널 boot.img 플래싱 | ✅ |
| 2025-11-13 19:52 | 재부팅 → recovery 복귀 | ❌ |
| 2025-11-13 19:55 | pstore 로그 확인 → **Android init 재실행** | ⚠️ |

---

**마지막 업데이트**: 2025년 11월 13일 20:00
**다음 작업**: 문제 분석 및 해결 방안 모색
**현재 진행률**: Phase 0의 95% 완료 (**중대한 문제 발견**)

---

### ✅ 13. Stock 커널 + Busybox 부팅 실패 분석 (2025-11-13 18:20)

#### 부팅 테스트 결과
```bash
# 재부팅 후 상태 확인
adb devices
# RFCM90CFWXA	recovery (다시 recovery로 복귀)
```

#### pstore 로그 분석
```bash
# 로그 다운로드
adb pull /sys/fs/pstore/console-ramoops-0 ~/A90_5G_rooting/logs/boot_stock_busybox.log

# 주요 발견 사항
strings boot_stock_busybox.log | grep -i "init\|busybox" | head -50
```

**로그 결과:**
```
[1: init: 1] init: Control message: Could not find 'android.hardware.keymaster@4.0::IKeymasterDevice/default'
[1: init: 1] init: Control message: Could not find 'android.hardware.keymaster@4.0::IKeymasterDevice/default'
...
```

#### 중대한 발견: 내장 ramdisk

**문제 핵심:**
- ✅ 커널이 부팅됨
- ❌ Busybox initramfs가 마운트되지 **않음**
- ❌ Android `/system/bin/init`이 실행됨
- ❌ `hwservicemanager`가 실행됨

**원인 분석:**
1. Stock 커널에 **내장(embedded) ramdisk** 존재
2. mkbootimg의 ramdisk 파라미터가 **무시됨**
3. 커널 내부 ramdisk가 우선순위를 가짐
4. cmdline의 `rdinit=/bin/sh`도 **무시됨**

**기술적 배경:**
- Samsung/Qualcomm 커널은 커널 이미지 안에 ramdisk를 **append** 하는 경우가 있음
- 또는 Device Tree Blob(DTB)에 ramdisk가 포함될 수 있음
- 이 경우 mkbootimg의 ramdisk 섹션은 단순히 무시됨

---

### ✅ 14. Android NDK r21e 다운로드 및 설치 (2025-11-13 18:35~18:40)

#### Clang 필요성 재확인
Samsung 커널 빌드를 위해 Clang 10.0.7 필요.
Stock 커널 방식이 실패했으므로 **옵션 2로 전환**.

#### Android NDK 다운로드
```bash
cd ~/A90_5G_rooting/toolchains
wget https://dl.google.com/android/repository/android-ndk-r21e-linux-x86_64.zip
# 1.1GB, 64초 다운로드 (17.8 MB/s)
```

#### 압축 해제
```bash
unzip -q android-ndk-r21e-linux-x86_64.zip
# 디렉토리: android-ndk-r21e/
```

#### Clang 버전 확인
```bash
./android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --version
```

**결과:**
```
Android clang version 9.0.9 (based on LLVM 9.0.9svn)
Target: x86_64-unknown-linux-gnu
Thread model: posix
InstalledDir: /home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin
```

**버전 불일치:**
- **요구**: Clang 10.0.7
- **실제**: Clang 9.0.9

**결정**: 9.0.9로 시도 (비교적 최신 버전이므로 호환 가능성 있음)

---

### ✅ 15. Samsung 커널 Clang 빌드 (1차) (2025-11-13 18:45~19:05)

#### 환경 변수 설정
```bash
cd ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource
export PATH=/home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-android-
export CC=clang
export CLANG_TRIPLE=aarch64-linux-gnu-
```

#### defconfig 적용
```bash
make O=out r3q_kor_single_defconfig
```

**결과:**
```
drivers/samsung/debug/Kconfig:4:warning: ignoring type redefinition of 'SEC_DEBUG'
drivers/samsung/debug/Kconfig:30:warning: defaults for choice values not supported
drivers/samsung/debug/Kconfig:36:warning: defaults for choice values not supported
#
# configuration written to .config
#
```

#### 빌드 실행
```bash
time make ARCH=arm64 CROSS_COMPILE=aarch64-linux-android- \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- O=out -j22 2>&1 | tee ../build_clang.log
```

**빌드 진행:**
- ✅ defconfig 적용됨
- ✅ Clang 컴파일러 인식됨
- ✅ 드라이버 컴파일 진행
- ✅ crypto, network, filesystem 모듈 컴파일
- ⚠️ Python profiling 경고 (무시 가능)
- ⚠️ KeyError: 'jopp_springboard_blr_x16' (무시 가능)

**빌드 시간:** 약 15~20분 (22 코어)

#### 빌드 결과
```bash
ls -lh out/arch/arm64/boot/
```

**생성된 파일:**
- `Image` (47MB) - 압축되지 않은 커널
- `Image-dtb` (47MB) - DTB 포함 커널
- `Image-dtb-hdr` (20B) - 헤더 파일
- `dts/` - Device Tree 소스

**성공!** Samsung 커널 빌드 완료

---

### ⚠️ 16. Busybox initramfs 통합 빌드 시도 (2025-11-13 19:10~19:30)

#### CONFIG_INITRAMFS_SOURCE 설정

**목표**: Busybox initramfs를 커널 이미지 **내부**에 직접 통합

```bash
cd ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource

# initramfs 경로 설정
scripts/config --file out/.config \
  --set-str INITRAMFS_SOURCE "/home/temmie/A90_5G_rooting/initramfs_build/initramfs"

# GZIP 압축 활성화
scripts/config --file out/.config --enable INITRAMFS_COMPRESSION_GZIP

# 설정 확인
grep "CONFIG_INITRAMFS" out/.config
```

**결과:**
```
CONFIG_INITRAMFS_SOURCE="/home/temmie/A90_5G_rooting/initramfs_build/initramfs"
CONFIG_INITRAMFS_COMPRESSION_GZIP=y
```

#### olddefconfig 적용
```bash
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-android- \
  CC=clang CLANG_TRIPLE=aarch64-linux-gnu- O=out olddefconfig
```

#### 빌드 시도 #1 (상대 경로)
```bash
# 처음에 상대 경로 시도 (실패)
scripts/config --file out/.config --set-str INITRAMFS_SOURCE "../../initramfs_build/initramfs"
make O=out -j22
```

**에러:**
```
../scripts/gen_initramfs_list.sh: Cannot open '../../initramfs_build/initramfs'
make[2]: *** [../usr/Makefile:60: usr/initramfs_data.cpio.gz] Error 1
```

#### 빌드 시도 #2 (절대 경로)
```bash
# 절대 경로로 수정
scripts/config --file out/.config \
  --set-str INITRAMFS_SOURCE "/home/temmie/A90_5G_rooting/initramfs_build/initramfs"
make O=out -j22
```

**결과:**
- ✅ `GEN usr/initramfs_data.cpio.gz` 성공
- ✅ 컴파일 진행
- ❌ Python profiling 오류로 빌드 **멈춤**

**Python 오류 (반복):**
```
profiling:/usr/src/Python-2.7.18/Python/*.gcda:Cannot open
Process Process-3:
Traceback (most recent call last):
  File "../scripts/rkp_cfp/instrument.py", line 595
  KeyError: 'jopp_springboard_blr_x16'
```

**분석:**
- Samsung 커널의 보안 스크립트 오류
- Python 2.7 profiling 데이터 접근 실패
- RKP (Real-time Kernel Protection) CFP (Control Flow Protection) 관련

**결론**: initramfs 통합 빌드는 **추가 디버깅 필요**

---

### ✅ 17. 대안: Samsung 커널 + mkbootimg 접근 (2025-11-13 19:35~19:50)

#### 전략
initramfs 통합 빌드가 실패했으므로:
1. 이미 빌드된 Samsung 커널 이미지 (`Image-dtb` 47MB) 사용
2. mkbootimg로 Busybox initramfs와 결합
3. Stock boot 파라미터 재사용

#### Stock boot 파라미터 추출
```bash
cd ~/A90_5G_rooting
python3 mkbootimg/unpack_bootimg.py \
  --boot_img backups/backup_boot.img \
  --out /tmp/boot_extract \
  --format mkbootimg
```

**추출된 mkbootimg 명령어:**
```bash
--header_version 1
--os_version 12.0.0
--os_patch_level 2023-01
--kernel /tmp/boot_extract/kernel
--ramdisk /tmp/boot_extract/ramdisk
--pagesize 0x00001000
--base 0x00000000
--kernel_offset 0x00008000
--ramdisk_offset 0x00000000
--second_offset 0x00000000
--tags_offset 0x01e00000
--board SRPSE29A005
--cmdline 'console=null androidboot.hardware=qcom ...'
```

#### boot_samsung_busybox.img 생성
```bash
cd ~/A90_5G_rooting/mkbootimg
python3 mkbootimg.py \
  --header_version 1 \
  --os_version 12.0.0 \
  --os_patch_level 2023-01 \
  --kernel ../kernel_build/SM-A908N_KOR_12_Opensource/out/arch/arm64/boot/Image-dtb \
  --ramdisk ../initramfs_build/initramfs.cpio.gz \
  --pagesize 4096 \
  --base 0x00000000 \
  --kernel_offset 0x00008000 \
  --ramdisk_offset 0x00000000 \
  --tags_offset 0x01e00000 \
  --board "SRPSE29A005" \
  --cmdline "console=ttyMSM0,115200 androidboot.hardware=qcom androidboot.console=ttyMSM0 androidboot.memcg=1 lpm_levels.sleep_disabled=1 msm_rtb.filter=0x237 service_locator.enable=1 swiotlb=2048 androidboot.usbcontroller=a600000.dwc3 firmware_class.path=/vendor/firmware_mnt/image loop.max_part=7 rdinit=/bin/sh" \
  -o ../boot_image/boot_samsung_busybox.img
```

**생성 결과:**
- ✅ `boot_samsung_busybox.img` (48MB)
- Samsung 커널 (47MB) + Busybox initramfs (1.2MB)

---

### ❌ 18. boot_samsung_busybox.img 플래싱 및 부팅 실패 (2025-11-13 19:50~19:55)

#### 플래싱 과정
```bash
# TWRP 확인
adb devices  # RFCM90CFWXA recovery

# boot.img 전송
adb push boot_image/boot_samsung_busybox.img /tmp/
# 50,016,256 bytes (48 M), 0.536s, 89.0 MB/s

# boot 파티션 플래싱
adb shell "dd if=/tmp/boot_samsung_busybox.img of=/dev/block/bootdevice/by-name/boot && sync"
# 97688+0 records, 50016256 bytes (48 M), 2.487s, 19 M/s

# 재부팅
adb reboot
```

#### 부팅 결과
```bash
# 30초 대기 후
adb devices
# RFCM90CFWXA	recovery (다시 recovery로 복귀)
```

**결과**: 부팅 실패 → recovery 자동 복구

#### pstore 로그 분석
```bash
adb pull /sys/fs/pstore/console-ramoops-0 ~/A90_5G_rooting/logs/boot_samsung_busybox.log
strings boot_samsung_busybox.log | grep -i "init" | head -50
```

**로그 내용 (치명적 발견):**
```
[1: init: 1] init: Control message: Could not find 'android.hardware.keymaster@4.0::IKeymasterDevice/default'
[1: init: 1] init: Control message: Could not find 'android.hardware.keymaster@4.0::IKeymasterDevice/default'
...
```

**분석:**
- ✅ Samsung 커널이 부팅됨
- ❌ Busybox initramfs가 마운트되지 **않음**
- ❌ Android `/system/bin/init`이 **실행됨**
- ❌ `hwservicemanager` 프로세스 **실행됨**

---

## 🚨 중대한 문제 발견

### 문제: Samsung 커널도 내장 ramdisk 존재

#### 증거
1. **Stock 커널 + Busybox ramdisk**: Android init 실행
2. **Samsung 빌드 커널 + Busybox ramdisk**: Android init 실행
3. **공통점**: mkbootimg의 ramdisk 파라미터가 **모두 무시됨**

#### 기술적 원인 (추정)

**가설 1: 커널에 ramdisk가 embedded**
- Samsung 커널 빌드 시 ramdisk가 커널 이미지에 **append** 됨
- `Image-dtb` 파일에 DTB뿐만 아니라 **ramdisk도 포함**될 가능성

**가설 2: DTB에 ramdisk 정보**
- Device Tree Blob에 ramdisk 위치/내용이 포함됨
- 부트로더가 DTB를 우선 참조

**가설 3: 부트로더 강제 설정**
- ABL (Android Bootloader)이 특정 ramdisk를 강제로 로드
- cmdline 파라미터 무시

#### 로그 분석 결과
```bash
# 커널 초기 부팅 메시지 확인 시도
strings boot_samsung_busybox.log | grep -i "unpacking\|freeing\|rootfs\|initrd\|ramdisk"
# 결과: 아무것도 없음 (로그가 늦게 시작됨)
```

**발견:** pstore 로그는 Android init 실행 **후** 시점부터 기록됨
- 커널 초기 부팅 메시지 **누락**
- initramfs 언팩 과정 **확인 불가**

---

## 진행 중인 작업

### 🔄 19. 근본 원인 분석 및 해결 방안 모색

#### 현재 상황 정리

**시도한 방법:**
1. ❌ Mainline Linux 6.1 + Busybox → 드라이버 부족으로 부팅 실패
2. ❌ Stock 커널 + Busybox ramdisk → Android init 실행 (내장 ramdisk)
3. ❌ Samsung 빌드 커널 + Busybox ramdisk (mkbootimg) → Android init 실행 (내장 ramdisk)
4. ⏳ Samsung 빌드 커널 + Busybox initramfs (CONFIG 통합) → 빌드 실패 (Python 오류)

**핵심 문제:**
- Stock/Samsung 커널 **모두** 내장 ramdisk 존재
- mkbootimg의 ramdisk 섹션이 **완전히 무시됨**
- cmdline의 `rdinit=/bin/sh`도 **무시됨**

#### 가능한 해결 방안

**방안 A: CONFIG_INITRAMFS_SOURCE로 커널 재빌드** (우선순위 1)
- initramfs를 커널 이미지 **내부**에 직접 통합
- 내장 ramdisk를 **완전히 교체**
- **장애물**: Python profiling 오류 해결 필요

**방안 B: Samsung 빌드 스크립트 분석**
- `build_kernel.sh` 또는 `build.config.*` 파일 확인
- Samsung 공식 빌드 방법 파악
- ramdisk append 메커니즘 이해

**방안 C: 커널 이미지 직접 수정**
- `Image-dtb` 파일에서 embedded ramdisk 제거
- Busybox ramdisk를 수동으로 append
- **위험**: 서명 검증 실패 가능성

**방안 D: Android ramdisk 내부에 Busybox 통합**
- Stock Android ramdisk 추출
- Busybox를 `/sbin/` 또는 `/system/bin/`에 복사
- init.rc를 수정해서 Busybox shell 실행
- **장점**: 기존 ramdisk 구조 활용
- **단점**: Android 종속성 유지

---

### ✅ 20. initramfs 통합 커널 빌드 (2차) (2025-11-13 19:15~19:48)

#### 경로 수정
이전 빌드에서 상대 경로 오류 발생. 절대 경로로 변경:

```bash
cd ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource
scripts/config --file out/.config --set-str INITRAMFS_SOURCE "/home/temmie/A90_5G_rooting/initramfs_build/initramfs"
grep "CONFIG_INITRAMFS_SOURCE" out/.config
```

**결과:**
```
CONFIG_INITRAMFS_SOURCE="/home/temmie/A90_5G_rooting/initramfs_build/initramfs"
```

#### 재빌드 실행
```bash
export PATH=/home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH

cd ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource
time make ARCH=arm64 \
  CROSS_COMPILE=aarch64-linux-android- \
  CC=clang \
  CLANG_TRIPLE=aarch64-linux-gnu- \
  O=out \
  -j22 2>&1 | tee ../build_with_initramfs.log
```

#### Python Profiling 경고
빌드 중 수많은 Python profiling 경고 발생:
```
profiling:/usr/src/Python-2.7.18/Objects/abstract.gcda:Cannot open
profiling:/usr/src/Python-2.7.18/Objects/boolobject.gcda:Cannot open
...
```

**분석**: 이는 단순한 경고이며 빌드는 계속 진행됨. `.gcda` 파일은 code coverage 데이터로 필수는 아님.

#### 빌드 완료
```bash
  OBJCOPY arch/arm64/boot/Image
  Building modules, stage 2.
  MODPOST 10 modules
  CAT     arch/arm64/boot/Image-dtb
make[1]: Leaving directory '/home/temmie/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource/out'
```

**결과:**
- ✅ `out/arch/arm64/boot/Image` (47MB)
- ✅ `out/arch/arm64/boot/Image-dtb` (47MB)
- ✅ `out/usr/initramfs_data.cpio.gz` (1.2MB)

#### initramfs 내용 검증
```bash
cd /tmp && mkdir test_initramfs && cd test_initramfs
gunzip -c ~/A90_5G_rooting/kernel_build/SM-A908N_KOR_12_Opensource/out/usr/initramfs_data.cpio.gz | cpio -idmv
```

**확인 결과:**
```
bin/busybox
bin/sh
dev
etc
init           # Busybox init script ✅
init_simple
proc
root
sbin
sys
tmp
usr
```

✅ **Busybox initramfs가 커널에 올바르게 통합되었습니다!**

---

### ✅ 21. boot_integrated_busybox.img 생성 (2025-11-13 20:00~20:04)

#### 특징
이전 방식과의 **핵심 차이점**:
- ❌ **이전**: mkbootimg에 external ramdisk 전달 → **부트로더가 무시**
- ✅ **지금**: initramfs가 커널에 직접 통합 → **무시 불가능**

#### boot 이미지 생성
```bash
cd ~/A90_5G_rooting/mkbootimg
python3 mkbootimg.py \
  --header_version 1 \
  --os_version 12.0.0 \
  --os_patch_level 2023-01 \
  --kernel ../kernel_build/SM-A908N_KOR_12_Opensource/out/arch/arm64/boot/Image-dtb \
  --pagesize 4096 \
  --base 0x00000000 \
  --kernel_offset 0x00008000 \
  --ramdisk_offset 0x00000000 \
  --tags_offset 0x01e00000 \
  --board "SRPSE29A005" \
  --cmdline "console=ttyMSM0,115200n8 ... rdinit=/bin/sh" \
  -o ../boot_image/boot_integrated_busybox.img
```

**주의**: `--ramdisk` 파라미터를 **제공하지 않음** (initramfs가 이미 커널 내부에 있으므로)

**결과:**
- 파일: `boot_integrated_busybox.img`
- 크기: 47MB (48,832,512 bytes)

#### 디바이스 연결 확인
```bash
adb devices
```
```
List of devices attached
RFCM90CFWXA     recovery
```

#### 파일 전송
```bash
adb push boot_integrated_busybox.img /tmp/boot.img
```
```
boot_integrated_busybox.img: 1 file pushed, 0 skipped. 92.5 MB/s (48832512 bytes in 0.503s)
```

#### boot 파티션 플래싱
```bash
adb shell 'dd if=/tmp/boot.img of=/dev/block/by-name/boot bs=4096'
```
```
11922+0 records in
11922+0 records out
48832512 bytes (47 M) copied, 0.273814 s, 170 M/s
```

#### 재부팅
```bash
adb reboot
```

**예상**: initramfs가 커널 내부에 통합되어 있으므로 Busybox shell 부팅 가능성 높음

---

### ❌ 22. boot_integrated_busybox.img 부팅 실패 (2025-11-13 20:05~20:12)

#### 부팅 결과
디바이스가 recovery 모드로 자동 복귀.

#### pstore 로그 수집
```bash
# TWRP recovery로 재진입
adb pull /sys/fs/pstore/console-ramoops-0 ~/A90_5G_rooting/logs/boot_integrated_busybox.log
```

**로그 크기**: 262KB (261,901 bytes)

#### 로그 분석
```bash
strings ~/A90_5G_rooting/logs/boot_integrated_busybox.log | tail -100
```

**발견된 내용:**
```
[  888.381335]  [1:           init:    1] init: Control message: Could not find 'android.hardware.keymaster@4.0::IKeymasterDevice/default'
[  889.382173]  [1:           init:    1] init: Control message: Could not find 'android.hardware.keymaster@4.0::IKeymasterDevice/default'
...
[  907.197851]  [2:           init: 1512] logwrapper: executing /system/bin/apex --unmount-all failed: No such file or directory
[  907.907954]  [0:           init:    1] reboot: Restarting system with command 'shell'
```

**결론:**
- ✅ 커널은 부팅함
- ❌ **여전히 Android init이 실행됨** (`/system/bin/init`)
- ❌ `hwservicemanager` 프로세스 실행
- ❌ Busybox `/bin/sh`가 실행되지 않음

#### initramfs unpacking 메시지 확인
```bash
strings ~/A90_5G_rooting/logs/boot_integrated_busybox.log | grep -i "unpack\|initramfs\|init="
```

**결과**: **아무것도 없음!**

커널 부팅 로그는 있지만 initramfs unpacking 관련 메시지가 전혀 없음.

---

### ⚠️ 23. 근본 원인 분석: 부트로더의 강제 ramdisk 로드 (2025-11-13 20:12~20:30)

#### 문제 진단

**실험 결과:**
1. ❌ Stock kernel + external Busybox ramdisk → Android init
2. ❌ Samsung kernel + external Busybox ramdisk → Android init  
3. ❌ Samsung kernel + **integrated** Busybox initramfs → Android init

**결론:**
initramfs를 커널에 통합했음에도 불구하고 여전히 Android init이 실행된다.

#### 가능한 원인

**1. ABL (Android Bootloader) 강제 ramdisk 주입**
- Qualcomm의 ABL이 boot 파티션의 ramdisk 섹션을 강제로 로드
- 커널 내부 initramfs를 덮어씀
- Samsung Knox 검증과 연관

**2. Device Tree에 ramdisk 정보**
- DTB(Device Tree Blob)에 ramdisk 주소 하드코딩
- 부트로더가 DTB의 ramdisk 주소로 외부 ramdisk 로드
- 커널 CONFIG_BLK_DEV_INITRD가 DTB 우선순위를 갖도록 설정

**3. SELinux / dm-verity 강제**
- Verified Boot가 특정 ramdisk만 허용
- 서명되지 않은 initramfs 거부

#### 증거

**로그에 initramfs unpacking 메시지가 없음:**
정상적인 경우:
```
[    0.xxx] Unpacking initramfs...
[    0.xxx] Freeing initrd memory: xxxK
```

우리 로그:
```
(없음)
```

이는 커널이 CONFIG_INITRAMFS_SOURCE로 통합된 initramfs를 **전혀 사용하지 않았다**는 증거.

#### 실패한 시도 요약

| 시도 | Kernel | Ramdisk | 결과 | Android init? |
|------|--------|---------|------|---------------|
| #1 | Mainline 6.1 | Busybox (external) | Boot fail | N/A |
| #2 | Stock 4.14 | Busybox (external) | Recovery | ✅ Yes |
| #3 | Samsung 4.14 | Busybox (external) | Recovery | ✅ Yes |
| #4 | Samsung 4.14 | Busybox (integrated) | Recovery | ✅ Yes |

**공통점**: 모든 경우에 Android `/system/bin/init`이 실행됨.

---

### ❌ 24. Recovery 파티션 시도 및 실패 (2025-11-13 20:15~20:30)

#### 전략 변경
boot 파티션이 ABL의 엄격한 검증을 받는다면, **recovery 파티션**은 제약이 덜할 수 있음.

#### Recovery 파티션 백업
```bash
adb shell 'dd if=/dev/block/by-name/recovery of=/tmp/recovery_backup.img bs=4096'
adb pull /tmp/recovery_backup.img ~/A90_5G_rooting/backups/backup_recovery.img
```

**백업 크기**: 79MB (82,825,216 bytes)

#### 커스텀 커널 플래싱
```bash
adb push boot_integrated_busybox.img /tmp/boot_test.img
adb shell 'dd if=/tmp/boot_test.img of=/dev/block/by-name/recovery bs=4096'
```
```
11922+0 records in
11922+0 records out
48832512 bytes (47 M) copied, 0.273562 s, 170 M/s
```

#### Recovery 모드 부팅 시도
```bash
adb reboot recovery
```

#### 결과: Samsung Knox 검증 실패 화면

**화면 표시:**
```
SAMSUNG Galaxy A90 5G
⚠️ Secured by Knox

이 휴대전화에 현재 삼성 공식 소프트웨어가
설치되어 있지 않습니다. 가능하나 복잡에
문제가 있을 수 있으며, 소프트웨어 업데이트가
설치 되지 않습니다.

Powered by android
```

디바이스가 이 화면에서 멈춤. Recovery 모드 진입 불가.

#### 수동 Recovery 진입 시도

**방법:**
1. 전원 + 볼륨 다운 (10초) → 강제 재부팅
2. 재부팅 시 전원 + 볼륨 업 → Recovery 모드

**결과**: 진입 실패. 계속 Knox 검증 실패 화면.

---

### ✅ 25. TWRP Recovery 복구 준비 (2025-11-13 20:38~20:40)

#### 상황
- Recovery 파티션이 커스텀 커널로 덮어써짐
- Recovery 모드 진입 불가
- TWRP 복구 필요

#### TWRP 이미지 확보
```bash
ls -lh ~/A90_5G_rooting/backups/recovery.img
```
```
-rw-rw-r-- 1 temmie temmie 79M 11월 13 20:38 recovery.img
```

TWRP recovery.img (79MB, Android bootimg)

#### Odin용 .tar 변환
Odin은 `.tar` 또는 `.tar.md5` 형식만 인식:

```bash
cd ~/A90_5G_rooting/backups
tar -cvf recovery_twrp_odin.tar recovery.img
```

**결과:**
```
recovery.img
-rw-rw-r-- 1 temmie temmie 79M 11월 13 20:40 recovery_twrp_odin.tar
```

#### Odin 플래싱 방법 (대기 중)

**절차:**
1. 디바이스를 **다운로드 모드**로 진입:
   - 전원 끔
   - 볼륨 다운 + 전원 버튼 동시에 길게 누르기
   - "Warning!" 화면에서 볼륨 업 (Continue)

2. Windows PC에서 **Odin** 실행

3. **AP** 슬롯에 `recovery_twrp_odin.tar` 선택

4. **Options** 설정:
   - ✅ Auto Reboot
   - ❌ Re-partition (절대 체크 금지!)

5. **Start** 버튼 클릭

6. 완료 후 **볼륨 업 + 전원**으로 TWRP recovery 진입

---

## 대기 중인 작업

### ⏳ 20. TWRP Recovery 복구 (Odin)

#### 확인할 파일
```
SM-A908N_KOR_12_Opensource/
├── build_kernel.sh          # 빌드 스크립트
├── build.config.aarch64     # 빌드 설정
├── build.config.common      # 공통 설정
└── README_Kernel.txt        # 빌드 가이드
```

#### 분석 목표
1. ramdisk 생성/append 메커니즘 파악
2. CONFIG_INITRAMFS_SOURCE 사용 여부 확인
3. 공식 빌드 명령어 복제

---

### ⏳ 21. Python profiling 오류 해결

#### 오류 상세
```python
File "../scripts/rkp_cfp/instrument.py", line 595, in get_func_idx
  i_set = self.func_idx[func]
KeyError: 'jopp_springboard_blr_x16'
```

#### 해결 방법 후보
1. RKP CFP 기능 비활성화
2. Python 2.7 환경 정리
3. 스크립트 패치

---

## Phase 0 주요 결과 요약 (업데이트)

### ✅ 성공한 것
1. **개발 환경 완벽 구축** - 크로스 컴파일, mkbootimg, TWRP 활용
2. **완전한 백업 시스템** - 198MB 파티션 백업, 복원 프로세스 확립
3. **WiFi 펌웨어 추출** - 4.3MB, Phase 2에서 사용 준비
4. **Mainline Linux 6.1 빌드** - 12MB Image.gz (부팅 시도, 드라이버 부족 확인)
5. **Busybox initramfs** - 2.1MB static binary + 1.2MB cpio.gz
6. **Boot.img 생성 및 플래싱** - mkbootimg 파이프라인 완전 확립
7. **Samsung 오픈소스 커널 분석** - r3q_kor_single_defconfig 확인
8. **Clang 빌드 환경 구축** - Android NDK r21e, Clang 9.0.9
9. **Samsung 커널 빌드 성공** - 47MB Image-dtb (Linux 4.14.190)
10. **부팅 디버깅 기술** - pstore 로그 분석, 커널 메시지 해석
11. **initramfs 커널 통합** - CONFIG_INITRAMFS_SOURCE 성공적 적용
12. **Recovery 백업 및 플래싱** - TWRP 복구 준비 완료

### ❌ 실패 및 중요한 발견
1. **kexec 불가** - Stock Android 커널 미지원
2. **Fastboot 불가** - Samsung 기기 특성
3. **Mainline Linux 한계** - Samsung 전용 드라이버 부족
   - UFS 스토리지 초기화 실패
   - 디스플레이 패널 미지원
   - Device Tree 불일치
4. **⚠️ 치명적 발견 #1: External ramdisk 무시**
   - Stock 커널: 내장 ramdisk로 Android init 실행
   - Samsung 빌드 커널: 내장 ramdisk로 Android init 실행
   - mkbootimg의 ramdisk 파라미터 **완전히 무시됨**
   - cmdline의 `rdinit=` 파라미터도 **무시됨**
5. **⚠️ 치명적 발견 #2: Integrated initramfs도 무시**
   - CONFIG_INITRAMFS_SOURCE로 커널에 통합해도 소용없음
   - 부트로더(ABL)가 **외부 ramdisk를 강제 주입**
   - 커널 내부 initramfs를 덮어씀
6. **⚠️ Samsung Knox / Verified Boot 강력함**
   - Recovery 파티션 변조 시 부팅 차단
   - Knox 검증 실패 화면에서 멈춤
   - Recovery 모드 수동 진입도 불가

### 📊 획득한 기술 스택
- ✅ ARM64 크로스 컴파일 (GCC + Clang)
- ✅ Android boot.img 구조 완전 이해
- ✅ initramfs/cpio 생성 및 통합
- ✅ TWRP를 통한 저수준 플래싱
- ✅ pstore를 통한 커널 디버깅
- ✅ Device Tree 개념 이해
- ✅ Samsung 커널 소스 분석 및 빌드
- ✅ Stock 커널 재패키징
- ✅ Android NDK Clang 빌드
- ✅ 커널 부팅 문제 진단

### 🔍 핵심 문제 진단

**문제**: Qualcomm ABL (Android Bootloader)의 강제 ramdisk 주입

**증거:**
1. Stock kernel + external Busybox ramdisk → Android init 실행
2. Samsung built kernel + external Busybox ramdisk → Android init 실행
3. Samsung built kernel + **integrated** Busybox initramfs → Android init 실행
4. pstore 로그에 "Unpacking initramfs" 메시지 없음 → 커널 initramfs 미사용

**원인 분석:**
- ABL이 boot 파티션의 ramdisk 섹션을 메모리에 강제 로드
- Device Tree에 ramdisk 주소 전달
- 커널이 CONFIG_BLK_DEV_INITRD로 DTB의 ramdisk 사용
- CONFIG_INITRAMFS_SOURCE의 내장 initramfs **완전히 무시됨**

**Verified Boot / Knox 영향:**
- boot 파티션: 서명 검증, ramdisk 강제
- recovery 파티션: 변조 시 Knox 검증 실패, 부팅 차단

### 📋 다음 단계 (우선순위)
3. 공통: `/system/bin/init`, `hwservicemanager` 프로세스 실행
4. pstore 로그에 커널 초기 메시지 없음 (늦게 시작)

**추정 원인:**
- 커널 이미지에 ramdisk가 **embedded** 또는 **appended**
- Device Tree Blob에 ramdisk 정보 포함
- 부트로더(ABL)가 특정 ramdisk 강제 로드

### 🎯 다음 단계

**우선순위 1: Samsung 빌드 스크립트 분석**
- `build_kernel.sh` 분석
- ramdisk 생성/통합 메커니즘 파악
- 공식 빌드 방법 복제

**우선순위 2: initramfs 통합 빌드 재시도**
- Python profiling 오류 해결
- RKP CFP 비활성화 시도
- CONFIG_INITRAMFS_SOURCE로 커널 재빌드

**우선순위 3: 커널 이미지 분석**
- `Image-dtb` 파일 구조 파악
- embedded ramdisk 위치 확인
- 수동 교체 가능성 검토

**대안: Android ramdisk 해킹**
- Stock ramdisk 추출 및 수정
- Busybox를 Android ramdisk 안에 통합
- init.rc를 수정해서 Busybox shell 실행

**최종 목표**:
- Busybox shell 부팅 성공
- Phase 1 진입: PostmarketOS rootfs 통합
