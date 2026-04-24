# Native Init Static Userland Candidates (2026-04-25)

이 문서는 `A90 Linux init v47` 이후 작은 Linux userland를 붙이기 위한
후보를 정리한다. 목표는 모든 명령을 native init 안에 계속 재구현하지 않고,
검증 가능한 static ARM64 도구 묶음을 확보하는 것이다.

## 결론

- 1차 후보는 `/cache/bin`에 올리는 static ARM64 multi-call binary다.
- 현재 1차 산출물은 `toybox 0.8.13` static ARM64 빌드다.
- 실기 검증 결과 `/cache/bin/toybox` 배치와 주요 applet 실행이 확인됐다.
- 가장 현실적인 순서는 `toybox` 단일 바이너리 실행 검증 후,
  필요한 applet만 `run /cache/bin/<tool> <applet> ...` 형태로 사용하는 것이다.
- boot ramdisk에 바로 포함하지 말고, 먼저 `/cache/bin`에서 실험한다.
- symlink farm 설치는 나중으로 미룬다. 현재 native shell의 `run`은 경로 실행이
  명확하므로 `busybox ls /proc`처럼 명시 호출하는 편이 안전하다.
- USB networking probe 전에 `ip`/`ifconfig`/`route`/`nc`/`ps`/`dmesg`/`grep`/`tail`
  계열 도구 확보 여부를 먼저 확인한다.

## 현재 기준점

- 최신 init: `A90 Linux init v47`
- 실행 경로: `run <path> [args...]`
- 현재 `run` 환경:
  - `PATH=/cache:/cache/bin:/bin:/system/bin`
  - `HOME=/`
  - `TERM=vt100`
- persistent safe write 영역: `/cache`
- bridge 상태: 보고서 작성 시점에는 host `127.0.0.1:54321`이 닫혀 있음
- host USB 상태: `/dev/ttyACM0`는 보이나 현재 사용자는 `dialout` 권한이 없음

## 로컬 빌드 환경

초기 관찰:

- `aarch64-linux-gnu-gcc`: 있음
- `aarch64-linux-gnu-strip`: 있음
- `aarch64-linux-gnu-readelf`: 있음
- `make`: 없음
- host `gcc`: 없음
- `musl-gcc`: 없음
- 간단한 AArch64 static hello binary 빌드는 성공함

빌드 준비 후 관찰:

```bash
sudo apt install -y \
  build-essential \
  make gcc \
  gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu libc6-dev-arm64-cross \
  libncurses-dev bison flex bc pkg-config \
  git curl wget tar bzip2 xz-utils patch file ca-certificates
```

결과:

- `make`: 있음
- host `gcc`: 있음
- `aarch64-linux-gnu-gcc`: 있음
- `aarch64-linux-gnu-strip`: 있음
- `aarch64-linux-gnu-readelf`: 있음
- `musl-gcc`: 없음
- `build-essential`, `libncurses-dev`, `bison`, `flex`, `bc`, `pkg-config`: 설치됨

의미:

- 단일 C helper는 지금도 `aarch64-linux-gnu-gcc -static`으로 만들 수 있다.
- `toybox` 전체 빌드가 가능해졌다.
- prebuilt binary 대신 공식 source tarball을 해시 고정 후 로컬 빌드하는 경로가 생겼다.

## Toybox 빌드 결과

재현 스크립트:

```bash
./scripts/revalidation/build_static_toybox.sh
```

입력:

- source: `https://landley.net/toybox/downloads/toybox-0.8.13.tar.gz`
- source SHA256: `9d4c124d7d731a2db399f6278baa2b42c2e3511f610c6ad30cc3f1a52581334b`
- build path: `external_tools/userland/`
- build log: `external_tools/userland/build/toybox-0.8.13-aarch64-static.log`

산출:

- artifact: `external_tools/userland/bin/toybox-aarch64-static-0.8.13`
- size: 약 `1.5 MiB`
- SHA256: `92a0917579c76fec965578ac242afbf7dedc4428297fb90f4c9caf7f538a718c`
- ELF: `ARM aarch64`, `statically linked`, `stripped`
- static check: `INTERP` segment 없음, dynamic section 없음

config 조정:

- enabled:
  - `CONFIG_IP`
  - `CONFIG_ROUTE`
  - `CONFIG_HEXDUMP`
  - 기본 `defconfig`의 `IFCONFIG`, `NETCAT`, `PS`, `DMESG`, `GREP`, `TAIL`, `MOUNT`, `UMOUNT`, `CP`, `CHMOD`, `FIND`, `TAR`, `READLINK`, `WHICH`
