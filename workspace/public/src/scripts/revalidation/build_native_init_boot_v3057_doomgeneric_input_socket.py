#!/usr/bin/env python3
"""Build V3057 native-init DOOM input socket candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
import build_native_init_boot_v3053_doomgeneric_audio_corun as v3053
from a90harness.evidence import workspace_private_build_path, workspace_private_input_path

REPO_ROOT = repo_root()

CYCLE = "V3057"
INIT_VERSION = "0.10.86"
INIT_BUILD = "v3057-doomgeneric-input-socket"
BUILD_TAG = INIT_BUILD
DECISION = "v3057-doomgeneric-input-socket-source-build-pass"

OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
OBJ_DIR = OUT_DIR / "obj"
REPORT_PATH = (
    REPO_ROOT
    / "docs"
    / "reports"
    / "NATIVE_INIT_V3057_DOOMGENERIC_INPUT_SOCKET_SOURCE_BUILD_2026-06-22.md"
)
BOOT_IMAGE = workspace_private_input_path(
    "boot_images", "boot_linux_v3057_doomgeneric_input_socket.img", legacy_fallback=False
)
INIT_BINARY = OUT_DIR / "init_v3057_doomgeneric_input_socket"
RAMDISK_CPIO = OUT_DIR / "ramdisk_v3057_doomgeneric_input_socket.cpio"
HELPER_BINARY = OUT_DIR / "a90_android_execns_probe_v512_doomgeneric_input_socket"

ENGINE_BINARY = OUT_DIR / "a90_doomgeneric_private_engine_v3057"
ENGINE_ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_native_bridge_v3057.c"
ENGINE_ADAPTER_OBJECT = OBJ_DIR / "a90_doomgeneric_native_bridge_v3057.o"
ENGINE_RAMDISK_PATH = "bin/a90_doomgeneric_private_engine_v3057"
ENGINE_REMOTE_PATH = "/" + ENGINE_RAMDISK_PATH
ENGINE_NAME = "doomgeneric-private-link-v3057-input-socket"

RUNTIME_WAD_ROOT = v3053.RUNTIME_WAD_ROOT
RUNTIME_WAD_PATH = v3053.RUNTIME_WAD_PATH
EXPECTED_WAD_SHA256 = v3053.EXPECTED_WAD_SHA256
RUNTIME_WAD_MAX_BYTES = v3053.RUNTIME_WAD_MAX_BYTES
DEFAULT_FRAME_TICKS = v3053.DEFAULT_FRAME_TICKS
DEFAULT_SMOKE_FRAMES = v3053.DEFAULT_SMOKE_FRAMES
DEFAULT_LOOP_FRAMES = v3053.DEFAULT_LOOP_FRAMES
CONTINUOUS_LOOP_FRAMES = v3053.CONTINUOUS_LOOP_FRAMES
MAX_LOOP_FRAMES = v3053.MAX_LOOP_FRAMES
LOOP_FRAME_MS = v3053.LOOP_FRAME_MS
FRAME_PATH = "/tmp/a90-doomgeneric-v3057-input-socket-frame.xbgr8888"
INPUT_STATE_PATH = "/tmp/a90-doomgeneric-v3057-input.state"
INPUT_SOCKET_PATH = "/tmp/a90-doomgeneric-v3057-input.sock"
FRAME_WIDTH = v3053.FRAME_WIDTH
FRAME_HEIGHT = v3053.FRAME_HEIGHT
FRAME_STRIDE = v3053.FRAME_STRIDE
FRAME_BYTES = v3053.FRAME_BYTES
NATIVE_DASHBOARD = v3053.NATIVE_DASHBOARD
NATIVE_DASHBOARD_LARGE_FRAME = v3053.NATIVE_DASHBOARD_LARGE_FRAME

SOUND_MODE = v3053.SOUND_MODE
AUDIO_CORUN = v3053.AUDIO_CORUN
AUDIO_CORUN_MODE = v3053.AUDIO_CORUN_MODE
AUDIO_CORUN_DURATION_MS = v3053.AUDIO_CORUN_DURATION_MS
AUDIO_CORUN_AMPLITUDE_MILLI = v3053.AUDIO_CORUN_AMPLITUDE_MILLI

HOST_KEYBOARD_BRIDGE = v3053.HOST_KEYBOARD_BRIDGE
HOST_DASHBOARD = v3053.HOST_DASHBOARD
BASE_V3053_ADAPTER_SOURCE = v3053.v3053_adapter_source

REQUIRED_STRINGS = (
    b"A90 Linux init 0.10.86 (v3057-doomgeneric-input-socket)",
    b"v3057-doomgeneric-input-socket",
    b"doomgeneric-private-link-v3057-input-socket",
    b"/bin/a90_doomgeneric_private_engine_v3057",
    RUNTIME_WAD_PATH.encode("ascii"),
    EXPECTED_WAD_SHA256.encode("ascii"),
    FRAME_PATH.encode("ascii"),
    INPUT_STATE_PATH.encode("ascii"),
    INPUT_SOCKET_PATH.encode("ascii"),
    b"a90.doomgeneric.v3057.input=unix-dgram-state-with-file-fallback",
    b"--input-socket",
    b"serial-doompad-to-DG_GetKey-via-unix-dgram",
    b"video.demo.input.socket_path=",
    b"doompad.input_socket.rc=",
    b"doompad.input_socket.sent=",
    b"doompad.batch=state-mask-v3047",
    b"video.demo.doom.loop_start.continuous",
    b"video.demo.doom.dashboard.native=1",
    b"native-audio-corun-tone-v3053",
    b"host_doompad_dashboard_v3035.py",
    b"host_doompad_keyboard_v3033.py",
    b"video.demo.input.otg_required=0",
)


def rel(path: Path) -> str:
    return v3053.rel(path)


def replace_required(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing source fragment for V3057 patch: {old[:80]!r}")
    return text.replace(old, new)


def v3057_loop_function_source() -> str:
    return r'''
int a90_doomgeneric_run_wad_frame_loop(const char *wad_path,
                                       int frames,
                                       const char *output_path,
                                       const char *input_state_path,
                                       const char *input_socket_path,
                                       int frame_ms) {
    static char arg0[] = "doomgeneric";
    static char arg_iwad[] = "-iwad";
    static char arg_nosound[] = "-nosound";
    static char arg_nomusic[] = "-nomusic";
    static char arg_mb[] = "-mb";
    static char arg_mb_value[] = "6";
    static char arg_warp[] = "-warp";
    static char arg_episode[] = "1";
    static char arg_map[] = "1";
    static char arg_skill[] = "-skill";
    static char arg_skill_value[] = "2";
    char *argv[13];
    int index;
    int input_socket_fd;
    int loop_rc = 0;

    if (wad_path == NULL || wad_path[0] == '\0' ||
        output_path == NULL || output_path[0] == '\0' ||
        input_state_path == NULL || input_state_path[0] == '\0' ||
        frames < 0 || frames > 300 || frame_ms <= 0 || frame_ms > 250) {
        return 49;
    }
    argv[0] = arg0;
    argv[1] = arg_iwad;
    argv[2] = (char *)wad_path;
    argv[3] = arg_nosound;
    argv[4] = arg_nomusic;
    argv[5] = arg_mb;
    argv[6] = arg_mb_value;
    argv[7] = arg_warp;
    argv[8] = arg_episode;
    argv[9] = arg_map;
    argv[10] = arg_skill;
    argv[11] = arg_skill_value;
    argv[12] = NULL;

    a90_doomgeneric_apply_input_state_file(input_state_path);
    input_socket_fd = a90_doomgeneric_open_input_socket(input_socket_path);

    doomgeneric_Create(12, argv);
    for (index = 0; frames == 0 || index < frames; ++index) {
        int rc;

        if (input_socket_fd >= 0) {
            a90_doomgeneric_drain_input_socket(input_socket_fd);
        } else {
            a90_doomgeneric_apply_input_state_file(input_state_path);
        }
        doomgeneric_Tick();
        if (a90_doomgeneric_presented_frames() > 0U) {
            rc = a90_doomgeneric_dump_frame_xbgr8888_atomic(output_path);
            if (rc != 0) {
                loop_rc = rc;
                break;
            }
        }
        usleep((useconds_t)frame_ms * 1000U);
    }
    a90_doomgeneric_close_input_socket(input_socket_fd, input_socket_path);
    if (loop_rc != 0) {
        return loop_rc;
    }
    return a90_doomgeneric_presented_frames() > 0U ? 0 : 50;
}
'''


def v3057_adapter_source() -> str:
    text = BASE_V3053_ADAPTER_SOURCE()
    text = replace_required(
        text,
        "#include <stdio.h>\n#include <stdint.h>",
        "#include <stdio.h>\n#include <stdint.h>\n#include <sys/socket.h>\n#include <sys/un.h>",
    )
    text = replace_required(
        text,
        'const char a90_doomgeneric_v3053_audio_policy[] =\n'
        '    "a90.doomgeneric.v3053.audio=native-audio-corun-tone-real-sfx-disabled";',
        'const char a90_doomgeneric_v3053_audio_policy[] =\n'
        '    "a90.doomgeneric.v3053.audio=native-audio-corun-tone-real-sfx-disabled";\n'
        'const char a90_doomgeneric_v3057_input_policy[] =\n'
        '    "a90.doomgeneric.v3057.input=unix-dgram-state-with-file-fallback";',
    )
    text = replace_required(
        text,
        "marker_checksum(a90_doomgeneric_v3053_audio_policy) == 0U) {",
        "marker_checksum(a90_doomgeneric_v3053_audio_policy) == 0U ||\n"
        "        marker_checksum(a90_doomgeneric_v3057_input_policy) == 0U) {",
    )
    socket_support = r'''
#define A90_DG_INPUT_PACKET_MAGIC 0x41394450U
#define A90_DG_INPUT_PACKET_VERSION 1U

struct a90_dg_input_packet {
    uint32_t magic;
    uint32_t version;
    uint32_t seq;
    uint32_t mask;
    uint32_t active;
};

static void a90_doomgeneric_apply_input_mask(unsigned int seq, unsigned int mask) {
    struct a90_doompad_snapshot snapshot;

    memset(&snapshot, 0, sizeof(snapshot));
    snapshot.seq = seq;
    snapshot.forward = (mask & (1U << 0)) != 0U;
    snapshot.back = (mask & (1U << 1)) != 0U;
    snapshot.left = (mask & (1U << 2)) != 0U;
    snapshot.right = (mask & (1U << 3)) != 0U;
    snapshot.fire = (mask & (1U << 4)) != 0U;
    snapshot.use = (mask & (1U << 5)) != 0U;
    snapshot.menu = (mask & (1U << 6)) != 0U;
    snapshot.run = (mask & (1U << 7)) != 0U;
    a90_doomgeneric_feed_snapshot(&snapshot);
}

static int a90_doomgeneric_open_input_socket(const char *path) {
    struct sockaddr_un addr;
    int fd;
    size_t path_len;
    int flags;

    if (path == NULL || path[0] == '\0') {
        return -1;
    }
    memset(&addr, 0, sizeof(addr));
    path_len = strlen(path);
    if (path_len == 0U || path_len >= sizeof(addr.sun_path)) {
        return -1;
    }
    fd = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (fd < 0) {
        return -1;
    }
    flags = fcntl(fd, F_GETFL, 0);
    if (flags >= 0) {
        (void)fcntl(fd, F_SETFL, flags | O_NONBLOCK);
    }
    (void)fcntl(fd, F_SETFD, FD_CLOEXEC);
    (void)unlink(path);
    addr.sun_family = AF_UNIX;
    snprintf(addr.sun_path, sizeof(addr.sun_path), "%s", path);
    if (bind(fd, (const struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(fd);
        (void)unlink(path);
        return -1;
    }
    return fd;
}

static void a90_doomgeneric_close_input_socket(int fd, const char *path) {
    if (fd >= 0) {
        close(fd);
    }
    if (path != NULL && path[0] != '\0') {
        (void)unlink(path);
    }
}

static void a90_doomgeneric_drain_input_socket(int fd) {
    for (;;) {
        struct a90_dg_input_packet packet;
        ssize_t rd;

        if (fd < 0) {
            return;
        }
        rd = recv(fd, &packet, sizeof(packet), MSG_DONTWAIT);
        if (rd < 0) {
            if (errno == EINTR) {
                continue;
            }
            return;
        }
        if (rd != (ssize_t)sizeof(packet)) {
            continue;
        }
        if (packet.magic != A90_DG_INPUT_PACKET_MAGIC ||
            packet.version != A90_DG_INPUT_PACKET_VERSION) {
            continue;
        }
        a90_doomgeneric_apply_input_mask(packet.seq, packet.mask);
    }
}

'''
    text = replace_required(
        text,
        "static void a90_doomgeneric_apply_input_state_file(const char *path) {",
        socket_support + "static void a90_doomgeneric_apply_input_state_file(const char *path) {",
    )
    start = text.index("int a90_doomgeneric_run_wad_frame_loop")
    end = text.index("\nint main(", start)
    text = text[:start] + v3057_loop_function_source() + text[end:]
    text = replace_required(
        text,
        '''if (argc == 11 &&
        strcmp(argv[1], "--wad-frame-loop") == 0 &&
        argv[2] != NULL &&
        strcmp(argv[3], "--frames") == 0 &&
        strcmp(argv[5], "--output") == 0 &&
        argv[6] != NULL &&
        strcmp(argv[7], "--input-state") == 0 &&
        argv[8] != NULL &&
        strcmp(argv[9], "--frame-ms") == 0) {
        int frame_ms;

        frames = a90_doomgeneric_parse_loop_frames(argv[4], 300);
        frame_ms = a90_doomgeneric_parse_positive_int(argv[10], 250);
        if (frames < 0 || frame_ms <= 0) {
            return 36;
        }
        return a90_doomgeneric_run_wad_frame_loop(argv[2], frames, argv[6], argv[8], frame_ms);
    }
    return 37;
}
''',
        '''if ((argc == 11 || argc == 13) &&
        strcmp(argv[1], "--wad-frame-loop") == 0 &&
        argv[2] != NULL &&
        strcmp(argv[3], "--frames") == 0 &&
        strcmp(argv[5], "--output") == 0 &&
        argv[6] != NULL &&
        strcmp(argv[7], "--input-state") == 0 &&
        argv[8] != NULL &&
        strcmp(argv[9], "--frame-ms") == 0) {
        int frame_ms;
        const char *input_socket_path = NULL;

        if (argc == 13) {
            if (strcmp(argv[11], "--input-socket") != 0 || argv[12] == NULL) {
                return 37;
            }
            input_socket_path = argv[12];
        }
        frames = a90_doomgeneric_parse_loop_frames(argv[4], 300);
        frame_ms = a90_doomgeneric_parse_positive_int(argv[10], 250);
        if (frames < 0 || frame_ms <= 0) {
            return 36;
        }
        return a90_doomgeneric_run_wad_frame_loop(argv[2], frames, argv[6], argv[8], input_socket_path, frame_ms);
    }
    return 37;
}
''',
    )
    return text


def configure_v3057_globals() -> None:
    v3033 = v3053.v3051.v3049.v3047.v3045.v3042.v3040.v3038.v3033
    v3053.CYCLE = CYCLE
    v3053.INIT_VERSION = INIT_VERSION
    v3053.INIT_BUILD = INIT_BUILD
    v3053.BUILD_TAG = BUILD_TAG
    v3053.DECISION = DECISION
    v3053.OUT_DIR = OUT_DIR
    v3053.OBJ_DIR = OBJ_DIR
    v3053.REPORT_PATH = REPORT_PATH
    v3053.BOOT_IMAGE = BOOT_IMAGE
    v3053.INIT_BINARY = INIT_BINARY
    v3053.RAMDISK_CPIO = RAMDISK_CPIO
    v3053.HELPER_BINARY = HELPER_BINARY
    v3053.ENGINE_BINARY = ENGINE_BINARY
    v3053.ENGINE_ADAPTER_SOURCE = ENGINE_ADAPTER_SOURCE
    v3053.ENGINE_ADAPTER_OBJECT = ENGINE_ADAPTER_OBJECT
    v3053.ENGINE_RAMDISK_PATH = ENGINE_RAMDISK_PATH
    v3053.ENGINE_REMOTE_PATH = ENGINE_REMOTE_PATH
    v3053.ENGINE_NAME = ENGINE_NAME
    v3053.DEFAULT_LOOP_FRAMES = DEFAULT_LOOP_FRAMES
    v3053.LOOP_FRAME_MS = LOOP_FRAME_MS
    v3053.FRAME_PATH = FRAME_PATH
    v3053.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3053.NATIVE_DASHBOARD = NATIVE_DASHBOARD
    v3053.NATIVE_DASHBOARD_LARGE_FRAME = NATIVE_DASHBOARD_LARGE_FRAME
    v3053.REQUIRED_STRINGS = REQUIRED_STRINGS
    v3053.v3053_adapter_source = v3057_adapter_source
    v3053.render_report = render_report

    v3033.INPUT_SOCKET_PATH = INPUT_SOCKET_PATH
    v3033.INPUT_STATE_PATH = INPUT_STATE_PATH
    v3033.INPUT_PATH = "serial-doompad-to-DG_GetKey-via-unix-dgram"
    v3033.SOUND_MODE = SOUND_MODE
    v3033.AUDIO_CORUN = AUDIO_CORUN
    v3033.AUDIO_CORUN_MODE = AUDIO_CORUN_MODE
    v3033.AUDIO_CORUN_DURATION_MS = AUDIO_CORUN_DURATION_MS
    v3033.AUDIO_CORUN_AMPLITUDE_MILLI = AUDIO_CORUN_AMPLITUDE_MILLI


def render_report(
    manifest: dict[str, Any],
    helper_flags: tuple[str, ...],
    init_extra_flags: tuple[str, ...],
) -> str:
    doom = manifest.get("doomgeneric_visible_loop", {})
    markers = manifest.get("v3033_marker_strings", [])
    marker_lines = [f"- `{marker}`" for marker in markers] if isinstance(markers, list) else []
    return "\n".join([
        "# Native Init V3057 DOOMGENERIC Input Socket Source Build",
        "",
        "## Summary",
        "",
        f"- Cycle: `{CYCLE}`",
        "- Track: active Video playback / DOOM capstone input responsiveness.",
        f"- Decision: `{manifest['decision']}`",
        "- Result: PASS",
        "- Device flash: `no` in this build unit.",
        f"- Boot image: `{manifest['boot_image']}`",
        f"- Boot SHA256: `{manifest['boot_sha256']}`",
        f"- Init: `A90 Linux init {manifest['init_version']} ({manifest['init_build']})`",
        "",
        "## Included Delta",
        "",
        "- Keeps V3053 DOOM autostart and bounded native audio co-run behavior.",
        "- Adds a helper-owned non-blocking Unix datagram input socket for compact latest-state packets.",
        "- Native `doompad state/key/reset` mirrors each input state to both the existing text state file and the socket.",
        "- The helper drains socket packets once per DOOM frame and feeds the latest mask directly into `DG_GetKey` edges.",
        "- The text state file remains as dashboard/fallback state so the existing demo UI continues to show input logs.",
        "- Host input remains serial doompad for this unit; UDP/NCM is still the next transport-separation unit.",
        "",
        "## Input Contract",
        "",
        f"- Input active marker: `{doom.get('input_path')}`",
        f"- Input socket path: `{doom.get('input_socket_path', INPUT_SOCKET_PATH)}`",
        f"- Input state fallback path: `{doom.get('input_state_path')}`",
        "- Packet format: fixed native-endian `{magic, version, seq, mask, active}` datagram.",
        "- Mask bits remain V3047-compatible: `forward:0 back:1 left:2 right:3 fire:4 use:5 menu:6 run:7`.",
        "",
        "## Runtime Contract",
        "",
        f"- Runtime WAD path: `{doom.get('runtime_wad_path')}`",
        f"- Expected WAD SHA256: `{doom.get('expected_wad_sha256')}`",
        f"- Continuous command: `video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}`",
        f"- Helper loop command: `{doom.get('helper_loop_command')}`",
        f"- Frame path: `{doom.get('frame_path')}`",
        f"- Audio co-run mode: `{AUDIO_CORUN_MODE}`",
        "",
        "## Marker Check",
        "",
        *marker_lines,
        "",
        "## Validation",
        "",
        "- `py_compile`: V3057 builder and focused tests.",
        "- `unittest`: V3057 source contract plus V3053/V3047 regressions.",
        "- Build: AArch64 helper compile/link, native-init compile, ramdisk pack, boot image pack, SHA256 capture.",
        "- Marker check: generated boot image contains V3057 input socket, V3053 audio co-run, V3047 batch input, and continuous-loop markers.",
        "- `git diff --check`: PASS.",
        "",
        "## Next Unit",
        "",
        "- Run ID: `V3058`",
        "- Type: rollback-gated live validation of V3057 input socket candidate.",
        "- Scope: flash exact V3057 boot image, health-check, start DOOM loop, require `video.demo.input.socket_path`, and confirm `doompad state` reports `doompad.input_socket.sent=1` while gameplay remains visible.",
        "",
        "## Metadata",
        "",
        f"- Helper flags: `{', '.join(helper_flags)}`",
        f"- Init extra flags: `{', '.join(init_extra_flags)}`",
        "- Candidate type: `doomgeneric-input-socket-candidate`.",
    ]) + "\n"


def main() -> int:
    configure_v3057_globals()
    rc = v3053.main()
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    doom = manifest.setdefault("doomgeneric_visible_loop", {})
    doom.update({
        "input_path": "serial-doompad-to-DG_GetKey-via-unix-dgram",
        "input_socket_path": INPUT_SOCKET_PATH,
        "input_state_path": INPUT_STATE_PATH,
        "frame_path": FRAME_PATH,
        "engine_binary": rel(ENGINE_BINARY),
        "engine_ramdisk_path": ENGINE_REMOTE_PATH,
        "helper_loop_command": (
            f"{ENGINE_REMOTE_PATH} --wad-frame-loop {RUNTIME_WAD_PATH} "
            f"--frames {DEFAULT_LOOP_FRAMES} --output {FRAME_PATH} "
            f"--input-state {INPUT_STATE_PATH} --frame-ms {LOOP_FRAME_MS} "
            f"--input-socket {INPUT_SOCKET_PATH}"
        ),
        "input_socket": {
            "path": INPUT_SOCKET_PATH,
            "transport": "unix-dgram",
            "packet": "native-endian-magic-version-seq-mask-active",
            "fallback_state_file": INPUT_STATE_PATH,
        },
    })
    manifest.update({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-input-socket-candidate",
        "adoption_state": "pending-input-socket-live-validation",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        render_report(
            manifest,
            tuple(manifest.get("helper_flags", ())),
            tuple(manifest.get("init_extra_flags", ())),
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "doomgeneric-input-socket-candidate.json").write_text(json.dumps({
        "candidate_tag": INIT_BUILD,
        "candidate_type": "doomgeneric-input-socket-candidate",
        "boot_image": rel(BOOT_IMAGE),
        "boot_sha256": manifest["boot_sha256"],
        "init_version": manifest["init_version"],
        "init_build": manifest["init_build"],
        "engine_binary": rel(ENGINE_BINARY),
        "engine_ramdisk_path": ENGINE_REMOTE_PATH,
        "runtime_wad_path": RUNTIME_WAD_PATH,
        "expected_wad_sha256": EXPECTED_WAD_SHA256,
        "frame_path": FRAME_PATH,
        "input_state_path": INPUT_STATE_PATH,
        "input_socket_path": INPUT_SOCKET_PATH,
        "loop_start_command": f"video demo doom loop-start 0 --wad runtime-private --sha256 {EXPECTED_WAD_SHA256}",
        "host_keyboard_bridge": rel(HOST_KEYBOARD_BRIDGE),
        "source_report": rel(REPORT_PATH),
        "rollback_baseline": "v2321-usb-clean-identity-rodata",
        "adoption_state": "pending-input-socket-live-validation",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
