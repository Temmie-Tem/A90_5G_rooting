// SPDX-License-Identifier: MIT
/* S22+ O3F direct-PID1 generic ACM control, with no libc or CRT. */

#include <stddef.h>
#include <stdint.h>

#include "s22plus_o2_loader_core.h"
#include "s22plus_o3_freestanding_protocol.h"
#include "module-plan.generated.h"

#define O3F_MARKER "S22_NATIVE_INIT_O3F_FREESTANDING_ACM"
#define O3F_VERSION "0.2"
#define O3F_MODULE_DIR "/lib/modules/"
#define O3F_STATUS_QUERY "O3 STATUS"
#define O3F_MAX_ECHO 128U
#define O3F_GATE_ATTEMPTS 100U
#define O3F_GATE_SLEEP_MS 100L
#define O3F_TTY_ATTEMPTS 100U
#define O3F_IDLE_TICKS 18000U

#define AT_FDCWD (-100)
#define O_RDONLY 00000000
#define O_WRONLY 00000001
#define O_RDWR 00000002
#define O_NOCTTY 00000400
#define O_NONBLOCK 00004000
#define O_CLOEXEC 02000000
#define S_IFCHR 0020000
#define MS_NOSUID 2UL
#define MS_NODEV 4UL
#define MS_NOEXEC 8UL
#define EINTR 4L
#define EAGAIN 11L
#define EBUSY 16L
#define EEXIST 17L
#define ENOENT 2L
#define EINVAL 22L
#define ENAMETOOLONG 36L
#define ETIMEDOUT 110L

#define NR_MKNODAT 33L
#define NR_MKDIRAT 34L
#define NR_UNLINKAT 35L
#define NR_SYMLINKAT 36L
#define NR_MOUNT 40L
#define NR_OPENAT 56L
#define NR_CLOSE 57L
#define NR_READ 63L
#define NR_WRITE 64L
#define NR_NEWFSTATAT 79L
#define NR_NANOSLEEP 101L
#define NR_FINIT_MODULE 273L

struct timespec64 {
    int64_t tv_sec;
    int64_t tv_nsec;
};

struct o3f_sbuf {
    char data[1024];
    size_t length;
    int truncated;
};

struct o3f_state {
    struct s22plus_o2_module_load_result load;
    struct s22plus_o2_proc_scan_result scan;
    uint64_t gate_mask;
    long proc_mount_rc;
    long sys_mount_rc;
    long dev_mount_rc;
    int registration_rc;
    long configfs_rc;
    long mode_write_rc;
    int mode_readback_ok;
    long udc_bind_rc;
    int udc_readback_ok;
    int tty_ready;
    unsigned int handled;
    unsigned int status_queries;
    unsigned int invalid;
    unsigned int crc_errors;
    unsigned int seq_errors;
    unsigned int io_reopens;
    uint32_t expected_seq;
    int have_seq;
    int protocol_recorded;
};

static inline long o3f_syscall6(long number, long a0, long a1, long a2, long a3, long a4, long a5) {
    register long x0 asm("x0") = a0;
    register long x1 asm("x1") = a1;
    register long x2 asm("x2") = a2;
    register long x3 asm("x3") = a3;
    register long x4 asm("x4") = a4;
    register long x5 asm("x5") = a5;
    register long x8 asm("x8") = number;
    asm volatile(
        "svc #0"
        : "+r"(x0)
        : "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5), "r"(x8)
        : "memory"
    );
    return x0;
}

static inline long o3f_syscall5(long number, long a0, long a1, long a2, long a3, long a4) {
    return o3f_syscall6(number, a0, a1, a2, a3, a4, 0);
}

static inline long o3f_syscall4(long number, long a0, long a1, long a2, long a3) {
    return o3f_syscall6(number, a0, a1, a2, a3, 0, 0);
}

static inline long o3f_syscall3(long number, long a0, long a1, long a2) {
    return o3f_syscall6(number, a0, a1, a2, 0, 0, 0);
}

static inline long o3f_syscall2(long number, long a0, long a1) {
    return o3f_syscall6(number, a0, a1, 0, 0, 0, 0);
}

static long o3f_open(const char *path, int flags, unsigned int mode) {
    return o3f_syscall4(NR_OPENAT, AT_FDCWD, (long)(uintptr_t)path, flags, mode);
}

static long o3f_close(int fd) {
    return o3f_syscall2(NR_CLOSE, fd, 0);
}

static long o3f_read(int fd, void *buffer, size_t size) {
    return o3f_syscall3(NR_READ, fd, (long)(uintptr_t)buffer, (long)size);
}

static long o3f_write(int fd, const void *buffer, size_t size) {
    return o3f_syscall3(NR_WRITE, fd, (long)(uintptr_t)buffer, (long)size);
}

static long o3f_mkdir(const char *path, unsigned int mode) {
    return o3f_syscall3(NR_MKDIRAT, AT_FDCWD, (long)(uintptr_t)path, mode);
}

