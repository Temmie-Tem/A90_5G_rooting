#include "a90_audio.h"

#include "a90_console.h"
#include "a90_util.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif

#define AUDIO_FW_DIR "/vendor/firmware_mnt/image"
#define AUDIO_FWCLASS_PATH "/sys/module/firmware_class/parameters/path"
#define AUDIO_BOOT_ATTR "/sys/kernel/boot_adsp/boot"
#define AUDIO_ADSP_BOOT_ONCE_TOKEN "AUD2_ONE_SHOT_ADSP_BOOT"
#define AUDIO_SND_MATERIALIZE_TOKEN "AUD3_DEV_SND_MATERIALIZE_ONLY"
#define AUDIO_SOUND_CLASS_DIR "/sys/class/sound"
#define AUDIO_DEV_SND_DIR "/dev/snd"
#define AUDIO_MAX_LISTED 8
#define AUDIO_SND_MAX_LISTED 64
#define AUDIO_MISSING_LIST_SIZE 192
#define AUDIO_ADSP_SEGMENT_MODEL "stock-sparse-b00-b11-b13-b16"

static const char *const AUDIO_ADSP_SEGMENTS[] = {
    "adsp.b00",
    "adsp.b01",
    "adsp.b02",
    "adsp.b03",
    "adsp.b04",
    "adsp.b05",
    "adsp.b06",
    "adsp.b07",
    "adsp.b08",
    "adsp.b09",
    "adsp.b10",
    "adsp.b11",
    "adsp.b13",
    "adsp.b14",
    "adsp.b15",
    "adsp.b16",
};

struct adsp_firmware_status {
    bool dir_exists;
    bool mdt_present;
    bool adspr_jsn_present;
    bool adspua_jsn_present;
    int present_segments;
    char missing_segments[AUDIO_MISSING_LIST_SIZE];
};

struct audio_snd_scan_stats {
    int entries;
    int allowed;
    int with_dev;
    int listed;
    int created;
    int already_ok;
    int missing;
    int invalid;
    int refused;
    int failed;
};

static const char *yesno(bool value) {
    return value ? "yes" : "no";
}

static bool path_lstat(const char *path, struct stat *st) {
    return lstat(path, st) == 0;
}

static bool path_is_dir(const char *path) {
    struct stat st;

    return path_lstat(path, &st) && S_ISDIR(st.st_mode);
}

static int count_dir_entries(const char *path) {
    DIR *dir;
    struct dirent *entry;
    int count = 0;

    dir = opendir(path);
    if (dir == NULL) {
        return 0;
    }
    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        ++count;
    }
    closedir(dir);
    return count;
}

static bool name_contains_ci(const char *name, const char *needle) {
    size_t name_len = strlen(name);
    size_t needle_len = strlen(needle);
    size_t offset;

    if (needle_len == 0 || needle_len > name_len) {
        return false;
    }
    for (offset = 0; offset + needle_len <= name_len; ++offset) {
        size_t index;
        bool matched = true;

        for (index = 0; index < needle_len; ++index) {
            char lhs = name[offset + index];
            char rhs = needle[index];

            if (lhs >= 'A' && lhs <= 'Z') {
                lhs = (char)(lhs - 'A' + 'a');
            }
            if (rhs >= 'A' && rhs <= 'Z') {
                rhs = (char)(rhs - 'A' + 'a');
            }
            if (lhs != rhs) {
                matched = false;
                break;
            }
        }
        if (matched) {
            return true;
        }
    }
    return false;
}

static bool make_child_path(char *out, size_t out_size, const char *base, const char *leaf) {
    size_t base_len = strlen(base);
    size_t leaf_len = strlen(leaf);

    if (out_size == 0 || base_len + 1 + leaf_len + 1 > out_size) {
        if (out_size > 0) {
            out[0] = '\0';
        }
        return false;
    }
    memcpy(out, base, base_len);
    out[base_len] = '/';
    memcpy(out + base_len + 1, leaf, leaf_len + 1);
    return true;
}

static bool starts_with(const char *value, const char *prefix) {
    return strncmp(value, prefix, strlen(prefix)) == 0;
}

static bool decimal_tail_nonempty(const char *value) {
    size_t index;

    if (value == NULL || value[0] == '\0') {
        return false;
    }
    for (index = 0; value[index] != '\0'; ++index) {
        if (value[index] < '0' || value[index] > '9') {
            return false;
        }
    }
    return true;
}

