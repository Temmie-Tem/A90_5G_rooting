# Native Init Shell Probe (2026-04-23)

이 문서는 `v8` 기준 `native init + USB ACM serial shell` 환경에서
`/proc`, `/dev`, `/sys/class`, `system-as-root` 구조를 직접 조회해
현재 단계에서 활용 가능한 커널/하드웨어 정보를 정리한 기록이다.

관찰은 host의 `serial -> TCP` 브릿지
(`scripts/revalidation/serial_tcp_bridge.py`)를 통해 수행했다.

---

## 요약

- `native init` 단계에서 **인터랙티브 텍스트 제어 채널은 이미 충분히 확보**됨
- Android userspace 없이도 다음 커널 클래스들이 이미 살아 있음:
  - backlight
  - DRM/KMS
  - input
  - power_supply
  - USB UDC
- 반면 `runandroid`와 `adbd`는 여전히 불안정
  - `toybox` 실행 시 `SIGSEGV`
  - `adbd`는 zombie 상태로 종료
  - FunctionFS에는 `ep0`만 있고 `ep1/ep2`가 생성되지 않음
- 따라서 다음 우선순위는 Android userspace 재사용보다
  **현재 shell에서 하드웨어 관찰/제어 범위를 더 넓히는 쪽**이 합리적임

---

## 직접 관찰값

### 커널 / 플랫폼

- kernel:
  - `Linux 4.14.190-25818860-abA908NKSU5EWA3`
- cmdline 주요 항목:
  - `init=/init`
  - `androidboot.verifiedbootstate=orange`
  - `androidboot.usbcontroller=a600000.dwc3`
  - `video=vfb:640x400,bpp=32,memsize=3072000`
- CPU:
  - `Qualcomm Technologies, Inc SM8150`
  - 8 cores visible in `/proc/cpuinfo`

### 메모리

- `MemTotal: 5472168 kB`
- `MemFree: 5211716 kB`
- `MemAvailable: 5235524 kB`
- swap 없음 (`SwapTotal: 0 kB`)

해석:
- 현재 shell 단계는 메모리 압박이 거의 없고,
  추가 probe/driver 실험 여유가 큼

### 마운트

`/proc/mounts` 기준:

- `rootfs / rootfs rw`
- `proc /proc`
- `sysfs /sys`
- `tmpfs /tmp`
- `/dev/block/sda31 /cache ext4 rw`
- `configfs /config`
- `/dev/block/sda28 /mnt/system ext4 ro`
- `adb /dev/usb-ffs/adb functionfs rw`

추가 관찰:
- `prepareandroid`를 반복 호출하면서 `/system` bind mount가 중복 기록됨
- 기능상 치명적이지는 않지만, 이후 `prepareandroid` idempotency 정리는 필요

### 블록 장치 / 루트 구조

- 직접 만든 노드:
  - `/dev/block/sda28`
  - `/dev/block/sda31`
- `mountsystem`로 `/mnt/system` 마운트 가능
- `system-as-root` 구조 재확인:
  - `/mnt/system` 아래에 Android root tree 존재
  - `/mnt/system/system` 아래에 실제 `bin`, `lib64`, `framework`, `app`, `etc` 존재

의미:
- 현재 shell에서 Android 파티션 자체를 관찰하는 데는 충분
- Android userspace를 실제 실행하는 문제와
  Android 파일시스템을 읽는 문제는 분리해서 봐야 함

---

## 하드웨어 클래스 관찰

### USB / serial

- UDC:
  - `/sys/class/udc/a600000.dwc3`
- serial console:
  - `/dev/ttyGS0`
- host 측 ACM:
  - `/dev/ttyACM0`
- 브릿지:
  - `127.0.0.1:54321` TCP 노출 확인

### FunctionFS / ADB 관련

실측:

- `/dev/usb-ffs/adb/ep0` 존재
- `ep0` 상태:
  - `mode=0600 uid=2000 gid=2000 size=0`
- `ep1`, `ep2` 미생성
- `adbd` 상태:
  - zombie

의미:
- FunctionFS mount 자체는 됨
- 그러나 descriptors/strings가 정상 등록되지 않아
  bulk endpoints가 생기지 않음
- host `lsusb -v` 기준으로도 ACM 2-interface만 보이고,
  ADB interface는 나타나지 않음

### 입력

- `/sys/class/input`에 `event0` ~ `event8` 존재
- 현재 확인된 input 이름:
  - `input0`: `qpnp_pon`
  - `input1`: `meta_event`
  - `input2`: `grip_sensor`
  - `input3`: `gpio_keys`
  - `input4`: `hall`
  - `input5`: `certify_hall`
  - `input6`: `sec_touchscreen`
  - `input7`: `sec_touchproximity`
  - `input8`: `sec_touchpad`
