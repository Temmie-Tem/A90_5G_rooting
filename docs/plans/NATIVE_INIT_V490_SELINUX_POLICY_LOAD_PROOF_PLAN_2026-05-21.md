# Native Init V490 SELinux Policy Load Proof Plan

- Date: 2026-05-21 KST
- Scope: prepare a bounded SELinux policy-load proof after V489 compile success
- Status: implementation-ready; live `/sys/fs/selinux/load` execution requires a separate explicit approval
- Final Wi-Fi objective status: not achieved yet

## Background

V488 proved that the vendor precompiled policy is not directly usable with the currently mounted system/system_ext policy hashes. V489 then proved that native init can compile the Android split policy with `/system/bin/secilc` using kernel policy version `31` and vendor mapping version `30.0`.

The next Wi-Fi blocker is not compilation anymore. The next blocker is whether the compiled Android policy can be loaded into the kernel SELinux subsystem without immediately reexecing PID1 or starting Android daemons in the same step.

## Reference Model

Android `init` loads SELinux policy early in boot. AOSP documents that split policy is assembled from platform, system_ext/product, vendor, and optional ODM policy, then loaded into the kernel before `init` switches enforcement and reexecs itself.

References:

- AOSP init split-policy implementation: `https://android.googlesource.com/platform/system/core/+/master/init/selinux.cpp`
- AOSP SELinux build documentation: `https://source.android.com/docs/security/features/selinux/build`

## V490 Design

V490 adds `a90_android_execns_probe v48` with a new mode:

```text
--mode sepolicy-load-proof --allow-policy-load-proof
```

The mode:

1. Creates the same private namespace shape as V489.
2. Compiles split policy using the V489-proven `secilc` argument shape.
3. Keeps the compiled policy in the helper temp root.
4. Opens `/sys/fs/selinux/load`.
5. Reads the compiled policy blob into memory and writes it once to the SELinuxfs load file.
6. Captures pre/post current context, enforcing state, policy version, bytes, and hash.
7. Does not reexec PID1.
8. Does not start service-manager, hwservicemanager, CNSS, Wi-Fi HAL, supplicant, wificond, scan/connect, DHCP, routing, or external ping.

## Gates

V490 intentionally has two independent gates:

| gate | purpose |
|---|---|
| runner approval phrase | prevents accidental live policy load from host scripts |
| helper `--allow-policy-load-proof` | prevents accidental live policy load from direct helper invocation |

Required live runner phrase:

```text
approve v490 native SELinux policy-load proof only; no init reexec, no daemon start and no Wi-Fi bring-up
```

Required deploy phrase:

```text
approve v490 deploy execns helper v48 only; no policy load, no daemon start and no Wi-Fi bring-up
```

## Expected Evidence

If live V490 is approved and succeeds, the manifest should show:

```text
decision=v490-selinux-policy-load-proof-pass
sepolicy_load.policy_load_attempted=1
sepolicy_load.policy_load_executed=1
sepolicy_load.init_reexec_executed=0
sepolicy_load.daemon_start_executed=0
sepolicy_load.wifi_hal_start_executed=0
sepolicy_load.wifi_bringup_executed=0
```

If it fails, the failure is still useful if it captures:

- compile attempt result
- `/sys/fs/selinux/load` open/write errno
- pre/post context
- pre/post enforcing state
- post-run native status

## Risk Boundary

This step is a global kernel SELinux policy mutation. It has no in-place rollback contract. The practical rollback path remains rebooting back into the known-good native init state if the load causes policy side effects.

Because of that, V490 must not combine policy load with:

- PID1 reexec
- SELinux domain transition test
- service-manager start
- Wi-Fi HAL start
- Wi-Fi scan/connect

Those must remain separate steps after the load proof.

## Next Steps

1. Build and optionally deploy helper v48.
2. Run V490 preflight and confirm no Android manager/HAL/CNSS/Wi-Fi process is already active.
3. Only with explicit approval, run the policy-load proof.
4. If V490 passes, plan V491 as a post-load domain-transition proof.
5. If domain transition works, retry service-manager/HAL registration.
6. Continue toward scan/connect/link-up, DHCP/routing, and external ping.
