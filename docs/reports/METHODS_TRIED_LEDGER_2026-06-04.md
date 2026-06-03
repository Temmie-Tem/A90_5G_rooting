# Methods-Tried Ledger — native wlan0 bring-up

Date: 2026-06-04. Host-only synthesis of the full commit history (1969 commits,
`54cf982`..`c6e9a53`) plus CLAUDE.md vNNN log and the 2026-06-04 deep analysis
(`docs/reports/WLAN_PD_PRODUCER_TRIGGER_DEEP_ANALYSIS_2026-06-04.md`).

Purpose: stop the loop from re-running shallow attempts and from re-investigating
the wrong subsystem. This is a map of **what was tried, how deep, the result, and
what is genuinely untried** — not a new experiment.

---

## 0. The one finding that reframes everything

Commit spend vs. payoff, mined from 1969 commit subjects:

| Track | commits | history range | verdict |
|---|---:|---|---|
| **External SDX50M** (esoc/mdm3/RC1/pcie1/MHI/PERST/LTSSM/GPIO135-142) | **~171** | #696–#1914 | **deep but WRONG MODEM** — off the wlan0 path (2026-06-02 pivot) |
| host-only `classif*` reanalysis | **437** | throughout | reanalysis-heavy; high re-classify : new-evidence ratio |
| cnss / wlfw / icnss / service69 | 86 | #266–#1961 | live but mostly passive "wait / found=0" observation |
| service-window / pm-service / per_mgr / property / binder | 67 | #967–#1944 | deep; **closed** (V1629: clean exit is an *effect* of real OFFLINE state) |
| in-kernel trace (tracefs/bpf/kprobe/uprobe/ftrace) | 30 | #190–#1955 | feasibility-blocked early; never a usable HDD/PD observer |
| internal-modem wlan_pd real path (wlan_pd/tqftpserv/wlanmdsp/pd-mapper/rmt_storage) | 61 | #847–#1964 | **the actual producer path — under-tried with dedicated live work** |
| RIL / libsec-ril / DMS / QCRIL | **6** | #1760–#1969 | **export + source-classify only; NO live RIL-inclusive QMI capture** |

The headline: **~240 commits (external-modem eSoC/RC1/PCIe, ≈ 12% of the whole
project) were spent on a subsystem that does not host wlan0.** Meanwhile the
actual wlan0 producer — the internal modem's `msm/modem/wlan_pd` — and its only
unexercised driver (RIL DMS/NAS modem-init) got the *least* dedicated live work.

---

## 1. Method matrix

Depth legend: **D**=deep (many cycles / live + source), **M**=medium, **S**=shallow.
State: **CLOSED** (ruled out), **OFF-PATH** (wrong subsystem), **OPEN** (live lead),
**UNTRIED**.

