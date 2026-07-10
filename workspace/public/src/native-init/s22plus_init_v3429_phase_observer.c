// SPDX-License-Identifier: MIT
/* S22+ V3429 direct-PID1 retained-ring phase observer. */

#include <stddef.h>
#include <stdint.h>

#include "s22plus_v3429_phase_observer.generated.h"

#define AT_FDCWD (-100L)
#define O_RDONLY 00000000
#define O_WRONLY 00000001
#define O_NONBLOCK 00004000
#define O_CLOEXEC 02000000
#define S_IFCHR 0020000
#define MS_NOSUID 2UL
#define MS_NODEV 4UL
#define MS_NOEXEC 8UL
#define EAGAIN 11L
#define EBUSY 16L
#define EEXIST 17L
#define EINTR 4L

#define NR_MKNODAT 33L
#define NR_MKDIRAT 34L
#define NR_MOUNT 40L
#define NR_OPENAT 56L
#define NR_CLOSE 57L
#define NR_READ 63L
#define NR_WRITE 64L
#define NR_READLINKAT 78L
#define NR_NANOSLEEP 101L
#define NR_FINIT_MODULE 273L
#define NR_EXIT_GROUP 94L

#define V3429_MODULE_PATH "/lib/modules/sec_log_buf.ko"
#define V3429_OSRELEASE_PATH "/proc/sys/kernel/osrelease"
#define V3429_PROC_MODULES_PATH "/proc/modules"
#define V3429_AP_KLOG_PATH "/proc/ap_klog"
#define V3429_LAST_KMSG_PATH "/proc/last_kmsg"
#define V3429_BIND_PATH "/sys/bus/platform/drivers/samsung,kernel_log_buf/8.samsung,kernel_log_buf"
#define V3429_FAIL_PREFIX "S22_V3429_PHASE_OBSERVER_FAIL " V3429_RAW_RUN_TOKEN " code="
#define V3429_READ_CHUNK 4096U
#define V3429_MODULES_MAX_BYTES (16U * 1024U * 1024U)
#define V3429_LINE_BYTES 512U
#define V3429_WAIT_ATTEMPTS 100U
#define V3429_WAIT_MS 100L

struct v3429_timespec {
    int64_t tv_sec;
    int64_t tv_nsec;
};

struct v3429_sha256 {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t block[64];
    size_t block_len;
};

struct v3429_snapshot_counts {
    size_t precheck_count;
    size_t final_count;
    size_t raw_run_count;
    size_t first_precheck;
    size_t first_final;
};

static uint8_t v3429_ring[V3429_RING_MAX_BYTES + 1U];

void *memcpy(void *destination, const void *source, size_t size) {
    uint8_t *output = (uint8_t *)destination;
    const uint8_t *input = (const uint8_t *)source;
    size_t index;
    for (index = 0; index < size; ++index) {
        output[index] = input[index];
    }
    return destination;
}

void *memset(void *destination, int value, size_t size) {
    uint8_t *output = (uint8_t *)destination;
    size_t index;
    for (index = 0; index < size; ++index) {
        output[index] = (uint8_t)value;
    }
    return destination;
}

