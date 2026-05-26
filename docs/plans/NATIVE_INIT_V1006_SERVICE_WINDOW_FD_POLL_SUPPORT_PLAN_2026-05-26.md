# V1006 Service-window fd Poll Support Plan

## Goal

Add helper `v171` source/build support for repeated `mdm_helper`
`/dev/esoc-0` fd polling inside the Android service-window subsystem trigger
mode.

V1005 selected this because:

- Android V1000 shows `mdm_helper` start to `/dev/subsys_esoc0` get is about
  `170ms`;
- V1004 only performed a single post-spawn fd gate and missed `/dev/esoc-0`;
- V911 proves native `mdm_helper` can hold `/dev/esoc-0` in a reduced runtime
  contract path.

## Scope

1. Bump `a90_android_execns_probe` to `v171`.
2. In service-window subsystem-trigger mode only, add bounded fd polling:
   - immediate short poll after `mdm_helper` spawn;
   - longer poll after `cnss-daemon` spawn;
   - aggregate poll seen/max/last markers.
3. Reduce the service-window trigger mode's `mdm_helper` → `cnss-daemon` delay
   to better match the Android baseline.
4. Keep the final trigger gate fail-closed: the actual `/dev/subsys_esoc0`
   trigger still requires the immediate final fd scan to be positive.

## Guardrails

V1006 is source/build-only:

- no deploy;
- no live service-window run;
- no actor start;
- no `/dev/esoc-0` or `/dev/subsys_esoc0` open;
- no eSoC ioctl;
- no Wi-Fi scan/connect/link-up;
- no credential use;
- no DHCP/routes/external ping;
- no boot image or partition mutation.

## Validation

```bash
scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v1006-execns-helper-v171-build/a90_android_execns_probe
strings tmp/wifi/v1006-execns-helper-v171-build/a90_android_execns_probe | \
  rg 'a90_android_execns_probe v171|fd_poll|mdm_helper_esoc0_fd_poll'
git diff --check
```
