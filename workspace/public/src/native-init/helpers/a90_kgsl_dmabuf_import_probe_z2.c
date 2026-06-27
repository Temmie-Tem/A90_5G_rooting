// No-present DRM msm GEM -> KGSL dma-buf import preflight for GPU Z2.

#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

#include <drm/drm.h>
#include <drm/drm_fourcc.h>
#include <drm/drm_mode.h>
#include <drm/msm_drm.h>

#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif

#ifndef DRM_CLOEXEC
#define DRM_CLOEXEC O_CLOEXEC
#endif

#define Z2_WIDTH 960U
#define Z2_HEIGHT 720U
#define Z2_BPP 4U
#define Z2_STRIDE (Z2_WIDTH * Z2_BPP)
#define Z2_BYTES ((uint64_t)Z2_STRIDE * Z2_HEIGHT)

#define KGSL_IOC_TYPE 0x09
#define KGSL_USER_MEM_TYPE_DMABUF 0x00000003U

struct kgsl_gpuobj_free {
    uint64_t flags;
    uint64_t priv;
    unsigned int id;
    unsigned int type;
    unsigned int len;
};

struct kgsl_gpuobj_info {
    uint64_t gpuaddr;
    uint64_t flags;
    uint64_t size;
    uint64_t va_len;
    uint64_t va_addr;
    unsigned int id;
};

struct kgsl_gpuobj_import {
    uint64_t priv;
    uint64_t priv_len;
    uint64_t flags;
    unsigned int type;
    unsigned int id;
};

struct kgsl_gpuobj_import_dma_buf {
    int fd;
};

#define IOCTL_KGSL_GPUOBJ_FREE _IOW(KGSL_IOC_TYPE, 0x46, struct kgsl_gpuobj_free)
#define IOCTL_KGSL_GPUOBJ_INFO _IOWR(KGSL_IOC_TYPE, 0x47, struct kgsl_gpuobj_info)
#define IOCTL_KGSL_GPUOBJ_IMPORT _IOWR(KGSL_IOC_TYPE, 0x48, struct kgsl_gpuobj_import)

static int ioctl_retry(int fd, unsigned long request, void *arg) {
    int rc;

    do {
        rc = ioctl(fd, request, arg);
    } while (rc < 0 && errno == EINTR);
    return rc;
}

static int negative_errno(void) {
    int saved = errno;

    return saved > 0 ? -saved : -EIO;
}

static int read_trimmed(const char *path, char *out, size_t out_size) {
    FILE *fp;

    if (out_size == 0) {
        errno = EINVAL;
        return -1;
    }
    fp = fopen(path, "r");
    if (fp == NULL) {
        return -1;
    }
    if (fgets(out, (int)out_size, fp) == NULL) {
        fclose(fp);
        errno = EIO;
        return -1;
    }
    fclose(fp);
    out[strcspn(out, "\r\n")] = '\0';
    return 0;
}

static int ensure_chrdev_path(const char *path,
                              const char *sysfs_dev_path,
                              const char *parent_dir) {
    char dev_info[64];
    unsigned int major_num;
    unsigned int minor_num;
    struct stat st;

    if (stat(path, &st) == 0 && S_ISCHR(st.st_mode)) {
        return 0;
    }
    if (read_trimmed(sysfs_dev_path, dev_info, sizeof(dev_info)) < 0) {
        return -1;
    }
    if (sscanf(dev_info, "%u:%u", &major_num, &minor_num) != 2) {
        errno = EINVAL;
        return -1;
    }
    if (parent_dir != NULL && mkdir(parent_dir, 0755) < 0 && errno != EEXIST) {
        return -1;
    }
    if (mknod(path, S_IFCHR | 0600, makedev(major_num, minor_num)) < 0 && errno != EEXIST) {
        return -1;
    }
    return 0;
}

static int get_cap(int fd, uint64_t capability, uint64_t *value) {
    struct drm_get_cap cap;

    memset(&cap, 0, sizeof(cap));
    cap.capability = capability;
    if (ioctl_retry(fd, DRM_IOCTL_GET_CAP, &cap) < 0) {
        return negative_errno();
    }
    *value = cap.value;
    return 0;
}

