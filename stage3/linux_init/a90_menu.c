#include "a90_menu.h"

static const struct screen_menu_item screen_menu_main_items[] = {
    { "APPS >",    "OPEN APP FOLDERS", SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_APPS },
    { "STATUS",    "LIVE SYSTEM VIEW", SCREEN_MENU_STATUS, SCREEN_MENU_PAGE_MAIN },
    { "NETWORK >", "NCM AND TCPCTL",   SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_NETWORK },
    { "POWER >",   "REBOOT OPTIONS",   SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_POWER },
    { "HIDE MENU", "RETURN TO HUD",    SCREEN_MENU_RESUME, SCREEN_MENU_PAGE_MAIN },
};

static const struct screen_menu_item screen_menu_apps_items[] = {
    { "ABOUT >",      "VERSION AND CREDITS", SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_ABOUT },
    { "MONITORING >", "STATUS APPLETS", SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_MONITORING },
    { "TOOLS >",      "TEST HELPERS",   SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_TOOLS },
    { "LOGS >",       "LOG VIEWERS",    SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_LOGS },
    { "BACK",         "MAIN MENU",      SCREEN_MENU_BACK,    SCREEN_MENU_PAGE_MAIN },
};

static const struct screen_menu_item screen_menu_about_items[] = {
    { "VERSION",     "CURRENT BUILD",   SCREEN_MENU_ABOUT_VERSION,  SCREEN_MENU_PAGE_ABOUT },
    { "CHANGELOG >", "VERSION DETAILS", SCREEN_MENU_SUBMENU,        SCREEN_MENU_PAGE_CHANGELOG },
    { "CREDITS",     "MADE BY",         SCREEN_MENU_ABOUT_CREDITS,  SCREEN_MENU_PAGE_ABOUT },
    { "BACK",        "APPS",            SCREEN_MENU_BACK,           SCREEN_MENU_PAGE_APPS },
};

