#include "spp_handler.h"
#include "hid_dev.h"    // So it knows what hid_key_t is
#include "esp_log.h"
#include "esp_bt_main.h"
#include "esp_gap_bt_api.h"
#include "esp_bt.h"

#define MAX_PAYLOAD_LEN 64
#define SPP_SERVER_NAME "ESP32_Key_Bridge"
static const char *TAG = "SPP_HANDLER";

typedef struct {
    char action[16];
    char payload[16];
    bool success;
} parsed_packet_t;

// This tells the SPP file that the send_ble_key function 
// is still living over in main.c for now.
extern void send_ble_key(uint8_t key_code, uint8_t modifier);

parsed_packet_t parse_spp_data(uint8_t *data, uint16_t len) {
    parsed_packet_t result = {0};
    
    if (len >= MAX_PAYLOAD_LEN) {
        ESP_LOGE(TAG, "Packet is too large: %d bytes", len);
        return result;
    }

    char local_copy[MAX_PAYLOAD_LEN];
    memcpy(local_copy, data, len);
    local_copy[len] = '\0';

    char *outer_saveptr = NULL;
    char *outer_token = strtok_r(local_copy, "|", &outer_saveptr);
    int success_count = 0; 

    while (outer_token != NULL) {
        char *inner_saveptr = NULL;

        char *key = strtok_r(outer_token, ":", &inner_saveptr);
        char *value = strtok_r(NULL, ":", &inner_saveptr);

        if (key != NULL && value != NULL) {
            if (strcmp(key, "ACTION") == 0) {
                strncpy(result.action, value, sizeof(result.action) - 1);
                success_count++;
            } else if (strcmp(key, "PAYLOAD") == 0) {
                strncpy(result.payload, value, sizeof(result.payload) - 1);
                success_count++;
            }
        }
        outer_token = strtok_r(NULL, "|", &outer_saveptr);
    }

    if (success_count == 2) {
        result.success = true;
    }
    return result;
}

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
            esp_spp_start_srv(ESP_SPP_SEC_NONE, ESP_SPP_ROLE_SLAVE, 1, SPP_SERVER_NAME);
            break;
        case ESP_SPP_DATA_IND_EVT:
            ESP_LOGI(TAG, "Relaying %d bytes to PC2", param->data_ind.len);
            ESP_LOG_BUFFER_HEXDUMP(TAG, param->data_ind.data, param->data_ind.len, ESP_LOG_INFO);
            ESP_LOGI(TAG, "Data from spp: %.*s", param->data_ind.len, (char *)param->data_ind.data);

            uint8_t data = param->data_ind.data[0];
            if (data == '\n' || data == '\r') {
                ESP_LOGI(TAG, "Received a heartbeat signal from PC1.");
                break;
            }
            
            parsed_packet_t packet = parse_spp_data(param->data_ind.data, param->data_ind.len);
            if (packet.success == false) {
                ESP_LOGE(TAG, "Failed to parse the packet: %.*s", param->data_ind.len, (char *)param->data_ind.data);
                break;
            }
            ESP_LOGI(TAG, "Parsed data: Action: %s, Payload: %s.", packet.action, packet.payload);

            data = (uint8_t)packet.payload[0];

            hid_key_t k = ascii_to_hid(data);
            if (k.code != 0) {
                // Updated send_ble_key to accept modifier
                send_ble_key(k.code, k.modifier); 
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
    // Gives more "airtime" to the Classic BT (PC1) side
    esp_bt_sleep_disable();

    // Setup Class of Device for Linux compatibility
    esp_bt_cod_t cod;
    cod.major = ESP_BT_COD_MAJOR_DEV_PERIPHERAL; // Change from COMPUTER to PERIPHERAL
    cod.minor = ESP_BT_COD_MINOR_PERIPHERAL_KEYBOARD; 
    esp_bt_gap_set_cod(cod, ESP_BT_SET_COD_ALL);

    /* Set Classic BT (SPP) Security */
    esp_bt_sp_param_t param_type = ESP_BT_SP_IOCAP_MODE;
    esp_bt_io_cap_t bt_iocap = ESP_BT_IO_CAP_NONE;
    esp_bt_gap_set_security_param(param_type, &bt_iocap, sizeof(uint8_t));

    /* Enable PIN pairing for older clients if needed */
    esp_bt_pin_type_t pin_type = ESP_BT_PIN_TYPE_FIXED;
    esp_bt_pin_code_t pin_code = {'1', '2', '3', '4'};
    esp_bt_gap_set_pin(pin_type, 0, pin_code);

    // Initialize SPP
    esp_spp_cfg_t spp_cfg = {.mode = ESP_SPP_MODE_CB, .enable_l2cap_ertm = false};
    ESP_ERROR_CHECK(esp_spp_register_callback(esp_spp_cb));
    ESP_ERROR_CHECK(esp_bt_gap_register_callback(esp_bt_gap_cb));
    ESP_ERROR_CHECK(esp_spp_enhanced_init(&spp_cfg));

    ESP_LOGI(TAG, "SPP Module initialized");
}