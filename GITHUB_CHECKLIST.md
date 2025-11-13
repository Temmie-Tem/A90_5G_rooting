# GitHub 업로드 체크리스트

## ✅ 올려야 할 파일 (PUBLIC)

### 문서
- [x] `README.md` - 프로젝트 소개 및 빠른 시작
- [x] `NATIVE_LINUX_BOOT_PLAN.md` - 전체 계획 및 로드맵
- [x] `LICENSE` - MIT 라이선스
- [x] `.gitignore` - 민감한 파일 제외 설정
- [ ] `CONTRIBUTING.md` - 기여 가이드라인 (나중에 추가)
- [ ] `CHANGELOG.md` - 변경 이력 (진행하면서 추가)

### 기술 문서
- [x] `temp_docs/galaxy-a90-5g-technical-documentation.md`
- [x] `temp_docs/*.txt` - 하드웨어 정보 (개인정보 없음)

### 스크립트 및 설정 파일 (작성 후)
- [ ] `scripts/backup.sh` - 백업 자동화 스크립트
- [ ] `scripts/extract_firmware.sh` - 펌웨어 추출 스크립트
- [ ] `scripts/setup_dev_env.sh` - 개발 환경 구축
- [ ] `configs/kernel_config` - 커널 설정 템플릿
- [ ] `configs/deviceinfo` - PostmarketOS 디바이스 정보
- [ ] `patches/` - 필요한 커널 패치들

### PostmarketOS 패키지 파일 (작성 후)
- [ ] `pmaports/device-samsung-r3q/` - 디바이스 패키지
- [ ] `pmaports/linux-samsung-r3q/` - 커널 패키지
- [ ] `pmaports/firmware-samsung-r3q/` - 펌웨어 패키지 (바이너리 제외)

---

## ❌ 올리면 안 되는 파일 (PRIVATE/SENSITIVE)

### 백업 파일 (절대 업로드 금지!)
- ❌ `backup_boot.img`
- ❌ `backup_recovery.img`
- ❌ `backup_*.img` (모든 파티션 백업)
- ❌ `backup_efs.tar.gz` (IMEI 등 민감 정보 포함!)
- ❌ `A90_backup/` 디렉토리 전체

### 추출한 펌웨어 (재배포 금지)
- ❌ `wifi_firmware/` 디렉토리
- ❌ `qwlan30.bin`, `bdwlan30.bin`, `Data.msc`
- ❌ `/vendor/firmware/` 에서 추출한 모든 바이너리
- ❌ `extracted_firmware/` 디렉토리

**대신 포함**: 펌웨어 추출 스크립트 + 다운로드 링크

### Samsung 커널 소스 (용량 크고 공식에서 다운로드 가능)
- ❌ `samsung_kernel/` 디렉토리
- ❌ `kernel.tar.gz`

