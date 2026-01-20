#include <stdio.h>
#include <string.h>
#include "nvs_flash.h"
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_log.h"
#include "esp_spp_api.h"
#include "esp_gap_bt_api.h"

#define SPP_SERVER_NAME "ESP32_Key_Bridge"
#define SPP_SHOW_DATE_LEN 32

static const char *TAG = "BT_SPP";

// Callback function
void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param);

void app_main() {

    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();

    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    // Enable Dual Mode (Classic + BLE)
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BTDM));
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());

    // --- SPP code --

    // 1. Register SPP Callback
    ESP_ERROR_CHECK(esp_spp_register_callback(esp_spp_cb));

    // 2. SPP mode initialization (Client/Server)
    esp_spp_cfg_t spp_cfg = {
        .mode = ESP_SPP_MODE_CB,
        .enable_l2cap_ertm = true, // Common default
    };

    esp_bt_cod_t cod;
    cod.major = ESP_BT_COD_MAJOR_DEV_COMPUTER; // Tell Linux we are a "Computer" class device
    esp_bt_gap_set_cod(cod, ESP_BT_SET_COD_ALL);

    ESP_ERROR_CHECK(esp_spp_enhanced_init(&spp_cfg));

    ESP_LOGI(TAG, "Dual Mode stack is up. SPP initialized.");

    ESP_LOGI(TAG, "Bluetooth dual mode activated succesfuly");
    ESP_LOGI(TAG, "NExt stape");
}

void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param) {
    switch (event) {
        case ESP_SPP_INIT_EVT:
            // SPP initialized, now get device's name and start the server
            ESP_LOGI(TAG, "ESP_SPP_INIT_EVT");
            esp_bt_gap_set_device_name(SPP_SERVER_NAME);
            esp_bt_gap_set_scan_mode(ESP_BT_CONNECTABLE, ESP_BT_GENERAL_DISCOVERABLE);
            // Start SPP server (initialize SPP_START_EVT)
            esp_spp_start_srv(ESP_SPP_SEC_NONE, ESP_SPP_ROLE_SLAVE, 1, SPP_SERVER_NAME);
            break;

        case ESP_SPP_START_EVT:
            // Server started, ready for connection
            ESP_LOGI(TAG, "ESP_SPP_START_EVT handle:%d sec_id:%d scn:%d", param->start, param->start.sec_id, param ->start.scn);
            ESP_LOGI(TAG, "SPP Server is ready. Look for a device '%s' at PC1.", SPP_SERVER_NAME);
            break;

        case ESP_SPP_SRV_OPEN_EVT:
            // Client connected
            ESP_LOGI(TAG, "ESP_SPP_SRV_OPEN_EVT Status %d handle %d, PC1 connected.", param->srv_open.status, param->srv_open.handle);
            break;

        case ESP_SPP_DATA_IND_EVT:
            // Received data from a client (it's a part that i need!)
            ESP_LOGI(TAG, "ESP_SPP_DATA_IND_EVT len=%d handle=%d", param->data_ind.len, param->data_ind.handle);

            // Print received data for debugging
            ESP_LOG_BUFFER_CHAR(TAG, param->data_ind.data, param->data_ind.len);

            // !!Here will be the logic of handling keys' codes
            // TODO: Logic to pass this data to the BLE Keyboard component
            break;

        case ESP_SPP_CLOSE_EVT:
            // CLient disconnected
            ESP_LOGI(TAG, "ESP_SPP_CLOSE_EVT Status %d handle %d, PC1 disconnected.", param -> close.status, param-> close.handle);
            break;

        default:
            break;
    }
}