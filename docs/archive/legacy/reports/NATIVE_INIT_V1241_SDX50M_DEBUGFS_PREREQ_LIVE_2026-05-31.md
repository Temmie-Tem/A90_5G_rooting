# V1241 SDX50M Debugfs Prerequisite Observer

- report: `docs/reports/NATIVE_INIT_V1241_SDX50M_DEBUGFS_PREREQ_LIVE_2026-05-31.md`
- classifier: `scripts/revalidation/native_wifi_sdx50m_debugfs_prereq_live_v1241.py`
- evidence: `tmp/wifi/v1241-sdx50m-debugfs-prereq-live/manifest.json`
- summary: `tmp/wifi/v1241-sdx50m-debugfs-prereq-live/summary.md`

- decision: `v1241-pinctrl-observer-ready-no-line-level`
- pass: `True`
- reason: debugfs exposes pinctrl ownership for AP2MDM/MDM2AP, but no direct line-level GPIO values.
- next_step: V1242 can sample pinctrl, IRQ, and PCIe around a bounded `pm-service` esoc0 trigger; do not rely on GPIO line values.

## Checks

| check | status | detail |
| --- | --- | --- |
| explicit flags | pass | `--allow-live-readonly --allow-temp-debugfs --assume-yes` supplied |
| V1240 input | pass | `v1240-response-inputs-visible-mdm2ap-silent` |
| runtime health | pass | version, bootstatus, selftest, post-bootstatus, post-selftest, and stopped netservice all clean |
| debugfs mount | pass | debugfs was not mounted before; V1241 mounted it temporarily |
| debugfs cleanup | pass | debugfs was unmounted after collection |
| pinctrl observer | pass | GPIO135/AP2MDM and GPIO142/MDM2AP pinctrl ownership lines are visible |
| MDM status IRQ | pass | `/proc/interrupts` exposes GPIO142 `mdm status`, count total `0` |
| PCIe/regulator surface | finding | PCIe debug surface and regulator summaries are readable enough for sampling, but not a line-level GPIO source |

## Key Evidence

| field | value |
| --- | --- |
| `mounted_before` | `False` |
| `mounted_by_v1241` | `True` |
| `mounted_during` | `True` |
| `mounted_after` | `False` |
| `gpio_debug_readable` | `True` |
| `pinctrl_debug_present` | `True` |
| AP2MDM observer | `pin 135 (GPIO_135): soc:qcom,mdm3 3000000.pinctrl:135 function gpio group gpio135` |
| MDM2AP observer | `pin 142 (GPIO_142): soc:qcom,mdm3 3000000.pinctrl:142 function gpio group gpio142` |
| soft reset / PMIC surface | PM8150/PM8150L pinctrl surfaces visible, but no direct reset line-level value |
| MDM status IRQ | GPIO142 IRQ count total `0` |
| PCIe debug lines | `6` |
| regulator focus lines | `63` |

## Interpretation

V1241 proves a cleanup-safe debugfs observer path exists in native init. It can
be mounted temporarily, sampled, and unmounted cleanly. The useful observer is
pinctrl ownership/configuration plus `/proc/interrupts`, not direct GPIO
line-level values: debugfs shows GPIO135 and GPIO142 are owned by
`soc:qcom,mdm3`, but does not expose a high/low level for these lines.

This changes the next gate shape. V1242 should not depend on reading AP2MDM or
MDM2AP line levels. It should run a bounded `pm-service` esoc0 trigger with
high-rate sampling of:

- GPIO142 `mdm status` IRQ count before/during/after the trigger;
- pinctrl ownership/configuration snapshots for GPIO135/GPIO142;
- PCIe RC1 debug/sysfs state;
- dmesg markers for PCIe, MHI, SSCTL, WLFW, BDF, and `wlan0`;
- cleanup state, including whether reboot is still required.

## Safety

Live classifier with explicitly allowed temporary debugfs mount only. No raw
eSoC/subsys open, GPIO/sysfs/debugfs control write, daemon start, Wi-Fi HAL,
scan/connect, credentials, DHCP/routes, external ping, reboot, flash, boot
image write, or partition write occurred. Postflight remained clean:
`selftest: pass=11 warn=1 fail=0`, `netservice enabled=no`, `tcpctl=stopped`,
and `boot: BOOT OK`.
