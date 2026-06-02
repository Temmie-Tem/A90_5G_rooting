# Native Init V1655 XBL Context Interpretation

## Summary

- Cycle: `V1655`
- Type: host-only redacted XBL context interpretation
- Decision: `v1655-xbl-context-interpretation-pass`
- Result: PASS
- Input: `tmp/wifi/v1654-xbl-context-probe-live/manifest.json`
- Source decision: `v1654-xbl-context-probe-live-pass`
- Total redacted records: `326`
- Duplicate groups: `96`
- Cross-slot duplicate groups: `96`
- Device commands: `0`
- Raw string output: `0`

## Checks

- `input_exists`: `True`
- `input_v1654_pass`: `True`
- `records_present`: `True`
- `record_fields_allowlisted`: `True`
- `host_only_no_device_command`: `True`
- `no_raw_string_output`: `True`
- `no_partition_write_command`: `True`
- `no_lower_layer_mutation`: `True`

## Artifact Summary

| artifact | records | high-signal records | classes | tokens | ranges |
|---|---:|---:|---|---|---|
| `xbl_a` | 175 | 175 | generic-power-token-context=87, no-token-context=84, pcie-context=1, sdx-mdm-context=3 | aop=44, pcie=1, pmic=26, pon=11, ps_hold=1, rpmh=83, sdx=3, vdd=9 | 20034:29600=29, 3340797:3377867=146 |
| `xbl_b` | 151 | 151 | generic-power-token-context=90, no-token-context=57, pcie-context=1, sdx-mdm-context=3 | aop=54, gpio=7, pcie=1, pmic=22, pon=13, ps_hold=1, rpmh=49, sdx=3, vdd=6 | 20027:30662=29, 3355345:3400091=122 |

## Class Clusters

| artifact | class | count | offset min | offset max | tokens |
|---|---|---:|---:|---:|---|
| `xbl_a` | `generic-power-token-context` | 87 | 20034 | 3377808 | aop=44, pmic=26, pon=11, vdd=9 |
| `xbl_a` | `no-token-context` | 84 | 21667 | 3369735 | ps_hold=1, rpmh=83 |
| `xbl_a` | `sdx-mdm-context` | 3 | 23261 | 23338 | sdx=3 |
| `xbl_a` | `pcie-context` | 1 | 3357265 | 3357265 | pcie=1 |
| `xbl_b` | `generic-power-token-context` | 90 | 20027 | 3400051 | aop=54, pmic=22, pon=13, vdd=6 |
| `xbl_b` | `no-token-context` | 57 | 21819 | 3398672 | gpio=7, ps_hold=1, rpmh=49 |
| `xbl_b` | `sdx-mdm-context` | 3 | 23237 | 23314 | sdx=3 |
| `xbl_b` | `pcie-context` | 1 | 3385761 | 3385761 | pcie=1 |

## Cross-Slot Duplicate Digest Groups

Only digest, token, class, and location metadata are shown. The digest is a SHA256 of private string text captured by V1654.

