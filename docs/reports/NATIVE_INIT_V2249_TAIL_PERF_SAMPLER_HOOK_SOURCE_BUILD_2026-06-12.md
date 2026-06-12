# Native Init V2249 Tail Perf Sampler Hook Source Build

## Summary

- Cycle: `V2249`
- Type: source/build-only rollbackable post-FWREADY tail exact-slide sampler test boot.
- Decision: `v2249-tail-perf-sampler-hook-source-build-pass`
- Result: PASS
- Reason: V2248 proved a host-side post-boot V2216 sampler can miss the qcacld/HDD tail; this build packages the V2216 sampler in ramdisk and starts it from the helper before `boot_wlan`.
- Manifest: `workspace/private/builds/native-init/v2249-tail-perf-sampler-hook/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2249_tail_perf_sampler_hook.img`
- Boot SHA256: `df0a39f03f313d9adff3aa519dfddbf9587a995053793fcf3ac4bca3d66b8536`
- Init: `A90 Linux init 0.9.269 (v2249-tail-perf-sampler-hook)`
- Helper marker: `a90_android_execns_probe v428` (binary marker string: `a90_android_execns_probe v428`)
- Helper SHA256: `fa9718619f905dd0d5d5a54b3fb608e9a966c3ce82547a2e97c55af35f0cc70e`
- Tail sampler ramdisk path: `/bin/a90_bpf_perf_regs_codeword_sample_ring`
- Tail sampler SHA256: `3a16efc217eafeacbcc95a5e6005d0abce02e89ab52ed537df1fc2b193ca3dd7`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Kept from V2237: service-object-visible route, post-FWREADY `boot_wlan`, firmware_class feeder, and strict supplicant terminate polling.
- Added for this build only: `A90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_SAMPLER=1` and ramdisk-local `/bin/a90_bpf_perf_regs_codeword_sample_ring`.
- Capture contract: start before `append_post_fw_ready_boot_wlan_trigger`, run for 45 s with 1 ms CPU-clock period, print up to 512 samples, write `/cache/native-init-v2249-tail-perf-regs-codeword.log`, then score with `a90_kernel_v2247_tail_pc_lr_scorer.py` after the live handoff.

## Helper Flags

- `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_SINK=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_MCFG_READBACK=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_LOGDW_ORDER_TIMESTAMPS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_READY_BEFORE_WLFW_VOTE=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_READWRITE_TRANSITION_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_PERMGR_VOTE_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_WLFW_LATE_MSG21_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_QCACLD_POST_BDF_FOCUSED_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_TOMBSTONE_RFS_VENDOR_RFS_PERMS=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_AUTODIR_PARITY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PROCESS_NAMESPACE_AUDIT=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_PARENT_TRAVERSE_PARITY=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_PERSIST_RFS_LEAF_PRECREATE=1`
- `-DA90_RFS_BRIDGE_SERVE_FIRMWARE_MNT_PROBE=1`
- `-DA90_WIFI_TEST_BOOT_TFTP_SHARED_SERVER_INFO_TMPFS=1`
- `-DA90_WIFI_TEST_BOOT_WLFW_INDICATION_LABEL_FIX=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_STATS_NUMERIC_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_STATS_EVENT_SUMMARY=1`
- `-DA90_WIFI_TEST_BOOT_POST_FW_READY_BOOT_WLAN_TRIGGER=1`
- `-DA90_WIFI_TEST_BOOT_ICNSS_REGISTER_PROBE_STACK_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_FIRMWARE_CLASS_FALLBACK_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_QCACLD_FIRMWARE_CLASS_FALLBACK_FEEDER=1`
- `-DA90_WIFI_TEST_BOOT_SERVICE_OBJECT_POST_FW_READY_FWCLASS_BRIDGE=1`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_HELPER_PATH="/bin/a90_bpf_perf_regs_codeword_sample_ring"`

## Safety Scope

This build script performed host-side source/build work only. The eventual live run remains rollbackable and observes kernel PC/LR with read-only BPF perf events. It does not scan/connect Wi-Fi beyond the existing bounded validation route, does not use credentials, does not configure DHCP/routes, does not ping externally, does not execute `probe_write_user`, and does not touch eSoC/PCIe/GDSC/PMIC/GPIO or device partitions.
