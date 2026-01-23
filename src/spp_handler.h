#ifndef SPP_HANDLER_H
#define SPP_HANDLER_H

#include "esp_spp_api.h"

// This is the function we will call in main.c to start everything
void spp_init(void);

// This is the callback that handles the actual data
void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param);

#endif