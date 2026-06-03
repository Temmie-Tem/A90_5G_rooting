# WLAN-PD Producer-Trigger Deep Analysis (host-only, 2026-06-04)

> Out-of-band synthesis report. NOT a `vNNN` cycle. Consolidates a host-only
> deep dive over existing Android-good captures, the native A1 integration
> capture (V1937), the exported Samsung RIL (`libsec-ril.so`, V1945), the staged
> ICNSS source, and external (web) architecture references. The goal is to fix
> what is **confirmed**, what is **refuted**, what **leads remain**, and the
> **direction**, so the research loop can re-anchor without re-deriving.

## 0. One-line conclusion

Native already reproduces the **entire pm-service + cnss-daemon userspace
producer chain** (modem power-on via `pm-service` `/dev/subsys_modem` fd, plus
the cnss WLFW worker lookup), yet the internal modem **never self-starts the
WLAN protection domain** (`msm/modem/wlan_pd`, instance 180). The blocker is
therefore **inside the modem / its boot environment**, not a missing AP
userspace action. **Lead B (modem EFS/NV parity) was refuted on
2026-06-04**: native's real `rmt_storage` serves the modem's full ~2 MB EFS
(v1713/v1691) and `wlan_pd` still never starts. The **sole surviving lead is
(A) the RIL DMS/NAS modem-init QMI handshake** — the only Android userspace
actor native does not run — which needs a new RIL-inclusive capture, not
re-analysis of current data.

---

## 1. Target architecture (confirmed)

- `wlan0` rides the **ICNSS** path, not `cnss2`/PCIe. The WLAN firmware
  (`wlanmdsp.mbn`) runs as a **user protection domain on the internal modem Q6
  DSP** (`msm/modem/wlan_pd`, instance **180**), sideloaded to the modem via
  `tqftpserv`. The external SDX50M (esoc0/mdm3/pcie1) is a **separate** PCIe 5G
  modem and is **not** on the `wlan0` path.
  - Source: project redirect doc
    `docs/reports/WLAN_PD_REDIRECT_AND_FIRMWARE_SERVE_GATE_2026-06-02.md`;
    service-locator returns `msm/modem/wlan_pd` instance 180 on **both** native
    and Android (V829, V1908, V1909).
