# WSTA214 AppArmor Feasibility

Date: 2026-07-05

## Verdict

PASS, with AppArmor not available under current evidence.  WSTA214 adds a
host-only AppArmor feasibility audit and concludes AppArmor should not be used
as the immediate D-harden lever.

Private evidence:

```text
workspace/private/runs/server-distro/wsta214-apparmor-feasibility-20260705T2205KST/wsta214_result.json
workspace/private/runs/server-distro/wsta214-apparmor-feasibility-20260705T2205KST/wsta214_apparmor_feasibility.json
workspace/private/runs/server-distro/wsta214-apparmor-feasibility-20260705T2205KST/wsta214_apparmor_feasibility.md
```

Decision:

```text
wsta214-apparmor-feasibility-source-pass
```

## Feasibility State

The accepted audit records:

```text
state=APPARMOR_NOT_AVAILABLE_UNDER_CURRENT_EVIDENCE
recommendation=do-not-use-apparmor-as-immediate-d-harden-lever
preferred_current_hardening_lever=legacy-iptables-loopback-default-drop
kernel_config_ready=false
runtime_observed=false
userspace_staged=false
profile_source_ready=false
profile_load_allowed=false
```

Blocking evidence:

```text
CONFIG_SECURITY_APPARMOR=y
runtime LSM/AppArmor presence
apparmor userspace/parser staged in Debian rootfs
```

This means the current server-distro path should not branch into AppArmor
profile work until new kernel/runtime/userspace evidence appears.

## Inputs

WSTA214 consumed existing redacted/source artifacts only:

```text
workspace/private/runs/server-distro/d0-device-live-20260702T200338Z/inventory_public_summary.json
workspace/private/runs/server-distro/debian-eye-hw-inventory-20260704T082032Z/debian_eye_public_summary.json
workspace/public/src/scripts/server-distro/build_debian_aarch64_rootfs.py
workspace/public/src/scripts/server-distro/prepare_wsta3_sta_rootfs.py
```

## Safety

This was host-only audit work.  No device action, boot flash, native reboot,
Wi-Fi connect/association, DHCP, ping, public tunnel, public smoke,
packet-filter mutation, rootfs mount, package install, userdata write, LSM
profile load, or switch-root occurred.

Safety fields from the accepted result:

```text
device_action=false
boot_flash=false
native_reboot=false
wifi_connect=false
dhcp=false
ping=false
public_tunnel=false
packet_filter_mutation=false
rootfs_mount=false
package_install=false
lsm_profile_load=false
userdata_touch=false
switch_root=false
public_url_value_logged=false
secret_values_logged=0
```

## Code Changes

- Added `run_wsta214_apparmor_feasibility.py`.
- Added focused WSTA214 tests.
- Updated `GOAL.md` with the accepted WSTA214 result.

## Next

Fold WSTA214 into the WSTA108 operator status bundle so AppArmor is parked from
immediate next-actions.  Continue D-harden through the already proven
legacy-iptables loopback/default-drop lever unless new AppArmor evidence appears.