| # | Method | range (vNNN / commit) | live? | depth | result | state |
|---|---|---|---|---|---|---|
| 1 | External eSoC ioctl (REG_REQ_ENG / WAIT_FOR_REQ / IMG_XFER_DONE / NOTIFY) | V846–V902 | live | D | reached `mdm_subsys_powerup` D-state; MDM2AP never asserts | OFF-PATH |
| 2 | `/dev/subsys_esoc0` open/hold | V847–V1238 | live | D | blocks in `mdm_subsys_powerup`, reboot-required | OFF-PATH |
| 3 | pci-msm corrected RC1 enumerate (`rc_sel=2`,`case=11`) | V1364–V1558 | live | D | RC1 PHY-ready→LTSSM POLL_COMPLIANCE→**no L0** | OFF-PATH |
| 4 | PMIC GPIO9 / AP2MDM GPIO135 PON parity | V1276–V1481 | live+host | D | GPIO135 set-high but sampled low; userspace hold EBUSY (kernel-owned) | OFF-PATH |
| 5 | Endpoint-electrical / pre-L0 tracefs (regulator/clk/gpio/irq) | V1499–V1552 | live | D | AP-side pcie1 GDSC/refclk/PERST confirmed; endpoint **silent** | OFF-PATH |
| 6 | Custom OSRC kernel w/ ICNSS/QCACLD log patch | V765–V775 | flash | D | builds; boots to Download-mode / no native init | PAUSED (boot-incompat) |
| 7 | tracefs / ftrace function filter | V754–V777 | live | M | mount works; `available_filter_functions` unavailable | CLOSED |
| 8 | BPF on `msm_pil_event:pil_notif` | V778–V782 | live | M | attach/count works; 8 PIL notifs, no service69 | CLOSED (observer only) |
| 9 | kprobe / dynamic-debug | V754, V1955 | host | S | not configured / not compiled in | CLOSED |
| 10 | `boot_wlan` + `qcwlanstate` lower-window | V750–V782 | live | M | enters HDD init, never "driver loaded" / ICNSS-QMI | CLOSED (needs producer first) |
| 11 | CNSS companion stack (qrtr-ns→pd-mapper→rmt→tftp→cnss_diag→cnss-daemon) | V735–V1586 | live | D | starts clean; reaches cld80211 netlink; **WLFW found=0** | OPEN (downstream of producer) |
| 12 | service-window pm-service/per_mgr full actor set | V856–V1633 | live | D | pm-service reaches subsys_modem fd; **clean-exits on OFFLINE state** | CLOSED (V1629 causality) |
| 13 | private property root / shutdown_critical_list shim | V857–V1628 | live | D | denials→0; pm-service still OFFLINE-branch exit | CLOSED |
| 14 | firmware mount parity (sda29 RO vendor overlay) | V268–V1586 | live | M | modem PIL "Brought out of reset"; mss ONLINE | DONE (prereq satisfied) |
| 15 | QRTR AF_QIPCRTR nameservice lookup matrix (servloc/servnotif/ssctl/wlfw) | V821–V829 | live | M | servloc 64/257 + servnotif 66/46081 publish; **wlfw 69 empty** | OPEN (never queried DMS/NAS) |
| 16 | service-locator GET_DOMAIN_LIST wlan/fw | V829 | live | M | returns `msm/modem/wlan_pd` inst 180 | DONE |
| 17 | service-notifier REGISTER_LISTENER on wlan_pd 180 | V830–V838 | live | D | QMI success but state `0x7fffffff` UNINIT; no indication | CLOSED (producer-side, not listener) |
| 18 | Android positive-control (handoff + rollback) | V833–V1957 | live | D | proves model valid: wlan_pd UP→WLFW→BDF→wlan0 | reference |
| 19 | Android tracefs queue-pair / PIL / sched capture | V1529–V1555 | live | M | icnss_driver_event_work = macloader HDD path, not first-trigger | CLOSED |
| 20 | Android msg22 / PM msgid edge capture | V1920–V1937 | live | M | tag-filtered logcat; **excludes RIL/DMS** | OPEN (re-capture w/o filter) |
| 21 | libsec-ril source export + PM-voter classify | V1940–V1946 | host | S | PLT shows only pm_client_register/connect — same as native | OPEN (DMS/NAS unread) |
| 22 | native A1 producer capture (pm-service + cnss uprobe) | V1937 | live | D | native == Android userspace; modem still silent | decisive (modem-internal wall) |

---

## 2. Deep but misdirected — External SDX50M (DO NOT REVISIT)

Methods #1–#5 above, ~240 commits, V844→~V1669. The entire eSoC/RC1/PCIe/MHI
investigation targeted the **external SDX50M 5G modem** (subsys9/esoc0/mdm3/pcie1).

Why it's off-path (triple-confirmed, `WLAN_PD_REDIRECT_AND_FIRMWARE_SERVE_GATE_2026-06-02.md`):
- wlan0 = ICNSS path on the **internal** modem (subsys0/mss). `wlanmdsp.mbn` is
  sideloaded to the internal modem DSP via tqftpserv.
