# Phase 2: Headless Android 구현 가이드

## 📋 프로젝트 개요

**목표**: Android GUI를 완전히 제거하여 순수 Linux 환경만 남기고 RAM 최대 절감

**현재 상태**:
- 총 RAM: 5.5GB
- 사용 중: 2.5GB (45%)
- Chroot 오버헤드: 11-20MB

**목표 상태**:
- 총 RAM: 5.5GB
- 사용 중: 800MB-1.2GB (15-22%)
- 절감량: 1.3-1.7GB (52-68% 절감)

**접근 방법**: 단계적 접근 (Staged Approach)
- 각 단계마다 재부팅 및 검증
- 문제 발생 시 즉시 복구 가능
- WiFi, SSH 필수 기능 유지 확인

---

## 🎯 4단계 구현 계획

### Stage 1: GUI 제거 (~600MB 절감)

**제거 대상**:
1. `com.android.systemui` - Android 상태바, 알림, 퀵 설정
2. `com.sec.android.app.launcher` - Samsung 런처
3. `com.samsung.android.honeyboard` - Samsung 키보드
4. `com.google.android.inputmethod.latin` - Gboard 키보드

**유지 이유**:
- GUI가 없으므로 입력/출력 불필요
- SSH를 통해서만 조작

**예상 결과**:
- 부팅 후 검은 화면
- SSH 접속 정상 작동
- WiFi 정상 작동
- RAM: 2.5GB → 1.9GB

**복구 방법**:
```bash
pm enable com.android.systemui
pm enable com.sec.android.app.launcher
reboot
```

---

### Stage 2: Samsung 서비스 제거 (~400MB 절감)

**제거 대상**:
1. `com.osp.app.signin` - Samsung Account
2. `com.samsung.android.bixby.agent` - Bixby
3. `com.samsung.android.bixby.service` - Bixby Service
4. `com.samsung.android.smartcallprovider` - Smart Call
5. `com.samsung.android.sm.devicesecurity` - Device Care
6. `com.sec.android.easyMover.Agent` - Smart Switch
7. `com.samsung.android.kgclient` - Knox Guard
8. `com.samsung.android.knox.analytics.uploader` - Knox Analytics

**유지 대상**:
- WiFi 관련 서비스 (필수)
- ADB 관련 서비스 (필수)

**예상 결과**:
- RAM: 1.9GB → 1.5GB
- SSH/WiFi 정상 작동 유지

**복구 방법**: 개별 패키지 enable

---

### Stage 3: Google 서비스 제거 (~300MB 절감)

**제거 대상**:
1. `com.google.android.gms` - Google Play Services (⚠️ 주의)
2. `com.android.vending` - Play Store
3. `com.google.android.gsf` - Google Services Framework
4. `com.google.android.apps.maps` - Google Maps
5. `com.google.android.youtube` - YouTube
6. `com.google.android.apps.photos` - Google Photos

**⚠️ 경고**:
- Google Play Services 제거 시 WiFi 인증 문제 발생 가능
- WPA2-Enterprise 네트워크 사용 시 주의
- 일반 WPA2-PSK는 문제없음

**예상 결과**:
- RAM: 1.5GB → 1.2GB
- SSH/WiFi 정상 작동 유지 (WPA2-PSK)

**복구 방법**:
```bash
pm enable com.google.android.gms
pm enable com.android.vending
reboot
```

---

### Stage 4: 불필요한 앱 제거 (~200MB 절감)

**제거 대상**:
1. Media & Sound:
   - `com.sec.android.app.music` - Samsung Music
   - `com.samsung.android.video` - Samsung Video
   - `com.sec.android.app.soundalive` - SoundAlive

2. Communication:
   - `com.samsung.android.messaging` - Samsung Messages
   - `com.samsung.android.contacts` - Samsung Contacts
   - `com.samsung.android.incallui` - Call UI

3. Gallery & Camera:
   - `com.sec.android.gallery3d` - Gallery
   - `com.sec.android.app.camera` - Camera

4. Samsung Apps:
   - `com.samsung.android.calendar` - Calendar
   - `com.samsung.android.email.provider` - Email
   - `com.sec.android.app.sbrowser` - Samsung Internet