- disabled:
  - `CONFIG_LOGIN`
  - `CONFIG_MKPASSWD`
  - `CONFIG_PASSWD`
  - `CONFIG_SU`
  - `CONFIG_SULOGIN`
  - `CONFIG_GETTY`

주의:

- `IP`, `ROUTE`, `HEXDUMP`는 toybox의 pending 영역을 사용하므로 실기 검증이 필요하다.
- glibc static link 특성상 `getaddrinfo`, `getpwnam`, `getgrnam` 계열 경고가 발생한다.
  단순 파일/프로세스/네트워크 인터페이스 확인에는 바로 쓸 수 있을 가능성이 높지만,
  DNS/사용자 DB 관련 applet은 실제 native init 환경에서 별도 확인해야 한다.

## Device-side 검증 결과

검증 경로:

1. native init v47 bridge 확인
2. `recovery` 명령으로 TWRP 진입
3. TWRP ADB로 `/cache/bin/toybox` 배치
4. SHA256 확인
5. TWRP에서 system reboot
6. native init v47에서 `run /cache/bin/toybox ...` 실행

배치 결과:

```text
/cache/bin/toybox
mode=0755 uid=0 gid=0 size=1567176
sha256=92a0917579c76fec965578ac242afbf7dedc4428297fb90f4c9caf7f538a718c
```

PASS:

| Command | Result |
|---|---|
| `stat /cache/bin/toybox` | `mode=0755`, size match |
| `run /cache/bin/toybox --help` | PASS |
| `run /cache/bin/toybox uname -a` | PASS |
| `run /cache/bin/toybox ls /proc` | PASS |
| `run /cache/bin/toybox ps -A` | PASS |
| `run /cache/bin/toybox ps -ef` | PASS |
| `run /cache/bin/toybox dmesg --help` | PASS |
| `run /cache/bin/toybox dmesg -s 1024` | PASS |
| `run /cache/bin/toybox hexdump -C /proc/version` | PASS |
| `run /cache/bin/toybox ifconfig -a` | PASS |
| `run /cache/bin/toybox route -n` | PASS |
| `run /cache/bin/toybox ip` | PASS, usage 출력 |
| `run /cache/bin/toybox netcat --help` | PASS |

주의/부분 동작:

- `run /cache/bin/toybox ps`는 header만 출력하고 `rc=1`을 반환했다.
  - 대체: `ps -A`, `ps -ef`는 정상 동작.
- `run /cache/bin/toybox netcat -h`는 `Unknown option 'h'`로 `rc=1`을 반환했다.
  - 대체: `netcat --help`는 정상 동작.
- `run /cache/bin/toybox ip addr`와 `ip link`는 interface 일부를 출력하지만
  `No such device` 메시지와 함께 `rc=1`을 반환했다.
  - `lo`, `bond0`, `dummy0` 출력은 확인됨.
  - USB network function 추가 후 다시 확인해야 한다.
- `ifconfig -a` 기준 현재 native init network interface는 `lo`, `bond0`, `dummy0` 중심이다.
- `route -n` 기준 현재 routing table은 비어 있다.

판정:

- V49 host-side build와 device-side execution baseline은 통과했다.
- 다음 작업은 toybox를 활용한 USB networking function probe다.

## 후보 1: BusyBox

장점:

- embedded Linux에서 검증된 multi-call utility 묶음이다.
- `sh`, `ls`, `cp`, `mount`, `ps`, `dmesg`, `grep`, `tail`, `hexdump`, `nc`,
  `ifconfig`, `route`, `ip` 등 필요한 applet을 한 바이너리로 가져올 수 있다.
- 공식 FAQ 기준 cross compile은 `CROSS_COMPILE=<prefix>` 방식으로 지원된다.

주의:

- BusyBox는 GPLv2다. 배포/공유 가능한 boot image에 포함하면 해당 BusyBox
  버전의 complete corresponding source 제공 의무를 함께 관리해야 한다.
- 공식 prebuilt binaries 디렉터리는 오래된 빌드 위주이며, 현 시점에 AArch64
  최신 prebuilt를 기준점으로 삼기 어렵다.
- glibc static build는 크기가 커질 수 있다. 장기적으로는 musl/uClibc 기반 빌드가
  더 적합할 수 있다.

현재 공식 관찰:

- 공식 downloads 기준 stable tarball은 `busybox-1.37.0.tar.bz2`
  (2024-09-26)이고 snapshot tarball도 존재한다.
- 공식 binary 디렉터리는 최신 AArch64 빌드를 제공하는 구조로 보이지 않는다.

권장 사용 방식:

```text
/cache/bin/busybox --help
/cache/bin/busybox uname -a
/cache/bin/busybox ls /proc
/cache/bin/busybox dmesg
/cache/bin/busybox ps
/cache/bin/busybox nc -h
```

