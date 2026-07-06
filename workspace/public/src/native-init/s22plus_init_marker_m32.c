// SPDX-License-Identifier: MIT
/*
 * S22+ M3.2 marker-only direct PID1 probe.
 *
 * M3.2 keeps M3.1's syscall-only behavior.  The build changes the boot ramdisk
 * packaging back to the stock legacy-LZ4 format, so the live question is not
 * confounded by the previous uncompressed-newc ramdisk format.
 */

#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <linux/reboot.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/types.h>
#include <unistd.h>

static const char k_marker[] =
    "S22_NATIVE_INIT_MARKER_ONLY_M32 version=0.2 pid1=direct "
    "proof=earliest-kmsg-pmsg ramdisk_format=legacy-lz4 fallback_pmsg_major=507 "
    "no_usb_modules=1 no_configfs=1 download_reboot_after_sec=10 park_on_reboot_return=1 "
    "no_android_handoff=1\n";

static void write_all(int fd, const char *buf, size_t len) {
    while (len > 0) {
        ssize_t rc = write(fd, buf, len);
        if (rc < 0) {
            if (errno == EINTR) {
                continue;
            }
            return;
        }
        if (rc == 0) {
            return;
        }
        buf += (size_t)rc;
        len -= (size_t)rc;
    }
}

static void mkdir_best_effort(const char *path, mode_t mode) {
    if (mkdir(path, mode) != 0 && errno == ENOENT) {
        return;
    }
}

static void ensure_chr_node(const char *path, mode_t mode, unsigned int major_num, unsigned int minor_num) {
    struct stat st;
    if (stat(path, &st) == 0 && S_ISCHR(st.st_mode)) {
        return;
    }
    if (errno == ENOENT) {
        (void)mknod(path, S_IFCHR | mode, makedev(major_num, minor_num));
    }
}

static void setup_early_nodes(void) {
    mkdir_best_effort("/dev", 0755);
    ensure_chr_node("/dev/kmsg", 0600, 1, 11);
    ensure_chr_node("/dev/pmsg0", 0222, 507, 0);
}

static void write_kmsg(const char *msg) {
    int fd = open("/dev/kmsg", O_WRONLY | O_CLOEXEC);
    if (fd >= 0) {
        write_all(fd, msg, strlen(msg));
        close(fd);
    }
}

static void write_pmsg(const char *msg) {
    int fd = open("/dev/pmsg0", O_WRONLY | O_CLOEXEC);
    if (fd >= 0) {
        write_all(fd, msg, strlen(msg));
        close(fd);
    }
}

static void emit(const char *msg) {
    write_kmsg(msg);
    write_pmsg(msg);
}

static void emitf(const char *fmt, ...) {
    char buf[384];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    if (n <= 0) {
        return;
    }
    if ((size_t)n >= sizeof(buf)) {
        n = (int)sizeof(buf) - 1;
        buf[n] = '\0';
    }
    emit(buf);
}

static void download_reboot_or_park(void) {
    emit("S22_NATIVE_INIT_MARKER_ONLY_M32 phase=download_reboot_attempt target=download\n");
    sync();
    errno = 0;
    long rc = syscall(
        SYS_reboot,
        LINUX_REBOOT_MAGIC1,
        LINUX_REBOOT_MAGIC2,
        LINUX_REBOOT_CMD_RESTART2,
        "download");
    emitf("S22_NATIVE_INIT_MARKER_ONLY_M32 phase=download_reboot_return rc=%ld errno=%d\n", rc, errno);

    for (unsigned int tick = 0;; ++tick) {
        emitf("S22_NATIVE_INIT_MARKER_ONLY_M32 phase=park download_reboot_failed=1 tick=%u\n", tick);
        sleep(10);
    }
}

int main(int argc, char **argv, char **envp) {
    (void)argc;
    (void)argv;
    (void)envp;

    setup_early_nodes();
    emit(k_marker);

    for (unsigned int tick = 0; tick < 10; ++tick) {
        emitf("S22_NATIVE_INIT_MARKER_ONLY_M32 phase=heartbeat tick=%u\n", tick);
        sleep(1);
    }

    download_reboot_or_park();
}