**대신 포함**: 
- 다운로드 링크 (https://opensource.samsung.com/)
- 사용한 커널 버전 및 설정만

### 빌드 아티팩트
- ❌ `*.img` (boot.img, recovery.img 등)
- ❌ `*.dtb`, `*.dtbo`
- ❌ `*.ko` (커널 모듈)
- ❌ `Image`, `Image.gz`, `Image.gz-dtb`
- ❌ `*.cpio.gz` (initramfs)
- ❌ `*.o` (오브젝트 파일)

### 개인 설정
- ❌ `wpa_supplicant.conf` (WiFi 비밀번호 포함!)
- ❌ `ssh_keys/`, `*.pem`, `*.key`
- ❌ 개인 IP 주소, MAC 주소가 포함된 로그

### 임시 파일
- ❌ `*.log`, `*.swp`, `*~`
- ❌ `.DS_Store`
- ❌ IDE 설정 (`.vscode/`, `.idea/`)

### pmbootstrap 작업 디렉토리
- ❌ `~/.local/var/pmbootstrap/` (로컬에만 유지)

---

## 📝 민감 정보 제거 체크리스트

업로드 전 반드시 확인:

### 1. 개인 식별 정보
- [ ] WiFi SSID, 비밀번호
- [ ] IP 주소, MAC 주소
- [ ] 이메일 주소, 실명
- [ ] 디바이스 시리얼 번호, IMEI

### 2. 로그 파일 확인
```bash
# 민감 정보 검색
grep -r "SSID\|password\|192.168\|wpa_passphrase" .
grep -r "IMEI\|Serial" .
grep -r "@gmail\|@naver\|@kakao" .
```

### 3. Git 히스토리 확인
```bash
# 실수로 커밋된 민감 파일 확인
git log --all --full-history -- "*.img"
git log --all --full-history -- "wpa_supplicant.conf"
```

---

## 🚀 업로드 전 최종 점검

### 1. .gitignore 테스트
```bash
# 제외되어야 할 파일들이 추적되지 않는지 확인
git status --ignored

# 민감한 확장자 체크
find . -name "*.img" -o -name "*.bin" -o -name "*backup*"
```

### 2. 문서 검토
- [ ] README.md가 최신 상태인가?
- [ ] 모든 링크가 작동하는가?
- [ ] 라이선스가 명확한가?
- [ ] 면책 조항이 포함되어 있는가?

### 3. 저작권 확인
- [ ] Samsung 커널 소스: 직접 포함 ❌, 다운로드 링크 ✅
- [ ] WiFi 펌웨어: 바이너리 포함 ❌, 추출 스크립트 ✅
- [ ] 참고한 코드: 출처 명시 ✅

### 4. 첫 커밋 준비
```bash
# 안전한 파일만 추가
git add README.md
git add LICENSE
git add .gitignore
git add NATIVE_LINUX_BOOT_PLAN.md
git add temp_docs/

# 상태 확인
git status

# 민감 파일이 없는지 최종 확인
git diff --cached

# 커밋
git commit -m "Initial commit: Project documentation and roadmap"

# 푸시 전 한 번 더 확인!
git log -p
```

---

## 📂 권장 폴더 구조

```
A90_5G_rooting/
├── README.md                    ✅ PUBLIC
├── LICENSE                      ✅ PUBLIC
├── .gitignore                   ✅ PUBLIC
├── NATIVE_LINUX_BOOT_PLAN.md    ✅ PUBLIC
├── CONTRIBUTING.md              ✅ PUBLIC (나중에)
├── CHANGELOG.md                 ✅ PUBLIC (나중에)
│
├── docs/                        ✅ PUBLIC
│   ├── hardware/
│   ├── troubleshooting/
│   └── faq.md
│
├── temp_docs/                   ✅ PUBLIC
│   ├── *.md
│   └── *.txt
│
├── scripts/                     ✅ PUBLIC
│   ├── backup.sh
│   ├── extract_firmware.sh
│   └── setup_dev_env.sh
│
├── configs/                     ✅ PUBLIC
│   ├── kernel_config
│   └── deviceinfo
│
├── pmaports/                    ✅ PUBLIC
│   ├── device-samsung-r3q/
│   ├── linux-samsung-r3q/
│   └── firmware-samsung-r3q/
│
├── patches/                     ✅ PUBLIC
│   └── *.patch
│
└── .private/                    ❌ PRIVATE (로컬에만)
    ├── backups/
    │   ├── backup_boot.img
    │   └── backup_*.img
    ├── firmware/
    │   └── *.bin
    ├── samsung_kernel/
    └── personal_notes.md
```

---

## ⚠️ 실수로 민감 파일을 커밋했다면?

### 최근 커밋에서 제거
```bash
git rm --cached backup_boot.img
git commit --amend
```

### 히스토리에서 완전 제거 (BFG 사용)
```bash
# BFG Repo Cleaner 다운로드
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# 민감 파일 제거
java -jar bfg-1.14.0.jar --delete-files backup_*.img

# 정리
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 강제 푸시 (주의!)
git push --force
```

---

## 📋 업로드 후 할 일

- [ ] GitHub 저장소 Description 설정
- [ ] Topics 추가: `postmarketos`, `samsung`, `snapdragon-855`, `linux`, `android`
- [ ] GitHub Pages 활성화 (선택)
- [ ] Issue 템플릿 추가
- [ ] Pull Request 템플릿 추가
- [ ] GitHub Actions 설정 (CI/CD, 나중에)
- [ ] XDA 포럼에 포스팅
- [ ] PostmarketOS Wiki에 디바이스 등록

---

**마지막 확인**: 업로드하기 전에 이 체크리스트를 한 번 더 검토하세요!
