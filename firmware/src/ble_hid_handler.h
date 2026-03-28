#ifndef BLE_HID_HANDLER_H
#define BLE_HID_HANDLER_H

#include "esp_gatts_api.h"
#include "esp_gap_ble_api.h"  // <--- This defines esp_gap_ble_cb_event_t
#include "esp_gatt_common_api.h"

// UUIDs and Handles
#define HIDD_APP_ID                 0x1812

// --- GATT Table Indices ---
enum {
    IDX_SVC,
    IDX_CHAR_HID_INFO,      IDX_VAL_HID_INFO,
    IDX_CHAR_REPORT_MAP,    IDX_VAL_REPORT_MAP,
    IDX_CHAR_PROTOCOL_MODE, IDX_VAL_PROTOCOL_MODE,
    IDX_CHAR_REPORT,        IDX_VAL_REPORT,         IDX_NTF_REPORT, IDX_REF_REPORT,
    IDX_CHAR_CONTROL_POINT, IDX_VAL_CONTROL_POINT,
    HIDD_LE_IDX_NB,
};

// The "Master Init" for BLE
void ble_hid_init(void);
void send_ble_key(uint8_t key_code, uint8_t modifier);

#endif