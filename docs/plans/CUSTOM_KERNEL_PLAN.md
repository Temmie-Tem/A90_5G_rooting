# Samsung Galaxy A90 5G (SM-A908N) 커스텀 커널 빌드 계획
## Phase 2 - Option 2: 커스텀 커널 최적화

**작성일**: 2025-11-16
**목표**: RAM 200MB 추가 절감 (1.41GB → 1.21GB PSS)
**현재 상태**: Phase 2 Option 1 완료 (235MB 절감)

---

## 📊 프로젝트 개요

### 현재 상황
- **Phase 1 완료**: Magisk Systemless Chroot (Debian, 11-20MB RAM)
- **Phase 2 Option 1 완료**: headless_boot_v2 Magisk 모듈
  - 163개 패키지 비활성화
  - SystemUI/Launcher 차단
  - RAM: 1.64GB → 1.41GB (235MB 절감)

### Option 2 목표
- **추가 RAM 절감**: 200MB
- **최종 목표**: 1.21GB PSS (또는 더 낮게)
- **방법**: 커스텀 커널 빌드 + 최적화
- **소요 시간**: 3-5시간 (작업) + 45-90분 (빌드)
- **위험도**: 낮음-중간 (백업 있음, 복구 가능)

---

## ✅ 이미 준비된 환경

### 1. 커널 소스
```
위치: /home/temmie/A90_5G_rooting/archive/phase0_native_boot_research/kernel_build/SM-A908N_KOR_12_Opensource/
커널 버전: Linux 4.14.190
Android 버전: 12.0.0
디바이스 코드: r3q (Galaxy A90 5G)
Defconfig: arch/arm64/configs/r3q_kor_single_defconfig (6,908 lines)
빌드 스크립트: build_kernel.sh (ready to use)
이전 빌드: Image-dtb 47MB (Phase 0에서 성공적으로 빌드됨)
```

### 2. 툴체인
```
Android NDK r21e: /home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/
Clang 버전: 9.0.9 (Android official toolchain)
GCC: aarch64-linux-android-4.9
타겟 아키텍처: ARM64 (aarch64)
상태: ✅ 검증됨, 사용 가능
```

### 3. 부팅 이미지 도구
```
mkbootimg: /home/temmie/A90_5G_rooting/mkbootimg/ (Python-based)
unpack_bootimg.py: ✅ Available
repack_bootimg.py: ✅ Available
```

### 4. 백업 파일 (중요!)
```
backup_boot.img: 64MB (Magisk 패치된 현재 부팅 이미지)
backup_recovery.img: 79MB (TWRP)
backup_abl.img: 4MB (부트로더 - 매우 중요!)
backup_efs.tar.gz: IMEI/MAC 주소 (절대 삭제 금지!)
backup_dtbo.img: 10MB
backup_vbmeta.img: 64KB
```

### 5. 빌드 환경
```
OS: Linux 6.14.0-35-generic (Ubuntu-based)
디스크 여유 공간: 106GB (충분)
필수 패키지: ✅ build-essential, bc, flex, bison, libssl-dev, libncurses-dev 설치됨
```

---

## 🎯 Option 2와 Option 3의 관계

### 핵심 발견
- **Option 2와 3은 상호 보완적** (mutually exclusive 아님)
- **겹치는 작업 60-70%** 존재
- **Option 2 → 3 순서 강력 권장**

### 공유 컴포넌트

| 컴포넌트 | Option 2 (커널) | Option 3 (AOSP) | 재사용 가능? |
|---------|-----------------|-----------------|--------------|
| Samsung 커널 소스 | ✅ 필수 | ✅ 필수 | 100% |
| Device Tree (.dtb) | ✅ 컴파일 | ✅ 동일 DTB 사용 | 100% |
| 커널 Config | ✅ 최적화 | ✅ AOSP에 통합 | 90% |
| 빌드 툴체인 | ✅ Clang/NDK | ✅ 동일 툴체인 | 100% |
| Boot Image | ✅ mkbootimg | ✅ ROM 빌드 포함 | 80% |
| WiFi 펌웨어 | ✅ 추출 및 테스트 | ✅ ROM에 복사 | 100% |

### 왜 Option 2를 먼저 해야 하는가?

1. **위험 관리**
   - 커널 실패: 10시간 손실 (복구 가능)
   - AOSP+커널 동시 실패: 100시간 손실 (치명적)

2. **점진적 가치**
   - Option 2만으로도 목표의 82% 달성 (1.21GB)
   - 유용한 결과물로 중단 가능
   - Option 2 없이 Option 3만: 100시간 투자해도 불확실

