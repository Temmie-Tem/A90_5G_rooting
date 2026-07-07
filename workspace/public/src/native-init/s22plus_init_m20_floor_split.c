// SPDX-License-Identifier: MIT
/*
 * Samsung S22+ M20 floor-split native init.
 *
 * Compile-time variants:
 *   M20B: setup minimal dev/proc/sys/run, then reboot(download), no kmsg write.
 *   M20C: setup minimal dev/proc/sys/run, emit /dev/kmsg marker, then reboot.
 */

#include <stddef.h>
#include <stdint.h>

#ifndef M20_VARIANT_LABEL
#define M20_VARIANT_LABEL "M20_UNSET"
#endif

#ifndef M20_MARKER
#define M20_MARKER "S22_NATIVE_INIT_M20_UNSET"
#endif

#ifndef M20_ENABLE_KMSG
#define M20_ENABLE_KMSG 0
#endif

#define AT_FDCWD (-100)

#define O_WRONLY 00000001
#define O_CLOEXEC 02000000

#define S_IFCHR 0020000

#define MS_NOSUID 2UL
#define MS_NODEV 4UL
#define MS_NOEXEC 8UL

#define EBUSY 16

#define NR_MKNODAT 33
#define NR_MKDIRAT 34
#define NR_MOUNT 40
#define NR_OPENAT 56
#define NR_CLOSE 57
#define NR_WRITE 64
#define NR_NANOSLEEP 101
#define NR_REBOOT 142

#define LINUX_REBOOT_MAGIC1 0xfee1deadUL
#define LINUX_REBOOT_MAGIC2 0x28121969UL
#define LINUX_REBOOT_CMD_RESTART2 0xa1b2c3d4UL

struct timespec64 {
    int64_t tv_sec;
    int64_t tv_nsec;
};

struct sbuf {
    char data[512];
    size_t len;
};

__attribute__((used)) static const char k_static_marker[] =
    M20_MARKER " version=0.1 variant=" M20_VARIANT_LABEL
    " runtime=freestanding raw_syscalls=1 minfs=dev,proc,sys,run "
#if M20_ENABLE_KMSG
    "kmsg_emit=1 "
#else
    "kmsg_emit=0 "
#endif
    "no_modules=1 no_configfs=1 no_usb_acm=1 no_gadget_setup=1 "
    "reboot_request=download no_android_handoff=1";

static inline long syscall6(long nr, long a0, long a1, long a2, long a3, long a4, long a5) {
    register long x0 asm("x0") = a0;
    register long x1 asm("x1") = a1;
    register long x2 asm("x2") = a2;
    register long x3 asm("x3") = a3;
    register long x4 asm("x4") = a4;
    register long x5 asm("x5") = a5;
    register long x8 asm("x8") = nr;
    asm volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5), "r"(x8) : "memory");
    return x0;
}

static inline long syscall5(long nr, long a0, long a1, long a2, long a3, long a4) {
    return syscall6(nr, a0, a1, a2, a3, a4, 0);
}

static inline long syscall4(long nr, long a0, long a1, long a2, long a3) {
    return syscall6(nr, a0, a1, a2, a3, 0, 0);
}

static inline long syscall3(long nr, long a0, long a1, long a2) {
    return syscall6(nr, a0, a1, a2, 0, 0, 0);
}

static inline long syscall2(long nr, long a0, long a1) {
    return syscall6(nr, a0, a1, 0, 0, 0, 0);
}

static long sys_mkdirat(const char *path, unsigned int mode) {
    return syscall3(NR_MKDIRAT, AT_FDCWD, (long)(uintptr_t)path, mode);
}

static long sys_mknodat(const char *path, unsigned int mode, uint64_t dev) {
    return syscall4(NR_MKNODAT, AT_FDCWD, (long)(uintptr_t)path, mode, (long)dev);
}

static long sys_mount(const char *source, const char *target, const char *fstype, unsigned long flags, const char *data) {
    return syscall5(
        NR_MOUNT,
        (long)(uintptr_t)source,
        (long)(uintptr_t)target,
        (long)(uintptr_t)fstype,
        (long)flags,
        (long)(uintptr_t)data);
}

static long sys_sleep_ms(long ms) {
    struct timespec64 req = {
        .tv_sec = ms / 1000,
        .tv_nsec = (ms % 1000) * 1000000,
    };
    return syscall2(NR_NANOSLEEP, (long)(uintptr_t)&req, 0);
}

static long sys_reboot_download(void) {
    return syscall4(
        NR_REBOOT,
        (long)LINUX_REBOOT_MAGIC1,
        (long)LINUX_REBOOT_MAGIC2,
        (long)LINUX_REBOOT_CMD_RESTART2,
        (long)(uintptr_t)"download");
}

static size_t cstr_len(const char *s) {
    size_t n = 0;
    while (s[n] != '\0') {
        ++n;
    }
    return n;
}

