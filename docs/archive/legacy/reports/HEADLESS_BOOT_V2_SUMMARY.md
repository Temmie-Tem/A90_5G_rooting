# Headless Boot v2 - 최종 요약

## 📊 프로젝트 개요

**목표**: Samsung Galaxy A90 5G에서 Android GUI 제거 및 headless 환경 구축
**기간**: 2025-11-16 17:00~19:30 (2.5시간)
**결과**: ✅ 성공 (RAM 235MB 절감, 14.3%)

---

## 🎯 최종 성과

### 메모리 절감
```
초기 측정:  1,722,207K (1.64GB PSS)
최종 결과:  1,475,932K (1.41GB PSS)
─────────────────────────────────
절감량:       246,275K (235MB)
절감률:       14.3%
목표 대비:    37% 달성 (목표 1.0GB)
```

### 패키지 비활성화
- **총 163개 패키지 자동 비활성화**
  - GUI 패키지: 23개
  - Samsung 블로트웨어: 79개 (FaceService, Galaxy Store, 통신사 앱)
  - Google 서비스: 20개
  - 기본 앱: 41개

### 기능 검증
- ✅ **SystemUI**: 완전 차단 (실행 안됨)
- ✅ **Launcher**: 완전 차단 (실행 안됨)
- ✅ **WiFi**: 정상 작동 (192.168.0.12/24)
- ✅ **SSH**: 자동 시작 완료
- ✅ **Debian Chroot**: 접근 가능 (Phase 1 성과 유지)
- ✅ **Headless Boot**: 화면 없이 운영 가능

---

## 🛠️ 기술적 구현

### Magisk 모듈 구조

```
headless_boot_v2/
├── module.prop                    # v2.0.0
├── system.prop                    # ro.config.headless=1 설정
├── post-fs-data.sh               # YABP 우회
├── service.sh                    # 163개 패키지 비활성화 + SSH
├── system/
│   ├── system_ext/priv-app/SystemUI/.replace
│   └── priv-app/TouchWizHome_2017/.replace
└── META-INF/com/google/android/
    ├── update-binary
    └── updater-script
```

### 핵심 기술

#### 1. Magisk Magic Mount `.replace`
**문제**: Android Zygote가 SystemUI를 필수 앱으로 자동 재시작
**해결**: `.replace` 파일로 APK를 Android에서 완전히 숨김

```bash
/data/adb/modules/headless_boot_v2/
  system/system_ext/priv-app/SystemUI/.replace
  system/priv-app/TouchWizHome_2017/.replace
```

**원리**: Magisk가 해당 디렉토리를 빈 디렉토리로 overlay → Zygote가 APK를 찾지 못함

#### 2. pm 명령 타이밍
**발견**: `pm disable-user`가 post-fs-data 단계에서 작동 안함
**원인**: Package Manager 미초기화
**해결**: service.sh (late_start 단계)로 이동

```bash
# post-fs-data.sh - BLOCKING (부팅 초기)
# YABP 우회만 담당

# service.sh - NON-BLOCKING (late_start)
# 부팅 완료 대기 → 163개 패키지 비활성화
```

#### 3. WiFi 의존성
**문제**: Settings/Phone 비활성화 시 WiFi 끊김
**원인**: WiFi 설정 변경에 Settings 프로세스 필요
**해결**: Settings, Phone 프로세스는 활성 상태 유지

---

## 📈 재부팅 테스트 결과

| 재부팅 | 패키지 비활성화 | SystemUI 상태 | WiFi | SSH | RAM (PSS) | 비고 |
|--------|----------------|---------------|------|-----|-----------|------|
| 1차    | 0개            | 10초마다 재시작 | ✅   | ✅  | 1.79GB ↑  | pm 실패 (post-fs-data) |
| 2차    | 157개          | ❌ 완전 차단   | ✅   | ✅  | 1.22GB ↓  | service.sh로 이동 성공 |
| 3차    | 163개          | ❌ 완전 차단   | ✅   | ✅  | 1.41GB    | 최종 안정 버전 |

---

## 🔍 주요 발견

### 성공 요인
1. **Magisk Magic Mount 활용** - 시스템 수정 없이 APK 숨김 성공
2. **pm 명령 타이밍** - service.sh 단계에서만 작동 확인
3. **SystemUI 보호 우회** - `.replace` 파일로 Zygote 우회
4. **WiFi 의존성 파악** - Settings/Phone 필수 확인
5. **완전 자동화** - 재부팅만으로 headless 환경 구축
6. **가역적 구현** - 모듈 제거로 원상복구 가능

