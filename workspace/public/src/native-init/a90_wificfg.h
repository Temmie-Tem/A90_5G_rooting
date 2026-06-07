#ifndef A90_WIFICFG_H
#define A90_WIFICFG_H

#include <stddef.h>

#define A90_WIFICFG_SUPPLICANT_CONF "/cache/a90-wifi/wpa_supplicant.conf"

int a90_wificfg_cmd(char **argv, int argc);
int a90_wificfg_print_status(void);
int a90_wificfg_prepare_supplicant_config(const char *profile_name,
                                          char *out_path,
                                          size_t out_path_size);

#endif
