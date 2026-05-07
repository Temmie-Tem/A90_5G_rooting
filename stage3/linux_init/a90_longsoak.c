#include "a90_longsoak.h"

#include "a90_config.h"
#include "a90_console.h"
#include "a90_log.h"
#include "a90_run.h"
#include "a90_runtime.h"
#include "a90_service.h"
#include "a90_util.h"

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif

static char longsoak_path[PATH_MAX];
static char longsoak_session[64];
static int longsoak_interval_sec;

static int longsoak_parse_positive_int(const char *text, int *out) {
    char *end = NULL;
    long value;

    if (text == NULL || text[0] == '\0' || out == NULL) {
        return -EINVAL;
    }
    errno = 0;
    value = strtol(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        return -EINVAL;
    }
    if (value < A90_LONGSOAK_MIN_INTERVAL_SEC ||
        value > A90_LONGSOAK_MAX_INTERVAL_SEC) {
        return -ERANGE;
    }
    *out = (int)value;
    return 0;
}

static void longsoak_build_session(char *out, size_t out_size) {
    snprintf(out, out_size, "%s-%ld", INIT_BUILD, monotonic_millis());
}

static int longsoak_build_path(const char *session, char *out, size_t out_size) {
    const char *log_dir = a90_runtime_log_dir();
    int written;

    if (log_dir == NULL || log_dir[0] == '\0') {
        log_dir = NATIVE_LOG_FALLBACK_DIR;
        (void)ensure_dir(log_dir, 0700);
    }
    written = snprintf(out, out_size, "%s/longsoak-%s.jsonl", log_dir, session);
    if (written < 0 || (size_t)written >= out_size) {
        return -ENAMETOOLONG;
    }
    return 0;
}

static bool longsoak_is_running(void) {
    (void)a90_service_reap(A90_SERVICE_LONGSOAK, NULL);
    return a90_service_pid(A90_SERVICE_LONGSOAK) > 0;
}

int a90_longsoak_start(int interval_sec) {
    char interval_arg[24];
    char *const argv[] = {
        (char *)A90_LONGSOAK_HELPER,
        longsoak_path,
        interval_arg,
        longsoak_session,
        NULL,
    };
    struct a90_run_config config;
    pid_t pid = -1;
    int rc;

    if (interval_sec <= 0) {
        interval_sec = A90_LONGSOAK_DEFAULT_INTERVAL_SEC;
    }
    if (interval_sec < A90_LONGSOAK_MIN_INTERVAL_SEC ||
        interval_sec > A90_LONGSOAK_MAX_INTERVAL_SEC) {
        a90_console_printf("longsoak: interval must be %d..%d seconds\r\n",
                A90_LONGSOAK_MIN_INTERVAL_SEC,
                A90_LONGSOAK_MAX_INTERVAL_SEC);
        return -ERANGE;
    }
    if (longsoak_is_running()) {
        a90_console_printf("longsoak: already running pid=%ld path=%s\r\n",
                (long)a90_service_pid(A90_SERVICE_LONGSOAK),
                longsoak_path[0] != '\0' ? longsoak_path : "-");
        return 0;
    }

    longsoak_build_session(longsoak_session, sizeof(longsoak_session));
    rc = longsoak_build_path(longsoak_session, longsoak_path, sizeof(longsoak_path));
    if (rc < 0) {
        a90_console_printf("longsoak: path build failed rc=%d\r\n", rc);
        return rc;
    }
    snprintf(interval_arg, sizeof(interval_arg), "%d", interval_sec);

    memset(&config, 0, sizeof(config));
    config.tag = "longsoak";
    config.argv = argv;
    config.stdio_mode = A90_RUN_STDIO_NULL;
    config.ignore_hup_pipe = true;
    config.setsid = false;
    config.kill_process_group = false;

    rc = a90_run_spawn(&config, &pid);
    if (rc < 0) {
        a90_console_printf("longsoak: spawn %s failed rc=%d\r\n",
                A90_LONGSOAK_HELPER, rc);
        return rc;
    }
    longsoak_interval_sec = interval_sec;
    a90_service_set_pid(A90_SERVICE_LONGSOAK, pid);
    a90_logf("longsoak", "started pid=%ld interval=%d path=%s session=%s",
            (long)pid, interval_sec, longsoak_path, longsoak_session);
    a90_console_printf("longsoak: started pid=%ld interval=%ds session=%s\r\n",
            (long)pid, interval_sec, longsoak_session);
    a90_console_printf("longsoak: path=%s\r\n", longsoak_path);
    return 0;
}

