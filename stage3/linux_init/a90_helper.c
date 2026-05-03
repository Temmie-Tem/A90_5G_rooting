#include "a90_helper.h"

#include "a90_config.h"
#include "a90_console.h"
#include "a90_log.h"
#include "a90_runtime.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static struct a90_helper_entry helper_entries[A90_HELPER_MAX_ENTRIES];
static int helper_count;
static int helper_warn_count;
static int helper_fail_count;
static bool helper_scanned;
static bool helper_manifest_present;
static char helper_manifest_path[PATH_MAX];
static char helper_summary_text[192];

static void helper_join(char *out, size_t out_size, const char *root, const char *name) {
    size_t used;

    if (out_size == 0) {
        return;
    }
    out[0] = '\0';
    if (root == NULL || name == NULL) {
        return;
    }
    snprintf(out, out_size, "%s", root);
    out[out_size - 1] = '\0';
    used = strlen(out);
    if (used + 1 < out_size) {
        out[used++] = '/';
        out[used] = '\0';
    }
    if (used < out_size) {
        strncat(out, name, out_size - used - 1);
    }
}

static bool helper_stat_regular(const char *path,
                                unsigned int *mode_out,
                                long long *size_out) {
    struct stat st;

    if (path == NULL || path[0] == '\0' || stat(path, &st) < 0) {
        return false;
    }
    if (!S_ISREG(st.st_mode)) {
        return false;
    }
    if (mode_out != NULL) {
        *mode_out = (unsigned int)(st.st_mode & 0777);
    }
    if (size_out != NULL) {
        *size_out = (long long)st.st_size;
    }
    return true;
}

static bool helper_is_executable(const char *path) {
    unsigned int mode = 0;

    if (!helper_stat_regular(path, &mode, NULL)) {
        return false;
    }
    return (mode & 0111) != 0;
}

static struct a90_helper_entry *helper_add(const char *name,
                                           const char *role,
                                           const char *fallback) {
    struct a90_runtime_status runtime;
    struct a90_helper_entry *entry;

    if (helper_count >= A90_HELPER_MAX_ENTRIES ||
        name == NULL ||
        name[0] == '\0') {
        return NULL;
    }
    entry = &helper_entries[helper_count++];
    memset(entry, 0, sizeof(*entry));
    snprintf(entry->name, sizeof(entry->name), "%s", name);
    snprintf(entry->role, sizeof(entry->role), "%s", role != NULL ? role : "helper");
    if (fallback != NULL) {
        snprintf(entry->fallback, sizeof(entry->fallback), "%s", fallback);
    }
    if (a90_runtime_get_status(&runtime) == 0 && runtime.bin[0] != '\0') {
        helper_join(entry->path, sizeof(entry->path), runtime.bin, name);
    } else {
        snprintf(entry->path, sizeof(entry->path), "%s/%s", A90_RUNTIME_CACHE_ROOT, name);
    }
    entry->expected_mode = 0755;
    entry->expected_size = 0;
    return entry;
}

static struct a90_helper_entry *helper_find_mutable(const char *name) {
    int index;

    if (name == NULL) {
        return NULL;
    }
    for (index = 0; index < helper_count; ++index) {
        if (strcmp(helper_entries[index].name, name) == 0) {
            return &helper_entries[index];
        }
    }
    return NULL;
}

static void helper_add_defaults(void) {
    (void)helper_add("a90_cpustress", "ramdisk-mirror", CPUSTRESS_HELPER);
    (void)helper_add("a90_usbnet", "net-helper", NETSERVICE_USB_HELPER);
    (void)helper_add("a90_tcpctl", "tcp-control", NETSERVICE_TCPCTL_HELPER);
    (void)helper_add("a90_rshell", "remote-shell", A90_RSHELL_RAMDISK_HELPER);
    (void)helper_add("busybox", "userland", A90_BUSYBOX_HELPER);
    (void)helper_add("toybox", "userland", NETSERVICE_TOYBOX);
    (void)helper_add("a90sleep", "test-helper", A90_SLEEP_HELPER);
}

