# NATIVE_INIT V2697 — ACDB firmware corpus staging

Date: 2026-06-18

## Scope

Host-only firmware extraction. The script extracts `vendor.img.ext4.lz4` from the private stock AP tar, converts the Android sparse vendor image to raw ext4 under `workspace/private`, rdumps only `/etc/acdbdata`, and reruns the V2696 scanner against that staged corpus. No device action, flash, Android handoff, audio ioctl, mixer write, PCM probe, or raw ACDB payload commit occurred.

## Result

- decision: `v2697-firmware-acdbdata-staged-selected-records-absent`
- ok: `True`
- stage_dir: `workspace/private/inputs/audio/acdbdata-v2697-firmware`
- scanner_decision: `v2696-acdb-db-staged-selected-records-incomplete`
- scanner_db_file_count: `1`

## Staged ACDB files

| file | size | sha256 |
| --- | ---: | --- |
| `workspace/private/inputs/audio/acdbdata-v2697-firmware/acdbdata/adsp_avs_config.acdb` | 240 | `93486f387507b7b8fb4e5bcb8472b4dece625ac9088e7c75dc591fece8a713da` |

## Selected topology DB scan

| cal_type | role | selected topology | DB parseable | payload parseable |
| ---: | --- | --- | --- | --- |
| 10 | `ADM_CUST_TOPOLOGY` | `0x10004000` | `False` | `True` |
| 14 | `ASM_CUST_TOPOLOGY` | `0x10005000` | `False` | `True` |
| 24 | `AFE_CUST_TOPOLOGY` | `0x1001025d` | `False` | `True` |

## Interpretation

The stock AP vendor image contains only one `/etc/acdbdata` file in this firmware extract: `adsp_avs_config.acdb` (240 bytes). The V2696 scanner finds no selected ADM `0x10004000`, ASM `0x10005000`, or AFE `0x1001025d` parseable records in that DB corpus. This means the selected topology records recovered in the core/custom payload are not present as simple parseable records in the staged `/vendor/etc/acdbdata` corpus.

This closes the host-only DB-staging branch as a source of byte-exact cal10/cal14 selected payloads. The remaining meaningful path is route-specific Android-good capture of the real HAL custom-topology SET path, or deeper libacdbloader runtime selector RE inside the own-process helper; native replay remains parked until byte-exact selected cal10/cal14 payloads are recovered.

## Validation

- `python3 -m py_compile workspace/public/src/scripts/revalidation/stage_audio_acdbdata_from_firmware_v2697.py tests/test_stage_audio_acdbdata_from_firmware_v2697.py`
- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation python3 -m unittest tests.test_stage_audio_acdbdata_from_firmware_v2697 -v`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/stage_audio_acdbdata_from_firmware_v2697.py --write-report`
- `PYTHONPATH=workspace/public/src/scripts/revalidation python3 workspace/public/src/scripts/revalidation/analyze_audio_acdb_db_selected_topology_v2696.py --db-root workspace/private/inputs/audio/acdbdata-v2697-firmware --json`
- `git diff --check`
