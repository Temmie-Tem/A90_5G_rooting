#ifndef A90_CONFIG_H
#define A90_CONFIG_H

#define INIT_VERSION "0.8.12"
#define INIT_BUILD "v81"
#define INIT_CREATOR "made by temmie0214"
#define INIT_BANNER "A90 Linux init " INIT_VERSION " (" INIT_BUILD ")"
#define BOOT_SPLASH_SECONDS 2
#define BOOT_HUD_REFRESH_SECONDS 2
#define NATIVE_LOG_PRIMARY "/cache/native-init.log"
#define NATIVE_LOG_FALLBACK "/tmp/native-init.log"
#define NATIVE_LOG_MAX_BYTES (256 * 1024)
#define KMS_LOG_TAIL_MAX_LINES 24
#define KMS_LOG_TAIL_LINE_MAX 96
#define BOOT_TIMELINE_MAX 32
#define CONSOLE_POLL_TIMEOUT_MS 1000
#define CONSOLE_IDLE_REATTACH_MS 60000
#define DISPLAY_TEST_PAGE_COUNT 4
#define AUTO_MENU_STATE_PATH "/tmp/a90-auto-menu-active"
#define AUTO_MENU_REQUEST_PATH "/tmp/a90-auto-menu-request"
#define NETSERVICE_FLAG_PATH "/cache/native-init-netservice"
#define NETSERVICE_LOG_PATH "/cache/native-init-netservice.log"
#define NETSERVICE_USB_HELPER "/cache/bin/a90_usbnet"
#define NETSERVICE_TCPCTL_HELPER "/cache/bin/a90_tcpctl"
#define NETSERVICE_TOYBOX "/cache/bin/toybox"
#define NETSERVICE_IFNAME "ncm0"
#define NETSERVICE_DEVICE_IP "192.168.7.2"
#define NETSERVICE_NETMASK "255.255.255.0"
#define NETSERVICE_TCP_PORT "2325"
#define NETSERVICE_TCP_IDLE_SECONDS "3600"
#define NETSERVICE_TCP_MAX_CLIENTS "0"
#define CMDV1X_MAX_ARGS 32
#define SD_BLOCK_NAME "mmcblk0p1"
#define SD_MOUNT_POINT "/mnt/sdext"
#define SD_FS_TYPE "ext4"
#define SD_WORKSPACE_DIR "/mnt/sdext/a90"
#define SD_EXPECTED_UUID "c6c81408-f453-11e7-b42a-23a2c89f58bc"
#define SD_ID_FILE SD_WORKSPACE_DIR "/.a90-native-id"
#define SD_BOOT_RW_TEST_FILE SD_WORKSPACE_DIR "/tmp/.boot-rw-test"
#define SD_NATIVE_LOG_PATH SD_WORKSPACE_DIR "/logs/native-init.log"
#define CACHE_STORAGE_ROOT "/cache"
#define TMP_STORAGE_ROOT "/tmp"
#define BOOT_SPLASH_LINE_COUNT 6
#define BOOT_SPLASH_LINE_MAX 96

#endif
