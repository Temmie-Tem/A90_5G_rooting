/*
 * Native-init hot-reload command: replace PID1 in place via execve() without a reboot.
 * See a90_init_reload.h for the design and safety contract. This file contains exactly one
 * execve() and no other process-replacement primitive.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "a90_init_reload.h"
#include "a90_console.h"
#include "a90_helper.h"

extern char **environ;

#define A90_RELOAD_TAG "A90RELOAD"
#define A90_RELOAD_TOKEN "INIT-RELOAD-EXECVE"
#define A90_RELOAD_STAGE_ROOT "/mnt/sdext/a90/flash-staging/"

static int reload_hex64_valid(const char *s) {
    size_t n = 0;
    if (!s) {
        return 0;
    }
    for (; s[n]; n++) {
        char c = s[n];
        int ok = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
        if (!ok) {
            return 0;
        }
    }
    return n == 64;
}

static int reload_path_allowed(const char *p) {
    size_t root;
    if (!p) {
        return 0;
    }
    root = strlen(A90_RELOAD_STAGE_ROOT);
    if (strncmp(p, A90_RELOAD_STAGE_ROOT, root) != 0) {
        return 0;
    }
    if (p[root] == '\0') {
        return 0; /* need a basename after the approved root */
    }
    if (strstr(p, "..") != NULL) {
        return 0;
    }
    for (const char *c = p; *c; c++) {
        if (*c == '\n' || *c == '\r') {
            return 0;
        }
    }
    return 1;
}

static int reload_sha_equal_ci(const char *a, const char *b) {
    for (int i = 0; i < 64; i++) {
        char ca = a[i];
        char cb = b[i];
        if (ca >= 'A' && ca <= 'Z') {
            ca = (char)(ca + 32);
        }
        if (cb >= 'A' && cb <= 'Z') {
            cb = (char)(cb + 32);
        }
        if (ca != cb || ca == '\0') {
            return 0;
        }
    }
    return 1;
}

int a90_init_reload_cmd(char **argv, int argc) {
    const char *tag = A90_RELOAD_TAG;
    const char *path;
    const char *expected_sha;
    int fd;
    struct stat st;
    unsigned char magic[4];
    ssize_t rd;
    char actual[65];
    size_t nenv;
    size_t idx;
    char **newenv;
    char *newargv[3];
    int e;

    if (argc != 4 || strcmp(argv[1], A90_RELOAD_TOKEN) != 0) {
        a90_console_printf("usage: reload %s <staged-init-path> <expected-sha256>\r\n",
                           A90_RELOAD_TOKEN);
        a90_console_printf("%s refused=missing-or-wrong-token-or-argc argc=%d\r\n", tag, argc);
        return -EPERM;
    }
    path = argv[2];
    expected_sha = argv[3];

    if (!reload_path_allowed(path)) {
        a90_console_printf("%s refused=path-outside-approved-staging path=%s\r\n", tag, path);
        return -EPERM;
    }
    if (!reload_hex64_valid(expected_sha)) {
        a90_console_printf("%s refused=bad-expected-sha\r\n", tag);
        return -EINVAL;
    }

    a90_console_printf("%s begin path=%s\r\n", tag, path);

    fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) {
        e = errno;
        a90_console_printf("%s open=fail errno=%d (%s)\r\n", tag, e, strerror(e));
        return -e;
    }
    if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_size <= 0) {
        a90_console_printf("%s stop=not-regular-or-empty\r\n", tag);
        close(fd);
        return -EINVAL;
    }
    rd = pread(fd, magic, sizeof(magic), 0);
    if (rd != (ssize_t)sizeof(magic) || memcmp(magic, "\x7f" "ELF", 4) != 0) {
        a90_console_printf("%s elf_magic=absent stop=not-elf\r\n", tag);
        close(fd);
        return -EINVAL;
    }
    close(fd);
    a90_console_printf("%s candidate=ok size=%lld elf=1\r\n", tag, (long long)st.st_size);

    if (a90_helper_sha256_file(path, actual, sizeof(actual)) != 0) {
        a90_console_printf("%s sha=compute-fail\r\n", tag);
        return -EIO;
    }
    if (!reload_sha_equal_ci(actual, expected_sha)) {
        a90_console_printf("%s sha=%s expected_sha_match=0 stop=sha-mismatch\r\n", tag, actual);
        return -EPERM;
    }
    a90_console_printf("%s sha=%s expected_sha_match=1\r\n", tag, actual);

    /* Build a new environment that marks this as a hot-reload for a future fast-path in main(),
       preserving the current environment and de-duplicating any prior marker. */
    nenv = 0;
    for (char **ep = environ; ep && *ep; ep++) {
        nenv++;
    }
    newenv = (char **)malloc((nenv + 2) * sizeof(char *));
    if (!newenv) {
        a90_console_printf("%s envp=oom stop=oom\r\n", tag);
        return -ENOMEM;
    }
    idx = 0;
    for (char **ep = environ; ep && *ep; ep++) {
        if (strncmp(*ep, "A90_RELOADED=", 13) == 0) {
            continue;
        }
        newenv[idx++] = *ep;
    }
    newenv[idx++] = (char *)"A90_RELOADED=1";
    newenv[idx] = NULL;

    newargv[0] = (char *)path;
    newargv[1] = (char *)"--reloaded";
    newargv[2] = NULL;

    a90_console_printf("%s execve_now path=%s host_note=serial-persists-no-reboot\r\n", tag, path);
    /* Flush filesystems (SD/cache) and let the console drain over USB serial before the image is
       replaced. execve tears down all other threads (auto-hud etc.) itself. */
    sync();
    usleep(200000);

    execve(path, newargv, newenv);

    /* Only reached if execve failed: the old init image is intact and still running. Safe. */
    e = errno;
    free(newenv);
    a90_console_printf("%s execve=fail errno=%d (%s) old-init-continues\r\n", tag, e, strerror(e));
    return -e;
}
