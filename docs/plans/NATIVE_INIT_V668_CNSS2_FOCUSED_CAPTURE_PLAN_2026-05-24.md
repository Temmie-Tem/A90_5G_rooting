# Native Init V668 cnss2 Focused Capture Plan

- date: `2026-05-24 KST`
- cycle: `V668`
- status: planned
- helper: `a90_android_execns_probe v110`
- runner: `scripts/revalidation/native_wifi_cnss2_focused_capture_v668.py`
- deploy wrapper: `scripts/revalidation/wifi_execns_helper_v110_deploy_preflight.py`

## Goal

V667 proved the next gap is between service-notifier `180/74` publication and
cnss2/QCA6390/WLFW progression. V668 adds focused read-only sysfs evidence
inside the known V666 service `74` positive window.

## Scope

V668 reuses the V666 bounded companion path:

```text
qrtr-ns -> rmt_storage -> tftp_server -> pd-mapper -> cnss_diag
  -> cnss-daemon -> service74 gate
  -> service-manager trio + vndservicemanager readiness
  -> initial cnss-daemon cleanup -> one cnss-daemon retry
```

Helper v110 adds read-only captures:

- immediately after service `74` opens;
- during the active companion/CNSS retry window.

Captured surfaces:

- `/sys/bus/platform/drivers/icnss`;
- `/sys/bus/platform/devices/18800000.qcom,icnss`;
- `/sys/bus/platform/devices/a0000000.qcom,cnss-qca6390`;
- `/sys/class/net` and `/sys/class/net/wlan0`;
- selected `uevent`, `modalias`, and `power/*` attributes;
- optional `/sys/kernel/debug/icnss` if present.

## Guardrails

V668 does not authorize:

- sysfs writes or subsystem state writes;
- direct ADSP/CDSP/SLPI boot-node writes;
- `esoc0` open/hold;
- Wi-Fi HAL, `wificond`, supplicant, or hostapd start;
- `qcwlanstate` or driver-state writes;
- scan/connect/link-up, credentials, DHCP, routes, or external ping;
- boot image or partition writes.

## Success Criteria

The proof passes if:

- helper v110 is deployed and exposes `cnss2_focus` capture tokens;
- service `74` opens again;
- focused captures exist at both `service74_open` and `window` phases;
- cleanup remains bounded and postflight safe.

The decision labels distinguish:

| decision | meaning |
| --- | --- |
| `v668-cnss2-focused-capture-gap-classified` | focused captures are present, but WLFW/BDF/`wlan0` markers remain absent |
| `v668-cnss2-focused-capture-wifi-surface-advanced` | lower Wi-Fi markers advance enough to plan the next gate |
| `v668-cnss2-focused-capture-missing` | live ran but helper focused captures were incomplete |

## Commands

Build helper:

```bash
mkdir -p tmp/wifi/v668-execns-helper-v110-build
bash scripts/revalidation/build_android_execns_probe_helper.sh \
  tmp/wifi/v668-execns-helper-v110-build/a90_android_execns_probe
```

Plan:

```bash
python3 scripts/revalidation/native_wifi_cnss2_focused_capture_v668.py \
  --out-dir tmp/wifi/v668-cnss2-focused-capture-plan \
  plan
```

Deploy preflight/deploy:

```bash
python3 scripts/revalidation/wifi_execns_helper_v110_deploy_preflight.py \
  --out-dir tmp/wifi/v668-execns-helper-v110-deploy-preflight \
  preflight

python3 scripts/revalidation/wifi_execns_helper_v110_deploy_preflight.py \
  --out-dir tmp/wifi/v668-execns-helper-v110-deploy-live \
  --approval-phrase 'approve v668 deploy execns helper v110 only; no daemon start and no Wi-Fi bring-up' \
  --apply --assume-yes run
```

Live proof:

```bash
python3 scripts/revalidation/native_wifi_cnss2_focused_capture_v668.py \
  --out-dir tmp/wifi/v668-cnss2-focused-capture-live \
  --approval-phrase 'approve v668 service74 cnss2 focused capture proof only; no Wi-Fi HAL start, no scan/connect/link-up and no external ping' \
  --apply --assume-yes run
```

## Next

If V668 remains gap-classified, the next candidate should use the focused
captures to choose between cnss2 callback/power sequencing, PCIe/MHI readiness,
or WLFW QRTR publication. Do not proceed to Wi-Fi HAL or scan/connect until
WLFW/BDF/`wlan0` evidence advances.