**예상 결과**:
- RAM: 1.2GB → 1.0GB 이하
- 완전한 헤드리스 환경

---

## 🛠️ 구현 스크립트

### 1. Stage 1 스크립트 (disable_gui.sh)

```bash
#!/system/bin/sh
# Stage 1: GUI 제거
# RAM 절감: ~600MB

LOGFILE="/data/local/tmp/headless_stage1.log"
echo "=== Stage 1: GUI Removal ===" > "$LOGFILE"
echo "Started: $(date)" >> "$LOGFILE"

# GUI Components
PACKAGES=(
    "com.android.systemui"
    "com.sec.android.app.launcher"
    "com.samsung.android.honeyboard"
    "com.google.android.inputmethod.latin"
)

echo "" >> "$LOGFILE"
echo "Disabling GUI packages..." >> "$LOGFILE"

for pkg in "${PACKAGES[@]}"; do
    echo "- Disabling: $pkg" | tee -a "$LOGFILE"
    pm disable-user --user 0 "$pkg" >> "$LOGFILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✓ Success" | tee -a "$LOGFILE"
    else
        echo "  ✗ Failed" | tee -a "$LOGFILE"
    fi
done

echo "" >> "$LOGFILE"
echo "Stage 1 completed: $(date)" >> "$LOGFILE"
echo "" >> "$LOGFILE"
echo "Next steps:" >> "$LOGFILE"
echo "1. Reboot device: reboot" >> "$LOGFILE"
echo "2. Test SSH: ssh root@192.168.0.12" >> "$LOGFILE"
echo "3. Check RAM: free -h" >> "$LOGFILE"
echo "4. If problem: adb shell pm enable com.android.systemui" >> "$LOGFILE"
echo "" >> "$LOGFILE"

cat "$LOGFILE"
```

### 2. Stage 2 스크립트 (disable_samsung.sh)

```bash
#!/system/bin/sh
# Stage 2: Samsung 서비스 제거
# RAM 절감: ~400MB

LOGFILE="/data/local/tmp/headless_stage2.log"
echo "=== Stage 2: Samsung Services Removal ===" > "$LOGFILE"
echo "Started: $(date)" >> "$LOGFILE"

# Samsung Services
PACKAGES=(
    "com.osp.app.signin"
    "com.samsung.android.bixby.agent"
    "com.samsung.android.bixby.service"
    "com.samsung.android.smartcallprovider"
    "com.samsung.android.sm.devicesecurity"
    "com.sec.android.easyMover.Agent"
    "com.samsung.android.kgclient"
    "com.samsung.android.knox.analytics.uploader"
)

echo "" >> "$LOGFILE"
echo "Disabling Samsung services..." >> "$LOGFILE"

for pkg in "${PACKAGES[@]}"; do
    echo "- Disabling: $pkg" | tee -a "$LOGFILE"
    pm disable-user --user 0 "$pkg" >> "$LOGFILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✓ Success" | tee -a "$LOGFILE"
    else
        echo "  ✗ Failed (maybe not installed)" | tee -a "$LOGFILE"
    fi
done

echo "" >> "$LOGFILE"
echo "Stage 2 completed: $(date)" >> "$LOGFILE"
cat "$LOGFILE"
```

### 3. Stage 3 스크립트 (disable_google.sh)

```bash
#!/system/bin/sh
# Stage 3: Google 서비스 제거
# RAM 절감: ~300MB
# ⚠️ WARNING: WiFi 인증 문제 발생 가능

LOGFILE="/data/local/tmp/headless_stage3.log"
echo "=== Stage 3: Google Services Removal ===" > "$LOGFILE"
echo "Started: $(date)" >> "$LOGFILE"
echo "" >> "$LOGFILE"
echo "⚠️  WARNING: This may affect WiFi authentication" >> "$LOGFILE"
echo "Make sure you can recover via ADB!" >> "$LOGFILE"
echo "" >> "$LOGFILE"

# Google Services
PACKAGES=(
    "com.google.android.gms"
    "com.android.vending"
    "com.google.android.gsf"
    "com.google.android.apps.maps"
    "com.google.android.youtube"
    "com.google.android.apps.photos"
)

echo "Disabling Google services..." >> "$LOGFILE"

for pkg in "${PACKAGES[@]}"; do
    echo "- Disabling: $pkg" | tee -a "$LOGFILE"
    pm disable-user --user 0 "$pkg" >> "$LOGFILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✓ Success" | tee -a "$LOGFILE"
    else
        echo "  ✗ Failed (maybe not installed)" | tee -a "$LOGFILE"
    fi
done

echo "" >> "$LOGFILE"
echo "Stage 3 completed: $(date)" >> "$LOGFILE"
cat "$LOGFILE"
```

