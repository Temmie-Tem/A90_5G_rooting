/*
 * a90_boot_audit.c — read-only boot-target auditor (§7.1).
 *
 * NO WRITE PATH. Everything here is O_RDONLY / read-only ioctls / sysfs reads. It exists to:
 *   (1) answer whether native-init (normal boot, PID1, under RKP) can open+read /dev/block/by-name/boot,
 *   (2) report the fd-derived identity the host-side boot-target guard needs to CONFIRM its pin
 *       (rdev major:minor, canonical path, size, logical/physical sector, PARTNAME, diskseq).
 *
 * Identity is taken from the OPENED fd (fstat st_rdev, BLKGETSIZE64) and from
 * /sys/dev/block/<maj>:<min>/ resolved from that rdev — matching the device-side contract the
 * eventual write command must honour. Output lines are "A90BOOTAUDIT key=value\r\n".
 */
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>
#include <linux/fs.h>

#include "a90_boot_audit.h"
#include "a90_console.h"
#include "a90_util.h"

#define BOOT_AUDIT_DEFAULT_TARGET "/dev/block/by-name/boot"

/* Extract PARTNAME=... from a sysfs uevent blob into out (lowercased trim left to the host guard). */
static void parse_partname(const char *uevent, char *out, size_t out_size) {
    out[0] = '\0';
    const char *p = uevent;
    while (p && *p) {
        if (strncmp(p, "PARTNAME=", 9) == 0) {
            p += 9;
            size_t i = 0;
            while (p[i] && p[i] != '\n' && p[i] != '\r' && i + 1 < out_size) {
                out[i] = p[i];
                i++;
            }
            out[i] = '\0';
            return;
        }
        const char *nl = strchr(p, '\n');
        if (!nl) {
            break;
        }
        p = nl + 1;
    }
}

int a90_boot_audit_cmd(char **argv, int argc) {
    const char *target = BOOT_AUDIT_DEFAULT_TARGET;
    if (argc > 2) {
        a90_console_printf("usage: boot-audit [target-path]\r\n");
        return -EINVAL;
    }
    if (argc == 2) {
        target = argv[1]; /* read-only inspection of any partition is permitted; no write happens */
    }

    a90_console_printf("A90BOOTAUDIT begin\r\n");
    a90_console_printf("A90BOOTAUDIT target=%s\r\n", target);

    /* Canonical path (resolve symlink for by-name entries). */
    char canonical[PATH_MAX];
    ssize_t clen = readlink(target, canonical, sizeof(canonical) - 1);
    if (clen >= 0) {
        canonical[clen] = '\0';
        a90_console_printf("A90BOOTAUDIT canonical=%s\r\n", canonical);
    } else {
        a90_console_printf("A90BOOTAUDIT canonical=%s (not-a-symlink errno=%d)\r\n", target, errno);
    }

    /* Open READ-ONLY. This is the §0.1 feasibility probe. */
    int fd = open(target, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        int e = errno;
        a90_console_printf("A90BOOTAUDIT open=fail errno=%d (%s)\r\n", e, strerror(e));
        a90_console_printf("A90BOOTAUDIT end rc=%d\r\n", -e);
        return -e;
    }
    a90_console_printf("A90BOOTAUDIT open=ok\r\n");

    struct stat st;
    if (fstat(fd, &st) == 0) {
        a90_console_printf("A90BOOTAUDIT is_block=%d\r\n", S_ISBLK(st.st_mode) ? 1 : 0);
        a90_console_printf("A90BOOTAUDIT rdev=%u:%u\r\n",
                           (unsigned)major(st.st_rdev), (unsigned)minor(st.st_rdev));
    } else {
        a90_console_printf("A90BOOTAUDIT fstat=fail errno=%d\r\n", errno);
        close(fd);
        a90_console_printf("A90BOOTAUDIT end rc=-1\r\n");
        return -EIO;
    }

    uint64_t size_bytes = 0;
    if (ioctl(fd, BLKGETSIZE64, &size_bytes) == 0) {
        a90_console_printf("A90BOOTAUDIT size_bytes=%llu\r\n", (unsigned long long)size_bytes);
    } else {
        a90_console_printf("A90BOOTAUDIT size_bytes=unknown errno=%d\r\n", errno);
    }

    int lbs = 0, pbs = 0;
    if (ioctl(fd, BLKSSZGET, &lbs) == 0) {
        a90_console_printf("A90BOOTAUDIT logical_sector=%d\r\n", lbs);
    }
    if (ioctl(fd, BLKPBSZGET, &pbs) == 0) {
        a90_console_printf("A90BOOTAUDIT physical_sector=%d\r\n", pbs);
    }

    /* sysfs facts resolved from the fd's rdev (not the path string). */
    char sysbase[128];
    snprintf(sysbase, sizeof(sysbase), "/sys/dev/block/%u:%u",
             (unsigned)major(st.st_rdev), (unsigned)minor(st.st_rdev));
    a90_console_printf("A90BOOTAUDIT sysfs=%s\r\n", sysbase);

    char path[192];
    char buf[4096];

    snprintf(path, sizeof(path), "%s/uevent", sysbase);
    if (read_text_file(path, buf, sizeof(buf)) >= 0) {
        char partname[64];
        parse_partname(buf, partname, sizeof(partname));
        a90_console_printf("A90BOOTAUDIT partname=%s\r\n", partname[0] ? partname : "unknown");
    } else {
        a90_console_printf("A90BOOTAUDIT partname=unreadable\r\n");
    }

    snprintf(path, sizeof(path), "%s/diskseq", sysbase);
    if (read_trimmed_text_file(path, buf, sizeof(buf)) >= 0 && buf[0]) {
        a90_console_printf("A90BOOTAUDIT diskseq=%s\r\n", buf);
    } else {
        a90_console_printf("A90BOOTAUDIT diskseq=absent\r\n");
    }

    snprintf(path, sizeof(path), "%s/size", sysbase);
    if (read_trimmed_text_file(path, buf, sizeof(buf)) >= 0 && buf[0]) {
        a90_console_printf("A90BOOTAUDIT sysfs_sectors=%s\r\n", buf);
    }

    close(fd);
    a90_console_printf("A90BOOTAUDIT end rc=0\r\n");
    return 0;
}
