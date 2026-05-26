# V1053 Modem Pre-Holder Plain Open Fallback Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| source patch | `stage3/linux_init/helpers/a90_android_execns_probe.c` | `v1053-plain-open-fallback-source-pass` |
| build artifact | `tmp/wifi/v1053-execns-helper-v180-build/a90_android_execns_probe` | `v1053-helper-v180-build-pass` |

V1053 adds a bounded diagnostic fallback for the V1052 `EFAULT` result. Helper
`v180` records the first nonblocking open errno and then retries the same private
root `/dev/subsys_modem` path with a plain read-only open.

## Changes

- Helper marker bumped to `a90_android_execns_probe v180`.
- The modem pre-holder now records:
  - `modem_pre_holder_nonblock_opened`
  - `modem_pre_holder_nonblock_errno`
  - `modem_pre_holder_plain_retry`
  - `modem_pre_holder_first_errno`
- Plain fallback uses:
  - `open("/dev/subsys_modem", O_RDONLY | O_CLOEXEC)`
- The existing parent-side bounded wait and cleanup semantics remain unchanged.

## Build Artifact

```text
path:   tmp/wifi/v1053-execns-helper-v180-build/a90_android_execns_probe
sha256: f260583dc99cc65390ffb719ba0c2618cbbbc25a523f0b1e4fc0a07e93df9641
size:   1188336 bytes
arch:   ELF 64-bit LSB executable, ARM aarch64, statically linked
```

Contract strings verified:

```text
a90_android_execns_probe v180
--allow-pm-full-contract-with-modem-holder
after-mdm-helper-esoc-fd-with-pm-full-contract-with-modem-holder
cnss_before_esoc.modem_pre_holder_nonblock_errno=%d
cnss_before_esoc.modem_pre_holder_plain_retry=1
cnss_before_esoc.modem_pre_holder_first_errno=%d
```

## Validation

```bash
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v1053-execns-helper-v180-build/a90_android_execns_probe
sha256sum tmp/wifi/v1053-execns-helper-v180-build/a90_android_execns_probe
stat -c 'size=%s mode=%a' tmp/wifi/v1053-execns-helper-v180-build/a90_android_execns_probe
strings tmp/wifi/v1053-execns-helper-v180-build/a90_android_execns_probe | \
  rg 'a90_android_execns_probe v180|modem_pre_holder_nonblock_errno|modem_pre_holder_plain_retry|modem_pre_holder_first_errno|--allow-pm-full-contract-with-modem-holder|after-mdm-helper-esoc-fd-with-pm-full-contract-with-modem-holder'
```

## Guardrails

No device contact, helper deploy, daemon start, subsystem open, Wi-Fi HAL,
scan/connect, credentials, DHCP/routes, external ping, sysfs write, GPIO write,
partition write, boot image write, or firmware mutation occurred in V1053.

## Next

V1054 should deploy helper `v180` only. V1055 should rerun the bounded live gate
and classify the private-root plain open result before any Wi-Fi HAL or
scan/connect work.
