#ifndef A90_SERVICE_H
#define A90_SERVICE_H

#include <sys/types.h>

enum a90_service_id {
    A90_SERVICE_HUD = 0,
    A90_SERVICE_TCPCTL,
    A90_SERVICE_ADBD,
    A90_SERVICE_COUNT
};

pid_t a90_service_pid(enum a90_service_id service);
void a90_service_set_pid(enum a90_service_id service, pid_t pid);
void a90_service_clear(enum a90_service_id service);
int a90_service_reap(enum a90_service_id service, int *status_out);
int a90_service_stop(enum a90_service_id service, int timeout_ms);

#endif
