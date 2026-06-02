# Native Init V1668 pcie1 Clock Vote Source Build

## Summary

- Cycle: `V1668`
- Type: source/build-only rollbackable native pcie1 clock vote proof test boot artifact
- Decision: `v1668-pcie1-clock-vote-wait-repair-source-build-pass`
- Result: PASS
- Reason: built a V1661-style natural-path observer with extended async clock-debug vote readiness wait and separate result capture
- Manifest: `tmp/wifi/v1668-pcie1-clock-vote-wait-repair-test-boot/manifest.json`
- Boot image: `tmp/wifi/v1668-pcie1-clock-vote-wait-repair-test-boot/boot_linux_v1668_pcie1_clock_vote_wait.img`
- Boot SHA256: `6397756237e98046d4c0559d27a21da1dbeeb8ab5b341fef6ef740f855c0ebc8`
- Init: `A90 Linux init 0.9.118 (v1668-pcie1-clock-vote-wait)`
- Init SHA256: `df10eaa117407d474b513f4a88fef363ba034e387d0f32d8ebbf97cca1522c84`
- Helper marker: `a90_android_execns_probe v303`
- Helper SHA256: `d58f637ce53b12f16f7143b388b20007553fe8d47bd6ed06379bde96a69c8798`

## Gate Contract

- Natural provider route remains the existing `__subsystem_get(esoc0)` route; no forced RC1 enumerate is enabled.
- PID1 mounts debugfs, writes only targeted clock debugfs `rate`/`enable` leaves, holds them through the supervised helper window, then disables only clocks successfully enabled by the test boot.
- The build keeps full `regulator_summary`, targeted named-clock, subsystem, GPIO/IRQ, provider-thread, GPIO tracepoint, and PIL tracepoint observations.
- It records `pcie1_clock_vote.*` safety fields with regulator/GDSC/pci-case/PMIC/GPIO/eSoC/boot-done/scan/connect all set to zero.
- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping.

## Artifact Paths

- Log path: `/cache/native-init-wifi-test-boot-v1668.log`
- Summary path: `/cache/native-init-wifi-test-boot-v1668.summary`
- Helper result path: `/cache/native-init-wifi-test-boot-v1668-helper.result`
- Watcher result path: `/cache/native-init-wifi-test-boot-v1668-natural-watcher.result`
- Window result path: `/cache/native-init-wifi-test-boot-v1668-clock-vote-window.result`

## Next

Run one rollbackable V1669 live handoff, restore `stage3/boot_linux_v724.img`, verify native `selftest fail=0`, then classify the clock vote result.