int a90_longsoak_stop(void) {
    pid_t pid = a90_service_pid(A90_SERVICE_LONGSOAK);
    int rc;

    if (pid <= 0) {
        a90_console_printf("longsoak: not running\r\n");
        return 0;
    }
    rc = a90_service_stop(A90_SERVICE_LONGSOAK, 3000);
    a90_logf("longsoak", "stop pid=%ld rc=%d path=%s",
            (long)pid, rc, longsoak_path[0] != '\0' ? longsoak_path : "-");
    a90_console_printf("longsoak: stopped pid=%ld rc=%d\r\n", (long)pid, rc);
    return rc;
}

int a90_longsoak_status(void) {
    bool running = longsoak_is_running();

    a90_console_printf("longsoak: running=%s pid=%ld interval=%ds session=%s\r\n",
            running ? "yes" : "no",
            (long)a90_service_pid(A90_SERVICE_LONGSOAK),
            longsoak_interval_sec,
            longsoak_session[0] != '\0' ? longsoak_session : "-");
    a90_console_printf("longsoak: path=%s\r\n",
            longsoak_path[0] != '\0' ? longsoak_path : "-");
    return 0;
}

int a90_longsoak_path(void) {
    a90_console_printf("%s\r\n", longsoak_path[0] != '\0' ? longsoak_path : "-");
    return longsoak_path[0] != '\0' ? 0 : -ENOENT;
}

int a90_longsoak_tail(int lines) {
    char ring[A90_LONGSOAK_TAIL_MAX_LINES][512];
    int fd;
    FILE *file;
    size_t count = 0;
    size_t index;

    if (lines <= 0) {
        lines = A90_LONGSOAK_TAIL_DEFAULT_LINES;
    }
    if (lines > A90_LONGSOAK_TAIL_MAX_LINES) {
        lines = A90_LONGSOAK_TAIL_MAX_LINES;
    }
    if (longsoak_path[0] == '\0') {
        a90_console_printf("longsoak: no path yet\r\n");
        return -ENOENT;
    }
    fd = open(longsoak_path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        int saved_errno = errno;

        a90_console_printf("longsoak: open %s: %s\r\n",
                longsoak_path, strerror(saved_errno));
        return -saved_errno;
    }
    file = fdopen(fd, "r");
    if (file == NULL) {
        int saved_errno = errno;

        close(fd);
        a90_console_printf("longsoak: fdopen %s: %s\r\n",
                longsoak_path, strerror(saved_errno));
        return -saved_errno;
    }
    while (fgets(ring[count % (size_t)lines], sizeof(ring[0]), file) != NULL) {
        ++count;
    }
    fclose(file);

    index = count > (size_t)lines ? count - (size_t)lines : 0;
    a90_console_printf("longsoak: tail path=%s lines=%d total=%u\r\n",
            longsoak_path, lines, (unsigned int)count);
    for (; index < count; ++index) {
        char *line = ring[index % (size_t)lines];

        trim_newline(line);
        a90_console_printf("%s\r\n", line);
    }
    return 0;
}

int a90_longsoak_cmd(char **argv, int argc) {
    const char *subcommand = argc > 1 ? argv[1] : "status";
    int value;
    int rc;

    if (strcmp(subcommand, "status") == 0) {
        if (argc != 1 && argc != 2) {
            a90_console_printf("usage: longsoak [status|start [interval]|stop|path|tail [lines]]\r\n");
            return -EINVAL;
        }
        return a90_longsoak_status();
    }
    if (strcmp(subcommand, "start") == 0) {
        if (argc > 3) {
            a90_console_printf("usage: longsoak start [interval]\r\n");
            return -EINVAL;
        }
        value = A90_LONGSOAK_DEFAULT_INTERVAL_SEC;
        if (argc == 3) {
            rc = longsoak_parse_positive_int(argv[2], &value);
            if (rc < 0) {
                a90_console_printf("longsoak: invalid interval %s\r\n", argv[2]);
                return rc;
            }
        }
        return a90_longsoak_start(value);
    }
    if (strcmp(subcommand, "stop") == 0) {
        if (argc != 2) {
            a90_console_printf("usage: longsoak stop\r\n");
            return -EINVAL;
        }
        return a90_longsoak_stop();
    }
    if (strcmp(subcommand, "path") == 0) {
        if (argc != 2) {
            a90_console_printf("usage: longsoak path\r\n");
            return -EINVAL;
        }
        return a90_longsoak_path();
    }
    if (strcmp(subcommand, "tail") == 0) {
        if (argc > 3) {
            a90_console_printf("usage: longsoak tail [lines]\r\n");
            return -EINVAL;
        }
        value = A90_LONGSOAK_TAIL_DEFAULT_LINES;
        if (argc == 3) {
            rc = longsoak_parse_positive_int(argv[2], &value);
            if (rc < 0) {
                a90_console_printf("longsoak: invalid tail lines %s\r\n", argv[2]);
                return rc;
            }
        }
        return a90_longsoak_tail(value);
    }

    a90_console_printf("usage: longsoak [status|start [interval]|stop|path|tail [lines]]\r\n");
    return -EINVAL;
}