static long o3f_mknod(const char *path, unsigned int mode, uint64_t device) {
    return o3f_syscall4(NR_MKNODAT, AT_FDCWD, (long)(uintptr_t)path, mode, (long)device);
}

static long o3f_unlink(const char *path) {
    return o3f_syscall3(NR_UNLINKAT, AT_FDCWD, (long)(uintptr_t)path, 0);
}

static long o3f_symlink(const char *target, const char *path) {
    return o3f_syscall3(NR_SYMLINKAT, (long)(uintptr_t)target, AT_FDCWD, (long)(uintptr_t)path);
}

static long o3f_mount(
    const char *source,
    const char *target,
    const char *type,
    unsigned long flags,
    const char *data
) {
    return o3f_syscall5(
        NR_MOUNT,
        (long)(uintptr_t)source,
        (long)(uintptr_t)target,
        (long)(uintptr_t)type,
        (long)flags,
        (long)(uintptr_t)data
    );
}

static long o3f_finit_module(int fd, const char *params) {
    return o3f_syscall3(NR_FINIT_MODULE, fd, (long)(uintptr_t)params, 0);
}

static long o3f_stat(const char *path) {
    uint64_t words[32];
    return o3f_syscall4(
        NR_NEWFSTATAT,
        AT_FDCWD,
        (long)(uintptr_t)path,
        (long)(uintptr_t)&words[0],
        0
    );
}

static long o3f_sleep_ms(long milliseconds) {
    struct timespec64 request = {
        .tv_sec = milliseconds / 1000,
        .tv_nsec = (milliseconds % 1000) * 1000000,
    };
    return o3f_syscall2(NR_NANOSLEEP, (long)(uintptr_t)&request, 0);
}

void *memset(void *destination, int value, size_t size) {
    unsigned char *output = (unsigned char *)destination;
    size_t index;
    for (index = 0; index < size; ++index) {
        output[index] = (unsigned char)value;
    }
    return destination;
}

void *memcpy(void *destination, const void *source, size_t size) {
    unsigned char *output = (unsigned char *)destination;
    const unsigned char *input = (const unsigned char *)source;
    size_t index;
    for (index = 0; index < size; ++index) {
        output[index] = input[index];
    }
    return destination;
}

static size_t o3f_strlen(const char *text) {
    size_t length = 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
}

static int o3f_streq(const char *left, const char *right) {
    size_t index = 0;
    while (left[index] != '\0' && right[index] != '\0') {
        if (left[index] != right[index]) {
            return 0;
        }
        ++index;
    }
    return left[index] == right[index];
}

static int o3f_bytes_equal(const uint8_t *left, size_t left_size, const char *right) {
    size_t right_size = o3f_strlen(right);
    size_t index;
    if (left_size != right_size) {
        return 0;
    }
    for (index = 0; index < left_size; ++index) {
        if (left[index] != (uint8_t)right[index]) {
            return 0;
        }
    }
    return 1;
}

static void o3f_copy(char *destination, size_t capacity, const char *source) {
    size_t index = 0;
    if (capacity == 0) {
        return;
    }
    while (index + 1 < capacity && source[index] != '\0') {
        destination[index] = source[index];
        ++index;
    }
    destination[index] = '\0';
}

static void o3f_move_left(uint8_t *buffer, size_t total, size_t consumed) {
    size_t index;
    if (consumed >= total) {
        return;
    }
    for (index = consumed; index < total; ++index) {
        buffer[index - consumed] = buffer[index];
    }
}

static void o3f_sb_putc(struct o3f_sbuf *buffer, char value) {
    if (buffer->length + 1 >= sizeof(buffer->data)) {
        buffer->truncated = 1;
        return;
    }
    buffer->data[buffer->length++] = value;
    buffer->data[buffer->length] = '\0';
}

static void o3f_sb_puts(struct o3f_sbuf *buffer, const char *text) {
    size_t index;
    for (index = 0; text[index] != '\0'; ++index) {
        o3f_sb_putc(buffer, text[index]);
    }
}

static void o3f_sb_put_u64(struct o3f_sbuf *buffer, uint64_t value) {
    char digits[32];
    size_t count = 0;
    if (value == 0) {
        o3f_sb_putc(buffer, '0');
        return;
    }
    while (value != 0 && count < sizeof(digits)) {
        digits[count++] = (char)('0' + value % 10U);
        value /= 10U;
    }
    while (count != 0) {
        o3f_sb_putc(buffer, digits[--count]);
    }
}

static void o3f_sb_put_i64(struct o3f_sbuf *buffer, int64_t value) {
    if (value < 0) {
        o3f_sb_putc(buffer, '-');
        o3f_sb_put_u64(buffer, (uint64_t)(-(value + 1)) + 1U);
    } else {
        o3f_sb_put_u64(buffer, (uint64_t)value);
    }
}

