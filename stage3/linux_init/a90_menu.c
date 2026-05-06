#include "a90_menu.h"

#include "a90_changelog.h"

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

static struct screen_menu_item screen_menu_changelog_items[A90_CHANGELOG_MAX_ENTRIES + 1];
static struct screen_menu_page screen_menu_changelog_page = {
    "ABOUT / CHANGELOG",
    screen_menu_changelog_items,
    0,
    SCREEN_MENU_PAGE_ABOUT,
};
static bool screen_menu_changelog_ready;

static void screen_menu_init_changelog_page(void) {
    size_t count;
    size_t index;

    if (screen_menu_changelog_ready) {
        return;
    }

    count = a90_changelog_count();
    if (count > A90_CHANGELOG_MAX_ENTRIES) {
        count = A90_CHANGELOG_MAX_ENTRIES;
    }

    for (index = 0; index < count; ++index) {
        const struct a90_changelog_entry *entry = a90_changelog_entry_at(index);

        screen_menu_changelog_items[index].name = entry != NULL ? entry->label : "UNKNOWN";
        screen_menu_changelog_items[index].summary = entry != NULL ? entry->summary : "CHANGELOG";
        screen_menu_changelog_items[index].action = SCREEN_MENU_CHANGELOG_ENTRY;
        screen_menu_changelog_items[index].target = SCREEN_MENU_PAGE_CHANGELOG;
    }

    screen_menu_changelog_items[count].name = "BACK";
    screen_menu_changelog_items[count].summary = "ABOUT";
    screen_menu_changelog_items[count].action = SCREEN_MENU_BACK;
    screen_menu_changelog_items[count].target = SCREEN_MENU_PAGE_ABOUT;
    screen_menu_changelog_page.count = count + 1;
    screen_menu_changelog_ready = true;
}

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
    if (page_id == SCREEN_MENU_PAGE_CHANGELOG) {
        screen_menu_init_changelog_page();
        return &screen_menu_changelog_page;
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
    case SCREEN_MENU_CHANGELOG_ENTRY:
        return SCREEN_APP_CHANGELOG_DETAIL;
    case SCREEN_MENU_CHANGELOG_0847:
        return SCREEN_APP_CHANGELOG_0847;
    case SCREEN_MENU_CHANGELOG_0846:
        return SCREEN_APP_CHANGELOG_0846;
    case SCREEN_MENU_CHANGELOG_0845:
        return SCREEN_APP_CHANGELOG_0845;
    case SCREEN_MENU_CHANGELOG_0844:
        return SCREEN_APP_CHANGELOG_0844;
    case SCREEN_MENU_CHANGELOG_0843:
        return SCREEN_APP_CHANGELOG_0843;
    case SCREEN_MENU_CHANGELOG_0842:
        return SCREEN_APP_CHANGELOG_0842;
    case SCREEN_MENU_CHANGELOG_0841:
        return SCREEN_APP_CHANGELOG_0841;
    case SCREEN_MENU_CHANGELOG_0840:
        return SCREEN_APP_CHANGELOG_0840;
    case SCREEN_MENU_CHANGELOG_0839:
        return SCREEN_APP_CHANGELOG_0839;
    case SCREEN_MENU_CHANGELOG_0838:
        return SCREEN_APP_CHANGELOG_0838;
    case SCREEN_MENU_CHANGELOG_0837:
        return SCREEN_APP_CHANGELOG_0837;
    case SCREEN_MENU_CHANGELOG_0836:
        return SCREEN_APP_CHANGELOG_0836;
    case SCREEN_MENU_CHANGELOG_0835:
        return SCREEN_APP_CHANGELOG_0835;
    case SCREEN_MENU_CHANGELOG_0834:
        return SCREEN_APP_CHANGELOG_0834;
    case SCREEN_MENU_CHANGELOG_0833:
        return SCREEN_APP_CHANGELOG_0833;
    case SCREEN_MENU_CHANGELOG_0832:
        return SCREEN_APP_CHANGELOG_0832;
    case SCREEN_MENU_CHANGELOG_0831:
        return SCREEN_APP_CHANGELOG_0831;
    case SCREEN_MENU_CHANGELOG_0830:
        return SCREEN_APP_CHANGELOG_0830;
    case SCREEN_MENU_CHANGELOG_0829:
        return SCREEN_APP_CHANGELOG_0829;
    case SCREEN_MENU_CHANGELOG_0828:
        return SCREEN_APP_CHANGELOG_0828;
    case SCREEN_MENU_CHANGELOG_0827:
        return SCREEN_APP_CHANGELOG_0827;
    case SCREEN_MENU_CHANGELOG_0826:
        return SCREEN_APP_CHANGELOG_0826;
    case SCREEN_MENU_CHANGELOG_0825:
        return SCREEN_APP_CHANGELOG_0825;
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

bool a90_menu_action_opens_app(enum screen_menu_action action, enum screen_app_id *out) {
    enum screen_app_id app_id = a90_menu_app_from_action(action);

    if (out != NULL) {
        *out = app_id;
    }
    return app_id != SCREEN_APP_NONE;
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

bool a90_menu_app_is_changelog(enum screen_app_id app_id) {
    return app_id == SCREEN_APP_CHANGELOG_DETAIL ||
           (app_id >= SCREEN_APP_CHANGELOG_0847 &&
            app_id <= SCREEN_APP_CHANGELOG_010);
}

bool a90_menu_page_is_changelog(enum screen_menu_page_id page_id) {
    return page_id == SCREEN_MENU_PAGE_CHANGELOG;
}

bool a90_menu_app_is_about(enum screen_app_id app_id) {
    switch (app_id) {
    case SCREEN_APP_ABOUT_VERSION:
    case SCREEN_APP_ABOUT_CHANGELOG:
    case SCREEN_APP_ABOUT_CREDITS:
        return true;
    default:
        return a90_menu_app_is_changelog(app_id);
    }
}
