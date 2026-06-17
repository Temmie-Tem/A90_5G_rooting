/*
 * V2630 ARM32 ioctl preload for ACDB SET-calibration payload capture.
 *
 * This is a measurement-only extension of the V2531 fake audio-cal ioctl shim.
 * It never opens the audio calibration device and never issues extra ioctls.  It always
 * fakes AUDIO_SET_CALIBRATION so the loader's SET path cannot reach the kernel,
 * while preserving and hashing the full SET argument and, when present, the
 * same-process dma-buf payload referenced by mem_handle.
 */

typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef unsigned char uint8_t;
typedef unsigned long uintptr_t;
typedef unsigned long size_t;
typedef unsigned long long uint64_t;

extern int *__errno(void);
extern char *getenv(const char *name);
extern void *mmap(void *addr, size_t length, int prot, int flags, int fd, long offset);
extern int munmap(void *addr, size_t length);

#define A90_TRACE_EVENTS_PATH "/data/local/tmp/a90-acdb-ownget/ioctl-trace-events.jsonl"
#define A90_SETCAL_EVENTS_PATH "/data/local/tmp/a90-acdb-ownget/setcal-events.jsonl"
#define A90_SETCAL_RAW_PREFIX "/data/local/tmp/a90-acdb-ownget/setcal-"

#define A90_AT_FDCWD (-100)
#define A90_O_WRONLY 00000001
#define A90_O_CREAT 00000100
#define A90_O_EXCL 00000200
#define A90_O_APPEND 00002000
#define A90_MODE_0600 0600

#define A90_NR_WRITE 4
#define A90_NR_CLOSE 6
#define A90_NR_GETPID 20
#define A90_NR_IOCTL 54
#define A90_NR_GETTID 224
#define A90_NR_OPENAT 322

#define A90_PROT_READ 1
#define A90_MAP_SHARED 1
#define A90_MAP_FAILED ((void *)-1L)

#define A90_AUDIO_ALLOCATE_CALIBRATION 0xc00461c8UL
#define A90_AUDIO_DEALLOCATE_CALIBRATION 0xc00461c9UL
#define A90_AUDIO_SET_CALIBRATION 0xc00461cbUL
#define A90_AUDIO_CAL_ARG_SAMPLE_BYTES 64U
#define A90_AUDIO_CAL_ARG_WORDS (A90_AUDIO_CAL_ARG_SAMPLE_BYTES / 4U)
#define A90_MAX_SET_ARG_BYTES 4096U
#define A90_MAX_DMABUF_BYTES 262144U
#define A90_FAKE_ALLOCATE_ENV "A90_ACDB_FAKE_ALLOCATE"

struct a90_arg_snapshot {
    int available;
    uint32_t requested_size;
    uint32_t sample_len;
    uint32_t words[A90_AUDIO_CAL_ARG_WORDS];
};

struct a90_setcal_header {
    int valid;
    uint32_t data_size;
    uint32_t version;
    uint32_t cal_type;
    uint32_t cal_type_size;
    uint32_t cal_hdr_version;
    uint32_t buffer_number;
    uint32_t cal_size;
    int32_t mem_handle;
};

static volatile uint32_t a90_setcal_sequence;

static long a90_syscall0(long nr)
{
    register long r0 asm("r0");
    register long r7 asm("r7") = nr;
    asm volatile("svc #0" : "=r"(r0) : "r"(r7) : "memory");
    return r0;
}

static long a90_syscall1(long nr, long a0)
{
    register long r0 asm("r0") = a0;
    register long r7 asm("r7") = nr;
    asm volatile("svc #0" : "+r"(r0) : "r"(r7) : "memory");
    return r0;
}

static long a90_syscall3(long nr, long a0, long a1, long a2)
{
    register long r0 asm("r0") = a0;
    register long r1 asm("r1") = a1;
    register long r2 asm("r2") = a2;
    register long r7 asm("r7") = nr;
    asm volatile("svc #0" : "+r"(r0) : "r"(r1), "r"(r2), "r"(r7) : "memory");
    return r0;
}

