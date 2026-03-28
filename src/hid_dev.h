#ifndef HID_DEV_H
#define HID_DEV_H

#include <stdint.h>

// This defines what a key looks like for both files
typedef struct {
    uint8_t code;      // The HID Scan Code (e.g., 0x04 for 'a')
    uint8_t modifier;  // The Modifier (e.g., 0x02 for Shift)
} hid_key_t;

// This tells other files that a function named ascii_to_hid exists
hid_key_t ascii_to_hid(uint8_t ascii);

#endif