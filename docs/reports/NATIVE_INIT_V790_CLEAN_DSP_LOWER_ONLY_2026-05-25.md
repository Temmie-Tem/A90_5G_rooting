# Native Init V790 Clean-DSP Lower-Only Report

## Result

- decision: `v790-clean-dsp-lower-only-blocked`
- pass: `false`
- runner: `scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py`
- evidence: `tmp/wifi/v790-clean-dsp-lower-only/`

## What Ran

```bash
python3 -m py_compile scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py
python3 scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py plan
python3 scripts/revalidation/native_wifi_clean_dsp_lower_only_v790.py run \
  --assume-yes \
  --allow-arm-clean-dsp \
  --allow-reboot \
  --allow-cleanup-umount \
  --allow-system-mount \
  --allow-selinuxfs-mount \
  --allow-policy-load \
  --allow-firmware-mounts \
  --allow-subsys-modem-holder \
  --allow-lower-companion \
  --allow-cleanup-reboot
```

## Evidence Summary

| Signal | Result |
| --- | --- |
| inline clean-DSP proof | pass |
| V401 SELinuxfs mount | pass |
| V490 policy load | pass |
| lower companion order | `qrtr-ns,rmt_storage,tftp_server,pd-mapper` |
| `cnss_diag` / `cnss-daemon` | not executed |
| `mss` | `OFFLINING -> ONLINE -> ONLINE` |
| `mdm3` | `OFFLINING -> OFFLINING -> OFFLINING` |
| QRTR RX/TX | `1 / 1` |
| `sysmon-qmi` | `4` |
| service-notifier markers | `2` |
| MHI/QCA6390/WLFW/BDF/`wlan0` | `0 / 0 / 0 / 0 / 0` |
| warning boundary | `pm_qos_add_request` duplicate request |
| post-cleanup health | healthy v724 |

## Interpretation

V790 reproduces the same warning boundary as V788 without `cnss_diag` or
`cnss-daemon`. That narrows the current blocker: CNSS-only userspace is not
required to trigger the warning. The shared trigger surface is now:

1. clean-DSP one-shot;
2. current V401/V490 SELinux prep;
3. lower companion stack;
4. service-notifier `180/74`;
5. ADSP/APR audio deferred probe;
6. duplicate `msm_asoc_machine_probe`;
7. `pm_qos_add_request()` duplicate request warning.

V787 clean-DSP alone was warning-free, and historical V733 lower-only was
warning-free. The failure appears in the combined current clean-DSP plus lower
companion path. This must be classified before CNSS/HAL/scan/connect work
continues.

## Safety

- `cnss_diag`/`cnss-daemon`: not executed
- service-manager start: not executed
- Wi-Fi HAL start: not executed
- scan/connect: not executed
- credential use: not executed
- DHCP/routes/external ping: not executed
- boot image or partition write: not executed
- custom kernel flash: not executed
- cleanup reboot: executed and post-cleanup status is healthy

## Next

V791 should be host-only first. Compare V790, V788, V787, and historical V733
to decide whether the next safe live isolation should omit V401/V490, omit
clean-DSP, or only read lower service surfaces without spawning the lower
companion daemons. Do not repeat lower companion live until that classifier is
written.