3. **학습 곡선**
   - 커널 디버깅 → ROM 디버깅 스킬 전수
   - Device tree 이해 → 두 옵션 모두 필수
   - 작은 범위에서 배우기 쉬움

4. **현재 상황**
   - 이미 목표의 86% 달성 (1.41GB / 1.0GB)
   - Option 2만으로도 충분할 수 있음

---

## 🛠️ 커널 최적화 전략

### A. 메모리 관리 최적화

#### 1. zRAM 설정 (고우선순위)
**현재 상태**: LZ4 압축 활성화됨
```bash
CONFIG_ZRAM=y
CONFIG_ZRAM_WRITEBACK=y
CONFIG_ZRAM_LRU_WRITEBACK=y
CONFIG_ZSMALLOC=y
```

**권장 변경**:
```bash
# Option 1: LZ4 유지 (빠름, 낮은 지연시간)
CONFIG_ZRAM_DEF_COMP_LZ4=y
CONFIG_ZRAM_DEF_COMP="lz4"

# Option 2: ZSTD로 전환 (더 좋은 압축, 20-30% 더 절감)
CONFIG_ZRAM_DEF_COMP_ZSTD=y
CONFIG_ZRAM_DEF_COMP="zstd"

# 런타임 튜닝 (Magisk 모듈에 추가):
echo 2G > /sys/block/zram0/disksize  # 크기 증가
```

**예상 절감**: 50-80MB

#### 2. SLUB 할당자 최적화
**현재**: `CONFIG_SLUB=y` (good)

**권장 변경**:
```bash
# 디버그 기능 비활성화 (10-20MB 절감)
# CONFIG_SLUB_DEBUG is not set
# CONFIG_SLABINFO is not set
# CONFIG_SLUB_CPU_PARTIAL is not set

# 극도의 메모리 절약 (임베디드 스타일)
# CONFIG_SLOB=y  # SLUB 대신 (5-10MB 절감, 더 느림)
```

**예상 절감**: 10-20MB

#### 3. Low Memory Killer (LMK) 튜닝
**방법**: 런타임 설정 (커널 config 아님)

**Magisk 모듈에 추가**:
```bash
# /data/local.prop or system.prop
ro.lmk.use_minfree_levels=true
ro.lmk.kill_heaviest_task=true
ro.config.low_ram=true  # 공격적인 메모리 관리 활성화
```

**예상 절감**: 20-40MB (간접적, 앱 빨리 종료)

### B. 드라이버 제거 (고영향)

#### 1. 카메라 드라이버 제거 (권장 - 사용 안함)
**현재**: 전체 활성화됨

**비활성화**:
```bash
# CONFIG_MEDIA_SUPPORT is not set
# CONFIG_MEDIA_CAMERA_SUPPORT is not set
# CONFIG_VIDEO_DEV is not set
# CONFIG_VIDEO_V4L2 is not set
# CONFIG_CAMERA_SYSFS_V2 is not set
```

**예상 절감**: 30-50MB RAM, 5-10MB 커널 크기

#### 2. 터치스크린 드라이버 (조건부)
**현재**: 40+ 터치스크린 드라이버 활성화됨

**물리적 터치스크린 유지 시**:
```bash
# 필요한 2개만 유지:
CONFIG_TOUCHSCREEN_IST40XX=y
CONFIG_TOUCHSCREEN_MELFAS_MSS100=y

# 나머지 40개 비활성화
```

**완전 헤드리스 (SSH만) 시**:
```bash
# CONFIG_INPUT_TOUCHSCREEN is not set  # 모두 비활성화
```

**예상 절감**: 15-25MB (완전 비활성화 시)

#### 3. 디스플레이/그래픽 최적화 (주의!)
**현재**: DRM과 Framebuffer 모두 활성화

**보수적 접근** (권장):
```bash
# 부트로더 호환성 위해 framebuffer 유지
CONFIG_FB=y
CONFIG_DRM=y

# 하지만 framebuffer 콘솔 비활성화 (RAM 절약)
# CONFIG_FRAMEBUFFER_CONSOLE is not set
# CONFIG_DRM_FBDEV_EMULATION is not set
```

**공격적 접근** (위험 - 부팅 실패 가능):
```bash
# 최소 framebuffer만
# CONFIG_DRM is not set
CONFIG_FB=y
CONFIG_FB_SIMPLE=y
```

**예상 절감**: 20-40MB

#### 4. 오디오 드라이버 (안전하게 비활성화 가능)
**현재**: 전체 오디오 스택 활성화됨