static long a90_syscall4(long nr, long a0, long a1, long a2, long a3)
{
    register long r0 asm("r0") = a0;
    register long r1 asm("r1") = a1;
    register long r2 asm("r2") = a2;
    register long r3 asm("r3") = a3;
    register long r7 asm("r7") = nr;
    asm volatile("svc #0" : "+r"(r0) : "r"(r1), "r"(r2), "r"(r3), "r"(r7) : "memory");
    return r0;
}

static int a90_open_append(const char *path)
{
    return (int)a90_syscall4(A90_NR_OPENAT, A90_AT_FDCWD, (long)path,
                             A90_O_WRONLY | A90_O_CREAT | A90_O_APPEND,
                             A90_MODE_0600);
}

static int a90_open_new(const char *path)
{
    return (int)a90_syscall4(A90_NR_OPENAT, A90_AT_FDCWD, (long)path,
                             A90_O_WRONLY | A90_O_CREAT | A90_O_EXCL,
                             A90_MODE_0600);
}

static void a90_close(int fd)
{
    if (fd >= 0)
        (void)a90_syscall1(A90_NR_CLOSE, fd);
}

static uint32_t a90_getpid(void)
{
    return (uint32_t)a90_syscall0(A90_NR_GETPID);
}

static uint32_t a90_gettid(void)
{
    return (uint32_t)a90_syscall0(A90_NR_GETTID);
}

static size_t a90_strlen(const char *s)
{
    size_t n = 0;
    while (s[n])
        n++;
    return n;
}

static int a90_streq(const char *a, const char *b)
{
    size_t i = 0;
    if (!a || !b)
        return 0;
    while (a[i] && b[i]) {
        if (a[i] != b[i])
            return 0;
        i++;
    }
    return a[i] == b[i];
}

static void a90_write_all(int fd, const void *buf, size_t len)
{
    const uint8_t *p = (const uint8_t *)buf;
    while (len > 0) {
        long rc = a90_syscall3(A90_NR_WRITE, fd, (long)p, (long)len);
        if (rc <= 0)
            return;
        p += (size_t)rc;
        len -= (size_t)rc;
    }
}

static void a90_write_str(int fd, const char *s)
{
    a90_write_all(fd, s, a90_strlen(s));
}

static void a90_write_dec(int fd, uint32_t value)
{
    char tmp[10];
    char out[10];
    uint32_t n = 0;
    uint32_t i = 0;
    if (value == 0) {
        a90_write_str(fd, "0");
        return;
    }
    while (value && n < sizeof(tmp)) {
        tmp[n++] = (char)('0' + (value % 10U));
        value /= 10U;
    }
    while (n)
        out[i++] = tmp[--n];
    a90_write_all(fd, out, i);
}

static void a90_write_sdec(int fd, int32_t value)
{
    uint32_t u;
    if (value < 0) {
        a90_write_str(fd, "-");
        u = (uint32_t)(0U - (uint32_t)value);
    } else {
        u = (uint32_t)value;
    }
    a90_write_dec(fd, u);
}

static void a90_write_hex32(int fd, uint32_t value)
{
    static const char h[] = "0123456789abcdef";
    char out[10];
    uint32_t i;
    out[0] = '0';
    out[1] = 'x';
    for (i = 0; i < 8; i++)
        out[2U + i] = h[(value >> (28U - (i * 4U))) & 0xfU];
    a90_write_all(fd, out, sizeof(out));
}

static void a90_write_hex_ptr(int fd, uintptr_t value)
{
    a90_write_hex32(fd, (uint32_t)value);
}

static void a90_hex8_raw(char *out, uint32_t value)
{
    static const char h[] = "0123456789abcdef";
    uint32_t i;
    for (i = 0; i < 8; i++)
        out[i] = h[(value >> (28U - (i * 4U))) & 0xfU];
}

static char *a90_append_str(char *p, const char *s)
{
    while (*s)
        *p++ = *s++;
    return p;
}

static char *a90_append_hex8_raw(char *p, uint32_t value)
{
    a90_hex8_raw(p, value);
    return p + 8;
}