- **WLAN-PD start mechanism** (web-confirmed): the WLAN firmware runs in the
  modem Q6 DSP as a user PD; as part of **ROOT-PD boot-up the modem queries the
  `pd_mapper` daemon on the AP to determine how many user PDs to load**.
  - Source: LKDDB `CONFIG_QCOM_PD_MAPPER`
    (https://cateee.net/lkddb/web-lkddb/QCOM_PD_MAPPER.html); LWN in-kernel
    pd-mapper (https://lwn.net/Articles/973399/).
- Mainline/pmOS brings up the same WCN3990 WLAN **without Android RIL**, using
  only `qrtr` + `pd-mapper` + `tqftpserv` + `rmtfs` plus the modem remoteproc;
  `wlanmdsp.mbn` must sit alongside `modem.mbn`.
  - Source: ath10k/sm8150 threads
    (https://mail-archive.com/ath10k@lists.infradead.org/msg16353.html). NOTE:
    mainline uses a different driver path (`ath10k_snoc` + kernel remoteproc),
    so "no RIL on mainline" does not prove "no RIL needed on the stock kernel".

## 2. The Android-good producer chain (confirmed, with timestamps)

Reconstructed from `tmp/wifi/v1934-android-libqmi-service69-positive-control-live-20260603-170139/`
(logcat, wall-clock `02:03:xx`) and
`tmp/wifi/v1753-android-good-wlan-pd-firmware-request/` (dmesg, uptime).

| time (logcat) | time (dmesg) | event |
|---|---|---|
| 49.314 | — | `PerMgrSrv` (pm-service) starts; modem/SDX50M/slpi/spss = off-line |
| 50.336–50.337 | — | `PerMgrSrv: PM-PROXY-THREAD voting for modem` → `modem ... is on-line` (voters 1) |
| 50.796 | ~8.689 | `cnss-daemon wlfw_start: Starting` |
| 50.825 | ~8.754 | `cnss-daemon wlfw_service_request: Start the pthread` (WLFW-69 wait worker) |
| 50.850 | — | `QCRIL voting for modem` (voters 3) + `QCRIL voting for SDX50M` |
| 51.389 | — | **modem self-requests `wlanmdsp.mbn` via tftp** from `/vendor/rfs/msm/mpss/readonly/vendor/firmware/wlanmdsp.mbn` (4 251 884 bytes) |
| — | 9.672951 | `service-notifier: root_service_service_ind_cb: ... msm/modem/wlan_pd, state: 0x1fffffff` → **WLAN-PD UP** |
| — | 9.673242 | `send_ind_ack: ... wlan_pd, instance 180` |
| 51.675 | 9.675476 | `cnss-daemon: WLFW service connected` / `icnss_qmi: QMI Server Connected` (WLFW service 69) |
| 51.787 | — | `wlfw_send_cap_req: chip_id: 0x30224 ... fw_version 0x3204038e (2022-08-08)` |
| 51.799 / 51.810 | 9.82 / 9.84 | `wlfw_send_bdf_download_req: regdb.bin / bdwlan.bin` (result 0) |
| ~57.437 | — | `wlan0` appears (`EthernetTracker: interfaceLinkStateChanged iface: wlan0`) |

**Key facts from the chain:**
- **F1.** Between the AP votes (50.3–50.85) and the modem's own `wlanmdsp`
  request (51.389) there is **no explicit AP→modem "start WLAN PD" command** in
  the (admittedly tag-filtered) logcat. The modem **self-starts** the WLAN PD
  ~0.5 s after being voted online while the cnss WLFW worker is waiting.
- **F2.** The first actor to bring the modem "on-line" is **`pm-service`'s own
  `PM-PROXY-THREAD`** (50.336); cnss and QCRIL are added voters afterward.
- **F3.** The downstream (post-WLAN-PD) chain is **fully healthy**: WLFW
  connect → `cap_req` → BDF (`regdb.bin`, `bdwlan.bin`, result 0) → `wlan0`.
  `cnss-daemon: Send DMS get mac address failed ... error 16` is **non-fatal**
  (MAC comes from `macloader`).
- **F4.** At boot the modem reads its **EFS** via `rmtfs`: registers
  `modemst1 (0x4a)`, `modemst2 (0x4b)`, `fsc (0xff)`, `fsg (0x58)` from
  `/boot/modem_fs*`, and reads ~2 MB from `modemst2`
  (`Bytes read = 2096128`, logcat 49.372).

## 3. The native A1 capture (confirmed — refutes prior hypotheses)

From `tmp/wifi/v1937-icnss-ipc-service69-integration/` (decision
`v1937-native-icnss-ipc-pd-registration-no-wlfw-arrive`).

Native companion order:
`servicemanager,hwservicemanager,vndservicemanager,qrtr_ns,pd_mapper,rmt_storage,tftp_server,pm_proxy_helper,per_mgr,vndservice_query,subsys_modem_holder,cnss_diag,cnss_daemon`.

**Native dmesg** (`v1936-handoff/test-v1393-dmesg.stdout.txt`):
- `4.467428 root_service_service_ind_cb: msm/adsp/audio_pd, state: 0x1fffffff`
  → **native ADSP audio guest-PD reaches UP**.
- `4.842989 [pm_proxy_helper:600] subsys-pil-tz 4080000.qcom,mss: modem:
  loading` → native modem is brought up by **`pm_proxy_helper` (raw holder)**.
- `5.427343 modem: Brought out of reset`; `5.484788 service_notifier_new_server
  ... 180 service` → **native modem registers the WLAN-PD SERVREG server
  (180)**.
- **No** `root_service_service_ind_cb ... msm/modem/wlan_pd` ever (confirmed by
  V1940: `wlanpd_ind = 1 (Android) vs 0 (native)`).

**Native pm-service uprobes** (`v1936-handoff/test-v1393-helper-result.stdout.txt`,
`wlan_pd_cnss_nonlog_control_flow.pm_server_uprobe.*`):
- `6.680276 pm_service_post_ack_power_state_loaded: power_state=0x2` → `0x3`
  (6.681579).
- `6.680293 pm_service_post_ack_open_path_loaded: path="/dev/subsys_modem"`.
- `6.680343 pm_service_post_ack_open_fd_store: open_rc=0x8` and
  `pm_service_post_ack_open_success_counter` → **native pm-service successfully
  opens `/dev/subsys_modem` (fd 8) on the power-on ACK path.**
- `per_mgr_process_count=1`, `per_mgr_thread_count=6`,
  `vendor_qcom_peripheral_manager_seen=1` → **pm-service is alive and
  registered as the PeripheralManager.**

**Native cnss WLFW worker uprobes** (`...libqmi_uprobe.*`):
- `6.675660 wlfw_start`; `6.681462 wlfw_service_request`;
  `6.681275 wlfw_worker_pthread_create_success`.
- `6.681516 libqmi_client_init_instance_entry: svc=WLFW instance=0xffff
  timeout=0x0` → enters the blocking WLFW init.
- `6.682540 libqmi_get_service_list_lookup_ret: found=0x0` (repeated) → WLFW
  service 69 not present; the lookup is a **local QRTR registry check**, it does
  not command the modem to start anything.
- Result: `wait_outstanding=True wait_return=False new_server69=False`,
  `wlfw69=False wlan_pd=False wlanmdsp=False wlan0=False`.

**N1 (decisive).** Native reproduces the full pm-service + cnss userspace:
PeripheralManager power-on of the modem (`/dev/subsys_modem` fd 8, power_state
`0x2→0x3`) **and** the cnss WLFW worker lookup/wait — **identical to Android** —
and the modem still never starts `wlan_pd`. The missing piece is **not** an AP
userspace action on the pm-service/cnss side.

## 4. Refuted hypotheses (with what refuted them)

| # | hypothesis | refuted by |
|---|---|---|
| R1 | `modemuw.jsn` is the trigger | native already has it; Android shows 0 `.jsn` reads before `wlanmdsp` (V1919) |
| R2 | SERVREG `msg22` peripheral-restart triggers wlan_pd | pm-service `msg22` uprobe = **0 hits** on normal Android boot (V1899) |
| R3 | pd-mapper / service-locator returns empty domain list | both native & Android return `wlan_pd` inst 180 (V829, V1908, V1909) |
| R4 | the untested "A1 combination" (service74 + clean-DSP + cnss worker) | achieved at V1922; wlan_pd still never UP through V1935 |
| R5 | RIL's PM **vote** is a special trigger | `libsec-ril` `ModemBoot::PeripheralManagerVote/Init` call **only** `pm_client_register/connect/event_acknowledge/disconnect/unregister` — the **same** API native's cnss already uses successfully (objdump, this session) |
| R6 | `service_notif_pd_restart` is the initial WLAN-PD start | it lives in `icnss_trigger_recovery()` (icnss.c ~L2603): **recovery only**, requires `ICNSS_PDR_REGISTERED` + an existing service_notifier handle (i.e. WLFW already up). Safety exclusion is correct. |
| R7 | DMS operating-mode `ONLINE` is the gate | airplane-mode counterexample: phone WiFi works while cellular operating-mode is OFFLINE/LOW_POWER, so WLAN-PD up is not gated on cellular ONLINE |
| R8 | native `pm-service` early-exit is the cause | V1937: pm-service is **alive** (6 threads), registered as PeripheralManager, and **opens `/dev/subsys_modem` fd 8** on the power-on ACK path (see N1) |

## 5. Open leads (finite; both require new evidence)

- **Lead A — RIL DMS/NAS modem-init handshake.** RIL is the one userspace actor
  native does not run. `libsec-ril.so` (Samsung RIL impl, `build.prop:
  vendor.sec.rild.libpath=/vendor/lib64/libsec-ril.so`) links the full modem
  QMI surface and drives modem operating state via `QMI_DMS_SET/GET_OPERATING_MODE`,
  `ModemProxy::SetRadioPowerInternal`, `PowerManager::DoRadioPower`. Hypothesis:
  the modem self-starts guest PDs (incl. WLAN) only after RIL completes its
  deep modem-init QMI handshake (DMS device-caps / operating-mode / NAS),
  which puts the modem in a full internal "initialized" state.
  - **Status: not testable from current captures.** The Android logcat is
    **tag-filtered and excludes RIL/secril/DMS logs**; the only RIL evidence is
    `PerMgrSrv` naming `QCRIL` as a vote client. Needs a **new RIL-inclusive
    Android capture** of modem-bound QMI in the `wlan_pd`-UP window.
  - Bounded: the DMS init handshake is a small, enumerable QMI set.

- **Lead B — modem EFS/NV parity. → REFUTED (2026-06-04 host check).** Native
  runs the **real `/vendor/bin/rmt_storage`** (`vendor_rmt_storage:s0`), and in
  `tmp/wifi/v1713-cnss-wlfw-prologue-adjacent-uprobe-handoff/` and
  `tmp/wifi/v1691-wlan-pd-cnss-property-lookup-handoff/` native dmesg shows the
  modem **connecting and serving its full EFS**:
  `rmt_storage_open_cb: Processing: Open Request for /boot/modem_fs1` (also
  `modem_fs2`, `modem_fsg`) at ~3.9 s, and
  `rmt_storage_rw_iovec_cb ... size=2097152 ... Done Write (bytes = 2097152)` —
  the modem reads/writes its ~2 MB EFS via native rmtfs. **`wlan_pd` still never
  reaches state-up** in those runs. So native serves the modem EFS correctly and
  EFS is **not** the blocker. (The V1937 dmesg only showed "Modem subsystem
  found" because that capture window was truncated before the later EFS I/O; it
  was not a failure — `rmt_storage` was alive and killed by SIGTERM at cleanup.)
  - Minor open observation: in native runs the modem issues a **full 2 MB write**
    to `modem_fs1` (~34 s, well after the wlan_pd window) whereas Android shows a
    2 MB **read** from `modem_fs2` at boot. Timing rules it out as the wlan_pd
    trigger cause, but the read-vs-write asymmetry is noted.

- **Lead C — missing modem-management daemons (low prob).** Native runs none of
  `qmuxd`, `netmgrd`, `secril_config_svc`, `irsc_util`, `time_daemon`
  (`QC-time-services` connects to the modem time QMI at logcat 49.497). Corpus
  never investigated `qmuxd`/`netmgrd`/`time_daemon`. Unlikely to gate WLAN, but
  part of the missing stack.

## 5b. Low-probability host digs (2026-06-04, exhausted)

Pursued every remaining host-only angle to shorten loop time; all reinforce the
modem-internal conclusion rather than open a new userspace trigger:

- **Syscall straces exist** (`tmp/wifi/v1753-.../cnss_daemon.strace.txt`,
  `rmt_storage.strace.txt`, `tftp_server.strace.txt`; also V1897). They are
  **short samples** (~18 lines), but the cnss-daemon strace shows only QRTR
  **control-socket service discovery** (`recvfrom`/`sendto` of
  NEW_SERVER/DEL_SERVER/NEW_LOOKUP on `AF_QIPCRTR ... QRTR_PORT_CTRL`) — i.e. the
  WLFW-service lookup. **No "start wlan_pd" command to the modem at the syscall
  level.** Reinforces: the modem self-starts the PD; no AP actor commands it.
- **Android actor census** (V1934 logcat tags): modem-facing actors are
  `tftp_server`, `vendor.rmt_storage`, `PerMgrSrv` (pm-service), `cnss-daemon`,
  `QC-time-services`, plus SDX50M-only `libmdmimgload`/`mdm_helper` and AP-side
  `macloader`/`CLD80211`. Native runs the core (qrtr-ns, pd-mapper, rmt_storage,
  tftp_server, pm-service, cnss). **Missing modem-facing actors on native:**
  **RIL** (dominant), `time_daemon` (`QC-time-services` connects to the modem
  time QMI at logcat 49.497), `qmuxd`, `netmgrd`. (`macloader` is AP-side — it
  writes the WLAN MAC into ICNSS, not the modem — so it cannot gate wlan_pd
  start.)
- **QRTR service-registry comparison: narrow visibility limit, NOT blind.**
  Native only lacks the kernel *dump* conveniences
  `/sys/kernel/debug/qrtr/{nodes,services}`, `/proc/net/qrtr`,
  `/sys/kernel/debug/msm_ipc_router/dump` (errno 2; V819/V820). The QRTR service
  set is **still enumerable** three ways: (1) active `AF_QIPCRTR` `NEW_LOOKUP`
  socket queries — the helper's `--qrtr-readback-matrix`, already used in
  V821–V825 (which found `servloc 64/257`, `servnotif 66/46081` published and
  `wlfw 69` empty); (2) dmesg SERVREG/sysmon `new_server` lines (74/180 + ssctl);
  (3) daemon strace. **The real gap is unqueried, not unobservable:** prior
  lookups only covered SERVREG/locator/WLFW; the modem **core QMI services
  (`DMS`=2, `NAS`=3, `WDS`, voice)** were never queried. A read-only lookup
  matrix for those on the live modem node (modem must be up → a test-boot run)
  would directly test whether the native modem publishes the full service set
  Android's does. Caveat: enumeration shows server-side publication only; it
  does not reveal RIL's *client* interaction (`set_operating_mode`), which still
  needs strace/RIL capture.

Net: of the missing modem-facing actors, **RIL is the only heavyweight modem-QMI
actor** (Lead A); `time_daemon`/`qmuxd`/`netmgrd` are secondary low-prob
candidates worth a single read-only check but not a primary track.

## 6. Big picture / direction

- **The wall is now located: modem-internal.** Same firmware; native reproduces
  the full pm-service + cnss userspace; the modem still won't self-start
  `wlan_pd`. The Android modem self-starts it with **no explicit AP command**,
  so the differentiator is **modem internal state**, reachable via Lead A (the
  RIL modem-init QMI handshake) — Lead B (EFS) is refuted — not a single "magic"
  QMI we can send.
- **Why ~250 prior cycles did not crack it:** there was no missing piece in the
  userspace layers the project kept reproducing (companion stack, pm-service,
  service-notifier, cnss WLFW worker). The missing piece changes the **modem's
  internal state**, which those layers do not.
- **Structural-wall probability is elevated but the problem is still finite.**
  With Lead B (EFS) refuted, the surviving Lead A is enumerable. This validates the loop's RIL
  pivot (V1940–V1946) **in direction**, but **redirects** it: the relevant RIL
  role is the **DMS/NAS modem-init handshake**, not the PM **vote** (R5 shows the
  vote is identical to what native already does).
- **Downstream risk is low** (F3): once `wlan_pd` is up, WLFW → cap_req → BDF →
  `wlan0` already works in the Android captures with the native-served firmware.
  Residual downstream risks to keep in mind: MSA-ready handshake/User-PD grace
  crash (ath10k `qcom,no-msa-ready-indicator` Freebox case), BDF/`bdwlan.bin`
  and `regdb.bin` serve paths, and the fact that any RIL-init path eventually
  crosses from passive observation into **active modem activation**.

## 7. Capture methods for Lead A (2026-06-04 web survey) + recommended next unit

The Lead-A question needs **decoded** modem-bound QMI (not just "does RIL talk to
the modem" — obviously yes), so we can identify and later **reproduce** the
minimal modem-init message set. Surveyed methods, ranked by feasibility for this
project (native init, static aarch64 helpers, proven Magisk/strace handoffs,
read-only):

| method | what it gives | feasibility | risk |
|---|---|---|---|
| **strace `-s9999 -xx` on modem-facing daemons** (rild + cnss-daemon + pm-service) | raw `AF_QIPCRTR` `sendmsg/recvmsg` QMI bytes, decodable offline (service/msgid/TLV via libqmi catalog) | **HIGH** — project already straces cnss/tftp/rmt in handoffs (V1147/1149/1158/1753) without breaking the good boot; add `rild` | low; ptrace perturbs timing (V1226/V1611) but message *content* is fine |
| **full QRTR service enumeration** (`qrtr-lookup`-style wildcard `NEW_LOOKUP`) | the modem node's published service set (is `DMS`=2 / `NAS`=3 / `WDS` up?) | **HIGH** — extend helper `--qrtr-readback-matrix`; pure socket, read-only | low |
| **Frida QMI tracer** (postmarketOS VoLTE method) | cleanly **decoded** QMI → GSMTAP/pcap (`qmi-gsmtap-decode`) | MED — needs frida-server + libqmi hooks pushed in the handoff | new components → higher first-try-fail |
| **Qualcomm DIAG** (`/dev/diag`, QCSuper/`qc_debug_monitor` → `.qmdl` → SCAT) | the modem's own complete QMI/event stream | MED — most complete single source, but log-mask + `.qmdl` QMI parsing is finicky | first-try mask/parse mismatch can waste a cycle |

**Recommended next unit — one comprehensive low-risk capture (go deep once):**
a single rollbackable Android handoff that, across the `wlan_pd`-UP window,
captures (1) `strace -s9999 -xx -e trace=sendmsg,recvmsg,sendto,recvfrom` on
**rild + cnss-daemon + pm-service**, (2) `dmesg` for the `wlan_pd` state-up
timestamp (correlation), and (3) a full QRTR service enumeration. Then **decode
offline**: parse the QMI bytes (service/msgid), correlate against `wlan_pd`-UP,
and identify the modem-init handshake. This yields, in one cycle: Lead A
confirm/refute **plus** the actual message set to reproduce **plus** the modem
service-set completeness. Escalate to Frida/DIAG **only if** strace payloads
prove fragmented/undecodable, or if stracing rild perturbs the good boot.

- ~~Lead B (EFS) check~~ — **done/refuted** (native rmtfs serves the full EFS;
  v1713/v1691). Do not spend loop cycles on EFS.
- Only after this capture narrows the modem-init contract should any **bounded
  active** modem-init QMI replay on native be considered — that crosses the
  project's passive-observation line and needs an explicit separate gate.

## 8. Sources

**Project artifacts (local, gitignored evidence):**
- `tmp/wifi/v1934-android-libqmi-service69-positive-control-live-20260603-170139/` (Android logcat/dmesg)
- `tmp/wifi/v1753-android-good-wlan-pd-firmware-request/` (Android wlan_pd dmesg/logcat)
- `tmp/wifi/v1937-icnss-ipc-service69-integration/` (native A1 capture; pm-service + cnss uprobes)
- `tmp/wifi/v1945-ril-impl-export/vendor-source/lib64/libsec-ril.so` (sha256 `b61f6a910aaa56c364d98a7847bef8e9a585b019e03a958b3fc7e07310686bee`)
- `tmp/wifi/v766-icnss-qcacld-patch-apply-build/source/drivers/soc/qcom/icnss.c`
- Reports: V1899, V1908/V1909, V1919, V1922–V1935, V1940 (`POST180_SERVREG_PRODUCER_GAP`), V1941 (`ANDROID_PM_VOTER_DELTA`), V1943–V1946 (RIL/`libsec-ril` classifiers)

**External (web):**
- pd-mapper / user-PD-on-modem mechanism: https://cateee.net/lkddb/web-lkddb/QCOM_PD_MAPPER.html , https://lwn.net/Articles/973399/
- WCN3990 `wlanmdsp.mbn` via tqftpserv / modem-side load: https://lists.infradead.org/pipermail/ath10k/2023-December/015046.html
- `qcom,no-msa-ready-indicator` (modem MSA-ready / User-PD crash case): https://www.mail-archive.com/ath10k@lists.infradead.org/msg16244.html
- sm8150 WiFi deps (pd-mapper/tqftpserv/qrtr/rmtfs, wlanmdsp alongside modem.mbn): https://mail-archive.com/ath10k@lists.infradead.org/msg16353.html

**External (web) — QMI/QRTR capture methods (§7):**
- `qmicli` (QRTR URI, service enumeration): https://www.freedesktop.org/software/libqmi/man/latest/qmicli.1.html
- `qrtr-lookup` / libqrtr service discovery: https://www.freedesktop.org/software/libqmi/libqrtr-glib/latest/QrtrNode.html ; linux-msm/qrtr: https://github.com/andersson/qrtr
- QCSuper (DIAG capture): https://github.com/P1sec/QCSuper
- qc_debug_monitor (DIAG debug messages): https://github.com/Cr4sh/qc_debug_monitor
- postmarketOS Frida QMI sniffing (decoded QMI→GSMTAP/pcap): https://postmarketos.org/blog/2025/06/17/volte-project-qmi-sniffing-with-frida/

## 9. Safety scope

Host-only analysis. No device command, flash, reboot, partition/EFS write,
`/dev/subsys_esoc0` open, PMIC/GPIO/GDSC write, Wi-Fi HAL, scan/connect,
credentials, DHCP/routes, or external ping was performed. Read-only device
checks during the session were limited to `a90ctl.py version/status` over the
existing bridge (native `A90 Linux init 0.9.68 (v724)`, `selftest fail=0`).
