# Samsung Galaxy A90 5G 커널 분석 보고서

## 현재 커널 정보 (Stock Android)

### 기본 정보
```
커널 버전: Linux 4.14.190
빌드 버전: 25818860-abA908NKSU5EWA3
컴파일러: Clang 10.0.7 for Android NDK
링커: GNU ld 2.27.0 (binutils-2.27-bd24d23f)
빌드 날짜: 2023년 1월 12일 18:53:40 KST
빌드 머신: dpi@SWDK6110
프리엠션: SMP PREEMPT
```

### 주요 특징
- **커널 베이스**: Linux 4.14 LTS (Android 기기에서 흔히 사용)
- **SoC**: Qualcomm Snapdragon 855 (SM8150)
- **아키텍처**: ARM64
- **빌드 타입**: PREEMPT (실시간 응답성 향상)

### 활성화된 주요 Kconfig
```
CONFIG_FTRACE       - 커널 함수 추적
CONFIG_ARM64        - ARM64 아키텍처
CONFIG_DM_VERITY    - Device-Mapper Verity (무결성 검증)
CONFIG_DM_VERITY_FEC - Forward Error Correction
CONFIG_SECURITY     - 보안 프레임워크
CONFIG_INTEGRITY    - 무결성 서브시스템
CONFIG_MODULES      - 커널 모듈 지원
```

### 비활성화된 Kconfig
```
CONFIG_LWTUNNEL is not enabled - Lightweight Tunnel (VPN/터널링)
```

## Samsung vs Mainline Linux 비교

### 커널 버전 차이

| 항목 | Stock Android | Mainline (우리가 시도) | 차이점 |
|------|---------------|----------------------|--------|
| **버전** | 4.14.190 | 6.1 LTS | +2년 차이, 많은 변경사항 |
| **컴파일러** | Clang 10.0.7 | GCC 13.x (aarch64-linux-gnu) | 컴파일러 완전히 다름 |
| **빌드 날짜** | 2023-01-12 | 2025-11-13 | 2년 차이 |
| **Samsung 패치** | 있음 (25818860-ab) | 없음 | **핵심 차이** |

### 주요 드라이버 차이점

#### Stock Android 커널에만 있는 것들:

**1. Qualcomm 전용 드라이버**
```
qcom,gcc-sm8150          - Global Clock Controller
qcom,gcc-sm8150-v2       - GCC v2 variant
qcom,gcc-sa8155          - SA8155 automotive variant
qcom,debugcc-sm8150      - Debug Clock Controller
qcom,sdxprairie-apcs-gcc - APCS GCC
```

**2. Samsung 전용 드라이버**
```
- 디스플레이: S6E3FC2_AMS670TA01 패널 드라이버
- UFS 스토리지: Samsung UFS 최적화
- PMIC: 전원 관리 IC
- 충전: max77705 충전 컨트롤러
- 배터리: 삼성 배터리 FG (Fuel Gauge)
```

**3. 카메라 서브시스템**
```
qcom,cam-a5              - ARM Cortex-A5 프로세서
qcom,cam-bps             - Bayer Processing Subsystem
qcom,cam-cdm-intf        - CDM Interface
qcom,cam-cpas            - Camera Platform Architecture Subsystem
qcom,cam-fd              - Face Detection
qcom,cam-icp             - Image Control Processor
qcom,cam-ipe             - Image Processing Engine
qcom,cam-isp             - Image Signal Processor
qcom,cam-jpeg            - JPEG 인코더
qcom,cam-lrme            - Low Resolution Motion Estimator
```

**4. 오디오 서브시스템**
```
qcom,msm-pcm-routing     - PCM 라우팅
qcom,msm-pcm-dsp-noirq   - DSP Non-IRQ
qcom,msm-pcm-hostless    - Hostless PCM
qcom,audio-pkt           - 오디오 패킷
qcom,avtimer             - AV 타이머
```

**5. 기타 Qualcomm 드라이버**
```
qcom,aop-ddr-msgs        - Always-On Processor DDR 메시지
qcom,aop-ddrss-cmds      - DDR Subsystem 명령어
qcom,aop-qmp-clk         - QMP 클럭
qcom,arm-cpu-mon         - CPU 모니터링
qcom,arm-memlat-mon      - Memory Latency 모니터링
qcom,bimc-bwmon4/5       - 대역폭 모니터링
qcom,btfmslim_slave      - Bluetooth FM SLIMbus
qcom,kgsl-hyp            - KGSL Hypervisor
```

## 왜 Mainline Linux 6.1이 실패했는가?

