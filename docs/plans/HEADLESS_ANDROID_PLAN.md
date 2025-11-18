# Phase 1: Magisk Systemless Chroot 헤드리스 안드로이드 구현

## 📋 프로젝트 개요

**목표**: Samsung Galaxy A90 5G에서 Magisk systemless chroot를 이용한 헤드리스 Linux 환경 구축

**동기**:
- Phase 0에서 네이티브 Linux 부팅이 불가능함을 확인
- Linux Deploy 경험이 이미 있음
- 새로운 기술 학습 및 최대 RAM 절감 원함

**예상 결과**:
- RAM 사용량: 500-800MB (현재 5GB 대비 84-90% 절감)
- 완전한 Linux 개발 환경 (Debian/Ubuntu)
- SSH를 통한 원격 접속
- WiFi 네트워킹 지원

---

## 🎯 학습 목표

이 프로젝트를 통해 다음을 학습합니다:

1. **Magisk Magic Mount 메커니즘**
   - Systemless 수정의 원리
   - AVB/dm-verity 우회 방법
   - Overlay mount 구조

2. **Android 부팅 프로세스**
   - PBL/SBL/ABL 부트로더 체인
   - post-fs, post-fs-data, service.d 단계
   - Init system과 Magisk hook 관계

3. **SELinux 정책 조작**
   - supolicy를 통한 정책 주입
   - chroot에 필요한 capability 이해
   - SELinux enforcing 모드에서 작동

4. **Mount Namespace**
   - Linux mount namespace 개념
   - Bind mount와 propagation
   - Android와 chroot 환경 분리

5. **시스템 수준 디버깅**
   - 부팅 로그 분석 (dmesg, logcat)
   - Mount 문제 해결
   - 타이밍 이슈 처리

---

## 📊 Phase 0 대비 차이점

| 항목 | Phase 0 (네이티브 부팅) | Phase 1 (Magisk Chroot) |
|------|------------------------|------------------------|
| **목표** | 완전한 네이티브 Linux | Android 위 Linux 환경 |
| **결과** | ❌ 불가능 (ABL/Knox 차단) | ✅ 가능 |
| **RAM 예상** | 150-300MB (이론) | 500-800MB (실제) |
| **부팅 경로** | 커널 → Linux init | 커널 → Android init → Chroot |
| **WiFi** | 드라이버 문제 | Android 드라이버 재사용 |
| **복잡도** | 높음 | 매우 높음 |
| **안정성** | 브릭 위험 | 복구 가능 |

**Phase 0 교훈**:
- ABL이 Android ramdisk를 하드코딩으로 강제 주입
- Knox/AVB가 /system 파티션 무결성 강제
- PBL이 SD 카드 부팅 미지원
- → **완전한 네이티브 부팅은 불가능**

**Phase 1 접근**:
- Android init을 받아들이고 그 위에 chroot 구축
- Magisk의 systemless 메커니즘 활용
- AVB 우회 (Magisk가 이미 해결)
- → **실용적이고 실현 가능한 접근**

---

## 🗓️ 전체 일정

### Week 1: 기초 학습 및 준비 (5일)

**Day 1-2: 이론 학습 및 문서 작성**
- Magisk 내부 구조 이해
- Android 부팅 프로세스 분석
- 기술 문서 작성
- 예상 시간: 8-12시간

**Day 3-4: Rootfs 준비**
- Linux rootfs 이미지 생성 (Debian/Ubuntu)
- 기본 패키지 설치
- SSH 설정
- 예상 시간: 4-6시간

**Day 5: 첫 번째 구현 시도**
- Magisk 모듈 기본 구조 작성
- post-fs-data.sh 초안
- 첫 테스트 (실패 예상)
- 예상 시간: 6-8시간

### Week 2: 구현 및 디버깅 (5-9일)

**Day 6-8: 핵심 문제 해결**
- SELinux 정책 설정
- Mount namespace 문제 해결
- 부팅 타이밍 조정
- 예상 시간: 12-20시간

**Day 9-11: 네트워크 및 서비스**
- WiFi 연결 안정화
- SSH 서버 자동 시작
- DNS 설정
- 예상 시간: 8-12시간

