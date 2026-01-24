#include "ble_hid_handler.h"
#include "esp_log.h"
#include "esp_hid_common.h"
#include <string.h>

// Logic-supporting includes
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_bt.h"
#include "esp_gap_ble_api.h"
#include "esp_gatts_api.h"

// --- HID Constants ---
#define HIDD_SERVICE_UUID           0x1812
#define HIDD_REPORT_UUID            0x2A4D
#define HIDD_REPORT_MAP_UUID        0x2A4B

static const char *TAG = "HID_HANDLER";

static uint16_t hid_conn_id = 0;
static bool connected_pc2 = false;
static esp_gatt_if_t hid_gatts_if = 0xff;
static uint16_t report_handle = 0;

// Mandatory UUIDs
static const uint16_t GATTS_SERVICE_UUID_HID      = 0x1812;
static const uint16_t GATTS_CHAR_UUID_HID_INFO    = 0x2A4A;
static const uint16_t GATTS_CHAR_UUID_REPORT_MAP  = 0x2A4B;
static const uint16_t GATTS_CHAR_UUID_REPORT      = 0x2A4D;
static const uint16_t GATTS_CHAR_UUID_PROTO_MODE  = 0x2A4E;
static const uint16_t GATTS_CHAR_UUID_CONTROL_PNT = 0x2A4C;

static const uint16_t primary_service_uuid         = ESP_GATT_UUID_PRI_SERVICE;
static const uint16_t character_declaration_uuid   = ESP_GATT_UUID_CHAR_DECLARE;
static const uint16_t character_client_config_uuid = ESP_GATT_UUID_CHAR_CLIENT_CONFIG;
static const uint16_t char_report_reference_uuid   = 0x2908;

static const uint8_t char_prop_read_notify = ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_NOTIFY;
static const uint8_t char_prop_read_write  = ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_WRITE_NR;

// Data Values
static const uint8_t hid_info_val[4] = {0x11, 0x01, 0x00, 0x03}; 
static const uint8_t protocol_mode_val = 0x01;
static const uint8_t report_ref[2] = {0x01, 0x01}; // ID 1, Type Input

// HID Keyboard Report Map
const uint8_t hid_report_map[] = {
    0x05, 0x01, 0x09, 0x06, 0xa1, 0x01, 0x85, 0x01, 0x05, 0x07, 0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 
    0x25, 0x01, 0x75, 0x01, 0x95, 0x08, 0x81, 0x02, 0x95, 0x01, 0x75, 0x08, 0x81, 0x01, 0x95, 0x06, 
    0x75, 0x08, 0x15, 0x00, 0x25, 0x65, 0x05, 0x07, 0x19, 0x00, 0x29, 0x65, 0x81, 0x00, 0xc0
};

uint16_t hidd_handle_table[HIDD_LE_IDX_NB];

// --- THE ATTRIBUTE DATABASE ---
const esp_gatts_attr_db_t gatt_db[HIDD_LE_IDX_NB] = {
    [IDX_SVC] = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&primary_service_uuid, ESP_GATT_PERM_READ, sizeof(uint16_t), sizeof(uint16_t), (uint8_t *)&GATTS_SERVICE_UUID_HID}},

    [IDX_CHAR_HID_INFO] = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&character_declaration_uuid, ESP_GATT_PERM_READ, 1, 1, (uint8_t *)&char_prop_read_notify}},
    [IDX_VAL_HID_INFO]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&GATTS_CHAR_UUID_HID_INFO, ESP_GATT_PERM_READ, 4, 4, (uint8_t *)hid_info_val}},

    [IDX_CHAR_REPORT_MAP] = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&character_declaration_uuid, ESP_GATT_PERM_READ, 1, 1, (uint8_t *)&char_prop_read_notify}},
    [IDX_VAL_REPORT_MAP]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&GATTS_CHAR_UUID_REPORT_MAP, ESP_GATT_PERM_READ, sizeof(hid_report_map), sizeof(hid_report_map), (uint8_t *)hid_report_map}},

    [IDX_CHAR_PROTOCOL_MODE] = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&character_declaration_uuid, ESP_GATT_PERM_READ, 1, 1, (uint8_t *)&char_prop_read_write}},
    [IDX_VAL_PROTOCOL_MODE]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&GATTS_CHAR_UUID_PROTO_MODE, ESP_GATT_PERM_READ|ESP_GATT_PERM_WRITE, 1, 1, (uint8_t *)&protocol_mode_val}},

    [IDX_CHAR_REPORT] = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&character_declaration_uuid, ESP_GATT_PERM_READ, 1, 1, (uint8_t *)&char_prop_read_notify}},
    [IDX_VAL_REPORT]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&GATTS_CHAR_UUID_REPORT, ESP_GATT_PERM_READ, 8, 0, NULL}},
    [IDX_NTF_REPORT]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&character_client_config_uuid, ESP_GATT_PERM_READ|ESP_GATT_PERM_WRITE, 2, 0, NULL}},
    [IDX_REF_REPORT]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&char_report_reference_uuid, ESP_GATT_PERM_READ, 2, 2, (uint8_t *)report_ref}},

    [IDX_CHAR_CONTROL_POINT] = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&character_declaration_uuid, ESP_GATT_PERM_READ, 1, 1, (uint8_t *)&char_prop_read_write}},
    [IDX_VAL_CONTROL_POINT]  = {{ESP_GATT_AUTO_RSP}, {ESP_UUID_LEN_16, (uint8_t *)&GATTS_CHAR_UUID_CONTROL_PNT, ESP_GATT_PERM_READ|ESP_GATT_PERM_WRITE, 1, 0, NULL}},
};