static void o3f_sb_put_hex(struct o3f_sbuf *buffer, uint64_t value) {
    static const char digits[] = "0123456789abcdef";
    char output[16];
    size_t count = 0;
    o3f_sb_puts(buffer, "0x");
    if (value == 0) {
        o3f_sb_putc(buffer, '0');
        return;
    }
    while (value != 0 && count < sizeof(output)) {
        output[count++] = digits[value & 0xfU];
        value >>= 4;
    }
    while (count != 0) {
        o3f_sb_putc(buffer, output[--count]);
    }
}

static long o3f_write_all(int fd, const void *data, size_t size) {
    const uint8_t *bytes = (const uint8_t *)data;
    size_t offset = 0;
    unsigned int stalls = 0;
    while (offset < size) {
        long amount = o3f_write(fd, bytes + offset, size - offset);
        if (amount > 0) {
            offset += (size_t)amount;
            stalls = 0;
            continue;
        }
        if (amount == -EINTR) {
            continue;
        }
        if (amount == -EAGAIN && stalls++ < 2000U) {
            (void)o3f_sleep_ms(1);
            continue;
        }
        return amount == 0 ? -EINVAL : amount;
    }
    return 0;
}

static void o3f_emit_path(const char *path, const char *text, size_t size) {
    long fd = o3f_open(path, O_WRONLY | O_NONBLOCK | O_CLOEXEC, 0);
    if (fd >= 0) {
        (void)o3f_write_all((int)fd, text, size);
        (void)o3f_close((int)fd);
    }
}

static void o3f_emit(const char *text) {
    size_t size = o3f_strlen(text);
    o3f_emit_path("/dev/kmsg", text, size);
    o3f_emit_path("/dev/pmsg0", text, size);
    o3f_emit_path("/dev/console", text, size);
}

static void o3f_emit_buffer(const struct o3f_sbuf *buffer) {
    o3f_emit_path("/dev/kmsg", buffer->data, buffer->length);
    o3f_emit_path("/dev/pmsg0", buffer->data, buffer->length);
    o3f_emit_path("/dev/console", buffer->data, buffer->length);
}

static uint64_t o3f_make_dev(unsigned int major_number, unsigned int minor_number) {
    return ((uint64_t)(minor_number & 0xffU)) |
           ((uint64_t)(major_number & 0xfffU) << 8) |
           ((uint64_t)(minor_number & ~0xffU) << 12) |
           ((uint64_t)(major_number & ~0xfffU) << 32);
}

static void o3f_mkdir_ok(const char *path, unsigned int mode) {
    long rc = o3f_mkdir(path, mode);
    (void)rc;
}

static void o3f_mkdir_p(const char *path, unsigned int mode) {
    char temporary[256];
    size_t length = o3f_strlen(path);
    size_t index;
    if (length == 0 || length >= sizeof(temporary)) {
        return;
    }
    o3f_copy(temporary, sizeof(temporary), path);
    for (index = 1; temporary[index] != '\0'; ++index) {
        if (temporary[index] == '/') {
            temporary[index] = '\0';
            o3f_mkdir_ok(temporary, mode);
            temporary[index] = '/';
        }
    }
    o3f_mkdir_ok(temporary, mode);
}

static void o3f_ensure_chr(
    const char *path,
    unsigned int mode,
    unsigned int major_number,
    unsigned int minor_number
) {
    (void)o3f_unlink(path);
    (void)o3f_mknod(path, S_IFCHR | mode, o3f_make_dev(major_number, minor_number));
}

static long o3f_mount_once(
    const char *source,
    const char *target,
    const char *type,
    unsigned long flags,
    const char *data
) {
    long rc = o3f_mount(source, target, type, flags, data);
    return rc == -EBUSY ? 0 : rc;
}

static void o3f_early_marker(void) {
    o3f_mkdir_ok("/dev", 0755);
    o3f_ensure_chr("/dev/kmsg", 0600, 1, 11);
    o3f_ensure_chr("/dev/pmsg0", 0220, 1, 12);
    o3f_emit(O3F_MARKER " phase=entry-pre-mount runtime=freestanding raw_syscalls=1\n");
}

static int o3f_setup_filesystems(struct o3f_state *state) {
    o3f_mkdir_p("/proc", 0755);
    o3f_mkdir_p("/sys", 0755);
    o3f_mkdir_p("/dev", 0755);
    o3f_mkdir_p("/config", 0755);
    state->proc_mount_rc = o3f_mount_once(
        "proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, ""
    );
    state->sys_mount_rc = o3f_mount_once(
        "sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, ""
    );
    state->dev_mount_rc = o3f_mount_once("devtmpfs", "/dev", "devtmpfs", MS_NOSUID, "mode=0755");
    if (state->dev_mount_rc != 0) {
        state->dev_mount_rc = o3f_mount_once("tmpfs", "/dev", "tmpfs", MS_NOSUID, "mode=0755");
    }
    o3f_ensure_chr("/dev/kmsg", 0600, 1, 11);
    o3f_ensure_chr("/dev/pmsg0", 0220, 1, 12);
    o3f_ensure_chr("/dev/console", 0600, 5, 1);
    o3f_ensure_chr("/dev/null", 0666, 1, 3);
    o3f_ensure_chr("/dev/zero", 0666, 1, 5);
    {
        struct o3f_sbuf output = {{0}, 0, 0};
        o3f_sb_puts(&output, O3F_MARKER " phase=mounts proc_rc=");
        o3f_sb_put_i64(&output, state->proc_mount_rc);
        o3f_sb_puts(&output, " sys_rc=");
        o3f_sb_put_i64(&output, state->sys_mount_rc);
        o3f_sb_puts(&output, " dev_rc=");
        o3f_sb_put_i64(&output, state->dev_mount_rc);
        o3f_sb_putc(&output, '\n');
        o3f_emit_buffer(&output);
    }
    return state->proc_mount_rc == 0 && state->sys_mount_rc == 0 && state->dev_mount_rc == 0 ? 0 : -1;
}

