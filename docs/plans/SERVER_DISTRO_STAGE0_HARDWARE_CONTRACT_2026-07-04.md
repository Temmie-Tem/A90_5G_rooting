# Server-Distro Stage0 Hardware Contract

- Date: 2026-07-04
- Status: LOCKED SOURCE-SIDE CONTRACT
- Scope: A90 D4/D-public userdata appliance after the V3383 handoff-cleanup live pass.
- Device action in this doc: none. This is a host-only planning artifact.

## 0. Purpose

Native init is Stage 0 for the server-distro appliance. Its job is not to run every
hardware demo at boot. Its job is to materialize the small set of kernel surfaces
that Debian cannot reliably create by itself, then hand control to Debian cleanly.

This contract turns the broad endgame design into an operational hardware policy:

- keep the default appliance boot minimal;
- wake only hardware needed for recovery, handoff, local visibility, or upstream
  server connectivity;
- push demo-only hardware behind explicit opt-in commands;
- never widen the existing safety envelope.

The parent architecture remains
`docs/plans/NATIVE_INIT_SERVER_DISTRO_ENDGAME_DESIGN_2026-06-30.md`.

## 1. Principles

1. **Kernel surfaces, not Android HAL emulation.** Stage 0 exposes kernel-level
   nodes and state such as `/dev/dri/card0`, USB gadget configfs, `/dev/block/*`,
   `/dev/snd/*`, and `wlan0`. Debian owns ordinary server userspace after
   `switch_root`.
2. **Default boot is appliance-first.** If a subsystem is not needed for
   recovery/control, storage handoff, local operator visibility, or upstream
   connectivity, it is not started automatically.
3. **Native daemons do not linger unless named as keepers.** A native child that
   owns a resource Debian must use is stopped before `switch_root`. V3383 proved
   this for the DRM/KMS HUD path.
4. **Opt-in demos stay available.** Audio, GPU, video, Doom, and stress tools are
   useful operator features, but they are not part of the base server boot.
5. **Safety boundaries are unchanged.** No forbidden partition writes, no raw
   non-boot flash path, no PMIC/regulator/GDSC/GPIO/backlight power writes, and no
   from-scratch panel re-init.

## 2. Default Appliance Boot Contract

These surfaces belong in the default D4/D-public appliance path.

| Surface | Native action before handoff | Debian-visible result | Handoff rule |
| --- | --- | --- | --- |
| Boot/control console | Bring up the serial/cmdv1 control path while native init is PID 1. | Operator can recover and inspect pre-handoff native state. | Ends at `switch_root`; no native console owner should remain. |
| USB gadget: ACM + NCM | Configure the USB gadget for serial control and local USB network. | Local USB network remains the recovery/admin path. | Kernel gadget state may persist; native control daemons stop unless explicitly retained. |
| Storage/rootfs | Identify the guarded userdata target, materialize needed device nodes, mount the appliance root, prepare `/proc`, `/sys`, `/dev`, and `devpts`. | Debian sees `/dev/block/a90-userdata` as `/` and normal pseudo-filesystems. | Native must fail closed before `switch_root` on target mismatch or rootfs validation failure. |
| DRM/KMS display | Optional native boot HUD is allowed for visual progress. | Debian can start its own HUD on `/dev/dri/card0`. | Native must stop tracked HUD and terminate native DRM owners before `switch_root`. |
| Local health/status | Expose version, status, selftest, and handoff logs before exec. | Post-handoff evidence moves to Debian logs and services. | No long-running native monitor is required for the default appliance. |

The current V3383 live result satisfies the DRM/KMS handoff rule:
`handoff_display service=autohud stop_rc=0`, `handoff_display=done killed=3 rc=0`,
Debian PID1 came up, and no native `/init` process remained after handoff.

## 3. Next Required Hardware Rung: Wi-Fi STA

The server-distro appliance is not complete as a standalone device until upstream
internet can come from the phone itself rather than the host USB network.

Default target:

- **STA-only `wlan0` upstream**: join a trusted AP and let Debian/cloudflared use
  that route.

Deferred target:

- **SoftAP + STA concurrency**: useful later, but qcacld concurrency is a separate
  proof. Do not block the server appliance on it.

Stage 0 ownership:

