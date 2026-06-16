/*
 * V2577 common-topology scoped ACDB capture arm.
 *
 * This hook avoids init-time acdb_ioctl dumping but arms before the topology
 * GET inside acdb_loader_send_common_custom_topology().  The acdb_ioctl tap is
 * expected to exit after the first ret==0 non-all-zero 4916-byte payload, so
 * the downstream allocate/memcpy/SET tail should not execute on success.
 */

typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef unsigned long size_t;

extern void *dlsym(void *handle, const char *symbol);
extern void a90_arm_capture(void) __attribute__((weak, visibility("default")));

#define A90_RTLD_NEXT ((void *)-1L)
#define A90_EVENTS_PATH "/data/local/tmp/a90-acdb-ownget/acdb-v2577-common-topology-arm-events.jsonl"

#define A90_AT_FDCWD (-100)
#define A90_O_WRONLY 00000001
#define A90_O_CREAT 00000100
#define A90_O_APPEND 00002000
#define A90_MODE_0600 0600

#define A90_NR_WRITE 4
#define A90_NR_CLOSE 6
#define A90_NR_GETPID 20
#define A90_NR_GETTID 224
#define A90_NR_OPENAT 322

typedef int32_t (*a90_common_topology_fn)(void);

static volatile int a90_in_hook;
static a90_common_topology_fn a90_real_common_topology;

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
    int i;

    if (v == 0) {
        a90_write_str(fd, "0");
        return;
    }
    while (v && n < (int)sizeof(rev)) {
        rev[n++] = (char)('0' + (v % 10));
        v /= 10;
    }
    for (i = n - 1; i >= 0; i--)
        a90_write_all(fd, &rev[i], 1);
}

static void a90_write_sdec(int fd, int value)
{
    if (value < 0) {
        a90_write_str(fd, "-");
        a90_write_dec(fd, (unsigned int)(-value));
    } else {
        a90_write_dec(fd, (unsigned int)value);
    }
}

static void a90_write_event(const char *stage, int code)
{
    int fd = a90_open_append(A90_EVENTS_PATH);
    if (fd < 0)
        return;

    a90_write_str(fd, "{\"event\":\"v2577_common_topology_arm\",\"stage\":\"");
    a90_write_str(fd, stage);
    a90_write_str(fd, "\",\"code\":");
    a90_write_sdec(fd, code);
    a90_write_str(fd, ",\"pid\":");
    a90_write_dec(fd, a90_getpid());
    a90_write_str(fd, ",\"tid\":");
    a90_write_dec(fd, a90_gettid());
    a90_write_str(fd, "}\n");
    a90_close(fd);
}

static void a90_resolve_real(void)
{
    if (!a90_real_common_topology)
        a90_real_common_topology = (a90_common_topology_fn)dlsym(A90_RTLD_NEXT, "acdb_loader_send_common_custom_topology");
}

__attribute__((visibility("default"))) int32_t acdb_loader_send_common_custom_topology(void)
{
    int32_t ret;

    a90_resolve_real();
    if (a90_in_hook) {
        if (!a90_real_common_topology)
            return -1;
        return a90_real_common_topology();
    }

    a90_in_hook = 1;
    a90_write_event("enter_common_topology", 0);
    if (a90_arm_capture) {
        a90_arm_capture();
        a90_write_event("armed_before_real_common_topology", 0);
    } else {
        a90_write_event("arm_capture_missing", -1);
    }

    if (!a90_real_common_topology) {
        a90_write_event("real_common_topology_missing", -1);
        a90_in_hook = 0;
        return -1;
    }

    ret = a90_real_common_topology();
    a90_write_event("real_common_topology_return", ret);
    a90_in_hook = 0;
    return ret;
}
