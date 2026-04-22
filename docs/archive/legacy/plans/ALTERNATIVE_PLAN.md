# Samsung Galaxy A90 5G - 대안 계획

## Phase 0 연구 결과 요약

**결론**: 완전한 네이티브 Linux 부팅은 **불가능**

**이유**:
- ABL이 커스텀 initramfs 실행 차단 (하드코딩됨)
- Knox/AVB가 /system 파티션 무결성 강제
- PBL이 SD 카드 부팅 미지원
- vbmeta 쓰기 보호로 Verified Boot 비활성화 불가

**시도한 모든 방법**:
1. ✅ 5회 커널 부팅 테스트 (mainline + Samsung)
2. ✅ Android init 하이재킹 시도 (AVB 복원)
3. ✅ Magisk overlay.d 조사
4. ✅ Halium/PostmarketOS 방식 검토
5. ✅ 전문가 의견 수집

---

## 대안 1: Termux + proot 환경 (권장)

### 개요
Android 위에서 proot를 사용해 완전한 Linux 사용자 공간 구축

### 장점
- ✅ **가장 안전**: 브릭 위험 전혀 없음
- ✅ **검증됨**: 수천 명의 사용자
- ✅ **WiFi/SSH 완벽 동작**: Android 드라이버 활용
- ✅ **개발 환경 완전**: GCC, Python, Node.js 등 모두 가능
- ✅ **SD 카드 활용**: /data에 chroot 환경 구축

### 단점
- ❌ Android 프레임워크 유지 필요
- ❌ RAM 절감 효과 제한적 (~600-800MB)

### 예상 RAM 사용량
```
Android (headless) : ~600MB
Termux proot-distro: +200MB
────────────────────────────
Total             : ~800MB-1GB
```

### 구현 단계

#### Step 1: Android 슬림화 (1-2일)
```bash
# ADB로 불필요한 시스템 앱 비활성화
pm disable-user --user 0 com.android.systemui  # UI 제거
pm disable-user --user 0 com.samsung.android.app.spage
pm disable-user --user 0 com.samsung.android.bixby.*
pm disable-user --user 0 com.samsung.android.game.*
# ... (50-100개 패키지 비활성화)

# 불필요한 서비스 중지
pm clear com.google.android.gms
pm disable-user --user 0 com.google.android.gms
```

**예상 RAM 절감**: 5GB → 1.5GB

#### Step 2: Termux 설치 및 설정 (1일)
```bash
# Termux 설치 (F-Droid에서)
# https://f-droid.org/en/packages/com.termux/

# Termux 내부에서
pkg update && pkg upgrade
pkg install proot-distro openssh git wget

# SSH 서버 시작
sshd
# 접속: ssh -p 8022 <device-ip>
```

#### Step 3: proot-distro 환경 구축 (1-2일)
```bash
# Debian 설치
proot-distro install debian

# 로그인
proot-distro login debian

# 개발 환경 설치
apt update && apt upgrade
apt install build-essential python3 nodejs git vim htop

# WiFi는 Android와 공유되어 자동 작동
# SSH 서버는 Termux sshd 사용
```

#### Step 4: 부팅 시 자동 시작 (1일)
```bash
# Tasker 또는 Automate 앱 사용
# 부팅 시 실행:
am startservice com.termux/.app.TermuxService
sleep 10
am broadcast --user 0 -a com.termux.RUN_COMMAND \
  --es command "sshd && proot-distro login debian"
```

### 최종 결과
- RAM: ~800MB-1GB (Android 최소화 + Termux)
- WiFi: ✅ 완벽 동작
- SSH: ✅ 완벽 동작
- 개발 환경: ✅ 완전한 Linux 환경
- 안정성: ⭐⭐⭐⭐⭐ 최고

---

## 대안 2: Magisk + Headless Android (고급)

### 개요
Android를 부팅하되, GUI를 완전히 제거하고 init.rc로 최소 서비스만 실행

