# Server-Distro WSTA18 Handoff Control-Plane Blocked

- Date: 2026-07-04
- Scope: native pre-handoff vs Debian post-handoff WLAN control-plane comparison
- Native resident: `0.11.140 (v3384-server-distro-hardware-contract)`
- Public exposure: not started
- Final device state: native V3384, `selftest fail=0`

## Summary

WSTA18 kept the WSTA17 lesson: do not cycle the Debian link down as a recovery step.  It
reused the link-down-free WSTA16 snapshot image and compared native pre-handoff WLAN
control-plane evidence with Debian post-handoff evidence.

Live result: native STA-only scan again materialized `wlan0` and visible BSS before handoff.
After `switch_root`, Debian still saw a managed `wlan0`, phy, and unblocked WLAN rfkill,
but direct `iw scan` returned rc `234` / `Invalid argument (-22)`.  A plain
`ip link set wlan0 up` without prior link-down returned rc `0`, so WSTA17's rc `2` was
specifically caused by the diagnostic link-down branch.  The stronger finding is from dmesg:
after PID1 handoff, the WLAN firmware/control path reports `firmware down indication`,
`PD service down ... Root PD shutdown`, and repeated `WMI stop in progress`.  The Debian
process snapshot lacks the native vendor WLAN userspace (`cnss-daemon`, `cnss_diag`, and
related Android/vendor companions); only kernel WLAN threads and Debian `dropbear` remain.

## Source Changes

None.  This was a report-only live diagnostic using the previously prepared WSTA16
snapshot-only image copied into a WSTA18 private run directory.

## Artifact Preparation

```text
run_dir=workspace/private/runs/server-distro/wsta18-control-plane-20260703T2351Z
source_image=WSTA16 immediate snapshot image
image_sha256=b8f0f98ea24875e5daada9d17ecfd62067ff316129308c83bda6d54910dac58a
remote_sha_match=true
```

No boot flash ran for WSTA18.  No userdata format/populate path ran.

The first handoff attempt stopped at `handoff-display-owner rc=-16` and unmounted the rootfs
after failure.  Because the image had been mounted rw, the SHA changed; the image was
reuploaded from the local private copy, the remote SHA matched again, and the retry reached
`exec_switch_root_now`.

## Live Evidence

Native pre-handoff gate:

```text
decision=wsta15-native-sta-only-scan-engine-ok
attempts_completed=11
attempt 11: wifi-scan-pass scan_result_count=10
selftest_fail_zero=true
```

Native pre-handoff control-plane evidence:

```text
wlan0_flags=0x1003
wlan_rfkill_state=unblocked
phy0_present=true
dmesg: cnss_diag cld80211 netlink activity
dmesg: cnss-daemon cld80211 netlink activity
dmesg: WLAN FW ready and driver loaded before handoff
```

Debian post-handoff marker and direct probes:

```text
pid1_comm=init
dropbear_started=1
wifi_sta_wlan0_present=1
wifi_sta_immediate_link_set_up_rc=0
wifi_sta_reg_immediate_before_link_up_iw_scan_rc=234
wifi_sta_reg_immediate_after_link_up_iw_scan_rc=234
manual_iw_scan_rc=234
manual_iw_scan_error=Invalid argument (-22)
manual_link_up_rc=0
tunnel_wifi_sta_gate_ok=0
```

Debian post-handoff process/control-plane evidence:

```text
present: cfg80211 kernel thread
present: WCNSS kernel threads
present: wlan_logging_th kernel thread
present: Debian dropbear
absent: cnss-daemon userspace
absent: cnss_diag userspace
absent: pm-service / qrtr-ns / pd-mapper / tftp_server / rmt_storage vendor userspace
```

Focused dmesg after handoff:

```text
firmware down indication
PD service down, cause: Root PD shutdown
WMI stop in progress
Failed to send WMI_DBGLOG_TIME_STAMP_SYNC_CMDID command
```

The device was rebooted from Debian and returned to native V3384:

```text
version=0.11.140 build=v3384-server-distro-hardware-contract
selftest: pass=12 warn=1 fail=0
```

## Interpretation

The failure is now below supplicant and below L3, but it is no longer just a generic
netdev/`iw` issue.  `switch_root` tears down or loses the Android/vendor WLAN control plane
that keeps the WCNSS root PD and WMI path alive.  Debian inherits enough kernel objects to
show `wlan0`/phy/rfkill, but the firmware control path is already down, so direct scan is
invalid.

The next design should not keep pushing direct Debian netdev ownership.  The practical
choices are:

1. preserve/relaunch the minimal vendor WLAN userspace/control-plane set across handoff;
2. keep Wi-Fi owned by native init and expose a bounded service/API to Debian;
3. run Debian as a chroot/container under native PID1 for the Wi-Fi-enabled appliance path
   instead of full `switch_root`;
4. treat full Debian PID1 handoff as local USB/server-only unless a control-plane bridge is
   built.

## Hygiene

- No public tunnel was started.
- No association, DHCP, gateway ping, DNS, API POST, or cloudflared path ran.
- No Wi-Fi SSID, PSK, BSSID, MAC, DHCP lease, private Wi-Fi address, gateway, DNS server,
  public URL, or generated hostname is recorded in this report.
- Raw transcripts, SSH keys, and images remain under `workspace/private/runs/`.
- The device ended on native V3384 with `selftest: pass=12 warn=1 fail=0`.
