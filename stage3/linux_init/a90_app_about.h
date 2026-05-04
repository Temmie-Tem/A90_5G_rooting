#ifndef A90_APP_ABOUT_H
#define A90_APP_ABOUT_H

#include "a90_menu.h"

int a90_app_about_draw(enum screen_app_id app_id);
int a90_app_about_draw_version(void);
int a90_app_about_draw_changelog(void);
int a90_app_about_draw_changelog_detail(enum screen_app_id app_id);
int a90_app_about_draw_credits(void);

#endif