static inline long v3429_syscall6(
    long number,
    long a0,
    long a1,
    long a2,
    long a3,
    long a4,
    long a5
) {
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

static inline long v3429_syscall5(long n, long a0, long a1, long a2, long a3, long a4) {
    return v3429_syscall6(n, a0, a1, a2, a3, a4, 0);
}

static inline long v3429_syscall4(long n, long a0, long a1, long a2, long a3) {
    return v3429_syscall6(n, a0, a1, a2, a3, 0, 0);
}

static inline long v3429_syscall3(long n, long a0, long a1, long a2) {
    return v3429_syscall6(n, a0, a1, a2, 0, 0, 0);
}

static inline long v3429_syscall2(long n, long a0, long a1) {
    return v3429_syscall6(n, a0, a1, 0, 0, 0, 0);
}

static long v3429_mkdir(const char *path, unsigned int mode) {
    return v3429_syscall3(NR_MKDIRAT, AT_FDCWD, (long)(uintptr_t)path, mode);
}

static uint64_t v3429_make_dev(unsigned int major_number, unsigned int minor_number) {
    return ((uint64_t)(minor_number & 0xffU)) |
           ((uint64_t)(major_number & 0xfffU) << 8) |
           ((uint64_t)(minor_number & ~0xffU) << 12) |
           ((uint64_t)(major_number & ~0xfffU) << 32);
}

static long v3429_mknod(
    const char *path,
    unsigned int mode,
    unsigned int major_number,
    unsigned int minor_number
) {
    return v3429_syscall4(
        NR_MKNODAT,
        AT_FDCWD,
        (long)(uintptr_t)path,
        S_IFCHR | mode,
        (long)v3429_make_dev(major_number, minor_number)
    );
}

static long v3429_mount(
    const char *source,
    const char *target,
    const char *type,
    unsigned long flags
) {
    return v3429_syscall5(
        NR_MOUNT,
        (long)(uintptr_t)source,
        (long)(uintptr_t)target,
        (long)(uintptr_t)type,
        (long)flags,
        (long)(uintptr_t)""
    );
}

static long v3429_open(const char *path, int flags) {
    return v3429_syscall4(NR_OPENAT, AT_FDCWD, (long)(uintptr_t)path, flags, 0);
}

static long v3429_close(int fd) {
    return v3429_syscall2(NR_CLOSE, fd, 0);
}

static long v3429_read(int fd, void *buffer, size_t size) {
    long amount;
    do {
        amount = v3429_syscall3(NR_READ, fd, (long)(uintptr_t)buffer, (long)size);
    } while (amount == -EINTR || amount == -EAGAIN);
    return amount;
}

static long v3429_write(int fd, const void *buffer, size_t size) {
    return v3429_syscall3(NR_WRITE, fd, (long)(uintptr_t)buffer, (long)size);
}

static long v3429_readlink(const char *path, char *buffer, size_t size) {
    return v3429_syscall4(
        NR_READLINKAT,
        AT_FDCWD,
        (long)(uintptr_t)path,
        (long)(uintptr_t)buffer,
        (long)size
    );
}

static long v3429_finit_module(int fd) {
    return v3429_syscall3(NR_FINIT_MODULE, fd, (long)(uintptr_t)"", 0);
}

static long v3429_sleep_ms(long milliseconds) {
    struct v3429_timespec request;
    request.tv_sec = milliseconds / 1000L;
    request.tv_nsec = (milliseconds % 1000L) * 1000000L;
    return v3429_syscall2(NR_NANOSLEEP, (long)(uintptr_t)&request, 0);
}

static size_t v3429_strlen(const char *text) {
    size_t length = 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
}

static int v3429_bytes_equal(const void *left, const void *right, size_t size) {
    const uint8_t *a = (const uint8_t *)left;
    const uint8_t *b = (const uint8_t *)right;
    size_t index;
    for (index = 0; index < size; ++index) {
        if (a[index] != b[index]) {
            return 0;
        }
    }
    return 1;
}

static uint32_t v3429_rotr(uint32_t value, unsigned int shift) {
    return (value >> shift) | (value << (32U - shift));
}

static uint32_t v3429_load32(const uint8_t *data) {
    return ((uint32_t)data[0] << 24) |
           ((uint32_t)data[1] << 16) |
           ((uint32_t)data[2] << 8) |
           (uint32_t)data[3];
}

static void v3429_store32(uint8_t *output, uint32_t value) {
    output[0] = (uint8_t)(value >> 24);
    output[1] = (uint8_t)(value >> 16);
    output[2] = (uint8_t)(value >> 8);
    output[3] = (uint8_t)value;
}

static void v3429_sha256_transform(struct v3429_sha256 *context, const uint8_t block[64]) {
    static const uint32_t constants[64] = {
        0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U,
        0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
        0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
        0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
        0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU,
        0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
        0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
        0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
        0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
        0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
        0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U,
        0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
        0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U,
        0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
        0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
        0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
    };
    uint32_t words[64];
    uint32_t a = context->state[0];
    uint32_t b = context->state[1];
    uint32_t c = context->state[2];
    uint32_t d = context->state[3];
    uint32_t e = context->state[4];
    uint32_t f = context->state[5];
    uint32_t g = context->state[6];
    uint32_t h = context->state[7];
    size_t index;

    for (index = 0; index < 16U; ++index) {
        words[index] = v3429_load32(block + index * 4U);
    }
    for (index = 16U; index < 64U; ++index) {
        uint32_t s0 = v3429_rotr(words[index - 15U], 7U) ^
                      v3429_rotr(words[index - 15U], 18U) ^
                      (words[index - 15U] >> 3U);
        uint32_t s1 = v3429_rotr(words[index - 2U], 17U) ^
                      v3429_rotr(words[index - 2U], 19U) ^
                      (words[index - 2U] >> 10U);
        words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
    }
    for (index = 0; index < 64U; ++index) {
        uint32_t sum1 = v3429_rotr(e, 6U) ^ v3429_rotr(e, 11U) ^ v3429_rotr(e, 25U);
        uint32_t choose = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + sum1 + choose + constants[index] + words[index];
        uint32_t sum0 = v3429_rotr(a, 2U) ^ v3429_rotr(a, 13U) ^ v3429_rotr(a, 22U);
        uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = sum0 + majority;
        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }
    context->state[0] += a;
    context->state[1] += b;
    context->state[2] += c;
    context->state[3] += d;
    context->state[4] += e;
    context->state[5] += f;
    context->state[6] += g;
    context->state[7] += h;
}

static void v3429_sha256_init(struct v3429_sha256 *context) {
    context->state[0] = 0x6a09e667U;
    context->state[1] = 0xbb67ae85U;
    context->state[2] = 0x3c6ef372U;
    context->state[3] = 0xa54ff53aU;
    context->state[4] = 0x510e527fU;
    context->state[5] = 0x9b05688cU;
    context->state[6] = 0x1f83d9abU;
    context->state[7] = 0x5be0cd19U;
    context->bit_count = 0;
    context->block_len = 0;
}

static void v3429_sha256_update(
    struct v3429_sha256 *context,
    const uint8_t *data,
    size_t size
) {
    context->bit_count += (uint64_t)size * 8U;
    while (size > 0U) {
        size_t available = sizeof(context->block) - context->block_len;
        size_t amount = size < available ? size : available;
        memcpy(context->block + context->block_len, data, amount);
        context->block_len += amount;
        data += amount;
        size -= amount;
        if (context->block_len == sizeof(context->block)) {
            v3429_sha256_transform(context, context->block);
            context->block_len = 0;
        }
    }
}

static void v3429_sha256_final(struct v3429_sha256 *context, uint8_t digest[32]) {
    uint8_t length[8];
    size_t index;
    context->block[context->block_len++] = 0x80U;
    if (context->block_len > 56U) {
        while (context->block_len < sizeof(context->block)) {
            context->block[context->block_len++] = 0;
        }
        v3429_sha256_transform(context, context->block);
        context->block_len = 0;
    }
    while (context->block_len < 56U) {
        context->block[context->block_len++] = 0;
    }
    for (index = 0; index < sizeof(length); ++index) {
        length[7U - index] = (uint8_t)(context->bit_count >> (index * 8U));
    }
    memcpy(context->block + 56U, length, sizeof(length));
    v3429_sha256_transform(context, context->block);
    for (index = 0; index < 8U; ++index) {
        v3429_store32(digest + index * 4U, context->state[index]);
    }
}

static int v3429_sha_selftest(void) {
    static const uint8_t expected[32] = {
        0xba, 0x78, 0x16, 0xbf, 0x8f, 0x01, 0xcf, 0xea,
        0x41, 0x41, 0x40, 0xde, 0x5d, 0xae, 0x22, 0x23,
        0xb0, 0x03, 0x61, 0xa3, 0x96, 0x17, 0x7a, 0x9c,
        0xb4, 0x10, 0xff, 0x61, 0xf2, 0x00, 0x15, 0xad,
    };
    struct v3429_sha256 context;
    uint8_t digest[32];
    v3429_sha256_init(&context);
    v3429_sha256_update(&context, (const uint8_t *)"abc", 3U);
    v3429_sha256_final(&context, digest);
    return v3429_bytes_equal(digest, expected, sizeof(expected));
}

static int v3429_verify_module_identity(void) {
    static const uint8_t expected_digest[32] = V3429_MODULE_SHA256_BYTES;
    struct v3429_sha256 context;
    uint8_t digest[32];
    uint8_t chunk[V3429_READ_CHUNK];
    uint64_t total = 0;
    long fd = v3429_open(V3429_MODULE_PATH, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return 0;
    }
    v3429_sha256_init(&context);
    for (;;) {
        long amount = v3429_read((int)fd, chunk, sizeof(chunk));
        if (amount < 0) {
            (void)v3429_close((int)fd);
            return 0;
        }
        if (amount == 0) {
            break;
        }
        total += (uint64_t)amount;
        if (total > V3429_MODULE_SIZE) {
            (void)v3429_close((int)fd);
            return 0;
        }
        v3429_sha256_update(&context, chunk, (size_t)amount);
    }
    if (v3429_close((int)fd) < 0 || total != V3429_MODULE_SIZE) {
        return 0;
    }
    v3429_sha256_final(&context, digest);
    return v3429_bytes_equal(digest, expected_digest, sizeof(digest));
}

static int v3429_verify_osrelease(void) {
    char buffer[128];
    size_t total = 0;
    size_t expected = v3429_strlen(V3429_KERNEL_OSRELEASE);
    long fd = v3429_open(V3429_OSRELEASE_PATH, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return 0;
    }
    for (;;) {
        long amount;
        if (total == sizeof(buffer)) {
            (void)v3429_close((int)fd);
            return 0;
        }
        amount = v3429_read((int)fd, buffer + total, sizeof(buffer) - total);
        if (amount < 0) {
            (void)v3429_close((int)fd);
            return 0;
        }
        if (amount == 0) {
            break;
        }
        total += (size_t)amount;
    }
    if (v3429_close((int)fd) < 0) {
        return 0;
    }
    if (total == expected + 1U && buffer[total - 1U] == '\n') {
        --total;
    }
    return total == expected &&
           v3429_bytes_equal(buffer, V3429_KERNEL_OSRELEASE, expected);
}

static int v3429_load_module(void) {
    long fd = v3429_open(V3429_MODULE_PATH, O_RDONLY | O_CLOEXEC);
    long load_rc;
    long close_rc;
    if (fd < 0) {
        return 0;
    }
    load_rc = v3429_finit_module((int)fd);
    close_rc = v3429_close((int)fd);
    return load_rc == 0 && close_rc == 0;
}

static int v3429_token_equal(
    const char *line,
    size_t start,
    size_t end,
    const char *expected
) {
    size_t expected_length = v3429_strlen(expected);
    return end - start == expected_length &&
           v3429_bytes_equal(line + start, expected, expected_length);
}

static int v3429_target_module_line(const char *line, size_t length) {
    size_t token_start[6];
    size_t token_end[6];
    size_t tokens = 0;
    size_t cursor = 0;
    while (cursor < length && tokens < 6U) {
        while (cursor < length && (line[cursor] == ' ' || line[cursor] == '\t')) {
            ++cursor;
        }
        if (cursor == length) {
            break;
        }
        token_start[tokens] = cursor;
        while (cursor < length && line[cursor] != ' ' && line[cursor] != '\t') {
            ++cursor;
        }
        token_end[tokens] = cursor;
        ++tokens;
    }
    if (tokens == 0U || !v3429_token_equal(line, token_start[0], token_end[0], "sec_log_buf")) {
        return 0;
    }
    if (tokens < 5U || !v3429_token_equal(line, token_start[4], token_end[4], "Live")) {
        return -1;
    }
    return 1;
}

static int v3429_verify_proc_modules(void) {
    uint8_t chunk[V3429_READ_CHUNK];
    char line[V3429_LINE_BYTES];
    size_t line_length = 0;
    int line_overflow = 0;
    uint64_t total = 0;
    size_t found = 0;
    long fd = v3429_open(V3429_PROC_MODULES_PATH, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return 0;
    }
    for (;;) {
        long amount = v3429_read((int)fd, chunk, sizeof(chunk));
        size_t index;
        if (amount < 0) {
            (void)v3429_close((int)fd);
            return 0;
        }
        if (amount == 0) {
            break;
        }
        total += (uint64_t)amount;
        if (total > V3429_MODULES_MAX_BYTES) {
            (void)v3429_close((int)fd);
            return 0;
        }
        for (index = 0; index < (size_t)amount; ++index) {
            uint8_t value = chunk[index];
            if (value == 0U) {
                (void)v3429_close((int)fd);
                return 0;
            }
            if (value == '\n') {
                int result = line_overflow ? 0 : v3429_target_module_line(line, line_length);
                if (result < 0) {
                    (void)v3429_close((int)fd);
                    return 0;
                }
                if (result > 0) {
                    ++found;
                }
                line_length = 0;
                line_overflow = 0;
            } else if (!line_overflow) {
                if (line_length < sizeof(line)) {
                    line[line_length++] = (char)value;
                } else {
                    line_overflow = 1;
                }
            }
        }
    }
    if (line_length != 0U || line_overflow) {
        int result = line_overflow ? 0 : v3429_target_module_line(line, line_length);
        if (result < 0) {
            (void)v3429_close((int)fd);
            return 0;
        }
        if (result > 0) {
            ++found;
        }
    }
    return v3429_close((int)fd) == 0 && found == 1U;
}

static int v3429_symlink_present(const char *path) {
    char target[512];
    long amount = v3429_readlink(path, target, sizeof(target));
    return amount > 0 && (size_t)amount < sizeof(target);
}

static int v3429_file_openable(const char *path) {
    long fd = v3429_open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return 0;
    }
    return v3429_close((int)fd) == 0;
}

