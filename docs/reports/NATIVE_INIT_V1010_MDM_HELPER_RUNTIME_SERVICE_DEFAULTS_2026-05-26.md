# V1010 mdm_helper Runtime Contract Service-defaults Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| plan | `tmp/wifi/v1010-mdm-helper-runtime-contract-service-defaults-plan/manifest.json` | `v1010-mdm-helper-runtime-contract-plan-ready` |
| live proof | `tmp/wifi/v1010-mdm-helper-runtime-contract-service-defaults-live/manifest.json` | `v1010-mdm-helper-esoc-fd-observed` |
| post-live health | `tmp/v1010-post-bootstatus.txt` | `selftest: pass=11 warn=1 fail=0` |

V1010 ran the reduced V911 order with helper `v171`, but forced
`--android-selinux-context-mode service-defaults`. The result stayed
fd-positive: `mdm_helper` opened `/dev/esoc-0` in both the window and final
snapshots.

## Key Evidence

| Signal | Value |
| --- | --- |
| helper | `a90_android_execns_probe v171` |
| mode | `wifi-companion-mdm-helper-runtime-contract-capture` |
| order | `property-shim,per_mgr_light,mdm_helper,no-pm_proxy_helper,no-controller-subsys-open` |
| Android SELinux context mode | `service-defaults` |
| `per_mgr_light` exec context | `u:r:vendor_per_mgr:s0` |
| `mdm_helper` exec context | `u:r:vendor_mdm_helper:s0` |
| `/dev/esoc-0` fd | `window=1 final=1` |
| `/dev/subsys_esoc0` controller open | `0` |
| `ks` / MHI process | `0` |
| cleanup reboot | `false` |

Post-live health remained clean:

```text
boot: BOOT OK shell 4.2s
selftest: pass=11 warn=1 fail=0
exposure: guard=ok warn=0 fail=0 ncm=absent tcpctl=stopped rshell=stopped boundary=usb-local
```

## Interpretation

V1010 closes the hypothesis that V911 only worked because `mdm_helper` stayed in
the `kernel` execution context. With service-defaults enabled,
`mdm_helper` transitioned to `u:r:vendor_mdm_helper:s0` and still opened
`/dev/esoc-0`.

The remaining V1008 gap is therefore not simply the `mdm_helper` SELinux domain.
The strongest next suspect is the full service-window environment:

1. actor ordering around service-manager, HAL, `wificond`, `per_mgr`, and
   `cnss-daemon`;
2. `per_mgr` lifecycle, because V1010 keeps `per_mgr_light` alive while V1008's
   full `per_mgr` exits `0`;
3. property/service state differences introduced by the larger actor set before
   `mdm_helper` checks `/dev/esoc-0`.

## Guardrails

V1010 did not perform final Wi-Fi bring-up work:

- no service-manager, CNSS daemon, Wi-Fi HAL, or `wificond`;
- no `/dev/subsys_esoc0` controller open;
- no eSoC ioctl;
- no Wi-Fi scan/connect/link-up;
- no credential use;
- no DHCP/routes;
- no external ping;
- no boot image, partition, firmware, GPIO, sysfs, or debugfs mutation.

## Validation

Executed:

```bash
python3 -m py_compile scripts/revalidation/native_wifi_mdm_helper_runtime_contract_service_defaults_v1010.py
python3 scripts/revalidation/native_wifi_mdm_helper_runtime_contract_service_defaults_v1010.py \
  --out-dir tmp/wifi/v1010-mdm-helper-runtime-contract-service-defaults-plan \
  plan
python3 scripts/revalidation/native_wifi_mdm_helper_runtime_contract_service_defaults_v1010.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-runtime-contract-capture \
  --allow-cleanup-reboot \
  --assume-yes \
  run
```

Result:

```text
decision: v1010-mdm-helper-esoc-fd-observed
pass: True
mdm_helper_start_executed: True
subsys_esoc0_open_attempted: False
wifi_hal_start_executed: False
external_ping_executed: False
```

## Next

Plan V1011 as a host-only comparator between V1008 and V1010 focused on the
full service-window actor delta. The likely live follow-up is a minimal
incremental actor gate: start reduced V1010 first, confirm `/dev/esoc-0`, then
add only the next Android-timing actor needed to see whether the fd disappears
or whether WLFW preconditions advance.
