#include "a90_app_about.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "a90_config.h"
#include "a90_draw.h"
#include "a90_kms.h"
#include "a90_util.h"

static uint32_t app_about_display_width_or(uint32_t fallback) {
    struct a90_kms_info info;

    a90_kms_info(&info);
    return info.width > 0 ? info.width : fallback;
}

static uint32_t app_about_text_scale(void) {
    uint32_t width = app_about_display_width_or(0);

    if (width >= 1080) {
        return 4;
    }
    if (width >= 720) {
        return 3;
    }
    return 2;
}

static uint32_t app_about_shrink_text_scale(const char *text,
                                            uint32_t scale,
                                            uint32_t max_width) {
    while (scale > 1 && (uint32_t)strlen(text) * scale * 6 > max_width) {
        --scale;
    }
    return scale;
}

static int app_about_draw_lines(const char *title,
                                const char *const *lines,
                                size_t count) {
    const char *footer = "PRESS ANY BUTTON TO RETURN";
    uint32_t scale;
    uint32_t title_scale;
    uint32_t left;
    uint32_t top;
    uint32_t content_width;
    uint32_t line_height;
    size_t index;

    if (a90_kms_begin_frame(0x050505) < 0) {
        return negative_errno_or(ENODEV);
    }

    scale = app_about_text_scale();
    title_scale = scale + 1;
    left = a90_kms_framebuffer()->width / 18;
    if (left < scale * 4) {
        left = scale * 4;
    }
    top = a90_kms_framebuffer()->height / 12;
    content_width = a90_kms_framebuffer()->width - (left * 2);
    line_height = scale * 10;

    a90_draw_text(a90_kms_framebuffer(), left, top, title, 0xffcc33,
                  app_about_shrink_text_scale(title, title_scale, content_width));
    top += line_height + scale * 4;

    a90_draw_rect(a90_kms_framebuffer(),
                  left - scale,
                  top - scale,
                  content_width,
                  line_height * ((uint32_t)count + 1),
                  0x202020);

    for (index = 0; index < count; ++index) {
        const char *line = lines[index] != NULL ? lines[index] : "";
        uint32_t color = index == 0 ? 0x88ee88 : 0xffffff;

        a90_draw_text(a90_kms_framebuffer(),
                      left,
                      top + (uint32_t)index * line_height,
                      line,
                      color,
                      app_about_shrink_text_scale(line, scale, content_width - scale * 2));
    }

    a90_draw_text(a90_kms_framebuffer(),
                  left,
                  a90_kms_framebuffer()->height - scale * 12,
                  footer,
                  0xffffff,
                  app_about_shrink_text_scale(footer, scale, content_width));

    if (a90_kms_present("screenabout", true) < 0) {
        return negative_errno_or(EIO);
    }
    return 0;
}

int a90_app_about_draw_version(void) {
    char version_line[96];
    const char *lines[5];

    snprintf(version_line, sizeof(version_line), "VERSION %s (%s)", INIT_VERSION, INIT_BUILD);
    lines[0] = INIT_BANNER;
    lines[1] = version_line;
    lines[2] = INIT_CREATOR;
    lines[3] = "KERNEL STOCK ANDROID LINUX 4.14";
    lines[4] = "RUNTIME CUSTOM STATIC PID 1";

    return app_about_draw_lines("ABOUT / VERSION", lines, SCREEN_MENU_COUNT(lines));
}