**비활성화**:
```bash
# CONFIG_SOUND is not set
# CONFIG_SND is not set
```

**예상 절감**: 15-25MB

### C. 디버깅 & 개발 기능 제거

```bash
# 커널 디버깅 비활성화 (프로덕션 커널)
# CONFIG_DEBUG_INFO is not set
# CONFIG_DEBUG_FS is not set
# CONFIG_DEBUG_KERNEL is not set
# CONFIG_SLUB_DEBUG is not set

# 트레이싱 비활성화
# CONFIG_FTRACE is not set
# CONFIG_TRACING is not set

# 프로파일링 비활성화
# CONFIG_PROFILING is not set
# CONFIG_OPROFILE is not set
```

**예상 절감**: 20-30MB 커널 크기, 10-15MB RAM

### D. 크기 최적화

```bash
# 성능 최적화에서 크기 최적화로 변경
# CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE is not set
CONFIG_CC_OPTIMIZE_FOR_SIZE=y

# 커널 바이너리 크기 20-30% 감소
# 트레이드오프: ~5-10% CPU 성능 손실 (헤드리스에서는 무시 가능)
```

**예상 절감**: 10-15MB 커널 크기, 5-10MB RAM

### E. 네트워크 최적화 (WiFi 보존!)

```bash
# 필수 WiFi 드라이버 유지
CONFIG_CFG80211=y
CONFIG_MAC80211=y
CONFIG_WLAN=y
CONFIG_QCA_CLD_WLAN=y  # Qualcomm WiFi (중요!)

# 불필요한 네트워크 기능 비활성화
# CONFIG_WIRELESS_EXT is not set
# CONFIG_WEXT_* is not set
# CONFIG_NETFILTER_ADVANCED is not set
```

**예상 절감**: 5-10MB

---

## 📊 예상 RAM 절감량

### 보수적 접근 (권장)

| 최적화 | 절감량 | 위험도 |
|--------|--------|--------|
| zRAM 튜닝 | 30MB | 낮음 ✅ |
| SLUB 최적화 | 10MB | 낮음 ✅ |
| 카메라 제거 | 30MB | 낮음 ✅ |
| 터치스크린 (기본 유지) | 5MB | 낮음 ✅ |
| 디스플레이 최적화 | 10MB | 낮음 ✅ |
| 오디오 제거 | 15MB | 낮음 ✅ |
| 디버그 제거 | 15MB | 낮음 ✅ |
| 크기 최적화 | 5MB | 낮음 ✅ |
| 네트워크 간소화 | 5MB | 낮음 ✅ |
| **총합** | **125MB** | - |

### 공격적 접근

| 최적화 | 절감량 | 위험도 |
|--------|--------|--------|
| zRAM (ZSTD) | 80MB | 낮음 ✅ |
| SLUB 최적화 | 20MB | 낮음 ✅ |
| 카메라 제거 | 50MB | 낮음 ✅ |
| 터치스크린 전체 제거 | 25MB | 중간 ⚠️ |
| 디스플레이 최소화 | 40MB | 높음 🚫 |
| 오디오 제거 | 25MB | 낮음 ✅ |
| 디버그 제거 | 30MB | 낮음 ✅ |
| 크기 최적화 | 10MB | 낮음 ✅ |
| 네트워크 간소화 | 10MB | 중간 ⚠️ |
| **총합** | **290MB** | - |

### 권장: 보수적 + 선택적 공격적 = **180-220MB**

이것만으로도 200MB 목표 달성! 🎉

---

## 📝 단계별 실행 계획

### Phase 1: 환경 준비 (15분)

#### Step 1.1: 필수 패키지 설치
```bash
cd /home/temmie/A90_5G_rooting
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    device-tree-compiler \
    lz4 \
    cpio \
    tar \
    pigz \
    git \
    curl \
    wget
```

#### Step 1.2: 툴체인 검증
```bash
/home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --version
# 예상 출력: clang version 9.0.9
```

#### Step 1.3: defconfig 백업
```bash
cd /home/temmie/A90_5G_rooting/archive/phase0_native_boot_research/kernel_build/SM-A908N_KOR_12_Opensource
cp arch/arm64/configs/r3q_kor_single_defconfig \
   arch/arm64/configs/r3q_kor_single_defconfig.backup
```

#### Step 1.4: 현재 boot 이미지 추가 백업
```bash
adb shell "su -c 'dd if=/dev/block/by-name/boot of=/sdcard/boot_current.img'"
adb pull /sdcard/boot_current.img /home/temmie/A90_5G_rooting/backups/backup_boot_current.img
```

