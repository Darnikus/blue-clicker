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

void esp_bt_gap_cb(esp_bt_gap_cb_event_t event, esp_bt_gap_cb_param_t *param) {
    switch (event) {
        case ESP_BT_GAP_AUTH_CMPL_EVT: {
            if (param->auth_cmpl.stat == ESP_BT_STATUS_SUCCESS) {
                ESP_LOGI(TAG, "Classic BT Authentication Success: %s", param->auth_cmpl.device_name);
            } else {
                ESP_LOGE(TAG, "Classic BT Authentication Failed, status:%d", param->auth_cmpl.stat);
            }
            break;
        }
        case ESP_BT_GAP_PIN_REQ_EVT: {
            // This is where the 1234 PIN we set above gets used
            ESP_LOGI(TAG, "Classic BT PIN Request. Sending default PIN...");
            if (param->pin_req.min_16_digit) {
                // Should not happen with typical SPP
            } else {
                esp_bt_pin_code_t pin_code = {'1', '2', '3', '4'};
                esp_bt_gap_pin_reply(param->pin_req.bda, true, 4, pin_code);
            }
            break;
        }
        default:
            break;
    }
}

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
    /* Set Classic BT (SPP) Security */
    esp_bt_sp_param_t param_type = ESP_BT_SP_IOCAP_MODE;
    esp_bt_io_cap_t bt_iocap = ESP_BT_IO_CAP_NONE;
    esp_bt_gap_set_security_param(param_type, &bt_iocap, sizeof(uint8_t));

    /* Enable PIN pairing for older clients if needed */
    esp_bt_pin_type_t pin_type = ESP_BT_PIN_TYPE_FIXED;
    esp_bt_pin_code_t pin_code = {'1', '2', '3', '4'};
    esp_bt_gap_set_pin(pin_type, 0, pin_code);

    // Initialize SPP
    esp_spp_cfg_t spp_cfg = {.mode = ESP_SPP_MODE_CB, .enable_l2cap_ertm = true};
    ESP_ERROR_CHECK(esp_spp_register_callback(esp_spp_cb));
    ESP_ERROR_CHECK(esp_spp_enhanced_init(&spp_cfg));

    ESP_LOGI(TAG, "SPP Module initialized");
}