### 4. Stage 4 스크립트 (disable_apps.sh)

```bash
#!/system/bin/sh
# Stage 4: 불필요한 앱 제거
# RAM 절감: ~200MB

LOGFILE="/data/local/tmp/headless_stage4.log"
echo "=== Stage 4: Unnecessary Apps Removal ===" > "$LOGFILE"
echo "Started: $(date)" >> "$LOGFILE"

# Unnecessary Apps
PACKAGES=(
    # Media
    "com.sec.android.app.music"
    "com.samsung.android.video"
    "com.sec.android.app.soundalive"

    # Communication
    "com.samsung.android.messaging"
    "com.samsung.android.contacts"
    "com.samsung.android.incallui"

    # Gallery & Camera
    "com.sec.android.gallery3d"
    "com.sec.android.app.camera"

    # Samsung Apps
    "com.samsung.android.calendar"
    "com.samsung.android.email.provider"
    "com.sec.android.app.sbrowser"
)

echo "" >> "$LOGFILE"
echo "Disabling unnecessary apps..." >> "$LOGFILE"

for pkg in "${PACKAGES[@]}"; do
    echo "- Disabling: $pkg" | tee -a "$LOGFILE"
    pm disable-user --user 0 "$pkg" >> "$LOGFILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✓ Success" | tee -a "$LOGFILE"
    else
        echo "  ✗ Failed (maybe not installed)" | tee -a "$LOGFILE"
    fi
done

echo "" >> "$LOGFILE"
echo "Stage 4 completed: $(date)" >> "$LOGFILE"
cat "$LOGFILE"
```

### 5. 전체 복구 스크립트 (restore_all.sh)

```bash
#!/system/bin/sh
# 전체 복구 스크립트
# 모든 비활성화된 패키지를 다시 활성화

LOGFILE="/data/local/tmp/headless_restore.log"
echo "=== Headless Android Restore ===" > "$LOGFILE"
echo "Started: $(date)" >> "$LOGFILE"

# All disabled packages
PACKAGES=(
    # Stage 1: GUI
    "com.android.systemui"
    "com.sec.android.app.launcher"
    "com.samsung.android.honeyboard"
    "com.google.android.inputmethod.latin"

    # Stage 2: Samsung Services
    "com.osp.app.signin"
    "com.samsung.android.bixby.agent"
    "com.samsung.android.bixby.service"
    "com.samsung.android.smartcallprovider"
    "com.samsung.android.sm.devicesecurity"
    "com.sec.android.easyMover.Agent"
    "com.samsung.android.kgclient"
    "com.samsung.android.knox.analytics.uploader"

    # Stage 3: Google Services
    "com.google.android.gms"
    "com.android.vending"
    "com.google.android.gsf"
    "com.google.android.apps.maps"
    "com.google.android.youtube"
    "com.google.android.apps.photos"

    # Stage 4: Apps
    "com.sec.android.app.music"
    "com.samsung.android.video"
    "com.sec.android.app.soundalive"
    "com.samsung.android.messaging"
    "com.samsung.android.contacts"
    "com.samsung.android.incallui"
    "com.sec.android.gallery3d"
    "com.sec.android.app.camera"
    "com.samsung.android.calendar"
    "com.samsung.android.email.provider"
    "com.sec.android.app.sbrowser"
)

echo "" >> "$LOGFILE"
echo "Re-enabling all packages..." >> "$LOGFILE"

for pkg in "${PACKAGES[@]}"; do
    echo "- Enabling: $pkg" | tee -a "$LOGFILE"
    pm enable "$pkg" >> "$LOGFILE" 2>&1
done

echo "" >> "$LOGFILE"
echo "Restore completed: $(date)" >> "$LOGFILE"
echo "Please reboot device: reboot" >> "$LOGFILE"

cat "$LOGFILE"
```