static void helper_set_manifest_path(void) {
    struct a90_runtime_status runtime;

    helper_manifest_path[0] = '\0';
    if (a90_runtime_get_status(&runtime) == 0 && runtime.pkg[0] != '\0') {
        helper_join(helper_manifest_path,
                    sizeof(helper_manifest_path),
                    runtime.pkg,
                    A90_HELPER_MANIFEST_NAME);
    } else {
        snprintf(helper_manifest_path,
                 sizeof(helper_manifest_path),
                 "%s/%s/%s",
                 A90_RUNTIME_CACHE_ROOT,
                 A90_RUNTIME_PKG_DIR,
                 A90_HELPER_MANIFEST_NAME);
    }
}

static void helper_apply_manifest_line(char *line) {
    char name[64];
    char path[PATH_MAX];
    char role[64];
    char required[16];
    char sha[65];
    char mode_text[32];
    char size_text[32];
    struct a90_helper_entry *entry;
    char *cursor = line;
    int fields;

    while (*cursor == ' ' || *cursor == '\t') {
        ++cursor;
    }
    if (*cursor == '\0' || *cursor == '#') {
        return;
    }

    memset(name, 0, sizeof(name));
    memset(path, 0, sizeof(path));
    memset(role, 0, sizeof(role));
    memset(required, 0, sizeof(required));
    memset(sha, 0, sizeof(sha));
    memset(mode_text, 0, sizeof(mode_text));
    memset(size_text, 0, sizeof(size_text));

    fields = sscanf(cursor,
                    "%63s %4095s %63s %15s %64s %31s %31s",
                    name,
                    path,
                    role,
                    required,
                    sha,
                    mode_text,
                    size_text);
    if (fields < 2) {
        return;
    }

    entry = helper_find_mutable(name);
    if (entry == NULL) {
        entry = helper_add(name, fields >= 3 ? role : "manifest", NULL);
    }
    if (entry == NULL) {
        return;
    }

    snprintf(entry->path, sizeof(entry->path), "%s", path);
    if (fields >= 3 && role[0] != '\0') {
        snprintf(entry->role, sizeof(entry->role), "%s", role);
    }
    if (fields >= 4) {
        entry->required = strcmp(required, "yes") == 0 ||
                          strcmp(required, "required") == 0 ||
                          strcmp(required, "1") == 0;
    }
    if (fields >= 5 && strcmp(sha, "-") != 0 && strcmp(sha, "none") != 0) {
        snprintf(entry->expected_sha256, sizeof(entry->expected_sha256), "%s", sha);
    }
    if (fields >= 6 && mode_text[0] != '\0' && strcmp(mode_text, "-") != 0) {
        entry->expected_mode = (unsigned int)strtoul(mode_text, NULL, 8);
    }
    if (fields >= 7 && size_text[0] != '\0' && strcmp(size_text, "-") != 0) {
        entry->expected_size = strtoll(size_text, NULL, 10);
    }
    entry->manifest_entry = true;
}

static void helper_load_manifest(void) {
    FILE *fp;
    char line[640];

    helper_manifest_present = false;
    fp = fopen(helper_manifest_path, "r");
    if (fp == NULL) {
        return;
    }
    helper_manifest_present = true;
    while (fgets(line, sizeof(line), fp) != NULL) {
        char *newline = strchr(line, '\n');

        if (newline != NULL) {
            *newline = '\0';
        }
        helper_apply_manifest_line(line);
    }
    fclose(fp);
}