| Surface | Native responsibility | Debian responsibility |
| --- | --- | --- |
| `wlan0` materialization | Vendor/qcacld bring-up and any required firmware/service glue. | IP config, route policy, tunnel client, and ordinary service networking once `wlan0` exists. |
| Wi-Fi credentials | Do not invent or commit credentials. Use private operator-provided config only. | Store/manage server profile in private runtime/config state. |
| Public tunnel | No inbound ports. Native init does not own the public tunnel. | Debian owns `cloudflared` or a later WireGuard/frp client as a normal service. |

Live validation for this rung must be bounded:

1. prove `wlan0` appears and remains stable;
2. prove STA association using private credentials only;
3. prove DHCP/static route to the upstream network;
4. prove Debian cloudflared can use the Wi-Fi route;
5. keep USB NCM as the recovery/admin path.

## 4. Opt-In Hardware

These stay available as commands or explicit profiles, but are not default
appliance boot requirements.

| Surface | Current role | Default policy |
| --- | --- | --- |
| Audio / ADSP / ACDB | Proven native speaker path, boot chime, demo audio. | Opt-in only. Use for alerts or demos, not base server boot. |
| GPU / KGSL direct | Proven graphics/research path and demos. | Opt-in only. The base HUD uses DRM/KMS dumb-buffer paths, not KGSL. |
| Video demos / Doom | Operator-facing demos and validation workloads. | Opt-in only. Never start during server boot. |
| Touch/game/keyboard input | Demo control surface. | Opt-in only. Server admin uses SSH/local USB. |
| CPU/GPU stress and longsoak | Diagnostics. | Opt-in only and bounded. |

If any opt-in mode needs a resource Debian owns, it must declare ownership and a
release path. Silent background ownership is not allowed.

## 5. Do Not Wake By Default

These are not part of the server appliance boot target.

| Surface | Policy |
| --- | --- |
| Modem/cellular stack | Do not wake by default. Forbidden modem-related partition writes remain absolute no-go. |
| Camera | Do not wake by default. |
| GNSS/location | Do not wake by default. |
| NFC/Bluetooth | Do not wake by default. |
| Sensor hubs | Do not wake by default unless a future explicit appliance feature requires them. |
| Android adbd/HAL services | Do not start as part of the appliance. Use native/debian admin paths. |

This list is about default activation, not source deletion. Recon tools may remain
in-tree for bounded, explicitly chartered investigations.

## 6. Ownership Matrix

| Resource | Pre-handoff owner | Post-handoff owner | Rule |
| --- | --- | --- | --- |
| `/dev/dri/card0` | Native HUD only while booting. | Debian HUD or no owner. | Native must release before `switch_root`. |
| USB ACM/NCM gadget | Kernel config from native init; native command helpers while active. | Kernel gadget persists; Debian may use NCM. | Must preserve recovery access. |
| `/dev/block/a90-userdata` | Native validates and mounts as target root. | Debian root filesystem. | Native stops touching it after `switch_root`. |
| `/dev/snd/*`, `/dev/msm_audio_cal` | Native only when audio opt-in runs. | Usually unowned. | No automatic audio route/gain changes. |
| `wlan0` | Native materializes vendor/qcacld surface. | Debian configures IP and services. | Wi-Fi STA rung must prove this boundary. |
| Public tunnel | None. | Debian service. | No public tunnel from native init. |

## 7. Implementation Consequences

Near-term work should not start by adding more hardware bring-up. It should first
make the contract observable:

1. Add a `server-distro hardware-contract` or equivalent status surface that
   prints which default, next-rung, opt-in, and denied surfaces are active.
2. Make D4/D-public handoff reports include the ownership matrix outcome:
   display released, USB control preserved, rootfs mounted, no native `/init`
   leftovers.
3. For Wi-Fi STA, build a separate bounded rung. Do not mix it with unrelated
   audio/GPU/demo work.
4. Keep default appliance boot small enough that a failed optional subsystem
   cannot block SSH/rootfs handoff.

## 8. Stop Conditions

Stop and report before device action if any proposed hardware activation requires:

- a forbidden partition write;
- a PMIC/regulator/GDSC/GPIO/backlight write;
- panel re-init outside the existing DRM/KMS path;
- committing credentials, tunnel URLs, or raw device identifiers;
- turning an opt-in demo into a default boot dependency without updating this
  contract.

## 9. Summary

Default Stage 0 is now: boot/control, USB gadget, guarded storage handoff,
optional native boot HUD with mandatory DRM release, and pre-handoff health logs.
The next real hardware frontier is Wi-Fi STA upstream. Audio, GPU, video, Doom,
input, stress, and other device demos remain explicit opt-in features.