static int v3429_wait_for_bind(void) {
    size_t attempt;
    for (attempt = 0; attempt < V3429_WAIT_ATTEMPTS; ++attempt) {
        if (v3429_symlink_present(V3429_BIND_PATH)) {
            return 1;
        }
        (void)v3429_sleep_ms(V3429_WAIT_MS);
    }
    return 0;
}

static int v3429_wait_for_proc_nodes(void) {
    size_t attempt;
    for (attempt = 0; attempt < V3429_WAIT_ATTEMPTS; ++attempt) {
        if (v3429_file_openable(V3429_AP_KLOG_PATH) &&
            v3429_file_openable(V3429_LAST_KMSG_PATH)) {
            return 1;
        }
        (void)v3429_sleep_ms(V3429_WAIT_MS);
    }
    return 0;
}

static size_t v3429_count_pattern(
    const uint8_t *buffer,
    size_t buffer_size,
    const char *pattern,
    size_t pattern_size,
    size_t *first_offset
) {
    size_t count = 0;
    size_t cursor = 0;
    *first_offset = (size_t)-1;
    if (pattern_size == 0U || buffer_size < pattern_size) {
        return 0;
    }
    while (cursor + pattern_size <= buffer_size) {
        if (v3429_bytes_equal(buffer + cursor, pattern, pattern_size)) {
            if (count == 0U) {
                *first_offset = cursor;
            }
            ++count;
            cursor += pattern_size;
        } else {
            ++cursor;
        }
    }
    return count;
}