- digest=`0148dff0fb85ea05f95246e8142d1f5dab9fe58d1a0e1dcb83261b8cb5d4955a` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3359850[3340797:3377867]; xbl_b@3358266[3355345:3400091]
- digest=`03c672a9a537870fe487d9337b381bb8b226c9b0dc2317477ad247a0b522317a` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3360972[3340797:3377867]; xbl_b@3359388[3355345:3400091]
- digest=`03e63af0f070b060bc91ec03d6c658fd3bf9ca97edf9bb143b7b721cb9f6d38c` count=`2` tokens=`vdd` classes=`generic-power-token-context` locations=xbl_a@21763[20034:29600]; xbl_b@21915[20027:30662]
- digest=`0400bafc6948dbe2899720b44f6c69a97c5ec6f5e50aeaf9b50fa56c8c8c4e89` count=`2` tokens=`aop` classes=`generic-power-token-context` locations=xbl_a@3366943[3340797:3377867]; xbl_b@3365291[3355345:3400091]
- digest=`040cbc3029e90a60e501a66130d1727c42ec1ca1d2b51f29f73de0ebbd9ab52a` count=`2` tokens=`pon` classes=`generic-power-token-context` locations=xbl_a@21850[20034:29600]; xbl_b@22002[20027:30662]
- digest=`0a6d654815e988c10da522bc1f8d3b47335746480e7dc8afe3c0a5f2d0220ea8` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3359330[3340797:3377867]; xbl_b@3357746[3355345:3400091]
- digest=`0cf0ca48efe387a43cce57e5e65e0d0a5251b55840c4f03ff693ede8f92dc06f` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3358794[3340797:3377867]; xbl_b@3357210[3355345:3400091]
- digest=`138af1e5803e5074c7fcfe48b5b5350375c9f05c1adb71e6ea2607d36a66e0dd` count=`2` tokens=`pmic` classes=`generic-power-token-context` locations=xbl_a@26720[20034:29600]; xbl_b@27392[20027:30662]
- digest=`15ad159461a10535357018e9a1982f88bd407c09935e1d0c05ddbb467eed6897` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3359255[3340797:3377867]; xbl_b@3357671[3355345:3400091]
- digest=`19183f445bdadcf7c20d1ce6721baf866e78e16d9d2bb3d5af17f4499ab156e8` count=`2` tokens=`ps_hold` classes=`no-token-context` locations=xbl_a@21667[20034:29600]; xbl_b@21819[20027:30662]
- digest=`222255e31500684b318d6b91a37f19da538e0eadf27425ecc695002c00497463` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3361255[3340797:3377867]; xbl_b@3359671[3355345:3400091]
- digest=`25bdf51614ee374e62062a6d954d2e23a14e31e5726cb70aee5a3e8de1270fd0` count=`2` tokens=`aop` classes=`generic-power-token-context` locations=xbl_a@3343167[3340797:3377867]; xbl_b@3355353[3355345:3400091]
- digest=`271931788a918db7d52411f29dd9856195e928c676c7193dea20bacb21a6ca28` count=`2` tokens=`aop` classes=`generic-power-token-context` locations=xbl_a@3343299[3340797:3377867]; xbl_b@3365755[3355345:3400091]
- digest=`28aba3a00260b1a04487e0ec9d7a204fef928e304bb7bdd0c9afc683e67e9b50` count=`2` tokens=`rpmh` classes=`no-token-context` locations=xbl_a@3359702[3340797:3377867]; xbl_b@3358118[3355345:3400091]
- digest=`2ebdcac135986a36f3f5af5d03e63e7517c33862baf2442f28eac9b650e78b03` count=`2` tokens=`pcie` classes=`pcie-context` locations=xbl_a@3357265[3340797:3377867]; xbl_b@3385761[3355345:3400091]
- digest=`32486fe151f6485497b5b01d7ba6f05c581d826b5474485da92cf5b62c214911` count=`2` tokens=`pmic` classes=`generic-power-token-context` locations=xbl_a@25936[20034:29600]; xbl_b@26608[20027:30662]

## Hypotheses

| id | strength | claim | evidence | limit |
|---|---|---|---|---|
| `H1` | `strong` | XBL remains the highest-yield bootloader-side artifact for SDX50M power context. | Both XBL slots contain PMIC/PON/SDX/RPMh/AOP/PCIe-class records inside the V1652-approved ranges. | The records are redacted hashes and token classes; they do not identify a concrete register, GPIO, or rail write. |
| `H2` | `medium` | The early PON range is relevant to the SDX50M path. | sdx_present=True ps_hold_present=True; early approved ranges contain PMIC/PON/VDD/SDX records. | No raw string text is exposed, so the exact bootloader function or data-table name remains private. |
| `H3` | `medium` | The dense RPMh/AOP range is likely a boot-resource vocabulary table or nearby code/data cluster. | rpmh_dense=True; large record clusters preserve RPMh/AOP/PMIC/PCIe token proximity. | Many records classify as no-token-context because the helper only emits hashed strings; semantic naming is intentionally absent. |
| `H4` | `weak-medium` | Cross-slot duplicate hashes show shared XBL code/data, but slot-local deltas still matter. | cross_slot_duplicate_groups=96 gpio_token_present=True. | Differences between xbl_a and xbl_b are not automatically causal without Android-good vs native-fail linkage. |

## Decision

V1655 keeps XBL as the strongest artifact-level explanation path, but it does not authorize direct PMIC, GPIO, GDSC, PCI, eSoC, or upper Wi-Fi actions. The evidence is sufficient for another host-only mapping pass, not for mutation.

## Next

V1656 should stay host-only and map these redacted hashes/classes against Android-good boot references or OSRC/XBL-adjacent public metadata where possible. A bounded rail or PMIC write requires a separate explicit gate with a concrete target and rollback contract.