### Phase 2: 커널 설정 (30-45분)

#### Step 2.1: 기본 설정 로드
```bash
cd /home/temmie/A90_5G_rooting/archive/phase0_native_boot_research/kernel_build/SM-A908N_KOR_12_Opensource

export ARCH=arm64
export SUBARCH=arm64

make O=out r3q_kor_single_defconfig
```

#### Step 2.2: 설정 메뉴 진입
```bash
make O=out menuconfig
# 또는 더 현대적인 인터페이스:
# make O=out nconfig
```

#### Step 2.3: 보수적 최적화 적용

**우선순위 1 - 안전한 최적화** (먼저 적용):

1. **General setup**
   - Optimize for size (`CONFIG_CC_OPTIMIZE_FOR_SIZE=y`)
   - Kernel compression mode → ZSTD (선택)

2. **Device Drivers → Multimedia support**
   - **DISABLE** (카메라 제거)
   - `[  ] Multimedia support` 체크 해제

3. **Device Drivers → Sound card support**
   - **DISABLE** (오디오 제거)
   - `[  ] Sound card support` 체크 해제

4. **Kernel hacking → Compile-time checks and compiler options**
   - **DISABLE** all debug options:
     - `[  ] Compile the kernel with debug info`
     - `[  ] Compile the kernel with frame pointers`

5. **Kernel hacking → Tracers**
   - **DISABLE** all:
     - `[  ] Kernel Function Tracer`
     - `[  ] Trace process context switches`

**우선순위 2 - zRAM 튜닝**:

1. **Device Drivers → Block devices → Compressed RAM block device**
   - `[*] Compressed RAM block device support`
   - Default compression: `lz4` (또는 `zstd` for better compression)
   - `[*] Write back incompressible page to backing device`

**우선순위 3 - 메모리 할당자**:

1. **General setup → Choose SLAB allocator**
   - `(X) SLUB (Unqueued Allocator)` 선택 (현재 설정 유지)
   - `[  ] SLUB debugging on by default` 비활성화
   - `[  ] Enable SLUB performance statistics` 비활성화

**우선순위 4 - 터치스크린** (선택적):

1. **Device Drivers → Input device support → Touchscreens**
   - 유지: `[*] IST40XX touchscreen`
   - 유지: `[*] MELFAS MSS100 touchscreen`
   - 나머지 40+ 드라이버 모두 비활성화

#### Step 2.4: 설정 저장
```bash
# menuconfig에서 Save → Exit

# defconfig로 저장
make O=out savedefconfig
cp out/defconfig arch/arm64/configs/r3q_optimized_defconfig
```

#### Step 2.5: 설정 검증 (중요!)
```bash
# WiFi 드라이버 확인 (필수!)
grep -E "(CONFIG_CFG80211|CONFIG_WLAN|CONFIG_QCA_CLD_WLAN)" out/.config
# 모두 =y 또는 =m이어야 함

# 스토리지 드라이버 확인
grep "CONFIG_SCSI_UFS_QCOM" out/.config
# =y여야 함

# zRAM 확인
grep "CONFIG_ZRAM" out/.config
# =y여야 함
```

### Phase 3: 커널 빌드 (45-90분, CPU 의존)

#### Step 3.1: 빌드 환경 설정
```bash
export ARCH=arm64
export SUBARCH=arm64
export CROSS_COMPILE=/home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android-
export CLANG_TRIPLE=aarch64-linux-gnu-
export CC=/home/temmie/A90_5G_rooting/toolchains/android-ndk-r21e/toolchains/llvm/prebuilt/linux-x86_64/bin/clang
export DTC_EXT=$(pwd)/tools/dtc
export CONFIG_BUILD_ARM64_DT_OVERLAY=y
```

#### Step 3.2: 클린 빌드
```bash
make O=out clean
# 완전히 깨끗하게: make O=out mrproper
```

#### Step 3.3: 빌드 시작
```bash
# 모든 CPU 코어 사용
make -j$(nproc) O=out 2>&1 | tee build_optimized.log

# 예상 소요 시간:
# - 4 코어: ~90분
# - 8 코어: ~45-60분
# - 16 코어: ~25-35분

# 진행 상황 모니터링 (다른 터미널에서):
tail -f build_optimized.log
```

#### Step 3.4: 빌드 결과 확인
```bash
# 빌드 성공 확인
ls -lh out/arch/arm64/boot/Image-dtb

# 예상 크기: 38-45MB (원본 49.8MB보다 작아야 함)
# 크기가 작을수록 성공적인 최적화

# 에러 확인
grep -i "error" build_optimized.log
# 출력 없어야 함
```

