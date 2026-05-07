#ifndef A90_LONGSOAK_H
#define A90_LONGSOAK_H

int a90_longsoak_start(int interval_sec);
int a90_longsoak_stop(void);
int a90_longsoak_status(void);
int a90_longsoak_path(void);
int a90_longsoak_tail(int lines);
int a90_longsoak_cmd(char **argv, int argc);

#endif
