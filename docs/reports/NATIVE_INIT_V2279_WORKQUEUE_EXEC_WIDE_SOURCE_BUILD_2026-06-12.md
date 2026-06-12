# Native Init V2279 Workqueue Execute Wide Source Build

## Summary

- Cycle: `V2279`
- Type: source/build-only rollbackable post-FWREADY wide workqueue execute_start coverage oracle test boot.
- Decision: `v2279-workqueue-exec-wide-source-build-pass`
- Result: PASS
- Reason: V2278 made the V2277 execute-start stack evidence classifiable but only for a partial printed window because most workqueue events overflowed. V2279 raises scalar sample capacity and prints all stored scalar rows while keeping stack-IP output bounded, so the next live run can classify function-pointer coverage without repeating the same V2277 limitation.
- Manifest: `workspace/private/builds/native-init/v2279-workqueue-exec-wide/manifest.json`
- Boot image: `workspace/private/inputs/boot_images/boot_linux_v2279_workqueue_exec_wide.img`
- Boot SHA256: `bfe6d2bb4f2e60e83b4b5ff104e153825bd10aa012afc1f5b4ee75909e57d541`
- Init: `A90 Linux init 0.9.276 (v2279-workqueue-exec-wide)`
- Helper marker: `a90_android_execns_probe v434` (binary marker string: `a90_android_execns_probe v434`)
- Helper SHA256: `9c2719cebb2625c9f56a4389e32906695f67d2aec939c580eafbe05b87e566de`
- Workqueue sampler ramdisk path: `/bin/a90_bpf_workqueue_exec_wide_sample_ring`
- Workqueue sampler SHA256: `02ee8071a02b867bb25e422b1ae835c8f627816ec05b818a5fd1dd2093bc0a91`
- Codeword sampler ramdisk path: `/bin/a90_bpf_perf_regs_codeword_sample_ring`
- Codeword sampler SHA256: `3a16efc217eafeacbcc95a5e6005d0abce02e89ab52ed537df1fc2b193ca3dd7`

## Route

- Helper runtime mode: `wifi-companion-wlan-pd-service-object-visible-trigger-start-only`
- Helper timeout: `75`
- Property root: `/mnt/sdext/a90/private-property-v317/v726/dev/__properties__`
- Kept from V2237: service-object-visible route, post-FWREADY `boot_wlan`, firmware_class feeder, and strict supplicant terminate polling.
- Added for this build only: `A90_WIFI_TEST_BOOT_WORKQUEUE_EXEC_WIDE_SAMPLER=1`, the inherited bounded workqueue sampler supervisor slot, `A90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_SAMPLER=1`, and ramdisk-local wide workqueue/codeword BPF helpers.
- Capture contract: start both samplers before `append_post_fw_ready_boot_wlan_trigger`; observe `workqueue_execute_start` scalar samples for 45000 ms into `/cache/native-init-v2279-workqueue-exec-wide.log`, and sample perf regs/codewords for 45000 ms into `/cache/native-init-v2279-tail-perf-regs-codeword.log`. The live classifier should apply the V2276 bounded UAO-patch-aware same-boot slide rule.
- Next live use: V2280 should flash this image, collect the helper result plus both sampler logs, roll back to the selected baseline, verify selftest `FAIL=0`, and classify the expanded function-pointer window and bounded stack prefix against the same-boot codeword evidence.

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
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_DURATION_MS=45000`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_PERIOD_NS=1000000`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_PRINT_LIMIT=1024`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_WAIT_MS=60000`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_OUTPUT_PATH="/cache/native-init-v2279-tail-perf-regs-codeword.log"`
- `-DA90_WIFI_TEST_BOOT_TAIL_PERF_REGS_CODEWORD_HELPER_PATH="/bin/a90_bpf_perf_regs_codeword_sample_ring"`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_EXEC_WIDE_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_FWCLASS_FUNC_SAMPLER=1`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_FWCLASS_FUNC_DURATION_MS=45000`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_FWCLASS_FUNC_PRINT_LIMIT=8192`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_FWCLASS_FUNC_WAIT_MS=60000`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_FWCLASS_FUNC_OUTPUT_PATH="/cache/native-init-v2279-workqueue-exec-wide.log"`
- `-DA90_WIFI_TEST_BOOT_WORKQUEUE_FWCLASS_FUNC_HELPER_PATH="/bin/a90_bpf_workqueue_exec_wide_sample_ring"`

## Safety Scope

This build script performed host-side source/build work only. The new combined route attaches a read-only BPF tracepoint program to `workqueue_execute_start` and a read-only BPF perf-event program for codeword sampling; both store evidence in BPF maps. It does not write tracefs controls, execute `probe_write_user`, scan/connect Wi-Fi, use credentials, configure DHCP/routes, ping externally, open `/dev/subsys_esoc0`, write PMIC/GPIO/GDSC controls, perform eSoC notify/`BOOT_DONE` spoof, run PCI rescan/platform bind-unbind, or write firmware/boot/device partitions.
