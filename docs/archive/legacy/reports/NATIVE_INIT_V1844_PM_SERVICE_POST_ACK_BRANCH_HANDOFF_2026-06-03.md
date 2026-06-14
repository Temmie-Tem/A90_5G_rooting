# Native Init V1844 PM-Service Post-Ack Branch Handoff

## Summary

- Cycle: `V1844`
- Type: one-run rollbackable PM-service post-ack branch hit-count discriminator
- Decision: `v1844-post-ack-open-branch-reached-rollback-pass`
- Result: PASS
- Reason: PM-service post-ack path reached the devnode open branch; lower-state evidence stayed bounded for rollback inspection
- Evidence: `tmp/wifi/v1844-pm-service-post-ack-branch-handoff`
- Rollback attempt: `from-native`
- Rollback ok: `True`
- Post-rollback version ok: `True`
- Post-rollback selftest fail=0: `True`
- Post-rollback version evidence: `tmp/wifi/v1844-pm-service-post-ack-branch-handoff/post-rollback-version-filtered.stdout.txt`
- Post-rollback selftest evidence: `tmp/wifi/v1844-pm-service-post-ack-branch-handoff/post-rollback-selftest.stdout.txt`

## Gate Label

- post-ack label: `post-ack-open-branch-reached`
- post-ack registered/enabled: `True` / `True`
- post-ack hit total: `20`
- post-ack hit keys: `['pm_service_ack_impl_entry', 'pm_service_ack_impl_match_dispatch', 'pm_service_post_ack_action_entry', 'pm_service_post_ack_client_state_store', 'pm_service_post_ack_vote_scan_done', 'pm_service_post_ack_action_branch', 'pm_service_post_ack_timer_settime_call', 'pm_service_post_ack_power_state_load', 'pm_service_post_ack_power_on_open_call', 'pm_service_post_ack_power_on_open_ret', 'pm_service_post_ack_unlock_return']`
- callback/ack label/total: `callback-ack-present-no-powerup` / `28`
- lower-continuation label: `lower-continuation-static-gap`
- PM focus change fields / mdm-status delta: `[]` / `0`
- PM focus MHI/wlan0 progress: `False`
- service-notifier / QIPCRTR labels: `service-notifier-uninit` / `qipcrtr-bound-recv-poll-timeout-passive`
- lower-state label: `stable-mdm3-offlining`
- safety ok: `True`

## PM-Service Post-Ack Hits