### Phase 4: 부팅 이미지 생성 (15분)

#### Step 4.1: 현재 boot.img에서 ramdisk 추출
```bash
mkdir -p /tmp/boot_extract
python3 /home/temmie/A90_5G_rooting/mkbootimg/unpack_bootimg.py \
    --boot_img /home/temmie/A90_5G_rooting/backups/backup_boot.img \
    --out /tmp/boot_extract
```

#### Step 4.2: 새 boot.img 생성
```bash
python3 /home/temmie/A90_5G_rooting/mkbootimg/mkbootimg.py \
    --kernel out/arch/arm64/boot/Image-dtb \
    --ramdisk /tmp/boot_extract/ramdisk \
    --cmdline "console=null androidboot.hardware=qcom androidboot.console=ttyMSM0 androidboot.memcg=1 lpm_levels.sleep_disabled=1 video=vfb:640x400,bpp=32,memsize=3072000 msm_rtb.filter=0x237 service_locator.enable=1 swiotlb=2048 androidboot.usbcontroller=a600000.dwc3 firmware_class.path=/vendor/firmware_mnt/image loop.max_part=7" \
    --base 0x00000000 \
    --kernel_offset 0x00008000 \
    --ramdisk_offset 0x01000000 \
    --tags_offset 0x01e00000 \
    --pagesize 4096 \
    --os_version 12.0.0 \
    --os_patch_level 2023-01 \
    --header_version 1 \
    -o boot_optimized.img

# 결과 확인
ls -lh boot_optimized.img
file boot_optimized.img
```

#### Step 4.3: Magisk 패치 적용 (중요 - root 유지)
```bash
# 디바이스로 전송
adb push boot_optimized.img /sdcard/Download/

# Magisk Manager에서:
# 1. 설치 → 파일 선택 및 패치
# 2. boot_optimized.img 선택
# 3. Magisk가 magisk_patched_XXXXX.img 생성

# 패치된 이미지 회수
adb pull /sdcard/Download/magisk_patched_*.img boot_optimized_magisk.img
```

### Phase 5: 안전한 테스트 (30-60분)

#### 🛑 체크포인트 3: 플래시 전 최종 확인

**플래시 전 체크리스트**:
- [ ] boot_optimized_magisk.img 파일 존재?
- [ ] backup_boot.img 백업 확인?
- [ ] backup_abl.img 백업 확인?
- [ ] 폰 배터리 60% 이상?
- [ ] WiFi/SSH 복구 방법 숙지?
- [ ] Download Mode 진입 방법 숙지?

**모두 체크되면 진행!**

#### Step 5.1: 방법 A - Fastboot 플래시 (권장)
```bash
# 부트로더로 재부팅
adb reboot bootloader

# 새 커널 플래시
fastboot flash boot boot_optimized_magisk.img

# 재부팅
fastboot reboot

# 3-5분 대기...
```

#### Step 5.2: 부팅 확인
```bash
# 부팅 완료 대기 (3-5분)
# WiFi LED 또는 화면 확인 (headless면 WiFi LED만)

# ADB 연결 확인
adb devices

# 커널 버전 확인
adb shell "su -c 'uname -r'"
# 예상: 4.14.190-r3q-optimized 또는 유사

# WiFi 확인 (중요!)
adb shell "su -c 'ip addr show wlan0'"
# inet 192.168.0.12/24 있어야 함

# SSH 확인
adb shell "su -c 'ps -A | grep sshd'"
# sshd 프로세스 실행 중이어야 함

# Magisk 확인
adb shell "su -c 'magisk -v'"
# Magisk 버전 출력되어야 함
```

#### Step 5.3: 메모리 측정
```bash
# 현재 메모리 사용량 측정
adb shell "su -c 'dumpsys meminfo | grep -A 20 \"Total RAM\"'" > mem_after_kernel.txt

# 주요 지표 확인
grep "Used RAM" mem_after_kernel.txt

# 예상:
# Before: Used RAM: 1,475,932K (1.41GB PSS)
# After:  Used RAM: 1,260,000K (1.20GB PSS) ← 목표!
```

#### Step 5.4: 안정성 테스트
```bash
# WiFi 안정성 (1시간)
ping -c 3600 192.168.0.12  # 1 ping/sec

# SSH 세션 테스트
ssh root@192.168.0.12 "uptime; free -m"

# 재부팅 테스트 (3회)
adb reboot
# 대기 후 WiFi/SSH 확인
# 3회 반복
```

