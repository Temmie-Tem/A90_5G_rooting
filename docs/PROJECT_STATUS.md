# Samsung Galaxy A90 5G - 프로젝트 현황

## 📊 프로젝트 정보

**디바이스**: Samsung Galaxy A90 5G (SM-A908N)
**SoC**: Qualcomm Snapdragon 855 (SM8150)
**RAM**: 5.5GB (현재 ~5GB 사용 중)
**상태**: Phase 0 완료, 대안 검토 중

---

## ✅ Phase 0: 네이티브 부팅 연구 (완료)

**기간**: 2025-11-13 ~ 2025-11-14
**결과**: ❌ **네이티브 부팅 불가능 확인**

### 주요 발견
1. ABL이 Android ramdisk 강제 주입 (하드코딩)
2. Knox/AVB가 /system 파티션 무결성 강제
3. PBL이 SD 카드 부팅 미지원
4. Mainline 커널의 Samsung 하드웨어 미지원

### 실행한 테스트
- ✅ 5회 커널 부팅 시도
- ✅ Android init 하이재킹 시도
- ✅ Magisk overlay.d 조사
- ✅ 완전한 문서화

### 참조 문서
- [Phase 0 연구 결과](../archive/phase0_native_boot_research/PROGRESS_LOG_PHASE0.md)
- [네이티브 부팅 계획](NATIVE_LINUX_BOOT_PLAN.md)
- [대안 계획](ALTERNATIVE_PLAN.md)

---

## 🎯 다음 계획 (미정)

### Option 1: Termux + proot-distro (권장) ⭐⭐⭐⭐⭐
- **목표**: Android 위에서 완전한 Linux 환경
- **RAM**: ~800MB-1GB
- **기간**: 1-2일
- **난이도**: ⭐ 쉬움
- **안정성**: 최고
- **WiFi/SSH**: 완벽 동작

### Option 2: 하드웨어 변경 (OnePlus 6T) ⭐⭐⭐⭐
- **목표**: 완전한 네이티브 Linux (PostmarketOS)
- **RAM**: ~200MB
- **비용**: $150-200 (중고)
- **난이도**: ⭐⭐⭐ 중상
- **완전한 네이티브**: ✅

### Option 3: Magisk Headless Android ⭐⭐
- **목표**: Android 최소화 + Linux 툴
- **RAM**: ~600-800MB
- **기간**: 1-2주
- **난이도**: ⭐⭐⭐⭐ 어려움
- **안정성**: 불확실

---

## 📁 프로젝트 구조

```
A90_5G_rooting/
├── archive/                    # 아카이브된 연구 자료
│   └── phase0_native_boot_research/
│       ├── README.md
│       ├── PROGRESS_LOG_PHASE0.md
│       ├── kernel_build/       # 9.5GB
│       ├── initramfs_build/    # 65MB
│       ├── system_mods/        # 12KB
│       └── boot_image/         # 392MB
├── backups/                    # TWRP 백업 (중요!)
│   ├── backup_boot.img
│   ├── backup_recovery.img
│   ├── backup_abl.img          # 매우 중요
│   ├── backup_efs.tar.gz       # 매우 중요 (IMEI)
│   └── ...
├── docs/                       # 문서
│   ├── PROJECT_STATUS.md       # 이 파일
│   ├── PROGRESS_LOG.md         # 현재 진행 로그
│   ├── NATIVE_LINUX_BOOT_PLAN.md
│   └── ALTERNATIVE_PLAN.md
├── logs/                       # 부팅 로그
│   ├── boot_no_rdinit.log
│   ├── boot_hijack_test1.log
│   └── ...
├── mkbootimg/                  # 부팅 이미지 도구
├── toolchains/                 # 크로스 컴파일 도구 (5.1GB)
└── wifi_firmware/              # WiFi 펌웨어 (4.3MB)
```

---

## 🔒 중요 백업 파일 (절대 삭제 금지)

### 필수 백업
- `backups/backup_abl.img` - ABL (부트로더)
- `backups/backup_efs.tar.gz` - IMEI/MAC 주소
- `backups/backup_boot.img` - 원본 부팅 이미지
- `backups/backup_recovery.img` - TWRP 리커버리

### 복구 방법
```bash
# Download Mode 진입: 전원 + 볼륨 다운
fastboot flash boot backups/backup_boot.img
fastboot flash recovery backups/backup_recovery.img
fastboot reboot
```

---

## 📈 디스크 사용량

```
toolchains/           5.1GB  (크로스 컴파일 도구)
archive/              10GB   (Phase 0 연구 자료)
backups/              435MB  (TWRP 백업)
SM-A908N_*.zip        233MB  (커널 소스)
wifi_firmware/        4.3MB
logs/                 1.2MB
docs/                 360KB
───────────────────────────
Total                 ~16GB
```

---

## 🎓 학습 내용

### 성공적으로 이해한 것
1. ✅ Qualcomm Secure Boot 체인 (PBL → SBL → ABL)
2. ✅ Samsung Knox 보안 구조
3. ✅ AVB/dm-verity 무결성 검증 메커니즘
4. ✅ Android init 프로세스
5. ✅ Magisk systemless 수정 방식
6. ✅ Linux initramfs vs Android ramdisk 차이

### 실패에서 배운 것
1. ❌ ABL 하드코딩은 우회 불가능
2. ❌ Knox/AVB 체인은 매우 강력
3. ❌ /system 수정은 자동 복원됨
4. ❌ SD 카드 직접 부팅은 PBL 제약
5. ❌ 완전한 네이티브는 하드웨어 변경 필요

---

## 🚀 다음 세션 준비

### 새 테스트 시작 시
1. 새로운 PROGRESS_LOG 생성
2. 명확한 목표 설정
3. 롤백 계획 수립
4. 백업 확인

### Termux 시작 시
- F-Droid 설치
- Termux 설치
- proot-distro 설정
- SSH 서버 구성

### 하드웨어 변경 고려 시
- OnePlus 6T 중고 가격 조사
- PostmarketOS 지원 확인
- 커뮤니티 리소스 확인

---

## 📞 연락처 및 리소스

### 커뮤니티
- XDA Developers: [SM-A908N 포럼](https://forum.xda-developers.com/samsung-galaxy-a90-5g)
- PostmarketOS: [Wiki](https://wiki.postmarketos.org/)
- Reddit: /r/postmarketos, /r/androidroot

### 참조 문서
- [Samsung 오픈소스](https://opensource.samsung.com/)
- [Qualcomm Boot Flow](https://source.android.com/docs/core/architecture/bootloader)
- [Magisk 문서](https://topjohnwu.github.io/Magisk/)

---

**마지막 업데이트**: 2025-11-14
**Phase 0 상태**: ✅ 완료
**다음 단계**: 사용자 결정 대기