__attribute__((noreturn)) static void o3f_park(const char *phase, long rc) {
    struct o3f_sbuf output = {{0}, 0, 0};
    o3f_sb_puts(&output, O3F_MARKER " phase=");
    o3f_sb_puts(&output, phase);
    o3f_sb_puts(&output, " result=fail rc=");
    o3f_sb_put_i64(&output, rc);
    o3f_sb_puts(&output, " action=park\n");
    o3f_emit_buffer(&output);
    for (;;) {
        (void)o3f_sleep_ms(10000);
        asm volatile("wfe" ::: "memory");
    }
}

static int o3f_module_filename_valid(const char *filename) {
    size_t length = o3f_strlen(filename);
    size_t index;
    if (length <= 3 || filename[length - 3] != '.' || filename[length - 2] != 'k' ||
        filename[length - 1] != 'o') {
        return 0;
    }
    for (index = 0; index < length; ++index) {
        if (filename[index] == '/') {
            return 0;
        }
        if (filename[index] == '.' && filename[index + 1] == '.') {
            return 0;
        }
    }
    return 1;
}

static long o3f_module_open(void *context, const char *filename) {
    char path[256];
    size_t prefix_size = sizeof(O3F_MODULE_DIR) - 1U;
    size_t filename_size;
    size_t index;
    (void)context;
    if (!o3f_module_filename_valid(filename)) {
        return -EINVAL;
    }
    filename_size = o3f_strlen(filename);
    if (prefix_size + filename_size + 1U > sizeof(path)) {
        return -ENAMETOOLONG;
    }
    for (index = 0; index < prefix_size; ++index) {
        path[index] = O3F_MODULE_DIR[index];
    }
    for (index = 0; index < filename_size; ++index) {
        path[prefix_size + index] = filename[index];
    }
    path[prefix_size + filename_size] = '\0';
    return o3f_open(path, O_RDONLY | O_CLOEXEC, 0);
}

static long o3f_module_finit(void *context, int fd, const char *params) {
    (void)context;
    return o3f_finit_module(fd, params);
}

static long o3f_module_close(void *context, int fd) {
    (void)context;
    return o3f_close(fd);
}

struct o3f_reader_context {
    int fd;
};

static long o3f_reader_read(void *context, void *buffer, size_t size) {
    struct o3f_reader_context *reader = (struct o3f_reader_context *)context;
    long amount;
    do {
        amount = o3f_read(reader->fd, buffer, size);
    } while (amount == -EINTR);
    return amount;
}

static int o3f_path_present(void *context, const char *path) {
    long rc;
    (void)context;
    rc = o3f_stat(path);
    if (rc == 0) {
        return 1;
    }
    if (rc == -ENOENT) {
        return 0;
    }
    return (int)rc;
}

static void o3f_emit_load(const struct o3f_state *state, int rc) {
    struct o3f_sbuf output = {{0}, 0, 0};
    o3f_sb_puts(&output, O3F_MARKER " phase=module-plan rc=");
    o3f_sb_put_i64(&output, rc);
    o3f_sb_puts(&output, " attempted=");
    o3f_sb_put_u64(&output, state->load.attempted);
    o3f_sb_puts(&output, " loaded=");
    o3f_sb_put_u64(&output, state->load.loaded);
    o3f_sb_puts(&output, " eexist=");
    o3f_sb_put_u64(&output, state->load.already_loaded);
    o3f_sb_puts(&output, " failed=");
    o3f_sb_put_u64(&output, state->load.failed);
    o3f_sb_puts(&output, " first=");
    o3f_sb_put_u64(&output, state->load.first_failure_index);
    o3f_sb_puts(&output, " first_rc=");
    o3f_sb_put_i64(&output, state->load.first_failure_rc);
    o3f_sb_putc(&output, '\n');
    o3f_emit_buffer(&output);
}