void *memcpy(void *dst, const void *src, size_t n) {
    unsigned char *d = (unsigned char *)dst;
    const unsigned char *s = (const unsigned char *)src;
    for (size_t i = 0; i < n; ++i) {
        d[i] = s[i];
    }
    return dst;
}

void *memset(void *dst, int value, size_t n) {
    unsigned char *d = (unsigned char *)dst;
    for (size_t i = 0; i < n; ++i) {
        d[i] = (unsigned char)value;
    }
    return dst;
}

static void copy_cstr(char *dst, size_t size, const char *src) {
    if (size == 0) {
        return;
    }
    size_t i = 0;
    while (i + 1 < size && src[i] != '\0') {
        dst[i] = src[i];
        ++i;
    }
    dst[i] = '\0';
}

static void mkdir_one(const char *path, unsigned int mode) {
    (void)sys_mkdirat(path, mode);
}

static void mkdir_p(const char *path, unsigned int mode) {
    char tmp[128];
    size_t len = cstr_len(path);
    if (len == 0 || len >= sizeof(tmp)) {
        return;
    }
    copy_cstr(tmp, sizeof(tmp), path);
    for (size_t i = 1; tmp[i] != '\0'; ++i) {
        if (tmp[i] == '/') {
            tmp[i] = '\0';
            mkdir_one(tmp, mode);
            tmp[i] = '/';
        }
    }
    mkdir_one(tmp, mode);
}

static uint64_t make_dev(unsigned int major_num, unsigned int minor_num) {
    return ((uint64_t)(minor_num & 0xffU)) | ((uint64_t)(major_num & 0xfffU) << 8) |
           ((uint64_t)(minor_num & ~0xffU) << 12) | ((uint64_t)(major_num & ~0xfffU) << 32);
}

static void ensure_chr_node(const char *path, unsigned int mode, unsigned int major_num, unsigned int minor_num) {
    (void)sys_mknodat(path, S_IFCHR | mode, make_dev(major_num, minor_num));
}

static long mount_one(const char *source, const char *target, const char *fstype, unsigned long flags, const char *data) {
    long rc = sys_mount(source, target, fstype, flags, data);
    if (rc == -EBUSY) {
        return 0;
    }
    return rc;
}

#if M20_ENABLE_KMSG
static long sys_openat(int dirfd, const char *path, int flags, unsigned int mode) {
    return syscall4(NR_OPENAT, dirfd, (long)(uintptr_t)path, flags, mode);
}

static long sys_close(int fd) {
    return syscall2(NR_CLOSE, fd, 0);
}

static long sys_write(int fd, const void *buf, size_t count) {
    return syscall3(NR_WRITE, fd, (long)(uintptr_t)buf, (long)count);
}

static void sb_putc(struct sbuf *sb, char ch) {
    if (sb->len + 1 < sizeof(sb->data)) {
        sb->data[sb->len++] = ch;
        sb->data[sb->len] = '\0';
    }
}

static void sb_puts(struct sbuf *sb, const char *s) {
    for (size_t i = 0; s[i] != '\0'; ++i) {
        sb_putc(sb, s[i]);
    }
}

static void emit_buf(const struct sbuf *sb) {
    long fd = sys_openat(AT_FDCWD, "/dev/kmsg", O_WRONLY | O_CLOEXEC, 0);
    if (fd >= 0) {
        (void)sys_write((int)fd, sb->data, sb->len);
        (void)sys_close((int)fd);
    }
}

static void emit_marker(void) {
    struct sbuf sb = {.data = {0}, .len = 0};
    sb_puts(&sb, M20_MARKER " phase=kmsg variant=" M20_VARIANT_LABEL " requested=1\n");
    emit_buf(&sb);
}
#endif

static void setup_minimal_fs(void) {
    mkdir_p("/dev", 0755);
    mkdir_p("/proc", 0755);
    mkdir_p("/sys", 0755);
    mkdir_p("/run", 0755);

    long dev_rc = mount_one("devtmpfs", "/dev", "devtmpfs", MS_NOSUID, "mode=0755");
    if (dev_rc != 0) {
        (void)mount_one("tmpfs", "/dev", "tmpfs", MS_NOSUID, "mode=0755");
    }
    ensure_chr_node("/dev/console", 0600, 5, 1);
    ensure_chr_node("/dev/null", 0666, 1, 3);
    ensure_chr_node("/dev/zero", 0666, 1, 5);
#if M20_ENABLE_KMSG
    ensure_chr_node("/dev/kmsg", 0600, 1, 11);
#endif

    (void)mount_one("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, "");
    (void)mount_one("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, "");
    (void)mount_one("tmpfs", "/run", "tmpfs", MS_NOSUID | MS_NODEV, "mode=0755");
}

__attribute__((noreturn)) void _start(void) {
    setup_minimal_fs();
#if M20_ENABLE_KMSG
    emit_marker();
#endif
    (void)sys_sleep_ms(250);
    (void)sys_reboot_download();
    for (;;) {
        asm volatile("wfe" ::: "memory");
    }
}
