// SPDX-License-Identifier: MIT
/*
 * Samsung S22+ Magisk-preserving first-stage init proof wrapper.
 *
 * Installed as /init in the Magisk-patched boot ramdisk with Magisk's original
 * /init moved to /init.magisk.  The wrapper emits a kmsg proof marker, restores
 * /init.magisk back to /init inside the ephemeral initramfs, then execs /init so
 * magiskinit still observes the path layout it expects.
 */

#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/types.h>
#include <unistd.h>

static const char k_marker[] =
    "S22_NATIVE_INIT_MAGISK_CHAINLOAD version=0.1 restore=/init.magisk->/init "
    "action=exec proof=kmsg-rooted-android-dmesg\n";

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

static void ensure_kmsg_node(void) {
    struct stat st;
    if (stat("/dev/kmsg", &st) == 0 && S_ISCHR(st.st_mode)) {
        return;
    }
    (void)mknod("/dev/kmsg", S_IFCHR | 0600, makedev(1, 11));
}

static void write_kmsg(const char *msg) {
    ensure_kmsg_node();
    int fd = open("/dev/kmsg", O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        return;
    }
    write_all(fd, msg, strlen(msg));
    close(fd);
}

static void write_marker_file(const char *path) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (fd < 0) {
        return;
    }
    write_all(fd, k_marker, sizeof(k_marker) - 1);
    fsync(fd);
    close(fd);
}

static int restore_magisk_init_path(void) {
    if (rename("/init", "/init.s22-wrapper") != 0) {
        write_kmsg("S22_NATIVE_INIT_MAGISK_CHAINLOAD rename_wrapper_failed\n");
        return -1;
    }
    if (rename("/init.magisk", "/init") != 0) {
        write_kmsg("S22_NATIVE_INIT_MAGISK_CHAINLOAD rename_magisk_failed\n");
        (void)rename("/init.s22-wrapper", "/init");
        return -1;
    }
    write_kmsg("S22_NATIVE_INIT_MAGISK_CHAINLOAD restored_init_path\n");
    return 0;
}

static char *k_fallback_argv[] = {"/init", NULL};

int main(int argc, char **argv, char **envp) {
    (void)argc;

    write_kmsg(k_marker);
    write_marker_file("/s22_native_init_magisk_chainload_ran");
    write_marker_file("/debug_ramdisk/s22_native_init_magisk_chainload_ran");

    if (argv == NULL || argv[0] == NULL) {
        argv = k_fallback_argv;
    }
    argv[0] = "/init";

    if (restore_magisk_init_path() == 0) {
        execve("/init", argv, envp);
    }

    execve("/init.magisk", argv, envp);

    write_kmsg("S22_NATIVE_INIT_MAGISK_CHAINLOAD exec_failed\n");
    for (;;) {
        pause();
    }
}