**Day 12-14: 최적화 및 문서화**
- RAM 사용량 최소화
- 부팅 속도 개선
- 전체 문서 완성
- 예상 시간: 8-12시간

**총 예상 시간**: 46-70시간 (5-14일)

---

## 📝 생성할 산출물

### 문서 (docs/)

1. **MAGISK_SYSTEMLESS_GUIDE.md** (핵심)
   - 전체 구현 단계별 가이드
   - 각 단계의 기술적 배경 설명
   - 예상 문제 및 해결 방법

2. **MAGISK_INTERNALS.md**
   - Magisk Magic Mount 메커니즘
   - Module 구조
   - post-fs-data vs service.d

3. **ANDROID_BOOT_PROCESS.md**
   - Android 부팅 전체 과정
   - Magisk hook 포인트
   - 타이밍 분석

4. **SELINUX_POLICY.md**
   - SELinux 기본 개념
   - supolicy 사용법
   - Chroot 관련 정책

5. **MOUNT_NAMESPACE.md**
   - Mount namespace 개념
   - Bind mount 실습
   - Propagation 옵션

6. **TROUBLESHOOTING.md**
   - 일반적 문제 및 해결법
   - 디버깅 방법
   - 복구 절차

### 스크립트 (scripts/magisk_module/)

7. **post-fs-data.sh**
   - Chroot 환경 마운트
   - SELinux 정책 주입
   - 상세 주석 포함

8. **service.d/boot_chroot.sh**
   - SSH 서버 시작
   - WiFi 연결 확인
   - 서비스 관리

9. **module.prop**
   - Magisk 모듈 메타데이터

10. **system/bin/bootlinux.sh**
    - Chroot 환경 진입 스크립트

11. **system/bin/killlinux.sh**
    - Chroot 환경 종료 스크립트

### 자동화 스크립트 (scripts/)

12. **create_rootfs.sh**
    - Debian/Ubuntu rootfs 자동 생성
    - 필수 패키지 설치
    - SSH 설정 자동화

13. **package_module.sh**
    - Magisk 모듈 ZIP 패키징
    - 권한 설정 자동화

14. **debug_magisk.sh**
    - 로그 수집
    - 마운트 상태 확인
    - 디버깅 정보 출력

---

## 🛠️ 기술 스택

### 필수 도구

**PC (Linux 권장)**:
- debootstrap (Debian rootfs 생성)
- qemu-user-static (ARM64 에뮬레이션)
- adb (Android Debug Bridge)
- zip/unzip (모듈 패키징)

**Android 디바이스**:
- Magisk v24.0 이상 (권장: v26.x)
- BusyBox (Magisk 모듈 또는 별도 설치)
- TWRP Recovery (백업 및 복구용)

### 기술 요구사항

**필수 지식**:
- Linux 명령어 기본 (ls, cd, mount, chmod)
- Shell scripting 기초
- SSH 사용법

**권장 지식**:
- Android 부팅 프로세스 이해
- Chroot 개념
- SELinux 기본

**학습할 내용**:
- Magisk 내부 구조 (프로젝트 중 학습)
- Mount namespace (실습을 통해 학습)
- 고급 디버깅 기법

---

## ⚠️ 위험 요소 및 대응

### 높은 위험

| 위험 | 발생 확률 | 영향 | 대응 방법 |
|------|----------|------|----------|
| **부팅 중단** | 30% | 높음 | TWRP에서 모듈 제거 |
| **마운트 포인트 오염** | 25% | 중간 | 언마운트 스크립트 |
| **SELinux 차단** | 40% | 중간 | supolicy 정책 추가 |

### 중간 위험

| 위험 | 발생 확률 | 영향 | 대응 방법 |
|------|----------|------|----------|
| **SSH 연결 실패** | 50% | 낮음 | 로그 확인 및 재시작 |
| **WiFi 미인식** | 20% | 중간 | 펌웨어 경로 마운트 |
| **타이밍 문제** | 35% | 중간 | sleep 추가 |

### 복구 방법

**Level 1: 모듈 비활성화**
```bash
# TWRP 리커버리 부팅
adb shell
rm /data/adb/modules/systemless_chroot/update
# 또는
rm -rf /data/adb/modules/systemless_chroot
reboot
```