int a90_app_about_draw_changelog(void) {
    const char *lines[] = {
        "0.9.13 v113 RUNTIME PACKAGE LAYOUT",
        "0.9.12 v112 USB SERVICE SOAK",
        "0.9.11 v111 EXTENDED SOAK RC",
        "0.9.10 v110 APP CONTROLLER CLEANUP",
        "0.9.9 v109 STRUCTURE AUDIT 2",
        "0.9.8 v108 APP INPUTMON API",
        "0.9.7 v107 APP DISPLAYTEST API",
        "0.9.6 v106 APP ABOUT API",
        "0.9.5 v105 SOAK RC",
        "0.9.1 v101 SERVICE MANAGER",
        "0.9.0 v100 REMOTE SHELL",
        "0.8.29 v98 HELPER DEPLOY",
        "0.8.28 v97 SD RUNTIME ROOT",
        "0.8.27 v96 STRUCTURE AUDIT",
        "0.8.26 v95 NETSERVICE USB API",
        "0.8.25 v94 BOOT SELFTEST",
        "0.8.24 v93 STORAGE API",
        "0.8.23 v92 SHELL CONTROLLER",
        "0.8.22 v91 CPUSTRESS HELPER",
        "0.8.21 v90 METRICS API",
        "0.8.20 v89 MENU CONTROL API",
        "0.8.19 v88 HUD API",
        "0.8.18 v87 INPUT API",
        "0.8.17 v86 KMS DRAW API",
        "0.8.16 v85 RUN SERVICE API",
        "0.8.15 v84 CMDPROTO API",
        "0.8.14 v83 CONSOLE API",
        "0.8.13 v82 LOG TIMELINE API",
        "0.8.12 v81 CONFIG UTIL API",
        "0.8.11 v80 SOURCE MODULES",
        "0.8.10 v79 BOOT SD PROBE",
        "0.8.9 v78 SD WORKSPACE",
        "0.8.8 v77 DISPLAY TEST PAGES",
        "0.8.7 v76 AT FRAGMENT FILTER",
        "0.8.6 v75 QUIET IDLE REATTACH",
        "0.8.5 v74 CMDV1 ARG ENCODING",
        "0.8.4 v73 CMDV1 PROTOCOL",
        "0.8.3 v72 DISPLAY TEST FIX",
        "0.8.2 v71 MENU LOG TAIL",
        "0.8.1 v70 INPUT MONITOR APP",
        "0.8.0 v69 INPUT GESTURE LAYOUT",
        "0.7.5 v68 LOG TAIL + MORE HISTORY",
        "0.7.4 v67 DETAIL CHANGELOG UI",
        "0.7.3 v66 ABOUT + VERSIONING",
        "0.7.2 v65 SPLASH SAFE LAYOUT",
        "0.7.1 v64 CUSTOM BOOT SPLASH",
        "0.7.0 v63 APP MENU + CPU STRESS",
        "0.6.0 v62 CPU STRESS / DEV NODES",
        "0.5.1 v61 CPU/GPU USAGE HUD",
        "0.5.0 v60 NETSERVICE / RECONNECT",
        "0.4.1 v59 AT SERIAL FILTER",
        "0.4.0 v55 NCM TCP CONTROL",
        "0.3.0 v53 MENU BUSY GATE",
        "0.2.0 v40 SHELL LOG HUD CORE",
        "0.1.0 v1  NATIVE INIT ORIGIN",
    };

    return app_about_draw_lines("ABOUT / CHANGELOG", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0838(void) {
    const char *lines[] = {
        "0.9.13 v113 RUNTIME PACKAGE LAYOUT",
        "Adds package-friendly dirs",
        "Reports pkg/bin helpers services",
        "Reports pkg/manifests path",
        "Keeps legacy helper manifest fallback",
        "Avoids destructive SD migration",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.13", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0837(void) {
    const char *lines[] = {
        "0.9.12 v112 USB SERVICE SOAK",
        "Keeps netservice opt-in",
        "Validates NCM ping path",
        "Exercises tcpctl host smoke",
        "Checks rollback to ACM-only",
        "Prepares runtime package layout",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.12", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0836(void) {
    const char *lines[] = {
        "0.9.11 v111 EXTENDED SOAK RC",
        "Keeps v110 runtime behavior",
        "Runs longer host soak profile",
        "Validates menu/service idle path",
        "Records RC stability baseline",
        "Prepares USB service soak",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.11", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0835(void) {
    const char *lines[] = {
        "0.9.10 v110 APP CONTROLLER CLEANUP",
        "Moves menu IPC to controller API",
        "Hides auto menu state files",
        "Keeps screenmenu nonblocking",
        "Keeps blindmenu rescue foreground",
        "Preserves app/menu UX",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.10", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0834(void) {
    const char *lines[] = {
        "0.9.9 v109 STRUCTURE AUDIT 2",
        "Audits post-v108 module debt",
        "Keeps user behavior unchanged",
        "Records next cleanup boundaries",
        "Refreshes latest build markers",
        "Prepares v110 controller cleanup",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.9", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0833(void) {
    const char *lines[] = {
        "0.9.8 v108 APP INPUTMON API",
        "Splits input monitor renderer",
        "Adds a90_app_inputmon.c/h",
        "Moves raw key visual state",
        "Adds input layout screen",
        "Keeps input API unchanged",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.8", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0832(void) {
    const char *lines[] = {
        "0.9.7 v107 APP DISPLAYTEST API",
        "Splits displaytest renderer",
        "Adds a90_app_displaytest.c/h",
        "Moves cutoutcal drawing path",
        "Keeps display UX unchanged",
        "Preserves v106 ABOUT module",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.7", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0831(void) {
    const char *lines[] = {
        "0.9.6 v106 APP ABOUT API",
        "Splits ABOUT app renderer",
        "Adds a90_app_about.c/h",
        "Moves version/changelog screens",
        "Keeps menu routing stable",
        "Preserves v105 UX behavior",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.6", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0830(void) {
    const char *lines[] = {
        "0.9.6 v106 APP ABOUT API",
        "0.9.5 v105 SOAK RC",
        "Stabilization release candidate",
        "Adds host native soak validator",
        "Keeps Wi-Fi bring-up blocked",
        "Exercises serial/service/runtime checks",
        "Preserves v104 behavior",
    };

    return app_about_draw_lines("CHANGELOG / 0.9.5", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0829(void) {
    const char *lines[] = {
        "0.8.29 v98 HELPER DEPLOY",
        "Adds a90_helper.c/h",
        "Adds helpers shell command",
        "Tracks helper manifest",
        "Prefers verified runtime helper",
        "Keeps ramdisk fallback",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.29", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0828(void) {
    const char *lines[] = {
        "0.8.28 v97 SD RUNTIME ROOT",
        "Adds a90_runtime.c/h",
        "Defines SD runtime root",
        "Adds runtime shell command",
        "Adds runtime selftest entry",
        "Keeps cache fallback bootable",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.28", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0827(void) {
    const char *lines[] = {
        "0.8.27 v96 STRUCTURE AUDIT",
        "Audits module boundaries",
        "Checks stale direct access",
        "Checks duplicate lifecycle code",
        "Applies low-risk cleanup only",
        "Keeps v95 UX behavior",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.27", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0826(void) {
    const char *lines[] = {
        "0.8.26 v95 NETSERVICE USB API",
        "Adds a90_usb_gadget.c/h",
        "Adds a90_netservice.c/h",
        "Moves ACM UDC helpers",
        "Moves NCM tcpctl policy",
        "Keeps raw USB control",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.26", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0825(void) {
    const char *lines[] = {
        "0.8.25 v94 BOOT SELFTEST",
        "Adds a90_selftest.c/h API",
        "Runs safe boot selftest",
        "Shows pass/warn/fail summary",
        "Adds selftest shell command",
        "Keeps failures warn-only",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.25", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0824(void) {
    const char *lines[] = {
        "0.8.24 v93 STORAGE API",
        "Adds a90_storage.c/h API",
        "Moves boot storage state out",
        "Moves SD probe and fallback",
        "Moves storage/mountsd commands",
        "Keeps netservice unchanged",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.24", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0823(void) {
    const char *lines[] = {
        "0.8.23 v92 SHELL CONTROLLER",
        "Adds a90_shell.c/h API",
        "Adds a90_controller.c/h",
        "Moves last result to shell API",
        "Moves menu busy policy out",
        "Keeps command UX unchanged",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.23", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0822(void) {
    const char *lines[] = {
        "0.8.22 v91 CPUSTRESS HELPER",
        "Adds /bin/a90_cpustress helper",
        "Moves stress workers out of PID1",
        "Uses a90_run process groups",
        "Shell cpustress UX unchanged",
        "Menu CPU stress uses helper pid",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.22", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0821(void) {
    const char *lines[] = {
        "0.8.21 v90 METRICS API",
        "Adds shared a90_metrics.c/h",
        "Moves status sensor reads out",
        "HUD now renders snapshots",
        "CPU stress uses metrics API",
        "Keeps display/menu UX stable",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.21", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0820(void) {
    const char *lines[] = {
        "0.8.20 v89 MENU CONTROL API",
        "Adds shared a90_menu.c/h",
        "Moves menu model/state out",
        "screenmenu now returns quickly",
        "show/hide uses autohud IPC",
        "Keeps blindmenu as rescue path",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.20", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0819(void) {
    const char *lines[] = {
        "0.8.19 v88 HUD API",
        "Adds shared a90_hud.c/h",
        "Moves boot splash renderer out",
        "Moves status HUD renderer out",
        "Moves log tail panel renderer out",
        "Keeps menu/app routing stable",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.19", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0818(void) {
    const char *lines[] = {
        "0.8.18 v87 INPUT API",
        "Adds shared a90_input.c/h",
        "Moves gesture decoder API out",
        "Moves key wait helpers out",
        "Keeps menu/HUD UX stable",
        "Shows boot time as 0.1s",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.18", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0817(void) {
    const char *lines[] = {
        "0.8.17 v86 KMS DRAW API",
        "Adds shared a90_kms.c/h",
        "Adds shared a90_draw.c/h",
        "Hides KMS framebuffer state",
        "Moves draw primitives out",
        "Keeps HUD/menu behavior stable",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.17", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0816(void) {
    const char *lines[] = {
        "0.8.16 v85 RUN SERVICE API",
        "Adds shared a90_run.c/h",
        "Adds service PID registry",
        "Moves run wait/cancel helpers",
        "Tracks hud/tcpctl/adbd PIDs",
        "Keeps netservice policy stable",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.16", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0815(void) {
    const char *lines[] = {
        "0.8.15 v84 CMDPROTO API",
        "Adds shared a90_cmdproto.c/h",
        "Moves A90P1 frame helpers",
        "Moves cmdv1x argv decoder",
        "Keeps shell dispatch unchanged",
        "Preserves host protocol output",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.15", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0814(void) {
    const char *lines[] = {
        "0.8.14 v83 CONSOLE API",
        "Adds shared a90_console.c/h",
        "Moves console fd state out",
        "Moves attach/reattach API",
        "Moves readline/cancel polling",
        "Keeps cmdv1/shell unchanged",
        "Prepares cmdproto boundary work",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.14", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0813(void) {
    const char *lines[] = {
        "0.8.13 v82 LOG TIMELINE API",
        "Adds shared a90_log.c/h",
        "Adds shared a90_timeline.c/h",
        "Moves log path state out",
        "Moves timeline ring state out",
        "Keeps console/shell stable",
        "Prepares console boundary work",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.13", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0812(void) {
    const char *lines[] = {
        "0.8.12 v81 CONFIG UTIL API",
        "Adds shared a90_config.h",
        "Adds shared a90_util.c/h",
        "Moves common file helpers",
        "Moves time/errno helpers",
        "Keeps PID1 behavior stable",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.12", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0811(void) {
    const char *lines[] = {
        "0.8.11 v80 SOURCE MODULES",
        "Splits PID1 source by module",
        "Keeps one static /init binary",
        "Preserves v79 runtime behavior",
        "Groups core/display/input/menu",
        "Groups storage/network/shell",
        "Prepares future helper split",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.11", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v0810(void) {
    const char *lines[] = {
        "0.8.10 v79 BOOT SD PROBE",
        "Checks SD during boot",
        "Verifies expected ext4 UUID",
        "Mounts /mnt/sdext/a90 if OK",
        "Runs boot-time rw probe",
        "Shows splash probe progress",
        "Warns HUD on SD fallback",
        "Keeps /cache fallback safe",
        "Adds storage status command",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.10", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v089(void) {
    const char *lines[] = {
        "0.8.9 v78 SD WORKSPACE",
        "Added mountsd command",
        "Controls ext4 SD at /mnt/sdext",
        "Creates /mnt/sdext/a90 workspace",
        "Adds bin logs tmp rootfs images",
        "Supports ro rw off init status",
        "Status shows mount and free MB",
        "Keeps UFS for boot and rescue",
        "Moves experiments toward SD",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.9", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v088(void) {
    const char *lines[] = {
        "0.8.8 v77 DISPLAY TEST PAGES",
        "Split display test into pages",
        "Page 1 color and pixel format",
        "Page 2 font scale and wrap",
        "Page 3 safe/cutout reference",
        "Page 4 HUD/menu preview",
        "Added cutoutcal command/app",
        "VOL adjusts POWER changes field",
        "VOL up/down changes page",
        "displaytest [page] via shell",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.8", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v087(void) {
    const char *lines[] = {
        "0.8.7 v76 AT FRAGMENT FILTER",
        "Ignores short A/T fragments",
        "Covers A T AT ATA ATAT",
        "Keeps full AT probe filter",
        "Prevents unknown command spam",
        "Logs ignored fragment category",
        "Normal lowercase shell remains",
        "Keeps cmdv1/cmdv1x unchanged",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.7", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v086(void) {
    const char *lines[] = {
        "0.8.6 v75 QUIET IDLE REATTACH",
        "Idle serial reattach still active",
        "Interval increased to 60 seconds",
        "Success logs hidden for idle path",
        "Failures remain visible in log tail",
        "Manual reattach logs still visible",
        "Keeps recovery behavior unchanged",
        "Reduces live log tail noise",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.6", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v085(void) {
    const char *lines[] = {
        "0.8.5 v74 CMDV1 ARG ENCODING",
        "Added cmdv1x len:hex argv",
        "Keeps old cmdv1 token path",
        "Host a90ctl auto-selects format",
        "Whitespace args stay framed",
        "Special chars avoid raw fallback",
        "Decoder validates length and hex",
        "Prepared safer automation calls",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.5", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v084(void) {
    const char *lines[] = {
        "0.8.4 v73 CMDV1 PROTOCOL",
        "Added cmdv1 command wrapper",
        "Emits A90P1 BEGIN and END",
        "Reports rc errno duration flags",
        "Keeps normal shell output intact",
        "Unknown/busy states are framed",
        "Host a90ctl can parse results",
        "Bridge automation gets safer",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.4", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v083(void) {
    const char *lines[] = {
        "0.8.3 v72 DISPLAY TEST FIX",
        "Added TOOLS / DISPLAY TEST",
        "Added color/font/wrap grid screen",
        "Added cutout top slot guide",
        "Widened main safe-area grid",
        "Fixed XBGR8888 color packing",
        "Displaytest command draws directly",
        "Validated flash and framebuffer",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.3", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v082(void) {
    const char *lines[] = {
        "0.8.2 v71 MENU LOG TAIL",
        "Shared log tail panel renderer",
        "HUD hidden keeps log tail view",
        "HUD menu also shows live log tail",
        "screenmenu uses spare space too",
        "Log colors highlight failures/input",
        "Long log lines wrap on screen",
        "Busy gate allows safe commands",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.2", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v081(void) {
    const char *lines[] = {
        "0.8.1 v70 INPUT MONITOR APP",
        "Added TOOLS / INPUT MONITOR",
        "Shows raw DOWN/UP/REPEAT events",
        "Shows gap between input events",
        "Shows key hold duration on release",
        "Shows decoded gesture/action",
        "Added inputmonitor shell command",
        "All-buttons exits monitor app",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.1", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v080(void) {
    const char *lines[] = {
        "0.8.0 v69 INPUT GESTURE LAYOUT",
        "Added inputlayout command",
        "Added waitgesture debug command",
        "Single click keeps old controls",
        "Double/long volume page moves",
        "POWER double and VOL combo back",
        "POWER long reserved for safety",
        "screenmenu/blindmenu use gestures",
    };

    return app_about_draw_lines("CHANGELOG / 0.8.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v075(void) {
    const char *lines[] = {
        "0.7.5 v68 LOG TAIL + HISTORY",
        "HUD menu hidden: log tail display",
        "HUD menu visible: item summary shown",
        "Changelog: 14 versions from v1",
        "Added v68 v61 v59 v55 v53 v40 v1",
        "Detail screens for all versions",
        "Log reads /cache/native-init.log",
        "Tail shows last 14 lines",
    };

    return app_about_draw_lines("CHANGELOG / 0.7.5", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v074(void) {
    const char *lines[] = {
        "0.7.4 v67 DETAIL CHANGELOG UI",
        "ABOUT text scale reduced",
        "VERSION/CREDITS use compact text",
        "CHANGELOG opens version list",
        "Each version opens detail screen",
        "Longer notes fit vertical display",
        "Current build remains visible",
        "Footer kept press-any-button",
    };

    return app_about_draw_lines("CHANGELOG / 0.7.4", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v073(void) {
    const char *lines[] = {
        "0.7.3 v66 ABOUT + VERSIONING",
        "Added semantic version display",
        "Added made by temmie0214",
        "Added APPS / ABOUT folder",
        "Added VERSION screen",
        "Added CHANGELOG summary screen",
        "Added CREDITS screen",
        "Updated version command output",
        "Updated status creator output",
        "Added VERSIONING.md and CHANGELOG.md",
    };

    return app_about_draw_lines("CHANGELOG / 0.7.3", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v072(void) {
    const char *lines[] = {
        "0.7.2 v65 SPLASH SAFE LAYOUT",
        "Reduced boot splash text scale",
        "Widened safe screen margins",
        "Shortened status rows",
        "Moved footer into safe area",
        "Avoided punch-hole overlap",
        "Verified visible splash layout",
        "Kept auto HUD transition",
    };

    return app_about_draw_lines("CHANGELOG / 0.7.2", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v071(void) {
    const char *lines[] = {
        "0.7.1 v64 CUSTOM BOOT SPLASH",
        "Replaced TEST boot screen",
        "Added A90 NATIVE INIT splash",
        "Added boot summary text",
        "Recorded display-splash timeline",
        "Kept shell handoff stable",
        "Kept status HUD after boot",
    };

    return app_about_draw_lines("CHANGELOG / 0.7.1", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v070(void) {
    const char *lines[] = {
        "0.7.0 v63 APP MENU",
        "Added APPS hierarchy",
        "Added MONITORING folder",
        "Added TOOLS folder",
        "Added LOGS folder",
        "Added CPU STRESS duration menu",
        "Kept app screens persistent",
        "Improved physical button flow",
    };

    return app_about_draw_lines("CHANGELOG / 0.7.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v060(void) {
    const char *lines[] = {
        "0.6.0 v62 CPU DIAGNOSTICS",
        "Added cpustress command",
        "Added CPU usage display",
        "Added temperature visibility",
        "Validated usage change under load",
        "Added /dev/null guard",
        "Added /dev/zero guard",
    };

    return app_about_draw_lines("CHANGELOG / 0.6.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v051(void) {
    const char *lines[] = {
        "0.5.1 v61 CPU/GPU USAGE HUD",
        "Added CPU usage percent to HUD",
        "Added GPU usage percent to HUD",
        "Read from /sys/kernel/gpu/gpu_busy",
        "Read /proc/stat for CPU idle delta",
        "Display: CPU temp usage GPU temp usage",
        "Verified readout updates live",
    };

    return app_about_draw_lines("CHANGELOG / 0.5.1", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v050(void) {
    const char *lines[] = {
        "0.5.0 v60 NETSERVICE BOOT",
        "Added opt-in boot-time netservice",
        "Flag: /cache/native-init-netservice",
        "Flag absent: ACM only at boot",
        "netservice enable/disable commands",
        "netservice stop/start for reconnect",
        "Validated UDC re-enum + NCM restore",
        "Host NCM interface name may change",
    };

    return app_about_draw_lines("CHANGELOG / 0.5.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v041(void) {
    const char *lines[] = {
        "0.4.1 v59 AT SERIAL FILTER",
        "Host modem probe sends AT commands",
        "AT/ATE0/AT+... lines ignored by shell",
        "Filter in native init input path",
        "No bridge-side workaround needed",
        "Stable ACM session under NetworkManager",
    };

    return app_about_draw_lines("CHANGELOG / 0.4.1", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v040(void) {
    const char *lines[] = {
        "0.4.0 v55 NCM TCP CONTROL",
        "USB NCM persistent composite gadget",
        "IPv6 netcat payload verified (v54)",
        "NCM ops helper: a90_usbnet",
        "TCP test helper: a90_nettest",
        "TCP control server: a90_tcpctl",
        "Host wrapper: a90ctl launch/client",
        "Soak validation: 100 round trips",
    };

    return app_about_draw_lines("CHANGELOG / 0.4.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v030(void) {
    const char *lines[] = {
        "0.3.0 v53 MENU BUSY GATE",
        "Hardware key menu always visible",
        "VOLUP/DN move POWER select",
        "Menu items: HIDE STATUS LOG",
        "Menu items: RECOVERY REBOOT POWEROFF",
        "Bridge busy gate: hide before recovery",
        "IPC via /tmp/a90-auto-menu-active",
        "bridge hide command clears menu",
    };

    return app_about_draw_lines("CHANGELOG / 0.3.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v020(void) {
    const char *lines[] = {
        "0.2.0 v40-v45 SHELL LOG HUD CORE",
        "Shell command dispatch stabilized",
        "Structured logging to /cache",
        "Boot timeline recording",
        "KMS/DRM status HUD: 4 rows scale 5",
        "BAT+PWR combined row",
        "Punch-hole camera y offset",
        "Per-segment label/value color split",
    };

    return app_about_draw_lines("CHANGELOG / 0.2.0", lines, SCREEN_MENU_COUNT(lines));
}

static int draw_screen_changelog_v010(void) {
    const char *lines[] = {
        "0.1.0 v1 NATIVE INIT ORIGIN",
        "PID 1 native C init confirmed",
        "KMS/DRM dumb buffer rendering",
        "5x7 bitmap font renderer",
        "USB CDC ACM serial shell",
        "TCP bridge 127.0.0.1:54321",
        "Input event probing (event0/3)",
        "Blind menu for button control",
    };

    return app_about_draw_lines("CHANGELOG / 0.1.0", lines, SCREEN_MENU_COUNT(lines));
}

int a90_app_about_draw_changelog_detail(enum screen_app_id app_id) {
    switch (app_id) {
    case SCREEN_APP_CHANGELOG_0838:
        return draw_screen_changelog_v0838();
    case SCREEN_APP_CHANGELOG_0837:
        return draw_screen_changelog_v0837();
    case SCREEN_APP_CHANGELOG_0836:
        return draw_screen_changelog_v0836();
    case SCREEN_APP_CHANGELOG_0835:
        return draw_screen_changelog_v0835();
    case SCREEN_APP_CHANGELOG_0834:
        return draw_screen_changelog_v0834();
    case SCREEN_APP_CHANGELOG_0833:
        return draw_screen_changelog_v0833();
    case SCREEN_APP_CHANGELOG_0832:
        return draw_screen_changelog_v0832();
    case SCREEN_APP_CHANGELOG_0831:
        return draw_screen_changelog_v0831();
    case SCREEN_APP_CHANGELOG_0830:
        return draw_screen_changelog_v0830();
    case SCREEN_APP_CHANGELOG_0829:
        return draw_screen_changelog_v0829();
    case SCREEN_APP_CHANGELOG_0828:
        return draw_screen_changelog_v0828();
    case SCREEN_APP_CHANGELOG_0827:
        return draw_screen_changelog_v0827();
    case SCREEN_APP_CHANGELOG_0826:
        return draw_screen_changelog_v0826();
    case SCREEN_APP_CHANGELOG_0825:
        return draw_screen_changelog_v0825();
    case SCREEN_APP_CHANGELOG_0824:
        return draw_screen_changelog_v0824();
    case SCREEN_APP_CHANGELOG_0823:
        return draw_screen_changelog_v0823();
    case SCREEN_APP_CHANGELOG_0822:
        return draw_screen_changelog_v0822();
    case SCREEN_APP_CHANGELOG_0821:
        return draw_screen_changelog_v0821();
    case SCREEN_APP_CHANGELOG_0820:
        return draw_screen_changelog_v0820();
    case SCREEN_APP_CHANGELOG_0819:
        return draw_screen_changelog_v0819();
    case SCREEN_APP_CHANGELOG_0818:
        return draw_screen_changelog_v0818();
    case SCREEN_APP_CHANGELOG_0817:
        return draw_screen_changelog_v0817();
    case SCREEN_APP_CHANGELOG_0816:
        return draw_screen_changelog_v0816();
    case SCREEN_APP_CHANGELOG_0815:
        return draw_screen_changelog_v0815();
    case SCREEN_APP_CHANGELOG_0814:
        return draw_screen_changelog_v0814();
    case SCREEN_APP_CHANGELOG_0813:
        return draw_screen_changelog_v0813();
    case SCREEN_APP_CHANGELOG_0812:
        return draw_screen_changelog_v0812();
    case SCREEN_APP_CHANGELOG_0811:
        return draw_screen_changelog_v0811();
    case SCREEN_APP_CHANGELOG_0810:
        return draw_screen_changelog_v0810();
    case SCREEN_APP_CHANGELOG_089:
        return draw_screen_changelog_v089();
    case SCREEN_APP_CHANGELOG_088:
        return draw_screen_changelog_v088();
    case SCREEN_APP_CHANGELOG_087:
        return draw_screen_changelog_v087();
    case SCREEN_APP_CHANGELOG_086:
        return draw_screen_changelog_v086();
    case SCREEN_APP_CHANGELOG_085:
        return draw_screen_changelog_v085();
    case SCREEN_APP_CHANGELOG_084:
        return draw_screen_changelog_v084();
    case SCREEN_APP_CHANGELOG_083:
        return draw_screen_changelog_v083();
    case SCREEN_APP_CHANGELOG_082:
        return draw_screen_changelog_v082();
    case SCREEN_APP_CHANGELOG_081:
        return draw_screen_changelog_v081();
    case SCREEN_APP_CHANGELOG_080:
        return draw_screen_changelog_v080();
    case SCREEN_APP_CHANGELOG_075:
        return draw_screen_changelog_v075();
    case SCREEN_APP_CHANGELOG_074:
        return draw_screen_changelog_v074();
    case SCREEN_APP_CHANGELOG_073:
        return draw_screen_changelog_v073();
    case SCREEN_APP_CHANGELOG_072:
        return draw_screen_changelog_v072();
    case SCREEN_APP_CHANGELOG_071:
        return draw_screen_changelog_v071();
    case SCREEN_APP_CHANGELOG_070:
        return draw_screen_changelog_v070();
    case SCREEN_APP_CHANGELOG_060:
        return draw_screen_changelog_v060();
    case SCREEN_APP_CHANGELOG_051:
        return draw_screen_changelog_v051();
    case SCREEN_APP_CHANGELOG_050:
        return draw_screen_changelog_v050();
    case SCREEN_APP_CHANGELOG_041:
        return draw_screen_changelog_v041();
    case SCREEN_APP_CHANGELOG_040:
        return draw_screen_changelog_v040();
    case SCREEN_APP_CHANGELOG_030:
        return draw_screen_changelog_v030();
    case SCREEN_APP_CHANGELOG_020:
        return draw_screen_changelog_v020();
    case SCREEN_APP_CHANGELOG_010:
        return draw_screen_changelog_v010();
    default:
        return 0;
    }
}

int a90_app_about_draw_credits(void) {
    const char *lines[] = {
        INIT_CREATOR,
        "DEVICE SAMSUNG GALAXY A90 5G",
        "MODEL SM-A908N",
        "KERNEL SAMSUNG STOCK 4.14",
        "CONTROL USB ACM + NCM",
        "PROJECT NATIVE INIT USERSPACE",
    };

    return app_about_draw_lines("ABOUT / CREDITS", lines, SCREEN_MENU_COUNT(lines));
}

int a90_app_about_draw(enum screen_app_id app_id) {
    switch (app_id) {
    case SCREEN_APP_ABOUT_VERSION:
        return a90_app_about_draw_version();
    case SCREEN_APP_ABOUT_CHANGELOG:
        return a90_app_about_draw_changelog();
    case SCREEN_APP_ABOUT_CREDITS:
        return a90_app_about_draw_credits();
    default:
        if (a90_menu_app_is_about(app_id)) {
            return a90_app_about_draw_changelog_detail(app_id);
        }
        return 0;
    }
}