## 후보 2: toybox

장점:

- Android 계열과 철학적으로 잘 맞는 command-line utility 묶음이다.
- upstream 문서상 Android/self-hosting을 중요한 목표로 둔다.
- BSD 계열 라이선스라 BusyBox보다 배포 관리 부담이 작을 가능성이 높다.
- static linking 방향과도 잘 맞는다.

주의:

- BusyBox보다 applet coverage가 다를 수 있으므로 USB networking에 필요한
  `ip`/`ifconfig`/`route`/`nc`/`telnet` 계열을 실제 config 기준으로 확인해야 한다.
- Android에 이미 있는 `/system/bin/toybox`는 동적 Android userspace 의존성이
  있을 수 있어 native init의 독립 userland 기준으로는 별도 static 빌드가 더 낫다.

현재 공식 관찰:

- toybox roadmap 기준 current release는 `0.8.13` (2025-10-14)로 표시된다.
- toybox FAQ는 static linking이 binary를 더 크게 만들지만 더 portable하게 만든다고 설명한다.

권장 사용 방식:

```text
/cache/bin/toybox --help
/cache/bin/toybox uname -a
/cache/bin/toybox ls /proc
/cache/bin/toybox ps
/cache/bin/toybox dmesg
```

## 후보 3: Buildroot 기반 rootfs

장점:

- BusyBox, libc, dropbear, networking tool 등을 한 번에 재현 가능한 rootfs로
  만들 수 있다.
- 장기적으로 “서버형 Linux 환경”에 가장 가까운 방향이다.

주의:

- 지금 단계에서는 과하다.
- native init의 console/log/display/recovery 안전성이 더 쌓인 뒤,
  별도 rootfs 후보를 `/cache` 또는 `userdata`에 올리는 단계에서 검토하는 편이 맞다.

## 추천 실험 순서

1. host build prerequisite 확인
   - `make`
   - host `gcc` 또는 `clang`
   - `aarch64-linux-gnu-gcc`
   - `aarch64-linux-gnu-strip`
2. `scripts/revalidation/build_static_toybox.sh`로 static ARM64 toybox를 빌드한다.
3. `external_tools/userland/bin/toybox-aarch64-static-0.8.13`를 `/cache/bin/toybox`에 복사한다.
4. native init에서 다음 순서로 검증한다.
   - `run /cache/bin/toybox --help`
   - `run /cache/bin/toybox uname -a`
   - `run /cache/bin/toybox ls /proc`
   - `run /cache/bin/toybox ps`
   - `run /cache/bin/toybox dmesg`
   - `run /cache/bin/toybox ifconfig -a`
   - `run /cache/bin/toybox route -n`
   - `run /cache/bin/toybox ip`
   - `run /cache/bin/toybox netcat -h`
5. applet별 성공/실패를 `/cache/native-init.log`와 repo report에 기록한다.
6. 그 다음 USB networking function probe로 넘어간다.

## Native Init 쪽 보강 후보

도구를 붙이기 전 native init에 바로 넣으면 좋은 작은 개선:

- `run`이 상대 경로 실행을 하지는 않으므로 사용자는 항상 절대 경로를 쓴다.
- `which <name>` 또는 `path <name>` 같은 단순 PATH 확인 명령을 추가하면 편하다.
- `chmod <mode> <path>`가 있으면 `/cache/bin`에 올린 파일 실기 테스트가 쉬워진다.
- `cp`가 없으므로 파일 배치는 당분간 TWRP/host/bridge 도구에 의존한다.
- shell parser는 아직 quote/escape를 지원하지 않으므로 복잡한 명령은 피한다.

## 판정

V49의 목표는 “정식 rootfs를 만들기”가 아니다.

V49의 완료 기준은 충족했다.

- static ARM64 toybox를 `/cache/bin/toybox`로 배치 완료
- native init에서 3개 이상 applet 실행 PASS
- networking 관련 applet 중 `ifconfig`, `route`, `ip`, `netcat` 동작 여부 기록 완료

현재 판단은 다음과 같다.

- 단기: `/cache/bin` 기반 explicit multi-call 실행
- 중기: toybox 실기 검증 후 부족하면 BusyBox를 추가 비교
- 장기: Buildroot rootfs + dropbear/SSH 후보 검토

## 참고 자료

- BusyBox downloads: https://busybox.net/downloads/
- BusyBox FAQ: https://busybox.net/FAQ.html
- BusyBox license: https://busybox.net/license.html
- Toybox overview: https://landley.net/code/toybox/
- Toybox FAQ: https://landley.net/toybox/faq.html
- Toybox roadmap: https://landley.net/toybox/roadmap.html
- Buildroot manual: https://buildroot.org/downloads/manual/manual.html
