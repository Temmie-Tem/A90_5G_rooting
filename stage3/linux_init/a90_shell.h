#ifndef A90_SHELL_H
#define A90_SHELL_H

#include <stdbool.h>
#include <stddef.h>

enum command_flags {
    CMD_NONE = 0,
    CMD_DISPLAY = 1 << 0,
    CMD_BLOCKING = 1 << 1,
    CMD_DANGEROUS = 1 << 2,
    CMD_BACKGROUND = 1 << 3,
    CMD_NO_DONE = 1 << 4,
};

typedef int (*command_handler)(char **argv, int argc);

struct shell_command {
    const char *name;
    command_handler handler;
    const char *usage;
    unsigned int flags;
};

struct shell_last_result {
    char command[64];
    int code;
    int saved_errno;
    long duration_ms;
    unsigned int flags;
};

struct a90_shell_command_stats {
    size_t total;
    size_t display;
    size_t blocking;
    size_t dangerous;
    size_t background;
    size_t no_done;
};

void a90_shell_save_last_result(const char *command,
                                int code,
                                int saved_errno,
                                long duration_ms,
                                unsigned int flags);
const struct shell_last_result *a90_shell_last_result(void);
void a90_shell_print_last_result(void);
unsigned long a90_shell_next_protocol_seq(void);
const struct shell_command *a90_shell_find_command(const struct shell_command *commands,
                                                   size_t count,
                                                   const char *name);
void a90_shell_collect_command_stats(const struct shell_command *commands,
                                     size_t count,
                                     struct a90_shell_command_stats *stats);
void a90_shell_format_flags(unsigned int flags, char *buf, size_t size);
void a90_shell_print_command_stats(const struct shell_command *commands, size_t count);
void a90_shell_print_command_inventory(const struct shell_command *commands, size_t count);
int a90_shell_result_errno(int result);
void a90_shell_print_result(const struct shell_command *command,
                            const char *name,
                            int result,
                            int result_errno,
                            long duration_ms);

#endif