static void helper_finalize_entry(struct a90_helper_entry *entry) {
    unsigned int mode = 0;
    long long size = 0;
    bool mode_bad = false;
    bool size_bad = false;

    entry->present = helper_stat_regular(entry->path, &mode, &size);
    entry->actual_mode = entry->present ? mode : 0;
    entry->actual_size = entry->present ? size : 0;
    entry->executable = entry->present && ((mode & 0111) != 0);
    entry->fallback_present = helper_is_executable(entry->fallback);
    entry->hash_checked = false;
    entry->hash_match = entry->expected_sha256[0] == '\0';
    snprintf(entry->actual_sha256,
             sizeof(entry->actual_sha256),
             "%s",
             entry->expected_sha256[0] != '\0' ? "unchecked" : "-");

    if (entry->executable) {
        snprintf(entry->preferred, sizeof(entry->preferred), "%s", entry->path);
    } else if (entry->fallback_present) {
        snprintf(entry->preferred, sizeof(entry->preferred), "%s", entry->fallback);
    } else {
        entry->preferred[0] = '\0';
    }

    if (entry->present && entry->expected_mode != 0 &&
        entry->actual_mode != entry->expected_mode) {
        mode_bad = true;
    }
    if (entry->present && entry->expected_size > 0 &&
        entry->actual_size != entry->expected_size) {
        size_bad = true;
    }

    if (entry->required && !entry->executable) {
        snprintf(entry->warning, sizeof(entry->warning), "required helper missing or not executable");
        ++helper_fail_count;
        return;
    }
    if (mode_bad) {
        snprintf(entry->warning,
                 sizeof(entry->warning),
                 "mode mismatch expected=%04o actual=%04o",
                 entry->expected_mode,
                 entry->actual_mode);
        ++helper_warn_count;
        return;
    }
    if (size_bad) {
        snprintf(entry->warning,
                 sizeof(entry->warning),
                 "size mismatch expected=%lld actual=%lld",
                 entry->expected_size,
                 entry->actual_size);
        ++helper_warn_count;
        return;
    }
    if (entry->manifest_entry && entry->expected_sha256[0] != '\0') {
        snprintf(entry->warning,
                 sizeof(entry->warning),
                 "sha256 present but device-side hash unchecked");
        ++helper_warn_count;
    }
}

int a90_helper_scan(void) {
    int index;

    memset(helper_entries, 0, sizeof(helper_entries));
    helper_count = 0;
    helper_warn_count = 0;
    helper_fail_count = 0;
    helper_scanned = true;
    helper_add_defaults();
    helper_set_manifest_path();
    helper_load_manifest();

    for (index = 0; index < helper_count; ++index) {
        helper_finalize_entry(&helper_entries[index]);
    }

    snprintf(helper_summary_text,
             sizeof(helper_summary_text),
             "helpers: entries=%d warn=%d fail=%d manifest=%s path=%s",
             helper_count,
             helper_warn_count,
             helper_fail_count,
             helper_manifest_present ? "yes" : "no",
             helper_manifest_path[0] != '\0' ? "set" : "none");
    a90_logf("helper", "%s", helper_summary_text);
    return helper_fail_count > 0 ? -EIO : 0;
}

static void helper_scan_if_needed(void) {
    if (!helper_scanned) {
        (void)a90_helper_scan();
    }
}

int a90_helper_count(void) {
    helper_scan_if_needed();
    return helper_count;
}

int a90_helper_entry_at(int index, struct a90_helper_entry *out) {
    helper_scan_if_needed();
    if (out == NULL || index < 0 || index >= helper_count) {
        errno = EINVAL;
        return -EINVAL;
    }
    *out = helper_entries[index];
    return 0;
}

int a90_helper_find(const char *name, struct a90_helper_entry *out) {
    int index;

    helper_scan_if_needed();
    if (name == NULL || out == NULL) {
        errno = EINVAL;
        return -EINVAL;
    }
    for (index = 0; index < helper_count; ++index) {
        if (strcmp(helper_entries[index].name, name) == 0) {
            *out = helper_entries[index];
            return 0;
        }
    }
    errno = ENOENT;
    return -ENOENT;
}

const char *a90_helper_manifest_path(void) {
    helper_scan_if_needed();
    return helper_manifest_path;
}

const char *a90_helper_preferred_path(const char *name, const char *fallback) {
    static char selected[PATH_MAX];
    struct a90_helper_entry entry;

    if (a90_helper_find(name, &entry) == 0 && entry.preferred[0] != '\0') {
        snprintf(selected, sizeof(selected), "%s", entry.preferred);
        return selected;
    }
    snprintf(selected, sizeof(selected), "%s", fallback != NULL ? fallback : "");
    return selected;
}

