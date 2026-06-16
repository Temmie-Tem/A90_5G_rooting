/*
 * V2583 common-topology hook for ACDB lower store_get metadata probing.
 *
 * V2582 proved acdb_loader_init_v3() reaches the common-topology path and then
 * crashes before returning to the post-init helper.  This interposer therefore
 * runs the V2580 store_get cases from inside the common-topology hook, after
 * patching the known initialized flag, and exits before the crashing init tail.
 *
 * It writes metadata only: ret, returned length, all-zero discriminator, and
 * FNV-1a32.  It does not dump raw ACDB bytes and does not call direct
 * acdb_ioctl or the audio calibration device.
 */

typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef unsigned short uint16_t;
typedef unsigned char uint8_t;
typedef unsigned long uintptr_t;
typedef unsigned long size_t;

extern void *dlsym(void *handle, const char *symbol);

#define A90_RTLD_NEXT ((void *)-1L)
#define A90_RTLD_DEFAULT ((void *)0)

#define A90_EVENTS_PATH "/data/local/tmp/a90-acdb-ownget/acdb-v2583-preinit-storeget-events.jsonl"
#define A90_LOADER_IS_INITIALIZED_OFF 0x00008034UL
#define A90_LOADER_INIT_FLAG_OFF 0x00018a9cUL
#define A90_OUTPUT_MAX 65536U
#define A90_INSTANCE_MAX 16U

#ifndef A90_V2583_CALL_REAL_COMMON_TOPOLOGY
#define A90_V2583_CALL_REAL_COMMON_TOPOLOGY 0
#endif

#define A90_AT_FDCWD (-100)
#define A90_O_WRONLY 00000001
#define A90_O_CREAT 00000100
#define A90_O_APPEND 00002000
#define A90_MODE_0600 0600

#define A90_NR_EXIT 1
#define A90_NR_WRITE 4
#define A90_NR_CLOSE 6
#define A90_NR_GETPID 20
#define A90_NR_GETTID 224
#define A90_NR_EXIT_GROUP 248
#define A90_NR_OPENAT 322

struct a90_store_req {
    uint32_t present;      /* +0: keeps get_audio_cal_v2-compatible wrappers happy */
    uint32_t pad04;        /* +4 */
    uint32_t pad08;        /* +8 */
    uint32_t f12;          /* +12 */
    uint32_t f16;          /* +16 */
    uint32_t f20;          /* +20 */
    uint32_t f24;          /* +24 */
    uint32_t selector;     /* +28 */
    uint32_t instance_ptr; /* +32 */
    uint32_t pad36_word;   /* +36, low half used by instance branches */
    uint32_t instance_len; /* +40 */
};

struct a90_case_def {
    const char *name;
    uint32_t selector;
    uint32_t instance_enabled;
    uint32_t f12;
    uint32_t f16;
    uint32_t f20;
    uint32_t f24;
    uint16_t f36;
};

typedef int32_t (*a90_common_topology_fn)(void);
typedef int32_t (*a90_store_get_audio_cal_fn)(void *req,
                                              uint8_t *out_buf,
                                              uint32_t *out_len_io);

static volatile int a90_in_hook;
static a90_common_topology_fn a90_real_common_topology;
static a90_store_get_audio_cal_fn a90_real_store_get_audio_cal;

static uint8_t a90_output[A90_OUTPUT_MAX];
static uint8_t a90_instance[A90_INSTANCE_MAX] = {
    0x41, 0x39, 0x30, 0x00, 0x15, 0x00, 0x00, 0x00,
    0x80, 0xbb, 0x00, 0x00, 0x80, 0xbb, 0x00, 0x00,
};

static const struct a90_case_def a90_cases[] = {
    {"store_selector_37", 37U, 0U, 15U, 48000U, 0U, 48000U, 0U},
    {"store_selector_0_no_instance", 0U, 0U, 15U, 48000U, 0U, 48000U, 0U},
    {"store_selector_0_instance", 0U, 1U, 15U, 48000U, 0U, 48000U, 0U},
    {"store_selector_1_no_instance", 1U, 0U, 15U, 48000U, 0U, 48000U, 0U},
    {"store_selector_1_instance", 1U, 1U, 15U, 48000U, 0U, 48000U, 0U},
};

static long a90_syscall0(long n)
{
    register long r7 __asm__("r7") = n;
    register long r0 __asm__("r0");
    __asm__ volatile("svc #0" : "=r"(r0) : "r"(r7) : "memory");
    return r0;
}

static long a90_syscall1(long n, long a0)
{
    register long r7 __asm__("r7") = n;
    register long r0 __asm__("r0") = a0;
    __asm__ volatile("svc #0" : "+r"(r0) : "r"(r7) : "memory");
    return r0;
}

