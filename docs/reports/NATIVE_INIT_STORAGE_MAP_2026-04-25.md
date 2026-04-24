# Native Init Storage / Partition Map (2026-04-25)

이 문서는 `A90 Linux init v45` 기준으로 확인한 저장소/파티션 정보를 정리한다.
목표는 native init 환경에서 어떤 저장소를 안전하게 쓸 수 있고, 어떤 파티션은
읽기 전용 또는 절대 금지로 둬야 하는지 구분하는 것이다.

## 결론

- 현재 실제로 쓰는 persistent 저장소는 `/cache` 하나다.
- `/cache`는 by-name 기준 `cache -> /dev/block/sda31`이며 native init log 저장에 사용 중이다.
- Android 본체 파티션인 `system`, `vendor`, `product`는 당장 지우거나 쓰기 대상으로 보지 않는다.
- 대용량 후보는 `userdata -> /dev/block/sda33`이지만 Android FBE/user data와 엮여 있어 별도 백업/포맷 계획 없이는 쓰지 않는다.
- `efs`, `sec_efs`, modem, persist, keymaster/keystore, vbmeta, bootloader 계열은 저장소 후보가 아니라 **do-not-touch** 영역이다.
- major/minor 번호는 부팅/열거 순서에 따라 달라질 수 있으므로 hardcode하지 않고 `/sys/class/block/<name>/dev` 또는 by-name 기준으로 다룬다.

## 현재 native init 관찰값

기준:

- latest native init: `A90 Linux init v45`
- control: USB ACM serial bridge
- observed from: native init shell
- by-name source: `backups/baseline_a_20260423_030309/by_name_listing.txt`

현재 mount:

```text
rootfs / rootfs rw 0 0
proc /proc proc rw,relatime 0 0
sysfs /sys sysfs rw,relatime 0 0
tmpfs /tmp tmpfs rw,relatime 0 0
/dev/block/sda31 /cache ext4 rw,relatime,i_version 0 0
configfs /config configfs rw,relatime 0 0
/dev/block/sda28 /mnt/system ext4 ro,relatime,i_version 0 0
```

현재 active write:

```text
/cache/native-init.log
/cache/v*_step
```

## Android 영역과의 관계

native init이 쓰는 저장공간은 새로 만든 디스크가 아니라 Android 펌웨어가 이미 나눠 둔
UFS 파티션 중 일부를 직접 마운트한 것이다.

- `/cache`는 Android/TWRP도 cache 용도로 쓸 수 있는 기존 파티션이다.
  - 현재 native init은 이 영역에 log와 작은 상태 파일만 쓴다.
  - Android 본체 OS나 사용자 데이터와 직접 같은 의미의 영역은 아니다.
- `system`, `vendor`, `product`는 Android OS/vendor 구성 파티션이다.
  - native init에서는 reference로만 보고 read-only 정책을 유지한다.
- `userdata`는 Android 사용자 데이터/FBE 영역이다.
  - 용량은 크지만 Android 데이터를 유지하려면 저장소 후보로 쓰면 안 된다.
  - native Linux 전용 저장소로 전환하려면 백업, 포맷, 복구 경로를 먼저 확정해야 한다.
- `efs`, modem, key/security, bootloader 계열은 저장공간이 아니라 장치 정체성/무선/보안/부팅에 필요한 상태다.
  - 일반 파일 저장 목적으로 쓰면 안 된다.

## 주요 파티션 요약

크기는 `/proc/partitions`의 1 KiB block 기준이다.

| Name | Block | Size | 현재 판단 | 메모 |
|---|---:|---:|---|---|
| `cache` | `sda31` | 600 MiB | safe write | native init log 저장소로 검증 완료 |
| `system` | `sda28` | 5.8 GiB | read-only | `/mnt/system` ro mount 검증 |
| `vendor` | `sda29` | 1.3 GiB | read-only | vendor driver/userspace reference |
| `product` | `sda30` | 200 MiB | read-only | carrier/product config |
| `userdata` | `sda33` | 110.4 GiB | conditional | encrypted user data, 별도 계획 필요 |
| `boot` | `sda24` | 64 MiB | controlled write only | native init boot image flash 대상 |
| `recovery` | `sda25` | 79 MiB | keep known-good | TWRP 복구 경로 |
| `vbmeta` | `sdd24` | 64 KiB | do not touch | verified boot metadata |
| `efs` | `sda9` | 20 MiB | do not touch | device identity/radio critical |
| `sec_efs` | `sda12` | 20 MiB | do not touch | Samsung security/identity data |
| `persist` | `sda8` | 32 MiB | do not touch | calibration/persistent vendor data |
| `modem` | `sda21` | 195 MiB | do not touch | modem firmware |
| `modemst1` | `sda1` | 2 MiB | do not touch | radio NV data |
| `modemst2` | `sda2` | 2 MiB | do not touch | radio NV data |
| `fsg` | `sdd3` | 2 MiB | do not touch | modem/radio backup data |
| `keydata` | `sda27` | 16 MiB | do not touch | key/security data |
| `keyrefuge` | `sda26` | 16 MiB | do not touch | key/security data |
| `keymaster` | `sdd12` | 512 KiB | do not touch | secure world/keymaster |
| `keystore` | `sda14` | 512 KiB | do not touch | keystore metadata |
| `xbl` | `sdb1` | 4 MiB | do not touch | bootloader |
| `xbl_config` | `sdb2` | 4 MiB | do not touch | bootloader config |
| `abl` | `sdd8` | 4 MiB | do not touch | Android bootloader |
| `tz` | `sdd5` | 4 MiB | do not touch | TrustZone |
| `hyp` | `sdd33` | 1 MiB | do not touch | hypervisor |