static int o3f_load_and_verify_modules(struct o3f_state *state) {
    struct s22plus_o2_module_loader_ops loader = {
        .context = NULL,
        .open_module = o3f_module_open,
        .finit_module = o3f_module_finit,
        .close_module = o3f_module_close,
    };
    const char *runtime_names[S22PLUS_O2_MODULE_PLAN_COUNT];
    unsigned char found[S22PLUS_O2_MODULE_PLAN_COUNT];
    struct o3f_reader_context context;
    struct s22plus_o2_reader reader;
    size_t index;
    long proc_fd;
    int rc = s22plus_o2_execute_module_plan(
        s22plus_o2_module_plan,
        S22PLUS_O2_MODULE_PLAN_COUNT,
        &loader,
        &state->load
    );
    o3f_emit_load(state, rc);
    if (rc != S22PLUS_O2_OK) {
        return rc;
    }
    for (index = 0; index < S22PLUS_O2_MODULE_PLAN_COUNT; ++index) {
        runtime_names[index] = s22plus_o2_module_plan[index].runtime_name;
    }
    proc_fd = o3f_open("/proc/modules", O_RDONLY | O_CLOEXEC, 0);
    if (proc_fd < 0) {
        return (int)proc_fd;
    }
    context.fd = (int)proc_fd;
    reader.context = &context;
    reader.read = o3f_reader_read;
    state->registration_rc = s22plus_o2_scan_proc_modules(
        &reader,
        runtime_names,
        S22PLUS_O2_MODULE_PLAN_COUNT,
        found,
        &state->scan
    );
    (void)o3f_close((int)proc_fd);
    {
        struct o3f_sbuf output = {{0}, 0, 0};
        o3f_sb_puts(&output, O3F_MARKER " phase=proc-modules rc=");
        o3f_sb_put_i64(&output, state->registration_rc);
        o3f_sb_puts(&output, " eof=");
        o3f_sb_put_i64(&output, state->scan.eof_seen);
        o3f_sb_puts(&output, " found=");
        o3f_sb_put_u64(&output, state->scan.found_count);
        o3f_sb_puts(&output, " bytes=");
        o3f_sb_put_u64(&output, state->scan.bytes_read);
        o3f_sb_putc(&output, '\n');
        o3f_emit_buffer(&output);
    }
    if (state->registration_rc != S22PLUS_O2_OK || !state->scan.eof_seen ||
        state->scan.found_count != S22PLUS_O2_MODULE_PLAN_COUNT) {
        return state->registration_rc != 0 ? state->registration_rc : -1;
    }
    return 0;
}

static int o3f_wait_gates(struct o3f_state *state) {
    struct s22plus_o2_gate_ops ops = {.context = NULL, .path_present = o3f_path_present};
    size_t prefix;
    for (prefix = 1; prefix <= S22PLUS_O2_BIND_GATE_COUNT; ++prefix) {
        unsigned int attempt;
        int passed = 0;
        for (attempt = 0; attempt < O3F_GATE_ATTEMPTS; ++attempt) {
            struct s22plus_o2_gate_result result;
            int rc = s22plus_o2_check_bind_gates(s22plus_o2_bind_gates, prefix, &ops, &result);
            if (rc == S22PLUS_O2_OK) {
                passed = 1;
                break;
            }
            if (rc < 0 || result.first_missing_index + 1U < prefix) {
                return rc < 0 ? rc : -1;
            }
            (void)o3f_sleep_ms(O3F_GATE_SLEEP_MS);
        }
        if (!passed) {
            return -ETIMEDOUT;
        }
        state->gate_mask |= UINT64_C(1) << (prefix - 1U);
        {
            struct o3f_sbuf output = {{0}, 0, 0};
            o3f_sb_puts(&output, O3F_MARKER " phase=gate-pass index=");
            o3f_sb_put_u64(&output, prefix - 1U);
            o3f_sb_puts(&output, " id=");
            o3f_sb_puts(&output, s22plus_o2_bind_gates[prefix - 1U].id);
            o3f_sb_putc(&output, '\n');
            o3f_emit_buffer(&output);
        }
    }
    return 0;
}

static long o3f_write_attr(const char *path, const char *value) {
    long fd = o3f_open(path, O_WRONLY | O_CLOEXEC, 0);
    long rc;
    if (fd < 0) {
        return fd;
    }
    rc = o3f_write_all((int)fd, value, o3f_strlen(value));
    (void)o3f_close((int)fd);
    return rc;
}

static long o3f_read_trim(const char *path, char *buffer, size_t capacity) {
    long fd;
    long amount;
    if (capacity < 2U) {
        return -EINVAL;
    }
    fd = o3f_open(path, O_RDONLY | O_CLOEXEC, 0);
    if (fd < 0) {
        return fd;
    }
    do {
        amount = o3f_read((int)fd, buffer, capacity - 1U);
    } while (amount == -EINTR);
    (void)o3f_close((int)fd);
    if (amount < 0) {
        return amount;
    }
    buffer[amount] = '\0';
    while (amount > 0 && (buffer[amount - 1] == '\n' || buffer[amount - 1] == '\r' ||
                          buffer[amount - 1] == ' ' || buffer[amount - 1] == '\t')) {
        buffer[--amount] = '\0';
    }
    return amount;
}

