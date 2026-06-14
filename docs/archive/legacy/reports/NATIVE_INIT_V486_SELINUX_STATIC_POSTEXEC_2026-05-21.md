# Native Init V486 SELinux Static Postexec Proof

- Date: 2026-05-21 KST
- Scope: bounded native-init SELinux domain handoff proof
- Result: `v486-selinux-static-postexec-kernel-stuck`
- Pass meaning: the blocker was isolated with a static post-exec proof; native-init Wi-Fi connect and external ping are still not achieved

## What Changed

- Added `a90_android_execns_probe v44` static post-exec SELinux proof support.
- Added internal `/proc/self/exe --selinux-print-current` path so the proof does not depend on Android `toybox` or bionic linker startup.
- Added `native_selinux_static_postexec_v486.py` to run a bounded matrix over Android service/HAL target domains.
- Added `wifi_execns_helper_v44_deploy_preflight.py` to deploy only `/cache/bin/a90_android_execns_probe` with explicit approval.
- Fixed V486 helper deploy preflight so an older remote helper is treated as `needs-deploy`, not as a hard blocker.
- Fixed post-exec evidence normalization so `postexec.current` is compared as the actual context value, not the full child output line.

## Evidence

- Build artifact: `tmp/wifi/v486-a90_android_execns_probe-v44/a90_android_execns_probe`
- Build SHA-256: `150630c088dda1e53173021575420a996cf395ded049bfdf0ab26e71dd4c38c9`
- Deploy preflight: `tmp/wifi/v486-helper-preflight-20260521-050828/manifest.json`
- Final deploy evidence: `tmp/wifi/v486-helper-redeploy-20260521-051642/manifest.json`
- Final live evidence: `tmp/wifi/v486-selinux-static-postexec-rerun-20260521-052305/manifest.json`
- Final summary: `tmp/wifi/v486-selinux-static-postexec-rerun-20260521-052305/summary.md`
- Post-status capture: `tmp/wifi/v486-post-status-20260521-052320.json`

## Matrix Result

| context | attr_mode | write_current | verify_current | write_exec | verify_exec | postexec_current | postexec_match |
|---|---:|---:|---:|---:|---:|---|---:|
| `u:r:hal_wifi_default:s0` | `exec` | - | - | `1` | `0` | `kernel` | `false` |
| `u:r:hal_wifi_default:s0` | `both` | `1` | `0` | `1` | `0` | `kernel` | `false` |
| `u:r:servicemanager:s0` | `exec` | - | - | `1` | `0` | `kernel` | `false` |
| `u:r:servicemanager:s0` | `both` | `1` | `0` | `1` | `0` | `kernel` | `false` |
| `u:r:hwservicemanager:s0` | `exec` | - | - | `1` | `0` | `kernel` | `false` |
| `u:r:hwservicemanager:s0` | `both` | `1` | `0` | `1` | `0` | `kernel` | `false` |

Representative transcript facts:

```text
selinux_domain_proof.write_exec.ok=1
selinux_domain_proof.verify_exec.match=0
selinux_domain_proof.verify_exec.value=kernel
selinux_domain_proof.postexec.raw=selinux_postexec_static.current=kernel
selinux_domain_proof.postexec.current=kernel
selinux_domain_proof.postexec.exit_code=0
selinux_domain_proof.postexec.match=0
```

## Interpretation

- The helper can write `/proc/self/task/<tid>/attr/current` and `attr/exec` without syscall failure, but readback remains `kernel`.
- Static post-exec via `/proc/self/exe --selinux-print-current` also remains `kernel` for `hal_wifi_default`, `servicemanager`, and `hwservicemanager` targets.
- This removes the V478 ambiguity where Android `toybox` startup could have hidden the post-exec context result.
- The V485 Android comparison remains valid: Android normally runs Samsung Wi-Fi HAL under `u:r:hal_wifi_default:s0`, while native-init bounded execution remains in `kernel`.
- Current strongest blocker before Wi-Fi HAL registration is SELinux domain handoff, not SSID scan/connect logic.

## Safety

- No service-manager, hwservicemanager, Wi-Fi HAL, CNSS, wpa_supplicant, wificond, scan, connect, DHCP, route change, credential read, or external ping was executed.
- V486 only performed child-local SELinux attr write/read and static re-exec proof commands.
- Final postflight was clean.
- Final native status remained healthy: `selftest: pass=11 warn=1 fail=0`.

## Next Work

1. Decide whether native init should mount/use Android SELinux policy surfaces before service/HAL starts, or whether Wi-Fi service experiments must explicitly run under a known fallback context.
2. Capture Android boot-complete SELinux procattr behavior for the same target contexts if more policy semantics are needed.
3. Do not retry Samsung Wi-Fi HAL registration as a supposed fix until the domain handoff issue is either corrected or intentionally accepted as non-fatal.
4. After domain handling is resolved, rerun Samsung `ISehWifi/default` registration, then readiness calls, then scan/connect/link-up, then external ping.
