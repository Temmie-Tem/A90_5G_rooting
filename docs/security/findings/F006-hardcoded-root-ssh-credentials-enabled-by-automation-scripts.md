# F006. Hardcoded root SSH credentials enabled by automation scripts

## Metadata

| field | value |
|---|---|
| finding_id | `ab2b5073f1388191a97d38ceaf0ce7b9` |
| finding_url | https://chatgpt.com/codex/cloud/security/findings/ab2b5073f1388191a97d38ceaf0ce7b9 |
| severity | `high` |
| status | `mitigated-host-batch5` |
| detected_at | `2026-04-27T22:50:57.207425Z` |
| committed_at | `2025-11-18 11:14:47 +0900` |
| commit_hash | `8775fe9dc00c9491470aae177203bf68a3b02234` |
| relevant_paths | `scripts/archive/legacy/utils/create_rootfs.sh | scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh | scripts/archive/legacy/magisk_module/headless_boot_v2/service.sh` |
| has_patch | `true` |

## CSV Description

Newly added automation scripts set `PermitRootLogin yes`, keep password auth enabled, and set the root password to a known static value (`root`). Another boot-time script starts `sshd` automatically and even logs connection guidance including the default password. A headless boot script then invokes this chroot SSH startup automatically when the module exists. Any attacker on the same network segment who can reach port 22 can authenticate as root using default credentials if the user has not manually changed it.

## Local Remediation

- Batch 5 changes archived rootfs automation to disable password SSH auth, keep root login key-only, lock the root password, and remove default `root` password guidance from boot logs.

## Codex Cloud Detail

Hardcoded root SSH credentials enabled by automation scripts
Link: https://chatgpt.com/codex/cloud/security/findings/ab2b5073f1388191a97d38ceaf0ce7b9
Criticality: high (attack path: high)
Status: new

# Metadata
Repo: Temmie-Tem/A90_5G_rooting
Commit: 8775fe9
Author: aosp@build.local
Created: 2026. 4. 28. 오전 7:50:57
Assignee: Unassigned
Signals: Security, Validated, Patch generated, Attack-path

# Summary
Introduced security bug: default, hardcoded root SSH credentials plus automatic SSH startup.
Newly added automation scripts set `PermitRootLogin yes`, keep password auth enabled, and set the root password to a known static value (`root`). Another boot-time script starts `sshd` automatically and even logs connection guidance including the default password. A headless boot script then invokes this chroot SSH startup automatically when the module exists. Any attacker on the same network segment who can reach port 22 can authenticate as root using default credentials if the user has not manually changed it.

# Validation
## Rubric
- [x] Confirm the vulnerable scripts/paths were introduced by the target commit.
- [x] Confirm root SSH + password authentication are explicitly enabled and a static root password is set in rootfs creation.
- [x] Confirm SSH daemon is started automatically by boot service logic.
- [x] Confirm boot-time/user-facing logs disclose default root SSH credential guidance.
- [x] Reproduce the effective insecure configuration behavior with a minimal PoC in-container.
## Report
I validated the finding with targeted file inspection plus a minimal non-destructive PoC.

1) Commit-introduction check:
- `git show --summary 8775fe9... -- <3 files>` shows all relevant scripts were created in this commit:
  - `scripts/utils/create_rootfs.sh`
  - `scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh`
  - `scripts/magisk_module/headless_boot_v2/service.sh`

2) Insecure default SSH/root credentials are explicitly configured:
- `scripts/utils/create_rootfs.sh:267` enters chroot context.
- In that chroot install block, lines `309-314` set:
  - `PermitRootLogin yes`
  - `PasswordAuthentication yes`
  - `echo "root:root" | chpasswd`
- Lines `376-377` print the default root password (`root`) and tell user to change it later.

3) SSH is auto-started at boot and password is disclosed in logs:
- `scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh:133` starts `/usr/sbin/sshd` in chroot.
- `.../boot_chroot.sh:171` logs `SSH: ssh root@$WIFI_IP (password: root)`.

4) Headless boot triggers this automatically:
- `scripts/magisk_module/headless_boot_v2/service.sh:301-303` runs `boot_chroot.sh` in background when module exists.

5) Dynamic PoC evidence:
- Ran `/workspace/validation_artifacts/default-root-ssh-credentials/poc_default_root_ssh.sh` (emulates the exact sed/chpasswd logic safely in a temp root dir).
- Output (`poc_output.txt`) shows:
  - `root_password_valid True`
  - resulting `sshd_config`:
    - `PermitRootLogin yes`
    - `PasswordAuthentication yes`
    - `Port 22`

Method-attempt notes per policy:
- Crash attempt surrogate executed (logic vuln, no crash expected): completed, exit 0.
- Valgrind attempt: `valgrind` not installed (`command not found`).
- Debugger attempt: `gdb` not installed (`command not found`).

