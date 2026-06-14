# Native Init V59 AT Serial Noise Filter

Date: `2026-04-26`

## Summary

Host 쪽 NetworkManager/modem probe가 USB ACM serial에 `AT` 계열 문자열을 보내면
native init shell이 이를 명령으로 오인해 `unknown command`를 출력할 수 있었다.

v59에서는 이 문제를 host bridge가 아니라 native init shell 입력 경로에서 처리한다.
즉 bridge 없이 직접 serial로 접근해도 unsolicited modem probe line은 조용히 무시된다.

## Implementation

Source:

```text
stage3/linux_init/init_v59.c
```

Changes:

- `INIT_VERSION`을 `v59`로 갱신
- `is_unsolicited_at_noise()` 추가
- `read_line()` 이후, `split_args()`/`find_command()` 이전에 AT noise 여부 확인
- 다음 형태를 shell command dispatch 전에 무시:
  - `AT`
  - `ATE0`
  - `AT+...`
  - `ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0`
- 무시한 line은 `/cache/native-init.log`에 기록:

```text
serial: ignored AT probe line=...
```

## Artifacts

```text
7c87459e49e77abf969256b0726cc6329470dc56ea0b7d73acfff4f4ab16d735  stage3/linux_init/init_v59
aa9ab262e77fd5f7d9795e2139f8c07794848314d81e38ef93a113d26c20b217  stage3/ramdisk_v59.cpio
9c4eb1b4b8024a481e71a5bb584c48fe11f1d454983a6e541e49213818120e07  stage3/boot_linux_v59.img
```

Generated artifacts are intentionally ignored by git; `init_v59.c` and this report are the tracked source of truth.

## Flash Validation

Command:

```bash
python3 ./scripts/revalidation/native_init_flash.py \
  stage3/boot_linux_v59.img \
  --expect-version "A90 Linux init v59" \
  --from-native \
  --bridge-timeout 240 \
  --recovery-timeout 180
```

Result:

```text
local image sha256: 9c4eb1b4b8024a481e71a5bb584c48fe11f1d454983a6e541e49213818120e07
remote image sha256: 9c4eb1b4b8024a481e71a5bb584c48fe11f1d454983a6e541e49213818120e07
boot block prefix sha256: 9c4eb1b4b8024a481e71a5bb584c48fe11f1d454983a6e541e49213818120e07
A90 Linux init v59
```

## Live Serial Validation

Host injection:

```bash
{
  printf '\n'
  printf 'AT\r'
  printf 'ATE0\r'
  printf 'AT+GCAP\r'
  printf 'ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0\r'
  printf 'version\n'
} | nc -w 8 127.0.0.1 54321
```

Observed output:

```text
a90:/# AT
a90:/# ATE0
a90:/# AT+GCAP
a90:/# ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0
a90:/# version
A90 Linux init v59
[done] version (0ms)
```

Important negative check:

```text
unknown command: AT
```

was not present.

Log validation:

```text
serial: ignored AT probe line=AT
serial: ignored AT probe line=ATE0
serial: ignored AT probe line=AT+GCAP
serial: ignored AT probe line=ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0
```

## Current Conclusion

- ACM serial can now tolerate common host modem probe noise.
- The filter is intentionally narrow: uppercase `AT` modem-style lines only.
- Normal lowercase shell commands remain unaffected.
- Next work should move to boot-time NCM/tcpctl service policy or USB reconnect soak.
