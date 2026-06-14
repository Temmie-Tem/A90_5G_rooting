# Native Init v62 CPU Stress / Dev Node Guard Report

Date: `2026-04-26`

## Summary

`A90 Linux init v62`는 v61에서 추가한 CPU/GPU usage `%` 표시를 실제 CPU 부하로 검증하고,
부팅 초기에 필수 `/dev` 노드를 안전하게 보정한다.

- CPU usage gauge: `cpustress 10 8` 실행 후 CPU usage가 `0%`에서 `29%`로 상승 확인
- GPU busy: CPU-only 부하에서는 `0%` 유지가 정상
- `/dev/null`: char device `1:3` 확인
- `/dev/zero`: char device `1:5` 확인
- 최신 verified boot image: `stage3/boot_linux_v62.img`

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v62` | `016f67ec1bd713533ed8d2d12e5e5f7cd5709406ce6351fa0d22f30d0bcdfa33` |
| `stage3/ramdisk_v62.cpio` | `13ced5f0e0d97887fe84036b777cd5efdc97b0c81089261b9397f5da12169629` |
| `stage3/boot_linux_v62.img` | `8c422903226980855e23b75379a60b4ec3ec0a680c457b28adfa5417fdf870b1` |

## Source Changes

- `stage3/linux_init/init_v62.c`
  - `INIT_VERSION "v62"`
  - `ensure_char_node_exact()` 추가
  - `setup_base_mounts()`에서 `/dev/null`과 `/dev/zero` 보정
  - `cpustress [sec] [workers]` 명령 추가
  - `cpustress`는 worker fork, timeout, q/Ctrl-C cancellation을 지원

## Flash Validation

실행:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v62.img \
  --from-native \
  --expect-version "A90 Linux init v62" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

결과:

- local SHA256 확인 — PASS
- remote `/tmp/native_init_boot.img` SHA256 확인 — PASS
- boot partition prefix SHA256 readback — PASS
- bridge `version` — `A90 Linux init v62`

## Runtime Validation

Bridge 확인:

```text
version
A90 Linux init v62
kernel: Linux 4.14.190-25818860-abA908NKSU5EWA3 aarch64
display: 1080x2400 connector=28 crtc=133 fb=207
```

`/dev` node 확인:

```text
stat /dev/null
mode=0600 uid=0 gid=0 size=0
rdev=1:3

stat /dev/zero
mode=0600 uid=0 gid=0 size=0
rdev=1:5
```

CPU stress 전:

```text
thermal: cpu=34.9C 0% gpu=33.3C 0%
memory: 250/5375MB used
```

CPU stress:

```text
cpustress 10 8
cpustress: workers=8 sec=10, q/Ctrl-C cancels
cpustress: done workers=8 sec=10
```

CPU stress 후:

```text
thermal: cpu=36.3C 29% gpu=34.6C 0%
memory: 252/5375MB used
```

Cooldown 후:

```text
thermal: cpu=35.4C 0% gpu=33.7C 0%
memory: 252/5375MB used
```

## Notes

- GPU usage가 `0%`인 것은 현재 테스트가 CPU-only workload라서 정상이다.
- KMS HUD/menu는 DRM dumb buffer 경로를 사용하므로 KGSL/3D GPU busy를 올리지 않는다.
- 이전 런타임에서 `/dev/null`이 regular file로 만들어지면 큰 파일로 메모리를 소모할 수 있었다.
  v62는 부팅 시점에 해당 경로가 올바른 char device가 아니면 삭제 후 재생성한다.

## Next

1. 실제 케이블 unplug/replug 이후 ACM/NCM/tcpctl 복구 확인
2. USB 재열거 중 `A`/`ATAT...` serial noise hardening
3. Wi-Fi 드라이버/펌웨어 read-only 인벤토리
