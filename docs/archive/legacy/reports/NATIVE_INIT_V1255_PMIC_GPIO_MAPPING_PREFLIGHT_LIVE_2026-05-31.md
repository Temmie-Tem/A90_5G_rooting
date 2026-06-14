# V1255 PMIC GPIO Mapping Preflight Live

- report: `docs/reports/NATIVE_INIT_V1255_PMIC_GPIO_MAPPING_PREFLIGHT_LIVE_2026-05-31.md`
- runner: `scripts/revalidation/native_wifi_pmic_power_mapping_preflight_live_v1255.py`
- helper: `/cache/bin/a90_android_execns_probe` (`a90_android_execns_probe v261`)
- evidence: `tmp/wifi/v1255-pmic-power-mapping-preflight-live/manifest.json`
- result: `v1255-pmic-gpio-mapping-incomplete`
- pass: `true`

## Scope

V1255 temporarily mounted debugfs only because it was absent before the run,
executed the deployed v261 PMIC GPIO mapping preflight, then unmounted debugfs
and verified postflight selftest. It did not request a GPIO line, write
PMIC/GPIO/debugfs or regulator state, open `/dev/subsys_esoc0`, start PM/CNSS/HAL
actors, scan/connect, use credentials, DHCP/routes, external ping, reboot,
flash, boot image write, or partition write.

## Findings

| Field | Value |
| --- | --- |
| `mounted_before` | `false` |
| `mounted_by_v1255` | `true` |
| `mounted_during` | `true` |
| `mounted_after` | `false` |
| `cleanup_ok` | `true` |
| `read_contract_ready` | `true` |
| `native_reproduction_candidate` | `true` |
| PMIC soft-reset line | `pin 7 (gpio9): (MUX UNCLAIMED) c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:1270` |
| GPIO debugfs range | `gpiochip2: GPIOs 1263-1273, parent: platform/c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000, c440000.qcom,spmi:qcom,pm8150l@4:pinctrl@c000:` |
| derived global base/end | `1263-1273` |
| derived expected offset | `7` |
| `gpiochip_identity_match` | `true` |
| `gpiochip_offset_match` | `true` |
| `/dev/gpiochip*` scan count | `0` |
| `gpiochip_candidate_seen` | `false` |
| `gpiochip_mapping_ready` | `false` |
| `mapping_preflight_ready` | `false` |
| `mdm3_state` | `OFFLINING` |
| GPIO142 IRQ count | `0` |
| postflight selftest | `fail=0` |

## Interpretation

V1255 proves the PMIC GPIO identity and offset from debugfs: PM8150L GPIO9 maps
to global line `1270`, range `1263-1273`, offset `7`. The missing piece is not
the mapping; it is the absence of `/dev/gpiochip*` character-device nodes in the
native runtime. The helper therefore correctly stayed fail-closed with
`native-candidate-mapping-incomplete`.

The next gate should not request the GPIO line yet. V1256 should be a read-only
device-node feasibility classifier: inspect `/sys/class/gpio` and related sysfs
for gpiochip device numbers, confirm whether a safe temporary `/dev/gpiochip2`
node could be created from kernel-provided `dev` metadata, and define cleanup
rules. Only after that can a later source/build gate add a bounded line-hold
proof.

## Safety

All zero-action markers passed: `mutation_attempted=0`,
`write_gate_implemented=0`, `gpio_line_request_executed=0`,
`esoc_ioctl_executed=0`, `pm_actor_executed=0`,
`cnss_daemon_start_executed=0`, `wifi_hal_start_executed=0`,
`scan_connect_linkup=0`, `credentials=0`, `dhcp_routing=0`, and
`external_ping=0`.

## Next

V1256 should classify gpiochip device-node feasibility read-only. It should not
create a device node, request a line, hold PMIC GPIO9, open `/dev/subsys_esoc0`,
or start PM/CNSS/HAL actors.