### Phase 6: 성공 시 - 릴리즈 준비 (30분)

#### Step 6.1: AnyKernel3 플래시 가능 ZIP 생성
```bash
# AnyKernel3 다운로드
cd /home/temmie/A90_5G_rooting
git clone https://github.com/osm0sis/AnyKernel3

# 설정
cd AnyKernel3
nano anykernel.sh  # 디바이스 정보 수정

# 커널 복사
cp ../archive/phase0_native_boot_research/kernel_build/SM-A908N_KOR_12_Opensource/out/arch/arm64/boot/Image-dtb ./

# ZIP 생성
zip -r9 ../r3q_optimized_kernel_v1.0.zip * -x .git README.md *placeholder
```

#### Step 6.2: 변경 사항 문서화
```bash
cat > KERNEL_CHANGELOG.md << 'EOF'
# Samsung Galaxy A90 5G Optimized Kernel v1.0

## 변경 사항
- 카메라 드라이버 제거 (30MB 절감)
- 오디오 드라이버 제거 (20MB 절감)
- 커널 디버깅 비활성화 (25MB 절감)
- 크기 최적화 (-Os 플래그)
- zRAM 압축 튜닝

## 메모리 절감
- Before: 1.41GB PSS
- After: X.XXGB PSS
- 절감: XXXMB (XX%)

## 테스트
- 3/3 성공적인 부팅
- WiFi 24시간 안정성 확인
- SSH 기능 정상
- Magisk root 보존됨
EOF
```

---

## ⚠️ 체크포인트 (중단 가능 지점)

### Checkpoint 1: 설정 후 (30분)
**질문**: 설정이 합리적인가?

**확인 사항**:
- ✅ WiFi 드라이버 여전히 활성화? (`CONFIG_QCA_CLD_WLAN=y`)
- ✅ 필수 스토리지 드라이버 활성화? (`CONFIG_SCSI_UFS_QCOM=y`)
- ✅ zRAM 설정 올바른가?
- ⚠️ 너무 많이 비활성화하지 않았나? (터치스크린, 디스플레이)

**선택**:
- 계속 진행 → 빌드 시작
- 설정 재검토 → `make O=out menuconfig` 다시 실행

### Checkpoint 2: 빌드 후 (90분)
**질문**: 빌드 성공했는가?

**성공 지표**:
- ✅ `Image-dtb` 파일 `out/arch/arm64/boot/`에 존재?
- ✅ 파일 크기: 38-50MB (원본 49.8MB보다 작음 = 좋음!)
- ✅ `build_optimized.log`에 에러 없음?

**빌드 실패 시**:
- 로그 마지막 50줄 확인: `tail -50 build_optimized.log`
- 일반적인 문제:
  - 툴체인 경로 누락
  - 충돌하는 config 옵션
  - defconfig 문법 오류
- 수정 후 재빌드

**선택**:
- 성공 → 부팅 이미지 생성 진행
- 실패 → 로그 분석 및 수정

### Checkpoint 3: 플래시 전 (120분)
**질문**: 디바이스에 플래시 준비 완료?

**플래시 전 체크리스트**:
- ✅ boot.img 성공적으로 생성?
- ✅ Magisk 패치 적용됨?
- ✅ 백업 검증 및 접근 가능?
- ✅ 복구 방법 선택? (TWRP/fastboot/Odin)
- ✅ 폰 배터리 60% 이상?

**중단 조건**:
- ❌ 백업 없음
- ❌ 복구 절차 불확실
- ❌ WiFi 드라이버 실수로 비활성화됨

**선택**:
- 준비 완료 → 플래시 진행
- 준비 부족 → 추가 준비

### Checkpoint 4: 첫 부팅 후 (150분)
**질문**: 디바이스가 성공적으로 부팅되었는가?

**성공 지표**:
- ✅ 폰이 Android로 부팅 (GUI 없어도 OK - Phase 2가 제거함)
- ✅ WiFi 연결됨 (`ip addr` 또는 LED 표시로 확인)
- ✅ SSH 접근 가능
- ✅ Magisk 작동 (`su` 명령 작동)

**부팅 실패 시**:
- 백업 boot.img 복원
- 커널 config 재검토
- 빌드 로그에서 경고 확인
- 덜 공격적인 최적화로 재빌드

**선택**:
- 성공 → 메모리 측정 진행
- 실패 → 복구 및 재시도

### Checkpoint 5: 메모리 측정 후 (180분)
**질문**: 목표 달성했는가?