static bool allowed_control_name(const char *name) {
    return starts_with(name, "controlC") && decimal_tail_nonempty(name + strlen("controlC"));
}

static bool allowed_pcm_name(const char *name) {
    const char *cursor;

    if (!starts_with(name, "pcmC")) {
        return false;
    }
    cursor = name + strlen("pcmC");
    if (*cursor < '0' || *cursor > '9') {
        return false;
    }
    while (*cursor >= '0' && *cursor <= '9') {
        ++cursor;
    }
    if (*cursor != 'D') {
        return false;
    }
    ++cursor;
    if (*cursor < '0' || *cursor > '9') {
        return false;
    }
    while (*cursor >= '0' && *cursor <= '9') {
        ++cursor;
    }
    if ((*cursor != 'p' && *cursor != 'c') || cursor[1] != '\0') {
        return false;
    }
    return true;
}

static bool allowed_sound_node_name(const char *name) {
    if (name == NULL || name[0] == '\0' ||
        strcmp(name, ".") == 0 || strcmp(name, "..") == 0 ||
        strchr(name, '/') != NULL) {
        return false;
    }
    return allowed_control_name(name) ||
           allowed_pcm_name(name) ||
           strcmp(name, "timer") == 0 ||
           strcmp(name, "seq") == 0;
}

static int parse_dev_numbers(const char *dev_info,
                             unsigned int *major_num,
                             unsigned int *minor_num) {
    char extra;

    if (sscanf(dev_info, "%u:%u%c", major_num, minor_num, &extra) != 2) {
        errno = EINVAL;
        return -1;
    }
    return 0;
}

static int sound_node_paths(const char *name,
                            char *sysfs_dev_path,
                            size_t sysfs_dev_path_size,
                            char *dev_node_path,
                            size_t dev_node_path_size) {
    char sysfs_entry_path[PATH_MAX];

    if (!allowed_sound_node_name(name)) {
        errno = EINVAL;
        return -1;
    }
    if (!make_child_path(sysfs_entry_path, sizeof(sysfs_entry_path), AUDIO_SOUND_CLASS_DIR, name) ||
        !make_child_path(sysfs_dev_path, sysfs_dev_path_size, sysfs_entry_path, "dev") ||
        !make_child_path(dev_node_path, dev_node_path_size, AUDIO_DEV_SND_DIR, name)) {
        errno = ENAMETOOLONG;
        return -1;
    }
    return 0;
}

static int read_sound_node_numbers(const char *name,
                                   char *sysfs_dev_path,
                                   size_t sysfs_dev_path_size,
                                   char *dev_node_path,
                                   size_t dev_node_path_size,
                                   unsigned int *major_num,
                                   unsigned int *minor_num,
                                   char *dev_info,
                                   size_t dev_info_size) {
    if (sound_node_paths(name, sysfs_dev_path, sysfs_dev_path_size,
                         dev_node_path, dev_node_path_size) < 0) {
        return -1;
    }
    if (read_trimmed_text_file(sysfs_dev_path, dev_info, dev_info_size) < 0) {
        return -1;
    }
    if (parse_dev_numbers(dev_info, major_num, minor_num) < 0) {
        return -1;
    }
    return 0;
}

static const char *sound_devnode_state(const char *path, dev_t wanted) {
    struct stat st;

    if (lstat(path, &st) < 0) {
        if (errno == ENOENT) {
            return "missing";
        }
        return "stat-failed";
    }
    if (!S_ISCHR(st.st_mode)) {
        return "not-char";
    }
    if (st.st_rdev != wanted) {
        return "mismatch";
    }
    return "ok";
}

static int count_dir_entries_matching(const char *path, const char *needle) {
    DIR *dir;
    struct dirent *entry;
    int count = 0;

    dir = opendir(path);
    if (dir == NULL) {
        return 0;
    }
    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        if (name_contains_ci(entry->d_name, needle)) {
            ++count;
        }
    }
    closedir(dir);
    return count;
}

static bool firmware_file_exists_ci_at(const char *dir_path, const char *wanted) {
    DIR *dir;
    struct dirent *entry;
    bool found = false;

    dir = opendir(dir_path);
    if (dir == NULL) {
        return false;
    }
    while ((entry = readdir(dir)) != NULL) {
        if (strcasecmp(entry->d_name, wanted) == 0) {
            found = true;
            break;
        }
    }
    closedir(dir);
    return found;
}

