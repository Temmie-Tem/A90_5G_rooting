# Native Init V1711 CNSS WLFW Start Prologue Static Classifier

## Summary

- Cycle: `V1711`
- Type: host-only `cnss-daemon` `wlfw_start@0xec00..0xec58` prologue classifier
- Decision: `v1711-wlfw-start-prologue-static-map-pass`
- Result: `PASS`
- Reason: V1710 proves wlfw_start entry but no first pthread init call; static prologue map identifies adjacent targets before 0xec58
- Evidence: `tmp/wifi/v1711-cnss-wlfw-start-prologue-static`

## Basis

- V1706 decision: `v1706-wlfw-start-branch-static-map-pass` pass `True`
- V1710 decision: `v1710-wlfw-start-pthread-create-not-reached-rollback-pass` pass `True` rollback `True`
- V1710 label: `wlfw-start-pthread-create-not-reached`
- V1710 hits: `wlfw_start=1`, `cal_mutex_call=0`
- Legacy firmware-serve label: `firmware-not-requested`

## Prologue Map

| Target | Offset | Instruction | Meaning |
| --- | --- | --- | --- |
| `wlfw_start_entry` | `0xec00` | `stp x29, x30, [sp, #-32]!` | function entry; V1705/V1708/V1710 prove this target is reachable |
| `wlfw_start_log_arg_severity` | `0xec20` | `mov w0, #0x2` | sets severity for the unconditional Starting log call |
| `wlfw_start_log_call` | `0xec24` | `bl 0xa21c` | unconditional log wrapper call before any pthread init |
| `wlfw_start_post_log_branch` | `0xec28` | `cbnz w19, 0xec48` | first proof that the unconditional log call returned |
| `wlfw_start_optional_pm_init1_call` | `0xec34` | `bl 0xc39c` | optional setup call when wlfw_start argument is zero |
| `wlfw_start_optional_pm_init1_return` | `0xec38` | `adrp x1, 0x6000` | optional setup call 1 returned |
| `wlfw_start_optional_pm_init2_call` | `0xec44` | `bl 0xc39c` | optional setup call 2 when wlfw_start argument is zero |
| `wlfw_start_common_state_base` | `0xec48` | `adrp x20, 0x21000` | common path after log/optional setup; first target before mutex state setup |
| `wlfw_start_cal_mutex_arg` | `0xec50` | `add x0, x20, #0x148` | builds cal_mutex pointer immediately before pthread_mutex_init |
| `wlfw_start_cal_mutex_call` | `0xec58` | `bl pthread_mutex_init@plt` | first pre-DMS pthread init call; V1710 proves this did not hit |

## Pattern Checks

| Pattern | Present |
| --- | --- |
| `entry` | `True` |
| `save_regs` | `True` |
| `arg_save` | `True` |
| `log_severity` | `True` |
| `log_call` | `True` |
| `post_log_branch` | `True` |
| `optional_pm_init1_call` | `True` |
| `optional_pm_init1_return` | `True` |
| `optional_pm_init2_call` | `True` |
| `common_state_base` | `True` |
| `cal_mutex_arg` | `True` |
| `cal_mutex_call` | `True` |

## Disassembly

```
    ec00:	a9be7bfd 	stp	x29, x30, [sp, #-32]!
    ec04:	a9014ff4 	stp	x20, x19, [sp, #16]
    ec08:	910003fd 	mov	x29, sp
    ec0c:	f0ffffa1 	adrp	x1, 5000 <__libc_init@plt-0xee30>
    ec10:	f0ffffa2 	adrp	x2, 5000 <__libc_init@plt-0xee30>
    ec14:	2a0003f3 	mov	w19, w0
    ec18:	913e5821 	add	x1, x1, #0xf96
    ec1c:	912ae442 	add	x2, x2, #0xab9
    ec20:	52800040 	mov	w0, #0x2                   	// #2
    ec24:	97ffed7e 	bl	a21c <__libc_init@plt-0x9c14>
    ec28:	35000113 	cbnz	w19, ec48 <__libc_init@plt-0x51e8>
    ec2c:	52800020 	mov	w0, #0x1                   	// #1
    ec30:	aa1f03e1 	mov	x1, xzr
    ec34:	97fff5da 	bl	c39c <__libc_init@plt-0x7a94>
    ec38:	90ffffc1 	adrp	x1, 6000 <__libc_init@plt-0xde30>
    ec3c:	91335021 	add	x1, x1, #0xcd4
    ec40:	2a1f03e0 	mov	w0, wzr
    ec44:	97fff5d6 	bl	c39c <__libc_init@plt-0x7a94>
    ec48:	f0000094 	adrp	x20, 21000 <android_set_abort_message@plt+0xc900>
    ec4c:	9126c294 	add	x20, x20, #0x9b0
    ec50:	91052280 	add	x0, x20, #0x148
    ec54:	aa1f03e1 	mov	x1, xzr
    ec58:	940015ea 	bl	14400 <pthread_mutex_init@plt>
    ec5c:	340000a0 	cbz	w0, ec70 <__libc_init@plt-0x51c0>
```

## Interpretation

- V1710 proves `wlfw_start@0xec00` is reached but `pthread_mutex_init@0xec58` is not reached.
- The only static instructions between those points are the unconditional log call at `0xec24`, an optional two-call setup path when the argument is zero, and the common state-base setup at `0xec48..0xec54`.
- Therefore the next live discriminator should trace adjacent prologue targets, especially `0xec24`, `0xec28`, `0xec48`, `0xec50`, and `0xec58`.
- Do not expand to WLFW QMI, BDF, MSA, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, or external ping until this prologue gap is resolved.

## Next Gate

- Type: source/build-only helper expansion followed by one rollbackable adjacent-prologue uprobe live run.
- Route: reuse V1710 internal-modem firmware-serve route only.
- Labels: `wlfw-start-log-call-no-return`, `wlfw-start-common-path-not-reached`, `wlfw-start-common-path-no-cal-mutex-arg`, `wlfw-start-cal-mutex-edge-no-call`, `wlfw-start-cal-mutex-call-reached`, `cnss-target-unavailable`.
- Forbidden: PM/service-window actors, `boot_wlan`, `/dev/subsys_esoc0`, forced RC1, fake-ONLINE, PMIC/GPIO/GDSC writes, eSoC notify/BOOT_DONE, PCI rescan, platform bind/unbind, Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping.
