// SPDX-License-Identifier: MIT
/*
 * Samsung S22+ M20A raw reboot-download positive control.
 *
 * This is the post-M19 floor split's first live candidate.  It performs one
 * direct arm64 reboot(2) syscall requesting Samsung download mode as the first
 * runtime action, then parks if the syscall returns.
 */

    .section .rodata
    .balign 8
    .global s22plus_m20a_static_marker
s22plus_m20a_static_marker:
    .asciz "S22_NATIVE_INIT_M20A_RAW_REBOOT raw-pid1 no-libc first-action-reboot-download then-park"

    .balign 8
download_arg:
    .asciz "download"

    .section .text
    .balign 16
    .global _start
    .type _start, %function
_start:
    // reboot(LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
    //        LINUX_REBOOT_CMD_RESTART2, "download")
    movz    x0, #0xdead
    movk    x0, #0xfee1, lsl #16
    movz    x1, #0x1969
    movk    x1, #0x2812, lsl #16
    movz    x2, #0xc3d4
    movk    x2, #0xa1b2, lsl #16
    adrp    x3, download_arg
    add     x3, x3, :lo12:download_arg
    mov     x8, #142
    svc     #0

1:
    wfe
    b       1b
    .size _start, . - _start
