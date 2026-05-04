#include "a90_controller.h"

#include <fcntl.h>
#include <string.h>
#include <unistd.h>

#include "a90_config.h"
#include "a90_shell.h"
#include "a90_util.h"

static void controller_write_file(const char *path, const char *value) {
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0644);

    if (fd < 0) {
        return;
    }
    write_all(fd, value, strlen(value));
    close(fd);
}

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

void a90_controller_clear_menu_ipc(void) {
    unlink(AUTO_MENU_STATE_PATH);
    unlink(AUTO_MENU_REQUEST_PATH);
}

void a90_controller_clear_menu_request(void) {
    unlink(AUTO_MENU_REQUEST_PATH);
}

void a90_controller_set_menu_active(bool active) {
    controller_write_file(AUTO_MENU_STATE_PATH, active ? "1\n" : "0\n");
}

void a90_controller_set_menu_state(bool active, bool power_page) {
    if (!active) {
        controller_write_file(AUTO_MENU_STATE_PATH, "0\n");
    } else if (power_page) {
        controller_write_file(AUTO_MENU_STATE_PATH, "power\n");
    } else {
        controller_write_file(AUTO_MENU_STATE_PATH, "1\n");
    }
}

bool a90_controller_menu_is_active(void) {
    char state[16];

    if (read_text_file(AUTO_MENU_STATE_PATH, state, sizeof(state)) < 0) {
        return false;
    }
    trim_newline(state);
    return strcmp(state, "1") == 0 ||
           strcmp(state, "active") == 0 ||
           strcmp(state, "menu") == 0 ||
           strcmp(state, "power") == 0;
}

bool a90_controller_menu_power_is_active(void) {
    char state[16];

    if (read_text_file(AUTO_MENU_STATE_PATH, state, sizeof(state)) < 0) {
        return false;
    }
    trim_newline(state);
    return strcmp(state, "power") == 0;
}

void a90_controller_request_menu_show(void) {
    controller_write_file(AUTO_MENU_REQUEST_PATH, "show\n");
}

void a90_controller_request_menu_hide(void) {
    controller_write_file(AUTO_MENU_REQUEST_PATH, "hide\n");
}

enum a90_controller_menu_request a90_controller_consume_menu_request(void) {
    char request[32];

    if (read_text_file(AUTO_MENU_REQUEST_PATH, request, sizeof(request)) < 0) {
        return A90_CONTROLLER_MENU_REQUEST_NONE;
    }
    unlink(AUTO_MENU_REQUEST_PATH);
    trim_newline(request);
    if (strcmp(request, "hide") == 0 ||
        strcmp(request, "hidemenu") == 0 ||
        strcmp(request, "resume") == 0 ||
        strcmp(request, "q") == 0 ||
        strcmp(request, "Q") == 0 ||
        strcmp(request, "0") == 0) {
        return A90_CONTROLLER_MENU_REQUEST_HIDE;
    }
    if (strcmp(request, "show") == 0 ||
        strcmp(request, "menu") == 0 ||
        strcmp(request, "screenmenu") == 0 ||
        strcmp(request, "1") == 0) {
        return A90_CONTROLLER_MENU_REQUEST_SHOW;
    }
    return A90_CONTROLLER_MENU_REQUEST_NONE;
}