static int expected_adsp_segments(void) {
    return (int)(sizeof(AUDIO_ADSP_SEGMENTS) / sizeof(AUDIO_ADSP_SEGMENTS[0]));
}

static void append_missing_segment(char *out, size_t out_size, const char *segment) {
    size_t used;
    size_t segment_len;

    if (out == NULL || out_size == 0 || segment == NULL) {
        return;
    }
    used = strlen(out);
    if (used > 0) {
        if (used + 1 >= out_size) {
            return;
        }
        out[used++] = ',';
        out[used] = '\0';
    }
    segment_len = strlen(segment);
    if (used + segment_len >= out_size) {
        if (used + 3 < out_size) {
            memcpy(out + used, "...", 4);
        }
        return;
    }
    memcpy(out + used, segment, segment_len + 1);
}

static void check_adsp_firmware_dir(const char *dir_path, struct adsp_firmware_status *status) {
    int index;

    if (status == NULL) {
        return;
    }
    memset(status, 0, sizeof(*status));
    status->dir_exists = path_is_dir(dir_path);
    status->mdt_present = firmware_file_exists_ci_at(dir_path, "adsp.mdt");
    status->adspr_jsn_present = firmware_file_exists_ci_at(dir_path, "adspr.jsn");
    status->adspua_jsn_present = firmware_file_exists_ci_at(dir_path, "adspua.jsn");
    strcpy(status->missing_segments, "none");
    for (index = 0; index < expected_adsp_segments(); ++index) {
        if (firmware_file_exists_ci_at(dir_path, AUDIO_ADSP_SEGMENTS[index])) {
            ++status->present_segments;
            continue;
        }
        if (strcmp(status->missing_segments, "none") == 0) {
            status->missing_segments[0] = '\0';
        }
        append_missing_segment(status->missing_segments,
                               sizeof(status->missing_segments),
                               AUDIO_ADSP_SEGMENTS[index]);
    }
    if (status->missing_segments[0] == '\0') {
        strcpy(status->missing_segments, "none");
    }
}

static bool adsp_firmware_complete(const struct adsp_firmware_status *status) {
    return status != NULL &&
           status->dir_exists &&
           status->mdt_present &&
           status->present_segments == expected_adsp_segments();
}

static void print_adsp_firmware_check(const char *prefix,
                                      const char *dir_path,
                                      const struct adsp_firmware_status *status) {
    a90_console_printf("audio.%s_dir=%s exists=%s\r\n",
                       prefix,
                       dir_path,
                       yesno(status != NULL && status->dir_exists));
    a90_console_printf("audio.%s.adsp_mdt=%s\r\n", prefix, yesno(status != NULL && status->mdt_present));
    a90_console_printf("audio.%s.adsp_segments_model=%s\r\n", prefix, AUDIO_ADSP_SEGMENT_MODEL);
    a90_console_printf("audio.%s.adsp_segments_present=%d expected=%d\r\n",
                       prefix,
                       status != NULL ? status->present_segments : 0,
                       expected_adsp_segments());
    a90_console_printf("audio.%s.adsp_segments_missing=%s\r\n",
                       prefix,
                       status != NULL ? status->missing_segments : "unknown");
    a90_console_printf("audio.%s.adspr_jsn=%s\r\n",
                       prefix,
                       yesno(status != NULL && status->adspr_jsn_present));
    a90_console_printf("audio.%s.adspua_jsn=%s\r\n",
                       prefix,
                       yesno(status != NULL && status->adspua_jsn_present));
}

static void print_trimmed_or_missing(const char *key, const char *path) {
    char value[256];

    if (read_trimmed_text_file(path, value, sizeof(value)) == 0) {
        flatten_inline_text(value);
        a90_console_printf("audio.%s=%s\r\n", key, value[0] != '\0' ? value : "empty");
        return;
    }
    a90_console_printf("audio.%s=missing errno=%d\r\n", key, errno);
}

static void print_mode_line(const char *key, const char *path) {
    struct stat st;

    if (path_lstat(path, &st)) {
        a90_console_printf("audio.%s.exists=yes mode=%03o type=%s\r\n",
                           key,
                           (unsigned int)(st.st_mode & 0777),
                           S_ISDIR(st.st_mode) ? "dir" :
                           S_ISREG(st.st_mode) ? "file" :
                           S_ISLNK(st.st_mode) ? "symlink" : "other");
        return;
    }
    a90_console_printf("audio.%s.exists=no errno=%d\r\n", key, errno);
}