- Timing proves precedence: wlan_pd UP **2153 ms before** esoc0 (V620); wlfw_start
  **53 ms before** esoc0 (V1331); trace `pil_modem=8 pil_esoc=0`.
- The external modem reaching (or not reaching) MDM2AP/RC1-L0 is irrelevant to wlan0.

Conclusion reached on that track was real (hardware wall at MDM2AP/LTSSM), but it
answers the wrong question. **Any future esoc/RC1/pcie1/GPIO135-142/PERST/MHI unit
is wasted** unless the goal explicitly changes to the SDX50M PCIe modem.

---

## 3. Tried but shallow — re-deepen candidates (HIGHEST VALUE)

These were touched but never driven to a decisive live result. Each lists the
gap and the new evidence needed.

### 3.1 RIL DMS/NAS modem-init handshake — **Lead A, top priority**
- Tried (#21, V1940–1946): only **source export + static classify** of
  `libsec-ril.so`. Found the PM-vote path (`ModemBoot::PeripheralManagerVote`)
  uses the same `pm_client_register/connect` native already runs → PM-vote refuted.
- **Never tried:** a live RIL-inclusive QMI capture. The DMS path
  (`QMI_DMS_SET/GET_OPERATING_MODE`) and NAS bring-up are the one heavyweight
  modem-QMI actor native does not run, and the existing Android logcat is
  **tag-filtered and excludes RIL/DMS** (#20).
- New evidence needed: Android handoff capturing modem-bound QMI in the
  wlan_pd-UP window with RIL included (strace on rild, or QRTR DMS/NAS lookup).

### 3.2 QRTR registry — DMS/NAS services never enumerated
- Tried (#15, V821–829): AF_QIPCRTR lookup for servloc/servnotif/ssctl/wlfw only.
  #1865 ran a qrtr registry handoff once.
- **Never queried:** DMS (0x02), NAS (0x03), WDS on the modem node — exactly the
  services RIL drives. The "visibility limitation" is narrow (only debugfs dumps
  absent); services ARE enumerable via socket lookup.
- New evidence needed: read-only DMS/NAS/WDS lookup matrix on the modem node,
  Android-good vs native, in the wlan_pd window.

### 3.3 tqftpserv actually serving wlanmdsp.mbn to the internal modem
- project_goal.md marks this the **first gate** and **UNVERIFIED**.
- Firmware *mount* parity is done (#14), and EFS serve is proven (rmt_storage,
  v1713/v1691), but a live trace that the **internal modem requests and receives
  `wlanmdsp.mbn` over tftp** (as Android does at logcat 51.389) was never captured
  on native.
- New evidence needed: native tftp/tqftpserv request trace during the lower window;
  compare against Android's self-request.

### 3.4 Unfiltered Android PM/QMI capture
- Tried (#20): msg22 / PM msgid edges, but logcat tag-filtered.
- New evidence needed: re-run the existing Android handoff with **no logcat tag
  filter** + dmesg wlan_pd timestamp anchor, so the RIL/DMS lines are retained.

---

## 4. Completely untried (zero commits)

| Method | feasibility | risk | why it could discriminate |
|---|---|---|---|
| **strace `-s9999 -xx` on rild + cnss-daemon + pm-service** (single Android handoff) | HIGH | low (read-only) | dumps exact AF_QIPCRTR sendmsg/recvmsg payloads → decode the modem-init QMI native is missing |
| **Frida QMI tracer** (postmarketOS VoLTE method → GSMTAP/pcap) | MED | low | structured QMI service/msg decode if raw strace payloads fragment |
| **Qualcomm DIAG / QCSuper / qc_debug_monitor** (`/dev/diag`→qmdl→SCAT) | MED | med (DIAG enable) | modem-side view of PD load decisions |
| **qmicli / qrtr-lookup full enumeration** in the live window | HIGH | low | one-shot Service/Version/Instance/Node/Port census incl. DMS/NAS |
| **modem ROOT-PD → pd_mapper query observation** | MED | low | confirms which guest PDs the modem decides to load and when |

None of strace/Frida/DIAG/qmicli appear anywhere in 1969 commits.

---

## 5. Refuted — DO NOT RETRY (with kill evidence)

From the 2026-06-04 deep analysis (R1–R8) plus Lead B:

| id | hypothesis | killed by |
|---|---|---|
| R1 | `modemuw.jsn` mismatch | V1919 |
| R2 | msg22 message gate | V1899 |
| R3 | empty pd-mapper DB | V829 / V1908 (returns wlan_pd 180) |
| R4 | A1 actor combo missing | V1922–1935 |
| R5 | RIL PM-vote missing | libsec-ril = same pm_client_register native runs |
| R6 | `service_notif_pd_restart` trigger | recovery-only (icnss_trigger_recovery) |
| R7 | operating-mode not ONLINE | airplane-mode WiFi works |
| R8 | native pm-service early-exit | V1937 (alive, 6 threads, opens subsys_modem fd8) |
| LB | modem EFS/NV parity | native serves full ~2MB EFS (v1713/v1691) |

Also closed: service-window route entirely (#12/#13, V1629 — pm-service OFFLINE
branch is an effect of real `subsys9=OFFLINING`, not the blocker); ftrace/kprobe
observers (#7/#9); listener-side timing on wlan_pd 180 (#17, V830–838).

---

## 6. Why so many cycles were shallow

Three structural patterns in the history explain the under-depth:

1. **Reanalysis loop** — 437 `classify` commits. The loop frequently re-classifies
   existing evidence (host-only) instead of capturing new live evidence. Many
   "next gate" selections produced another classifier, not a measurement.
2. **Wrong-subsystem lock-in** — once V844 anchored on esoc0, ~240 commits chased
   the external modem to a hardware wall before the 2026-06-02 redirect.
3. **Producer/consumer inversion** — most live work (cnss/wlfw/service69/listener)
   sits on the **consumer** side waiting for `wlan_pd` UP. The **producer** (the
   internal modem deciding to start the guest PD) was probed almost entirely by
   *classification*, never by a RIL-inclusive live QMI capture.

---

## 7. Recommended next units (priority order)

1. **One comprehensive low-risk capture (go deep once):** single rollbackable
   Android handoff — `strace -s9999 -xx -e trace=sendmsg,recvmsg,sendto,recvfrom`
   on rild + cnss-daemon + pm-service, **unfiltered** dmesg for the wlan_pd UP
   timestamp, and a full `qrtr-lookup` enumeration. Decode QMI offline. This single
   unit covers Lead A (3.1), the DMS/NAS gap (3.2), and the unfiltered capture (3.4).
2. If strace payloads fragment → **Frida QMI tracer** for structured decode.
3. **Native tqftpserv serve verification** (3.3) — confirm the first gate before
   any producer-trigger attempt.
4. Only if 1–3 implicate a specific modem-side decision → consider **DIAG**.

Each is read-only / rollbackable and inside the existing safety scope. None
requires a new write primitive.

---

## 8. Sources

- Full commit history `54cf982`..`c6e9a53` (1969 commits); keyword/era mining
  2026-06-04 (this ledger's tables are derived from `git log --format=%s`).
- CLAUDE.md vNNN log (through V1633 in-file; frontier V1946).
- `docs/reports/WLAN_PD_PRODUCER_TRIGGER_DEEP_ANALYSIS_2026-06-04.md` (R1–R8, Lead A,
  capture-method survey, web sources).
- `docs/reports/WLAN_PD_REDIRECT_AND_FIRMWARE_SERVE_GATE_2026-06-02.md` (wrong-modem
  redirect, triple confirmation).
- memory `project-goal-and-structure` (corrected architecture, surviving leads).