Conclusion: the suspected issue is valid. The commit introduces an auto-boot SSH path plus known default root credentials, enabling straightforward adjacent-network root compromise if unchanged by the user.

# Evidence
scripts/magisk_module/headless_boot_v2/service.sh (L301 to 303)
  Note: Automatically invokes chroot boot script, which starts SSH, making insecure SSH exposure happen on boot when module is present.
```
if [ -f "/data/adb/modules/systemless_chroot/service.d/boot_chroot.sh" ]; then
    sh /data/adb/modules/systemless_chroot/service.d/boot_chroot.sh >> "$LOGFILE" 2>&1 &
    sleep 2
```

scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh (L133 to 136)
  Note: Starts SSH daemon automatically at boot in the chroot environment.
```
$BUSYBOX chroot "$CHROOT_MNT" /usr/sbin/sshd -E /var/log/sshd.log 2>>"$LOGFILE"

if [ $? -eq 0 ]; then
    log "  SSH server started successfully"
```

scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh (L170 to 172)
  Note: Logs SSH command with the default password (`password: root`), reinforcing exploitable default credentials.
```
if [ -n "$WIFI_IP" ]; then
    log "SSH: ssh root@$WIFI_IP (password: root)"
else
```

scripts/utils/create_rootfs.sh (L309 to 314)
  Note: Explicitly enables root SSH login and password authentication, then sets a hardcoded root password (`root:root`).
```
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config

# Root 비밀번호 (기본값)
echo "root:root" | chpasswd
```

scripts/utils/create_rootfs.sh (L376 to 377)
  Note: Confirms the default root password in output, indicating this insecure credential is intentional default behavior.
```
    echo "기본 root 비밀번호: root"
    echo "보안을 위해 SSH 접속 후 비밀번호를 변경하세요!"
```

Proposed patch:
diff --git a/scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh b/scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh
index ed3911c93f007aeb6b8bbde8e7c66fad06a7db90..dd5d07d634352c4f697ed2dfe1b09e34e13d863a 100755
--- a/scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh
+++ b/scripts/archive/legacy/magisk_module/systemless_chroot/service.d/boot_chroot.sh
@@ -146,33 +146,33 @@ log "[Step 4/5] SSH service handled"
 # ====================================================================

 log "[Step 5/5] Logging network information..."

 # WiFi IP 주소 확인
 WIFI_IP=$(ip -4 addr show wlan0 2>/dev/null | grep inet | awk '{print $2}' | cut -d/ -f1)

 if [ -n "$WIFI_IP" ]; then
     log "  WiFi IP: $WIFI_IP"
     log "  SSH Connection: ssh root@$WIFI_IP"
 else
     log "  WiFi not connected yet"
 fi

 log "[Step 5/5] Network info logged"

 # ====================================================================
 # 완료
 # ====================================================================

 log "========================================="
 log "Chroot services started successfully!"
 log "========================================="

 if [ -n "$WIFI_IP" ]; then
-    log "SSH: ssh root@$WIFI_IP (password: root)"
+    log "SSH: ssh root@$WIFI_IP (key-based auth)"
 else
     log "Connect to WiFi and check IP with: ip addr show wlan0"
 fi

 log ""

-exit 0
\ No newline at end of file
+exit 0


diff --git a/scripts/archive/legacy/utils/create_rootfs.sh b/scripts/archive/legacy/utils/create_rootfs.sh
index 76b97813cac5609042b7825aaf9e5c0562eee446..dc6259aa1355bfb135866e9a9533d0f4c5df6a8f 100755
--- a/scripts/archive/legacy/utils/create_rootfs.sh
+++ b/scripts/archive/legacy/utils/create_rootfs.sh
@@ -283,57 +283,57 @@ apt install -y \
     git \
     htop \
     tmux \
     screen \
     net-tools \
     iputils-ping \
     traceroute \
     dnsutils \
     build-essential \
     python3 \
     python3-pip \
     python3-venv \
     gcc \
     g++ \
     make \
     cmake \
     gdb \
     strace \
     locales

 # SSH 디렉토리
 mkdir -p /run/sshd
 mkdir -p /root/.ssh
 chmod 700 /root/.ssh

-# SSH 설정
-sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
-sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
+# SSH 설정 (보안 기본값: root 비밀번호 로그인 비활성화)
+sed -i -E 's/^#?PermitRootLogin .*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
+sed -i -E 's/^#?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
 sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config

-# Root 비밀번호 (기본값)
-echo "root:root" | chpasswd
+# Root 계정 비밀번호 잠금 (SSH 키 기반 접속만 허용)
+passwd -l root >/dev/null 2>&1 || true

 # 타임존
 ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

 # 로케일
 echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
 echo "ko_KR.UTF-8 UTF-8" >> /etc/locale.gen
 locale-gen
 update-locale LANG=en_US.UTF-8

 # 불필요한 서비스 비활성화 (headless)
 systemctl disable bluetooth 2>/dev/null || true
 systemctl disable avahi-daemon 2>/dev/null || true

 # APT 캐시 정리
 apt clean
 apt autoremove -y

 echo ""
 echo "====================================="
 echo "  패키지 설치 완료!"
 echo "====================================="

 CHROOT_EOF

