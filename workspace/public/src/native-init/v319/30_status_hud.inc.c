/* Included by the current native-init translation unit. Do not compile standalone. */

static struct a90_hud_storage_status current_hud_storage_status(void) {
    static struct a90_storage_status snapshot;
    static struct a90_runtime_status runtime;
    struct a90_hud_storage_status storage = {
        .backend = "unknown",
        .root = "",
        .warning = "",
    };

    if (a90_runtime_get_status(&runtime) == 0 && runtime.initialized) {
        storage.backend = runtime.backend;
        storage.root = runtime.root;
        storage.warning = runtime.warning;
    } else if (a90_storage_get_status(&snapshot) == 0) {
        storage.backend = snapshot.backend;
        storage.root = snapshot.root;
        storage.warning = snapshot.warning;
    }
    return storage;
}

static bool parse_color_arg(const char *arg, uint32_t *color_out) {
    unsigned int value;

    if (strcmp(arg, "black") == 0) {
        *color_out = 0x000000;
        return true;
    }
    if (strcmp(arg, "white") == 0) {
        *color_out = 0xffffff;
        return true;
    }
    if (strcmp(arg, "red") == 0) {
        *color_out = 0xff0000;
        return true;
    }
    if (strcmp(arg, "green") == 0) {
        *color_out = 0x00ff00;
        return true;
    }
    if (strcmp(arg, "blue") == 0) {
        *color_out = 0x0000ff;
        return true;
    }
    if (strcmp(arg, "gray") == 0 || strcmp(arg, "grey") == 0) {
        *color_out = 0x808080;
        return true;
    }
    if (sscanf(arg, "%x", &value) == 1) {
        *color_out = value & 0xffffffU;
        return true;
    }
    return false;
}

static int cmd_kmsprobe(void) {
    return a90_kms_probe(true);
}

static int cmd_video_status(void) {
    struct a90_kms_info info;

    a90_kms_info(&info);
    a90_console_printf("video.status.version=1\r\n");
    a90_console_printf("video.status.path=kms-dumb-buffer\r\n");
    a90_console_printf("video.status.venus=not-used\r\n");
    a90_console_printf("video.status.kgsl=not-used\r\n");
    a90_console_printf("video.status.raw_dsi=blocked\r\n");
    a90_console_printf("video.status.power_writes=blocked\r\n");
    a90_console_printf("video.status.kms.initialized=%d\r\n", info.initialized ? 1 : 0);
    if (info.initialized) {
        a90_console_printf("video.status.kms.size=%ux%u\r\n", info.width, info.height);
        a90_console_printf("video.status.kms.connector=%u\r\n", info.connector_id);
        a90_console_printf("video.status.kms.encoder=%u\r\n", info.encoder_id);
        a90_console_printf("video.status.kms.crtc=%u\r\n", info.crtc_id);
        a90_console_printf("video.status.kms.fb=%u\r\n", info.fb_id);
        a90_console_printf("video.status.kms.current_buffer=%u\r\n", info.current_buffer);
    } else {
        a90_console_printf("video.status.kms.size=0x0\r\n");
    }
    a90_console_printf("video.status.next=video frame [bars|checker|mono|0xRRGGBB]\r\n");
    return 0;
}

static void video_draw_bars(struct a90_fb *fb) {
    static const uint32_t colors[] = {
        0xffffff, 0xffff00, 0x00ffff, 0x00ff00,
        0xff00ff, 0xff0000, 0x0000ff, 0x202020,
    };
    uint32_t index;
    uint32_t bar_width;

    if (fb == NULL || fb->width == 0) {
        return;
    }
    bar_width = fb->width / (uint32_t)(sizeof(colors) / sizeof(colors[0]));
    if (bar_width == 0) {
        bar_width = 1;
    }
    for (index = 0; index < sizeof(colors) / sizeof(colors[0]); ++index) {
        uint32_t x = index * bar_width;
        uint32_t width = (index + 1 == sizeof(colors) / sizeof(colors[0])) ?
                         (fb->width > x ? fb->width - x : 0) :
                         bar_width;
        a90_draw_rect(fb, x, 0, width, fb->height, colors[index]);
    }
}

