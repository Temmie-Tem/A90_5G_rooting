#ifndef A90_BOOT_AUDIT_H
#define A90_BOOT_AUDIT_H

/*
 * Read-only boot-target auditor (§7.1 of the self-dd fast-flash tool design).
 *
 * This module has NO write path compiled in. It opens the boot block O_RDONLY, reports the
 * fd-derived identity (canonical path, rdev major:minor, size, logical/physical sector, PARTNAME,
 * diskseq) as machine-parseable "A90BOOTAUDIT key=value" lines, and answers the open feasibility
 * question of whether native-init can even read the boot partition under RKP. The host side parses
 * this into the boot-target guard's BlockIdentity and confirms the pin. It never writes, never dd's.
 */
int a90_boot_audit_cmd(char **argv, int argc);

#endif /* A90_BOOT_AUDIT_H */
