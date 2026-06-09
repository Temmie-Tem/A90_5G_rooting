#ifndef A90_WIFICFG_H
#define A90_WIFICFG_H

#include <stdbool.h>
#include <stddef.h>

#define A90_WIFICFG_SUPPLICANT_CONF "/cache/a90-wifi/wpa_supplicant.conf"
#define A90_WIFICFG_UI_MAX_PROFILES 8

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

struct a90_wificfg_profile_summary {
    bool exists;
    bool parsed;
    bool ssid_file_configured;
    bool psk_file_configured;
    bool ssid_usable;
    bool psk_usable;
    int load_rc;
    int enabled;
    int priority;
    char name[96];
    char source_hint[16];
    char source[16];
    char band[192];
    char key_mgmt[192];
    char decision[80];
};

struct a90_wificfg_profile_list {
    int profile_count;
    int stored_count;
    int duplicate_count;
    int overflow_count;
    struct a90_wificfg_autoconnect autoconnect;
    struct a90_wificfg_profile_summary profiles[A90_WIFICFG_UI_MAX_PROFILES];
};

int a90_wificfg_cmd(char **argv, int argc);
int a90_wificfg_print_status(void);
int a90_wificfg_collect_profile_list(struct a90_wificfg_profile_list *out);
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