static void video_draw_checker(struct a90_fb *fb) {
    uint32_t tile;
    uint32_t y;

    if (fb == NULL) {
        return;
    }
    tile = fb->width / 12;
    if (tile < 32) {
        tile = 32;
    }
    for (y = 0; y < fb->height; y += tile) {
        uint32_t x;

        for (x = 0; x < fb->width; x += tile) {
            uint32_t color = (((x / tile) + (y / tile)) & 1U) ? 0x101820 : 0xd8e8ff;
            a90_draw_rect(fb, x, y, tile, tile, color);
        }
    }
}

static int cmd_video_frame(char **argv, int argc) {
    const char *pattern = argc >= 3 ? argv[2] : "bars";
    struct a90_fb *fb;
    uint32_t color = 0x05070c;
    bool solid = false;
    uint32_t scale;

    if (argc > 3) {
        a90_console_printf("usage: video frame [bars|checker|mono|0xRRGGBB]\r\n");
        return -EINVAL;
    }
    if (strcmp(pattern, "bars") != 0 &&
        strcmp(pattern, "checker") != 0 &&
        strcmp(pattern, "mono") != 0) {
        if (!parse_color_arg(pattern, &color)) {
            a90_console_printf("usage: video frame [bars|checker|mono|0xRRGGBB]\r\n");
            return -EINVAL;
        }
        solid = true;
    }

    if (a90_kms_begin_frame(color) < 0) {
        return negative_errno_or(ENODEV);
    }
    fb = a90_kms_framebuffer();
    if (fb == NULL) {
        return -ENODEV;
    }

    if (strcmp(pattern, "bars") == 0) {
        video_draw_bars(fb);
    } else if (strcmp(pattern, "checker") == 0) {
        video_draw_checker(fb);
    } else if (strcmp(pattern, "mono") == 0 || solid) {
        a90_draw_clear(fb, color);
    }

    scale = fb->width >= 1080 ? 4 : 2;
    a90_draw_rect(fb, 24, 24, fb->width > 48 ? fb->width - 48 : fb->width, scale * 18, 0x06101c);
    a90_draw_rect_outline(fb, 24, 24, fb->width > 48 ? fb->width - 48 : fb->width,
                          scale * 18, scale > 2 ? 2 : 1, 0x66ddff);
    a90_draw_text(fb, 24 + scale * 3, 24 + scale * 4, "A90 VIDEO FRAME", 0x66ddff, scale);
    a90_draw_text(fb, 24 + scale * 3, 24 + scale * 11, pattern, 0xffffff, scale > 2 ? 2 : 1);

    if (a90_kms_present("videoframe", true) < 0) {
        return negative_errno_or(EIO);
    }
    a90_console_printf("video.frame.presented=1\r\n");
    a90_console_printf("video.frame.pattern=%s\r\n", pattern);
    a90_console_printf("video.frame.size=%ux%u\r\n", fb->width, fb->height);
    a90_console_printf("video.frame.path=kms-dumb-buffer\r\n");
    return 0;
}

static int handle_video(char **argv, int argc) {
    const char *subcommand = argc > 1 ? argv[1] : "status";

    if (strcmp(subcommand, "status") == 0) {
        if (argc != 1 && argc != 2) {
            a90_console_printf("usage: video [status|frame [bars|checker|mono|0xRRGGBB]]\r\n");
            return -EINVAL;
        }
        return cmd_video_status();
    }
    if (strcmp(subcommand, "frame") == 0 || strcmp(subcommand, "demo") == 0) {
        return cmd_video_frame(argv, argc);
    }

    a90_console_printf("usage: video [status|frame [bars|checker|mono|0xRRGGBB]]\r\n");
    return -EINVAL;
}

static int cmd_kmssolid(char **argv, int argc) {
    uint32_t color = 0x000000;

    if (argc >= 2 && !parse_color_arg(argv[1], &color)) {
        a90_console_printf("usage: kmssolid [black|white|red|green|blue|gray|0xRRGGBB]\r\n");
        return -EINVAL;
    }

    if (a90_kms_begin_frame(color) < 0) {
        return negative_errno_or(ENODEV);
    }
    if (a90_kms_present("kmssolid", true) < 0) {
        return negative_errno_or(EIO);
    }
    return 0;
}