static int msm_gem_info_u64(int fd, uint32_t handle, uint32_t info, uint64_t *value) {
    struct drm_msm_gem_info arg;

    memset(&arg, 0, sizeof(arg));
    arg.handle = handle;
    arg.info = info;
    if (ioctl_retry(fd, DRM_IOCTL_MSM_GEM_INFO, &arg) < 0) {
        return negative_errno();
    }
    *value = arg.value;
    return 0;
}

static int close_drm_gem_handle(int fd, uint32_t handle) {
    struct drm_gem_close close_arg;

    if (handle == 0U) {
        return 0;
    }
    memset(&close_arg, 0, sizeof(close_arg));
    close_arg.handle = handle;
    if (ioctl_retry(fd, DRM_IOCTL_GEM_CLOSE, &close_arg) < 0) {
        return negative_errno();
    }
    return 0;
}

static int free_kgsl_gpuobj(int fd, unsigned int id) {
    struct kgsl_gpuobj_free free_arg;

    if (id == 0U) {
        return 0;
    }
    memset(&free_arg, 0, sizeof(free_arg));
    free_arg.id = id;
    if (ioctl_retry(fd, IOCTL_KGSL_GPUOBJ_FREE, &free_arg) < 0) {
        return negative_errno();
    }
    return 0;
}

