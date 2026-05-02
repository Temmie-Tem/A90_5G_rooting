#ifndef A90_NETSERVICE_H
#define A90_NETSERVICE_H

#include <stdbool.h>
#include <sys/types.h>

struct a90_netservice_status {
    bool enabled;
    bool usbnet_helper;
    bool tcpctl_helper;
    bool toybox_helper;
    bool ncm_present;
    bool tcpctl_running;
    pid_t tcpctl_pid;
    const char *flag_path;
    const char *log_path;
    const char *ifname;
    const char *device_ip;
    const char *netmask;
    const char *tcp_port;
    const char *tcp_idle_seconds;
    const char *tcp_max_clients;
};

bool a90_netservice_enabled(void);
int a90_netservice_set_enabled(bool enabled);
int a90_netservice_start(void);
int a90_netservice_stop(void);
void a90_netservice_reap(void);
int a90_netservice_status(struct a90_netservice_status *out);

#endif
