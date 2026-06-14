# Native Init V1400 Wi-Fi Test Boot Supervisor Source Build

## Summary

- Cycle: `V1400`
- Type: source/build-only Wi-Fi test boot supervisor update
- Decision: `v1400-wifi-test-boot-supervisor-source-build-pass`
- Result: PASS
- Artifact: `tmp/wifi/v1400-wifi-test-boot/boot_linux_v1400_wifi_test.img`
- Boot SHA256: `461d69cdf9d0680421dea9f77b3f444f028bb4c188a964bd6d7fd98142cdd27c`

V1400 responds to the V1399 finding that the PID1-launched helper was already a
zombie by the `35s` summary sample. The test boot now starts a non-blocking
supervisor child; that supervisor spawns the helper, waits with a bounded
`40s` timeout, and records helper wait result, raw status, exit code or signal,
timeout state, log size, and `wlan0` presence.

## Implementation

- Adds compile-time supervised-helper mode to the Wi-Fi test boot hook.
- Keeps PID1 non-blocking: PID1 forks a supervisor and returns to boot flow.
- Supervisor owns the helper process and can therefore wait for its exit status.
- Summary output appends `supervised=1`, `helper_wait_rc`, `helper_timed_out`,
  `helper_status_raw`, `helper_exit_code` or `helper_signal` fields.
- V1400 uses distinct `/cache` paths to avoid V1397/V1399 evidence reuse.

## Artifact

| Item | Path | SHA256 |
|---|---|---|
| PID1 | `tmp/wifi/v1400-wifi-test-boot/init_v1400_wifi_test` | `04d326e1927fec5c1794dade65b6c195e253632fd3b35010d74e991213a79af7` |
| helper | `tmp/wifi/v1400-wifi-test-boot/a90_android_execns_probe_v286` | `e5fc81a5becb2c6e6efd2ca026800560ed9e0e72a692f0fbb07861cf26d5380f` |
| ramdisk | `tmp/wifi/v1400-wifi-test-boot/ramdisk_v1400_wifi_test.cpio` | `8f4f45d90d944ca4d054f40ee2695de36430772f4153aedc123cd3de77d25586` |
| boot image | `tmp/wifi/v1400-wifi-test-boot/boot_linux_v1400_wifi_test.img` | `461d69cdf9d0680421dea9f77b3f444f028bb4c188a964bd6d7fd98142cdd27c` |

## V1400 Runtime Paths

- Log: `/cache/native-init-wifi-test-boot-v1400.log`
- Summary: `/cache/native-init-wifi-test-boot-v1400.summary`
- Helper PID file: `/cache/native-init-wifi-test-boot-v1400.pid`
- Supervisor PID file: `/cache/native-init-wifi-test-boot-v1400-supervisor.pid`
- Supervisor timeout: `40s`

## Validation

- `python3 -m py_compile` passed for the modified builder path.
- V1400 builder produced static aarch64 PID1/helper binaries.
- Boot image marker verification passed for `A90 Linux init 0.9.71 (v1400-wifitest)`,
  `a90_android_execns_probe v286`, `A90v1400`, and the V1400 `/cache` paths.
- Builder verified forbidden credential-like byte patterns were absent from the
  PID1, helper, ramdisk, and boot image artifacts.
- No device command, flash, reboot, partition write, Wi-Fi scan/connect,
  credentials, DHCP/routes, or external ping occurred in V1400.

## Next

V1401 should run local artifact sanity for the exact V1400 manifest and boot
image. The first later live handoff should flash only `tmp/wifi/v1400-wifi-test-boot/boot_linux_v1400_wifi_test.img`, expect
`A90 Linux init 0.9.71 (v1400-wifitest)`, collect `/cache/native-init-wifi-test-boot-v1400.log` and
`/cache/native-init-wifi-test-boot-v1400.summary`, then roll back to `stage3/boot_linux_v724.img`.
