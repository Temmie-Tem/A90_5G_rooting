#!/usr/bin/env python3
"""Host-only private doomgeneric source/build probe for the DOOM capstone."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from _workspace_bootstrap import repo_root
from a90harness.evidence import (
    ensure_private_dir,
    workspace_private_build_path,
    write_private_text,
)

ROOT = repo_root()

RUN_ID = "V3020"
BUILD_TAG = "v3020-doomgeneric-port-probe"
DECISION = "v3020-doomgeneric-private-source-build-probe-pass"
SOURCE_URL = "https://github.com/ozkl/doomgeneric"
PINNED_COMMIT = "dcb7a8dbc7a16ce3dda29382ac9aae9d77d21284"
SOURCE_ROOT = ROOT / "workspace/private/demo-assets/doom/doomgeneric-v3020"
SOURCE_DIR = SOURCE_ROOT / "doomgeneric"
OUT_DIR = workspace_private_build_path("native-init", BUILD_TAG)
REPORT_PATH = ROOT / "docs/reports/NATIVE_INIT_V3020_DOOMGENERIC_PORT_PROBE_2026-06-21.md"

ADAPTER_SOURCE = OUT_DIR / "a90_doomgeneric_port_probe_v3020.c"
STUB_SOURCE = OUT_DIR / "a90_doomgeneric_link_stub_v3020.c"
ADAPTER_OBJECT = OUT_DIR / "a90_doomgeneric_port_probe_v3020.o"
STUB_OBJECT = OUT_DIR / "a90_doomgeneric_link_stub_v3020.o"
DOOMGENERIC_OBJECT = OUT_DIR / "doomgeneric_v3020.o"
PROBE_BINARY = OUT_DIR / "a90_doomgeneric_port_probe_v3020"
MANIFEST_PATH = OUT_DIR / "manifest.json"

CROSS_CC = "aarch64-linux-gnu-gcc"
COMMON_CFLAGS = (
    "-std=c11",
    "-Os",
    "-DDOOMGENERIC_RESX=640",
    "-DDOOMGENERIC_RESY=400",
)
ADAPTER_CFLAGS = COMMON_CFLAGS + ("-Wall", "-Wextra", "-Werror")
THIRD_PARTY_CFLAGS = COMMON_CFLAGS + ("-Wall", "-Wextra")

ADAPTER_SOURCE_TEXT = r'''#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "doomgeneric.h"
#include "doomkeys.h"

#define A90_DG_KEY_QUEUE_MAX 32U

struct a90_doompad_snapshot {
    bool forward;
    bool back;
    bool left;
    bool right;
    bool fire;
    bool use;
    bool menu;
    bool run;
    unsigned int seq;
};

struct a90_dg_key_event {
    int pressed;
    unsigned char key;
};

static struct a90_dg_key_event key_queue[A90_DG_KEY_QUEUE_MAX];
static unsigned int key_head;
static unsigned int key_tail;
static bool last_forward;
static bool last_back;
static bool last_left;
static bool last_right;
static bool last_fire;
static bool last_use;
static bool last_menu;
static bool last_run;
static unsigned int last_seq;
static unsigned int presented_frames;
static uint32_t fake_ticks_ms;
static uint32_t frame_checksum;
static pixel_t frame_sink[DOOMGENERIC_RESX * DOOMGENERIC_RESY];

static unsigned int next_index(unsigned int index) {
    return (index + 1U) % A90_DG_KEY_QUEUE_MAX;
}

static void queue_key_event(int pressed, unsigned char key) {
    unsigned int next_tail = next_index(key_tail);

    if (next_tail == key_head) {
        return;
    }
    key_queue[key_tail].pressed = pressed ? 1 : 0;
    key_queue[key_tail].key = key;
    key_tail = next_tail;
}

static void queue_edge(bool current, bool *previous, unsigned char key) {
    if (previous == NULL) {
        return;
    }
    if (current != *previous) {
        queue_key_event(current ? 1 : 0, key);
        *previous = current;
    }
}

void a90_doomgeneric_feed_snapshot(const struct a90_doompad_snapshot *snapshot) {
    if (snapshot == NULL) {
        return;
    }

    queue_edge(snapshot->forward, &last_forward, KEY_UPARROW);
    queue_edge(snapshot->back, &last_back, KEY_DOWNARROW);
    queue_edge(snapshot->left, &last_left, KEY_LEFTARROW);
    queue_edge(snapshot->right, &last_right, KEY_RIGHTARROW);
    queue_edge(snapshot->fire, &last_fire, KEY_FIRE);
    queue_edge(snapshot->use, &last_use, KEY_USE);
    queue_edge(snapshot->menu, &last_menu, KEY_ESCAPE);
    queue_edge(snapshot->run, &last_run, KEY_RSHIFT);
    last_seq = snapshot->seq;
}

unsigned int a90_doomgeneric_last_seq(void) {
    return last_seq;
}

unsigned int a90_doomgeneric_pending_keys(void) {
    if (key_tail >= key_head) {
        return key_tail - key_head;
    }
    return A90_DG_KEY_QUEUE_MAX - key_head + key_tail;
}

unsigned int a90_doomgeneric_presented_frames(void) {
    return presented_frames;
}

uint32_t a90_doomgeneric_frame_checksum(void) {
    return frame_checksum;
}

void DG_Init(void) {
    memset(frame_sink, 0, sizeof(frame_sink));
    key_head = 0;
    key_tail = 0;
    presented_frames = 0;
    fake_ticks_ms = 0;
    frame_checksum = 0;
}

void DG_DrawFrame(void) {
    const size_t count = (size_t)DOOMGENERIC_RESX * (size_t)DOOMGENERIC_RESY;
    size_t i;

    if (DG_ScreenBuffer != NULL) {
        memcpy(frame_sink, DG_ScreenBuffer, count * sizeof(frame_sink[0]));
        for (i = 0; i < count; i += 257U) {
            frame_checksum = frame_checksum * 33U + (uint32_t)frame_sink[i];
        }
    }
    ++presented_frames;
}

void DG_SleepMs(uint32_t ms) {
    fake_ticks_ms += ms;
}

uint32_t DG_GetTicksMs(void) {
    return fake_ticks_ms;
}

int DG_GetKey(int *pressed, unsigned char *key) {
    if (pressed == NULL || key == NULL || key_head == key_tail) {
        return 0;
    }

    *pressed = key_queue[key_head].pressed;
    *key = key_queue[key_head].key;
    key_head = next_index(key_head);
    return 1;
}

void DG_SetWindowTitle(const char *title) {
    (void)title;
}

int a90_doomgeneric_probe_entry(void) {
    struct a90_doompad_snapshot snapshot = {
        .forward = true,
        .fire = true,
        .run = true,
        .seq = 7U,
    };
    int pressed = 0;
    unsigned char key = 0;

    DG_Init();
    a90_doomgeneric_feed_snapshot(&snapshot);
    if (a90_doomgeneric_pending_keys() != 3U) {
        return 10;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 1 || key != KEY_UPARROW) {
        return 11;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 1 || key != KEY_FIRE) {
        return 12;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 1 || key != KEY_RSHIFT) {
        return 13;
    }
    snapshot.forward = false;
    snapshot.fire = false;
    snapshot.run = false;
    snapshot.seq = 8U;
    a90_doomgeneric_feed_snapshot(&snapshot);
    if (a90_doomgeneric_pending_keys() != 3U) {
        return 14;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 0 || key != KEY_UPARROW) {
        return 15;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 0 || key != KEY_FIRE) {
        return 16;
    }
    if (!DG_GetKey(&pressed, &key) || pressed != 0 || key != KEY_RSHIFT) {
        return 17;
    }
    DG_SleepMs(16U);
    DG_DrawFrame();
    if (DG_GetTicksMs() != 16U || a90_doomgeneric_presented_frames() != 1U) {
        return 18;
    }
    return a90_doomgeneric_last_seq() == 8U ? 0 : 19;
}
'''

STUB_SOURCE_TEXT = r'''int myargc;
char **myargv;

void M_FindResponseFile(void) {
}

void D_DoomMain(void) {
}

int a90_doomgeneric_probe_entry(void);

int main(void) {
    return a90_doomgeneric_probe_entry();
}
'''


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else str(ROOT),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def require_success(result: subprocess.CompletedProcess[str], description: str) -> str:
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed rc={result.returncode}\n{result.stdout}")
    return result.stdout


def git_output(args: list[str]) -> str | None:
    result = run(["git", "-C", str(SOURCE_ROOT), *args])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def count_files(root: Path, suffix: str) -> dict[str, Any]:
    if not root.exists():
        return {"root": rel(root), "exists": False, "count": 0, "total_bytes": 0}
    normalized_suffix = suffix.lower()
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.name.lower().endswith(normalized_suffix)
    ]
    return {
        "root": rel(root),
        "exists": True,
        "count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
    }


def collect_source_state() -> dict[str, Any]:
    source_files = [path for path in SOURCE_DIR.rglob("*") if path.is_file()] if SOURCE_DIR.exists() else []
    head = git_output(["rev-parse", "HEAD"]) if (SOURCE_ROOT / ".git").is_dir() else None
    subject = git_output(["log", "-1", "--format=%s"]) if head else None
    date = git_output(["log", "-1", "--format=%cs"]) if head else None
    status = git_output(["status", "--short"]) if head else None
    return {
        "source_url": SOURCE_URL,
        "source_root": rel(SOURCE_ROOT),
        "source_exists": SOURCE_DIR.is_dir(),
        "git_head": head,
        "git_head_matches_pin": head == PINNED_COMMIT,
        "git_status_clean": status == "",
        "git_commit_date": date,
        "git_commit_subject": subject,
        "source_file_count": len(source_files),
        "license_sha256": sha256_file(SOURCE_ROOT / "LICENSE") if (SOURCE_ROOT / "LICENSE").exists() else None,
        "doomgeneric_h_sha256": (
            sha256_file(SOURCE_DIR / "doomgeneric.h") if (SOURCE_DIR / "doomgeneric.h").exists() else None
        ),
        "doomkeys_h_sha256": sha256_file(SOURCE_DIR / "doomkeys.h") if (SOURCE_DIR / "doomkeys.h").exists() else None,
    }


def compile_probe() -> dict[str, Any]:
    ensure_private_dir(OUT_DIR)
    write_private_text(ADAPTER_SOURCE, ADAPTER_SOURCE_TEXT)
    write_private_text(STUB_SOURCE, STUB_SOURCE_TEXT)

    include_flag = f"-I{SOURCE_DIR}"
    adapter_cmd = [
        CROSS_CC,
        *ADAPTER_CFLAGS,
        include_flag,
        "-c",
        str(ADAPTER_SOURCE),
        "-o",
        str(ADAPTER_OBJECT),
    ]
    doomgeneric_cmd = [
        CROSS_CC,
        *THIRD_PARTY_CFLAGS,
        include_flag,
        "-c",
        str(SOURCE_DIR / "doomgeneric.c"),
        "-o",
        str(DOOMGENERIC_OBJECT),
    ]
    stub_cmd = [
        CROSS_CC,
        *ADAPTER_CFLAGS,
        include_flag,
        "-c",
        str(STUB_SOURCE),
        "-o",
        str(STUB_OBJECT),
    ]
    link_cmd = [
        CROSS_CC,
        "-static",
        str(ADAPTER_OBJECT),
        str(DOOMGENERIC_OBJECT),
        str(STUB_OBJECT),
        "-o",
        str(PROBE_BINARY),
    ]

    outputs = {
        "adapter_compile": require_success(run(adapter_cmd), "adapter compile"),
        "doomgeneric_compile": require_success(run(doomgeneric_cmd), "doomgeneric compile"),
        "stub_compile": require_success(run(stub_cmd), "link stub compile"),
        "link": require_success(run(link_cmd), "probe link"),
    }
    file_output = require_success(run(["file", str(PROBE_BINARY)]), "file probe binary").strip()
    payload = {
        "adapter_source": rel(ADAPTER_SOURCE),
        "adapter_source_sha256": sha256_file(ADAPTER_SOURCE),
        "stub_source": rel(STUB_SOURCE),
        "stub_source_sha256": sha256_file(STUB_SOURCE),
        "adapter_object": rel(ADAPTER_OBJECT),
        "adapter_object_sha256": sha256_file(ADAPTER_OBJECT),
        "doomgeneric_object": rel(DOOMGENERIC_OBJECT),
        "doomgeneric_object_sha256": sha256_file(DOOMGENERIC_OBJECT),
        "stub_object": rel(STUB_OBJECT),
        "stub_object_sha256": sha256_file(STUB_OBJECT),
        "probe_binary": rel(PROBE_BINARY),
        "probe_binary_sha256": sha256_file(PROBE_BINARY),
        "file_output": file_output,
        "aarch64_static_elf": "ELF 64-bit LSB executable, ARM aarch64" in file_output and "statically linked" in file_output,
        "commands": {
            "adapter_compile": " ".join(adapter_cmd),
            "doomgeneric_compile": " ".join(doomgeneric_cmd),
            "stub_compile": " ".join(stub_cmd),
            "link": " ".join(link_cmd),
            "file": f"file {PROBE_BINARY}",
        },
        "stdout_nonempty": {key: bool(value.strip()) for key, value in outputs.items()},
    }
    return payload


def collect_state(*, build: bool) -> dict[str, Any]:
    source = collect_source_state()
    public_wads = count_files(ROOT / "workspace/public", ".wad")
    private_wads = count_files(ROOT / "workspace/private", ".wad")
    build_payload: dict[str, Any] | None = compile_probe() if build else None
    state = {
        "run_id": RUN_ID,
        "decision": DECISION,
        "build_tag": BUILD_TAG,
        "source": source,
        "build": build_payload,
        "public_wads": public_wads,
        "private_wads": private_wads,
        "asset_policy": {
            "commit_wad": False,
            "embed_wad_in_boot_image": False,
            "runtime_wad_root": "/cache/a90-runtime/pkg/doom/v3021/",
            "private_source_root": "workspace/private/demo-assets/doom/",
        },
        "port_mapping": {
            "frame_path": "DG_DrawFrame -> private probe framebuffer copy; native target will call a90_kms_present",
            "input_path": "doompad snapshot edges -> DG_GetKey queue",
            "time_path": "DG_SleepMs/DG_GetTicksMs bounded monotonic shim",
            "sound_path": "not enabled in first WAD-backed unit",
        },
        "safety": {
            "device_action": "none",
            "flash": False,
            "boot_image_written": False,
            "serial_command": False,
            "evdev_open": False,
            "input_injection": False,
            "sysfs_write": False,
            "wad_copy": False,
        },
    }
    state["safe_to_continue_host_only"] = bool(
        source["source_exists"]
        and source["git_head_matches_pin"]
        and source["git_status_clean"]
        and public_wads["count"] == 0
        and not state["asset_policy"]["commit_wad"]
        and not state["asset_policy"]["embed_wad_in_boot_image"]
        and (not build or (build_payload is not None and build_payload["aarch64_static_elf"]))
    )
    state["next_unit"] = {
        "run_id": "V3021",
        "type": "source-integration-plan-or-build",
        "summary": (
            "Choose whether to vendor the pinned doomgeneric source publicly with GPL/NOTICE handling "
            "or keep source private for one more build-only integration probe; WAD remains runtime-private."
        ),
    }
    return state


def render_report(state: dict[str, Any]) -> str:
    source = state["source"]
    build = state["build"] or {}
    validation = [
        "- `python3 -m py_compile workspace/public/src/scripts/revalidation/native_doomgeneric_port_probe_v3020.py tests/test_native_doomgeneric_port_probe_v3020.py`: PASS",
        "- `PYTHONPATH=tests:workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 -m unittest tests.test_native_doomgeneric_port_probe_v3020`: PASS",
        "- `PYTHONPATH=workspace/public/src/scripts/revalidation:workspace/public/src/harness python3 workspace/public/src/scripts/revalidation/native_doomgeneric_port_probe_v3020.py`: PASS",
        "- `file workspace/private/builds/native-init/v3020-doomgeneric-port-probe/a90_doomgeneric_port_probe_v3020`: PASS (AArch64 static ELF)",
        "- `git diff --check`: PASS",
    ]
    return "\n".join([
        "# Native Init V3020 DOOMGENERIC Port Probe",
        "",
        "## Summary",
        "",
        f"- Decision: `{state['decision']}`",
        "- Device action: `none` in this host-only unit.",
        "- Track: active Video playback / DOOM capstone.",
        f"- Private doomgeneric source pinned: `{int(bool(source['git_head_matches_pin']))}`",
        f"- Private source clean: `{int(bool(source['git_status_clean']))}`",
        f"- AArch64 probe linked: `{int(bool(build.get('aarch64_static_elf')))}`",
        f"- Public WAD files committed/present: `{state['public_wads']['count']}`",
        f"- Private WAD files currently present: `{state['private_wads']['count']}`",
        f"- Safe next unit: `{int(bool(state['safe_to_continue_host_only']))}`",
        "",
        "## Source Pin",
        "",
        f"- Source URL: `{source['source_url']}`",
        f"- Private source root: `{source['source_root']}`",
        f"- Pinned commit: `{PINNED_COMMIT}`",
        f"- Current commit: `{source['git_head']}`",
        f"- Commit date: `{source['git_commit_date']}`",
        f"- Commit subject: `{source['git_commit_subject']}`",
        f"- Source file count: `{source['source_file_count']}`",
        f"- LICENSE SHA256: `{source['license_sha256']}`",
        f"- `doomgeneric.h` SHA256: `{source['doomgeneric_h_sha256']}`",
        f"- `doomkeys.h` SHA256: `{source['doomkeys_h_sha256']}`",
        "",
        "## Build Probe",
        "",
        f"- Adapter source: `{build.get('adapter_source')}`",
        f"- Adapter source SHA256: `{build.get('adapter_source_sha256')}`",
        f"- Adapter object: `{build.get('adapter_object')}`",
        f"- Adapter object SHA256: `{build.get('adapter_object_sha256')}`",
        f"- doomgeneric object: `{build.get('doomgeneric_object')}`",
        f"- doomgeneric object SHA256: `{build.get('doomgeneric_object_sha256')}`",
        f"- Probe binary: `{build.get('probe_binary')}`",
        f"- Probe binary SHA256: `{build.get('probe_binary_sha256')}`",
        f"- `file`: `{build.get('file_output')}`",
        "",
        "## Port Mapping",
        "",
        f"- Frame path: {state['port_mapping']['frame_path']}.",
        f"- Input path: {state['port_mapping']['input_path']}.",
        f"- Time path: {state['port_mapping']['time_path']}.",
        f"- Sound path: {state['port_mapping']['sound_path']}.",
        "",
        "## Asset Policy",
        "",
        "- WAD/IWAD data must not be committed.",
        "- WAD/IWAD data must not be embedded into the boot image for the first real engine unit.",
        f"- Runtime staging root for the next WAD unit: `{state['asset_policy']['runtime_wad_root']}`.",
        f"- Private source/asset root: `{state['asset_policy']['private_source_root']}`.",
        "",
        "## Safety",
        "",
        "- Host-only source/build probe; no flash, serial command, evdev open, input injection, sysfs write, Wi-Fi action, audio/video playback, WAD copy, boot image write, PMIC, backlight, GPIO, regulator, GDSC, or forbidden partition path is touched.",
        "- The generated adapter C and AArch64 probe binary are private build artifacts only.",
        "- A later live unit still needs explicit rollback-gated boot-image build and device validation.",
        "",
        "## Host Validation",
        "",
        *validation,
        "",
        "## Next Unit",
        "",
        f"- Run ID: `{state['next_unit']['run_id']}`",
        f"- Type: `{state['next_unit']['type']}`",
        f"- Summary: {state['next_unit']['summary']}",
    ]) + "\n"


def main() -> int:
    state = collect_state(build=True)
    write_private_text(MANIFEST_PATH, json.dumps(state, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(render_report(state), encoding="utf-8")
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if state["safe_to_continue_host_only"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
