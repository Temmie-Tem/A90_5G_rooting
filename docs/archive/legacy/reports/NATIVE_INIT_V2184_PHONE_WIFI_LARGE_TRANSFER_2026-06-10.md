# Native Init V2184 Phone Wi-Fi Large Transfer Validation

## Summary

- Baseline under test: `A90 Linux init 0.9.256 (v2184-network-ui-p0-p1)`.
- Phone-side server: `a90-wifi-lab-20260610-upload-metadata-v2`.
- Type: same-LAN phone server download/upload integrity validation.
- Decision: `v2184-phone-large-transfer-512m-1g-pass`.
- Result: PASS.
- Reason: A90 completed 512MiB and 1GiB bidirectional transfers over `wlan0`,
  and SHA256 matched on both download and upload paths.
- Evidence directory:
  `workspace/private/runs/wifi/v2184-phone-large-transfer-20260610-072720`.

## Results

| Size | Direction | SHA256 | Command Duration | Throughput |
| --- | --- | --- | --- | --- |
| `512MiB` | Phone to A90 download | match | `14.325s` | `35.742 MiB/s` |
| `512MiB` | A90 to phone upload | match | `8.013s` | `63.896 MiB/s` |
| `1GiB` | Phone to A90 download | match | `27.247s` | `37.582 MiB/s` |
| `1GiB` | A90 to phone upload | match | `15.225s` | `67.258 MiB/s` |

Phone receiver timing reported:

- `512MiB` upload: `7.516746s`, `68.115 MiB/s`.
- `1GiB` upload: `14.300933s`, `71.604 MiB/s`.

Post-transfer state:

- `wlan0` remained present and carrier stayed `1`.
- Final native-init selftest reported `fail=0`.

## Safety Scope

- A90 and the phone were on the same local Wi-Fi/LAN.
- Transfer files were staged under removable/private storage on A90, not under
  `/cache`.
- Public report omits private IP addresses, SSID, BSSID, MAC-derived peer
  details, and raw artifact paths beyond the private evidence root.
- No credentials were printed by the transfer server or public report.

## Notes

- This closes a strong single-run large-transfer integrity check for V2184.
- It is not a multi-hour soak or N-run large-transfer campaign.
- A practical follow-up, if needed before baseline promotion, is
  `cleanup -> reconnect -> 512MiB bidirectional SHA` once.