**목표**: 1.21GB PSS (현재 1.41GB에서 200MB 감소)

**평가**:
- ✅ 200MB+ 절감: **성공!** 문서화 및 최종 릴리즈 준비
- ⚠️ 100-199MB 절감: 부분 성공, 추가 최적화 고려
- ❌ <100MB 절감: 공격적인 접근 필요 또는 비현실적 목표

**다음 단계**:
- 성공 시: 문서 작성, 플래시 가능 ZIP 생성
- 부분 성공: 어떤 최적화가 효과 없었는지 확인
- 실패 시: 대안 접근 (런타임 튜닝, AOSP 빌드) 고려

---

## 🔄 복구 절차

### 시나리오 1: 커널이 부팅 안됨 (검은 화면)
```bash
# 방법 1: Fastboot 복구
adb reboot bootloader
fastboot flash boot /home/temmie/A90_5G_rooting/backups/backup_boot.img
fastboot reboot

# 방법 2: Odin 복구
# 1. Download Mode 진입 (전원 + 볼륨다운 + 볼륨업 동시에, 폰 꺼진 상태에서)
# 2. Odin으로 backup_boot.img.tar 플래시 (AP 슬롯)
# 3. 재부팅
```

### 시나리오 2: 부팅 루프
```bash
# 강제로 recovery mode 진입
# 부팅 중 전원 + 볼륨업 길게 누름
# TWRP에서:
adb shell "dd if=/sdcard/backup_boot.img of=/dev/block/by-name/boot"
adb reboot
```

### 시나리오 3: WiFi 작동 안함
```bash
# 이건 치명적 - WiFi 드라이버 보존 필수!
# 복구:
# 1. backup_boot.img 플래시
# 2. 재부팅
# 3. 커널 재빌드, WiFi 드라이버 활성화 확인:
#    CONFIG_CFG80211=y
#    CONFIG_MAC80211=y
#    CONFIG_WLAN=y
#    CONFIG_QCA_CLD_WLAN=y
```

### 시나리오 4: 커널 플래시 후 Magisk 손실
```bash
# 커널 재패치
adb push boot_optimized.img /sdcard/
# Magisk Manager에서: 설치 → 파일 선택 및 패치
adb pull /sdcard/Download/magisk_patched_*.img
fastboot flash boot magisk_patched_*.img
```

### 시나리오 5: 완전 벽돌 (부팅 안됨, 복구 안됨)
```bash
# 최후의 수단: 스톡 펌웨어 플래시
# 1. SamMobile/Sammobile.com에서 SM-A908N 스톡 ROM 다운로드
# 2. Odin으로 전체 펌웨어 플래시
# 3. 모든 데이터 손실되지만 복원됨
# 4. 필요 파일: AP, BL, CP, CSC
```

---

## 📊 예상 결과

### 보수적 접근 (권장)
- **RAM 절감**: 120-160MB
- **최종 RAM**: 1.25-1.29GB PSS
- **성공률**: 95%
- **위험도**: 매우 낮음 ✅
- **성능 영향**: -2 to -5% CPU (무시 가능)

### 보수적 + 런타임 튜닝 (최선)
- **RAM 절감**: 150-220MB
- **최종 RAM**: 1.19-1.26GB PSS
- **목표 달성**: ✅ (200MB 목표)
- **성공률**: 90%
- **위험도**: 낮음 ✅
- **성능 영향**: -5% CPU, +5-10% I/O 지연 (zRAM)

### 공격적 접근
- **RAM 절감**: 210-310MB
- **최종 RAM**: 1.10-1.20GB PSS
- **목표 달성**: ✅✅ (목표 초과!)
- **성공률**: 70-80%
- **위험도**: 중간 ⚠️
- **성능 영향**: -5 to -10% CPU, +10-15% I/O 지연

---

## 📋 필수 파일 체크리스트

### 빌드 전
- [ ] Samsung 커널 소스 (SM-A908N_KOR_12_Opensource/)
- [ ] Android NDK r21e 툴체인
- [ ] mkbootimg 도구
- [ ] 백업 파일 (backup_boot.img, backup_abl.img, backup_efs.tar.gz)

### 빌드 중
- [ ] build_optimized.log (에러 체크용)
- [ ] out/.config (설정 검증용)
- [ ] Image-dtb (빌드 결과)

### 플래시 전
- [ ] boot_optimized.img (새 커널)
- [ ] boot_optimized_magisk.img (Magisk 패치됨)
- [ ] backup_boot_current.img (추가 백업)

