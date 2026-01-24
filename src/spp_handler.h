#ifndef SPP_HANDLER_H
#define SPP_HANDLER_H

#include "esp_spp_api.h"
#include "esp_gap_bt_api.h"

// This is the function we will call in main.c to start everything
void spp_init(void);

void esp_bt_gap_cb(esp_bt_gap_cb_event_t event, esp_bt_gap_cb_param_t *param);

#endif