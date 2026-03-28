#include <stdio.h>
#include <string.h>
#include "nvs_flash.h"
#include "esp_log.h"
#include "esp_err.h"

// System-level BT management
#include "esp_bt.h"
#include "esp_bt_main.h"

#include "spp_handler.h"
#include "ble_hid_handler.h"

static const char *TAG = "KEY_BRIDGE";

void app_main() {
    // 1. Storage
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // 2. Hardware/Radio
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BTDM));
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());

    // 3. Services
    spp_init();    // PC1 Logic + Classic Security + CoD
    ble_hid_init(); // PC2 Logic + BLE Security

    ESP_LOGI(TAG, "System ready. PC1: SPP, PC2: BLE Keyboard.");
}