static int v3429_read_snapshot(size_t *size_out) {
    size_t total = 0;
    long fd = v3429_open(V3429_AP_KLOG_PATH, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        return 0;
    }
    for (;;) {
        size_t available = V3429_RING_MAX_BYTES - total;
        long amount;
        if (available == 0U) {
            amount = v3429_read((int)fd, v3429_ring + total, 1U);
            if (amount != 0) {
                (void)v3429_close((int)fd);
                return 0;
            }
            break;
        }
        if (available > V3429_READ_CHUNK) {
            available = V3429_READ_CHUNK;
        }
        amount = v3429_read((int)fd, v3429_ring + total, available);
        if (amount < 0) {
            (void)v3429_close((int)fd);
            return 0;
        }
        if (amount == 0) {
            break;
        }
        total += (size_t)amount;
    }
    if (v3429_close((int)fd) < 0 || total == 0U) {
        return 0;
    }
    *size_out = total;
    return 1;
}

static int v3429_classify_snapshot(
    size_t expected_precheck,
    size_t expected_final,
    size_t expected_raw,
    int require_order
) {
    struct v3429_snapshot_counts counts;
    size_t snapshot_size;
    size_t ignored;
    if (!v3429_read_snapshot(&snapshot_size)) {
        return 0;
    }
    counts.precheck_count = v3429_count_pattern(
        v3429_ring,
        snapshot_size,
        V3429_PRECHECK_FRAME,
        V3429_PRECHECK_FRAME_LEN,
        &counts.first_precheck
    );
    counts.final_count = v3429_count_pattern(
        v3429_ring,
        snapshot_size,
        V3429_FINAL_FRAME,
        V3429_FINAL_FRAME_LEN,
        &counts.first_final
    );
    counts.raw_run_count = v3429_count_pattern(
        v3429_ring,
        snapshot_size,
        V3429_RAW_RUN_TOKEN,
        V3429_RAW_RUN_TOKEN_LEN,
        &ignored
    );
    if (counts.precheck_count != expected_precheck ||
        counts.final_count != expected_final ||
        counts.raw_run_count != expected_raw) {
        return 0;
    }
    if (require_order && counts.first_precheck >= counts.first_final) {
        return 0;
    }
    return 1;
}