static long a90_syscall3(long n, long a0, long a1, long a2)
{
    register long r7 __asm__("r7") = n;
    register long r0 __asm__("r0") = a0;
    register long r1 __asm__("r1") = a1;
    register long r2 __asm__("r2") = a2;
    __asm__ volatile("svc #0" : "+r"(r0) : "r"(r1), "r"(r2), "r"(r7) : "memory");
    return r0;
}

static long a90_syscall4(long n, long a0, long a1, long a2, long a3)
{
    register long r7 __asm__("r7") = n;
    register long r0 __asm__("r0") = a0;
    register long r1 __asm__("r1") = a1;
    register long r2 __asm__("r2") = a2;
    register long r3 __asm__("r3") = a3;
    __asm__ volatile("svc #0" : "+r"(r0) : "r"(r1), "r"(r2), "r"(r3), "r"(r7) : "memory");
    return r0;
}

static void a90_exit_group(int code)
{
    (void)a90_syscall1(A90_NR_EXIT_GROUP, code);
    (void)a90_syscall1(A90_NR_EXIT, code);
    for (;;) {
    }
}

static int a90_open_append(const char *path)
{
    return (int)a90_syscall4(A90_NR_OPENAT, A90_AT_FDCWD, (long)path,
                             A90_O_WRONLY | A90_O_CREAT | A90_O_APPEND,
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
    while (s && s[n])
        n++;
    return n;
}

static void a90_write_all(int fd, const char *p, size_t len)
{
    while (len) {
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

static void a90_write_dec(int fd, unsigned int v)
{
    char rev[16];
    int n = 0;
    if (v == 0) {
        a90_write_str(fd, "0");
        return;
    }
    while (v && n < (int)sizeof(rev)) {
        rev[n++] = (char)('0' + (v % 10));
        v /= 10;
    }
    while (n)
        a90_write_all(fd, &rev[--n], 1U);
}

static void a90_write_signed(int fd, int value)
{
    if (value < 0) {
        a90_write_str(fd, "-");
        a90_write_dec(fd, (unsigned int)(-value));
    } else {
        a90_write_dec(fd, (unsigned int)value);
    }
}

static void a90_write_hex32(int fd, uint32_t value)
{
    static const char hex[] = "0123456789abcdef";
    char buf[10];
    int i;
    buf[0] = '0';
    buf[1] = 'x';
    for (i = 0; i < 8; i++)
        buf[2 + i] = hex[(value >> (28 - (i * 4))) & 0xfU];
    a90_write_all(fd, buf, sizeof(buf));
}

static void a90_memzero(void *ptr, uint32_t len)
{
    uint8_t *p = (uint8_t *)ptr;
    uint32_t i;
    for (i = 0; i < len; i++)
        p[i] = 0U;
}

static int a90_is_all_zero(const uint8_t *ptr, uint32_t len)
{
    uint32_t i;
    for (i = 0; i < len; i++) {
        if (ptr[i] != 0U)
            return 0;
    }
    return 1;
}

static uint32_t a90_fnv1a32(const uint8_t *ptr, uint32_t len)
{
    uint32_t h = 2166136261U;
    uint32_t i;
    for (i = 0; i < len; i++) {
        h ^= (uint32_t)ptr[i];
        h *= 16777619U;
    }
    return h;
}

static void a90_write_event_header(int fd, const char *stage)
{
    a90_write_str(fd, "{\"event\":\"v2583_preinit_store_get\",\"stage\":\"");
    a90_write_str(fd, stage);
    a90_write_str(fd, "\",\"pid\":");
    a90_write_dec(fd, a90_getpid());
    a90_write_str(fd, ",\"tid\":");
    a90_write_dec(fd, a90_gettid());
}

static void a90_write_simple_event(const char *stage, int code)
{
    int fd = a90_open_append(A90_EVENTS_PATH);
    if (fd < 0)
        return;
    a90_write_event_header(fd, stage);
    a90_write_str(fd, ",\"code\":");
    a90_write_signed(fd, code);
    a90_write_str(fd, "}\n");
    a90_close(fd);
}

static void a90_write_hex_event(const char *stage, uint32_t value)
{
    int fd = a90_open_append(A90_EVENTS_PATH);
    if (fd < 0)
        return;
    a90_write_event_header(fd, stage);
    a90_write_str(fd, ",\"value\":\"");
    a90_write_hex32(fd, value);
    a90_write_str(fd, "\"}\n");
    a90_close(fd);
}

static void a90_write_case_event(const char *name, uint32_t selector, uint32_t instance_enabled,
                                 int32_t ret, uint32_t out_len, int all_zero, uint32_t fnv)
{
    int fd = a90_open_append(A90_EVENTS_PATH);
    if (fd < 0)
        return;
    a90_write_event_header(fd, "case_return");
    a90_write_str(fd, ",\"case\":\"");
    a90_write_str(fd, name);
    a90_write_str(fd, "\",\"selector\":");
    a90_write_dec(fd, selector);
    a90_write_str(fd, ",\"instance\":");
    a90_write_dec(fd, instance_enabled);
    a90_write_str(fd, ",\"ret\":");
    a90_write_signed(fd, ret);
    a90_write_str(fd, ",\"out_len\":");
    a90_write_dec(fd, out_len);
    a90_write_str(fd, ",\"all_zero\":");
    a90_write_str(fd, all_zero ? "true" : "false");
    a90_write_str(fd, ",\"fnv1a32\":\"");
    a90_write_hex32(fd, fnv);
    a90_write_str(fd, "\"}\n");
    a90_close(fd);
}

static void a90_prepare_req(struct a90_store_req *req, const struct a90_case_def *def)
{
    a90_memzero(req, sizeof(*req));
    req->present = 1U;
    req->f12 = def->f12;
    req->f16 = def->f16;
    req->f20 = def->f20;
    req->f24 = def->f24;
    req->selector = def->selector;
    if (def->instance_enabled) {
        req->instance_ptr = (uint32_t)(unsigned long)a90_instance;
        req->pad36_word = (uint32_t)def->f36;
        req->instance_len = A90_INSTANCE_MAX;
    }
}

static void a90_resolve_symbols(void)
{
    if (!a90_real_common_topology)
        a90_real_common_topology = (a90_common_topology_fn)dlsym(A90_RTLD_NEXT, "acdb_loader_send_common_custom_topology");
    if (!a90_real_store_get_audio_cal)
        a90_real_store_get_audio_cal = (a90_store_get_audio_cal_fn)dlsym(A90_RTLD_DEFAULT, "acdb_loader_store_get_audio_cal");
    if (!a90_real_store_get_audio_cal)
        a90_real_store_get_audio_cal = (a90_store_get_audio_cal_fn)dlsym(A90_RTLD_NEXT, "acdb_loader_store_get_audio_cal");
}

static int a90_patch_initialized_flag(void)
{
    uintptr_t is_initialized;
    uintptr_t base;
    volatile unsigned char *flag;

    is_initialized = (uintptr_t)dlsym(A90_RTLD_DEFAULT, "acdb_loader_is_initialized");
    if (!is_initialized)
        is_initialized = (uintptr_t)dlsym(A90_RTLD_NEXT, "acdb_loader_is_initialized");
    if (!is_initialized)
        return -1;

    is_initialized &= ~(uintptr_t)1U;
    base = is_initialized - A90_LOADER_IS_INITIALIZED_OFF;
    flag = (volatile unsigned char *)(base + A90_LOADER_INIT_FLAG_OFF);
    *flag = 1U;
    a90_write_hex_event("patched_initialized_flag_addr", (uint32_t)(uintptr_t)flag);
    return 0;
}

static void a90_run_store_get_cases(void)
{
    uint32_t i;

    if (!a90_real_store_get_audio_cal) {
        a90_write_simple_event("store_get_missing", -1);
        return;
    }

    for (i = 0; i < (uint32_t)(sizeof(a90_cases) / sizeof(a90_cases[0])); i++) {
        struct a90_store_req req;
        uint32_t out_len = A90_OUTPUT_MAX;
        int32_t ret;
        uint32_t observed_len;
        uint32_t hash;
        int zero;

        a90_memzero(a90_output, A90_OUTPUT_MAX);
        a90_prepare_req(&req, &a90_cases[i]);
        ret = a90_real_store_get_audio_cal(&req, a90_output, &out_len);
        observed_len = out_len <= A90_OUTPUT_MAX ? out_len : A90_OUTPUT_MAX;
        zero = a90_is_all_zero(a90_output, observed_len);
        hash = a90_fnv1a32(a90_output, observed_len);
        a90_write_case_event(a90_cases[i].name, a90_cases[i].selector,
                             a90_cases[i].instance_enabled, ret, out_len, zero, hash);
    }
}

__attribute__((visibility("default"))) int32_t acdb_loader_send_common_custom_topology(void)
{
    int32_t common_ret = -90;
    int patch_ret;

    if (a90_in_hook)
        return -92;
    a90_in_hook = 1;

    a90_write_simple_event("entered_common_topology_hook", 0);
    a90_resolve_symbols();
#if A90_V2583_CALL_REAL_COMMON_TOPOLOGY
    if (a90_real_common_topology) {
        a90_write_simple_event("before_real_common_topology", 0);
        common_ret = a90_real_common_topology();
        a90_write_simple_event("real_common_topology_return", common_ret);
    } else {
        a90_write_simple_event("real_common_topology_missing", -1);
    }
#else
    common_ret = 0;
    a90_write_simple_event("skip_real_common_topology", 0);
#endif

    patch_ret = a90_patch_initialized_flag();
    a90_write_simple_event("patch_initialized_flag_return", patch_ret);
    a90_write_simple_event("before_store_get_cases", 0);
    a90_run_store_get_cases();
    a90_write_simple_event("exit_before_init_tail", common_ret);
    a90_exit_group(0);
    return common_ret;
}