**Level 2: Magisk 재설치**
```bash
# TWRP에서
adb push Magisk-v26.x.apk /sdcard/
# Install APK as ZIP
```

**Level 3: 전체 복원**
```bash
# TWRP Restore
# 또는 fastboot로 백업 이미지 플래시
```

---

## 📊 성공 기준

### 기능 요구사항

- ✅ Chroot 환경이 부팅 시 자동 마운트됨
- ✅ SSH 서버가 자동으로 시작됨
- ✅ WiFi를 통한 네트워크 접속 가능
- ✅ Debian/Ubuntu 패키지 관리 정상 작동
- ✅ Python, GCC 등 개발 도구 사용 가능

### 성능 요구사항

- ✅ RAM 사용량 800MB 이하
- ✅ 부팅 시간 60초 이하
- ✅ SSH 응답 시간 1초 이하
- ✅ 파일 I/O 성능 양호

### 안정성 요구사항

- ✅ 24시간 연속 운영 가능
- ✅ 재부팅 후 자동 복구
- ✅ 시스템 업데이트 후에도 작동
- ✅ 문제 발생 시 복구 가능

---

## 🎓 학습 체크리스트

이 프로젝트를 완료하면 다음을 이해하게 됩니다:

### Magisk 관련
- [ ] Magisk의 systemless 수정 원리
- [ ] Magic Mount 동작 방식
- [ ] post-fs-data.sh와 service.d의 차이
- [ ] Magisk 모듈 구조와 lifecycle

### Android 시스템
- [ ] Android 부팅 전체 과정
- [ ] init 시스템과 service 관리
- [ ] SELinux enforcing 모드에서의 작동
- [ ] Mount namespace와 프로세스 격리

### Linux 고급 기술
- [ ] Chroot 원리와 한계
- [ ] Bind mount와 propagation
- [ ] Capability와 권한 관리
- [ ] 시스템 수준 디버깅

### 문제 해결
- [ ] 부팅 로그 분석 능력
- [ ] Mount 문제 진단 및 해결
- [ ] SELinux 정책 문제 해결
- [ ] 타이밍 이슈 대응

---

## 🔄 대안 계획 (Fallback)

만약 Magisk Systemless Chroot 구현이 실패하거나 너무 복잡한 경우:

### Plan B: Linux Deploy
- 복잡도: 2.5/10
- 시간: 2-4시간
- RAM: 1-1.5GB
- 안정성: 95%

### Plan C: 하드웨어 변경
- OnePlus 6T + PostmarketOS
- 비용: $150-200
- 완전한 네이티브 Linux

---

## 📚 참고 자료

### 공식 문서
- [Magisk 공식 문서](https://topjohnwu.github.io/Magisk/)
- [Magisk GitHub](https://github.com/topjohnwu/Magisk)
- [Android Init Language](https://android.googlesource.com/platform/system/core/+/master/init/README.md)

### 커뮤니티
- [XDA Developers - A90 5G Forum](https://forum.xda-developers.com/)
- [r/androidroot](https://reddit.com/r/androidroot)
- [r/magisk](https://reddit.com/r/Magisk)

### 학습 리소스
- Linux Mount Namespaces 튜토리얼
- SELinux Policy Language 가이드
- Android Bootloader 분석 자료

---

## 📈 진행 상황 추적

**시작일**: 2025-11-14
**예상 완료일**: 2025-11-28 (14일 후)

**현재 상태**: Phase 1 계획 수립 완료

**다음 단계**:
1. Magisk Systemless 구현 가이드 작성
2. Magisk 내부 구조 분석 문서 작성
3. Android 부팅 프로세스 문서 작성

---

## ✅ 프로젝트 승인

**승인자**: User
**승인일**: 2025-11-14
**승인 조건**:
- Linux Deploy 경험이 있음
- 새로운 기술 학습 원함
- 5-14일 소요 시간 수용
- 복잡도 7.5/10 이해함

**기대 효과**:
- Android 시스템 깊은 이해
- 포트폴리오용 고급 프로젝트
- 다른 프로젝트에 재사용 가능한 기술
- 최대 RAM 절감 (500-800MB)

---

**다음 문서**: [MAGISK_SYSTEMLESS_GUIDE.md](../guides/MAGISK_SYSTEMLESS_GUIDE.md)