static int v3429_emit_frame(const char *frame, size_t frame_size) {
    char output[384];
    long fd;
    long amount;
    if (frame_size + 1U > sizeof(output)) {
        return 0;
    }
    memcpy(output, frame, frame_size);
    output[frame_size] = '\n';
    fd = v3429_open("/dev/kmsg", O_WRONLY | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) {
        return 0;
    }
    amount = v3429_write((int)fd, output, frame_size + 1U);
    return v3429_close((int)fd) == 0 && amount == (long)(frame_size + 1U);
}

static size_t v3429_render_failure(
    char *output,
    size_t output_size,
    unsigned int code
) {
    size_t length = 0;
    char digits[16];
    size_t count = 0;
    size_t index;
    const char *prefix = V3429_FAIL_PREFIX;
    if (output == NULL || output_size == 0U) {
        return 0;
    }
    while (prefix[length] != '\0' && length < output_size) {
        output[length] = prefix[length];
        ++length;
    }
    if (prefix[length] != '\0') {
        return 0;
    }
    do {
        digits[count++] = (char)('0' + code % 10U);
        code /= 10U;
    } while (code != 0U && count < sizeof(digits));
    if (length + count + 1U > output_size) {
        return 0;
    }
    for (index = 0; index < count; ++index) {
        output[length++] = digits[count - 1U - index];
    }
    output[length++] = '\n';
    return length;
}

