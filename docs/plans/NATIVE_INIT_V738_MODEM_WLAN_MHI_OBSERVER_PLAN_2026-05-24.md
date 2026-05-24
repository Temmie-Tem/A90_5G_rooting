# Native Init V738 Modem/WLAN/MHI Observer Plan

- date: `2026-05-24 KST`
- runner: `scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py`
- evidence target: `tmp/wifi/v738-modem-wlan-mhi-observer/`

## Goal

Run the next bounded live observer selected by V737:

```text
real vendor firmware namespace
  + subsys_modem holder
  + lower companion stack
  + CNSS diag/daemon start-only
  -> classify mss/mdm3, WLAN static surface, QCA/MHI/WLFW/service 69, BDF, wlan0
```

V738 keeps the previous safety boundary: no service-manager, no Wi-Fi HAL,
no scan/connect, no credential use, no DHCP/routes, and no external ping.

## Inputs

| input | purpose |
| --- | --- |
| V737 | corrected SM8250 CNSS2/PCIe routing |
| V735-compatible observer | known safe firmware-mounted modem holder + lower/CNSS-only live window |
| V401 | current-boot `selinuxfs` runtime surface |
| V490 | current-boot native SELinux policy-load proof |

## Scope

Allowed:

1. mount `selinuxfs` for the current boot;
2. load the Android SELinux split policy without init reexec;
3. mount firmware/vendor surfaces read-only inside the proof window;
4. open and hold only `subsys_modem`;
5. start lower companion services and `cnss_diag`/`cnss-daemon` start-only;
6. reboot as cleanup boundary.

Forbidden:

```text
esoc0 open
subsystem state writes
module load/unload
service-manager start
Wi-Fi HAL start
scan/connect
credential use
DHCP/routes
external ping
boot or partition writes
```

## Expected Classification

If `mss` reaches `ONLINE` but `mdm3` stays `OFFLINING`, and QCA/MHI/WLFW/BDF/
`wlan0` stay absent, V738 classifies the blocker as the lower `mdm3`/WLAN-PD to
MHI continuation gap and routes V739 to Android/native lower-trigger comparison.

## Validation Commands

```bash
python3 -m py_compile scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py

python3 scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py \
  --out-dir tmp/wifi/v738-modem-wlan-mhi-observer-plan plan

python3 scripts/revalidation/a90ctl.py --timeout 10 hide

python3 scripts/revalidation/wifi_selinuxfs_toybox_mount_live_executor.py \
  --out-dir tmp/wifi/v738-v401-current-run-retry \
  --approval-phrase 'approve v401 toybox mount selinuxfs runtime surface only; no daemon start and no Wi-Fi bring-up' \
  --apply --assume-yes run

python3 scripts/revalidation/a90ctl.py --timeout 30 mountsystem ro

python3 scripts/revalidation/native_selinux_policy_load_proof_v490.py \
  --out-dir tmp/wifi/v738-v490-current-run \
  --expect-version 'A90 Linux init 0.9.68 (v724)' \
  --helper-sha256 547232ddb352740bb7a7f1d0f9116162584e34a536b9d9b77869ed8d838e7c89 \
  --approval-phrase 'approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up' \
  --apply --assume-yes run

python3 scripts/revalidation/native_wifi_modem_wlan_mhi_observer_v738.py \
  --out-dir tmp/wifi/v738-modem-wlan-mhi-observer \
  --v490-manifest tmp/wifi/v738-v490-current-run/manifest.json \
  run
```
