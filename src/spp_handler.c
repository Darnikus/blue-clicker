#include "spp_handler.h"
#include "hid_dev.h"    // So it knows what hid_key_t is
#include "esp_log.h"
#include "esp_bt_main.h"
#include "esp_gap_bt_api.h"

#define SPP_SERVER_NAME "ESP32_Key_Bridge"
static const char *TAG = "SPP_HANDLER";

// This tells the SPP file that the send_ble_key function 
// is still living over in main.c for now.
extern void send_ble_key(uint8_t key_code, uint8_t modifier);

void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param) {
    switch (event) {
        case ESP_SPP_INIT_EVT:
            esp_bt_gap_set_device_name(SPP_SERVER_NAME);
            esp_bt_gap_set_scan_mode(ESP_BT_CONNECTABLE, ESP_BT_GENERAL_DISCOVERABLE);
            // Change ESP_SPP_SEC_NONE to ESP_SPP_SEC_AUTHENTICATE
            esp_spp_start_srv(ESP_SPP_SEC_AUTHENTICATE, ESP_SPP_ROLE_SLAVE, 1, SPP_SERVER_NAME);
            break;
        case ESP_SPP_DATA_IND_EVT:
            ESP_LOGI(TAG, "Relaying %d bytes to PC2", param->data_ind.len);
            for (int i = 0; i < param->data_ind.len; i++) {
                uint8_t data = param->data_ind.data[i];
                if (data == '\n' || data == '\r') continue;

                hid_key_t k = ascii_to_hid(data);
                if (k.code != 0) {
                    // Updated send_ble_key to accept modifier
                    send_ble_key(k.code, k.modifier); 
                }
            }
            break;
        case ESP_SPP_SRV_OPEN_EVT:
            ESP_LOGI(TAG, "PC1 connected (SPP)");
            break;
        case ESP_SPP_CLOSE_EVT:
            ESP_LOGI(TAG, "PC1 disconnected (SPP)");
            break;
        default: break;
    }
}

void spp_init(void) {
    // Initialize SPP
    esp_spp_cfg_t spp_cfg = {.mode = ESP_SPP_MODE_CB, .enable_l2cap_ertm = true};
    ESP_ERROR_CHECK(esp_spp_register_callback(esp_spp_cb));
    ESP_ERROR_CHECK(esp_spp_enhanced_init(&spp_cfg));

    ESP_LOGI(TAG, "SPP Module initialized");
}