static void print_firmware_status(void) {
    struct adsp_firmware_status mounted_status;
    struct adsp_firmware_status class_status;
    char fwclass_path[PATH_MAX];

    check_adsp_firmware_dir(AUDIO_FW_DIR, &mounted_status);
    print_adsp_firmware_check("firmware", AUDIO_FW_DIR, &mounted_status);
    if (read_trimmed_text_file(AUDIO_FWCLASS_PATH, fwclass_path, sizeof(fwclass_path)) == 0 &&
        fwclass_path[0] != '\0') {
        flatten_inline_text(fwclass_path);
        check_adsp_firmware_dir(fwclass_path, &class_status);
        print_adsp_firmware_check("firmware_class", fwclass_path, &class_status);
        a90_console_printf("audio.firmware_class.adsp_complete=%s\r\n",
                           yesno(adsp_firmware_complete(&class_status)));
        return;
    }
    a90_console_printf("audio.firmware_class_dir=unavailable\r\n");
    a90_console_printf("audio.firmware_class.adsp_complete=no\r\n");
}

static void print_remoteproc_status(void) {
    DIR *dir;
    struct dirent *entry;
    int listed = 0;

    a90_console_printf("audio.remoteproc.count=%d\r\n", count_dir_entries("/sys/class/remoteproc"));
    dir = opendir("/sys/class/remoteproc");
    if (dir == NULL) {
        a90_console_printf("audio.remoteproc.open_errno=%d\r\n", errno);
        return;
    }
    while ((entry = readdir(dir)) != NULL && listed < AUDIO_MAX_LISTED) {
        char base[PATH_MAX];
        char name_path[PATH_MAX];
        char state_path[PATH_MAX];
        char name[128] = "missing";
        char state[128] = "missing";

        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        snprintf(base, sizeof(base), "/sys/class/remoteproc/%s", entry->d_name);
        if (!make_child_path(name_path, sizeof(name_path), base, "name") ||
            read_trimmed_text_file(name_path, name, sizeof(name)) < 0) {
            snprintf(name, sizeof(name), "missing");
        }
        if (!make_child_path(state_path, sizeof(state_path), base, "state") ||
            read_trimmed_text_file(state_path, state, sizeof(state)) < 0) {
            snprintf(state, sizeof(state), "missing");
        }
        flatten_inline_text(name);
        flatten_inline_text(state);
        a90_console_printf("audio.remoteproc.%d.node=%s name=%s state=%s\r\n",
                           listed,
                           entry->d_name,
                           name,
                           state);
        ++listed;
    }
    closedir(dir);
}

static void print_class_counts(void) {
    a90_console_printf("audio.rpmsg.count=%d adsp_like=%d cdsp_like=%d\r\n",
                       count_dir_entries("/sys/bus/rpmsg/devices"),
                       count_dir_entries_matching("/sys/bus/rpmsg/devices", "adsp"),
                       count_dir_entries_matching("/sys/bus/rpmsg/devices", "cdsp"));
    a90_console_printf("audio.rpmsg_class.count=%d\r\n", count_dir_entries("/sys/class/rpmsg"));
    a90_console_printf("audio.fastrpc_class.count=%d\r\n", count_dir_entries("/sys/class/fastrpc"));
    a90_console_printf("audio.sound_class.count=%d card_like=%d control_like=%d\r\n",
                       count_dir_entries("/sys/class/sound"),
                       count_dir_entries_matching("/sys/class/sound", "card"),
                       count_dir_entries_matching("/sys/class/sound", "control"));
    a90_console_printf("audio.dev_snd.count=%d control_like=%d pcm_like=%d\r\n",
                       count_dir_entries("/dev/snd"),
                       count_dir_entries_matching("/dev/snd", "controlC"),
                       count_dir_entries_matching("/dev/snd", "pcm"));
}

static void print_proc_asound(void) {
    char cards[512];

    if (read_trimmed_text_file("/proc/asound/cards", cards, sizeof(cards)) == 0) {
        flatten_inline_text(cards);
        a90_console_printf("audio.proc_asound_cards=%s\r\n", cards[0] != '\0' ? cards : "empty");
    } else {
        a90_console_printf("audio.proc_asound_cards=missing errno=%d\r\n", errno);
    }
}

