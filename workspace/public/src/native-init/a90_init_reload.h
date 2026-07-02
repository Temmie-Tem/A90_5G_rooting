#ifndef A90_INIT_RELOAD_H
#define A90_INIT_RELOAD_H

/*
 * Native-init hot-reload (flash-cycle infrastructure).
 *
 * `reload <token> <staged-init-path> <expected-sha256>` replaces the running PID1 in place with a
 * staged new init ELF via execve(), WITHOUT a reboot. The USB gadget / configfs state lives in the
 * kernel and native-init's gadget setup is idempotent and never unbinds the UDC, so the host serial
 * link persists across the execve and the new init comes straight back to a shell. This skips the
 * ~17s bootloader+kernel boot and the USB re-enumeration that a reflash+reboot pays, which is the
 * dominant cost of a research flash cycle.
 *
 * DANGEROUS: if the new init image is broken and crashes during early startup, PID1 exits and the
 * kernel panics; recover via reboot / TWRP. The command is therefore token-gated, requires the
 * candidate in the approved staging root, and validates a caller-pinned SHA-256 plus ELF magic
 * before execve. A FAILED execve is safe: the old init image is intact and keeps running.
 *
 * Output lines are "A90RELOAD key=value". Registered CMD_DANGEROUS | CMD_NO_DONE (like reboot): on
 * success the command does not return a normal A90P1 END because the process image is replaced.
 */
int a90_init_reload_cmd(char **argv, int argc);

#endif /* A90_INIT_RELOAD_H */
