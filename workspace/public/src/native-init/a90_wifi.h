#ifndef A90_WIFI_H
#define A90_WIFI_H

int a90_wifi_cmd(char **argv, int argc);
int a90_wifi_print_status(void);
int a90_wifi_scan_once(int delay_ms);
int a90_wifi_connect_profile(const char *profile_name);
int a90_wifi_dhcp_profile(const char *profile_name);
int a90_wifi_cleanup(void);
int a90_wifi_start_boot_autoconnect_once(void);

#endif
