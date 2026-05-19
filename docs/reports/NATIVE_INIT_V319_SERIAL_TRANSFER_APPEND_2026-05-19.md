# V319 Serial Transfer Append Report

## Summary

- Result: PASS.
- Native build: `A90 Linux init 0.9.61 (v319)`.
- Boot image: `stage3/boot_linux_v319.img`.
- Purpose: provide a bounded ACM serial transfer primitive for the V317 private property namespace proof after V318 showed `toybox sh` is unavailable.

## Artifacts

| artifact | sha256 |
| --- | --- |
| `stage3/linux_init/init_v319` | `d8cf63a6231d95a1c29e4a3587cc38e900ff46007f8f686f22c9fc814c60d7d1` |
| `stage3/ramdisk_v319.cpio` | `d264d2130f1480e4cc19f33b618fd4365e65238101b9fe13c38474d138ee7256` |
| `stage3/boot_linux_v319.img` | `98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8` |

## Static Validation

```text
aarch64-linux-gnu-gcc -static -Os -Wall -Wextra -o stage3/linux_init/init_v319 ...
file stage3/linux_init/init_v319
strings stage3/boot_linux_v319.img | rg 'A90 Linux init 0.9.61 \(v319\)|A90v319|appendfile|0.9.61 v319'
git diff --check
```

Result: PASS.

## Flash Validation

Command:

```text
python3 scripts/revalidation/native_init_flash.py stage3/boot_linux_v319.img --from-native --expect-version "A90 Linux init 0.9.61 (v319)" --verify-protocol auto
```

Result: PASS.

Observed:

```text
remote image sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
boot block prefix sha256: 98cc57153bcc4c235193e28fd52650485ffc1f19aa6464942e5216839d4597c8
cmdv1 verify passed: version/status rc=0 status=ok
```

## Live Smoke

Evidence: `tmp/wifi/v319-serial-transfer-append-smoke/`.

Decision: `serial-transfer-append-smoke-pass`.

Checks:

| check | result |
| --- | --- |
| version reports v319 | PASS |
| help lists `appendfile` | PASS |
| uuencoded payload append/decode SHA-256 | PASS |
| `/tmp/v319-deny` outside allowed workspaces rejected | PASS |
| 1500-byte `cmdv1x` append works and `stat` reports `size=1500` | PASS |

## V317 Runner Revalidation

The V317 runner now avoids `toybox sh` and uses:

```text
appendfile <tmp.uue> <uuencoded chunk>
run /cache/bin/toybox uudecode -o <tmp-file> <tmp.uue>
run /cache/bin/toybox sha256sum <tmp-file>
```

Revalidated manifests:

| evidence | decision | pass |
| --- | --- | --- |
| `tmp/wifi/v317-private-property-namespace-proof-plan/manifest.json` | `private-property-namespace-proof-plan-ready` | `true` |
| `tmp/wifi/v317-private-property-namespace-proof-refuse/manifest.json` | `private-property-namespace-proof-approval-required` | `false` |
| `tmp/wifi/v317-private-property-namespace-proof-cleanup-refuse/manifest.json` | `private-property-namespace-proof-approval-required` | `false` |
| `tmp/wifi/v317-private-property-namespace-proof-audit/manifest.json` | `private-property-namespace-proof-audit-pass` | `true` |
| `tmp/wifi/v317-private-property-namespace-proof-audit/selftest-manifest.json` | `private-property-namespace-proof-audit-selftest-pass` | `true` |

Updated transfer estimate:

```text
files=5 bytes=524988 chunk_size=1536 chunks=471 estimated_commands=505 max_script_chars=3294 status=pass
```

## Safety

- `appendfile` is scoped to A90 runtime/cache/temp workspaces and uses `O_NOFOLLOW`.
- The smoke test only created temporary files under `/mnt/sdext/a90/tmp` and removed them.
- V317 live proof is still blocked until the exact approval phrase is supplied.
- No daemon start, Wi-Fi bring-up, global property replacement, or property service socket was performed.

## Next Step

Run the V317 private namespace proof only with the existing exact approval phrase, then inspect the copied private workdir and cleanup result. That proof still does not start Android daemons or Wi-Fi.