static int cmd_kmsframe(void) {
    if (a90_kms_begin_frame(0x080808) < 0) {
        return negative_errno_or(ENODEV);
    }
    a90_draw_boot_frame(a90_kms_framebuffer());
    if (a90_kms_present("kmsframe", true) < 0) {
        return negative_errno_or(EIO);
    }
    return 0;
}

static int cmd_statusscreen(void) {
    if (a90_kms_begin_frame(0x000000) < 0) {
        return negative_errno_or(ENODEV);
    }
    a90_console_printf("statusscreen: drawing giant TEST probe\r\n");
    a90_draw_giant_test_probe(a90_kms_framebuffer());
    if (a90_kms_present("statusscreen", true) < 0) {
        return negative_errno_or(EIO);
    }
    return 0;
}

static int cmd_statushud(void) {
    struct a90_hud_storage_status storage = current_hud_storage_status();

    a90_console_printf("statushud: drawing sensor HUD\r\n");
    return a90_hud_draw_status_frame(&storage, "statushud", true);
}

static int wait_watch_delay(int refresh_sec) {
    int remaining_ticks = refresh_sec * 10;

    while (remaining_ticks-- > 0) {
        enum a90_cancel_kind cancel = a90_console_poll_cancel(100);

        if (cancel != CANCEL_NONE) {
            return a90_console_cancelled("watchhud", cancel);
        }
    }

    return 0;
}

static int clamp_hud_refresh(int refresh_sec);

static int cmd_watchhud(char **argv, int argc) {
    int refresh_sec = 2;
    int count = 0;
    int index = 0;
    int first_error = 0;
    bool drew_frame = false;

    if (argc >= 2 && sscanf(argv[1], "%d", &refresh_sec) != 1) {
        a90_console_printf("usage: watchhud [sec] [count]\r\n");
        return -EINVAL;
    }
    if (argc >= 3 && sscanf(argv[2], "%d", &count) != 1) {
        a90_console_printf("usage: watchhud [sec] [count]\r\n");
        return -EINVAL;
    }
    refresh_sec = clamp_hud_refresh(refresh_sec);

    a90_console_printf("watchhud: refresh=%ds count=%s, q/Ctrl-C cancels\r\n",
            refresh_sec,
            count > 0 ? argv[2] : "forever");

    while (count <= 0 || index < count) {
        if (a90_kms_begin_frame(0x000000) == 0) {
            struct a90_hud_storage_status storage = current_hud_storage_status();

            a90_hud_draw_status_overlay(a90_kms_framebuffer(),
                                        &storage,
                                        (unsigned int)refresh_sec,
                                        (unsigned int)(index + 1));
            if (a90_kms_present("watchhud", true) == 0) {
                drew_frame = true;
            } else if (first_error == 0) {
                first_error = negative_errno_or(EIO);
            }
        } else if (first_error == 0) {
            first_error = negative_errno_or(ENODEV);
        }
        ++index;
        if (count > 0 && index >= count) {
            break;
        }
        {
            int wait_rc = wait_watch_delay(refresh_sec);

            if (wait_rc < 0) {
                return wait_rc;
            }
        }
    }

    return drew_frame ? 0 : first_error;
}

static int clamp_hud_refresh(int refresh_sec) {
    if (refresh_sec < 1) {
        return 1;
    }
    if (refresh_sec > 60) {
        return 60;
    }
    return refresh_sec;
}

static void reap_hud_child(void) {
    if (a90_service_reap(A90_SERVICE_HUD, NULL) > 0) {
        a90_controller_clear_menu_ipc();
    }
}

static void stop_auto_hud(bool verbose) {
    reap_hud_child();
    if (a90_service_pid(A90_SERVICE_HUD) <= 0) {
        if (verbose) {
            a90_console_printf("autohud: not running\r\n");
        }
        return;
    }

    (void)a90_service_stop(A90_SERVICE_HUD, 2000);
    a90_controller_clear_menu_ipc();
    if (verbose) {
        a90_console_printf("autohud: stopped\r\n");
    }
}

/* forward declarations for auto_hud_loop */