static int audio_scan_snd_nodes(bool materialize, struct audio_snd_scan_stats *stats) {
    DIR *dir;
    struct dirent *entry;

    memset(stats, 0, sizeof(*stats));
    dir = opendir(AUDIO_SOUND_CLASS_DIR);
    if (dir == NULL) {
        a90_console_printf("audio.snd.sysfs_open_errno=%d\r\n", errno);
        return negative_errno_or(ENOENT);
    }

    while ((entry = readdir(dir)) != NULL) {
        char sysfs_dev_path[PATH_MAX];
        char dev_node_path[PATH_MAX];
        char dev_info[64];
        unsigned int major_num = 0;
        unsigned int minor_num = 0;
        dev_t wanted;
        const char *node_state;

        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        ++stats->entries;
        if (!allowed_sound_node_name(entry->d_name)) {
            ++stats->refused;
            continue;
        }
        ++stats->allowed;
        if (read_sound_node_numbers(entry->d_name,
                                    sysfs_dev_path,
                                    sizeof(sysfs_dev_path),
                                    dev_node_path,
                                    sizeof(dev_node_path),
                                    &major_num,
                                    &minor_num,
                                    dev_info,
                                    sizeof(dev_info)) < 0) {
            ++stats->invalid;
            if (stats->listed < AUDIO_SND_MAX_LISTED) {
                a90_console_printf("audio.snd.%d.name=%s dev=invalid errno=%d action=skip\r\n",
                                   stats->listed,
                                   entry->d_name,
                                   errno);
                ++stats->listed;
            }
            continue;
        }
        ++stats->with_dev;
        wanted = makedev(major_num, minor_num);
        node_state = sound_devnode_state(dev_node_path, wanted);
        if (strcmp(node_state, "ok") == 0) {
            ++stats->already_ok;
        } else if (strcmp(node_state, "missing") == 0) {
            ++stats->missing;
        } else {
            ++stats->invalid;
        }

        if (stats->listed < AUDIO_SND_MAX_LISTED) {
            a90_console_printf("audio.snd.%d.name=%s sysfs_dev=%u:%u devnode=%s state=%s\r\n",
                               stats->listed,
                               entry->d_name,
                               major_num,
                               minor_num,
                               dev_node_path,
                               node_state);
            ++stats->listed;
        }

        if (!materialize) {
            continue;
        }
        if (strcmp(node_state, "ok") == 0) {
            continue;
        }
        if (strcmp(node_state, "missing") != 0) {
            a90_console_printf("audio.snd.materialize.refused=%s state=%s\r\n",
                               entry->d_name,
                               node_state);
            continue;
        }
        if (mknod(dev_node_path, S_IFCHR | 0600, wanted) < 0) {
            if (errno == EEXIST && strcmp(sound_devnode_state(dev_node_path, wanted), "ok") == 0) {
                ++stats->already_ok;
                continue;
            }
            a90_console_printf("audio.snd.materialize.failed=%s errno=%d\r\n",
                               entry->d_name,
                               errno);
            ++stats->failed;
            continue;
        }
        ++stats->created;
        a90_console_printf("audio.snd.materialize.created=%s major=%u minor=%u\r\n",
                           entry->d_name,
                           major_num,
                           minor_num);
    }
    closedir(dir);
    return 0;
}

static void audio_print_snd_scan_summary(const char *prefix, const struct audio_snd_scan_stats *stats) {
    a90_console_printf("%s.entries=%d allowed=%d with_dev=%d listed=%d missing=%d already_ok=%d invalid=%d refused=%d created=%d failed=%d\r\n",
                       prefix,
                       stats->entries,
                       stats->allowed,
                       stats->with_dev,
                       stats->listed,
                       stats->missing,
                       stats->already_ok,
                       stats->invalid,
                       stats->refused,
                       stats->created,
                       stats->failed);
}

static int audio_print_snd_status(void) {
    struct audio_snd_scan_stats stats;
    int rc;

    a90_console_printf("audio.snd_status.version=1\r\n");
    a90_console_printf("audio.snd_status.read_only=1\r\n");
    print_class_counts();
    print_proc_asound();
    rc = audio_scan_snd_nodes(false, &stats);
    audio_print_snd_scan_summary("audio.snd_status", &stats);
    a90_console_printf("audio.status.audio_playback_attempted=0\r\n");
    return rc;
}