## 저장소 등급

### Safe Write

#### `/tmp`

- Type: `tmpfs`
- Persistence: 없음
- 용도:
  - 임시 파일
  - 테스트 출력
  - 부팅 중 fallback log
- 주의:
  - 재부팅 시 사라짐

#### `/cache`

- by-name: `cache -> /dev/block/sda31`
- Type: `ext4`
- Mount: `/cache rw`
- Persistence: 재부팅/TWRP 왕복 후 보존 확인
- 용도:
  - `/cache/native-init.log`
  - 작은 static tool 후보
  - native init 상태 파일
- 주의:
  - Android/TWRP도 cache 성격으로 사용할 수 있음
  - 큰 바이너리 묶음이나 장기 데이터 저장소로 쓰기 전 용량 정책 필요

### Conditional

#### `userdata`

- by-name: `userdata -> /dev/block/sda33`
- Size: 약 110 GiB
- Android property 기준:
  - `ro.crypto.state=encrypted`
  - `ro.crypto.type=file`
- 판단:
  - native Linux 저장공간으로는 가장 큰 후보
  - 하지만 Android 사용자 데이터/FBE/metadata와 엮일 수 있음
  - Android를 유지할 생각이 있으면 쓰지 않음
  - Android 포기를 전제로 해도 전체 백업과 복구 절차 확인 후 별도 포맷 계획 필요

#### `mmcblk0p1`

- Size: 약 59.6 GiB
- by-name mapping 없음
- `removable=0`로 관찰됨
- 판단:
  - 현재 정체 미확인
  - 파일시스템/용도 식별 전까지 쓰지 않음
  - 추후 `blkid`, filesystem probe, TWRP mount 목록으로 확인 필요

### Read-only Reference

#### `system`

- by-name: `system -> /dev/block/sda28`
- Mount: `/mnt/system ro`
- 용도:
  - Android root/system-as-root 구조 참고
  - Android dynamic binary 실험 시 reference
  - TWRP/Android 복구 기준
- 정책:
  - native init에서는 ro mount만 허용

#### `vendor`, `product`, `omr`

- by-name:
  - `vendor -> /dev/block/sda29`
  - `product -> /dev/block/sda30`
  - `omr -> /dev/block/sda32`
- 용도:
  - vendor firmware/userspace/config reference
  - carrier/OMR config reference
- 정책:
  - 아직 mount/write 대상 아님
  - 추후 read-only mount helper가 생기면 ro만 허용

### Controlled Write Only

#### `boot`

- by-name: `boot -> /dev/block/sda24`
- 현재 native init boot image flash 대상
- 정책:
  - `native_init_flash.py` 경로로만 기록
  - image SHA256 확인 후 기록
  - known-good boot 백업 유지

#### `recovery`

- by-name: `recovery -> /dev/block/sda25`
- TWRP 복구 경로
- 정책:
  - 현재는 건드리지 않음
  - TWRP 유지가 native init 실험의 안전망

### Do Not Touch

아래 계열은 native Linux 저장소 후보가 아니다.

- identity/radio:
  - `efs`
  - `sec_efs`
  - `modemst1`
  - `modemst2`
  - `fsg`
  - `fsc`
  - `mdm1m9kefs1`
  - `mdm1m9kefs2`
  - `mdm1m9kefs3`
  - `mdm1m9kefsc`
- calibration/persistent vendor:
  - `persist`
  - `persistent`
  - `param`
  - `misc`
- secure/key material:
  - `keydata`
  - `keyrefuge`
  - `keymaster`
  - `keystore`
  - `storsec`
  - `secdata`
  - `uefisecapp`
  - `uefivarstore`
- bootloader/secure boot:
  - `xbl`
  - `xbl_config`
  - `abl`
  - `aop`
  - `tz`
  - `hyp`
  - `cmnlib`
  - `cmnlib64`
  - `devcfg`
  - `vbmeta`
- modem/firmware:
  - `modem`
  - `apnhlos`
  - `dsp`
  - `bluetooth`
  - `qupfw`

## 설계 규칙

1. 파티션 접근은 이름 기준으로 생각한다.
   - 예: `cache`, `system`, `userdata`
   - `/dev/block/sda31` 같은 경로는 by-name 결과로만 해석한다.
2. major/minor는 hardcode하지 않는다.
   - v41에서 hardcoded minor 때문에 `/cache` mount가 실패한 사례가 있었다.
   - 현재 init은 `/sys/class/block/<name>/dev`를 읽어 node를 만든다.
3. writable persistent storage의 1차 기준은 `/cache`다.
4. 대용량 저장소는 `userdata`를 후보로 보되 Android 데이터 포기/백업/포맷 계획 전에는 쓰지 않는다.
5. 복구 경로인 TWRP `recovery`와 known-good `boot` 백업을 항상 유지한다.

## 다음 작업

- native init shell에 `blockinfo` 또는 `byname` 명령 추가 검토
- `/cache/bin` tool path 정책 정리
- `userdata`를 native data partition으로 쓸지 여부는 별도 의사결정 문서 작성
- `mmcblk0p1` 정체 확인
- USB gadget map report 작성
