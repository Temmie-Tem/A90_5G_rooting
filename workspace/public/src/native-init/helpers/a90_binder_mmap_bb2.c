#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#define DEFAULT_BINDER_PATH "/dev/binder"
#define DEFAULT_MAP_LENGTH (1024UL * 1024UL)
#define MAX_MAP_LENGTH (4UL * 1024UL * 1024UL)

static const char *decision_for_errno(int err) {
    switch (err) {
    case 0:
        return "bb2-mmap-ok";
    case EPERM:
        return "bb2-mmap-eperm-vmwrite";
    case EINVAL:
        return "bb2-mmap-einval-not-group-leader-or-flags";
    case EBUSY:
        return "bb2-mmap-ebusy";
    case ENOMEM:
        return "bb2-mmap-enomem";
    default:
        return "bb2-mmap-failed";
    }
}

static void usage(const char *program) {
    fprintf(stderr, "usage: %s [--path /dev/binder] [--length BYTES]\n", program);
}

static int parse_ulong(const char *text, unsigned long *out) {
    char *end = NULL;
    unsigned long value;

    errno = 0;
    value = strtoul(text, &end, 0);
    if (errno || end == text || *end != '\0') {
        return -1;
    }
    *out = value;
    return 0;
}

int main(int argc, char **argv) {
    const char *path = DEFAULT_BINDER_PATH;
    unsigned long map_length = DEFAULT_MAP_LENGTH;
    int fd = -1;
    int open_errno = 0;
    int mmap_errno = 0;
    int munmap_errno = 0;
    int close_errno = 0;
    int munmap_rc = 0;
    int close_rc = 0;
    void *mapping = MAP_FAILED;

    for (int index = 1; index < argc; index++) {
        if (strcmp(argv[index], "--path") == 0) {
            if (++index >= argc) {
                usage(argv[0]);
                return 2;
            }
            path = argv[index];
        } else if (strcmp(argv[index], "--length") == 0) {
            if (++index >= argc || parse_ulong(argv[index], &map_length) != 0) {
                usage(argv[0]);
                return 2;
            }
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    printf("bb2.helper=a90_binder_mmap_bb2\n");
    printf("bb2.helper_version=1\n");
    printf("bb2.path=%s\n", path);
    printf("bb2.map_length=%lu\n", map_length);
    printf("bb2.prot=PROT_READ\n");
    printf("bb2.flags=MAP_PRIVATE|MAP_NORESERVE\n");
    printf("bb2.no_ioctl=1\n");
    printf("bb2.no_transaction=1\n");
    printf("bb2.no_deref=1\n");

    if (map_length == 0 || map_length > MAX_MAP_LENGTH || (map_length % 4096UL) != 0) {
        printf("bb2.decision=bb2-helper-invalid-length\n");
        printf("bb2.exit_rc=2\n");
        return 2;
    }

    fd = open(path, O_RDWR | O_CLOEXEC);
    open_errno = (fd < 0) ? errno : 0;
    printf("bb2.open_rc=%d\n", fd < 0 ? -1 : 0);
    printf("bb2.open_errno=%d\n", open_errno);
    if (fd < 0) {
        printf("bb2.decision=bb2-open-fail\n");
        printf("bb2.exit_rc=3\n");
        return 3;
    }

    mapping = mmap(NULL, map_length, PROT_READ, MAP_PRIVATE | MAP_NORESERVE, fd, 0);
    mmap_errno = (mapping == MAP_FAILED) ? errno : 0;
    printf("bb2.mmap_rc=%d\n", mapping == MAP_FAILED ? -1 : 0);
    printf("bb2.mmap_errno=%d\n", mmap_errno);
    printf("bb2.mmap_addr=0x%llx\n",
           mapping == MAP_FAILED ? 0ULL : (unsigned long long)(uintptr_t)mapping);

    if (mapping != MAP_FAILED) {
        munmap_rc = munmap(mapping, map_length);
        munmap_errno = (munmap_rc != 0) ? errno : 0;
    }
    printf("bb2.munmap_rc=%d\n", mapping == MAP_FAILED ? 0 : munmap_rc);
    printf("bb2.munmap_errno=%d\n", munmap_errno);

    close_rc = close(fd);
    close_errno = (close_rc != 0) ? errno : 0;
    printf("bb2.close_rc=%d\n", close_rc);
    printf("bb2.close_errno=%d\n", close_errno);

    if (mapping == MAP_FAILED) {
        printf("bb2.decision=%s\n", decision_for_errno(mmap_errno));
        printf("bb2.exit_rc=4\n");
        return 4;
    }
    if (munmap_rc != 0 || close_rc != 0) {
        printf("bb2.decision=bb2-cleanup-failed\n");
        printf("bb2.exit_rc=5\n");
        return 5;
    }

    printf("bb2.decision=bb2-mmap-ok\n");
    printf("bb2.exit_rc=0\n");
    return 0;
}