---

## 📊 단계별 검증 절차

### Stage 1 검증 (GUI 제거 후)

**1. 부팅 확인**:
```bash
# PC에서
adb wait-for-device
adb shell "echo 'Boot completed'"
```

**2. SSH 접속 확인**:
```bash
ssh root@192.168.0.12
# 비밀번호 입력
```

**3. WiFi 확인**:
```bash
# Chroot 내에서
ip addr show wlan0
ping -c 3 8.8.8.8
```

**4. RAM 측정**:
```bash
# Android shell에서
adb shell free -h

# 예상 결과:
#               total        used        free
# Mem:          5.2G         1.9G        3.3G
```

**5. 프로세스 확인**:
```bash
adb shell "ps -A | grep -E 'system_server|surfaceflinger|netd|wpa_supplicant'"
```

**성공 기준**:
- ✅ SSH 접속 성공
- ✅ WiFi 연결 유지
- ✅ RAM < 2.0GB
- ✅ 핵심 프로세스 실행 중

**실패 시 복구**:
```bash
adb shell pm enable com.android.systemui
adb shell pm enable com.sec.android.app.launcher
adb reboot
```

---

### Stage 2-4 검증 (동일 절차)

각 Stage마다 동일한 검증 절차 반복:
1. 스크립트 실행
2. 재부팅
3. SSH 접속 확인
4. WiFi 연결 확인
5. RAM 측정
6. 로그 확인

---

## ⚠️ 위험 요소 및 대응

### 높은 위험

| 위험 | 발생 확률 | 영향 | 대응 방법 |
|------|----------|------|----------|
| **부팅 후 검은 화면** | 95% | 낮음 | 정상 (예상된 동작) |
| **SSH 연결 실패** | 15% | 높음 | ADB로 복구 |
| **WiFi 연결 끊김** | 10% | 높음 | Stage 3 롤백 |

### 중간 위험

| 위험 | 발생 확률 | 영향 | 대응 방법 |
|------|----------|------|----------|
| **Google Play Services 의존성** | 30% | 중간 | GMS 재활성화 |
| **타이밍 문제** | 20% | 낮음 | 재부팅 |

### 복구 레벨

**Level 1: 개별 패키지 재활성화**
```bash
adb shell pm enable <package_name>
adb reboot
```

**Level 2: Stage 롤백**
```bash
# Stage 3에서 문제 발생 시
adb shell pm enable com.google.android.gms
adb shell pm enable com.android.vending
adb reboot
```

**Level 3: 전체 복구**
```bash
adb push restore_all.sh /data/local/tmp/
adb shell sh /data/local/tmp/restore_all.sh
adb reboot
```

**Level 4: TWRP 복구**
```bash
# TWRP에서 Magisk 모듈 제거
adb shell
rm -rf /data/adb/modules/systemless_chroot
reboot
```

---

## 📝 실행 순서

### 준비 단계

1. **백업 생성** (TWRP):
```bash
# TWRP Recovery로 부팅
# Backup → Boot, System, Data 선택 → Swipe to Backup
```

2. **스크립트 전송**:
```bash
cd /home/temmie/A90_5G_rooting/scripts/headless_android
adb push disable_gui.sh /data/local/tmp/
adb push disable_samsung.sh /data/local/tmp/
adb push disable_google.sh /data/local/tmp/
adb push disable_apps.sh /data/local/tmp/
adb push restore_all.sh /data/local/tmp/
adb shell chmod +x /data/local/tmp/*.sh
```

3. **현재 RAM 측정**:
```bash
adb shell free -h > /tmp/ram_before.txt
```

---

### 실행 단계

**Stage 1: GUI 제거**
```bash
# 1. 스크립트 실행
adb shell sh /data/local/tmp/disable_gui.sh

# 2. 재부팅
adb reboot

# 3. 부팅 대기 (검은 화면 정상)
adb wait-for-device
sleep 10

# 4. SSH 접속 테스트
ssh root@192.168.0.12

# 5. RAM 측정
adb shell free -h

# 6. 성공 시 다음 단계, 실패 시 복구
```