### 장점
- ✅ Android 커널/드라이버 활용
- ✅ Magisk overlay.d로 systemless 수정
- ✅ WiFi/하드웨어 완벽 지원
- ⚠️ Termux보다 약간 더 슬림

### 단점
- ❌ Android init 유지 필요 (~200-300MB)
- ⚠️ 복잡도 높음
- ⚠️ 업데이트 시 Magisk 재설정 필요

### 예상 RAM 사용량
```
Android init    : ~200MB
Minimal services: ~100MB
Busybox/Toolbox : ~50MB
WiFi/네트워크   : ~100MB
SSH/서비스      : ~50MB
────────────────────────
Total          : ~500-600MB
```

### 구현 방법

#### 1. Magisk overlay.d 설정
```bash
# /data/adb/magisk/overlay.d/ 구조
overlay.d/
├── init.headless.rc
└── sbin/
    ├── custom_init.sh
    ├── wifi_manager.sh
    └── ssh_start.sh
```

#### 2. init.headless.rc 내용
```rc
on post-fs-data
    # Android UI 차단
    stop surfaceflinger
    stop zygote
    stop zygote_secondary

    # 최소 서비스만 시작
    start custom_services

service custom_services /system/bin/sh ${MAGISKTMP}/custom_init.sh
    user root
    group root
    oneshot
    seclabel u:r:su:s0
```

#### 3. custom_init.sh 스크립트
```bash
#!/system/bin/sh
# WiFi 활성화
svc wifi enable
sleep 5

# SSH 시작 (Magisk 모듈: SSH for Magisk)
/system/xbin/sshd -p 22 &

# Busybox chroot 환경으로 전환
if [ -d /data/linux_root ]; then
    chroot /data/linux_root /sbin/init
fi

exec /system/bin/sh
```

### 최종 결과
- RAM: ~500-600MB (이론적 최소)
- 실용성: ⚠️ 제한적 (Android 의존성)
- 복잡도: ⭐⭐⭐⭐ 높음

---

## 대안 3: 하드웨어 변경

### 추천 기기

#### Option A: PinePhone Pro
- **SoC**: Rockchip RK3399
- **RAM**: 4GB
- **OS**: PostmarketOS, Manjaro ARM 등
- **가격**: ~$400
- **장점**: 완전한 mainline 지원
- **단점**: 성능이 A90 5G보다 낮음

#### Option B: Librem 5
- **SoC**: NXP i.MX 8M Quad
- **RAM**: 3GB
- **OS**: PureOS (Debian)
- **가격**: ~$1200
- **장점**: 프라이버시 중심, kill switch
- **단점**: 매우 비쌈

#### Option C: OnePlus 6/6T
- **SoC**: Snapdragon 845
- **PostmarketOS**: ⭐⭐⭐⭐ (공식 지원)
- **가격**: ~$150-200 (중고)
- **장점**: A90 5G와 비슷한 성능, 커뮤니티 지원
- **WiFi**: ✅ ath10k 지원

---

## 비교 및 권장사항

| 옵션 | RAM 절감 | 난이도 | 비용 | WiFi | SSH | 권장도 |
|------|----------|--------|------|------|-----|--------|
| **Termux proot** | 1GB | ⭐ 쉬움 | $0 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Magisk headless | 500MB | ⭐⭐⭐⭐ 어려움 | $0 | ✅ | ✅ | ⭐⭐ |
| PinePhone Pro | 완전 | ⭐⭐ 중간 | $400 | ✅ | ✅ | ⭐⭐⭐⭐ |
| Librem 5 | 완전 | ⭐ 쉬움 | $1200 | ✅ | ✅ | ⭐⭐⭐ |
| OnePlus 6T | 완전 | ⭐⭐⭐ 중상 | $150 | ✅ | ✅ | ⭐⭐⭐⭐ |

---

## 최종 권장사항

### 시나리오 A: "실용성 우선" (권장)
→ **Termux + proot-distro**

