# A90 Native Init V61 CPU/GPU Usage HUD Report

Date: `2026-04-26`

## Summary

`A90 Linux init v61`은 기존 HUD/status의 CPU/GPU 온도 표시에 사용률 `%`를 추가한 버전이다.
이번 단계에서는 화면 공간을 아끼기 위해 퍼센트만 넣고, GPU clock/frequency 표시는 후순위로 남겼다.

표시 목표:

```text
CPU 35.1C 0% GPU 33.5C 0%
```

## Artifacts

| artifact | SHA256 |
|---|---|
| `stage3/linux_init/init_v61` | `7fce8bac65af8cd997d7f150c0939b6e4fa757ea0ecfeb89e0213c3fa955f427` |
| `stage3/ramdisk_v61.cpio` | `2ce70282a001db47d42b900ccc0bfaf3aed7dee1528107048912bfbaab53d729` |
| `stage3/boot_linux_v61.img` | `40a33381be60ea8eaf91e7f09256d3d0de100c8959c3687a3b4aa95696c7cdb2` |

## Implementation

`stage3/linux_init/init_v61.c` 변경:

- `INIT_VERSION`을 `v61`로 갱신
- CPU usage:
  - `/proc/stat` 첫 `cpu` aggregate line을 읽음
  - 이전 샘플과 현재 샘플의 total/idle delta로 busy percent 계산
  - 첫 샘플은 delta가 없으므로 `?`로 표시
- GPU usage:
  - `/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage`를 읽음
  - 값은 `0 %` 형태로 제공되며 숫자 부분을 `%`로 정규화
- HUD/status:
  - `thermal: cpu=<temp> <usage> gpu=<temp> <usage>`
  - HUD row 2: `CPU <temp> <usage> GPU <temp> <usage>`

## Validation

Build:

```text
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra
```

Result:

- static ARM64 build — PASS
- marker strings in boot image — PASS

Flash:

```bash
python3 scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v61.img \
  --from-native \
  --expect-version "A90 Linux init v61" \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Result:

- local image SHA256: `40a33381be60ea8eaf91e7f09256d3d0de100c8959c3687a3b4aa95696c7cdb2`
- remote image SHA256: `40a33381be60ea8eaf91e7f09256d3d0de100c8959c3687a3b4aa95696c7cdb2`
- boot partition prefix SHA256: `40a33381be60ea8eaf91e7f09256d3d0de100c8959c3687a3b4aa95696c7cdb2`
- bridge `version`: `A90 Linux init v61`

Status output:

```text
thermal: cpu=35.1C 0% gpu=33.5C 0%
```

After `statushud` redraw:

```text
thermal: cpu=35.3C 12% gpu=33.6C 0%
```

Final state:

```text
autohud: running
netservice: disabled tcpctl=stopped
```

## Notes

- CPU usage is delta-based, so the first sample after boot can display `?`.
- GPU usage currently uses the direct KGSL `gpu_busy_percentage` sysfs value.
- GPU frequency was confirmed available through KGSL, but not added to HUD yet to preserve space.

## Next Work

1. User visual confirmation of row spacing on the physical screen
2. If space remains, consider compact GPU clock display such as `257M`
3. Continue physical USB unplug/replug validation and serial noise hardening