- event capability 관찰:
  - 일부 event 노드는 `key`, `sw`, `msc` 위주
  - 일부는 `abs` 포함 (`touchscreen`/sensor 후보)
  - `gpio_keys`가 존재하므로 전원/볼륨키 계열 입력 추적 가능성이 높음
- 실측 버튼 매핑:
  - `event0` (`qpnp_pon`) → `code 0x0074`
    - press/release 쌍 확인
    - Linux input 기준 `KEY_POWER`
  - `event3` (`gpio_keys`) → `code 0x0073`
    - press/release 쌍 확인
    - Linux input 기준 `KEY_VOLUMEUP`
- raw capability bitmap 기준 최종 해석:
  - `event0` key bitmap = `14000000000000 0`
    - 64-bit word 기준 bit 50 + bit 52 set
    - 각각 `114 (KEY_VOLUMEDOWN)` + `116 (KEY_POWER)`
  - `event3` key bitmap = `8000000000000 0`
    - 64-bit word 기준 bit 51 set
    - `115 (KEY_VOLUMEUP)`

따라서 버튼 매핑은:

- `event0 (qpnp_pon)`:
  - `KEY_POWER`
  - `KEY_VOLUMEDOWN`
- `event3 (gpio_keys)`:
  - `KEY_VOLUMEUP`

후속 검증:

- `v13`에서 `inputcaps` bitmap word ordering을 수정한 뒤
  아래 출력으로 자동 해석도 실측과 일치함을 재확인:
  - `inputcaps event0`
    - `KEY_VOLUMEDOWN(114)=yes`
    - `KEY_VOLUMEUP(115)=no`
    - `KEY_POWER(116)=yes`
  - `inputcaps event3`
    - `KEY_VOLUMEDOWN(114)=no`
    - `KEY_VOLUMEUP(115)=yes`
    - `KEY_POWER(116)=no`

의미:
- 입력 장치 enumeration은 이미 끝난 상태
- 다음 probe로 각 이벤트 노드의 이름/능력을 읽으면
  볼륨키·터치·전원키 등 식별 가능성이 높음

### 백라이트

- `/sys/class/backlight/panel0-backlight`
- 현재 brightness: `255`
- max_brightness: `365`
- `panel0-backlight` sysfs 디렉토리 자체는 정상 노출
- `v9`에서 `writefile` 추가 후 실측:
  - `writefile /sys/class/backlight/panel0-backlight/brightness 32`
  - 이후 `cat .../brightness` → `32`
  - 다시 `writefile ... 255` 후 `cat .../brightness` → `255`

의미:
- 최소한 패널 백라이트 제어용 sysfs는 살아 있음
- 화면 출력이 없어도 backlight 변화 실험은 가능
- 따라서 현재 custom shell은
  **기본 sysfs write 실험을 수행할 수 있는 수준**까지 도달함

### DRM / graphics

- `/sys/class/drm` 관찰값:
  - `card0`
  - `card0-DSI-1`
  - `card0-DP-1`
  - `card0-Virtual-1`
  - `renderD128`
  - `sde-crtc-0`
  - `sde-crtc-1`
  - `sde-crtc-2`
- `card0-DSI-1` 내부:
  - `enabled`
  - `status`
  - `modes`
  - `dpms`
  - `edid`
  - `uevent`
- `card0` 내부:
  - `sde-crtc-0`
  - `sde-crtc-1`
  - `sde-crtc-2`
  - `card0-DSI-1`
  - `card0-Virtual-1`
  - `card0-DP-1`

의미:
- DRM/KMS 계층은 커널에서 이미 올라와 있음
- 현재 `/dev`에 `dri/*` 노드가 자동으로 보이지 않았지만,
  sysfs 기준으로는 화면 경로 탐색이 가능한 상태
- 특히 DSI connector 속성이 이미 보이므로,
  최소한 connector 상태/모드 관찰은 현재 shell에서도 가능

### 전원

- `/sys/class/power_supply` 관찰값:
  - `battery`
  - `usb`
  - `otg`
  - charger/fuelgauge 계열 다수

의미:
- 배터리/충전/USB 전원 상태는 추가 관찰 가능

### 네트워크

- `/sys/class/net` 관찰값:
  - `lo`
  - `dummy0`
  - `bond0`
  - `sit0`
  - `ip_vti0`
  - `ip6tnl0`
  - `ip6_vti0`