int main(void) {
    int drm_fd = -1;
    int kgsl_fd = -1;
    int prime_fd = -1;
    void *map = MAP_FAILED;
    struct drm_msm_gem_new gem;
    uint32_t drm_handle = 0;
    uint32_t fb_id = 0;
    unsigned int kgsl_id = 0;
    uint64_t dumb = 0;
    uint64_t addfb2_modifiers = 0;
    uint64_t prime = 0;
    uint64_t offset = 0;
    uint64_t iova = 0;
    int rc_offset = -ENOSYS;
    int rc_iova = -ENOSYS;
    int rc_mmap = -ENOSYS;
    int rc_prime_export = -ENOSYS;
    int rc_addfb2 = -ENOSYS;
    int rc_kgsl_import = -ENOSYS;
    int rc_kgsl_info = -ENOSYS;
    int rc_kgsl_free = 0;
    int rc_rmfb = 0;
    int rc_close_drm = 0;
    struct kgsl_gpuobj_info kgsl_info;

    memset(&kgsl_info, 0, sizeof(kgsl_info));
    printf("probe.version=1\n");
    printf("probe.scope=z2-drm-msm-gem-to-kgsl-dmabuf-import-preflight\n");
    printf("probe.target.width=%u height=%u stride=%u bytes=%llu format=XB24 flags=MSM_BO_SCANOUT|MSM_BO_WC\n",
           Z2_WIDTH, Z2_HEIGHT, Z2_STRIDE, (unsigned long long)Z2_BYTES);

    if (ensure_chrdev_path("/dev/dri/card0", "/sys/class/drm/card0/dev", "/dev/dri") < 0) {
        printf("probe.drm.open.rc=%d\n", negative_errno());
        printf("probe.result=z2-open-drm-failed\n");
        return 1;
    }
    drm_fd = open("/dev/dri/card0", O_RDWR | O_CLOEXEC);
    if (drm_fd < 0) {
        printf("probe.drm.open.rc=%d\n", negative_errno());
        printf("probe.result=z2-open-drm-failed\n");
        return 1;
    }
    printf("probe.drm.open.rc=0 node=/dev/dri/card0\n");
    if (get_cap(drm_fd, DRM_CAP_DUMB_BUFFER, &dumb) == 0) {
        printf("probe.drm.cap.dumb_buffer=%llu\n", (unsigned long long)dumb);
    }
    if (get_cap(drm_fd, DRM_CAP_ADDFB2_MODIFIERS, &addfb2_modifiers) == 0) {
        printf("probe.drm.cap.addfb2_modifiers=%llu\n", (unsigned long long)addfb2_modifiers);
    }
    if (get_cap(drm_fd, DRM_CAP_PRIME, &prime) == 0) {
        printf("probe.drm.cap.prime=0x%llx import=%d export=%d\n",
               (unsigned long long)prime,
               (prime & DRM_PRIME_CAP_IMPORT) ? 1 : 0,
               (prime & DRM_PRIME_CAP_EXPORT) ? 1 : 0);
    }

    memset(&gem, 0, sizeof(gem));
    gem.size = Z2_BYTES;
    gem.flags = MSM_BO_SCANOUT | MSM_BO_WC;
    if (ioctl_retry(drm_fd, DRM_IOCTL_MSM_GEM_NEW, &gem) < 0) {
        printf("probe.drm.msm_gem_new.rc=%d\n", negative_errno());
        goto out;
    }
    drm_handle = gem.handle;
    printf("probe.drm.msm_gem_new.rc=0 handle=%u requested_size=%llu flags=0x%x\n",
           drm_handle, (unsigned long long)gem.size, gem.flags);

    rc_offset = msm_gem_info_u64(drm_fd, drm_handle, MSM_INFO_GET_OFFSET, &offset);
    rc_iova = msm_gem_info_u64(drm_fd, drm_handle, MSM_INFO_GET_IOVA, &iova);
    printf("probe.drm.msm_gem_info.offset.rc=%d value=0x%llx\n", rc_offset, (unsigned long long)offset);
    printf("probe.drm.msm_gem_info.iova.rc=%d value=0x%llx\n", rc_iova, (unsigned long long)iova);

    if (rc_offset == 0) {
        map = mmap(NULL, (size_t)Z2_BYTES, PROT_READ | PROT_WRITE, MAP_SHARED, drm_fd, (off_t)offset);
        if (map == MAP_FAILED) {
            rc_mmap = negative_errno();
        } else {
            volatile uint32_t *words = (volatile uint32_t *)map;
            uint32_t word_count = (uint32_t)(Z2_BYTES / sizeof(uint32_t));

            words[0] = 0xff102030U;
            words[word_count / 2U] = 0xff405060U;
            words[word_count - 1U] = 0xff708090U;
            __sync_synchronize();
            printf("probe.drm.mmap.sample first=0x%08x middle=0x%08x last=0x%08x words=%u\n",
                   words[0], words[word_count / 2U], words[word_count - 1U], word_count);
            rc_mmap = 0;
        }
    }
    printf("probe.drm.mmap.rc=%d\n", rc_mmap);

    {
        struct drm_prime_handle prime_arg;

        memset(&prime_arg, 0, sizeof(prime_arg));
        prime_arg.handle = drm_handle;
        prime_arg.flags = DRM_CLOEXEC;
        if (ioctl_retry(drm_fd, DRM_IOCTL_PRIME_HANDLE_TO_FD, &prime_arg) < 0) {
            rc_prime_export = negative_errno();
        } else {
            prime_fd = prime_arg.fd;
            rc_prime_export = 0;
        }
        printf("probe.drm.prime.export.rc=%d fd_valid=%d\n", rc_prime_export, prime_fd >= 0 ? 1 : 0);
    }

    {
        struct drm_mode_fb_cmd2 addfb2;

        memset(&addfb2, 0, sizeof(addfb2));
        addfb2.width = Z2_WIDTH;
        addfb2.height = Z2_HEIGHT;
        addfb2.pixel_format = DRM_FORMAT_XBGR8888;
        addfb2.handles[0] = drm_handle;
        addfb2.pitches[0] = Z2_STRIDE;
        if (ioctl_retry(drm_fd, DRM_IOCTL_MODE_ADDFB2, &addfb2) < 0) {
            rc_addfb2 = negative_errno();
        } else {
            fb_id = addfb2.fb_id;
            rc_addfb2 = 0;
        }
        printf("probe.drm.addfb2.rc=%d fb_id=%u width=%u height=%u pitch=%u\n",
               rc_addfb2, fb_id, Z2_WIDTH, Z2_HEIGHT, Z2_STRIDE);
    }

    if (ensure_chrdev_path("/dev/kgsl-3d0", "/sys/class/kgsl/kgsl-3d0/dev", "/dev") < 0) {
        printf("probe.kgsl.open.rc=%d\n", negative_errno());
        goto out;
    }
    kgsl_fd = open("/dev/kgsl-3d0", O_RDWR | O_CLOEXEC);
    if (kgsl_fd < 0) {
        printf("probe.kgsl.open.rc=%d\n", negative_errno());
        goto out;
    }
    printf("probe.kgsl.open.rc=0 node=/dev/kgsl-3d0\n");

    if (prime_fd >= 0) {
        struct kgsl_gpuobj_import_dma_buf import_dmabuf;
        struct kgsl_gpuobj_import import_arg;

        memset(&import_dmabuf, 0, sizeof(import_dmabuf));
        import_dmabuf.fd = prime_fd;
        memset(&import_arg, 0, sizeof(import_arg));
        import_arg.priv = (uint64_t)(uintptr_t)&import_dmabuf;
        import_arg.priv_len = sizeof(import_dmabuf);
        import_arg.flags = 0;
        import_arg.type = KGSL_USER_MEM_TYPE_DMABUF;
        if (ioctl_retry(kgsl_fd, IOCTL_KGSL_GPUOBJ_IMPORT, &import_arg) < 0) {
            rc_kgsl_import = negative_errno();
        } else {
            kgsl_id = import_arg.id;
            rc_kgsl_import = 0;
        }
        printf("probe.kgsl.gpuobj_import.rc=%d id=%u type=dmabuf flags=0x%llx\n",
               rc_kgsl_import, kgsl_id, (unsigned long long)import_arg.flags);
    } else {
        printf("probe.kgsl.gpuobj_import.rc=%d id=0 type=dmabuf flags=0x0\n", rc_kgsl_import);
    }

    if (kgsl_id != 0U) {
        memset(&kgsl_info, 0, sizeof(kgsl_info));
        kgsl_info.id = kgsl_id;
        if (ioctl_retry(kgsl_fd, IOCTL_KGSL_GPUOBJ_INFO, &kgsl_info) < 0) {
            rc_kgsl_info = negative_errno();
        } else {
            rc_kgsl_info = 0;
        }
        printf("probe.kgsl.gpuobj_info.rc=%d id=%u gpuaddr=0x%llx size=%llu flags=0x%llx va_len=%llu va_addr=0x%llx\n",
               rc_kgsl_info,
               kgsl_info.id,
               (unsigned long long)kgsl_info.gpuaddr,
               (unsigned long long)kgsl_info.size,
               (unsigned long long)kgsl_info.flags,
               (unsigned long long)kgsl_info.va_len,
               (unsigned long long)kgsl_info.va_addr);
    } else {
        printf("probe.kgsl.gpuobj_info.rc=%d id=0 gpuaddr=0x0 size=0 flags=0x0 va_len=0 va_addr=0x0\n",
               rc_kgsl_info);
    }

out:
    if (kgsl_fd >= 0 && kgsl_id != 0U) {
        rc_kgsl_free = free_kgsl_gpuobj(kgsl_fd, kgsl_id);
    }
    if (fb_id != 0U) {
        uint32_t rmfb_id = fb_id;

        if (ioctl_retry(drm_fd, DRM_IOCTL_MODE_RMFB, &rmfb_id) < 0) {
            rc_rmfb = negative_errno();
        }
    }
    if (map != MAP_FAILED) {
        (void)munmap(map, (size_t)Z2_BYTES);
    }
    if (prime_fd >= 0) {
        (void)close(prime_fd);
    }
    if (drm_handle != 0U) {
        rc_close_drm = close_drm_gem_handle(drm_fd, drm_handle);
    }
    printf("probe.cleanup.kgsl_free.rc=%d rmfb.rc=%d close_drm_handle.rc=%d\n",
           rc_kgsl_free, rc_rmfb, rc_close_drm);

    printf("probe.result=%s\n",
           rc_mmap == 0 &&
           rc_prime_export == 0 &&
           rc_addfb2 == 0 &&
           rc_kgsl_import == 0 &&
           rc_kgsl_info == 0 &&
           kgsl_info.gpuaddr != 0ULL &&
           kgsl_info.size >= Z2_BYTES &&
           rc_kgsl_free == 0 &&
           rc_rmfb == 0 &&
           rc_close_drm == 0
           ? "z2-kgsl-dmabuf-import-preflight-pass"
           : "z2-kgsl-dmabuf-import-preflight-partial");

    if (kgsl_fd >= 0) {
        (void)close(kgsl_fd);
    }
    if (drm_fd >= 0) {
        (void)close(drm_fd);
    }
    return 0;
}