static void v3429_emit_failure(unsigned int code) {
    char output[128];
    size_t length = v3429_render_failure(output, sizeof(output), code);
    long fd;
    if (length == 0U) {
        return;
    }
    fd = v3429_open("/dev/kmsg", O_WRONLY | O_NONBLOCK | O_CLOEXEC);
    if (fd >= 0) {
        (void)v3429_write((int)fd, output, length);
        (void)v3429_close((int)fd);
    }
}

__attribute__((noreturn)) static void v3429_quiet_park(void) {
    for (;;) {
        (void)v3429_sleep_ms(1000L);
        asm volatile("wfe" ::: "memory");
    }
}

__attribute__((noreturn)) static void v3429_fail(unsigned int code) {
    v3429_emit_failure(code);
    v3429_quiet_park();
}

#if defined(V3429_SHA256_SELFTEST_ONLY)
__attribute__((noreturn)) void _start(void) {
    long status = v3429_sha_selftest() ? 0 : 1;
    (void)v3429_syscall2(NR_EXIT_GROUP, status, 0);
    for (;;) {
        asm volatile("wfe" ::: "memory");
    }
}
#elif defined(V3429_FAILURE_SELFTEST_ONLY)
__attribute__((noreturn)) void _start(void) {
    static const char expected[] = V3429_FAIL_PREFIX "18\n";
    char output[128];
    char too_small[64];
    size_t first_offset;
    size_t size = v3429_render_failure(output, sizeof(output), 18U);
    size_t short_size = v3429_render_failure(too_small, sizeof(too_small), 18U);
    size_t count = v3429_count_pattern(
        (const uint8_t *)output,
        size,
        V3429_RAW_RUN_TOKEN,
        V3429_RAW_RUN_TOKEN_LEN,
        &first_offset
    );
    int pass = size == sizeof(expected) - 1U &&
               short_size == 0U &&
               count == 1U &&
               first_offset != (size_t)-1 &&
               v3429_bytes_equal(output, expected, sizeof(expected) - 1U);
    (void)v3429_syscall2(NR_EXIT_GROUP, pass ? 0 : 1, 0);
    for (;;) {
        asm volatile("wfe" ::: "memory");
    }
}
#else
__attribute__((noreturn)) void _start(void) {
    long rc;

    if (!v3429_sha_selftest()) {
        v3429_fail(1U);
    }
    rc = v3429_mkdir("/dev", 0755);
    if (rc != 0 && rc != -EEXIST) {
        v3429_fail(2U);
    }
    rc = v3429_mknod("/dev/kmsg", 0600, 1U, 11U);
    if (rc != 0 && rc != -EEXIST) {
        v3429_fail(3U);
    }
    rc = v3429_mkdir("/proc", 0755);
    if (rc != 0 && rc != -EEXIST) {
        v3429_fail(4U);
    }
    rc = v3429_mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC);
    if (rc != 0 && rc != -EBUSY) {
        v3429_fail(5U);
    }
    rc = v3429_mkdir("/sys", 0755);
    if (rc != 0 && rc != -EEXIST) {
        v3429_fail(6U);
    }
    rc = v3429_mount("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC);
    if (rc != 0 && rc != -EBUSY) {
        v3429_fail(7U);
    }
    if (!v3429_verify_osrelease()) {
        v3429_fail(8U);
    }
    if (!v3429_verify_module_identity()) {
        v3429_fail(9U);
    }
    if (!v3429_load_module()) {
        v3429_fail(10U);
    }
    if (!v3429_verify_proc_modules()) {
        v3429_fail(11U);
    }
    if (!v3429_wait_for_bind()) {
        v3429_fail(12U);
    }
    if (!v3429_wait_for_proc_nodes()) {
        v3429_fail(13U);
    }
    if (!v3429_classify_snapshot(0U, 0U, 0U, 0)) {
        v3429_fail(14U);
    }
    if (!v3429_emit_frame(V3429_PRECHECK_FRAME, V3429_PRECHECK_FRAME_LEN)) {
        v3429_fail(15U);
    }
    if (!v3429_classify_snapshot(1U, 0U, 1U, 0)) {
        v3429_fail(16U);
    }
    if (!v3429_emit_frame(V3429_FINAL_FRAME, V3429_FINAL_FRAME_LEN)) {
        v3429_fail(17U);
    }
    if (!v3429_classify_snapshot(1U, 1U, 2U, 1)) {
        v3429_fail(18U);
    }
    v3429_quiet_park();
}
#endif