static int o3f_parse_device_numbers(
    const char *text,
    unsigned int *major_number,
    unsigned int *minor_number
) {
    unsigned int major_value = 0;
    unsigned int minor_value = 0;
    size_t index = 0;
    if (text[index] < '0' || text[index] > '9') {
        return 0;
    }
    while (text[index] >= '0' && text[index] <= '9') {
        major_value = major_value * 10U + (unsigned int)(text[index++] - '0');
    }
    if (text[index++] != ':' || text[index] < '0' || text[index] > '9') {
        return 0;
    }
    while (text[index] >= '0' && text[index] <= '9') {
        minor_value = minor_value * 10U + (unsigned int)(text[index++] - '0');
    }
    if (text[index] != '\0') {
        return 0;
    }
    *major_number = major_value;
    *minor_number = minor_value;
    return 1;
}

static void o3f_materialize_ttygs0(void) {
    char value[64];
    unsigned int major_number;
    unsigned int minor_number;
    if (o3f_read_trim("/sys/class/tty/ttyGS0/dev", value, sizeof(value)) >= 0 &&
        o3f_parse_device_numbers(value, &major_number, &minor_number)) {
        o3f_ensure_chr("/dev/ttyGS0", 0600, major_number, minor_number);
    }
}

static int o3f_create_gadget(struct o3f_state *state) {
    static const char *const paths[] = {
        "/config/usb_gadget",
        "/config/usb_gadget/g1",
        "/config/usb_gadget/g1/strings",
        "/config/usb_gadget/g1/strings/0x409",
        "/config/usb_gadget/g1/configs",
        "/config/usb_gadget/g1/configs/c.1",
        "/config/usb_gadget/g1/configs/c.1/strings",
        "/config/usb_gadget/g1/configs/c.1/strings/0x409",
        "/config/usb_gadget/g1/functions",
        "/config/usb_gadget/g1/functions/acm.usb0",
    };
    struct attribute {
        const char *path;
        const char *value;
    };
    static const struct attribute attributes[] = {
        {"/config/usb_gadget/g1/idVendor", "0x04e8"},
        {"/config/usb_gadget/g1/idProduct", "0x6861"},
        {"/config/usb_gadget/g1/bcdUSB", "0x0200"},
        {"/config/usb_gadget/g1/bcdDevice", "0x0002"},
        {"/config/usb_gadget/g1/strings/0x409/serialnumber", "S22O3FACM01"},
        {"/config/usb_gadget/g1/strings/0x409/manufacturer", "S22 Native"},
        {"/config/usb_gadget/g1/strings/0x409/product", "S22 O3F Freestanding ACM"},
        {"/config/usb_gadget/g1/configs/c.1/MaxPower", "500"},
        {"/config/usb_gadget/g1/configs/c.1/bmAttributes", "0x80"},
        {"/config/usb_gadget/g1/configs/c.1/strings/0x409/configuration", "acm"},
    };
    size_t index;
    long rc;
    state->configfs_rc = o3f_mount_once(
        "configfs", "/config", "configfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, ""
    );
    if (state->configfs_rc != 0) {
        return (int)state->configfs_rc;
    }
    for (index = 0; index < sizeof(paths) / sizeof(paths[0]); ++index) {
        o3f_mkdir_p(paths[index], 0755);
        if (o3f_stat(paths[index]) != 0) {
            return -1;
        }
    }
    for (index = 0; index < sizeof(attributes) / sizeof(attributes[0]); ++index) {
        rc = o3f_write_attr(attributes[index].path, attributes[index].value);
        if (rc != 0) {
            return (int)rc;
        }
    }
    rc = o3f_symlink("../../functions/acm.usb0", "/config/usb_gadget/g1/configs/c.1/f1");
    if (rc != 0 && rc != -EEXIST) {
        return (int)rc;
    }
    state->mode_write_rc = o3f_write_attr(
        "/sys/devices/platform/soc/a600000.ssusb/mode", "peripheral"
    );
    if (state->mode_write_rc != 0) {
        return (int)state->mode_write_rc;
    }
    {
        char value[128];
        state->mode_readback_ok = o3f_read_trim(
            "/sys/devices/platform/soc/a600000.ssusb/mode", value, sizeof(value)
        ) >= 0 && o3f_streq(value, "peripheral");
    }
    if (!state->mode_readback_ok) {
        return -1;
    }
    state->udc_bind_rc = o3f_write_attr("/config/usb_gadget/g1/UDC", "a600000.dwc3");
    if (state->udc_bind_rc != 0) {
        return (int)state->udc_bind_rc;
    }
    {
        char value[128];
        state->udc_readback_ok = o3f_read_trim(
            "/config/usb_gadget/g1/UDC", value, sizeof(value)
        ) >= 0 && o3f_streq(value, "a600000.dwc3");
    }
    if (!state->udc_readback_ok) {
        return -1;
    }
    for (index = 0; index < O3F_TTY_ATTEMPTS; ++index) {
        if (o3f_stat("/dev/ttyGS0") != 0) {
            o3f_materialize_ttygs0();
        }
        if (o3f_stat("/dev/ttyGS0") == 0) {
            state->tty_ready = 1;
            return 0;
        }
        (void)o3f_sleep_ms(O3F_GATE_SLEEP_MS);
    }
    return -ETIMEDOUT;
}

