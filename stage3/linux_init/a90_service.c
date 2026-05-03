#include "a90_service.h"

#include "a90_log.h"
#include "a90_run.h"

#include <errno.h>
#include <string.h>
#include <sys/wait.h>

static pid_t service_pids[A90_SERVICE_COUNT] = {
    -1,
    -1,
    -1,
    -1,
};

static const char *service_name(enum a90_service_id service) {
    switch (service) {
    case A90_SERVICE_HUD:
        return "autohud";
    case A90_SERVICE_TCPCTL:
        return "tcpctl";
    case A90_SERVICE_ADBD:
        return "adbd";
    case A90_SERVICE_RSHELL:
        return "rshell";
    default:
        return "unknown";
    }
}

static int valid_service(enum a90_service_id service) {
    return service >= 0 && service < A90_SERVICE_COUNT;
}

pid_t a90_service_pid(enum a90_service_id service) {
    if (!valid_service(service)) {
        return -1;
    }
    return service_pids[service];
}

void a90_service_set_pid(enum a90_service_id service, pid_t pid) {
    if (!valid_service(service)) {
        return;
    }
    service_pids[service] = pid;
    a90_logf("service", "%s pid=%ld", service_name(service), (long)pid);
}

void a90_service_clear(enum a90_service_id service) {
    if (!valid_service(service)) {
        return;
    }
    if (service_pids[service] > 0) {
        a90_logf("service", "%s clear pid=%ld",
                    service_name(service), (long)service_pids[service]);
    }
    service_pids[service] = -1;
}

int a90_service_reap(enum a90_service_id service, int *status_out) {
    pid_t pid;
    int status = 0;
    int rc;

    if (!valid_service(service)) {
        return -EINVAL;
    }

    pid = service_pids[service];
    if (pid <= 0) {
        return 0;
    }

    rc = a90_run_reap_pid(pid, &status);
    if (rc == 1) {
        if (status_out != NULL) {
            *status_out = status;
        }
        a90_logf("service", "%s reaped pid=%ld status=0x%x",
                    service_name(service), (long)pid, status);
        service_pids[service] = -1;
        return 1;
    }
    if (rc < 0) {
        a90_logf("service", "%s reap failed pid=%ld rc=%d error=%s",
                    service_name(service), (long)pid, rc, strerror(-rc));
    }
    return rc;
}

int a90_service_stop(enum a90_service_id service, int timeout_ms) {
    pid_t pid;
    int status = 0;
    int rc;

    if (!valid_service(service)) {
        return -EINVAL;
    }

    pid = service_pids[service];
    if (pid <= 0) {
        return 0;
    }

    rc = a90_run_stop_pid(pid, service_name(service), timeout_ms, &status);
    service_pids[service] = -1;
    a90_logf("service", "%s stopped pid=%ld rc=%d status=0x%x",
                service_name(service), (long)pid, rc, status);
    return rc;
}