### 발견한 한계
**Option 1 (Magisk 모듈) 최대 절감**: 235MB (14.3%)

**제거 불가능한 필수 프로세스**:
- System 프로세스: 307MB PSS (Android 핵심 서버)
- Settings 앱: WiFi 설정에 필수
- Phone 프로세스: 통신 기능에 필수
- Surfaceflinger: 46MB (그래픽 서버)

**추가 최적화 필요 시**: Option 2 (커스텀 커널) 또는 Option 3 (AOSP 빌드) 시도 필요

---

## 📁 파일 위치

### 로컬 개발 파일
```
/home/temmie/A90_5G_rooting/scripts/magisk_module/headless_boot_v2/
├── module.prop
├── system.prop
├── post-fs-data.sh
├── service.sh
├── system/
│   ├── system_ext/priv-app/SystemUI/.replace
│   └── priv-app/TouchWizHome_2017/.replace
└── META-INF/...
```

### 디바이스 설치 위치
```
/data/adb/modules/headless_boot_v2/
```

### 로그 파일
```
/data/local/tmp/headless_boot_v2.log          # post-fs-data 로그
/data/local/tmp/headless_boot_v2_service.log  # service 로그
```

---

## 🚀 향후 최적화 옵션

### Option 1: Magisk 모듈 (✅ 완료)
- **달성**: RAM 235MB 절감 (14.3%)
- **소요 시간**: 2.5시간
- **위험도**: 낮음 (완전 가역적)
- **상태**: ✅ 완료

### Option 2: 커스텀 커널 (선택 가능)
- **목표**: 추가 200MB 절감
- **방법**:
  - zRAM 압축 활성화
  - Low-Memory-Killer 튜닝
  - 불필요한 드라이버 제거
  - Samsung 커널 소스 기반 빌드
- **소요 시간**: 5-10시간
- **위험도**: 중간 (TWRP 복구 가능)
- **요구사항**: ✅ Bootloader 언락 확인됨

### Option 3: AOSP 최소 빌드 (장기 프로젝트)
- **목표**: 추가 630MB 절감 (총 865MB 절감)
- **최종 RAM**: 900MB PSS 목표
- **방법**:
  - Minimal Android (no GUI, no GMS) 빌드
  - SystemUI 없이 컴파일
  - 최소한의 서비스만 포함
- **소요 시간**: 50-100시간
- **위험도**: 높음 (벽돌 가능성, 실패율 50-70%)
- **요구사항**: ✅ Bootloader 언락 확인됨

---

## 📝 학습 내용

### Magisk 관련
- ✅ Magisk Magic Mount `.replace` 파일 활용법
- ✅ post-fs-data.sh vs service.sh 차이 (BLOCKING vs NON-BLOCKING)
- ✅ Magisk lifecycle과 Android 부팅 단계
- ✅ Systemless 수정의 안전성과 가역성

### Android 시스템
- ✅ Zygote의 앱 보호 메커니즘
- ✅ Package Manager 초기화 타이밍
- ✅ SystemUI 자동 재시작 메커니즘
- ✅ WiFi 설정의 Settings 프로세스 의존성

### 문제 해결
- ✅ pm 명령이 특정 부팅 단계에서만 작동하는 이유
- ✅ SystemUI를 kill하면 자동으로 재시작되는 이유
- ✅ APK 파일을 숨겨 앱 시작을 완전히 차단하는 방법
- ✅ WiFi 유지를 위한 최소 프로세스 파악

---

## ✅ 결론

**Phase 2 (Option 1) 완료**: headless_boot_v2 Magisk 모듈을 통해 안전하고 가역적인 방식으로 Android GUI를 제거하고 RAM을 235MB (14.3%) 절감했습니다.

**주요 성과**:
1. SystemUI/Launcher 완전 차단
2. 163개 패키지 자동 비활성화
3. WiFi/SSH 정상 작동
4. 완전 자동화 (재부팅만으로 headless 환경)
5. 가역적 구현 (모듈 제거로 원상복구)

**한계**:
- Option 1 최대 절감: 235MB (14.3%)
- 목표 1.0GB까지 추가 410MB 절감 필요
- 추가 최적화는 Option 2 (커스텀 커널) 또는 Option 3 (AOSP 빌드) 필요

**권장 사항**:
- 현재 상태로 만족 → Phase 2 종료
- 추가 최적화 원함 → Option 2 시도 (5-10시간, 중위험)
- 최대 성능 추구 → Option 3 도전 (50-100시간, 고위험)

---

**작성일**: 2025-11-16
**버전**: v2.0.0
**상태**: 완료 및 검증됨
