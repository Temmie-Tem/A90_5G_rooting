#define _DEFAULT_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#define O0_MAGIC "S2O0"
#define O0_VERSION 1U
#define O0_REQUEST 1U
#define O0_RESPONSE 2U
#define O0_HEADER_SIZE 16U
#define O0_MAX_PAYLOAD 1024U

static volatile sig_atomic_t g_stop;

static void on_signal(int signum) {
    (void)signum;
    g_stop = 1;
}

static uint16_t load_le16(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static uint32_t load_le32(const uint8_t *p) {
    return (uint32_t)p[0] |
           ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
}

static void store_le16(uint8_t *p, uint16_t value) {
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
}

static void store_le32(uint8_t *p, uint32_t value) {
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
    p[2] = (uint8_t)(value >> 16);
    p[3] = (uint8_t)(value >> 24);
}

static uint32_t crc32_update(uint32_t crc, const uint8_t *data, size_t len) {
    crc = ~crc;
    for (size_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (unsigned int bit = 0; bit < 8U; ++bit) {
            uint32_t mask = (uint32_t)-(int32_t)(crc & 1U);
            crc = (crc >> 1) ^ (0xedb88320U & mask);
        }
    }
    return ~crc;
}

static uint32_t frame_crc(const uint8_t header[O0_HEADER_SIZE], const uint8_t *payload, size_t len) {
    uint32_t crc = crc32_update(0U, header, 12U);
    return crc32_update(crc, payload, len);
}

static int64_t monotonic_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (int64_t)ts.tv_sec * 1000LL + (int64_t)ts.tv_nsec / 1000000LL;
}

static int wait_fd(int fd, short events, int timeout_ms) {
    struct pollfd pfd = {.fd = fd, .events = events, .revents = 0};
    int rc;
    do {
        rc = poll(&pfd, 1, timeout_ms);
    } while (rc < 0 && errno == EINTR && !g_stop);
    if (rc <= 0) {
        return rc;
    }
    if ((pfd.revents & (POLLERR | POLLHUP | POLLNVAL)) != 0) {
        return -1;
    }
    return (pfd.revents & events) != 0 ? 1 : 0;
}

static int read_exact(int fd, uint8_t *buf, size_t len, int timeout_ms) {
    size_t done = 0;
    int64_t deadline = monotonic_ms() + timeout_ms;
    while (done < len && !g_stop) {
        int64_t remaining = deadline - monotonic_ms();
        if (remaining <= 0) {
            return 0;
        }
        int ready = wait_fd(fd, POLLIN, (int)remaining);
        if (ready <= 0) {
            return ready;
        }
        ssize_t rc = read(fd, buf + done, len - done);
        if (rc > 0) {
            done += (size_t)rc;
            continue;
        }
        if (rc < 0 && (errno == EINTR || errno == EAGAIN)) {
            continue;
        }
        return -1;
    }
    return done == len ? 1 : -1;
}

static int write_all(int fd, const uint8_t *buf, size_t len, int timeout_ms) {
    size_t done = 0;
    int64_t deadline = monotonic_ms() + timeout_ms;
    while (done < len && !g_stop) {
        int64_t remaining = deadline - monotonic_ms();
        if (remaining <= 0) {
            return 0;
        }
        int ready = wait_fd(fd, POLLOUT, (int)remaining);
        if (ready <= 0) {
            return ready;
        }
        ssize_t rc = write(fd, buf + done, len - done);
        if (rc > 0) {
            done += (size_t)rc;
            continue;
        }
        if (rc < 0 && (errno == EINTR || errno == EAGAIN)) {
            continue;
        }
        return -1;
    }
    return done == len ? 1 : -1;
}

static int open_tty(const char *path, int flush_input, struct termios *saved, int *have_saved) {
    int fd = open(path, O_RDWR | O_NOCTTY | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) {
        return -1;
    }
    struct termios tio;
    if (tcgetattr(fd, saved) != 0) {
        close(fd);
        return -1;
    }
    *have_saved = 1;
    tio = *saved;
    cfmakeraw(&tio);
    tio.c_cflag |= CLOCAL | CREAD;
    tio.c_cc[VMIN] = 0;
    tio.c_cc[VTIME] = 0;
    if (tcsetattr(fd, TCSANOW, &tio) != 0) {
        close(fd);
        *have_saved = 0;
        return -1;
    }
    if (flush_input) {
        (void)tcflush(fd, TCIOFLUSH);
    }
    return fd;
}

