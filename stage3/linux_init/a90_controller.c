#include "a90_controller.h"

#include <string.h>

#include "a90_shell.h"

bool a90_controller_is_hide_word(const char *name) {
    return name != NULL &&
           (strcmp(name, "q") == 0 ||
            strcmp(name, "Q") == 0 ||
            strcmp(name, "hide") == 0 ||
            strcmp(name, "hidemenu") == 0 ||
            strcmp(name, "resume") == 0);
}

static bool command_is_menu_control(const char *name) {
    return strcmp(name, "screenmenu") == 0 ||
           strcmp(name, "menu") == 0 ||
           strcmp(name, "hide") == 0 ||
           strcmp(name, "hidemenu") == 0 ||
           strcmp(name, "resume") == 0 ||
           strcmp(name, "stophud") == 0;
}

static bool command_waits_for_input(const char *name) {
    return strcmp(name, "blindmenu") == 0 ||
           strcmp(name, "waitkey") == 0 ||
           strcmp(name, "readinput") == 0 ||
           strcmp(name, "waitgesture") == 0;
}

static bool command_allowed_on_power_page(const char *name) {
    return strcmp(name, "help") == 0 ||
           strcmp(name, "version") == 0 ||
           strcmp(name, "status") == 0 ||
           strcmp(name, "bootstatus") == 0 ||
           strcmp(name, "storage") == 0 ||
           strcmp(name, "timeline") == 0 ||
           strcmp(name, "last") == 0 ||
           strcmp(name, "logpath") == 0 ||
           strcmp(name, "logcat") == 0 ||
           strcmp(name, "inputlayout") == 0 ||
           strcmp(name, "inputmonitor") == 0 ||
           strcmp(name, "uname") == 0 ||
           strcmp(name, "pwd") == 0 ||
           strcmp(name, "mounts") == 0 ||
           strcmp(name, "reattach") == 0 ||
           strcmp(name, "stophud") == 0;
}

enum a90_controller_busy_reason a90_controller_command_busy_reason(const char *name,
                                                                   unsigned int flags,
                                                                   bool menu_active,
                                                                   bool power_page_active) {
    if (name == NULL || !menu_active) {
        return A90_CONTROLLER_BUSY_NONE;
    }
    if (command_is_menu_control(name)) {
        return A90_CONTROLLER_BUSY_NONE;
    }
    if (!power_page_active) {
        if ((flags & CMD_DANGEROUS) != 0) {
            return A90_CONTROLLER_BUSY_DANGEROUS;
        }
        if (command_waits_for_input(name)) {
            return A90_CONTROLLER_BUSY_AUTO_MENU;
        }
        return A90_CONTROLLER_BUSY_NONE;
    }
    if (command_allowed_on_power_page(name)) {
        return A90_CONTROLLER_BUSY_NONE;
    }
    return A90_CONTROLLER_BUSY_POWER;
}

const char *a90_controller_busy_message(enum a90_controller_busy_reason reason) {
    switch (reason) {
    case A90_CONTROLLER_BUSY_POWER:
        return "[busy] power menu active; send hide/q before commands";
    case A90_CONTROLLER_BUSY_DANGEROUS:
        return "[busy] auto menu active; hide/q before dangerous command";
    case A90_CONTROLLER_BUSY_AUTO_MENU:
        return "[busy] auto menu active; command waits for input/menu control";
    case A90_CONTROLLER_BUSY_NONE:
    default:
        return "";
    }
}
