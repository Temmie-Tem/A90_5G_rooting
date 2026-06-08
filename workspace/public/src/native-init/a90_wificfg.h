#ifndef A90_WIFICFG_H
#define A90_WIFICFG_H

#include <stdbool.h>
#include <stddef.h>

#define A90_WIFICFG_SUPPLICANT_CONF "/cache/a90-wifi/wpa_supplicant.conf"

struct a90_wificfg_autoconnect {
    bool config_present;
    bool config_valid;
    bool enabled;
    bool profile_valid;
    int connect_timeout_sec;
    int dhcp;
    int external_ping;
    int scan_before_connect;
    int retry_count;
    char profile[96];
    char decision[80];
};

int a90_wificfg_cmd(char **argv, int argc);
int a90_wificfg_print_status(void);
int a90_wificfg_print_profile_list(void);
int a90_wificfg_print_profile_status(const char *profile_name);
int a90_wificfg_print_autoconnect_status(void);
int a90_wificfg_set_autoconnect(bool enabled, const char *profile_name);
int a90_wificfg_get_autoconnect(struct a90_wificfg_autoconnect *out,
                                const char *profile_override);
int a90_wificfg_prepare_supplicant_config(const char *profile_name,
                                          char *out_path,
                                          size_t out_path_size);

#endif
