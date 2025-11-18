# Magisk Systemless Chroot 구현 가이드

Samsung Galaxy A90 5G에서 Magisk systemless chroot를 이용한 완전한 Linux 환경 구축

**난이도**: ⭐⭐⭐⭐ (7.5/10)
**예상 시간**: 5-14일
**필수 조건**: Magisk 루팅, TWRP 백업, Linux 기본 지식

---

## 📑 목차

1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [Phase 1: 환경 설정](#phase-1-환경-설정)
4. [Phase 2: Rootfs 생성](#phase-2-rootfs-생성)
5. [Phase 3: Magisk 모듈 작성](#phase-3-magisk-모듈-작성)
6. [Phase 4: 설치 및 테스트](#phase-4-설치-및-테스트)
7. [Phase 5: 네트워크 설정](#phase-5-네트워크-설정)
8. [Phase 6: 최적화](#phase-6-최적화)
9. [문제 해결](#문제-해결)
10. [참고 자료](#참고-자료)

---

## 개요

### 무엇을 만드는가?

Android 시스템 위에서 완전한 Linux 환경을 chroot로 실행하되, **Magisk의 systemless 메커니즘**을 활용하여 AVB/dm-verity 검증을 우회합니다.

### 작동 원리

```
부팅 시퀀스:
┌──────────────────────────────────────────────────┐
│ 1. Kernel 부팅 (Linux 4.14)                       │
│ 2. ABL이 Android ramdisk 주입 (피할 수 없음)      │
│ 3. Android init 시작 (/system/bin/init)          │
│ 4. Magisk post-fs-data hook 진입 ◄─ 여기서 개입!│
│    ├─ ext4 이미지를 /data/linux_root에 마운트    │
│    ├─ /dev, /proc, /sys bind mount               │
│    └─ WiFi 펌웨어 경로 연결                      │
│ 5. Magisk service.d hook 진입                    │
│    ├─ SSH 서버 시작 (chroot 내부)                │
│    └─ 서비스 모니터링                            │
│ 6. Android 부팅 완료                             │
│ 7. SSH로 chroot 환경 접속 가능 ✅                │
└──────────────────────────────────────────────────┘

실행 환경:
┌─────────────────────────────────────┐
│ Android System (Host)                │
│  ├─ Kernel 4.14                     │
│  ├─ Android init                     │
│  ├─ Magisk systemless mount          │
│  └─ /data/linux_root/ ◄─ Chroot     │
│       ├─ Debian/Ubuntu rootfs        │
│       ├─ SSH server (port 22)        │
│       └─ 개발 환경 (GCC, Python등)   │
└─────────────────────────────────────┘
```

### 왜 Magisk인가?

**문제**: Android의 AVB (Android Verified Boot)는 /system 파티션의 무결성을 검증합니다. 직접 수정하면 dm-verity가 자동으로 복원합니다.

**Magisk의 해결책**:
1. **Magic Mount**: /data에 있는 파일을 /system에 overlay 마운트
2. **AVB 우회**: Magisk가 이미 vbmeta를 패치하여 검증 우회
3. **Systemless**: 실제 /system 파티션은 건드리지 않음
4. **부팅 hook**: post-fs-data와 service.d로 부팅 과정에 개입

---

## 사전 준비

### 필수 요구사항

#### Android 디바이스 (A90 5G)

✅ **확인 완료**:
- [x] 부트로더 언락됨
- [x] TWRP 리커버리 설치됨
- [x] Magisk 루팅 가능 (v24.0+ 권장)
- [x] 백업 생성됨 (boot, system, vendor)

⚠️ **확인 필요**:
```bash
# Magisk 버전 확인
adb shell su -c "magisk -v"
# 출력 예: 26.4 (26400)
# → v24.0 이상이어야 함

# BusyBox 설치 확인
adb shell "busybox --help" || echo "BusyBox 필요!"

# 여유 공간 확인
adb shell df -h /data
# → 최소 8GB 필요 (rootfs 6GB + 여유 2GB)
```

#### PC (Linux 권장)

**필수 패키지** (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install -y \
    debootstrap \
    qemu-user-static \
    binfmt-support \
    android-tools-adb \
    android-tools-fastboot \
    zip unzip \
    e2fsprogs \
    parted
```

**선택 패키지** (권장):
```bash
sudo apt install -y \
    screen \
    tmux \
    vim \
    git
```

### 백업 (매우 중요!)

**TWRP 백업** (필수):
```bash
# TWRP 리커버리로 부팅
adb reboot recovery

# TWRP 터치스크린에서:
# Backup → Boot + System + Vendor + Data 선택
# Swipe to Backup

# PC로 복사
adb pull /sdcard/TWRP/BACKUPS/ ~/A90_backup_$(date +%Y%m%d)/
```

**boot.img 백업** (추가):
```bash
adb shell su -c "dd if=/dev/block/bootdevice/by-name/boot of=/sdcard/backup_boot.img"
adb pull /sdcard/backup_boot.img ~/A90_backup/
```

**복구 방법 기억**:
```bash
# 문제 발생 시 TWRP에서:
# 1. Restore 메뉴
# 2. 백업 선택
# 3. Swipe to Restore
```

---

## Phase 1: 환경 설정

**목표**: Magisk와 BusyBox를 설정하고 작업 디렉토리 준비

**예상 시간**: 1-2시간
**난이도**: ⭐⭐

### Step 1.1: Magisk 설치 및 확인

**Magisk가 이미 설치된 경우**:
```bash
# 버전 확인
adb shell su -c "magisk -v"
# 26.4 (26400) 이상 권장

# Magisk 환경 변수 확인
adb shell su -c "echo \$MAGISKTMP"
# 출력 예: /sbin/.magisk/img
```

**Magisk가 없는 경우**:
```bash
# 최신 Magisk 다운로드
wget https://github.com/topjohnwu/Magisk/releases/latest/download/Magisk-v26.4.apk

# ADB로 설치
adb install Magisk-v26.4.apk

# Magisk 앱 실행 → 설치 → 직접 설치 (권장)
# 또는 boot.img 패치 방식
```

### Step 1.2: BusyBox 설치

**방법 A: Magisk 모듈 (권장)**
```bash
# osm0sis BusyBox 모듈 다운로드
wget https://github.com/osm0sis/BusyBox-NDK/releases/download/1.36.1/busybox-ndk-1.36.1-arm64-signed.zip

# Magisk Manager에서 설치
# Modules → Install from storage → busybox-ndk*.zip 선택
# 재부팅

# 확인
adb shell "busybox --help"
```

**방법 B: 수동 설치**
```bash
# 바이너리 다운로드
wget https://github.com/osm0sis/busybox-ndk/releases/download/1.36.1/busybox-arm64

# 디바이스로 전송 및 설치
adb push busybox-arm64 /sdcard/
adb shell
su
cp /sdcard/busybox-arm64 /data/adb/magisk/busybox
chmod 755 /data/adb/magisk/busybox
/data/adb/magisk/busybox --install -s /data/adb/magisk/
exit
```

### Step 1.3: 작업 디렉토리 준비

**PC에서**:
```bash
# 프로젝트 디렉토리 구조 생성
cd ~/A90_5G_rooting
mkdir -p magisk_chroot/{module,rootfs,scripts}
cd magisk_chroot

# 디렉토리 구조:
# magisk_chroot/
# ├── module/           # Magisk 모듈 파일들
# ├── rootfs/           # Linux rootfs 생성 작업
# └── scripts/          # 유틸리티 스크립트
```

**디바이스에서**:
```bash
adb shell
su

# Chroot 디렉토리 생성
mkdir -p /data/linux_root
chmod 755 /data/linux_root

# 로그 디렉토리
mkdir -p /data/adb/magisk_logs
chmod 755 /data/adb/magisk_logs

exit
```

---

## Phase 2: Rootfs 생성

**목표**: Debian/Ubuntu ARM64 rootfs 이미지 생성

**예상 시간**: 2-4시간 (다운로드 속도 의존)
**난이도**: ⭐⭐⭐

### Step 2.1: Rootfs 배포판 선택

| 배포판 | 권장도 | 크기 | 특징 |
|--------|--------|------|------|
| **Debian 12 (Bookworm)** | ⭐⭐⭐⭐⭐ | ~400MB | 안정적, 패키지 풍부 |
| Ubuntu 22.04 | ⭐⭐⭐⭐ | ~450MB | 최신 패키지, 사용자 많음 |
| Alpine Linux | ⭐⭐⭐ | ~150MB | 경량, 패키지 적음 |
| Arch Linux ARM | ⭐⭐ | ~600MB | 최신, 복잡함 |

**권장**: Debian 12 (Bookworm) - 안정성과 호환성

### Step 2.2: ext4 이미지 파일 생성

**PC에서 실행**:

```bash
cd ~/A90_5G_rooting/magisk_chroot/rootfs

# 1. 6GB 빈 이미지 생성
dd if=/dev/zero of=debian_arm64.img bs=1M count=6144
# 예상 시간: 2-5분

# 2. ext4 파일시스템 포맷
mkfs.ext4 -F -L "Linux_Root" debian_arm64.img
# -F: 파일에 강제 포맷
# -L: 볼륨 레이블

# 3. 마운트 포인트 생성
mkdir -p mnt
sudo mount -o loop debian_arm64.img mnt

# 4. 마운트 확인
df -h mnt
# 출력: /dev/loop0        5.8G   24K  5.5G   1% /path/to/mnt
```

**왜 ext4 이미지인가?**
- **장점**: 파일 권한 보존, 심볼릭 링크 지원, 성능 우수
- **단점**: 고정 크기 (resize 가능하긴 함)
- **대안**: 디렉토리 기반 (더 간단하지만 약간 느림)

### Step 2.3: Debian rootfs 설치

**debootstrap으로 Debian 설치**:

```bash
# ARM64 qemu 에뮬레이션 설정
sudo apt install -y qemu-user-static binfmt-support

# qemu-arm64 바이너리 복사 (chroot에서 ARM64 실행)
sudo cp /usr/bin/qemu-aarch64-static mnt/usr/bin/

# Debian Bookworm ARM64 설치
sudo debootstrap \
    --arch=arm64 \
    --variant=minbase \
    --include=systemd,udev,dbus,apt,wget,curl,ca-certificates \
    bookworm \
    mnt \
    http://deb.debian.org/debian/

# 예상 시간: 15-45분 (네트워크 속도에 따라)
# 용량: 약 400MB
```

**설치 중 출력 예**:
```
I: Retrieving InRelease
I: Checking Release signature
I: Valid Release signature (key id ...)
I: Retrieving Packages
I: Validating Packages
I: Resolving dependencies of required packages...
I: Resolving dependencies of base packages...
I: Found additional required dependencies: ...
I: Checking component main on http://deb.debian.org/debian...
I: Retrieving libacl1 ...
[... 수백 개 패키지 다운로드 ...]
I: Base system installed successfully.
```

### Step 2.4: Rootfs 기본 설정

**Chroot 진입 및 설정**:

```bash
# /proc, /sys, /dev 마운트 (chroot에서 필요)
sudo mount -t proc proc mnt/proc
sudo mount -t sysfs sys mnt/sys
sudo mount --rbind /dev mnt/dev
sudo mount --make-rslave mnt/dev

# Chroot 진입
sudo chroot mnt /bin/bash

# === Chroot 내부에서 실행 ===

# 1. 호스트명 설정
echo "a90-debian" > /etc/hostname

# 2. hosts 파일
cat > /etc/hosts << 'EOF'
127.0.0.1       localhost
127.0.1.1       a90-debian
::1             localhost ip6-localhost ip6-loopback
EOF

# 3. DNS 설정
cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

# 4. APT 소스 설정
cat > /etc/apt/sources.list << 'EOF'
deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
EOF

# 5. 패키지 업데이트
apt update
apt upgrade -y

# 6. 필수 패키지 설치
apt install -y \
    openssh-server \
    openssh-client \
    sudo \
    vim \
    nano \
    wget \
    curl \
    git \
    htop \
    tmux \
    screen \
    net-tools \
    iputils-ping \
    traceroute \
    dnsutils \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    gcc \
    g++ \
    make \
    cmake \
    gdb \
    strace

# 예상 시간: 10-20분
# 추가 용량: ~800MB

# 7. SSH 설정
mkdir -p /run/sshd
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# SSH 설정 파일 수정
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config

# Root 비밀번호 설정
passwd
# 입력: 원하는 비밀번호 (예: root123)

# 8. 일반 사용자 생성 (선택)
useradd -m -s /bin/bash user
passwd user
usermod -aG sudo user

# 9. 타임존 설정
ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

# 10. 로케일 설정
apt install -y locales
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
update-locale LANG=en_US.UTF-8

# Chroot 종료
exit
```

**언마운트**:
```bash
# Chroot에서 나온 후 PC에서 실행
sudo umount mnt/dev
sudo umount mnt/proc
sudo umount mnt/sys
sudo umount mnt

# 이미지 무결성 확인
e2fsck -f debian_arm64.img
# 오류 없어야 함
```

### Step 2.5: 이미지 전송

**디바이스로 전송**:

```bash
# 이미지 압축 (선택, 전송 시간 단축)
gzip -9 debian_arm64.img
# debian_arm64.img.gz 생성 (~1.5GB)

# ADB로 전송
adb push debian_arm64.img.gz /sdcard/
# 예상 시간: 5-15분 (USB 3.0 기준)

# 디바이스에서 압축 해제 및 이동
adb shell
su
cd /data/linux_root
gzip -d < /sdcard/debian_arm64.img.gz > debian_arm64.img
rm /sdcard/debian_arm64.img.gz

# 권한 설정
chmod 600 debian_arm64.img
chown root:root debian_arm64.img

# 확인
ls -lh /data/linux_root/
# -rw------- 1 root root 6.0G ... debian_arm64.img

exit
```

---

## Phase 3: Magisk 모듈 작성

**목표**: Magisk 모듈 구조 생성 및 부팅 스크립트 작성

**예상 시간**: 4-8시간
**난이도**: ⭐⭐⭐⭐

### Step 3.1: 모듈 디렉토리 구조

**PC에서**:

```bash
cd ~/A90_5G_rooting/magisk_chroot/module

# 디렉토리 생성
mkdir -p systemless_chroot/{META-INF/com/google/android,system/bin,service.d,common}

cd systemless_chroot

# 최종 구조:
# systemless_chroot/
# ├── META-INF/com/google/android/
# │   ├── update-binary           # Magisk 설치 스크립트
# │   └── updater-script         # (비어있음)
# ├── module.prop                # 모듈 정보
# ├── post-fs-data.sh           # 부팅 시 실행 (BLOCKING)
# ├── service.d/
# │   └── boot_chroot.sh        # 서비스 시작 (NON-BLOCKING)
# ├── system/bin/
# │   ├── bootlinux             # Chroot 시작 스크립트
# │   └── killlinux             # Chroot 종료 스크립트
# └── common/
#     └── system.prop           # 시스템 속성 (선택)
```

### Step 3.2: module.prop 작성

```bash
cat > module.prop << 'EOF'
id=systemless_chroot
name=Systemless Linux Chroot
version=1.0.0
versionCode=100
author=YourName
description=Magisk systemless chroot environment for Debian ARM64. Provides full Linux development environment with SSH access.
updateJson=https://example.com/update.json
EOF
```

**필드 설명**:
- `id`: 고유 식별자 (다른 모듈과 중복 불가)
- `name`: 모듈 이름
- `version`: 버전 문자열
- `versionCode`: 버전 숫자 (업데이트 비교용)
- `author`: 제작자
- `description`: 설명
- `updateJson`: 업데이트 URL (선택)

### Step 3.3: post-fs-data.sh 작성 (핵심!)

이 스크립트가 **가장 중요**합니다. 부팅 시 chroot 환경을 마운트합니다.

```bash
cat > post-fs-data.sh << 'SCRIPT_EOF'
#!/system/bin/sh
# post-fs-data.sh - Magisk Systemless Chroot Initialization
#
# 실행 시점: post-fs-data 단계 (부팅 중, BLOCKING)
# 제한 시간: 40초 (타임아웃 주의!)
# 목적: Chroot 환경 마운트 및 기본 설정

MODDIR=${0%/*}
LOGFILE=/data/adb/magisk_logs/chroot_init.log

# ====================================================================
# 로깅 함수
# ====================================================================
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOGFILE"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] ERROR: $1" | tee -a "$LOGFILE" >&2
}

# ====================================================================
# 설정 변수
# ====================================================================
CHROOT_PATH="/data/linux_root"
CHROOT_IMG="$CHROOT_PATH/debian_arm64.img"
CHROOT_MNT="$CHROOT_PATH/mnt"

# ====================================================================
# 시작
# ====================================================================
log "========================================================"
log "Magisk Systemless Chroot Initialization Started"
log "========================================================"
log "Module: $MODDIR"
log "Image: $CHROOT_IMG"
log "Mount: $CHROOT_MNT"

# ====================================================================
# Step 1: 이전 마운트 정리 (매우 중요!)
# ====================================================================
log "[Step 1] Cleaning up previous mounts..."

umount_chroot() {
    local mnt_list="
        $CHROOT_MNT/vendor/firmware_mnt
        $CHROOT_MNT/data
        $CHROOT_MNT/dev/pts
        $CHROOT_MNT/dev/shm
        $CHROOT_MNT/dev
        $CHROOT_MNT/proc
        $CHROOT_MNT/sys
        $CHROOT_MNT
    "

    for mnt in $mnt_list; do
        if mountpoint -q "$mnt" 2>/dev/null; then
            log "  Unmounting: $mnt"
            umount -f -l "$mnt" 2>/dev/null || true
        fi
    done
}

umount_chroot

# ====================================================================
# Step 2: 디렉토리 생성
# ====================================================================
log "[Step 2] Creating directories..."

if [ ! -d "$CHROOT_PATH" ]; then
    mkdir -p "$CHROOT_PATH"
    chmod 755 "$CHROOT_PATH"
    log "  Created: $CHROOT_PATH"
fi

if [ ! -d "$CHROOT_MNT" ]; then
    mkdir -p "$CHROOT_MNT"
    chmod 755 "$CHROOT_MNT"
    log "  Created: $CHROOT_MNT"
fi

# ====================================================================
# Step 3: 이미지 존재 확인
# ====================================================================
log "[Step 3] Checking rootfs image..."

if [ ! -f "$CHROOT_IMG" ]; then
    log_error "Rootfs image not found: $CHROOT_IMG"
    log_error "Please create rootfs image first!"
    exit 1
fi

IMG_SIZE=$(du -h "$CHROOT_IMG" | cut -f1)
log "  Image found: $IMG_SIZE"

# ====================================================================
# Step 4: Rootfs 이미지 마운트
# ====================================================================
log "[Step 4] Mounting rootfs image..."

# 타임아웃 설정 (30초)
timeout 30 mount -o noatime,nodiratime "$CHROOT_IMG" "$CHROOT_MNT" 2>&1 | tee -a "$LOGFILE"

if [ $? -ne 0 ]; then
    log_error "Failed to mount rootfs image"
    log_error "Check image integrity: e2fsck -f $CHROOT_IMG"
    exit 1
fi

if ! mountpoint -q "$CHROOT_MNT"; then
    log_error "Mount verification failed"
    exit 1
fi

log "  Rootfs mounted successfully"

# ====================================================================
# Step 5: 필수 디렉토리 생성 (chroot 내부)
# ====================================================================
log "[Step 5] Creating essential directories..."

for dir in dev proc sys dev/pts dev/shm run tmp var/run; do
    if [ ! -d "$CHROOT_MNT/$dir" ]; then
        mkdir -p "$CHROOT_MNT/$dir"
        log "  Created: $CHROOT_MNT/$dir"
    fi
done

# ====================================================================
# Step 6: /dev 마운트
# ====================================================================
log "[Step 6] Mounting /dev..."

mount --rbind /dev "$CHROOT_MNT/dev" 2>&1 | tee -a "$LOGFILE"
if [ $? -eq 0 ]; then
    mount --make-rslave "$CHROOT_MNT/dev" 2>&1 | tee -a "$LOGFILE"
    log "  /dev mounted successfully"
else
    log_error "Failed to mount /dev"
fi

# /dev/pts (pseudo-terminal)
if [ ! -d "$CHROOT_MNT/dev/pts" ]; then
    mkdir -p "$CHROOT_MNT/dev/pts"
fi
mount -t devpts devpts "$CHROOT_MNT/dev/pts" -o gid=5,mode=620 2>&1 | tee -a "$LOGFILE"
log "  /dev/pts mounted"

# /dev/shm (shared memory)
if [ ! -d "$CHROOT_MNT/dev/shm" ]; then
    mkdir -p "$CHROOT_MNT/dev/shm"
fi
mount -t tmpfs tmpfs "$CHROOT_MNT/dev/shm" 2>&1 | tee -a "$LOGFILE"
log "  /dev/shm mounted"

# ====================================================================
# Step 7: /proc 마운트
# ====================================================================
log "[Step 7] Mounting /proc..."

mount -t proc proc "$CHROOT_MNT/proc" 2>&1 | tee -a "$LOGFILE"
if [ $? -eq 0 ]; then
    log "  /proc mounted successfully"
else
    log_error "Failed to mount /proc"
fi

# ====================================================================
# Step 8: /sys 마운트
# ====================================================================
log "[Step 8] Mounting /sys..."

mount --rbind /sys "$CHROOT_MNT/sys" 2>&1 | tee -a "$LOGFILE"
if [ $? -eq 0 ]; then
    mount --make-rslave "$CHROOT_MNT/sys" 2>&1 | tee -a "$LOGFILE"
    log "  /sys mounted successfully"
else
    log_error "Failed to mount /sys"
fi

# ====================================================================
# Step 9: WiFi 펌웨어 마운트 (A90 5G 특화)
# ====================================================================
log "[Step 9] Mounting WiFi firmware..."

if [ -d "/vendor/firmware_mnt" ]; then
    mkdir -p "$CHROOT_MNT/vendor/firmware_mnt"
    mount --rbind /vendor/firmware_mnt "$CHROOT_MNT/vendor/firmware_mnt" 2>&1 | tee -a "$LOGFILE"
    if [ $? -eq 0 ]; then
        mount --make-rslave "$CHROOT_MNT/vendor/firmware_mnt" 2>&1 | tee -a "$LOGFILE"
        log "  WiFi firmware mounted"
    else
        log "  WiFi firmware not available (may affect WiFi)"
    fi
else
    log "  /vendor/firmware_mnt not found, skipping"
fi

# ====================================================================
# Step 10: SD 카드 마운트 (데이터 교환용)
# ====================================================================
log "[Step 10] Mounting SD card..."

if [ -d "/sdcard" ]; then
    mkdir -p "$CHROOT_MNT/data"
    mount --rbind /sdcard "$CHROOT_MNT/data" 2>&1 | tee -a "$LOGFILE"
    if [ $? -eq 0 ]; then
        mount --make-rslave "$CHROOT_MNT/data" 2>&1 | tee -a "$LOGFILE"
        log "  SD card mounted at /data"
    fi
else
    log "  /sdcard not found, skipping"
fi

# ====================================================================
# Step 11: DNS 설정 복사
# ====================================================================
log "[Step 11] Copying DNS configuration..."

if [ -f "/etc/resolv.conf" ]; then
    cp /etc/resolv.conf "$CHROOT_MNT/etc/resolv.conf" 2>/dev/null
    log "  DNS configuration copied"
else
    # Fallback: Google DNS
    cat > "$CHROOT_MNT/etc/resolv.conf" << 'DNS_EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
DNS_EOF
    log "  Fallback DNS configured"
fi

# ====================================================================
# Step 12: SELinux 정책 추가 (Magisk v25+)
# ====================================================================
log "[Step 12] Configuring SELinux policies..."

if command -v supolicy >/dev/null 2>&1; then
    # Root에게 chroot 관련 capability 추가
    supolicy --live \
        'allow su su capability { dac_read_search dac_override sys_admin sys_chroot }' \
        2>&1 | tee -a "$LOGFILE"

    supolicy --live \
        'allow su su capability2 { syslog }' \
        2>&1 | tee -a "$LOGFILE"

    log "  SELinux policies applied"
else
    log "  supolicy not available, skipping"
fi

# ====================================================================
# Step 13: 상태 파일 생성
# ====================================================================
log "[Step 13] Creating status file..."

echo "MOUNTED" > "$CHROOT_PATH/status"
echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$CHROOT_PATH/mount_time"
log "  Status file created"

# ====================================================================
# 완료
# ====================================================================
log "========================================================"
log "Chroot Initialization Completed Successfully"
log "========================================================"
log "Mount point: $CHROOT_MNT"
log "Status: READY"
log ""
log "Next: SSH server will start in service.d stage"
log "========================================================"

exit 0
SCRIPT_EOF

chmod 755 post-fs-data.sh
```

**스크립트 주요 포인트**:

1. **언마운트 정리**: 이전 마운트가 남아있으면 문제 발생
2. **타임아웃**: post-fs-data는 40초 제한, 초과 시 부팅 중단
3. **bind mount**: --rbind (recursive), --make-rslave (propagation)
4. **SELinux**: supolicy로 chroot 권한 추가
5. **로깅**: 모든 단계 기록 (디버깅 필수)

### Step 3.4: service.d/boot_chroot.sh 작성

```bash
mkdir -p service.d
cat > service.d/boot_chroot.sh << 'SCRIPT_EOF'
#!/system/bin/sh
# boot_chroot.sh - Start services in chroot environment
#
# 실행 시점: service.d 단계 (부팅 완료 후, NON-BLOCKING)
# 목적: SSH 서버 및 기타 서비스 시작

MODDIR=${0%/*}/..
LOGFILE=/data/adb/magisk_logs/chroot_service.log

# ====================================================================
# 로깅 함수
# ====================================================================
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOGFILE"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] ERROR: $1" | tee -a "$LOGFILE" >&2
}

# ====================================================================
# 설정 변수
# ====================================================================
CHROOT_MNT="/data/linux_root/mnt"
CHROOT_STATUS="/data/linux_root/status"

# ====================================================================
# 시작
# ====================================================================
log "========================================================"
log "Chroot Service Initialization Started"
log "========================================================"

# ====================================================================
# Step 1: Chroot 마운트 확인
# ====================================================================
log "[Step 1] Verifying chroot mount..."

if [ ! -f "$CHROOT_STATUS" ]; then
    log_error "Status file not found: $CHROOT_STATUS"
    log_error "Chroot may not be mounted"
    exit 1
fi

STATUS=$(cat "$CHROOT_STATUS")
if [ "$STATUS" != "MOUNTED" ]; then
    log_error "Chroot status: $STATUS (expected: MOUNTED)"
    exit 1
fi

if ! mountpoint -q "$CHROOT_MNT"; then
    log_error "Chroot not mounted at: $CHROOT_MNT"
    exit 1
fi

log "  Chroot mount verified: OK"

# ====================================================================
# Step 2: WiFi 연결 대기
# ====================================================================
log "[Step 2] Waiting for WiFi connection..."

# 최대 30초 대기
for i in $(seq 1 30); do
    if ping -c 1 -W 1 8.8.8.8 >/dev/null 2>&1; then
        log "  WiFi connected (attempt $i)"
        break
    fi
    sleep 1
done

# WiFi 상태 확인
if ping -c 1 -W 1 8.8.8.8 >/dev/null 2>&1; then
    log "  Network: CONNECTED"
else
    log "  Network: DISCONNECTED (services may not work)"
fi

# ====================================================================
# Step 3: SSH 서버 시작
# ====================================================================
log "[Step 3] Starting SSH server..."

# SSH 키 생성 (처음만)
chroot "$CHROOT_MNT" /bin/bash << 'SSH_INIT'
    if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
        echo "Generating SSH host keys..."
        ssh-keygen -A
    fi

    # SSH 디렉토리 권한
    chmod 700 /root/.ssh 2>/dev/null || true
    chmod 755 /run/sshd 2>/dev/null || mkdir -p /run/sshd
SSH_INIT

# SSH 데몬 시작
chroot "$CHROOT_MNT" /bin/bash -c '/usr/sbin/sshd' 2>&1 | tee -a "$LOGFILE"

if [ $? -eq 0 ]; then
    log "  SSH server started successfully"

    # SSH 프로세스 확인
    SSH_PID=$(chroot "$CHROOT_MNT" /bin/bash -c 'pgrep sshd' | head -1)
    if [ -n "$SSH_PID" ]; then
        log "  SSH PID: $SSH_PID"
    fi
else
    log_error "Failed to start SSH server"
fi

# ====================================================================
# Step 4: IP 주소 확인
# ====================================================================
log "[Step 4] Network information..."

IP_ADDR=$(ip addr show wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
if [ -n "$IP_ADDR" ]; then
    log "  IP Address: $IP_ADDR"
    log "  SSH: ssh root@$IP_ADDR"
else
    log "  IP Address: NOT AVAILABLE"
fi

# ====================================================================
# Step 5: 상태 업데이트
# ====================================================================
log "[Step 5] Updating status..."

echo "RUNNING" > /data/linux_root/status
echo "$(date '+%Y-%m-%d %H:%M:%S')" > /data/linux_root/service_time

# ====================================================================
# 완료
# ====================================================================
log "========================================================"
log "Chroot Services Started Successfully"
log "========================================================"
log "Status: RUNNING"
if [ -n "$IP_ADDR" ]; then
    log "Connect: ssh root@$IP_ADDR"
fi
log "========================================================"

exit 0
SCRIPT_EOF

chmod 755 service.d/boot_chroot.sh
```

### Step 3.5: 유틸리티 스크립트

**bootlinux (chroot 진입 스크립트)**:

```bash
mkdir -p system/bin
cat > system/bin/bootlinux << 'SCRIPT_EOF'
#!/system/bin/sh
# bootlinux - Enter chroot environment

CHROOT_MNT="/data/linux_root/mnt"

if ! mountpoint -q "$CHROOT_MNT"; then
    echo "Error: Chroot not mounted"
    echo "Please reboot or check /data/adb/magisk_logs/chroot_init.log"
    exit 1
fi

# Chroot 진입
echo "Entering Linux chroot environment..."
chroot "$CHROOT_MNT" /bin/bash -l

exit 0
SCRIPT_EOF

chmod 755 system/bin/bootlinux
```

**killlinux (chroot 종료 스크립트)**:

```bash
cat > system/bin/killlinux << 'SCRIPT_EOF'
#!/system/bin/sh
# killlinux - Stop chroot services and unmount

CHROOT_MNT="/data/linux_root/mnt"

echo "Stopping chroot services..."

# SSH 종료
chroot "$CHROOT_MNT" /bin/bash -c 'pkill sshd' 2>/dev/null

# 모든 chroot 프로세스 종료
for pid in $(lsof "$CHROOT_MNT" 2>/dev/null | awk 'NR>1 {print $2}' | sort -u); do
    echo "Killing process: $pid"
    kill -9 "$pid" 2>/dev/null
done

# 언마운트
echo "Unmounting chroot..."
umount -f -l "$CHROOT_MNT/vendor/firmware_mnt" 2>/dev/null
umount -f -l "$CHROOT_MNT/data" 2>/dev/null
umount -f -l "$CHROOT_MNT/dev/pts" 2>/dev/null
umount -f -l "$CHROOT_MNT/dev/shm" 2>/dev/null
umount -f -l "$CHROOT_MNT/dev" 2>/dev/null
umount -f -l "$CHROOT_MNT/proc" 2>/dev/null
umount -f -l "$CHROOT_MNT/sys" 2>/dev/null
umount -f -l "$CHROOT_MNT" 2>/dev/null

echo "STOPPED" > /data/linux_root/status

echo "Chroot stopped"
exit 0
SCRIPT_EOF

chmod 755 system/bin/killlinux
```

### Step 3.6: update-binary (Magisk 설치 스크립트)

```bash
cat > META-INF/com/google/android/update-binary << 'SCRIPT_EOF'
#!/sbin/sh
##########################################################################################
#
# Magisk Module Installer Script
#
##########################################################################################

OUTFD=$2
ZIPFILE=$3

ps | grep zygote | grep -v grep >/dev/null && BOOTMODE=true || BOOTMODE=false
$BOOTMODE || ps -A 2>/dev/null | grep zygote | grep -v grep >/dev/null && BOOTMODE=true

[ -z $TMPDIR ] && TMPDIR=/dev/tmp

ui_print() {
  $BOOTMODE && echo "$1" || echo -e "ui_print $1\nui_print" >> /proc/self/fd/$OUTFD
}

require_new_magisk() {
  ui_print "***********************************"
  ui_print " Please install Magisk v20.4+!"
  ui_print "***********************************"
  exit 1
}

MAGISKBIN=/data/adb/magisk
[ -d $MAGISKBIN ] || require_new_magisk

ui_print "- Extracting module files"
unzip -o "$ZIPFILE" -d $TMPDIR/install >&2

MODID=$(grep_prop id $TMPDIR/install/module.prop)
MODPATH=$NVBASE/modules/$MODID

rm -rf $MODPATH
mkdir -p $MODPATH

ui_print "- Installing module: $MODID"
cp -af $TMPDIR/install/* $MODPATH/
chmod -R 755 $MODPATH

ui_print "- Setting permissions"
set_perm_recursive $MODPATH 0 0 0755 0644

ui_print "- Module installed successfully"
ui_print ""
ui_print "========================================"
ui_print "  Systemless Chroot Module Installed"
ui_print "========================================"
ui_print ""
ui_print "Next steps:"
ui_print "1. Copy rootfs image to /data/linux_root/debian_arm64.img"
ui_print "2. Reboot"
ui_print "3. Check logs: /data/adb/magisk_logs/"
ui_print "4. SSH: ssh root@<device-ip>"
ui_print ""

exit 0
SCRIPT_EOF

chmod 755 META-INF/com/google/android/update-binary
```

**updater-script (비워둠)**:
```bash
touch META-INF/com/google/android/updater-script
```

---

## Phase 4: 설치 및 테스트

**목표**: Magisk 모듈 설치 및 첫 부팅 테스트

**예상 시간**: 2-4시간 (디버깅 포함)
**난이도**: ⭐⭐⭐⭐

### Step 4.1: 모듈 ZIP 패키징

```bash
cd ~/A90_5G_rooting/magisk_chroot/module

# ZIP 생성
cd systemless_chroot
zip -r -9 ../systemless_chroot_v1.0.zip *

# 확인
cd ..
unzip -t systemless_chroot_v1.0.zip

# 필수 파일 체크
unzip -l systemless_chroot_v1.0.zip | grep -E "(module.prop|post-fs-data.sh|boot_chroot.sh)"
```

### Step 4.2: 모듈 설치

**방법 A: Magisk Manager (GUI)**

```bash
# ZIP을 디바이스로 전송
adb push systemless_chroot_v1.0.zip /sdcard/

# Magisk Manager 실행:
# 1. Modules 탭
# 2. Install from storage
# 3. systemless_chroot_v1.0.zip 선택
# 4. 설치 완료 대기
# 5. Reboot (아직 하지 마세요!)
```

**방법 B: ADB (CLI)**

```bash
adb push systemless_chroot_v1.0.zip /sdcard/

adb shell
su
magisk --install-module /sdcard/systemless_chroot_v1.0.zip

# 출력 확인
# - Extracting module files
# - Installing module: systemless_chroot
# - Module installed successfully

exit
```

### Step 4.3: 로그 디렉토리 확인

```bash
adb shell
su
mkdir -p /data/adb/magisk_logs
chmod 755 /data/adb/magisk_logs
exit
```

### Step 4.4: 첫 번째 재부팅

```bash
# 재부팅 전 준비
adb shell "echo 'Rebooting...' && sync"

# 재부팅
adb reboot

# 부팅 시간 측정 시작
# 예상: 60-90초
```

### Step 4.5: 부팅 로그 확인

**재부팅 후 즉시 로그 확인**:

```bash
# ADB 연결 대기
adb wait-for-device

# Chroot 초기화 로그
adb shell su -c "cat /data/adb/magisk_logs/chroot_init.log"

# 예상 출력:
# [2025-11-14 10:30:45] ========================================
# [2025-11-14 10:30:45] Magisk Systemless Chroot Initialization Started
# [2025-11-14 10:30:45] ========================================
# [2025-11-14 10:30:45] [Step 1] Cleaning up previous mounts...
# [2025-11-14 10:30:45] [Step 2] Creating directories...
# [2025-11-14 10:30:45] [Step 3] Checking rootfs image...
# [2025-11-14 10:30:45]   Image found: 6.0G
# [2025-11-14 10:30:46] [Step 4] Mounting rootfs image...
# [2025-11-14 10:30:48]   Rootfs mounted successfully
# ...
# [2025-11-14 10:31:05] Chroot Initialization Completed Successfully

# 서비스 시작 로그
adb shell su -c "cat /data/adb/magisk_logs/chroot_service.log"

# Magisk 전체 로그
adb logcat -d | grep -i magisk

# Kernel 로그
adb shell dmesg | tail -100
```

### Step 4.6: 마운트 상태 확인

```bash
adb shell
su

# Chroot 마운트 확인
mountpoint /data/linux_root/mnt
# 출력: /data/linux_root/mnt is a mountpoint

# 마운트 포인트 목록
mount | grep linux_root

# 예상 출력:
# /dev/block/loop0 on /data/linux_root/mnt type ext4 (rw,noatime,nodiratime)
# /dev on /data/linux_root/mnt/dev type devtmpfs (rw)
# proc on /data/linux_root/mnt/proc type proc (rw)
# sys on /data/linux_root/mnt/sys type sysfs (rw)
# ...

exit
```

### Step 4.7: Chroot 진입 테스트

```bash
adb shell
su
bootlinux

# === Chroot 내부 ===
# root@a90-debian:/#

# 기본 명령어 테스트
whoami
# root

hostname
# a90-debian

uname -a
# Linux a90-debian 4.14.xxx #1 SMP PREEMPT ... aarch64 GNU/Linux

df -h
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/loop0      5.8G  1.5G  4.0G  28% /

apt --version
# apt 2.6.1 (arm64)

python3 --version
# Python 3.11.2

gcc --version
# gcc (Debian 12.2.0-14) 12.2.0

# 네트워크 테스트
ping -c 3 8.8.8.8
# 성공 시: 3 packets transmitted, 3 received

# DNS 테스트
nslookup google.com
# 성공 시: IP 주소 반환

# Chroot 나가기
exit
```

---

## Phase 5: 네트워크 설정

**목표**: SSH 접속 및 네트워크 안정화

**예상 시간**: 1-2시간
**난이도**: ⭐⭐⭐

### Step 5.1: IP 주소 확인

```bash
adb shell
su

# WiFi 인터페이스 확인
ip addr show wlan0

# 예상 출력:
# 3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 3000
#     link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
#     inet 192.168.1.123/24 brd 192.168.1.255 scope global wlan0
#        valid_lft forever preferred_lft forever

# IP 주소만 추출
ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
# 192.168.1.123

exit
```

### Step 5.2: SSH 서버 확인

```bash
adb shell
su
bootlinux

# === Chroot 내부 ===

# SSH 프로세스 확인
ps aux | grep sshd
# root      1234  0.0  0.1  12345  6789 ?        Ss   10:31   0:00 /usr/sbin/sshd

# SSH 포트 리스닝 확인
netstat -tlnp | grep :22
# tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1234/sshd

# SSH 서비스 상태
service ssh status
# sshd is running

exit
exit
```

### Step 5.3: PC에서 SSH 접속

```bash
# PC에서 (디바이스와 같은 WiFi 네트워크)

# 첫 접속
ssh root@192.168.1.123

# 첫 접속 시 fingerprint 확인
# The authenticity of host '192.168.1.123' can't be established.
# ED25519 key fingerprint is SHA256:...
# Are you sure you want to continue connecting (yes/no)? yes

# 비밀번호 입력 (rootfs 생성 시 설정한 것)
# Password: root123

# 성공!
# root@a90-debian:~#

# 환경 테스트
pwd
# /root

ls -la
# drwx------  3 root root 4096 ... .
# drwxr-xr-x 18 root root 4096 ... ..
# drwx------  2 root root 4096 ... .ssh

# 네트워크 테스트
ping -c 3 google.com
# PING google.com (142.250.xxx.xxx) 56(84) bytes of data.
# 64 bytes from ... : icmp_seq=1 ttl=117 time=12.3 ms

# 패키지 설치 테스트
apt update
apt install -y cowsay

cowsay "Magisk Chroot Works!"
#  ______________________
# < Magisk Chroot Works! >
#  ----------------------
#         \   ^__^
#          \  (oo)\_______
#             (__)\       )\/\
#                 ||----w |
#                 ||     ||
```

### Step 5.4: SSH Key 인증 설정 (선택)

**PC에서**:

```bash
# SSH Key 생성 (없는 경우)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Public key 복사
cat ~/.ssh/id_ed25519.pub

# 디바이스로 전송
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@192.168.1.123

# 또는 수동:
ssh root@192.168.1.123
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3... your_email@example.com" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
exit

# 비밀번호 없이 접속 테스트
ssh root@192.168.1.123
# 비밀번호 묻지 않고 바로 접속됨
```

### Step 5.5: SSH 설정 강화 (선택)

**Chroot 내부에서**:

```bash
ssh root@192.168.1.123

# sshd_config 편집
vim /etc/ssh/sshd_config

# 권장 설정:
# Port 22                          # 포트 변경 (선택: 2222 등)
# PermitRootLogin yes              # Root 로그인 허용 (개발용)
# PasswordAuthentication yes       # 비밀번호 인증 (또는 no)
# PubkeyAuthentication yes         # Key 인증 활성화
# PermitEmptyPasswords no          # 빈 비밀번호 금지
# X11Forwarding no                 # X11 비활성화 (불필요)
# MaxAuthTries 3                   # 인증 시도 제한
# ClientAliveInterval 300          # 타임아웃 5분
# ClientAliveCountMax 2            # 타임아웃 횟수

# SSH 재시작
service ssh restart

# 접속 유지 여부 확인
# (다른 터미널에서 다시 접속 테스트)
```

---

## Phase 6: 최적화

**목표**: RAM 사용량 최소화 및 부팅 속도 개선

**예상 시간**: 2-4시간
**난이도**: ⭐⭐⭐

### Step 6.1: 현재 RAM 사용량 측정

**Chroot 내부에서**:

```bash
ssh root@192.168.1.123

# 전체 메모리 사용량
free -h
#               total        used        free      shared  buff/cache   available
# Mem:           5.3Gi       1.2Gi       3.8Gi        16Mi       320Mi       3.9Gi
# Swap:             0B          0B          0B

# 프로세스별 메모리 사용량
ps aux --sort=-rss | head -20

# Chroot 내부 프로세스만
ps aux | awk '{mem[$11] += $6} END {for (proc in mem) printf "%s: %.2f MB\n", proc, mem[proc]/1024}' | sort -t: -k2 -nr | head -10
```

**Android 호스트에서**:

```bash
adb shell
su

# 전체 메모리
free -m

# Android 프로세스
ps -A --sort=-rss | head -20

exit
```

### Step 6.2: 불필요한 서비스 비활성화

**Chroot 내부에서**:

```bash
# 실행 중인 서비스 확인
service --status-all

# 비활성화 후보 (headless 환경)
service bluetooth stop 2>/dev/null
service avahi-daemon stop 2>/dev/null
service cups stop 2>/dev/null

# 부팅 시 비활성화
systemctl disable bluetooth 2>/dev/null
systemctl disable avahi-daemon 2>/dev/null
systemctl disable cups 2>/dev/null

# 삭제 (공간 절약)
apt remove --purge -y \
    bluetooth \
    bluez \
    avahi-daemon \
    cups \
    cups-client

apt autoremove -y
apt clean

# 공간 확인
df -h /
```

### Step 6.3: Swap 설정 (선택)

**Chroot 내부에서**:

```bash
# Swap 파일 생성 (1GB)
fallocate -l 1G /swap.img
chmod 600 /swap.img
mkswap /swap.img
swapon /swap.img

# 확인
free -h
# Swap:          1.0Gi          0B       1.0Gi

# /etc/fstab에 추가 (영구적)
echo "/swap.img none swap sw 0 0" >> /etc/fstab

# Swappiness 조정 (기본: 60, 권장: 10)
sysctl vm.swappiness=10
echo "vm.swappiness=10" >> /etc/sysctl.conf
```

### Step 6.4: 부팅 속도 개선

**post-fs-data.sh 최적화**:

```bash
# PC에서 모듈 수정
cd ~/A90_5G_rooting/magisk_chroot/module/systemless_chroot

# post-fs-data.sh에 추가 (Step 4 이후):
# 병렬 마운트로 속도 개선
# 이미 작성된 스크립트에 최적화 포함됨

# 타임아웃 줄이기 (30초 → 20초)
sed -i 's/timeout 30/timeout 20/' post-fs-data.sh

# 재패키징
cd ..
zip -r -9 systemless_chroot_v1.1.zip systemless_chroot/

# 업데이트
adb push systemless_chroot_v1.1.zip /sdcard/
adb shell
su
magisk --install-module /sdcard/systemless_chroot_v1.1.zip
reboot
```

### Step 6.5: 최종 RAM 사용량 확인

```bash
# 재부팅 후
adb wait-for-device
adb shell
su

# 전체 메모리
free -m
#               total        used        free      shared  buff/cache   available
# Mem:           5432        1234        3890          16         308        4080

# Chroot 진입
bootlinux

free -h
#               total        used        free      shared  buff/cache   available
# Mem:           5.3Gi       800Mi       4.2Gi        16Mi       300Mi       4.3Gi

# 목표 달성 확인:
# Android (최소화): ~500MB
# Chroot: ~300MB
# 총: ~800MB ✅

exit
exit
```

---

## 문제 해결

### 일반적 문제

#### 문제 1: 부팅 후 Chroot 마운트 안 됨

**증상**:
```bash
adb shell mountpoint /data/linux_root/mnt
# /data/linux_root/mnt is not a mountpoint
```

**원인**: post-fs-data.sh 실행 실패

**해결**:
```bash
# 로그 확인
adb shell su -c "cat /data/adb/magisk_logs/chroot_init.log"

# 일반적 원인:
# 1. 이미지 파일 없음
adb shell su -c "ls -lh /data/linux_root/debian_arm64.img"

# 2. 이미지 손상
adb shell su -c "e2fsck -f /data/linux_root/debian_arm64.img"

# 3. 타임아웃
# → post-fs-data.sh의 timeout 값 증가

# 수동 마운트 시도
adb shell
su
mount -o loop /data/linux_root/debian_arm64.img /data/linux_root/mnt
# 오류 메시지 확인
```

#### 문제 2: SSH 서버 시작 안 됨

**증상**:
```bash
ssh root@192.168.1.123
# ssh: connect to host 192.168.1.123 port 22: Connection refused
```

**원인**: sshd 미실행

**해결**:
```bash
adb shell
su
bootlinux

# SSH 프로세스 확인
ps aux | grep sshd
# (없음)

# 수동 시작
/usr/sbin/sshd

# 오류 메시지 확인
/usr/sbin/sshd -D -d
# debug1: sshd version OpenSSH_x.x, ...
# 오류 메시지 분석

# 일반적 원인:
# 1. Host key 없음
ssh-keygen -A

# 2. 권한 문제
chmod 700 /root/.ssh
chmod 600 /etc/ssh/*_key

# 3. 포트 충돌
netstat -tlnp | grep :22
# 다른 프로세스가 점유 중

# 재시작
service ssh restart
```

#### 문제 3: WiFi 연결 안 됨 (Chroot 내부)

**증상**:
```bash
ping 8.8.8.8
# ping: connect: Network is unreachable
```

**원인**: /etc/resolv.conf 문제 또는 DNS 설정

**해결**:
```bash
# DNS 설정 확인
cat /etc/resolv.conf
# (비어있거나 잘못됨)

# DNS 재설정
cat > /etc/resolv.conf << 'EOF'
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF

# 네트워크 인터페이스 확인
ip addr

# 게이트웨이 확인
ip route
# default via 192.168.1.1 dev wlan0

# 연결 테스트
ping -c 3 8.8.8.8
```

#### 문제 4: 부팅 무한 대기

**증상**: 재부팅 후 부팅이 완료되지 않음

**원인**: post-fs-data.sh 타임아웃 초과 (40초 제한)

**복구**:
```bash
# 강제 재부팅 (전원 버튼 길게 누름)

# TWRP 리커버리로 부팅
# 볼륨 업 + 전원 버튼

# ADB 연결
adb shell

# 모듈 비활성화
rm /data/adb/modules/systemless_chroot/update
# 또는 완전 삭제
rm -rf /data/adb/modules/systemless_chroot

# 재부팅
reboot
```

#### 문제 5: 마운트 포인트 오염

**증상**:
```bash
umount /data/linux_root/mnt
# umount: target is busy
```

**원인**: Chroot 내부 프로세스가 실행 중

**해결**:
```bash
# Chroot 프로세스 확인
lsof /data/linux_root/mnt

# 모든 프로세스 종료
for pid in $(lsof /data/linux_root/mnt | awk 'NR>1 {print $2}' | sort -u); do
    kill -9 "$pid"
done

# 강제 언마운트
umount -f -l /data/linux_root/mnt

# 마운트 포인트 완전 정리
for mnt in $(mount | grep linux_root | awk '{print $3}' | tac); do
    umount -f -l "$mnt"
done
```

---

## 참고 자료

### 공식 문서

- [Magisk 공식 문서](https://topjohnwu.github.io/Magisk/)
- [Magisk Module Template](https://github.com/topjohnwu/Magisk-Module-Template)
- [Debian ARM64](https://wiki.debian.org/Arm64Port)

### 커뮤니티

- [XDA Developers - A90 5G](https://forum.xda-developers.com/)
- [r/Magisk](https://reddit.com/r/Magisk)
- [r/androidroot](https://reddit.com/r/androidroot)

### 관련 프로젝트

- [Linux Deploy](https://github.com/meefik/linuxdeploy)
- [Termux](https://termux.com/)
- [PostmarketOS](https://postmarketos.org/)

---

**다음 문서**: [MAGISK_INTERNALS.md](MAGISK_INTERNALS.md) - Magisk 내부 구조 분석
