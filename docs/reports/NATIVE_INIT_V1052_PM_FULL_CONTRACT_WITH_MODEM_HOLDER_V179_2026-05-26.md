# V1052 PM Full-Contract with Modem Holder v179 Report

## Result

| Unit | Evidence | Decision |
| --- | --- | --- |
| current-boot selinuxfs | `tmp/wifi/v1052-v401-selinuxfs-mount/manifest.json` | `toybox-selinuxfs-mount-live-executor-run-pass` |
| policy load | `tmp/wifi/v1052-v490-policy-load-v179/manifest.json` | `v490-selinux-policy-load-proof-pass` |
| PM domain proof | `tmp/wifi/v1052-v1042-pm-selinux-domain-proof-v179/manifest.json` | `v1042-pm-selinux-domain-handoff-present` |
| live gate | `tmp/wifi/v1052-pm-full-contract-with-modem-holder-live/manifest.json` | `v1052-modem-pre-holder-not-confirmed-clean` |

V1052 proves the V1050 namespace repair worked: the modem pre-holder entered the
helper private root and attempted `/dev/subsys_modem`. The remaining blocker is
not path visibility; the driver open returned `errno=14` and the PM fd contract
still did not form.

## Findings

- Helper/live guard:
  - helper: `a90_android_execns_probe v179`
  - matrix: `pm_full_contract_with_modem_holder_matrix=1`
  - runtime-domain guard blocked: `0`
  - cleanup reboot executed: `1`
- Private node:
  - `private_node.subsys_modem.exists=1`
  - `private_node.subsys_modem.path=/tmp/a90-v231-711/root/dev/subsys_modem`
  - major/minor: `236:0`
  - mode/owner: `0640`, `1000:1000`
- Modem pre-holder:
  - `modem_pre_holder_child_chroot=1`
  - `modem_pre_holder_path=/dev/subsys_modem`
  - `modem_pre_holder_opened=0`
  - `modem_pre_holder_errno=14`
  - `modem_pre_holder_open_reported=0`
  - `modem_pre_holder_result_reported=1`
  - `modem_pre_holder_confirmed=0`
- PM fd contract:
  - `pm_proxy_helper_subsys_modem_fd_count=0`
  - `per_mgr_subsys_modem_fd_count=0`
  - `pm_full_contract_seen=0`
- Actor/postflight:
  - `mdm_helper_esoc0_fd_seen=1`
  - `all_postflight_safe=0`
  - `result=reboot-required`
  - post-reboot `bootstatus` and `selftest` passed.

## Interpretation

V1049's `ENOENT` was a helper namespace bug and is fixed. V1052 exposes the next
lower blocker: opening the private-root `/dev/subsys_modem` character device
returns `EFAULT` (`errno=14`) before a holder fd can be established.

The next source/build-only step should distinguish whether `EFAULT` is caused by
the first `O_NONBLOCK` open attempt. Older lower-window shell holders used a
plain blocking open path, so a bounded fallback from nonblocking open to plain
open is the next minimal test. Do not widen to service-manager, HAL, scan/connect,
or Wi-Fi bring-up until `/dev/subsys_modem` holder formation is understood.

## Validation

```bash
python3 -m py_compile scripts/revalidation/native_wifi_pm_full_contract_with_modem_holder_live_v1052.py
python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --out-dir tmp/wifi/v1052-v401-selinuxfs-mount \
  --approval-phrase "approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --out-dir tmp/wifi/v1052-v490-policy-load-v179 \
  --helper-sha256 9cb6d49849af181a87a5619e7b3ed7f0f513223ef97ce8b0599ce43694453a7b \
  --approval-phrase "approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_wifi_pm_selinux_domain_proof_v177_v1042.py \
  --out-dir tmp/wifi/v1052-v1042-pm-selinux-domain-proof-v179 \
  --v490-manifest tmp/wifi/v1052-v490-policy-load-v179/manifest.json \
  --helper-sha256 9cb6d49849af181a87a5619e7b3ed7f0f513223ef97ce8b0599ce43694453a7b \
  --approval-phrase "approve v1042 PM SELinux domain proof v177 only; no daemon start and no Wi-Fi bring-up" \
  --apply --assume-yes run
python3 scripts/revalidation/native_wifi_pm_full_contract_with_modem_holder_live_v1052.py \
  --allow-mountsystem-ro \
  --allow-selinuxfs-mount \
  --allow-mdm-helper-cnss-service-manager-matrix \
  --allow-pm-full-contract-with-modem-holder \
  --allow-cleanup-reboot \
  --assume-yes run
python3 scripts/revalidation/a90ctl.py --hide-on-busy bootstatus
python3 scripts/revalidation/a90ctl.py --hide-on-busy selftest
```

## Guardrails

No `ks`, MHI pipe transfer, Wi-Fi HAL, `wificond`, scan/connect, credentials,
DHCP/routes, external ping, controller eSoC notify, BOOT_DONE spoofing, boot
image write, partition write, firmware mutation, GPIO write, sysfs write, or
debugfs write occurred. `/dev/subsys_esoc0` was not opened because WLFW
precondition was not observed.

## Next

V1053 should be source/build-only: change the pre-holder to record the first
nonblocking errno and retry a plain blocking `open("/dev/subsys_modem")` for the
bounded holder path, producing helper `v180`.
