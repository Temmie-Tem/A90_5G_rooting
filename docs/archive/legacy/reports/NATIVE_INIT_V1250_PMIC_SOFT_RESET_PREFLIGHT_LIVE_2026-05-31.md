# V1250 PMIC Soft-reset Preflight Live

- report: `docs/reports/NATIVE_INIT_V1250_PMIC_SOFT_RESET_PREFLIGHT_LIVE_2026-05-31.md`
- live runner: `scripts/revalidation/native_wifi_pmic_soft_reset_preflight_live_v1250.py`
- helper: `/cache/bin/a90_android_execns_probe` (`a90_android_execns_probe v260`)
- evidence: `tmp/wifi/v1250-pmic-soft-reset-preflight-live/manifest.json`
- result: `v1250-pmic-soft-reset-readonly-classified-no-candidate`
- pass: `true`

## Scope

V1250 executed only the read-only PMIC soft-reset preflight. It did not perform a
PMIC/GPIO/debugfs/regulator write, eSoC ioctl, PM actor start, CNSS daemon start,
Wi-Fi HAL start, scan/connect, credential use, DHCP/routes, external ping,
reboot, flash, boot image write, or partition write.

## Findings

| Field | Value |
| --- | --- |
| Helper SHA/marker/mode | pass |
| Live helper result | `read-only-incomplete` |
| `debugfs_pinctrl_present` | `0` |
| `debugfs_regulator_present` | `0` |
| GPIO class nodes | `gpio9=0`, `gpio135=0`, `gpio142=0` |
| PMIC soft-reset line | absent because pinctrl debugfs is not mounted |
| PCIe GDSC lines | absent because regulator debugfs is not mounted |
| `mdm3_state` | `OFFLINING` |
| GPIO142 IRQ count | `0` |
| `read_contract_ready` | `0` |
| `native_reproduction_candidate` | `0` |
| postflight selftest | `fail=0` |

## Interpretation

V1250 did not disprove the V1243/V1246 PMIC/GDSC blocker. It only shows that the
new helper's global read-only preflight cannot see the required pinctrl/regulator
surfaces when debugfs is not mounted. The next gate should reproduce the V1241
pattern: temporarily mount debugfs for read-only observation, run the same PMIC
preflight, and clean up. That remains an observation gate; no PMIC write or eSoC
ioctl should be added yet.

## Safety

All zero-action markers passed: `mutation_attempted=0`,
`write_gate_implemented=0`, `write_blocked=1`, `esoc_ioctl_executed=0`,
`pm_actor_executed=0`, `cnss_daemon_start_executed=0`,
`wifi_hal_start_executed=0`, `scan_connect_linkup=0`, `credentials=0`,
`dhcp_routing=0`, and `external_ping=0`.

## Next

V1251 should be a bounded debugfs read-surface preflight: mount debugfs only if
absent, run helper v260 read-only PMIC preflight, unmount/cleanup, and verify
postflight selftest. No write gate yet.