static size_t o3f_build_status(struct o3f_state *state, uint8_t *payload) {
    struct o3f_sbuf output = {{0}, 0, 0};
    const char *protocol_result =
        state->protocol_recorded && state->invalid == 0 && state->crc_errors == 0 && state->seq_errors == 0
            ? "pass"
            : "pending";
#define O3F_STATUS_TEXT(key, value) o3f_sb_puts(&output, key "=" value "\n")
#define O3F_STATUS_I64(key, value) do { o3f_sb_puts(&output, key "="); o3f_sb_put_i64(&output, (int64_t)(value)); o3f_sb_putc(&output, '\n'); } while (0)
#define O3F_STATUS_U64(key, value) do { o3f_sb_puts(&output, key "="); o3f_sb_put_u64(&output, (uint64_t)(value)); o3f_sb_putc(&output, '\n'); } while (0)
    O3F_STATUS_TEXT("marker", O3F_MARKER);
    O3F_STATUS_TEXT("version", O3F_VERSION);
    O3F_STATUS_TEXT("phase", "control-ready");
    O3F_STATUS_TEXT("result", "ready");
    O3F_STATUS_I64("rc", 0);
    O3F_STATUS_U64("plan_count", S22PLUS_O2_MODULE_PLAN_COUNT);
    O3F_STATUS_U64("module_attempted", state->load.attempted);
    O3F_STATUS_U64("module_loaded", state->load.loaded);
    O3F_STATUS_U64("module_eexist", state->load.already_loaded);
    O3F_STATUS_U64("module_failed", state->load.failed);
    O3F_STATUS_U64("module_first_failure_index", state->load.first_failure_index);
    O3F_STATUS_I64("module_first_failure_rc", state->load.first_failure_rc);
    O3F_STATUS_I64("proc_registration_rc", state->registration_rc);
    O3F_STATUS_I64("proc_eof", state->scan.eof_seen);
    O3F_STATUS_U64("proc_bytes", state->scan.bytes_read);
    O3F_STATUS_U64("proc_found", state->scan.found_count);
    o3f_sb_puts(&output, "gate_mask=");
    o3f_sb_put_hex(&output, state->gate_mask);
    o3f_sb_putc(&output, '\n');
    O3F_STATUS_U64("gate_count", S22PLUS_O2_BIND_GATE_COUNT);
    O3F_STATUS_I64("configfs_rc", state->configfs_rc);
    O3F_STATUS_I64("ssusb_mode_write_rc", state->mode_write_rc);
    O3F_STATUS_I64("ssusb_mode_readback_ok", state->mode_readback_ok);
    O3F_STATUS_I64("udc_bind_rc", state->udc_bind_rc);
    O3F_STATUS_I64("udc_readback_ok", state->udc_readback_ok);
    O3F_STATUS_I64("ttyGS0_ready", state->tty_ready);
    O3F_STATUS_TEXT("gadget_function", "acm.usb0");
    O3F_STATUS_TEXT("udc", "a600000.dwc3");
    o3f_sb_puts(&output, "protocol_result=");
    o3f_sb_puts(&output, protocol_result);
    o3f_sb_putc(&output, '\n');
    O3F_STATUS_U64("protocol_handled", state->handled);
    O3F_STATUS_U64("protocol_invalid", state->invalid);
    O3F_STATUS_U64("protocol_crc_errors", state->crc_errors);
    O3F_STATUS_U64("protocol_seq_errors", state->seq_errors);
    O3F_STATUS_U64("protocol_io_reopens", state->io_reopens);
#undef O3F_STATUS_U64
#undef O3F_STATUS_I64
#undef O3F_STATUS_TEXT
    if (output.truncated || output.length > S22PLUS_O3F_MAX_PAYLOAD) {
        return 0;
    }
    memcpy(payload, output.data, output.length);
    return output.length;
}

static void o3f_record_protocol_if_complete(struct o3f_state *state) {
    if (!state->protocol_recorded && state->handled == O3F_MAX_ECHO) {
        state->protocol_recorded = 1;
        o3f_emit(
            state->invalid == 0 && state->crc_errors == 0 && state->seq_errors == 0
                ? O3F_MARKER " phase=protocol-pass handled=128\n"
                : O3F_MARKER " phase=protocol-fail handled=128\n"
        );
    }
}