static const struct screen_menu_item screen_menu_changelog_items[] = {
    { "0.8.24 v93", "STORAGE API",       SCREEN_MENU_CHANGELOG_0824, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.23 v92", "SHELL CONTROLLER",  SCREEN_MENU_CHANGELOG_0823, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.22 v91", "CPUSTRESS HELPER",   SCREEN_MENU_CHANGELOG_0822, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.21 v90", "METRICS API",        SCREEN_MENU_CHANGELOG_0821, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.20 v89", "MENU CONTROL API",   SCREEN_MENU_CHANGELOG_0820, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.19 v88", "HUD API",            SCREEN_MENU_CHANGELOG_0819, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.18 v87", "INPUT API",          SCREEN_MENU_CHANGELOG_0818, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.17 v86", "KMS DRAW API",      SCREEN_MENU_CHANGELOG_0817, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.16 v85", "RUN SERVICE API",    SCREEN_MENU_CHANGELOG_0816, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.15 v84", "CMDPROTO API",       SCREEN_MENU_CHANGELOG_0815, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.14 v83", "CONSOLE API",        SCREEN_MENU_CHANGELOG_0814, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.13 v82", "LOG TIMELINE API",   SCREEN_MENU_CHANGELOG_0813, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.12 v81", "CONFIG UTIL API",    SCREEN_MENU_CHANGELOG_0812, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.11 v80", "SOURCE MODULES",     SCREEN_MENU_CHANGELOG_0811, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.10 v79", "BOOT SD PROBE",      SCREEN_MENU_CHANGELOG_0810, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.9 v78", "SD WORKSPACE",         SCREEN_MENU_CHANGELOG_089, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.8 v77", "DISPLAY TEST PAGES",   SCREEN_MENU_CHANGELOG_088, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.7 v76", "AT FRAGMENT FILTER",    SCREEN_MENU_CHANGELOG_087, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.6 v75", "QUIET IDLE REATTACH",  SCREEN_MENU_CHANGELOG_086, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.5 v74", "CMDV1 ARG ENCODING",   SCREEN_MENU_CHANGELOG_085, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.4 v73", "CMDV1 PROTOCOL",       SCREEN_MENU_CHANGELOG_084, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.3 v72", "DISPLAY TEST FIX",     SCREEN_MENU_CHANGELOG_083, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.2 v71", "MENU LOG TAIL",        SCREEN_MENU_CHANGELOG_082, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.1 v70", "INPUT MONITOR APP",    SCREEN_MENU_CHANGELOG_081, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.8.0 v69", "INPUT GESTURE LAYOUT", SCREEN_MENU_CHANGELOG_080, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.7.5 v68", "LOG TAIL + HISTORY",  SCREEN_MENU_CHANGELOG_075, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.7.4 v67", "DETAIL CHANGELOG UI", SCREEN_MENU_CHANGELOG_074, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.7.3 v66", "ABOUT + VERSIONING",  SCREEN_MENU_CHANGELOG_073, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.7.2 v65", "SPLASH SAFE LAYOUT",  SCREEN_MENU_CHANGELOG_072, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.7.1 v64", "CUSTOM BOOT SPLASH",  SCREEN_MENU_CHANGELOG_071, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.7.0 v63", "APP MENU",            SCREEN_MENU_CHANGELOG_070, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.6.0 v62", "CPU DIAGNOSTICS",     SCREEN_MENU_CHANGELOG_060, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.5.1 v61", "CPU/GPU USAGE HUD",  SCREEN_MENU_CHANGELOG_051, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.5.0 v60", "NETSERVICE BOOT",    SCREEN_MENU_CHANGELOG_050, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.4.1 v59", "AT SERIAL FILTER",   SCREEN_MENU_CHANGELOG_041, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.4.0 v55", "NCM TCP CONTROL",    SCREEN_MENU_CHANGELOG_040, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.3.0 v53", "MENU BUSY GATE",     SCREEN_MENU_CHANGELOG_030, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.2.0 v40", "SHELL LOG HUD CORE", SCREEN_MENU_CHANGELOG_020, SCREEN_MENU_PAGE_CHANGELOG },
    { "0.1.0 v1",  "NATIVE INIT ORIGIN", SCREEN_MENU_CHANGELOG_010, SCREEN_MENU_PAGE_CHANGELOG },
    { "BACK",      "ABOUT",              SCREEN_MENU_BACK,           SCREEN_MENU_PAGE_ABOUT },
};

static const struct screen_menu_item screen_menu_monitoring_items[] = {
    { "LIVE STATUS", "DRAW STATUS HUD", SCREEN_MENU_STATUS, SCREEN_MENU_PAGE_MONITORING },
    { "BACK",        "APPS",            SCREEN_MENU_BACK,   SCREEN_MENU_PAGE_APPS },
};

static const struct screen_menu_item screen_menu_tools_items[] = {
    { "INPUT MONITOR", "RAW KEY + GESTURE LOG", SCREEN_MENU_INPUT_MONITOR, SCREEN_MENU_PAGE_TOOLS },
    { "DISPLAY TEST",  "COLORS FONT GRID",      SCREEN_MENU_DISPLAY_TEST,  SCREEN_MENU_PAGE_TOOLS },
    { "CUTOUT CAL",    "ALIGN CAMERA HOLE",     SCREEN_MENU_CUTOUT_CAL,   SCREEN_MENU_PAGE_TOOLS },
    { "CPU STRESS >", "SELECT TEST TIME", SCREEN_MENU_SUBMENU, SCREEN_MENU_PAGE_CPU_STRESS },
    { "BACK",         "APPS",             SCREEN_MENU_BACK,    SCREEN_MENU_PAGE_APPS },
};

static const struct screen_menu_item screen_menu_cpu_stress_items[] = {
    { "5 SECONDS",  "QUICK CHECK",     SCREEN_MENU_CPU_STRESS_5,  SCREEN_MENU_PAGE_CPU_STRESS },
    { "10 SECONDS", "DEFAULT CHECK",   SCREEN_MENU_CPU_STRESS_10, SCREEN_MENU_PAGE_CPU_STRESS },
    { "30 SECONDS", "THERMAL SAMPLE",  SCREEN_MENU_CPU_STRESS_30, SCREEN_MENU_PAGE_CPU_STRESS },
    { "60 SECONDS", "LONGER SAMPLE",   SCREEN_MENU_CPU_STRESS_60, SCREEN_MENU_PAGE_CPU_STRESS },
    { "BACK",       "TOOLS",           SCREEN_MENU_BACK,          SCREEN_MENU_PAGE_TOOLS },
};

static const struct screen_menu_item screen_menu_logs_items[] = {
    { "LOG SUMMARY", "BOOT/COMMAND LOG", SCREEN_MENU_LOG,  SCREEN_MENU_PAGE_LOGS },
    { "BACK",        "APPS",             SCREEN_MENU_BACK, SCREEN_MENU_PAGE_APPS },
};

static const struct screen_menu_item screen_menu_network_items[] = {
    { "NET STATUS", "NCM/TCPCTL STATE", SCREEN_MENU_NET_STATUS, SCREEN_MENU_PAGE_NETWORK },
    { "BACK",       "MAIN MENU",        SCREEN_MENU_BACK,       SCREEN_MENU_PAGE_MAIN },
};

static const struct screen_menu_item screen_menu_power_items[] = {
    { "RECOVERY", "REBOOT TO TWRP", SCREEN_MENU_RECOVERY, SCREEN_MENU_PAGE_POWER },
    { "REBOOT",   "RESTART DEVICE", SCREEN_MENU_REBOOT,   SCREEN_MENU_PAGE_POWER },
    { "POWEROFF", "POWER OFF",      SCREEN_MENU_POWEROFF, SCREEN_MENU_PAGE_POWER },
    { "BACK",     "MAIN MENU",      SCREEN_MENU_BACK,     SCREEN_MENU_PAGE_MAIN },
};

static const struct screen_menu_page screen_menu_pages[SCREEN_MENU_PAGE_COUNT] = {
    [SCREEN_MENU_PAGE_MAIN] = {
        "MAIN MENU", screen_menu_main_items,
        SCREEN_MENU_COUNT(screen_menu_main_items), SCREEN_MENU_PAGE_MAIN
    },
    [SCREEN_MENU_PAGE_APPS] = {
        "APPS", screen_menu_apps_items,
        SCREEN_MENU_COUNT(screen_menu_apps_items), SCREEN_MENU_PAGE_MAIN
    },
    [SCREEN_MENU_PAGE_ABOUT] = {
        "APPS / ABOUT", screen_menu_about_items,
        SCREEN_MENU_COUNT(screen_menu_about_items), SCREEN_MENU_PAGE_APPS
    },
    [SCREEN_MENU_PAGE_CHANGELOG] = {
        "ABOUT / CHANGELOG", screen_menu_changelog_items,
        SCREEN_MENU_COUNT(screen_menu_changelog_items), SCREEN_MENU_PAGE_ABOUT
    },
    [SCREEN_MENU_PAGE_MONITORING] = {
        "APPS / MONITORING", screen_menu_monitoring_items,
        SCREEN_MENU_COUNT(screen_menu_monitoring_items), SCREEN_MENU_PAGE_APPS
    },
    [SCREEN_MENU_PAGE_TOOLS] = {
        "APPS / TOOLS", screen_menu_tools_items,
        SCREEN_MENU_COUNT(screen_menu_tools_items), SCREEN_MENU_PAGE_APPS
    },
    [SCREEN_MENU_PAGE_CPU_STRESS] = {
        "TOOLS / CPU STRESS", screen_menu_cpu_stress_items,
        SCREEN_MENU_COUNT(screen_menu_cpu_stress_items), SCREEN_MENU_PAGE_TOOLS
    },
    [SCREEN_MENU_PAGE_LOGS] = {
        "APPS / LOGS", screen_menu_logs_items,
        SCREEN_MENU_COUNT(screen_menu_logs_items), SCREEN_MENU_PAGE_APPS
    },
    [SCREEN_MENU_PAGE_NETWORK] = {
        "NETWORK", screen_menu_network_items,
        SCREEN_MENU_COUNT(screen_menu_network_items), SCREEN_MENU_PAGE_MAIN
    },
    [SCREEN_MENU_PAGE_POWER] = {
        "POWER", screen_menu_power_items,
        SCREEN_MENU_COUNT(screen_menu_power_items), SCREEN_MENU_PAGE_MAIN
    },
};

const struct screen_menu_page *a90_menu_page(enum screen_menu_page_id page_id) {
    if ((int)page_id < 0 || page_id >= SCREEN_MENU_PAGE_COUNT) {
        page_id = SCREEN_MENU_PAGE_MAIN;
    }
    return &screen_menu_pages[page_id];
}

long a90_menu_cpu_stress_seconds(enum screen_menu_action action) {
    switch (action) {
    case SCREEN_MENU_CPU_STRESS_5:
        return 5;
    case SCREEN_MENU_CPU_STRESS_10:
        return 10;
    case SCREEN_MENU_CPU_STRESS_30:
        return 30;
    case SCREEN_MENU_CPU_STRESS_60:
        return 60;
    default:
        return 0;
    }
}

enum screen_app_id a90_menu_app_from_action(enum screen_menu_action action) {
    switch (action) {
    case SCREEN_MENU_ABOUT_VERSION:
        return SCREEN_APP_ABOUT_VERSION;
    case SCREEN_MENU_ABOUT_CHANGELOG:
        return SCREEN_APP_ABOUT_CHANGELOG;
    case SCREEN_MENU_ABOUT_CREDITS:
        return SCREEN_APP_ABOUT_CREDITS;
    case SCREEN_MENU_CHANGELOG_0824:
        return SCREEN_APP_CHANGELOG_0824;
    case SCREEN_MENU_CHANGELOG_0823:
        return SCREEN_APP_CHANGELOG_0823;
    case SCREEN_MENU_CHANGELOG_0822:
        return SCREEN_APP_CHANGELOG_0822;
    case SCREEN_MENU_CHANGELOG_0821:
        return SCREEN_APP_CHANGELOG_0821;
    case SCREEN_MENU_CHANGELOG_0820:
        return SCREEN_APP_CHANGELOG_0820;
    case SCREEN_MENU_CHANGELOG_0819:
        return SCREEN_APP_CHANGELOG_0819;
    case SCREEN_MENU_CHANGELOG_0818:
        return SCREEN_APP_CHANGELOG_0818;
    case SCREEN_MENU_CHANGELOG_0817:
        return SCREEN_APP_CHANGELOG_0817;
    case SCREEN_MENU_CHANGELOG_0816:
        return SCREEN_APP_CHANGELOG_0816;
    case SCREEN_MENU_CHANGELOG_0815:
        return SCREEN_APP_CHANGELOG_0815;
    case SCREEN_MENU_CHANGELOG_0814:
        return SCREEN_APP_CHANGELOG_0814;
    case SCREEN_MENU_CHANGELOG_0813:
        return SCREEN_APP_CHANGELOG_0813;
    case SCREEN_MENU_CHANGELOG_0812:
        return SCREEN_APP_CHANGELOG_0812;
    case SCREEN_MENU_CHANGELOG_0811:
        return SCREEN_APP_CHANGELOG_0811;
    case SCREEN_MENU_CHANGELOG_0810:
        return SCREEN_APP_CHANGELOG_0810;
    case SCREEN_MENU_CHANGELOG_089:
        return SCREEN_APP_CHANGELOG_089;
    case SCREEN_MENU_CHANGELOG_088:
        return SCREEN_APP_CHANGELOG_088;
    case SCREEN_MENU_CHANGELOG_087:
        return SCREEN_APP_CHANGELOG_087;
    case SCREEN_MENU_CHANGELOG_086:
        return SCREEN_APP_CHANGELOG_086;
    case SCREEN_MENU_CHANGELOG_085:
        return SCREEN_APP_CHANGELOG_085;
    case SCREEN_MENU_CHANGELOG_084:
        return SCREEN_APP_CHANGELOG_084;
    case SCREEN_MENU_CHANGELOG_083:
        return SCREEN_APP_CHANGELOG_083;
    case SCREEN_MENU_CHANGELOG_082:
        return SCREEN_APP_CHANGELOG_082;
    case SCREEN_MENU_CHANGELOG_081:
        return SCREEN_APP_CHANGELOG_081;
    case SCREEN_MENU_CHANGELOG_080:
        return SCREEN_APP_CHANGELOG_080;
    case SCREEN_MENU_CHANGELOG_075:
        return SCREEN_APP_CHANGELOG_075;
    case SCREEN_MENU_CHANGELOG_074:
        return SCREEN_APP_CHANGELOG_074;
    case SCREEN_MENU_CHANGELOG_073:
        return SCREEN_APP_CHANGELOG_073;
    case SCREEN_MENU_CHANGELOG_072:
        return SCREEN_APP_CHANGELOG_072;
    case SCREEN_MENU_CHANGELOG_071:
        return SCREEN_APP_CHANGELOG_071;
    case SCREEN_MENU_CHANGELOG_070:
        return SCREEN_APP_CHANGELOG_070;
    case SCREEN_MENU_CHANGELOG_060:
        return SCREEN_APP_CHANGELOG_060;
    case SCREEN_MENU_CHANGELOG_051:
        return SCREEN_APP_CHANGELOG_051;
    case SCREEN_MENU_CHANGELOG_050:
        return SCREEN_APP_CHANGELOG_050;
    case SCREEN_MENU_CHANGELOG_041:
        return SCREEN_APP_CHANGELOG_041;
    case SCREEN_MENU_CHANGELOG_040:
        return SCREEN_APP_CHANGELOG_040;
    case SCREEN_MENU_CHANGELOG_030:
        return SCREEN_APP_CHANGELOG_030;
    case SCREEN_MENU_CHANGELOG_020:
        return SCREEN_APP_CHANGELOG_020;
    case SCREEN_MENU_CHANGELOG_010:
        return SCREEN_APP_CHANGELOG_010;
    default:
        return SCREEN_APP_NONE;
    }
}


void a90_menu_state_init(struct a90_menu_state *state) {
    if (state == NULL) {
        return;
    }
    state->page = SCREEN_MENU_PAGE_MAIN;
    state->selected = 0;
}

const struct screen_menu_page *a90_menu_state_page(const struct a90_menu_state *state) {
    if (state == NULL) {
        return a90_menu_page(SCREEN_MENU_PAGE_MAIN);
    }
    return a90_menu_page(state->page);
}

enum screen_menu_page_id a90_menu_state_page_id(const struct a90_menu_state *state) {
    if (state == NULL) {
        return SCREEN_MENU_PAGE_MAIN;
    }
    return state->page;
}

size_t a90_menu_state_selected_index(const struct a90_menu_state *state) {
    const struct screen_menu_page *page;

    if (state == NULL) {
        return 0;
    }
    page = a90_menu_page(state->page);
    if (page->count == 0) {
        return 0;
    }
    if (state->selected >= page->count) {
        return page->count - 1;
    }
    return state->selected;
}

const struct screen_menu_item *a90_menu_state_selected(const struct a90_menu_state *state) {
    const struct screen_menu_page *page = a90_menu_state_page(state);
    size_t selected = a90_menu_state_selected_index(state);

    if (page->count == 0) {
        return NULL;
    }
    return &page->items[selected];
}

void a90_menu_state_move(struct a90_menu_state *state, int delta) {
    const struct screen_menu_page *page;
    long selected;
    long count;

    if (state == NULL) {
        return;
    }
    page = a90_menu_page(state->page);
    if (page->count == 0) {
        state->selected = 0;
        return;
    }
    count = (long)page->count;
    selected = (long)a90_menu_state_selected_index(state) + (long)delta;
    selected %= count;
    if (selected < 0) {
        selected += count;
    }
    state->selected = (size_t)selected;
}

void a90_menu_state_set_page(struct a90_menu_state *state,
                             enum screen_menu_page_id page_id) {
    if (state == NULL) {
        return;
    }
    if ((int)page_id < 0 || page_id >= SCREEN_MENU_PAGE_COUNT) {
        page_id = SCREEN_MENU_PAGE_MAIN;
    }
    state->page = page_id;
    state->selected = 0;
}

bool a90_menu_state_back(struct a90_menu_state *state) {
    const struct screen_menu_page *page;

    if (state == NULL) {
        return false;
    }
    page = a90_menu_page(state->page);
    if (state->page == SCREEN_MENU_PAGE_MAIN) {
        state->selected = 0;
        return false;
    }
    state->page = page->parent;
    state->selected = 0;
    return true;
}

bool a90_menu_app_is_about(enum screen_app_id app_id) {
    switch (app_id) {
    case SCREEN_APP_ABOUT_VERSION:
    case SCREEN_APP_ABOUT_CHANGELOG:
    case SCREEN_APP_ABOUT_CREDITS:
    case SCREEN_APP_CHANGELOG_0824:
    case SCREEN_APP_CHANGELOG_0823:
    case SCREEN_APP_CHANGELOG_0822:
    case SCREEN_APP_CHANGELOG_0821:
    case SCREEN_APP_CHANGELOG_0820:
    case SCREEN_APP_CHANGELOG_0819:
    case SCREEN_APP_CHANGELOG_0818:
    case SCREEN_APP_CHANGELOG_0817:
    case SCREEN_APP_CHANGELOG_0816:
    case SCREEN_APP_CHANGELOG_0815:
    case SCREEN_APP_CHANGELOG_0814:
    case SCREEN_APP_CHANGELOG_0813:
    case SCREEN_APP_CHANGELOG_0812:
    case SCREEN_APP_CHANGELOG_0811:
    case SCREEN_APP_CHANGELOG_0810:
    case SCREEN_APP_CHANGELOG_089:
    case SCREEN_APP_CHANGELOG_088:
    case SCREEN_APP_CHANGELOG_087:
    case SCREEN_APP_CHANGELOG_086:
    case SCREEN_APP_CHANGELOG_085:
    case SCREEN_APP_CHANGELOG_084:
    case SCREEN_APP_CHANGELOG_083:
    case SCREEN_APP_CHANGELOG_082:
    case SCREEN_APP_CHANGELOG_081:
    case SCREEN_APP_CHANGELOG_080:
    case SCREEN_APP_CHANGELOG_075:
    case SCREEN_APP_CHANGELOG_074:
    case SCREEN_APP_CHANGELOG_073:
    case SCREEN_APP_CHANGELOG_072:
    case SCREEN_APP_CHANGELOG_071:
    case SCREEN_APP_CHANGELOG_070:
    case SCREEN_APP_CHANGELOG_060:
    case SCREEN_APP_CHANGELOG_051:
    case SCREEN_APP_CHANGELOG_050:
    case SCREEN_APP_CHANGELOG_041:
    case SCREEN_APP_CHANGELOG_040:
    case SCREEN_APP_CHANGELOG_030:
    case SCREEN_APP_CHANGELOG_020:
    case SCREEN_APP_CHANGELOG_010:
        return true;
    default:
        return false;
    }
}