esp_ble_adv_params_t hidd_adv_params = {
    .adv_int_min        = 0x20,
    .adv_int_max        = 0x40,
    .adv_type           = ADV_TYPE_IND,
    .own_addr_type      = BLE_ADDR_TYPE_PUBLIC,
    .channel_map        = ADV_CHNL_ALL,
    .adv_filter_policy  = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};

uint8_t raw_adv_data[] = {
    // Flags: General Discoverable, BR/EDR Not Supported (for the BLE side)
    0x02, 0x01, 0x06,
    // Appearance: HID Keyboard (0x03C1)
    0x03, 0x19, 0xC1, 0x03,
    // Device Name: ESP32_Keyboard
    0x0F, 0x09, 'E','S','P','3','2','_','K','e','y','b','o','a','r','d'
};

// --- BLE HID Logic: Sending keys ---
void send_ble_key(uint8_t key_code, uint8_t modifier) {
    if (!connected_pc2 || report_handle == 0) return;

    // Byte 0 is modifier, Byte 2 is the key
    uint8_t report[8] = {modifier, 0, key_code, 0, 0, 0, 0, 0};
    uint8_t empty[8]  = {0, 0, 0, 0, 0, 0, 0, 0};

    esp_ble_gatts_send_indicate(hid_gatts_if, hid_conn_id, report_handle, 8, report, false);
    vTaskDelay(pdMS_TO_TICKS(10)); 
    esp_ble_gatts_send_indicate(hid_gatts_if, hid_conn_id, report_handle, 8, empty, false);
}

void ble_gap_event_handler(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t *param) {
    switch (event) {
        case ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT:
            // NOW it is safe to start
            esp_ble_gap_start_advertising(&hidd_adv_params);
            break;
        case ESP_GAP_BLE_SEC_REQ_EVT:
            /* Send the positive(true) reply to the peer device to allow pairing */
            esp_ble_gap_security_rsp(param->ble_security.ble_req.bd_addr, true);
            break;
        case ESP_GAP_BLE_AUTH_CMPL_EVT:
            if (param->ble_security.auth_cmpl.success) {
                ESP_LOGI(TAG, "BLE Authentication Success");
            } else {
                ESP_LOGE(TAG, "BLE Authentication Failed, reason = 0x%x", param->ble_security.auth_cmpl.fail_reason);
            }
            break;
        default:
            break;
    }
}

// --- BLE GATT Callback (Interface for PC2) ---
void gatts_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param) {
    switch (event) {
        case ESP_GATTS_REG_EVT:
            hid_gatts_if = gatts_if;
            esp_ble_gap_set_device_name("ESP32_Keyboard");
            // ONLY config the data here, don't start yet
            esp_ble_gap_config_adv_data_raw(raw_adv_data, sizeof(raw_adv_data));
            esp_ble_gatts_create_attr_tab(gatt_db, gatts_if, HIDD_LE_IDX_NB, 0);
            break;
        case ESP_GATTS_CREAT_ATTR_TAB_EVT:
            if (param->add_attr_tab.status == ESP_GATT_OK) {
                memcpy(hidd_handle_table, param->add_attr_tab.handles, sizeof(hidd_handle_table));
                report_handle = hidd_handle_table[IDX_VAL_REPORT];
                esp_ble_gatts_start_service(hidd_handle_table[IDX_SVC]);
            }
            break;
        case ESP_GATTS_CONNECT_EVT:
            hid_conn_id = param->connect.conn_id;
            connected_pc2 = true;
            break;
        case ESP_GATTS_DISCONNECT_EVT:
            connected_pc2 = false;
            esp_ble_gap_start_advertising(&hidd_adv_params);
            break;
        default: break;
    }
}

void ble_hid_init(void) {
    // Setup BLE Security
    esp_ble_auth_req_t auth_req = ESP_LE_AUTH_BOND; // Enable bonding (saving the pair)
    esp_ble_io_cap_t iocap = ESP_IO_CAP_NONE;       // No keyboard/display on ESP32 itself
    uint8_t key_size = 16;
    uint8_t init_key = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
    uint8_t rsp_key = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;

    esp_ble_gap_set_security_param(ESP_BLE_SM_AUTHEN_REQ_MODE, &auth_req, sizeof(uint8_t));
    esp_ble_gap_set_security_param(ESP_BLE_SM_IOCAP_MODE, &iocap, sizeof(uint8_t));
    esp_ble_gap_set_security_param(ESP_BLE_SM_MAX_KEY_SIZE, &key_size, sizeof(uint8_t));
    esp_ble_gap_set_security_param(ESP_BLE_SM_SET_INIT_KEY, &init_key, sizeof(uint8_t));
    esp_ble_gap_set_security_param(ESP_BLE_SM_SET_RSP_KEY, &rsp_key, sizeof(uint8_t));

    // Initialize BLE
    ESP_ERROR_CHECK(esp_ble_gap_register_callback(ble_gap_event_handler));
    ESP_ERROR_CHECK(esp_ble_gatts_register_callback(gatts_event_handler));
    ESP_ERROR_CHECK(esp_ble_gatts_app_register(HIDD_APP_ID));
}