**이유**:
- 완전한 Linux 개발 환경
- WiFi/SSH 완벽 작동
- 안전함 (브릭 위험 없음)
- 1-2일 내 구축 가능
- RAM ~800MB-1GB (목표 대비 양호)

**시작 방법**:
```bash
# 1. F-Droid에서 Termux 설치
# 2. pkg install proot-distro openssh
# 3. proot-distro install debian
# 4. SSH 서버 시작
```

---

### 시나리오 B: "극한 최적화 시도" (실험적)
→ **Magisk headless + Busybox chroot**

**이유**:
- 이론적으로 500-600MB까지 가능
- Magisk systemless로 AVB 우회
- SD 카드에 chroot 환경

**경고**:
- 복잡도 매우 높음
- 안정성 불확실
- 업데이트 시 재작업 필요

---

### 시나리오 C: "완전한 네이티브 원함" (하드웨어 변경)
→ **OnePlus 6T + PostmarketOS**

**이유**:
- 공식 PostmarketOS 지원
- Snapdragon 845 (성능 유사)
- 중고 $150-200으로 저렴
- mainline 커널 지원 양호

---

## 다음 단계 제안

### 즉시 실행 가능: Termux 방법 (1-2일)

**Day 1**:
1. F-Droid 설치
2. Termux 설치
3. proot-distro 설정
4. Debian 환경 구축

**Day 2**:
1. SSH 서버 설정
2. 개발 도구 설치
3. 부팅 자동화 설정
4. 테스트 및 최적화

**결과**: 완전히 작동하는 Linux 개발 환경 (WiFi + SSH)

---

## 학습된 교훈

### 성공한 것
1. ✅ ABL ramdisk 주입 메커니즘 파악
2. ✅ AVB/dm-verity 동작 원리 이해
3. ✅ Magisk overlay.d 시스템 발견
4. ✅ 안전한 테스트 방법론 (TWRP 백업)

### 실패한 것
1. ❌ 네이티브 부팅은 구조적으로 불가능
2. ❌ /system 파티션 수정은 AVB가 복원
3. ❌ SD 카드 직접 부팅은 PBL 제약
4. ❌ ABL 우회는 Knox가 차단

### 핵심 인사이트
**"완전한 Android 없이 완전한 네이티브 Linux"는 불가능하지만,
"Android 커널 위에서 슬림한 headless 환경"을 목표로 한다면
~600MB-1GB RAM 사용으로 실용적인 대안 가능**

---

## 프로젝트 아카이빙

### 백업 유지
```bash
~/A90_5G_rooting/
├── backups/          # TWRP 파티션 백업 (보존)
├── docs/             # 모든 문서 (보존)
├── logs/             # 부팅 로그 (보존)
└── kernels/          # 빌드된 커널 (선택적 삭제)
```

### 문서 보존
- [PROGRESS_LOG.md](PROGRESS_LOG.md) - 전체 연구 과정
- [NATIVE_LINUX_BOOT_PLAN.md](NATIVE_LINUX_BOOT_PLAN.md) - Phase 0 결과 포함
- [ALTERNATIVE_PLAN.md](ALTERNATIVE_PLAN.md) (이 문서) - 대안 계획

---

## 결론

**Samsung Galaxy A90 5G에서 완전한 네이티브 Linux 부팅은 불가능**하지만,
여러 실용적인 대안이 존재합니다.

**권장 방향**:
1. **Termux + proot**: 빠르고 안전하며 실용적
2. **하드웨어 변경**: 진정한 네이티브 원한다면 OnePlus 6T 추천
3. **현재 상태 유지**: 프로젝트 종료, 학습 경험으로 마무리

**최종 조언**:
"완벽한 네이티브"를 포기하고 "실용적인 Linux 환경"으로 목표를 조정한다면,
Termux는 매우 훌륭한 솔루션입니다.

---

**문서 작성일**: 2025-11-14
**Phase 0 상태**: ✅ 완료
**프로젝트 상태**: 대안 검토 중
**권장 방향**: Termux + proot-distro 또는 하드웨어 변경