### 1. 드라이버 부재
Mainline Linux 6.1에는 위의 **Samsung/Qualcomm 전용 드라이버들이 전혀 없음**:
- ❌ UFS 스토리지 초기화 실패
- ❌ 디스플레이 패널 인식 불가
- ❌ PMIC/전원 관리 오류
- ❌ 카메라 서브시스템 없음

### 2. Device Tree 불일치
```
Stock:     정확한 SM-A908N 전용 DTB (Samsung이 생성)
Mainline:  sm8150-mtp.dtb (범용 개발 보드용)
```

**결과**: 하드웨어 주소, GPIO 매핑, 클럭 설정 모두 불일치

### 3. 부트 프로토콜 차이
```
Stock:     Samsung Bootloader 전용 설정
Mainline:  표준 Linux ARM64 부트 프로토콜
```

pstore 로그에서 발견:
```
WARNING: x1-x3 nonzero in violation of boot protocol
This indicates a broken bootloader or old kernel
```

### 4. 보안 프레임워크
Stock Android는 다음을 요구:
- dm-verity (루트 파일시스템 무결성)
- SELinux
- AVB (Android Verified Boot)

Mainline 커널에는 이런 설정 없음.

## 오픈소스 커널 다운로드 전략

### 확인된 정보
- **버전 일치**: A908NKSU5EWA3 (현재 커널과 정확히 동일!)
- **소스 제공**: https://opensource.samsung.com
- **파일명**: SM-A908N_KOR_12_Opensource.zip

### 예상 내용
1. **Linux 4.14.190 소스**
2. **Samsung 패치셋** (25818860-ab)
3. **SM-A908N 전용 Device Tree**
4. **모든 드라이버 소스코드**:
   - UFS 스토리지
   - 디스플레이 (S6E3FC2)
   - PMIC/배터리
   - WiFi (qca_cld)
   - 카메라
   - 오디오

### 우리가 해야 할 작업

#### ✅ 이미 완료
1. Busybox 2.1MB static binary 빌드
2. initramfs 생성 (1.2MB)
3. mkbootimg 파이프라인 확립

#### 🔄 Samsung 커널 빌드 시
1. **소스 다운로드 및 압축 해제**
2. **기존 defconfig 확인**
   ```bash
   # arch/arm64/configs/ 에서 SM-A908N 설정 찾기
   # 아마도: r3q_defconfig 또는 a90_defconfig
   ```
3. **initramfs 통합**
   ```
   CONFIG_INITRAMFS_SOURCE="../../initramfs_build/initramfs"
   CONFIG_INITRAMFS_COMPRESSION_GZIP=y
   ```
4. **불필요한 것 제거** (선택사항)
   - Android 관련 드라이버 (일부)
   - SELinux (선택적)
   - dm-verity (선택적)

5. **빌드**
   ```bash
   make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j22
   ```

6. **boot.img 생성**
   - 기존 방법과 동일
   - DTB는 Samsung 소스에서 나온 것 사용

### 주의사항

#### ⚠️ Clang vs GCC
- Samsung은 **Clang 10.0.7** 사용
- 우리는 **GCC 13.x** 사용
- **호환성 이슈 가능**

**대안**:
1. 일단 GCC로 시도 (간단함)
2. 실패 시 Clang 10.0.7 다운로드

#### ⚠️ 커널 버전 변경 금지
- **4.14.190 그대로 유지**
- 버전 변경하면 드라이버 깨짐

## 다음 단계 체크리스트

- [ ] Android 부팅 후 추가 정보 수집
  - [ ] /proc/config.gz 확인
  - [ ] /proc/cmdline 확인
  - [ ] dmesg 드라이버 로딩 순서 확인
- [ ] SM-A908N_KOR_12_Opensource.zip 다운로드
- [ ] 소스 압축 해제 및 구조 분석
- [ ] defconfig 찾기 및 확인
- [ ] initramfs 통합 방법 결정
- [ ] 빌드 시도

## 예상 결과

### 성공 시나리오
Samsung 커널 + Busybox initramfs로 부팅하면:
1. ✅ UFS 스토리지 정상 인식
2. ✅ 디스플레이 초기화 (framebuffer 콘솔)
3. ✅ PMIC/전원 관리 정상
4. ✅ Busybox shell 접근
5. ✅ WiFi 드라이버 로드 가능 (Phase 2)

### 최악 시나리오
실패 시에도:
- TWRP 백업으로 복구 가능
- 모든 파티션 백업 완료됨
- 복구 프로세스 확립됨

---

**작성일**: 2025-11-13
**다음 업데이트**: Android 부팅 후 /proc/config.gz 분석