### 테스트 중
- [ ] mem_before.txt (baseline 메모리)
- [ ] mem_after_kernel.txt (커널 후 메모리)
- [ ] build_optimized.log (문제 발생 시 참조)

---

## 🎯 성공 기준

### 주요 목표
- ✅ **RAM 절감**: 200MB (1.41GB → 1.21GB PSS)
- 달성 조건: 최종 PSS ≤ 1.21GB

### 부가 목표
- ✅ WiFi 안정성 (24시간 연결 끊김 없음)
- ✅ SSH 접근성 (< 1초 응답)
- ✅ 부팅 신뢰성 (3/3 성공적인 부팅)
- ✅ Magisk 기능성 (root 접근 보존됨)
- ✅ Debian chroot 작동 (Phase 1 기능)

### 문서화 목표
- ✅ 완전한 빌드 로그 저장
- ✅ 메모리 전/후 측정
- ✅ Config 변경 사항 문서화
- ✅ 플래시 가능 커널 릴리즈

---

## ⏱️ 빌드 시간 예상

### 보수적 타임라인

| 단계 | 소요 시간 | 밤샘 가능? |
|------|-----------|----------|
| 환경 준비 | 15분 | No |
| 커널 설정 | 30-45분 | No (결정 필요) |
| 커널 빌드 | 45-90분 | ✅ Yes |
| 부팅 이미지 생성 | 15분 | No |
| 테스트 | 30-60분 | No |
| **총합** | **2.5-4시간** | - |

### CPU별 빌드 시간

시스템 (예상 4-8 코어):
- 4 코어: ~90분
- 8 코어: ~45-60분
- 16 코어: ~25-35분

### 최적화: Ccache

```bash
# ccache 설치로 재빌드 속도 향상
sudo apt-get install ccache

# 설정
export USE_CCACHE=1
export CCACHE_DIR=/home/temmie/.ccache
ccache -M 20G  # 20GB 캐시 설정

# 이후 재빌드: 5-15분! (vs 45-90분)
```

---

## 🚀 대안 접근법 (커널 빌드 실패 시)

### Plan B: 런타임 커널 튜닝만
재빌드 불필요, 기존 커널 튜닝만.

**Magisk 모듈 생성: kernel_tuning_v1**

**system.prop**:
```properties
vm.swappiness=100
vm.vfs_cache_pressure=200
vm.dirty_ratio=20
vm.dirty_background_ratio=5
ro.config.low_ram=true
ro.lmk.use_minfree_levels=true
```

**post-fs-data.sh**:
```bash
#!/system/bin/sh
# zRAM 크기 증가
echo 2G > /sys/block/zram0/disksize
swapoff /dev/block/zram0
mkswap /dev/block/zram0
swapon /dev/block/zram0 -p 32758

# Low memory killer 튜닝
echo "2048,4096,8192,16384,24576,32768" > /sys/module/lowmemorykiller/parameters/minfree
```

**예상 절감**: 30-60MB (커널보다 적지만 제로 위험)

### Plan C: 하이브리드 접근
커널 최적화 + 런타임 튜닝으로 최대 효과.

**단계**:
1. 보수적 커널 빌드 (카메라/오디오/디버그 제거)
2. 공격적인 런타임 튜닝 (zRAM, LMK, vm.*)
3. 측정 및 반복

**예상 절감**: 150-220MB (안전성과 효율성의 최적 균형)

### Plan D: AOSP 빌드 대기 (Phase 3)
커널 최적화가 목표 미달성 시, 전체 AOSP 최소 빌드로 연기.

**타임라인**: 50-100시간
**예상 절감**: 600-800MB (커널보다 훨씬 많음)
**위험**: 높음 (커스텀 AOSP 실패율 50-70%)

---

## 🔗 관련 문서

- [Phase 2 Option 1 완료 요약](HEADLESS_BOOT_V2_SUMMARY.md)
- [Phase 1 구현 가이드](../guides/MAGISK_SYSTEMLESS_GUIDE.md)
- [프로젝트 현황](PROJECT_STATUS.md)
- [진행 로그](PROGRESS_LOG.md)

---

## 📞 다음 단계

계획 검토 후 다음 중 선택:

1. **바로 시작** → Phase 1 환경 준비부터
2. **자동 빌드 스크립트** → 전체 과정 자동화
3. **defconfig 미리 생성** → 최적화 설정 파일 준비
4. **더 공격적인 계획** → 터치스크린/ZSTD 등 추가

---

**작성일**: 2025-11-16
**상태**: 계획 단계, 실행 대기
**다음**: 사용자 승인 및 실행 시작