- USB networking 인터페이스 (`rndis*`, `usb*`)는 아직 없음

의미:
- 네트워크 스택 자체는 커널에 존재
- 하지만 USB networking gadget은 아직 별도 구성 필요

---

## 외부 문서로 확인한 해석

### FunctionFS

Linux kernel 문서에 따르면:

- FunctionFS는 mount 시 `ep0`만 제공
- userspace driver가 descriptors/strings를 `ep0`에 써야
  `ep#` endpoint 파일이 나타남
- 모든 파일이 닫히면 함수가 비활성화됨

현재 실측 `ep0 only` 상태는
**descriptor 등록이 끝나지 않았거나 adbd가 그 전에 종료됐음**을 시사한다.

참고:
- https://docs.kernel.org/usb/functionfs.html

### Android USB configfs 순서

AOSP init 스크립트는

1. `start adbd`
2. `sys.usb.ffs.ready=1` 대기
3. `ffs.adb` symlink 추가
4. `UDC` bind

순서로 ADB를 올린다.

현재 custom init에서도 같은 구조를 흉내 냈지만,
Android runtime/SELinux/property/init choreography 일부가 빠져 있어
`adbd`가 안정적으로 descriptor를 올리지 못하는 가능성이 높다.

참고:
- https://android.googlesource.com/platform/system/core/+/master/rootdir/init.usb.configfs.rc

### adbd privilege drop

AOSP `adbd_main()`은
`drop_privileges()` 이후 `usb_init()`을 호출한다.

즉 FunctionFS 접근은 root 유지보다
**적절한 group/capability/환경을 맞추는 문제**에 가깝다.

참고:
- https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/android12-gsi/daemon/main.cpp
- https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/daemon/usb.cpp

### backlight / input / DRM

Linux kernel 문서 기준:

- backlight는 `/sys/class/backlight/<name>/brightness`와 `max_brightness`로 제어
- input event 장치의 능력은
  `class/input/event*/device/capabilities/`와 `properties`에서 식별 가능
- DRM/KMS는 sysfs에 connector/CRTC/device를 노출

참고:
- https://docs.kernel.org/gpu/backlight.html
- https://docs.kernel.org/input/event-codes.html
- https://docs.kernel.org/gpu/drm-kms.html

---

## 지금 단계에서 더 필요한 정보

우선순위 기준으로는 아래가 가장 가치가 높다.

### 1. 입력 장치 식별

필요 정보:

- `event0` ~ `event8` 각각의 이름
- capabilities
- 볼륨키 / 전원키 / 터치 식별 여부

의도:
- 화면 없이도 버튼 기반 복구/메뉴/상태 전환 가능성 판단

### 2. 화면 제어 가능 범위

필요 정보:

- backlight write가 실제로 패널 밝기를 바꾸는지
- DRM 관련 `/dev/dri/*` 노드를 현재 shell에서 만들 수 있는지
- framebuffer/DRM debugfs/sysfs에서 최소 표시 경로가 보이는지

의도:
- “멈춘 것처럼 보이는 화면”에 최소 진행 표시를 넣을 수 있는지 판단

현재 blocker:

- `writefile`은 확보했으므로,
  다음 blocker는 실제 화면 변화 관찰과
  더 정교한 입력/DRM 상태 추적임

### 3. USB networking 가능성

필요 정보:

- `RNDIS/NCM` function 추가 시 host에 새 네트워크 인터페이스가 생기는지
- 장치 측에서 corresponding netdev가 생성되는지

의도:
- ADB보다 단순한 `USB networking + SSH` 경로로 전환할 수 있는지 판단

### 4. `prepareandroid` 정리

필요 정보:

- `/system` bind mount 중복 여부
- symlink/mount 중복 호출이 이후 실험에 영향을 주는지

의도:
- shell helper를 idempotent하게 만들기

---

## 현재 추천 방향

지금 상태에선 아래 우선순위가 가장 합리적이다.

1. Android dynamic binary / ADB 추적은 잠시 보류
2. 현재 shell에서 **input + backlight + DRM probe**를 우선 진행
3. 실용 채널은 `serial + TCP bridge`를 유지
4. 다음 통신층 후보는 `USB networking + SSH`

이유:

- 텍스트 제어 채널은 이미 충분히 확보됨
- 반면 Android userspace 재사용은 아직 비용이 큼
- 커널이 이미 노출한 하드웨어 클래스부터 읽는 편이
  다음 설계(화면/입력/네트워크)를 더 빠르게 좁혀 준다