static int audio_snd_materialize_once(char **argv, int argc) {
    struct audio_snd_scan_stats stats;
    int rc;

    a90_console_printf("audio.snd_materialize.version=1\r\n");
    a90_console_printf("audio.snd_materialize.scope=AUD-3-preflight-node-materialization-only\r\n");
    a90_console_printf("audio.status.audio_playback_attempted=0\r\n");

    if (argc != 3 || argv == NULL || argv[2] == NULL ||
        strcmp(argv[2], AUDIO_SND_MATERIALIZE_TOKEN) != 0) {
        a90_console_printf("audio.snd_materialize.refused=missing-token\r\n");
        a90_console_printf("usage: audio snd-materialize-once %s\r\n", AUDIO_SND_MATERIALIZE_TOKEN);
        return -EPERM;
    }
    if (count_dir_entries_matching(AUDIO_SOUND_CLASS_DIR, "control") <= 0) {
        a90_console_printf("audio.snd_materialize.refused=no-control-sysfs\r\n");
        return -ENOENT;
    }
    if (ensure_dir(AUDIO_DEV_SND_DIR, 0755) < 0) {
        a90_console_printf("audio.snd_materialize.refused=dev-snd-dir errno=%d\r\n", errno);
        return negative_errno_or(EIO);
    }

    rc = audio_scan_snd_nodes(true, &stats);
    audio_print_snd_scan_summary("audio.snd_materialize", &stats);
    a90_console_printf("audio.snd_materialize.open_attempted=0\r\n");
    a90_console_printf("audio.snd_materialize.ioctl_attempted=0\r\n");
    a90_console_printf("audio.snd_materialize.playback_attempted=0\r\n");
    if (rc < 0) {
        return rc;
    }
    if (stats.failed > 0 || stats.invalid > 0) {
        return -EIO;
    }
    if (stats.created == 0 && stats.already_ok == 0) {
        return -ENOENT;
    }
    return 0;
}

static int audio_print_adsp_status(void) {
    struct audio_snd_scan_stats snd_stats;
    a90_console_printf("audio.status.version=1\r\n");
    a90_console_printf("audio.status.read_only=1\r\n");
    print_trimmed_or_missing("firmware_class_path", AUDIO_FWCLASS_PATH);
    print_mode_line("boot_adsp_boot", AUDIO_BOOT_ATTR);
    print_firmware_status();
    print_remoteproc_status();
    print_class_counts();
    print_proc_asound();
    if (audio_scan_snd_nodes(false, &snd_stats) == 0) {
        audio_print_snd_scan_summary("audio.snd_status", &snd_stats);
    }
    print_mode_line("dev_subsys_adsp", "/dev/subsys_adsp");
    print_mode_line("dev_adsprpc_smd", "/dev/adsprpc-smd");
    a90_console_printf("audio.status.activation_write_attempted=0\r\n");
    a90_console_printf("audio.status.audio_playback_attempted=0\r\n");
    return 0;
}