@@ -351,35 +351,35 @@ CHROOT_EOF
     # Step 10: 이미지 무결성 검사
     log_info "[Step 10/10] 이미지 무결성 검사 중..."
     e2fsck -f -y "$IMG_NAME"
     log_success "무결성 검사 완료"

     # 완료
     echo ""
     echo "========================================"
     echo "  🎉 Rootfs 생성 완료!"
     echo "========================================"
     echo ""
     echo "출력 파일: $IMG_NAME"
     echo "파일 크기: $(du -h "$IMG_NAME" | cut -f1)"
     echo ""
     echo "다음 단계:"
     echo "1. 이미지를 디바이스로 전송:"
     echo "   adb push $IMG_NAME /sdcard/"
     echo ""
     echo "2. 디바이스에서 이동:"
     echo "   adb shell"
     echo "   su"
     echo "   mv /sdcard/$IMG_NAME /data/linux_root/"
     echo ""
     echo "3. Magisk 모듈 설치 후 재부팅"
     echo ""
-    echo "기본 root 비밀번호: root"
-    echo "보안을 위해 SSH 접속 후 비밀번호를 변경하세요!"
+    echo "기본 SSH 비밀번호 로그인: 비활성화"
+    echo "보안을 위해 SSH 키를 설정한 후 접속하세요."
     echo ""
 }

 # ====================================================================
 # 스크립트 실행
 # ====================================================================

 main "$@"

# Attack-path analysis
Final: high | Decider: model_decided | Matrix severity: medium | Policy adjusted: medium
## Rationale
Kept at high because code-backed evidence shows a direct, non-speculative attack path: boot-time sshd startup + root password auth + hardcoded root credential. Impact is major (root compromise). Not raised to critical due local-network (adjacent) exposure and dependency on deployment/user behavior (module installed, password not changed), which reduce universality versus broad unauthenticated internet exploitation.
## Likelihood
medium - Exploit steps are simple (known credentials over SSH) but require adjacent-network reachability and unchanged default password; these conditions are plausible in typical Wi-Fi deployment.
## Impact
high - Successful exploitation yields remote root shell over SSH in the deployed Linux environment, enabling full command execution and broad compromise of device-side Linux workload integrity/confidentiality/availability.
## Assumptions
- Magisk service scripts execute as root on the target Android device.
- The user follows repository setup flow (create_rootfs + module install + reboot).
- Device is reachable from at least one local network segment (e.g., Wi-Fi).
- User does not immediately rotate the default root password.
- Rootfs image created using scripts/utils/create_rootfs.sh
- systemless_chroot/headless_boot_v2 Magisk modules installed and booted
- Attacker has network path to device on TCP/22
- Default root password remains unchanged
## Path
[LAN attacker] -> [sshd on :22 auto-started] -> [login root/root] -> [root shell in chroot]
## Path evidence
- `scripts/utils/create_rootfs.sh:309-314` - Explicitly enables root SSH login, enables password authentication, and sets root password to static value root:root.
- `scripts/utils/create_rootfs.sh:376-377` - Prints default root password in user-facing output, confirming intended default credential behavior.
- `scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh:4-6` - Script comment states boot-time execution and purpose to start SSH service.
- `scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh:133-136` - Starts sshd automatically in chroot during boot service flow.
- `scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh:151-155` - Uses Wi-Fi IP and logs SSH connection string, indicating network-reachable SSH usage.
- `scripts/magisk_module/systemless_chroot/service.d/boot_chroot.sh:170-171` - Logs explicit default credential guidance '(password: root)'.
- `scripts/magisk_module/headless_boot_v2/service.sh:301-303` - Automatically invokes boot_chroot.sh at boot when module exists.
- `scripts/magisk_module/systemless_chroot/post-fs-data.sh:163-170` - Bind-mounts /dev into chroot, indicating high-privilege runtime context once root shell is obtained.
## Narrative
The repository’s normal automation path configures SSH for root password login, sets root password to a known static value (root), and auto-starts sshd at boot. This creates a realistic adjacent-network remote root compromise path when the module is installed and the default password remains unchanged.
## Controls
- Weak control only: post-setup message asks user to change password manually
- No script-level SSH hardening enforcing non-root or key-only auth
- No repository evidence of firewall/network ACL enforcement for SSH in these runtime scripts
## Blindspots
- Static-only analysis cannot confirm real-world router/NAT/firewall conditions around the device.
- Could not verify whether downstream users commonly rotate credentials immediately after setup.
- No runtime packet-level validation in this stage; reliance is on script logic and prior validation artifact.