void a90_helper_summary(char *out, size_t out_size) {
    helper_scan_if_needed();
    if (out == NULL || out_size == 0) {
        return;
    }
    snprintf(out,
             out_size,
             "entries=%d warn=%d fail=%d manifest=%s",
             helper_count,
             helper_warn_count,
             helper_fail_count,
             helper_manifest_present ? "yes" : "no");
}

bool a90_helper_has_failures(void) {
    helper_scan_if_needed();
    return helper_fail_count > 0;
}

bool a90_helper_has_warnings(void) {
    helper_scan_if_needed();
    return helper_warn_count > 0;
}

int a90_helper_print_inventory(bool verbose) {
    int index;

    (void)a90_helper_scan();
    a90_console_printf("helpers: entries=%d warn=%d fail=%d manifest=%s\r\n",
            helper_count,
            helper_warn_count,
            helper_fail_count,
            helper_manifest_present ? "yes" : "no");
    a90_console_printf("helpers: manifest_path=%s\r\n", helper_manifest_path);
    if (!verbose) {
        return helper_fail_count > 0 ? -EIO : 0;
    }
    for (index = 0; index < helper_count; ++index) {
        const struct a90_helper_entry *entry = &helper_entries[index];

        a90_console_printf("helper: name=%s role=%s present=%s exec=%s required=%s path=%s\r\n",
                entry->name,
                entry->role,
                entry->present ? "yes" : "no",
                entry->executable ? "yes" : "no",
                entry->required ? "yes" : "no",
                entry->path);
        a90_console_printf("helper: name=%s preferred=%s fallback=%s fallback_present=%s mode=%04o size=%lld sha=%s\r\n",
                entry->name,
                entry->preferred[0] != '\0' ? entry->preferred : "-",
                entry->fallback[0] != '\0' ? entry->fallback : "-",
                entry->fallback_present ? "yes" : "no",
                entry->actual_mode,
                entry->actual_size,
                entry->actual_sha256[0] != '\0' ? entry->actual_sha256 : "-");
        if (entry->warning[0] != '\0') {
            a90_console_printf("helper: name=%s warning=%s\r\n",
                    entry->name,
                    entry->warning);
        }
    }
    return helper_fail_count > 0 ? -EIO : 0;
}

int a90_helper_cmd_helpers(char **argv, int argc) {
    bool verbose = false;
    bool verify = false;
    struct a90_helper_entry entry;

    if (argc <= 1 ||
        strcmp(argv[1], "status") == 0) {
        return a90_helper_print_inventory(false);
    }
    if (strcmp(argv[1], "verbose") == 0) {
        return a90_helper_print_inventory(true);
    }
    if (strcmp(argv[1], "path") == 0) {
        if (argc != 3) {
            a90_console_printf("usage: helpers path <name>\r\n");
            return -EINVAL;
        }
        if (a90_helper_find(argv[2], &entry) < 0) {
            a90_console_printf("helpers: %s not found\r\n", argv[2]);
            return -ENOENT;
        }
        a90_console_printf("helper: name=%s preferred=%s path=%s fallback=%s\r\n",
                entry.name,
                entry.preferred[0] != '\0' ? entry.preferred : "-",
                entry.path,
                entry.fallback[0] != '\0' ? entry.fallback : "-");
        return entry.preferred[0] != '\0' ? 0 : -ENOENT;
    }
    if (strcmp(argv[1], "verify") == 0) {
        verify = true;
        verbose = true;
        if (argc == 3) {
            if (a90_helper_find(argv[2], &entry) < 0) {
                a90_console_printf("helpers: %s not found\r\n", argv[2]);
                return -ENOENT;
            }
            a90_console_printf("helper: name=%s present=%s exec=%s preferred=%s warning=%s\r\n",
                    entry.name,
                    entry.present ? "yes" : "no",
                    entry.executable ? "yes" : "no",
                    entry.preferred[0] != '\0' ? entry.preferred : "-",
                    entry.warning[0] != '\0' ? entry.warning : "-");
            return entry.required && entry.warning[0] != '\0' ? -EIO : 0;
        }
    }
    if (verify && argc == 2) {
        return a90_helper_print_inventory(verbose);
    }
    a90_console_printf("usage: helpers [status|verbose|path <name>|verify [name]]\r\n");
    return -EINVAL;
}