struct a90_sha256 {
    uint32_t h[8];
    uint64_t bits;
    uint8_t block[64];
    uint32_t used;
};


static uint32_t a90_rotr(uint32_t x, uint32_t n)
{
    return (x >> n) | (x << (32U - n));
}

static uint32_t a90_load_be32(const uint8_t *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static void a90_store_be32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v >> 24);
    p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8);
    p[3] = (uint8_t)v;
}

static void a90_sha256_transform(struct a90_sha256 *ctx, const uint8_t *block)
{
    static const uint32_t k[64] = {
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
    uint32_t w[64];
    uint32_t a, b, c, d, e, f, g, h;
    uint32_t i;

    for (i = 0; i < 16; i++)
        w[i] = a90_load_be32(block + (i * 4U));
    for (i = 16; i < 64; i++) {
        uint32_t s0 = a90_rotr(w[i - 15], 7) ^ a90_rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = a90_rotr(w[i - 2], 17) ^ a90_rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }

    a = ctx->h[0];
    b = ctx->h[1];
    c = ctx->h[2];
    d = ctx->h[3];
    e = ctx->h[4];
    f = ctx->h[5];
    g = ctx->h[6];
    h = ctx->h[7];
    for (i = 0; i < 64; i++) {
        uint32_t s1 = a90_rotr(e, 6) ^ a90_rotr(e, 11) ^ a90_rotr(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + s1 + ch + k[i] + w[i];
        uint32_t s0 = a90_rotr(a, 2) ^ a90_rotr(a, 13) ^ a90_rotr(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = s0 + maj;
        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }
    ctx->h[0] += a;
    ctx->h[1] += b;
    ctx->h[2] += c;
    ctx->h[3] += d;
    ctx->h[4] += e;
    ctx->h[5] += f;
    ctx->h[6] += g;
    ctx->h[7] += h;
}

static void a90_sha256_init(struct a90_sha256 *ctx)
{
    uint32_t i;
    ctx->h[0] = 0x6a09e667U;
    ctx->h[1] = 0xbb67ae85U;
    ctx->h[2] = 0x3c6ef372U;
    ctx->h[3] = 0xa54ff53aU;
    ctx->h[4] = 0x510e527fU;
    ctx->h[5] = 0x9b05688cU;
    ctx->h[6] = 0x1f83d9abU;
    ctx->h[7] = 0x5be0cd19U;
    ctx->bits = 0;
    ctx->used = 0;
    for (i = 0; i < 64; i++)
        ctx->block[i] = 0;
}

static void a90_sha256_update(struct a90_sha256 *ctx, const uint8_t *data, uint32_t len)
{
    uint32_t i;
    ctx->bits += ((uint64_t)len) << 3;
    for (i = 0; i < len; i++) {
        ctx->block[ctx->used++] = data[i];
        if (ctx->used == 64) {
            a90_sha256_transform(ctx, ctx->block);
            ctx->used = 0;
        }
    }
}

static void a90_sha256_final(struct a90_sha256 *ctx, uint8_t out[32])
{
    uint32_t i;
    uint64_t bits = ctx->bits;
    ctx->block[ctx->used++] = 0x80U;
    if (ctx->used > 56) {
        while (ctx->used < 64)
            ctx->block[ctx->used++] = 0;
        a90_sha256_transform(ctx, ctx->block);
        ctx->used = 0;
    }
    while (ctx->used < 56)
        ctx->block[ctx->used++] = 0;
    for (i = 0; i < 8; i++)
        ctx->block[56 + i] = (uint8_t)(bits >> (56U - (i * 8U)));
    a90_sha256_transform(ctx, ctx->block);
    for (i = 0; i < 8; i++)
        a90_store_be32(out + (i * 4U), ctx->h[i]);
}

static void a90_hex32(char out[8], uint32_t v)
{
    static const char hex[] = "0123456789abcdef";
    int i;
    for (i = 7; i >= 0; i--) {
        out[i] = hex[v & 0xfU];
        v >>= 4;
    }
}

static void a90_sha_hex(char out[64], const uint8_t digest[32])
{
    static const char hex[] = "0123456789abcdef";
    uint32_t i;
    for (i = 0; i < 32; i++) {
        out[i * 2U] = hex[(digest[i] >> 4) & 0xfU];
        out[i * 2U + 1U] = hex[digest[i] & 0xfU];
    }
}


static const char *a90_ioctl_name(uint32_t request)
{
    if (request == A90_AUDIO_ALLOCATE_CALIBRATION)
        return "AUDIO_ALLOCATE_CALIBRATION";
    if (request == A90_AUDIO_DEALLOCATE_CALIBRATION)
        return "AUDIO_DEALLOCATE_CALIBRATION";
    if (request == A90_AUDIO_SET_CALIBRATION)
        return "AUDIO_SET_CALIBRATION";
    return "unknown";
}

static int a90_is_audio_cal_ioctl(uint32_t request)
{
    return request == A90_AUDIO_ALLOCATE_CALIBRATION ||
           request == A90_AUDIO_DEALLOCATE_CALIBRATION ||
           request == A90_AUDIO_SET_CALIBRATION;
}

static int a90_fake_allocate_enabled(void)
{
    const char *value = getenv(A90_FAKE_ALLOCATE_ENV);
    return a90_streq(value, "1") || a90_streq(value, "true") || a90_streq(value, "yes");
}

static int a90_should_fake_success(uint32_t request)
{
    /* V2630 safety invariant: always fake AUDIO_SET_CALIBRATION; never pass it through. */
    if (request == A90_AUDIO_SET_CALIBRATION)
        return 1;
    if (!a90_fake_allocate_enabled())
        return 0;
    return request == A90_AUDIO_ALLOCATE_CALIBRATION ||
           request == A90_AUDIO_DEALLOCATE_CALIBRATION;
}

static void a90_set_errno(int err)
{
    int *slot = __errno();
    if (slot)
        *slot = err;
}

static int a90_is_all_zero(const uint8_t *buf, uint32_t len)
{
    uint32_t i;
    for (i = 0; i < len; i++) {
        if (buf[i])
            return 0;
    }
    return 1;
}

static void a90_copy_arg_snapshot(uint32_t request, uintptr_t arg,
                                  struct a90_arg_snapshot *snapshot)
{
    const volatile uint32_t *source = (const volatile uint32_t *)arg;
    uint32_t sample_len;
    uint32_t words;
    uint32_t i;

    snapshot->available = 0;
    snapshot->requested_size = 0;
    snapshot->sample_len = 0;
    for (i = 0; i < A90_AUDIO_CAL_ARG_WORDS; i++)
        snapshot->words[i] = 0;

    if (!a90_is_audio_cal_ioctl(request) || arg == 0)
        return;

    snapshot->requested_size = source[0];
    sample_len = snapshot->requested_size;
    if (sample_len > A90_AUDIO_CAL_ARG_SAMPLE_BYTES)
        sample_len = A90_AUDIO_CAL_ARG_SAMPLE_BYTES;
    if (sample_len < 4U)
        sample_len = 4U;
    words = (sample_len + 3U) / 4U;
    if (words > A90_AUDIO_CAL_ARG_WORDS)
        words = A90_AUDIO_CAL_ARG_WORDS;
    for (i = 0; i < words; i++)
        snapshot->words[i] = source[i];
    snapshot->sample_len = words * 4U;
    snapshot->available = 1;
}

static void a90_parse_setcal_header(uintptr_t arg, struct a90_setcal_header *header)
{
    const volatile uint32_t *source = (const volatile uint32_t *)arg;
    header->valid = 0;
    header->data_size = 0;
    header->version = 0;
    header->cal_type = 0;
    header->cal_type_size = 0;
    header->cal_hdr_version = 0;
    header->buffer_number = 0;
    header->cal_size = 0;
    header->mem_handle = -1;
    if (!arg)
        return;
    header->data_size = source[0];
    if (header->data_size < 32U || header->data_size > A90_MAX_SET_ARG_BYTES)
        return;
    header->version = source[1];
    header->cal_type = source[2];
    header->cal_type_size = source[3];
    header->cal_hdr_version = source[4];
    header->buffer_number = source[5];
    header->cal_size = source[6];
    header->mem_handle = (int32_t)source[7];
    header->valid = 1;
}

static void a90_make_raw_path(char *out, const char *kind, uint32_t seq,
                              uint32_t cal_type, uint32_t len)
{
    char *p = out;
    p = a90_append_str(p, A90_SETCAL_RAW_PREFIX);
    p = a90_append_str(p, kind);
    p = a90_append_str(p, "-p");
    p = a90_append_hex8_raw(p, a90_getpid());
    p = a90_append_str(p, "-s");
    p = a90_append_hex8_raw(p, seq);
    p = a90_append_str(p, "-cal");
    p = a90_append_hex8_raw(p, cal_type);
    p = a90_append_str(p, "-len");
    p = a90_append_hex8_raw(p, len);
    p = a90_append_str(p, ".bin");
    *p = 0;
}

static int a90_dump_raw_file(const char *path, const uint8_t *buf, uint32_t len,
                             char sha_hex[64], int *all_zero)
{
    struct a90_sha256 sha;
    uint8_t digest[32];
    int fd;

    *all_zero = a90_is_all_zero(buf, len);
    a90_sha256_init(&sha);
    a90_sha256_update(&sha, buf, len);
    a90_sha256_final(&sha, digest);
    a90_sha_hex(sha_hex, digest);

    fd = a90_open_new(path);
    if (fd < 0)
        return fd;
    a90_write_all(fd, buf, len);
    a90_close(fd);
    return 0;
}

static void a90_write_arg_snapshot(int fd, const struct a90_arg_snapshot *snapshot)
{
    uint32_t i;
    uint32_t word_count = snapshot->sample_len / 4U;

    a90_write_str(fd, ",\"arg_snapshot\":{\"available\":");
    a90_write_str(fd, snapshot->available ? "true" : "false");
    if (!snapshot->available) {
        a90_write_str(fd, "}");
        return;
    }
    a90_write_str(fd, ",\"requested_size\":");
    a90_write_dec(fd, snapshot->requested_size);
    a90_write_str(fd, ",\"sample_len\":");
    a90_write_dec(fd, snapshot->sample_len);
    if (word_count >= 8U) {
        a90_write_str(fd, ",\"data_size\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[0]);
        a90_write_str(fd, ",\"version\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[1]);
        a90_write_str(fd, ",\"cal_type\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[2]);
        a90_write_str(fd, ",\"cal_type_size\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[3]);
        a90_write_str(fd, ",\"type_version\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[4]);
        a90_write_str(fd, ",\"buffer_number\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[5]);
        a90_write_str(fd, ",\"cal_size\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[6]);
        a90_write_str(fd, ",\"mem_handle\":");
        a90_write_sdec(fd, (int32_t)snapshot->words[7]);
    }
    a90_write_str(fd, ",\"words_le\":[");
    for (i = 0; i < word_count; i++) {
        if (i)
            a90_write_str(fd, ",");
        a90_write_str(fd, "\"");
        a90_write_hex32(fd, snapshot->words[i]);
        a90_write_str(fd, "\"");
    }
    a90_write_str(fd, "]}");
}

static void a90_write_ioctl_event(int fd, uint32_t request, uintptr_t arg,
                                  int32_t ret, int32_t err, const char *intercept,
                                  const struct a90_arg_snapshot *snapshot)
{
    int out = a90_open_append(A90_TRACE_EVENTS_PATH);
    if (out < 0)
        return;
    a90_write_str(out, "{\"event\":\"ioctl_trace\",\"pid\":");
    a90_write_dec(out, a90_getpid());
    a90_write_str(out, ",\"tid\":");
    a90_write_dec(out, a90_gettid());
    a90_write_str(out, ",\"fd\":");
    a90_write_sdec(out, fd);
    a90_write_str(out, ",\"request\":\"");
    a90_write_hex32(out, request);
    a90_write_str(out, "\",\"name\":\"");
    a90_write_str(out, a90_ioctl_name(request));
    a90_write_str(out, "\",\"arg\":\"");
    a90_write_hex_ptr(out, arg);
    a90_write_str(out, "\",\"ret\":");
    a90_write_sdec(out, ret);
    a90_write_str(out, ",\"errno\":");
    a90_write_sdec(out, err);
    a90_write_str(out, ",\"intercept\":\"");
    a90_write_str(out, intercept);
    a90_write_str(out, "\"");
    a90_write_arg_snapshot(out, snapshot);
    a90_write_str(out, "}\n");
    a90_close(out);
}

static void a90_write_setcal_event(uint32_t seq, int fd, uintptr_t arg,
                                   const struct a90_setcal_header *header,
                                   const char *arg_path, int arg_dump_rc,
                                   const char arg_sha[64], int arg_all_zero,
                                   const char *dmabuf_status, const char *dmabuf_path,
                                   int dmabuf_rc, const char dmabuf_sha[64],
                                   int dmabuf_all_zero, int mmap_errno)
{
    int out = a90_open_append(A90_SETCAL_EVENTS_PATH);
    if (out < 0)
        return;
    a90_write_str(out, "{\"event\":\"setcal_capture\",\"pid\":");
    a90_write_dec(out, a90_getpid());
    a90_write_str(out, ",\"tid\":");
    a90_write_dec(out, a90_gettid());
    a90_write_str(out, ",\"sequence\":");
    a90_write_dec(out, seq);
    a90_write_str(out, ",\"fd\":");
    a90_write_sdec(out, fd);
    a90_write_str(out, ",\"request\":\"0xc00461cb\",\"arg\":\"");
    a90_write_hex_ptr(out, arg);
    a90_write_str(out, "\",\"header_valid\":");
    a90_write_str(out, header->valid ? "true" : "false");
    a90_write_str(out, ",\"data_size\":");
    a90_write_dec(out, header->data_size);
    a90_write_str(out, ",\"version\":");
    a90_write_dec(out, header->version);
    a90_write_str(out, ",\"cal_type\":");
    a90_write_dec(out, header->cal_type);
    a90_write_str(out, ",\"cal_type_size\":");
    a90_write_dec(out, header->cal_type_size);
    a90_write_str(out, ",\"cal_hdr_version\":");
    a90_write_dec(out, header->cal_hdr_version);
    a90_write_str(out, ",\"buffer_number\":");
    a90_write_dec(out, header->buffer_number);
    a90_write_str(out, ",\"cal_size\":");
    a90_write_dec(out, header->cal_size);
    a90_write_str(out, ",\"mem_handle\":");
    a90_write_sdec(out, header->mem_handle);
    a90_write_str(out, ",\"set_arg\":{\"path\":\"");
    a90_write_str(out, arg_path ? arg_path : "");
    a90_write_str(out, "\",\"len\":");
    a90_write_dec(out, header->valid ? header->data_size : 0U);
    a90_write_str(out, ",\"dump_rc\":");
    a90_write_sdec(out, arg_dump_rc);
    a90_write_str(out, ",\"sha256\":\"");
    a90_write_all(out, arg_sha, 64);
    a90_write_str(out, "\",\"all_zero\":");
    a90_write_str(out, arg_all_zero ? "true" : "false");
    a90_write_str(out, "},\"dmabuf\":{\"status\":\"");
    a90_write_str(out, dmabuf_status);
    a90_write_str(out, "\",\"path\":\"");
    a90_write_str(out, dmabuf_path ? dmabuf_path : "");
    a90_write_str(out, "\",\"len\":");
    a90_write_dec(out, (header->valid && header->cal_size <= A90_MAX_DMABUF_BYTES) ? header->cal_size : 0U);
    a90_write_str(out, ",\"dump_rc\":");
    a90_write_sdec(out, dmabuf_rc);
    a90_write_str(out, ",\"mmap_errno\":");
    a90_write_sdec(out, mmap_errno);
    a90_write_str(out, ",\"sha256\":\"");
    a90_write_all(out, dmabuf_sha, 64);
    a90_write_str(out, "\",\"all_zero\":");
    a90_write_str(out, dmabuf_all_zero ? "true" : "false");
    a90_write_str(out, "}}\n");
    a90_close(out);
}

static void a90_capture_setcal_arg_and_dmabuf(int fd, uintptr_t arg)
{
    struct a90_setcal_header header;
    uint32_t seq = ++a90_setcal_sequence;
    char arg_path[160];
    char dmabuf_path[160];
    char arg_sha[64];
    char dmabuf_sha[64];
    int arg_all_zero = 0;
    int dmabuf_all_zero = 0;
    int arg_dump_rc = -1;
    int dmabuf_rc = -1;
    int mmap_errno = 0;
    const char *dmabuf_status = "not-attempted";
    void *mapping;
    uint32_t i;

    for (i = 0; i < 64U; i++) {
        arg_sha[i] = '0';
        dmabuf_sha[i] = '0';
    }
    arg_path[0] = 0;
    dmabuf_path[0] = 0;

    a90_parse_setcal_header(arg, &header);
    if (header.valid) {
        a90_make_raw_path(arg_path, "arg", seq, header.cal_type, header.data_size);
        /* Dump exactly arg[0:data_size], not just the 32-byte basic header. */
        arg_dump_rc = a90_dump_raw_file(arg_path, (const uint8_t *)arg, header.data_size,
                                        arg_sha, &arg_all_zero);
        if (header.cal_size == 0U) {
            dmabuf_status = "header-only";
        } else if (header.mem_handle < 0) {
            dmabuf_status = "no-mem-handle";
        } else if (header.cal_size > A90_MAX_DMABUF_BYTES) {
            dmabuf_status = "cal-size-over-cap";
        } else {
            dmabuf_status = "mmap-attempted";
            mapping = mmap(0, header.cal_size, A90_PROT_READ, A90_MAP_SHARED,
                           header.mem_handle, 0);
            if (mapping == A90_MAP_FAILED) {
                int *slot = __errno();
                mmap_errno = slot ? *slot : 0;
                dmabuf_status = "mmap-failed";
            } else {
                a90_make_raw_path(dmabuf_path, "dmabuf", seq, header.cal_type, header.cal_size);
                dmabuf_rc = a90_dump_raw_file(dmabuf_path, (const uint8_t *)mapping,
                                              header.cal_size, dmabuf_sha,
                                              &dmabuf_all_zero);
                (void)munmap(mapping, header.cal_size);
                dmabuf_status = dmabuf_rc == 0 ? "dumped" : "dump-failed";
            }
        }
    } else {
        dmabuf_status = "invalid-header";
    }

    a90_write_setcal_event(seq, fd, arg, &header, arg_path, arg_dump_rc,
                           arg_sha, arg_all_zero, dmabuf_status, dmabuf_path,
                           dmabuf_rc, dmabuf_sha, dmabuf_all_zero, mmap_errno);
}

__attribute__((visibility("default")))
int ioctl(int fd, unsigned long request, ...)
{
    __builtin_va_list ap;
    uintptr_t arg;
    struct a90_arg_snapshot snapshot;
    const char *intercept = "pass-through";
    long rc;
    int err = 0;
    int ret;

    __builtin_va_start(ap, request);
    arg = (uintptr_t)__builtin_va_arg(ap, void *);
    __builtin_va_end(ap);

    a90_copy_arg_snapshot((uint32_t)request, arg, &snapshot);

    if ((uint32_t)request == A90_AUDIO_SET_CALIBRATION)
        a90_capture_setcal_arg_and_dmabuf(fd, arg);

    if (a90_should_fake_success((uint32_t)request)) {
        ret = 0;
        err = 0;
        intercept = ((uint32_t)request == A90_AUDIO_SET_CALIBRATION) ? "fake-set-always" : "fake-success";
        a90_set_errno(0);
    } else {
        rc = a90_syscall3(A90_NR_IOCTL, fd, (long)request, (long)arg);
        if (rc < 0 && rc >= -4095) {
            err = (int)(-rc);
            ret = -1;
            a90_set_errno(err);
        } else {
            ret = (int)rc;
        }
    }

    a90_write_ioctl_event(fd, (uint32_t)request, arg, ret, err, intercept, &snapshot);
    return ret;
}
