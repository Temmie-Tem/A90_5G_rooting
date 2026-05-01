#ifndef A90_CONTROLLER_H
#define A90_CONTROLLER_H

#include <stdbool.h>

enum a90_controller_busy_reason {
    A90_CONTROLLER_BUSY_NONE = 0,
    A90_CONTROLLER_BUSY_AUTO_MENU,
    A90_CONTROLLER_BUSY_DANGEROUS,
    A90_CONTROLLER_BUSY_POWER,
};

bool a90_controller_is_hide_word(const char *name);
enum a90_controller_busy_reason a90_controller_command_busy_reason(const char *name,
                                                                   unsigned int flags,
                                                                   bool menu_active,
                                                                   bool power_page_active);
const char *a90_controller_busy_message(enum a90_controller_busy_reason reason);

#endif