static int audio_adsp_boot_once(char **argv, int argc) {
    struct adsp_firmware_status mounted_status;
    struct adsp_firmware_status class_status;
    struct stat st;
    char fwclass_path[PATH_MAX];
    int fwclass_read_rc;
    int fd;

    a90_console_printf("audio.adsp_boot_once.version=1\r\n");
    a90_console_printf("audio.adsp_boot_once.scope=AUD-2-liveness-only\r\n");
    a90_console_printf("audio.status.audio_playback_attempted=0\r\n");

    if (argc != 3 || argv == NULL || argv[2] == NULL ||
        strcmp(argv[2], AUDIO_ADSP_BOOT_ONCE_TOKEN) != 0) {
        a90_console_printf("audio.adsp_boot_once.refused=missing-token\r\n");
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        a90_console_printf("usage: audio adsp-boot-once %s\r\n", AUDIO_ADSP_BOOT_ONCE_TOKEN);
        return -EPERM;
    }

    if (!path_lstat(AUDIO_BOOT_ATTR, &st)) {
        a90_console_printf("audio.adsp_boot_once.refused=no-boot-attr errno=%d\r\n", errno);
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return negative_errno_or(ENOENT);
    }
    if (!path_is_dir(AUDIO_FW_DIR)) {
        a90_console_printf("audio.adsp_boot_once.refused=no-firmware-dir\r\n");
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return -ENOENT;
    }
    check_adsp_firmware_dir(AUDIO_FW_DIR, &mounted_status);
    if (!mounted_status.mdt_present) {
        a90_console_printf("audio.adsp_boot_once.refused=no-adsp-mdt\r\n");
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return -ENOENT;
    }
    if (mounted_status.present_segments != expected_adsp_segments()) {
        a90_console_printf("audio.adsp_boot_once.refused=missing-adsp-segments present=%d expected=%d model=%s missing=%s\r\n",
                           mounted_status.present_segments,
                           expected_adsp_segments(),
                           AUDIO_ADSP_SEGMENT_MODEL,
                           mounted_status.missing_segments);
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return -ENOENT;
    }
    fwclass_read_rc = read_trimmed_text_file(AUDIO_FWCLASS_PATH, fwclass_path, sizeof(fwclass_path));
    if (fwclass_read_rc < 0) {
        a90_console_printf("audio.adsp_boot_once.refused=firmware-class-path-unreadable errno=%d\r\n",
                           errno);
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return negative_errno_or(ENOENT);
    }
    if (fwclass_path[0] == '\0') {
        a90_console_printf("audio.adsp_boot_once.refused=firmware-class-path-empty\r\n");
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return -ENOENT;
    }
    flatten_inline_text(fwclass_path);
    check_adsp_firmware_dir(fwclass_path, &class_status);
    if (!adsp_firmware_complete(&class_status)) {
        a90_console_printf("audio.adsp_boot_once.refused=firmware-class-path-incomplete path=%s mdt=%s present=%d expected=%d model=%s missing=%s\r\n",
                           fwclass_path,
                           yesno(class_status.mdt_present),
                           class_status.present_segments,
                           expected_adsp_segments(),
                           AUDIO_ADSP_SEGMENT_MODEL,
                           class_status.missing_segments);
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return -ENOENT;
    }
    if (count_dir_entries_matching("/sys/bus/rpmsg/devices", "adsp") > 0 ||
        count_dir_entries_matching("/sys/class/sound", "card") > 0 ||
        count_dir_entries_matching("/dev/snd", "controlC") > 0) {
        a90_console_printf("audio.adsp_boot_once.refused=already-up-or-sound-present\r\n");
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return -EALREADY;
    }

    fd = open(AUDIO_BOOT_ATTR, O_WRONLY | O_CLOEXEC);
    if (fd < 0) {
        a90_console_printf("audio.adsp_boot_once.write=open_failed errno=%d\r\n", errno);
        a90_console_printf("audio.status.activation_write_attempted=0\r\n");
        return negative_errno_or(EIO);
    }

    a90_console_printf("audio.status.activation_write_attempted=1\r\n");
    if (write_all_checked(fd, "1\n", 2) < 0) {
        a90_console_printf("audio.adsp_boot_once.write=failed errno=%d\r\n", errno);
        close(fd);
        return negative_errno_or(EIO);
    }
    if (close(fd) < 0) {
        a90_console_printf("audio.adsp_boot_once.write=close_failed errno=%d\r\n", errno);
        return negative_errno_or(EIO);
    }
    a90_console_printf("audio.adsp_boot_once.write=accepted\r\n");
    a90_console_printf("audio.adsp_boot_once.retry=forbidden\r\n");
    return 0;
}

int a90_audio_cmd(char **argv, int argc) {
    if (argc <= 1 ||
        (argc == 2 && (strcmp(argv[1], "adsp-status") == 0 || strcmp(argv[1], "status") == 0))) {
        return audio_print_adsp_status();
    }
    if (argc >= 2 && argv != NULL && argv[1] != NULL && strcmp(argv[1], "adsp-boot-once") == 0) {
        return audio_adsp_boot_once(argv, argc);
    }
    if (argc == 2 && argv != NULL && argv[1] != NULL && strcmp(argv[1], "snd-status") == 0) {
        return audio_print_snd_status();
    }
    if (argc >= 2 && argv != NULL && argv[1] != NULL && strcmp(argv[1], "snd-materialize-once") == 0) {
        return audio_snd_materialize_once(argv, argc);
    }
    a90_console_printf("usage: audio [adsp-status|status|snd-status|adsp-boot-once|snd-materialize-once]\r\n");
    return -EINVAL;
}