static void close_tty(int fd, const struct termios *saved, int have_saved) {
    if (have_saved) {
        (void)tcsetattr(fd, TCSANOW, saved);
    }
    close(fd);
}

static int parse_uint(const char *text, unsigned int *out) {
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' || value > 0xffffffffUL) {
        return -1;
    }
    *out = (unsigned int)value;
    return 0;
}

static void usage(const char *argv0) {
    fprintf(stderr,
            "usage: %s [--device PATH] [--max-requests N] [--idle-timeout-ms N]\n",
            argv0);
}

int main(int argc, char **argv) {
    const char *device = "/dev/ttyGS0";
    unsigned int max_requests = 128U;
    unsigned int idle_timeout_ms = 60000U;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--device") == 0 && i + 1 < argc) {
            device = argv[++i];
        } else if (strcmp(argv[i], "--max-requests") == 0 && i + 1 < argc) {
            if (parse_uint(argv[++i], &max_requests) != 0 || max_requests == 0U) {
                usage(argv[0]);
                return 2;
            }
        } else if (strcmp(argv[i], "--idle-timeout-ms") == 0 && i + 1 < argc) {
            if (parse_uint(argv[++i], &idle_timeout_ms) != 0 || idle_timeout_ms < 1000U) {
                usage(argv[0]);
                return 2;
            }
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);
    signal(SIGHUP, on_signal);

    unsigned int handled = 0;
    unsigned int invalid = 0;
    unsigned int crc_errors = 0;
    unsigned int seq_errors = 0;
    unsigned int io_reopens = 0;
    uint32_t expected_seq = 0U;
    int have_seq = 0;
    int first_open = 1;
    int64_t last_activity = monotonic_ms();

    printf("S22_O0_DAEMON_READY device=%s max_requests=%u idle_timeout_ms=%u\n",
           device, max_requests, idle_timeout_ms);

    while (!g_stop && handled < max_requests) {
        if ((uint64_t)(monotonic_ms() - last_activity) >= idle_timeout_ms) {
            break;
        }
        struct termios saved;
        int have_saved = 0;
        int fd = open_tty(device, first_open, &saved, &have_saved);
        first_open = 0;
        if (fd < 0) {
            ++io_reopens;
            usleep(50000U);
            continue;
        }

        while (!g_stop && handled < max_requests) {
            uint8_t header[O0_HEADER_SIZE];
            uint8_t payload[O0_MAX_PAYLOAD];
            int rc = read_exact(fd, header, sizeof(header), 1000);
            if (rc == 0) {
                if ((uint64_t)(monotonic_ms() - last_activity) >= idle_timeout_ms) {
                    break;
                }
                continue;
            }
            if (rc < 0) {
                ++io_reopens;
                break;
            }
            last_activity = monotonic_ms();

            uint16_t payload_len = load_le16(&header[6]);
            uint32_t seq = load_le32(&header[8]);
            uint32_t received_crc = load_le32(&header[12]);
            if (memcmp(header, O0_MAGIC, 4) != 0 || header[4] != O0_VERSION ||
                header[5] != O0_REQUEST || payload_len > O0_MAX_PAYLOAD) {
                ++invalid;
                break;
            }
            rc = read_exact(fd, payload, payload_len, 2000);
            if (rc <= 0) {
                ++io_reopens;
                break;
            }
            if (frame_crc(header, payload, payload_len) != received_crc) {
                ++crc_errors;
                continue;
            }
            if (have_seq && seq != expected_seq) {
                ++seq_errors;
            }
            expected_seq = seq + 1U;
            have_seq = 1;

            header[5] = O0_RESPONSE;
            store_le16(&header[6], payload_len);
            store_le32(&header[8], seq);
            store_le32(&header[12], 0U);
            store_le32(&header[12], frame_crc(header, payload, payload_len));
            if (write_all(fd, header, sizeof(header), 2000) <= 0 ||
                write_all(fd, payload, payload_len, 2000) <= 0) {
                ++io_reopens;
                break;
            }
            ++handled;
            last_activity = monotonic_ms();
        }
        close_tty(fd, &saved, have_saved);
    }

    printf("S22_O0_DAEMON_DONE handled=%u expected=%u invalid=%u crc_errors=%u "
           "seq_errors=%u io_reopens=%u stopped=%u\n",
           handled, max_requests, invalid, crc_errors, seq_errors, io_reopens,
           g_stop ? 1U : 0U);
    return handled == max_requests && invalid == 0U && crc_errors == 0U &&
                   seq_errors == 0U
               ? 0
               : 1;
}
