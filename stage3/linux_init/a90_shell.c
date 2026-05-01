#include "a90_shell.h"

#include <stdio.h>
#include <string.h>
#include <errno.h>

#include "a90_console.h"

static struct shell_last_result last_result = {
    .command = "<none>",
    .code = 0,
    .saved_errno = 0,
    .duration_ms = 0,
    .flags = CMD_NONE,
};

static unsigned long shell_protocol_seq = 0;

void a90_shell_save_last_result(const char *command,
                                int code,
                                int saved_errno,
                                long duration_ms,
                                unsigned int flags) {
    snprintf(last_result.command, sizeof(last_result.command), "%s", command);
    last_result.code = code;
    last_result.saved_errno = saved_errno;
    last_result.duration_ms = duration_ms;
    last_result.flags = flags;
}

const struct shell_last_result *a90_shell_last_result(void) {
    return &last_result;
}

void a90_shell_print_last_result(void) {
    a90_console_printf("last: command=%s code=%d errno=%d duration=%ldms flags=0x%x\r\n",
            last_result.command,
            last_result.code,
            last_result.saved_errno,
            last_result.duration_ms,
            last_result.flags);
    if (last_result.saved_errno != 0) {
        a90_console_printf("last: error=%s\r\n", strerror(last_result.saved_errno));
    }
}

unsigned long a90_shell_next_protocol_seq(void) {
    return ++shell_protocol_seq;
}

const struct shell_command *a90_shell_find_command(const struct shell_command *commands,
                                                   size_t count,
                                                   const char *name) {
    size_t index;

    if (commands == NULL || name == NULL) {
        return NULL;
    }

    for (index = 0; index < count; ++index) {
        if (strcmp(name, commands[index].name) == 0) {
            return &commands[index];
        }
    }

    return NULL;
}

int a90_shell_result_errno(int result) {
    if (result < 0) {
        return -result;
    }
    return 0;
}

void a90_shell_print_result(const struct shell_command *command,
                            const char *name,
                            int result,
                            int result_errno,
                            long duration_ms) {
    if (command != NULL && (command->flags & CMD_NO_DONE) != 0 && result == 0) {
        return;
    }
    if (result == 0) {
        a90_console_printf("[done] %s (%ldms)\r\n", name, duration_ms);
    } else if (result < 0) {
        a90_console_printf("[err] %s rc=%d errno=%d (%s) (%ldms)\r\n",
                name,
                result,
                result_errno,
                strerror(result_errno),
                duration_ms);
    } else {
        a90_console_printf("[err] %s rc=%d (%ldms)\r\n",
                name,
                result,
                duration_ms);
    }
}