static int o3f_process_frame(
    struct o3f_state *state,
    int fd,
    const uint8_t *frame,
    size_t frame_size
) {
    struct s22plus_o3f_request_view request;
    uint8_t status_payload[S22PLUS_O3F_MAX_PAYLOAD];
    uint8_t response[S22PLUS_O3F_MAX_FRAME];
    const uint8_t *response_payload;
    size_t response_payload_size;
    size_t response_size;
    int validate_rc = s22plus_o3f_validate_request(frame, frame_size, &request);
    if (validate_rc != S22PLUS_O3F_FRAME_OK) {
        if (validate_rc == S22PLUS_O3F_FRAME_CRC) {
            ++state->crc_errors;
        } else {
            ++state->invalid;
        }
        return validate_rc;
    }
    if (state->have_seq && request.sequence != state->expected_seq) {
        ++state->seq_errors;
    }
    state->expected_seq = request.sequence + 1U;
    state->have_seq = 1;
    response_payload = request.payload;
    if (o3f_bytes_equal(request.payload, request.payload_length, O3F_STATUS_QUERY)) {
        response_payload_size = o3f_build_status(state, status_payload);
        response_payload = status_payload;
        ++state->status_queries;
        if (response_payload_size == 0) {
            ++state->invalid;
            return -1;
        }
    } else if (state->handled < O3F_MAX_ECHO) {
        response_payload = request.payload;
        response_payload_size = request.payload_length;
        ++state->handled;
    } else {
        static const uint8_t limit[] = "result=echo-limit\n";
        response_payload = limit;
        response_payload_size = sizeof(limit) - 1U;
        ++state->invalid;
    }
    response_size = s22plus_o3f_build_response(
        response,
        sizeof(response),
        request.sequence,
        response_payload,
        response_payload_size
    );
    if (response_size == 0 || o3f_write_all(fd, response, response_size) != 0) {
        return -1;
    }
    o3f_record_protocol_if_complete(state);
    return 0;
}

__attribute__((noreturn)) static void o3f_control_loop(struct o3f_state *state) {
    uint8_t receive[S22PLUS_O3F_MAX_FRAME * 2U];
    size_t receive_size = 0;
    unsigned int idle_ticks = 0;
    long fd = -1;
    o3f_emit(O3F_MARKER " phase=control-ready serial=S22O3FACM01 protocol=S2O0-v1\n");
    for (;;) {
        long amount;
        if (fd < 0) {
            fd = o3f_open("/dev/ttyGS0", O_RDWR | O_NOCTTY | O_NONBLOCK | O_CLOEXEC, 0);
            if (fd < 0) {
                ++state->io_reopens;
                if (idle_ticks++ >= O3F_IDLE_TICKS) {
                    o3f_park("control-open-timeout", fd);
                }
                (void)o3f_sleep_ms(10);
                continue;
            }
        }
        amount = o3f_read((int)fd, receive + receive_size, sizeof(receive) - receive_size);
        if (amount > 0) {
            receive_size += (size_t)amount;
            idle_ticks = 0;
            while (receive_size >= S22PLUS_O3F_HEADER_SIZE) {
                uint16_t payload_size = s22plus_o3f_load_le16(&receive[6]);
                size_t frame_size;
                if (payload_size > S22PLUS_O3F_MAX_PAYLOAD) {
                    ++state->invalid;
                    receive_size = 0;
                    break;
                }
                frame_size = S22PLUS_O3F_HEADER_SIZE + (size_t)payload_size;
                if (receive_size < frame_size) {
                    break;
                }
                (void)o3f_process_frame(state, (int)fd, receive, frame_size);
                o3f_move_left(receive, receive_size, frame_size);
                receive_size -= frame_size;
            }
            if (receive_size == sizeof(receive)) {
                ++state->invalid;
                receive_size = 0;
            }
            continue;
        }
        if (amount == -EINTR) {
            continue;
        }
        if (amount == -EAGAIN) {
            if (!state->protocol_recorded && idle_ticks++ >= O3F_IDLE_TICKS) {
                o3f_park("control-idle-timeout", -ETIMEDOUT);
            }
            (void)o3f_sleep_ms(10);
            continue;
        }
        if (amount == 0) {
            (void)o3f_close((int)fd);
            fd = -1;
            receive_size = 0;
            ++state->io_reopens;
            (void)o3f_sleep_ms(10);
            continue;
        }
        (void)o3f_close((int)fd);
        fd = -1;
        receive_size = 0;
        ++state->io_reopens;
        (void)o3f_sleep_ms(10);
    }
}

__attribute__((noreturn)) void _start(void) {
    struct o3f_state state;
    int rc;
    memset(&state, 0, sizeof(state));
    state.load.first_failure_index = S22PLUS_O2_MODULE_PLAN_COUNT;
    o3f_early_marker();
    if (o3f_setup_filesystems(&state) != 0) {
        o3f_park("filesystem-setup", -1);
    }
    o3f_emit(
        O3F_MARKER " version=" O3F_VERSION " pid1=direct runtime=freestanding "
        "raw_syscalls=1 plan_count=59 generic_acm=1 no_android_handoff=1\n"
    );
    rc = o3f_load_and_verify_modules(&state);
    if (rc != 0) {
        o3f_park("module-verification", rc);
    }
    rc = o3f_wait_gates(&state);
    if (rc != 0) {
        o3f_park("bind-gates", rc);
    }
    rc = o3f_create_gadget(&state);
    if (rc != 0) {
        o3f_park("generic-acm", rc);
    }
    o3f_control_loop(&state);
}