- `pm_service_ack_impl_entry` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740616: pm_service_ack_impl_entry: (0x5565f7a3f4) handle=0xb400007f2a8060e0 state=0x2`
- `pm_service_ack_impl_match_dispatch` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740623: pm_service_ack_impl_match_dispatch: (0x5565f7a474) client=0xb400007fae426180 handle=0xb400007f2a8060e0 state=0x2`
- `pm_service_post_ack_action_entry` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740629: pm_service_post_ack_action_entry: (0x5565f7c788) client=0xb400007fae426180 handle=0xb400007f2a8060e0 state=0x2`
- `pm_service_post_ack_client_state_store` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740636: pm_service_post_ack_client_state_store: (0x5565f7c82c) client=0xb400007f2a8060e0 state=0x2`
- `pm_service_post_ack_vote_scan_done` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740641: pm_service_post_ack_vote_scan_done: (0x5565f7c894)`
- `pm_service_post_ack_action_branch` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740647: pm_service_post_ack_action_branch: (0x5565f7c8a0) action_flags=0x1`
- `pm_service_post_ack_timer_settime_call` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740650: pm_service_post_ack_timer_settime_call: (0x5565f7c8c0)`
- `pm_service_post_ack_power_state_load` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740659: pm_service_post_ack_power_state_load: (0x5565f7c8c8) power_state=0x6e`
- `pm_service_post_ack_qmi_restart_ind_call` registered/enabled/hits: `1` / `1` / `0` first=`none`
- `pm_service_post_ack_power_on_open_call` registered/enabled/hits: `1` / `1` / `1` first=`Binder:596_2-601   [000] ....     6.740667: pm_service_post_ack_power_on_open_call: (0x5565f7cccc) path="/dev/subsys_modem"`
- `pm_service_post_ack_power_on_open_ret` registered/enabled/hits: `1` / `1` / `1` first=`Binder:596_2-601   [000] ....     6.740711: pm_service_post_ack_power_on_open_ret: (0x5565f7ccd4) open_rc=0x7`
- `pm_service_post_ack_unlock_return` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.741633: pm_service_post_ack_unlock_return: (0x5565f7cd1c)`

## Callback/Ack Hits

- `periph_pm_callback_stub_entry` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [003] ....     6.740188: periph_pm_callback_stub_entry: (0x7faeba9a5c)`
- `periph_pm_callback_write_state` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [003] ....     6.740200: periph_pm_callback_write_state: (0x7faeba9adc)`
- `periph_pm_callback_remote_binder` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [003] ....     6.740203: periph_pm_callback_remote_binder: (0x7faeba9ae4)`
- `periph_pm_callback_transact_call` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [003] ....     6.740209: periph_pm_callback_transact_call: (0x7faeba9afc)`
- `periph_pm_callback_transact_return` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [003] ....     6.740245: periph_pm_callback_transact_return: (0x7faeba9b00)`
- `periph_pm_client_ack_entry` registered/enabled/hits: `1` / `1` / `2` first=`Binder:612_2-621   [000] ....     6.740300: periph_pm_client_ack_entry: (0x7fb95886f0)`
- `periph_pm_client_ack_match` registered/enabled/hits: `1` / `1` / `2` first=`Binder:612_2-621   [000] ....     6.740307: periph_pm_client_ack_match: (0x7fb9588754)`
- `periph_pm_client_ack_virtual_call` registered/enabled/hits: `1` / `1` / `2` first=`Binder:612_2-621   [000] ....     6.740521: periph_pm_client_ack_virtual_call: (0x7fb9588780)`
- `periph_pm_server_ontransact_entry` registered/enabled/hits: `1` / `1` / `5` first=`Binder:596_2-601   [001] ....     6.391346: periph_pm_server_ontransact_entry: (0x7faeba95bc)`
- `periph_pm_server_ack_read_state` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740606: periph_pm_server_ack_read_state: (0x7faeba9750)`
- `periph_pm_server_ack_impl_call` registered/enabled/hits: `1` / `1` / `2` first=`Binder:596_2-601   [000] ....     6.740611: periph_pm_server_ack_impl_call: (0x7faeba9760)`
- `periph_pm_server_ack_write_ret` registered/enabled/hits: `1` / `1` / `3` first=`Binder:596_2-601   [003] ....     6.740453: periph_pm_server_ack_write_ret: (0x7faeba9814)`

## Lower State

- mdm3/MHI/WLFW69/wlan0: `OFFLINING` / `False` / `False` / `False`
- service180/service74/wlan_pd raw: `1,1,1` / `0,0,0` / `0,0,0`
- PM-client register/connect/return-path rc: `0` / `0` / `0`

## Property Runtime

- Remote root: `/mnt/sdext/a90/private-property-v317/v1843/dev/__properties__`
- Transport: `serial-uudecode-tar-gz`
- Uploaded files/bytes: `22` / `2759988`
- property_info SHA verified: `True`
- vendor_default_prop SHA verified: `True`

## Safety Scope

- The new V1844 surface only adds read-only `pm-service` uprobe hit counts on the V1843 test boot image.
- No Wi-Fi HAL, scan/connect, credentials, DHCP/routes, external ping, direct `/dev/subsys_esoc0` open, fake ONLINE, PMIC/GPIO/GDSC write, eSoC notify, BOOT_DONE spoof, forced RC1, `boot_wlan`, restart-PD request, PCI rescan, or platform bind/unbind was used.
- Mutation scope is private property runtime staging on `/mnt/sdext`, one test boot flash, and rollback to `stage3/boot_linux_v724.img`.

## Next

- Do not proceed to Wi-Fi HAL/scan/connect unless WLFW service 69 and `wlan0` are present.
- If post-ack open targets `/dev/subsys_modem` while lower state stays static, classify PM-service peripheral selection/state flags around `0x88a0`/`0x88c8` before any new mutation.