**Stage 2: Samsung 서비스 제거**
```bash
adb shell sh /data/local/tmp/disable_samsung.sh
adb reboot
# ... 검증 절차 반복 ...
```

**Stage 3: Google 서비스 제거** (⚠️ 주의)
```bash
# WiFi 문제 발생 가능 - ADB 연결 유지 필수
adb shell sh /data/local/tmp/disable_google.sh
adb reboot
# ... 검증 절차 반복 ...
```

**Stage 4: 불필요한 앱 제거**
```bash
adb shell sh /data/local/tmp/disable_apps.sh
adb reboot
# ... 검증 절차 반복 ...
```

---

## 📊 예상 결과

### RAM 사용량 추이

| Stage | 제거 항목 | RAM 사용량 | 절감량 | 누적 절감 |
|-------|----------|-----------|--------|----------|
| **시작** | - | 2.5GB | - | - |
| **Stage 1** | GUI | 1.9GB | 600MB | 600MB |
| **Stage 2** | Samsung | 1.5GB | 400MB | 1.0GB |
| **Stage 3** | Google | 1.2GB | 300MB | 1.3GB |
| **Stage 4** | Apps | 1.0GB | 200MB | 1.5GB |

### 최종 목표

**시스템 구성**:
- Android Framework: 800MB (최소)
- Linux Chroot: 11-20MB
- 여유 RAM: 4.6GB (85%)

**사용 가능 환경**:
- ✅ SSH 접속 (Chroot)
- ✅ WiFi 네트워킹
- ✅ ADB 디버깅
- ✅ Debian 패키지 관리
- ❌ Android GUI (완전 제거)

---

## 🎓 학습 목표

이 Phase 2를 통해 다음을 학습합니다:

1. **Android Package Manager**:
   - pm disable-user vs pm uninstall
   - User 0 (system user) 개념
   - 패키지 의존성 이해

2. **Android System Architecture**:
   - GUI vs Framework 분리
   - System Server의 역할
   - 필수 서비스 vs 선택 서비스

3. **RAM 최적화**:
   - Android 메모리 관리
   - 프로세스 우선순위
   - LowMemoryKiller 동작

4. **문제 해결**:
   - Headless 환경 디버깅
   - ADB를 통한 복구
   - 단계적 문제 격리

---

## 📚 참고 자료

### 공식 문서
- [Android Package Manager](https://developer.android.com/reference/android/content/pm/PackageManager)
- [Android System Services](https://source.android.com/docs/core/architecture/services)
- [ADB Commands](https://developer.android.com/tools/adb)

### 커뮤니티
- [XDA: Debloating Samsung Devices](https://forum.xda-developers.com/)
- [r/androidroot: Headless Android](https://reddit.com/r/androidroot)

---

## ✅ 성공 기준

### 기능 요구사항
- ✅ Android GUI 완전 제거
- ✅ SSH 접속 정상 작동
- ✅ WiFi 연결 유지
- ✅ Chroot 환경 정상 작동
- ✅ ADB 디버깅 가능

### 성능 요구사항
- ✅ RAM 사용량 1.2GB 이하 (현재 2.5GB 대비 52% 절감)
- ✅ 부팅 시간 변화 없음
- ✅ SSH 응답 시간 변화 없음

### 안정성 요구사항
- ✅ 재부팅 후 자동 복구
- ✅ WiFi 자동 연결
- ✅ SSH 서버 자동 시작
- ✅ 문제 발생 시 ADB 복구 가능

---

## 📈 진행 상황 추적

**시작일**: 2025-11-15
**예상 완료일**: 2025-11-15 (1일 이내)

**현재 상태**: Phase 2 계획 수립 완료

**다음 단계**:
1. ✅ 구현 가이드 작성 (완료)
2. ⏳ Stage 1 스크립트 생성
3. ⏳ Stage 1 실행 및 검증
4. ⏳ Stage 2-4 순차 실행

---

**이전 문서**: [HEADLESS_ANDROID_PLAN.md](../plans/HEADLESS_ANDROID_PLAN.md)
**관련 문서**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
