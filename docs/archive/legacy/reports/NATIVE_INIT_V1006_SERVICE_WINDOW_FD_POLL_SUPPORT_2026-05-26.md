# V1006 Service-window fd Poll Support Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| helper source/build | `tmp/wifi/v1006-execns-helper-v171-build/build.log` | `v1006-helper-v171-build-pass` |

V1006 adds helper `v171` source/build support for repeated `mdm_helper`
`/dev/esoc-0` fd polling inside the Android service-window subsystem trigger
mode. No deploy or live trigger was run in V1006.

## Implemented

- Bumped `a90_android_execns_probe` to `v171`.
- Added bounded fd polling markers under
  `android_wifi_service_window.fd_poll.*`.
- Added an immediate short poll after `mdm_helper` spawn.
- Added a longer poll after `cnss-daemon` spawn.
- Added aggregate markers:
  - `android_wifi_service_window.mdm_helper_esoc0_fd_poll_seen`;
  - `android_wifi_service_window.mdm_helper_esoc0_fd_poll_max_count`;
  - `android_wifi_service_window.mdm_helper_esoc0_fd_poll_last_count`;
  - `android_wifi_service_window.mdm_helper_esoc0_fd_poll_after_mdm_seen`;
  - `android_wifi_service_window.mdm_helper_esoc0_fd_poll_after_cnss_seen`.
- Reduced the trigger-capture mode's `mdm_helper` to `cnss-daemon` delay from
  the generic `300ms` path to a short `10ms` wait so the live mode can more
  closely match the Android V1000 `7.125ms` baseline.
- Kept the actual `/dev/subsys_esoc0` trigger fail-closed: the final immediate
  fd scan must still be positive before the trigger child can start.

## Validation

Executed:

```bash
mkdir -p tmp/wifi/v1006-execns-helper-v171-build
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v1006-execns-helper-v171-build/a90_android_execns_probe \
  2>&1 | tee tmp/wifi/v1006-execns-helper-v171-build/build.log

strings tmp/wifi/v1006-execns-helper-v171-build/a90_android_execns_probe | \
  rg 'a90_android_execns_probe v171|fd_poll|mdm_helper_esoc0_fd_poll|wifi-companion-android-wifi-service-window-subsys-trigger-capture'

git diff --check
```

Result:

```text
artifact: tmp/wifi/v1006-execns-helper-v171-build/a90_android_execns_probe
sha256: 347f38ab24d67bf300bd6dccd033a081328ec5afdd711b49f3d0d2f9328cf3a1
linkage: statically linked, no dynamic section
strings: v171 mode/fd-poll markers present
git diff --check: pass
```

## Guardrails

V1006 was source/build-only:

- no deploy;
- no device command;
- no Android boot or ADB command;
- no actor start;
- no `/dev/esoc-0` or `/dev/subsys_esoc0` open;
- no eSoC ioctl;
- no Wi-Fi scan/connect/link-up;
- no credential use;
- no DHCP/routes/external ping;
- no boot image, partition, firmware, GPIO, sysfs, or debugfs mutation.

## Next

Use V1007 for deploy-only helper `v171` parity. After deploy, use a separate
live gate to refresh current-boot SELinux state and rerun the service-window
subsystem trigger capture with fd-poll evidence. Do not combine deploy and live
trigger execution in one unit.
